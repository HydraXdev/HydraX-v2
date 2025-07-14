-- Migration: Add authentication and session fields to users table
-- Date: 2025-01-11
-- Description: Adds fields needed for proper user authentication and session management

-- Add missing fields to users table if they don't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS username VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS first_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS api_key VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS api_key_created_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ban_reason TEXT;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Add missing fields to user_profiles table if they don't exist
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS notification_settings JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS trading_preferences JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS ui_theme VARCHAR(50) DEFAULT 'dark',
ADD COLUMN IF NOT EXISTS language_code VARCHAR(10) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS referred_by_user_id BIGINT REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS recruitment_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recruitment_xp_earned INTEGER DEFAULT 0;

-- Add indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_callsign ON user_profiles(callsign);
CREATE INDEX IF NOT EXISTS idx_user_profiles_referral_code ON user_profiles(referral_code);

-- Create session tracking table (for future distributed sessions)
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT check_expires_after_created CHECK (expires_at > created_at)
);

-- Add indexes for sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create user activity log table
CREATE TABLE IF NOT EXISTS user_activity_log (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for activity log
CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_type ON user_activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at ON user_activity_log(created_at);

-- Create email verification table
CREATE TABLE IF NOT EXISTS email_verifications (
    verification_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    verification_code VARCHAR(100) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_email_pending CHECK (is_verified = TRUE OR user_id IS NOT NULL)
);

-- Add indexes for email verification
CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verifications_code ON email_verifications(verification_code);

-- Update existing Press Pass accounts to have proper tier
UPDATE users 
SET tier = 'PRESS_PASS' 
WHERE tier IS NULL 
  AND subscription_status = 'trial';

-- Set default notification settings for existing users
UPDATE user_profiles 
SET notification_settings = '{
    "trades": true,
    "signals": true,
    "news": true,
    "achievements": true,
    "daily_summary": true,
    "promotional": false
}'::jsonb
WHERE notification_settings IS NULL OR notification_settings = '{}'::jsonb;

-- Set default trading preferences for existing users
UPDATE user_profiles 
SET trading_preferences = '{
    "theater": "DEMO",
    "risk_mode": "default",
    "auto_trading": false,
    "max_daily_trades": 5,
    "preferred_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
    "trading_hours": "all"
}'::jsonb
WHERE trading_preferences IS NULL OR trading_preferences = '{}'::jsonb;

-- Add comments for documentation
COMMENT ON COLUMN users.api_key IS 'Secure API key for external integrations';
COMMENT ON COLUMN users.is_banned IS 'Whether user account is suspended';
COMMENT ON COLUMN user_profiles.referral_code IS 'Unique code for user referrals';
COMMENT ON COLUMN user_profiles.onboarding_completed IS 'Whether user completed the full onboarding flow';
COMMENT ON TABLE user_sessions IS 'Active user sessions for authentication';
COMMENT ON TABLE user_activity_log IS 'Detailed user activity tracking for analytics';
COMMENT ON TABLE email_verifications IS 'Email verification tokens and status';