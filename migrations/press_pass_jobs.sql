-- 🎫 BITTEN Press Pass Scheduled Jobs and Helpers
-- Version: 1.0
-- Created: 2025-01-08
-- Description: Scheduled jobs, marketing functions, and helper procedures for Press Pass system

-- ==========================================
-- SCHEDULED JOB DEFINITIONS
-- ==========================================

-- Table to track job execution history
CREATE TABLE IF NOT EXISTS press_pass_job_history (
    job_id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- success, failed, skipped
    records_affected INTEGER,
    error_message TEXT,
    duration_ms INTEGER
);

-- ==========================================
-- NIGHTLY XP RESET JOB (00:00 UTC)
-- ==========================================

CREATE OR REPLACE FUNCTION job_nightly_xp_reset()
RETURNS void AS $$
DECLARE
    start_time TIMESTAMP;
    affected_users INTEGER;
    total_xp_burned INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Get counts before reset
    SELECT COUNT(*), SUM(xp_earned_today) 
    INTO affected_users, total_xp_burned
    FROM press_pass_shadow_stats 
    WHERE xp_earned_today > 0;
    
    -- Execute the reset
    PERFORM reset_daily_shadow_xp();
    
    -- Log the job execution
    INSERT INTO press_pass_job_history (job_name, status, records_affected, duration_ms)
    VALUES (
        'nightly_xp_reset',
        'success',
        affected_users,
        EXTRACT(MILLISECONDS FROM clock_timestamp() - start_time)::INTEGER
    );
    
    -- Trigger marketing notifications
    PERFORM queue_xp_reset_notifications(affected_users, total_xp_burned);
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO press_pass_job_history (job_name, status, error_message)
    VALUES ('nightly_xp_reset', 'failed', SQLERRM);
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- WARNING NOTIFICATIONS JOB (23:00 UTC)
-- ==========================================

CREATE OR REPLACE FUNCTION job_xp_expiry_warnings()
RETURNS void AS $$
DECLARE
    start_time TIMESTAMP;
    warnings_sent INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Create temporary table of users to warn
    CREATE TEMP TABLE temp_warning_queue AS
    SELECT * FROM get_xp_reset_warnings();
    
    GET DIAGNOSTICS warnings_sent = ROW_COUNT;
    
    -- Queue notifications (integrate with your notification system)
    INSERT INTO notification_queue (user_id, notification_type, payload, scheduled_for)
    SELECT 
        user_id,
        'xp_expiry_warning',
        jsonb_build_object(
            'xp_to_lose', xp_to_lose,
            'engagement_level', engagement_level,
            'minutes_remaining', 60 - EXTRACT(MINUTE FROM CURRENT_TIMESTAMP)
        ),
        CURRENT_TIMESTAMP
    FROM temp_warning_queue;
    
    -- Log job execution
    INSERT INTO press_pass_job_history (job_name, status, records_affected, duration_ms)
    VALUES (
        'xp_expiry_warnings',
        'success',
        warnings_sent,
        EXTRACT(MILLISECONDS FROM clock_timestamp() - start_time)::INTEGER
    );
    
    DROP TABLE temp_warning_queue;
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO press_pass_job_history (job_name, status, error_message)
    VALUES ('xp_expiry_warnings', 'failed', SQLERRM);
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ENGAGEMENT TRACKING JOB (Every 4 hours)
-- ==========================================

CREATE OR REPLACE FUNCTION job_update_engagement_signals()
RETURNS void AS $$
DECLARE
    start_time TIMESTAMP;
    users_updated INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Update near conversion signals
    UPDATE press_pass_shadow_stats p
    SET near_conversion_signals = near_conversion_signals + 1,
        xp_at_near_conversion = xp_earned_today
    WHERE xp_earned_today > 150
        AND trades_executed_today > 5
        AND win_rate_today > 60
        AND NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = p.user_id AND c.enlisted_after = TRUE
        );
    
    GET DIAGNOSTICS users_updated = ROW_COUNT;
    
    -- Update conversion readiness scores
    UPDATE conversion_signal_tracker
    SET conversion_triggers = conversion_triggers || 
        jsonb_build_array(
            jsonb_build_object(
                'trigger', 'high_engagement',
                'timestamp', CURRENT_TIMESTAMP,
                'xp_level', (SELECT xp_earned_today FROM press_pass_shadow_stats WHERE user_id = conversion_signal_tracker.user_id)
            )
        )
    WHERE user_id IN (
        SELECT user_id FROM press_pass_shadow_stats 
        WHERE near_conversion_signals > 2
    )
    AND enlisted_after = FALSE;
    
    -- Log job execution
    INSERT INTO press_pass_job_history (job_name, status, records_affected, duration_ms)
    VALUES (
        'update_engagement_signals',
        'success',
        users_updated,
        EXTRACT(MILLISECONDS FROM clock_timestamp() - start_time)::INTEGER
    );
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO press_pass_job_history (job_name, status, error_message)
    VALUES ('update_engagement_signals', 'failed', SQLERRM);
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- MARKETING AUTOMATION FUNCTIONS
-- ==========================================

