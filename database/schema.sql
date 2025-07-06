-- 🎯 BITTEN PostgreSQL Database Schema
-- Version: 1.0
-- Last Updated: 2025-01-07

-- Create database
-- CREATE DATABASE bitten_production;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For better indexing

-- ==========================================
-- USERS & AUTHENTICATION
-- ==========================================

-- Users table (core user data)
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    
    -- Subscription info
    tier VARCHAR(50) NOT NULL DEFAULT 'NIBBLER',
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    payment_method VARCHAR(50),
    
    -- MT5 connection
    mt5_account_id VARCHAR(255),
    mt5_broker_server VARCHAR(255),
    mt5_connected BOOLEAN DEFAULT FALSE,
    
    -- Security
    api_key VARCHAR(255) UNIQUE,
    api_key_created_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_users_telegram_id (telegram_id),
    INDEX idx_users_tier (tier),
    INDEX idx_users_subscription_status (subscription_status)
);

-- User profiles (extended user data)
CREATE TABLE user_profiles (
    profile_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- XP & Progression
    total_xp INTEGER NOT NULL DEFAULT 0,
    current_rank VARCHAR(50) NOT NULL DEFAULT 'RECRUIT',
    medals_data JSONB DEFAULT '[]'::jsonb,
    achievements_data JSONB DEFAULT '[]'::jsonb,
    
    -- Trading stats
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_profit_usd DECIMAL(15,2) DEFAULT 0,
    total_pips INTEGER DEFAULT 0,
    largest_win_usd DECIMAL(15,2) DEFAULT 0,
    largest_loss_usd DECIMAL(15,2) DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    worst_streak INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    
    -- Recruitment
    referral_code VARCHAR(50) UNIQUE,
    referred_by_user_id BIGINT REFERENCES users(user_id),
    recruitment_count INTEGER DEFAULT 0,
    recruitment_xp_earned INTEGER DEFAULT 0,
    
    -- Preferences
    notification_settings JSONB DEFAULT '{}'::jsonb,
    trading_preferences JSONB DEFAULT '{}'::jsonb,
    ui_theme VARCHAR(50) DEFAULT 'dark',
    language_code VARCHAR(10) DEFAULT 'en',
    
    -- Metadata
    last_trade_at TIMESTAMP WITH TIME ZONE,
    profile_completed BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_profiles_referral_code (referral_code),
    INDEX idx_profiles_total_xp (total_xp DESC)
);

-- ==========================================
-- TRADING DATA
-- ==========================================

-- Trades table
CREATE TABLE trades (
    trade_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Trade identifiers
    mt5_ticket BIGINT UNIQUE,
    internal_id UUID DEFAULT uuid_generate_v4(),
    
    -- Trade details
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    lot_size DECIMAL(10,2) NOT NULL,
    
    -- Prices
    entry_price DECIMAL(10,5) NOT NULL,
    exit_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),
    
    -- Results
    profit_usd DECIMAL(15,2),
    profit_pips DECIMAL(10,2),
    commission DECIMAL(10,2) DEFAULT 0,
    swap DECIMAL(10,2) DEFAULT 0,
    
    -- Risk metrics
    risk_amount DECIMAL(15,2),
    risk_percent DECIMAL(5,2),
    risk_reward_ratio DECIMAL(5,2),
    
    -- BITTEN specific
    tcs_score INTEGER,
    fire_mode VARCHAR(50),
    tier_at_trade VARCHAR(50),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    close_reason VARCHAR(100),
    
    -- Timing
    signal_time TIMESTAMP WITH TIME ZONE,
    open_time TIMESTAMP WITH TIME ZONE,
    close_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_trades_user_id (user_id),
    INDEX idx_trades_symbol (symbol),
    INDEX idx_trades_status (status),
    INDEX idx_trades_open_time (open_time DESC),
    INDEX idx_trades_fire_mode (fire_mode)
);

