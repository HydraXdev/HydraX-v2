-- Add PRESS_PASS to tier enum values
-- Migration: add_press_pass_tier_enum.sql
-- Created: 2025-01-08
-- Description: Add PRESS_PASS tier to existing tier columns

-- First, check if PRESS_PASS already exists in any enum types
DO $$ 
BEGIN
    -- Add PRESS_PASS to tier column in users table if not exists
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum 
        WHERE enumlabel = 'PRESS_PASS' 
        AND enumtypid = (
            SELECT pg_type.oid 
            FROM pg_type 
            JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace 
            WHERE pg_type.typname = 'tierlevel' 
            AND pg_namespace.nspname = 'public'
        )
    ) THEN
        -- If using enum type, add the value
        ALTER TYPE tierlevel ADD VALUE IF NOT EXISTS 'PRESS_PASS' BEFORE 'NIBBLER';
    END IF;
END $$;

-- Update any CHECK constraints that might be validating tier values
-- This handles cases where tier is a VARCHAR with CHECK constraint instead of enum

-- For users table
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_tier_values;
ALTER TABLE users ADD CONSTRAINT check_tier_values 
    CHECK (tier IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));

-- For subscription_plans table
ALTER TABLE subscription_plans DROP CONSTRAINT IF EXISTS check_tier_values;
ALTER TABLE subscription_plans ADD CONSTRAINT check_tier_values 
    CHECK (tier IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));

-- For trades table (tier_at_trade column)
ALTER TABLE trades DROP CONSTRAINT IF EXISTS check_tier_at_trade_values;
ALTER TABLE trades ADD CONSTRAINT check_tier_at_trade_values 
    CHECK (tier_at_trade IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));

-- Insert PRESS_PASS subscription plan if it doesn't exist
INSERT INTO subscription_plans (tier, name, description, price_usd, billing_period, features, limits, is_active)
VALUES (
    'PRESS_PASS',
    'Press Pass',
    'Free trial tier with limited features - 1 trade per day, 60% min TCS, XP resets nightly',
    0.00,
    'monthly',
    '{
        "daily_shots": 1,
        "min_tcs": 60,
        "has_chaingun": false,
        "has_autofire": false,
        "has_stealth": false,
        "has_sniper_access": false,
        "has_midnight_hammer": false,
        "fire_type": "manual",
        "xp_reset_nightly": true
    }'::jsonb,
    '{
        "max_trades_per_day": 1,
        "max_open_trades": 1,
        "risk_per_shot": 2.0,
        "drawdown_cap": 6.0,
        "min_balance": 100
    }'::jsonb,
    true
) ON CONFLICT (tier) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    features = EXCLUDED.features,
    limits = EXCLUDED.limits,
    updated_at = CURRENT_TIMESTAMP;

-- Update existing users who might need PRESS_PASS tier (optional)
-- This would set inactive users without a subscription to PRESS_PASS
-- UPDATE users 
-- SET tier = 'PRESS_PASS' 
-- WHERE subscription_status = 'inactive' 
-- AND tier = 'NIBBLER'
-- AND NOT EXISTS (
--     SELECT 1 FROM user_subscriptions 
--     WHERE user_subscriptions.user_id = users.user_id 
--     AND status = 'active'
-- );

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON subscription_plans TO bitten_app;

-- Migration complete
INSERT INTO migration_history (filename, applied_at) 
VALUES ('add_press_pass_tier_enum.sql', CURRENT_TIMESTAMP)
ON CONFLICT (filename) DO NOTHING;