-- Queue XP reset notifications
CREATE OR REPLACE FUNCTION queue_xp_reset_notifications(
    affected_users INTEGER,
    total_xp_burned INTEGER
)
RETURNS void AS $$
BEGIN
    -- Insert into your notification queue table
    -- This is a placeholder - integrate with your actual notification system
    INSERT INTO notification_queue (
        notification_type,
        payload,
        scheduled_for,
        priority
    ) VALUES (
        'press_pass_xp_reset_summary',
        jsonb_build_object(
            'affected_users', affected_users,
            'total_xp_burned', total_xp_burned,
            'reset_time', CURRENT_TIMESTAMP,
            'message', format('%s XP burned from %s Press Pass users', total_xp_burned, affected_users)
        ),
        CURRENT_TIMESTAMP,
        'low'
    );
END;
$$ LANGUAGE plpgsql;

-- Get email campaign targets
CREATE OR REPLACE FUNCTION get_press_pass_email_targets(
    campaign_type VARCHAR DEFAULT 'engagement'
)
RETURNS TABLE (
    user_id BIGINT,
    email VARCHAR,
    segment VARCHAR,
    personalization_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH user_segments AS (
        SELECT 
            p.user_id,
            CASE
                WHEN p.total_xp_burned_lifetime > 1000 THEN 'power_user'
                WHEN p.days_active >= 5 THEN 'engaged'
                WHEN p.last_trade_at < CURRENT_TIMESTAMP - INTERVAL '3 days' THEN 'at_risk'
                WHEN p.total_trades_executed < 5 THEN 'new_user'
                ELSE 'standard'
            END as segment,
            p.total_xp_burned_lifetime,
            p.highest_xp_before_reset,
            p.lifetime_win_rate,
            p.last_trade_at
        FROM press_pass_shadow_stats p
        WHERE NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = p.user_id AND c.enlisted_after = TRUE
        )
    )
    SELECT 
        us.user_id,
        u.email,
        us.segment,
        jsonb_build_object(
            'total_xp_lost', us.total_xp_burned_lifetime,
            'best_day_xp', us.highest_xp_before_reset,
            'win_rate', us.lifetime_win_rate,
            'days_since_trade', EXTRACT(DAY FROM CURRENT_TIMESTAMP - us.last_trade_at),
            'recommended_action', CASE us.segment
                WHEN 'power_user' THEN 'upgrade_now'
                WHEN 'engaged' THEN 'maintain_momentum'
                WHEN 'at_risk' THEN 'reactivation'
                WHEN 'new_user' THEN 'education'
                ELSE 'general_engagement'
            END
        ) as personalization_data
    FROM user_segments us
    JOIN users u ON u.user_id = us.user_id
    WHERE CASE campaign_type
        WHEN 'power_users' THEN us.segment = 'power_user'
        WHEN 'at_risk' THEN us.segment = 'at_risk'
        WHEN 'new' THEN us.segment = 'new_user'
        ELSE TRUE
    END;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ANALYTICS AGGREGATION FUNCTIONS
-- ==========================================