-- Trade modifications log
CREATE TABLE trade_modifications (
    modification_id BIGSERIAL PRIMARY KEY,
    trade_id BIGINT NOT NULL REFERENCES trades(trade_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    
    modification_type VARCHAR(50) NOT NULL, -- sl_change, tp_change, partial_close
    old_value DECIMAL(10,5),
    new_value DECIMAL(10,5),
    reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_trade_mods_trade_id (trade_id)
);

-- ==========================================
-- RISK MANAGEMENT
-- ==========================================

-- Daily risk sessions
CREATE TABLE risk_sessions (
    session_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    
    -- Daily stats
    starting_balance DECIMAL(15,2) NOT NULL,
    ending_balance DECIMAL(15,2),
    trades_taken INTEGER DEFAULT 0,
    trades_won INTEGER DEFAULT 0,
    trades_lost INTEGER DEFAULT 0,
    
    -- Risk metrics
    daily_pnl DECIMAL(15,2) DEFAULT 0,
    daily_pnl_percent DECIMAL(5,2) DEFAULT 0,
    max_drawdown_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Behavioral tracking
    consecutive_losses INTEGER DEFAULT 0,
    consecutive_wins INTEGER DEFAULT 0,
    tilt_strikes INTEGER DEFAULT 0,
    medic_mode_activated BOOLEAN DEFAULT FALSE,
    medic_activated_at TIMESTAMP WITH TIME ZONE,
    
    -- Cooldowns
    cooldown_active BOOLEAN DEFAULT FALSE,
    cooldown_expires_at TIMESTAMP WITH TIME ZONE,
    cooldown_reason TEXT,
    
    -- Risk mode
    risk_mode VARCHAR(50) DEFAULT 'default',
    risk_percent_used DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint for one session per user per day
    UNIQUE(user_id, session_date),
    INDEX idx_risk_sessions_user_date (user_id, session_date DESC)
);

-- ==========================================
-- XP & GAMIFICATION
-- ==========================================

-- XP transactions
CREATE TABLE xp_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    
    -- Source tracking
    source_type VARCHAR(50) NOT NULL, -- trade, achievement, daily, referral, bonus
    source_id BIGINT, -- Reference to trade_id, achievement_id, etc
    
    -- Details
    description TEXT,
    multipliers JSONB DEFAULT '[]'::jsonb, -- [{type: 'weekend', value: 2.0}]
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_xp_trans_user_id (user_id),
    INDEX idx_xp_trans_created_at (created_at DESC)
);

-- Achievements
CREATE TABLE achievements (
    achievement_id BIGSERIAL PRIMARY KEY,
    
    -- Definition
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    tier VARCHAR(50), -- bronze, silver, gold, platinum
    
    -- Requirements
    requirements JSONB NOT NULL, -- {trades: 100, win_rate: 0.7}
    
    -- Rewards
    xp_reward INTEGER DEFAULT 0,
    medal_reward JSONB,
    unlock_features JSONB,
    
    -- Display
    icon_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_achievements_category (category),
    INDEX idx_achievements_tier (tier)
);

-- User achievements (earned)
CREATE TABLE user_achievements (
    user_achievement_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id BIGINT NOT NULL REFERENCES achievements(achievement_id),
    
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    progress JSONB DEFAULT '{}'::jsonb, -- Current progress towards achievement
    
    UNIQUE(user_id, achievement_id),
    INDEX idx_user_achievements_user_id (user_id)
);

-- ==========================================
-- NEWS & MARKET DATA
-- ==========================================

-- Economic news events
CREATE TABLE news_events (
    event_id BIGSERIAL PRIMARY KEY,
    
    -- Event details
    external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    country VARCHAR(10),
    currency VARCHAR(10),
    impact VARCHAR(20), -- high, medium, low
    
    -- Times
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    blackout_start TIMESTAMP WITH TIME ZONE,
    blackout_end TIMESTAMP WITH TIME ZONE,
    
    -- Data
    forecast VARCHAR(50),
    previous VARCHAR(50),
    actual VARCHAR(50),
    
    -- Metadata
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_news_events_time (event_time),
    INDEX idx_news_events_currency (currency),
    INDEX idx_news_events_impact (impact)
);

-- ==========================================
-- SUBSCRIPTIONS & PAYMENTS
-- ==========================================

-- Subscription plans
CREATE TABLE subscription_plans (
    plan_id BIGSERIAL PRIMARY KEY,
    
    tier VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pricing
    price_usd DECIMAL(10,2) NOT NULL,
    price_crypto JSONB, -- {BTC: 0.001, ETH: 0.05}
    billing_period VARCHAR(50) DEFAULT 'monthly',
    
    -- Features
    features JSONB NOT NULL,
    limits JSONB NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_plans_tier (tier)
);

