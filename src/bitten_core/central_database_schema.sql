-- BITTEN Central User Database Schema
-- Single source of truth for all user data
-- Created: 2025-01-15

-- Drop existing tables if they exist (for clean installation)
DROP TABLE IF EXISTS user_audit_log CASCADE;
DROP TABLE IF EXISTS active_trading_slots CASCADE;
DROP TABLE IF EXISTS user_achievements CASCADE;
DROP TABLE IF EXISTS user_trading_stats CASCADE;
DROP TABLE IF EXISTS user_trading_guardrails CASCADE;
DROP TABLE IF EXISTS user_referrals CASCADE;
DROP TABLE IF EXISTS user_xp CASCADE;
DROP TABLE IF EXISTS user_fire_modes CASCADE;
DROP TABLE IF EXISTS user_mt5_accounts CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Core Users Table (Master Record)
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    user_uuid TEXT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    tier TEXT NOT NULL DEFAULT 'NIBBLER' CHECK (tier IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER')),
    subscription_status TEXT DEFAULT 'INACTIVE' CHECK (subscription_status IN ('ACTIVE', 'INACTIVE', 'EXPIRED', 'TRIAL')),
    subscription_expires_at TIMESTAMP,
    stripe_customer_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- User Profiles (Extended Information)
CREATE TABLE user_profiles (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    callsign TEXT,
    bio TEXT,
    timezone TEXT DEFAULT 'UTC',
    risk_percentage REAL DEFAULT 2.0 CHECK (risk_percentage >= 0.5 AND risk_percentage <= 5.0),
    daily_tactic TEXT DEFAULT 'LONE_WOLF',
    account_currency TEXT DEFAULT 'USD',
    notification_settings JSONB DEFAULT '{"trades": true, "signals": true, "news": false}'::jsonb,
    trading_preferences JSONB DEFAULT '{"symbols": [], "sessions": []}'::jsonb,
    ui_theme TEXT DEFAULT 'dark' CHECK (ui_theme IN ('dark', 'light', 'auto')),
    language_code TEXT DEFAULT 'en',
    profile_image_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- MT5 Trading Accounts
CREATE TABLE user_mt5_accounts (
    account_id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    account_number BIGINT NOT NULL,
    broker TEXT NOT NULL,
    server TEXT NOT NULL,
    balance DECIMAL(12,2) DEFAULT 0.00,
    equity DECIMAL(12,2) DEFAULT 0.00,
    margin DECIMAL(12,2) DEFAULT 0.00,
    free_margin DECIMAL(12,2) DEFAULT 0.00,
    leverage INTEGER DEFAULT 100,
    currency TEXT DEFAULT 'USD',
    account_type TEXT DEFAULT 'DEMO' CHECK (account_type IN ('DEMO', 'LIVE')),
    is_primary BOOLEAN DEFAULT FALSE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(telegram_id, account_number)
);

-- Fire Mode Settings
CREATE TABLE user_fire_modes (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    current_mode TEXT DEFAULT 'manual' CHECK (current_mode IN ('manual', 'select', 'auto')),
    max_slots INTEGER DEFAULT 1 CHECK (max_slots >= 1 AND max_slots <= 3),
    slots_in_use INTEGER DEFAULT 0,
    auto_fire_tcs_threshold INTEGER DEFAULT 75 CHECK (auto_fire_tcs_threshold >= 50 AND auto_fire_tcs_threshold <= 100),
    chaingun_count INTEGER DEFAULT 0,
    last_mode_change TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- XP and Level System
CREATE TABLE user_xp (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    total_xp INTEGER DEFAULT 0 CHECK (total_xp >= 0),
    current_level INTEGER DEFAULT 1,
    daily_xp INTEGER DEFAULT 0,
    weekly_xp INTEGER DEFAULT 0,
    monthly_xp INTEGER DEFAULT 0,
    last_daily_reset DATE,
    last_weekly_reset DATE,
    last_monthly_reset DATE,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    prestige_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Achievements System
CREATE TABLE user_achievements (
    achievement_id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    achievement_code TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT NOW(),
    progress JSONB DEFAULT '{}'::jsonb,
    UNIQUE(telegram_id, achievement_code)
);

-- Referral System
CREATE TABLE user_referrals (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    personal_referral_code TEXT UNIQUE NOT NULL,
    referred_by_code TEXT,
    referred_by_user BIGINT REFERENCES users(telegram_id),
    referral_count INTEGER DEFAULT 0 CHECK (referral_count >= 0),
    active_referral_count INTEGER DEFAULT 0,
    total_credits_earned DECIMAL(10,2) DEFAULT 0.00,
    pending_credits DECIMAL(10,2) DEFAULT 0.00,
    applied_credits DECIMAL(10,2) DEFAULT 0.00,
    lifetime_commission DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trading Statistics
CREATE TABLE user_trading_stats (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_pnl DECIMAL(12,2) DEFAULT 0.00,
    best_trade DECIMAL(12,2) DEFAULT 0.00,
    worst_trade DECIMAL(12,2) DEFAULT 0.00,
    average_win DECIMAL(12,2) DEFAULT 0.00,
    average_loss DECIMAL(12,2) DEFAULT 0.00,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    worst_streak INTEGER DEFAULT 0,
    last_trade_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trading Guardrails (Risk Management)
CREATE TABLE user_trading_guardrails (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    -- Daily limits
    max_daily_loss DECIMAL(5,4) DEFAULT 0.06 CHECK (max_daily_loss >= 0.01 AND max_daily_loss <= 1.0),
    max_daily_trades INTEGER DEFAULT 6 CHECK (max_daily_trades >= 1 AND max_daily_trades <= 100),
    daily_trades_used INTEGER DEFAULT 0,
    daily_loss_amount DECIMAL(12,2) DEFAULT 0.00,
    daily_starting_balance DECIMAL(12,2),
    last_daily_reset DATE DEFAULT CURRENT_DATE,
    -- Position limits
    max_concurrent_trades INTEGER DEFAULT 3 CHECK (max_concurrent_trades >= 1 AND max_concurrent_trades <= 20),
    current_open_trades INTEGER DEFAULT 0,
    -- Risk settings
    risk_per_trade DECIMAL(5,4) DEFAULT 0.02 CHECK (risk_per_trade >= 0.001 AND risk_per_trade <= 0.10),
    -- Circuit breakers
    consecutive_losses INTEGER DEFAULT 0,
    cooldown_until TIMESTAMP,
    emergency_stop_active BOOLEAN DEFAULT FALSE,
    emergency_stop_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Active Trading Slots (For Fire Mode)
CREATE TABLE active_trading_slots (
    slot_id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    mission_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    lot_size DECIMAL(10,4),
    entry_price DECIMAL(12,6),
    stop_loss DECIMAL(12,6),
    take_profit DECIMAL(12,6),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'PENDING')),
    pnl DECIMAL(12,2),
    close_reason TEXT
);

-- Comprehensive Audit Log
CREATE TABLE user_audit_log (
    log_id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_subscription_status ON users(subscription_status);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_mt5_accounts_telegram_id ON user_mt5_accounts(telegram_id);
CREATE INDEX idx_mt5_accounts_primary ON user_mt5_accounts(telegram_id, is_primary);

CREATE INDEX idx_trading_stats_telegram_id ON user_trading_stats(telegram_id);
CREATE INDEX idx_trading_stats_last_trade ON user_trading_stats(last_trade_at);

CREATE INDEX idx_guardrails_telegram_id ON user_trading_guardrails(telegram_id);
CREATE INDEX idx_guardrails_daily_reset ON user_trading_guardrails(last_daily_reset);

CREATE INDEX idx_active_slots_telegram_id ON active_trading_slots(telegram_id);
CREATE INDEX idx_active_slots_status ON active_trading_slots(status);
CREATE INDEX idx_active_slots_opened_at ON active_trading_slots(opened_at);

CREATE INDEX idx_audit_log_telegram_id ON user_audit_log(telegram_id);
CREATE INDEX idx_audit_log_created_at ON user_audit_log(created_at);
CREATE INDEX idx_audit_log_action ON user_audit_log(action);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_mt5_accounts_updated_at BEFORE UPDATE ON user_mt5_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_fire_modes_updated_at BEFORE UPDATE ON user_fire_modes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_xp_updated_at BEFORE UPDATE ON user_xp
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_referrals_updated_at BEFORE UPDATE ON user_referrals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_trading_stats_updated_at BEFORE UPDATE ON user_trading_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_trading_guardrails_updated_at BEFORE UPDATE ON user_trading_guardrails
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();