-- Generate Press Pass cohort analysis
CREATE OR REPLACE FUNCTION generate_cohort_analysis(
    cohort_period VARCHAR DEFAULT 'week' -- day, week, month
)
RETURNS TABLE (
    cohort_date DATE,
    users_count INTEGER,
    day_1_retention DECIMAL,
    day_3_retention DECIMAL,
    day_7_retention DECIMAL,
    conversion_rate DECIMAL,
    avg_lifetime_xp INTEGER,
    avg_trades_per_user DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH cohorts AS (
        SELECT 
            user_id,
            DATE_TRUNC(cohort_period, MIN(created_at))::DATE as cohort_date,
            MIN(created_at) as first_seen
        FROM trade_logs_all
        WHERE tier = 'press_pass'
        GROUP BY user_id
    ),
    retention AS (
        SELECT 
            c.cohort_date,
            COUNT(DISTINCT c.user_id) as cohort_size,
            COUNT(DISTINCT CASE 
                WHEN t.entry_time >= c.first_seen + INTERVAL '1 day' 
                AND t.entry_time < c.first_seen + INTERVAL '2 days' 
                THEN c.user_id END) as day_1_active,
            COUNT(DISTINCT CASE 
                WHEN t.entry_time >= c.first_seen + INTERVAL '3 days' 
                AND t.entry_time < c.first_seen + INTERVAL '4 days' 
                THEN c.user_id END) as day_3_active,
            COUNT(DISTINCT CASE 
                WHEN t.entry_time >= c.first_seen + INTERVAL '7 days' 
                AND t.entry_time < c.first_seen + INTERVAL '8 days' 
                THEN c.user_id END) as day_7_active,
            COUNT(DISTINCT conv.user_id) as converted_users,
            AVG(ps.total_xp_burned_lifetime) as avg_lifetime_xp,
            COUNT(t.log_id)::DECIMAL / COUNT(DISTINCT c.user_id) as avg_trades
        FROM cohorts c
        LEFT JOIN trade_logs_all t ON c.user_id = t.user_id AND t.tier = 'press_pass'
        LEFT JOIN conversion_signal_tracker conv ON c.user_id = conv.user_id AND conv.enlisted_after = TRUE
        LEFT JOIN press_pass_shadow_stats ps ON c.user_id = ps.user_id
        GROUP BY c.cohort_date
    )
    SELECT 
        cohort_date,
        cohort_size,
        ROUND(100.0 * day_1_active / NULLIF(cohort_size, 0), 2) as day_1_retention,
        ROUND(100.0 * day_3_active / NULLIF(cohort_size, 0), 2) as day_3_retention,
        ROUND(100.0 * day_7_active / NULLIF(cohort_size, 0), 2) as day_7_retention,
        ROUND(100.0 * converted_users / NULLIF(cohort_size, 0), 2) as conversion_rate,
        ROUND(avg_lifetime_xp)::INTEGER as avg_lifetime_xp,
        ROUND(avg_trades, 2) as avg_trades_per_user
    FROM retention
    ORDER BY cohort_date DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- REAL-TIME DASHBOARD FUNCTIONS
-- ==========================================

-- Get real-time Press Pass stats
CREATE OR REPLACE FUNCTION get_realtime_press_pass_stats()
RETURNS TABLE (
    active_users_now INTEGER,
    trades_last_hour INTEGER,
    xp_earned_last_hour INTEGER,
    top_performer_user_id BIGINT,
    top_performer_xp INTEGER,
    conversion_ready_count INTEGER,
    minutes_until_reset INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT CASE WHEN t.entry_time > CURRENT_TIMESTAMP - INTERVAL '5 minutes' THEN t.user_id END)::INTEGER as active_users_now,
        COUNT(CASE WHEN t.entry_time > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 1 END)::INTEGER as trades_last_hour,
        SUM(CASE WHEN t.entry_time > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN t.xp_earned ELSE 0 END)::INTEGER as xp_earned_last_hour,
        (SELECT user_id FROM press_pass_shadow_stats ORDER BY xp_earned_today DESC LIMIT 1) as top_performer_user_id,
        (SELECT xp_earned_today FROM press_pass_shadow_stats ORDER BY xp_earned_today DESC LIMIT 1) as top_performer_xp,
        (SELECT COUNT(*) FROM v_press_pass_hot_leads WHERE lead_type = 'ready_to_convert')::INTEGER as conversion_ready_count,
        (EXTRACT(HOUR FROM '24:00:00'::TIME - CURRENT_TIME AT TIME ZONE 'UTC') * 60 + 
         EXTRACT(MINUTE FROM '24:00:00'::TIME - CURRENT_TIME AT TIME ZONE 'UTC'))::INTEGER as minutes_until_reset
    FROM trade_logs_all t
    WHERE t.tier = 'press_pass';
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- CRON JOB SETUP (PostgreSQL pg_cron extension)
-- ==========================================

/*
-- If using pg_cron extension:
SELECT cron.schedule('reset-press-pass-xp', '0 0 * * *', 'SELECT job_nightly_xp_reset();');
SELECT cron.schedule('xp-expiry-warnings', '0 23 * * *', 'SELECT job_xp_expiry_warnings();');
SELECT cron.schedule('engagement-signals', '0 */4 * * *', 'SELECT job_update_engagement_signals();');

-- If using system cron:
-- Add to crontab:
-- 0 0 * * * psql -U bitten_app -d bitten_db -c "SELECT job_nightly_xp_reset();"
-- 0 23 * * * psql -U bitten_app -d bitten_db -c "SELECT job_xp_expiry_warnings();"
-- 0 */4 * * * psql -U bitten_app -d bitten_db -c "SELECT job_update_engagement_signals();"
*/

-- ==========================================
-- NOTIFICATION QUEUE TABLE (if not exists)
-- ==========================================

CREATE TABLE IF NOT EXISTS notification_queue (
    queue_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    notification_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, failed, cancelled
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notification_queue_status (status, scheduled_for) WHERE status = 'pending',
    INDEX idx_notification_queue_user (user_id),
    INDEX idx_notification_queue_type (notification_type)
);

-- ==========================================
-- SAMPLE USAGE & TESTING
-- ==========================================

/*
-- Test nightly reset
SELECT job_nightly_xp_reset();

-- Test warning generation
SELECT * FROM get_xp_reset_warnings();

-- Get email targets for power user campaign
SELECT * FROM get_press_pass_email_targets('power_users');

-- View job history
SELECT * FROM press_pass_job_history ORDER BY execution_time DESC LIMIT 10;

-- Get real-time stats
SELECT * FROM get_realtime_press_pass_stats();

-- Generate weekly cohort analysis
SELECT * FROM generate_cohort_analysis('week');
*/

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================

INSERT INTO migration_history (filename) VALUES ('press_pass_jobs.sql');