-- User subscriptions
CREATE TABLE user_subscriptions (
    subscription_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    plan_id BIGINT NOT NULL REFERENCES subscription_plans(plan_id),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Payment
    payment_method VARCHAR(50),
    payment_processor VARCHAR(50),
    processor_subscription_id VARCHAR(255),
    
    -- Billing
    last_payment_at TIMESTAMP WITH TIME ZONE,
    next_payment_at TIMESTAMP WITH TIME ZONE,
    payment_failures INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_subs_user_id (user_id),
    INDEX idx_user_subs_status (status),
    INDEX idx_user_subs_expires_at (expires_at)
);

-- Payment transactions
CREATE TABLE payment_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subscription_id BIGINT REFERENCES user_subscriptions(subscription_id),
    
    -- Transaction details
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    payment_method VARCHAR(50),
    processor VARCHAR(50),
    processor_transaction_id VARCHAR(255),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    failure_reason TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_payment_trans_user_id (user_id),
    INDEX idx_payment_trans_status (status)
);

-- ==========================================
-- AUDIT & LOGGING
-- ==========================================

-- Audit log
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id BIGINT,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created_at (created_at DESC)
);

-- ==========================================
-- FUNCTIONS & TRIGGERS
-- ==========================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create update triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_risk_sessions_updated_at BEFORE UPDATE ON risk_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate user stats
CREATE OR REPLACE FUNCTION calculate_user_stats(p_user_id BIGINT)
RETURNS TABLE (
    total_trades INTEGER,
    win_rate DECIMAL,
    profit_factor DECIMAL,
    avg_win DECIMAL,
    avg_loss DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_trades,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                (COUNT(*) FILTER (WHERE profit_usd > 0)::DECIMAL / COUNT(*)::DECIMAL * 100)
            ELSE 0 
        END as win_rate,
        CASE 
            WHEN SUM(profit_usd) FILTER (WHERE profit_usd < 0) != 0 THEN
                ABS(SUM(profit_usd) FILTER (WHERE profit_usd > 0) / SUM(profit_usd) FILTER (WHERE profit_usd < 0))
            ELSE 0
        END as profit_factor,
        AVG(profit_usd) FILTER (WHERE profit_usd > 0) as avg_win,
        AVG(profit_usd) FILTER (WHERE profit_usd < 0) as avg_loss
    FROM trades
    WHERE user_id = p_user_id AND status = 'closed';
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- INITIAL DATA
-- ==========================================

-- Insert subscription plans
INSERT INTO subscription_plans (tier, name, price_usd, features, limits) VALUES
('NIBBLER', 'Nibbler', 39.00, 
 '{"single_shot": true, "max_daily_trades": 6, "risk_percent": 1.0}'::jsonb,
 '{"daily_loss_limit": 6.0, "tcs_minimum": 70}'::jsonb),
('FANG', 'Fang', 89.00,
 '{"single_shot": true, "chaingun": true, "max_daily_trades": 10, "risk_percent": 1.25}'::jsonb,
 '{"daily_loss_limit": 8.5, "tcs_minimum": 85}'::jsonb),
('COMMANDER', 'Commander', 139.00,
 '{"single_shot": true, "chaingun": true, "auto_fire": true, "max_daily_trades": 10, "risk_percent": 1.25}'::jsonb,
 '{"daily_loss_limit": 8.5, "tcs_minimum": 91}'::jsonb),
('APEX', 'Apex', 188.00,
 '{"single_shot": true, "chaingun": true, "auto_fire": true, "stealth": true, "unlimited_trades": true, "risk_percent": 1.25}'::jsonb,
 '{"daily_loss_limit": 8.5, "tcs_minimum": 91}'::jsonb);

-- Create indexes for performance
CREATE INDEX idx_trades_user_profit ON trades(user_id, profit_usd);
CREATE INDEX idx_trades_user_time ON trades(user_id, open_time DESC);
CREATE INDEX idx_risk_sessions_active ON risk_sessions(user_id) WHERE cooldown_active = TRUE;
CREATE INDEX idx_users_active_subs ON users(tier, subscription_status) WHERE subscription_status = 'active';

-- ==========================================
-- PERMISSIONS (Run as superuser)
-- ==========================================

-- Create application user
-- CREATE USER bitten_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE bitten_production TO bitten_app;
-- GRANT USAGE ON SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;