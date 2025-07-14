-- 🎫 BITTEN Press Pass Database Migration
-- Version: 1.0
-- Created: 2025-01-08
-- Description: Tables for Press Pass onboarding system including trade logging,
--              shadow XP tracking, and conversion analytics

-- ==========================================
-- TRADE LOGS FOR ALL USERS
-- ==========================================

-- Comprehensive trade logging for all users including Press Pass
CREATE TABLE trade_logs_all (
    log_id BIGSERIAL PRIMARY KEY,
    
    -- User identification
    user_id BIGINT NOT NULL,
    tier VARCHAR(50) NOT NULL, -- press_pass, nibbler, fang, commander, apex
    
    -- Trade details
    symbol VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    direction VARCHAR(10) NOT NULL, -- buy, sell
    lot_size DECIMAL(10,4) NOT NULL,
    
    -- Trade results
    entry_price DECIMAL(10,5) NOT NULL,
    exit_price DECIMAL(10,5),
    pips_result DECIMAL(10,2),
    percentage_result DECIMAL(10,4),
    profit_loss DECIMAL(15,2),
    
    -- Trade metadata
    strategy_used VARCHAR(100),
    fire_mode VARCHAR(50),
    signal_confidence INTEGER,
    trade_tag VARCHAR(100),
    
    -- Session info
    session_type VARCHAR(50), -- london, newyork, tokyo, sydney
    news_events JSONB DEFAULT '[]'::jsonb,
    
    -- Status
    status VARCHAR(50) DEFAULT 'open', -- open, closed, cancelled
    close_reason VARCHAR(100), -- sl_hit, tp_hit, manual, signal_exit
    
    -- XP tracking
    xp_earned INTEGER DEFAULT 0,
    xp_multiplier DECIMAL(3,2) DEFAULT 1.0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_trade_logs_user (user_id),
    INDEX idx_trade_logs_tier (tier),
    INDEX idx_trade_logs_entry_time (entry_time DESC),
    INDEX idx_trade_logs_symbol (symbol),
    INDEX idx_trade_logs_status (status),
    INDEX idx_trade_logs_user_status (user_id, status)
);

-- ==========================================
-- PRESS PASS WEEKLY LIMITS
-- ==========================================

-- Track weekly Press Pass limits (200 max per week)
CREATE TABLE press_pass_weekly_limits (
    limit_id BIGSERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL, -- Monday of the week
    accounts_created INTEGER DEFAULT 0,
    limit_reached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(week_start_date),
    INDEX idx_weekly_limits_week (week_start_date DESC)
);

-- ==========================================
-- PRESS PASS SHADOW STATS (XP TRACKING ONLY)
-- ==========================================

-- Minimal XP tracking for Press Pass users (resets nightly, no restoration)
CREATE TABLE press_pass_shadow_stats (
    stat_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    
    -- Current day XP only (resets nightly, no restoration)
    xp_earned_today INTEGER DEFAULT 0,
    trades_executed_today INTEGER DEFAULT 0,
    
    -- Simple tracking for urgency messaging
    total_resets INTEGER DEFAULT 0,
    last_reset_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id),
    INDEX idx_shadow_stats_user (user_id),
    INDEX idx_shadow_stats_xp_today (xp_earned_today DESC)
);

-- ==========================================
-- CONVERSION SIGNAL TRACKER
-- ==========================================

