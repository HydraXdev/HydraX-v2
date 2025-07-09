-- 🎫 BITTEN Press Pass Views and Analytics
-- Version: 1.0
-- Created: 2025-01-08
-- Description: Views and analytics functions for Press Pass onboarding system

-- ==========================================
-- ANALYTICS VIEWS
-- ==========================================

-- Press Pass user overview
CREATE OR REPLACE VIEW v_press_pass_overview AS
SELECT 
    p.user_id,
    p.xp_earned_today,
    p.total_xp_burned_lifetime,
    p.trades_executed_today,
    p.win_rate_today,
    p.lifetime_win_rate,
    p.days_active,
    p.last_trade_at,
    p.highest_xp_before_reset,
    c.enlisted_after,
    c.enlisted_tier,
    c.time_to_enlist_days,
    CASE 
        WHEN p.last_trade_at > CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 'active'
        WHEN p.last_trade_at > CURRENT_TIMESTAMP - INTERVAL '3 days' THEN 'cooling'
        WHEN p.last_trade_at > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'dormant'
        ELSE 'churned'
    END as engagement_status,
    CASE
        WHEN p.total_xp_burned_lifetime > 1000 THEN 'high_potential'
        WHEN p.total_xp_burned_lifetime > 500 THEN 'medium_potential'
        WHEN p.total_xp_burned_lifetime > 100 THEN 'low_potential'
        ELSE 'observer'
    END as conversion_potential
FROM press_pass_shadow_stats p
LEFT JOIN conversion_signal_tracker c ON p.user_id = c.user_id;

-- Daily Press Pass metrics
CREATE OR REPLACE VIEW v_press_pass_daily_metrics AS
SELECT 
    DATE(CURRENT_TIMESTAMP) as metric_date,
    COUNT(DISTINCT user_id) as active_users,
    SUM(xp_earned_today) as total_xp_earned,
    SUM(xp_burned_last_night) as total_xp_burned,
    AVG(win_rate_today) as avg_win_rate,
    SUM(trades_executed_today) as total_trades,
    COUNT(DISTINCT CASE WHEN xp_earned_today > 100 THEN user_id END) as high_performers,
    COUNT(DISTINCT CASE WHEN near_conversion_signals > 0 THEN user_id END) as near_conversions
FROM press_pass_shadow_stats
WHERE last_trade_at > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Conversion funnel analysis
CREATE OR REPLACE VIEW v_conversion_funnel AS
SELECT 
    COUNT(DISTINCT user_id) as total_press_pass_users,
    COUNT(DISTINCT CASE WHEN enlisted_after = TRUE THEN user_id END) as converted_users,
    COUNT(DISTINCT CASE WHEN enlisted_after = FALSE AND press_pass_end_date IS NOT NULL THEN user_id END) as expired_unconverted,
    COUNT(DISTINCT CASE WHEN enlisted_after = FALSE AND press_pass_end_date IS NULL THEN user_id END) as active_press_pass,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN enlisted_after = TRUE THEN user_id END) / NULLIF(COUNT(DISTINCT user_id), 0), 2) as conversion_rate,
    AVG(CASE WHEN enlisted_after = TRUE THEN time_to_enlist_days END) as avg_days_to_convert,
    AVG(CASE WHEN enlisted_after = TRUE THEN xp_lost_prior_to_enlist END) as avg_xp_lost_before_convert
FROM conversion_signal_tracker;

-- Top performing Press Pass users (conversion targets)
CREATE OR REPLACE VIEW v_press_pass_hot_leads AS
SELECT 
    p.user_id,
    p.total_xp_burned_lifetime,
    p.total_trades_executed,
    p.lifetime_win_rate,
    p.days_active,
    p.last_trade_at,
    p.highest_xp_before_reset,
    p.best_win_streak,
    CURRENT_TIMESTAMP - p.last_trade_at as time_since_last_trade,
    CASE
        WHEN p.total_xp_burned_lifetime > 500 AND p.lifetime_win_rate > 60 THEN 'ready_to_convert'
        WHEN p.days_active > 5 AND p.total_trades_executed > 20 THEN 'engaged_user'
        WHEN p.highest_xp_before_reset > 200 THEN 'frustrated_achiever'
        ELSE 'nurture'
    END as lead_type
FROM press_pass_shadow_stats p
LEFT JOIN conversion_signal_tracker c ON p.user_id = c.user_id
WHERE c.enlisted_after IS NULL OR c.enlisted_after = FALSE
ORDER BY p.total_xp_burned_lifetime DESC;

