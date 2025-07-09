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
-- PRESS PASS SHADOW STATS
-- ==========================================

-- Shadow XP and stats tracking for Press Pass users (resets nightly)
CREATE TABLE press_pass_shadow_stats (
    stat_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    
    -- Daily XP tracking
    xp_earned_today INTEGER DEFAULT 0,
    xp_burned_last_night INTEGER DEFAULT 0,
    total_xp_burned_lifetime INTEGER DEFAULT 0,
    
    -- Daily performance
    trades_executed_today INTEGER DEFAULT 0,
    wins_today INTEGER DEFAULT 0,
    losses_today INTEGER DEFAULT 0,
    win_rate_today DECIMAL(5,2),
    
    -- Cumulative stats (don't reset)
    total_trades_executed INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    lifetime_win_rate DECIMAL(5,2),
    best_daily_xp INTEGER DEFAULT 0,
    best_win_streak INTEGER DEFAULT 0,
    
    -- Engagement metrics
    days_active INTEGER DEFAULT 0,
    last_trade_at TIMESTAMP WITH TIME ZONE,
    last_reset_at TIMESTAMP WITH TIME ZONE,
    
    -- Session tracking
    most_active_session VARCHAR(50),
    preferred_pairs JSONB DEFAULT '[]'::jsonb, -- ["EUR/USD", "GBP/USD"]
    average_trade_duration_minutes INTEGER,
    
    -- Conversion signals
    near_conversion_signals INTEGER DEFAULT 0, -- Times they almost enlisted
    xp_at_near_conversion INTEGER DEFAULT 0,
    highest_xp_before_reset INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id),
    INDEX idx_shadow_stats_user (user_id),
    INDEX idx_shadow_stats_last_trade (last_trade_at DESC),
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
    press_pass_duration_days INTEGER,
    
    -- Conversion tracking
    enlisted_after BOOLEAN DEFAULT FALSE,
    enlisted_date TIMESTAMP WITH TIME ZONE,
    enlisted_tier VARCHAR(50), -- nibbler, fang, commander, apex
    time_to_enlist_days INTEGER,
    conversion_source VARCHAR(100), -- email, telegram, webapp, organic
    
    -- Performance before conversion
    xp_lost_prior_to_enlist INTEGER DEFAULT 0,
    trades_before_enlist INTEGER DEFAULT 0,
    win_rate_before_enlist DECIMAL(5,2),
    best_streak_before_enlist INTEGER DEFAULT 0,
    
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

-- Update shadow stats when new trades are logged
CREATE OR REPLACE FUNCTION update_shadow_stats_on_trade()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tier = 'press_pass' AND NEW.status = 'closed' THEN
        -- Update or insert shadow stats
        INSERT INTO press_pass_shadow_stats (user_id, trades_executed_today, total_trades_executed, last_trade_at)
        VALUES (NEW.user_id, 1, 1, NEW.exit_time)
        ON CONFLICT (user_id) DO UPDATE SET
            trades_executed_today = press_pass_shadow_stats.trades_executed_today + 1,
            total_trades_executed = press_pass_shadow_stats.total_trades_executed + 1,
            last_trade_at = NEW.exit_time,
            xp_earned_today = press_pass_shadow_stats.xp_earned_today + COALESCE(NEW.xp_earned, 0),
            wins_today = CASE WHEN NEW.pips_result > 0 THEN press_pass_shadow_stats.wins_today + 1 ELSE press_pass_shadow_stats.wins_today END,
            losses_today = CASE WHEN NEW.pips_result < 0 THEN press_pass_shadow_stats.losses_today + 1 ELSE press_pass_shadow_stats.losses_today END,
            total_wins = CASE WHEN NEW.pips_result > 0 THEN press_pass_shadow_stats.total_wins + 1 ELSE press_pass_shadow_stats.total_wins END,
            total_losses = CASE WHEN NEW.pips_result < 0 THEN press_pass_shadow_stats.total_losses + 1 ELSE press_pass_shadow_stats.total_losses END,
            updated_at = CURRENT_TIMESTAMP;
            
        -- Update win rates
        UPDATE press_pass_shadow_stats
        SET win_rate_today = CASE 
                WHEN (wins_today + losses_today) > 0 
                THEN (wins_today::DECIMAL / (wins_today + losses_today)) * 100 
                ELSE 0 
            END,
            lifetime_win_rate = CASE 
                WHEN (total_wins + total_losses) > 0 
                THEN (total_wins::DECIMAL / (total_wins + total_losses)) * 100 
                ELSE 0 
            END
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_shadow_stats_trigger
AFTER INSERT OR UPDATE ON trade_logs_all
FOR EACH ROW EXECUTE FUNCTION update_shadow_stats_on_trade();

-- Reset shadow XP at midnight UTC
CREATE OR REPLACE FUNCTION reset_daily_shadow_xp()
RETURNS void AS $$
BEGIN
    -- Store burned XP before reset
    UPDATE press_pass_shadow_stats
    SET xp_burned_last_night = xp_earned_today,
        total_xp_burned_lifetime = total_xp_burned_lifetime + xp_earned_today,
        highest_xp_before_reset = GREATEST(highest_xp_before_reset, xp_earned_today),
        xp_earned_today = 0,
        trades_executed_today = 0,
        wins_today = 0,
        losses_today = 0,
        win_rate_today = 0,
        last_reset_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE xp_earned_today > 0;
END;
$$ LANGUAGE plpgsql;

-- Track conversion when user enlists
CREATE OR REPLACE FUNCTION track_conversion()
RETURNS TRIGGER AS $$
DECLARE
    press_pass_start TIMESTAMP WITH TIME ZONE;
    total_xp_lost INTEGER;
    total_trades INTEGER;
    avg_win_rate DECIMAL(5,2);
BEGIN
    -- Only track if upgrading from press_pass
    IF OLD.tier = 'press_pass' AND NEW.tier != 'press_pass' THEN
        -- Get Press Pass start date
        SELECT MIN(created_at) INTO press_pass_start
        FROM trade_logs_all
        WHERE user_id = NEW.user_id AND tier = 'press_pass';
        
        -- Get shadow stats
        SELECT total_xp_burned_lifetime, total_trades_executed, lifetime_win_rate
        INTO total_xp_lost, total_trades, avg_win_rate
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
            xp_lost_prior_to_enlist,
            trades_before_enlist,
            win_rate_before_enlist
        ) VALUES (
            NEW.user_id,
            press_pass_start,
            CURRENT_TIMESTAMP,
            TRUE,
            CURRENT_TIMESTAMP,
            NEW.tier,
            EXTRACT(DAY FROM CURRENT_TIMESTAMP - press_pass_start)::INTEGER,
            COALESCE(total_xp_lost, 0),
            COALESCE(total_trades, 0),
            COALESCE(avg_win_rate, 0)
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