-- Track conversion analytics for Press Pass to paid tier transitions
CREATE TABLE conversion_signal_tracker (
    tracker_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    
    -- Press Pass journey
    press_pass_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    press_pass_end_date TIMESTAMP WITH TIME ZONE,
    press_pass_duration_days INTEGER DEFAULT 7,
    
    -- Conversion tracking
    enlisted_after BOOLEAN DEFAULT FALSE,
    enlisted_date TIMESTAMP WITH TIME ZONE,
    enlisted_tier VARCHAR(50), -- nibbler, fang, commander, apex
    time_to_enlist_days INTEGER,
    conversion_source VARCHAR(100), -- email, telegram, webapp, organic
    
    -- Performance before conversion (current day only)
    xp_preserved_at_enlistment INTEGER DEFAULT 0, -- Current day XP + 50 bonus
    enlistment_bonus_xp INTEGER DEFAULT 50,
    trades_before_enlist INTEGER DEFAULT 0,
    
    -- Engagement signals
    email_opens INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    telegram_interactions INTEGER DEFAULT 0,
    webapp_sessions INTEGER DEFAULT 0,
    
    -- Conversion triggers
    conversion_triggers JSONB DEFAULT '[]'::jsonb, -- ["xp_reset_warning", "leaderboard_tease", "squad_invite"]
    final_trigger VARCHAR(100), -- The last action before conversion
    
    -- Marketing attribution
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referral_code VARCHAR(50),
    
    -- Retention after conversion
    still_active_30_days BOOLEAN,
    still_active_60_days BOOLEAN,
    still_active_90_days BOOLEAN,
    ltv_estimate DECIMAL(15,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id),
    INDEX idx_conversion_user (user_id),
    INDEX idx_conversion_enlisted (enlisted_after),
    INDEX idx_conversion_date (enlisted_date),
    INDEX idx_conversion_source (conversion_source),
    INDEX idx_conversion_campaign (utm_campaign)
);

-- ==========================================
-- TRIGGERS FOR AUTOMATED UPDATES
-- ==========================================

-- Update shadow stats when new trades are logged (simplified)
CREATE OR REPLACE FUNCTION update_shadow_stats_on_trade()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tier = 'press_pass' AND NEW.status = 'closed' THEN
        -- Update or insert shadow stats (current day only)
        INSERT INTO press_pass_shadow_stats (user_id, trades_executed_today, xp_earned_today)
        VALUES (NEW.user_id, 1, COALESCE(NEW.xp_earned, 0))
        ON CONFLICT (user_id) DO UPDATE SET
            trades_executed_today = press_pass_shadow_stats.trades_executed_today + 1,
            xp_earned_today = press_pass_shadow_stats.xp_earned_today + COALESCE(NEW.xp_earned, 0),
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_shadow_stats_trigger
AFTER INSERT OR UPDATE ON trade_logs_all
FOR EACH ROW EXECUTE FUNCTION update_shadow_stats_on_trade();

-- Reset XP at midnight UTC (no restoration, just wipe)
CREATE OR REPLACE FUNCTION reset_daily_press_pass_xp()
RETURNS void AS $$
BEGIN
    -- Simply reset XP to 0 - no preservation, no shadow tracking
    UPDATE press_pass_shadow_stats
    SET xp_earned_today = 0,
        trades_executed_today = 0,
        total_resets = total_resets + 1,
        last_reset_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE xp_earned_today > 0;
END;
$$ LANGUAGE plpgsql;

-- Check and update weekly Press Pass limits
CREATE OR REPLACE FUNCTION check_weekly_press_pass_limit()
RETURNS BOOLEAN AS $$
DECLARE
    current_week_start DATE;
    current_count INTEGER;
    limit_reached BOOLEAN;
BEGIN
    -- Get Monday of current week
    current_week_start := DATE_TRUNC('week', CURRENT_DATE)::DATE;
    
    -- Get or create weekly record
    INSERT INTO press_pass_weekly_limits (week_start_date, accounts_created)
    VALUES (current_week_start, 0)
    ON CONFLICT (week_start_date) DO NOTHING;
    
    -- Get current count
    SELECT accounts_created, limit_reached INTO current_count, limit_reached
    FROM press_pass_weekly_limits
    WHERE week_start_date = current_week_start;
    
    -- Return whether limit is reached
    RETURN (current_count >= 200 OR limit_reached);
END;
$$ LANGUAGE plpgsql;

-- Increment weekly Press Pass count
CREATE OR REPLACE FUNCTION increment_weekly_press_pass_count()
RETURNS void AS $$
DECLARE
    current_week_start DATE;
    new_count INTEGER;