-- Trading pattern analysis for Press Pass users
CREATE OR REPLACE VIEW v_press_pass_trading_patterns AS
SELECT 
    t.user_id,
    COUNT(DISTINCT t.symbol) as unique_pairs_traded,
    COUNT(t.log_id) as total_trades,
    AVG(EXTRACT(EPOCH FROM (t.exit_time - t.entry_time))/60) as avg_trade_duration_minutes,
    MODE() WITHIN GROUP (ORDER BY t.session_type) as favorite_session,
    MODE() WITHIN GROUP (ORDER BY t.symbol) as favorite_pair,
    AVG(t.lot_size) as avg_lot_size,
    SUM(CASE WHEN t.pips_result > 0 THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(t.log_id), 0) * 100 as win_rate,
    AVG(ABS(t.pips_result)) as avg_pips_per_trade
FROM trade_logs_all t
WHERE t.tier = 'press_pass' AND t.status = 'closed'
GROUP BY t.user_id;

-- ==========================================
-- REPORTING FUNCTIONS
-- ==========================================

-- Get Press Pass conversion metrics by date range
CREATE OR REPLACE FUNCTION get_press_pass_metrics(
    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    metric_date DATE,
    new_press_passes INTEGER,
    active_users INTEGER,
    conversions INTEGER,
    conversion_rate DECIMAL,
    total_xp_burned INTEGER,
    avg_trades_per_user DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(tl.entry_time) as metric_date,
        COUNT(DISTINCT CASE WHEN DATE(first_trade.first_trade_date) = DATE(tl.entry_time) THEN tl.user_id END) as new_press_passes,
        COUNT(DISTINCT tl.user_id) as active_users,
        COUNT(DISTINCT c.user_id) as conversions,
        ROUND(100.0 * COUNT(DISTINCT c.user_id) / NULLIF(COUNT(DISTINCT tl.user_id), 0), 2) as conversion_rate,
        COALESCE(SUM(ps.xp_burned_last_night), 0)::INTEGER as total_xp_burned,
        ROUND(COUNT(tl.log_id)::DECIMAL / NULLIF(COUNT(DISTINCT tl.user_id), 0), 2) as avg_trades_per_user
    FROM trade_logs_all tl
    LEFT JOIN (
        SELECT user_id, MIN(entry_time) as first_trade_date
        FROM trade_logs_all
        WHERE tier = 'press_pass'
        GROUP BY user_id
    ) first_trade ON tl.user_id = first_trade.user_id
    LEFT JOIN conversion_signal_tracker c ON tl.user_id = c.user_id 
        AND DATE(c.enlisted_date) = DATE(tl.entry_time)
    LEFT JOIN press_pass_shadow_stats ps ON tl.user_id = ps.user_id
    WHERE tl.tier = 'press_pass'
        AND DATE(tl.entry_time) BETWEEN start_date AND end_date
    GROUP BY DATE(tl.entry_time)
    ORDER BY metric_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Get user-specific Press Pass journey
CREATE OR REPLACE FUNCTION get_press_pass_journey(p_user_id BIGINT)
RETURNS TABLE (
    journey_day INTEGER,
    trades_count INTEGER,
    xp_earned INTEGER,
    xp_burned INTEGER,
    win_rate DECIMAL,
    best_trade_pips DECIMAL,
    worst_trade_pips DECIMAL,
    engagement_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH daily_stats AS (
        SELECT 
            DATE(t.entry_time) as trade_date,
            COUNT(t.log_id) as trades_count,
            SUM(t.xp_earned) as xp_earned,
            SUM(CASE WHEN t.pips_result > 0 THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(t.log_id), 0) * 100 as win_rate,
            MAX(t.pips_result) as best_trade_pips,
            MIN(t.pips_result) as worst_trade_pips
        FROM trade_logs_all t
        WHERE t.user_id = p_user_id AND t.tier = 'press_pass'
        GROUP BY DATE(t.entry_time)
    ),
    first_day AS (
        SELECT MIN(trade_date) as start_date FROM daily_stats
    )
    SELECT 
        (ds.trade_date - fd.start_date)::INTEGER + 1 as journey_day,
        ds.trades_count::INTEGER,
        COALESCE(ds.xp_earned, 0)::INTEGER,
        COALESCE(ps.xp_burned_last_night, 0)::INTEGER as xp_burned,
        ROUND(ds.win_rate, 2),
        ds.best_trade_pips,
        ds.worst_trade_pips,
        (ds.trades_count * 10 + COALESCE(ds.xp_earned, 0) / 10)::INTEGER as engagement_score
    FROM daily_stats ds
    CROSS JOIN first_day fd
    LEFT JOIN press_pass_shadow_stats ps ON ps.user_id = p_user_id
    ORDER BY journey_day;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ALERT FUNCTIONS
-- ==========================================

-- Get users who need XP reset warning
CREATE OR REPLACE FUNCTION get_xp_reset_warnings()
RETURNS TABLE (
    user_id BIGINT,
    xp_to_lose INTEGER,
    last_trade_minutes_ago INTEGER,
    engagement_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.user_id,
        p.xp_earned_today,
        EXTRACT(MINUTE FROM CURRENT_TIMESTAMP - p.last_trade_at)::INTEGER,
        CASE
            WHEN p.xp_earned_today > 200 THEN 'high'
            WHEN p.xp_earned_today > 100 THEN 'medium'
            ELSE 'low'
        END as engagement_level
    FROM press_pass_shadow_stats p
    WHERE p.xp_earned_today > 50
        AND EXTRACT(HOUR FROM CURRENT_TIMESTAMP AT TIME ZONE 'UTC') >= 23
        AND NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = p.user_id AND c.enlisted_after = TRUE
        )
    ORDER BY p.xp_earned_today DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- MAINTENANCE FUNCTIONS
-- ==========================================

-- Clean up old Press Pass data (users who never converted after X days)
CREATE OR REPLACE FUNCTION cleanup_old_press_pass_data(days_threshold INTEGER DEFAULT 90)
RETURNS TABLE (
    users_cleaned INTEGER,
    trades_removed INTEGER,
    stats_removed INTEGER
) AS $$
DECLARE
    v_users_cleaned INTEGER;
    v_trades_removed INTEGER;
    v_stats_removed INTEGER;
BEGIN
    -- Get count of users to clean
    SELECT COUNT(DISTINCT p.user_id) INTO v_users_cleaned
    FROM press_pass_shadow_stats p
    WHERE p.last_trade_at < CURRENT_TIMESTAMP - (days_threshold || ' days')::INTERVAL
        AND NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = p.user_id AND c.enlisted_after = TRUE
        );
    
    -- Remove old trade logs
    DELETE FROM trade_logs_all t
    WHERE t.tier = 'press_pass'
        AND t.entry_time < CURRENT_TIMESTAMP - (days_threshold || ' days')::INTERVAL
        AND NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = t.user_id AND c.enlisted_after = TRUE
        );
    GET DIAGNOSTICS v_trades_removed = ROW_COUNT;
    
    -- Remove old shadow stats
    DELETE FROM press_pass_shadow_stats p
    WHERE p.last_trade_at < CURRENT_TIMESTAMP - (days_threshold || ' days')::INTERVAL
        AND NOT EXISTS (
            SELECT 1 FROM conversion_signal_tracker c 
            WHERE c.user_id = p.user_id AND c.enlisted_after = TRUE
        );
    GET DIAGNOSTICS v_stats_removed = ROW_COUNT;
    
    RETURN QUERY SELECT v_users_cleaned, v_trades_removed, v_stats_removed;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- SAMPLE QUERIES FOR COMMON USE CASES
-- ==========================================

/*
-- Get today's Press Pass performance
SELECT * FROM v_press_pass_daily_metrics;

-- Find hot leads ready for conversion
SELECT * FROM v_press_pass_hot_leads LIMIT 20;

-- Check conversion funnel health
SELECT * FROM v_conversion_funnel;

-- Get specific user's Press Pass journey
SELECT * FROM get_press_pass_journey(12345);

-- Get users who need XP reset warnings (run at 23:00 UTC)
SELECT * FROM get_xp_reset_warnings();

-- Get last 7 days metrics
SELECT * FROM get_press_pass_metrics(CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE);

-- Find most successful Press Pass patterns
SELECT 
    favorite_session,
    favorite_pair,
    AVG(win_rate) as avg_win_rate,
    COUNT(*) as user_count
FROM v_press_pass_trading_patterns
GROUP BY favorite_session, favorite_pair
HAVING COUNT(*) > 5
ORDER BY avg_win_rate DESC;
*/

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================

INSERT INTO migration_history (filename) VALUES ('press_pass_views.sql');