BEGIN
    current_week_start := DATE_TRUNC('week', CURRENT_DATE)::DATE;
    
    UPDATE press_pass_weekly_limits
    SET accounts_created = accounts_created + 1,
        limit_reached = (accounts_created + 1 >= 200),
        updated_at = CURRENT_TIMESTAMP
    WHERE week_start_date = current_week_start;
END;
$$ LANGUAGE plpgsql;

-- Track conversion when user enlists
CREATE OR REPLACE FUNCTION track_conversion()
RETURNS TRIGGER AS $$
DECLARE
    press_pass_start TIMESTAMP WITH TIME ZONE;
    current_xp INTEGER;
    total_trades INTEGER;
BEGIN
    -- Only track if upgrading from press_pass
    IF OLD.tier = 'press_pass' AND NEW.tier != 'press_pass' THEN
        -- Get Press Pass start date
        SELECT MIN(created_at) INTO press_pass_start
        FROM trade_logs_all
        WHERE user_id = NEW.user_id AND tier = 'press_pass';
        
        -- Get current day XP only (what they're preserving)
        SELECT xp_earned_today, trades_executed_today
        INTO current_xp, total_trades
        FROM press_pass_shadow_stats
        WHERE user_id = NEW.user_id;
        
        -- Insert or update conversion tracking
        INSERT INTO conversion_signal_tracker (
            user_id,
            press_pass_start_date,
            press_pass_end_date,
            enlisted_after,
            enlisted_date,
            enlisted_tier,
            time_to_enlist_days,
            xp_preserved_at_enlistment,
            enlistment_bonus_xp,
            trades_before_enlist
        ) VALUES (
            NEW.user_id,
            press_pass_start,
            CURRENT_TIMESTAMP,
            TRUE,
            CURRENT_TIMESTAMP,
            NEW.tier,
            EXTRACT(DAY FROM CURRENT_TIMESTAMP - press_pass_start)::INTEGER,
            COALESCE(current_xp, 0) + 50, -- Current XP + 50 bonus
            50,
            COALESCE(total_trades, 0)
        )
        ON CONFLICT (user_id) DO UPDATE SET
            enlisted_after = TRUE,
            enlisted_date = CURRENT_TIMESTAMP,
            enlisted_tier = NEW.tier,
            press_pass_end_date = CURRENT_TIMESTAMP,
            time_to_enlist_days = EXTRACT(DAY FROM CURRENT_TIMESTAMP - conversion_signal_tracker.press_pass_start_date)::INTEGER,
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger should be created on the users table when tier changes
-- CREATE TRIGGER track_conversion_trigger
-- AFTER UPDATE OF tier ON users
-- FOR EACH ROW EXECUTE FUNCTION track_conversion();

-- ==========================================
-- PERFORMANCE INDEXES
-- ==========================================

-- Composite indexes for common queries
CREATE INDEX idx_press_pass_active_users ON press_pass_shadow_stats(xp_earned_today DESC, last_trade_at DESC) WHERE xp_earned_today > 0;
CREATE INDEX idx_trade_logs_press_pass ON trade_logs_all(user_id, entry_time DESC) WHERE tier = 'press_pass';
CREATE INDEX idx_conversion_ready ON press_pass_shadow_stats(total_xp_burned_lifetime DESC, total_trades_executed DESC) WHERE total_xp_burned_lifetime > 100;

-- ==========================================
-- INITIAL DATA & SCHEDULING
-- ==========================================

-- Note: Schedule this function to run daily at 00:00 UTC
-- Example cron job or scheduled task:
-- 0 0 * * * psql -d bitten_db -c "SELECT reset_daily_shadow_xp();"

-- ==========================================
-- PERMISSIONS (Run as superuser)
-- ==========================================

-- Grant permissions to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================

-- Migration version tracking
INSERT INTO migration_history (filename) VALUES ('press_pass_tables.sql');