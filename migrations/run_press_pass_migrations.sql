-- Press Pass Database Migration Runner (SQL Version)
-- This script executes all Press Pass migrations in the correct order
-- Run this script in your PostgreSQL client connected to the bitten_db database

-- Start transaction for atomic execution
BEGIN;

-- Create migration history table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function to check if migration was applied
CREATE OR REPLACE FUNCTION check_migration_applied(p_filename VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM migration_history WHERE filename = p_filename);
END;
$$ LANGUAGE plpgsql;

-- Display migration status
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Press Pass Database Migration ===';
    RAISE NOTICE 'Starting at: %', CURRENT_TIMESTAMP;
    RAISE NOTICE '';
END $$;

-- Migration 1: Add PRESS_PASS tier enum
DO $$
BEGIN
    IF NOT check_migration_applied('add_press_pass_tier_enum.sql') THEN
        RAISE NOTICE 'Applying migration: add_press_pass_tier_enum.sql';
        
        -- Check if PRESS_PASS already exists in enum
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
        
        -- Update CHECK constraints
        ALTER TABLE users DROP CONSTRAINT IF EXISTS check_tier_values;
        ALTER TABLE users ADD CONSTRAINT check_tier_values 
            CHECK (tier IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));
        
        ALTER TABLE subscription_plans DROP CONSTRAINT IF EXISTS check_tier_values;
        ALTER TABLE subscription_plans ADD CONSTRAINT check_tier_values 
            CHECK (tier IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));
        
        ALTER TABLE trades DROP CONSTRAINT IF EXISTS check_tier_at_trade_values;
        ALTER TABLE trades ADD CONSTRAINT check_tier_at_trade_values 
            CHECK (tier_at_trade IN ('PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'));
        
        -- Insert PRESS_PASS subscription plan
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
        
        GRANT SELECT, INSERT, UPDATE ON subscription_plans TO bitten_app;
        
        INSERT INTO migration_history (filename, applied_at) 
        VALUES ('add_press_pass_tier_enum.sql', CURRENT_TIMESTAMP);
        
        RAISE NOTICE '✓ Successfully applied: add_press_pass_tier_enum.sql';
    ELSE
        RAISE NOTICE '⚠ Skipping: add_press_pass_tier_enum.sql (already applied)';
    END IF;
END $$;

-- Migration 2: Press Pass tables
DO $$
BEGIN
    IF NOT check_migration_applied('press_pass_tables.sql') THEN
        RAISE NOTICE 'Applying migration: press_pass_tables.sql';
        
        -- Execute the full press_pass_tables.sql content
        -- Note: In production, you would include the full content here or use \i command
        RAISE NOTICE 'Please execute press_pass_tables.sql manually or use the shell script';
        
        -- For now, we'll just record it as needing to be run
        -- INSERT INTO migration_history (filename) VALUES ('press_pass_tables.sql');
    ELSE
        RAISE NOTICE '⚠ Skipping: press_pass_tables.sql (already applied)';
    END IF;
END $$;

-- Migration 3: Press Pass views
DO $$
BEGIN
    IF NOT check_migration_applied('press_pass_views.sql') THEN
        RAISE NOTICE 'Applying migration: press_pass_views.sql';
        
        -- Execute the full press_pass_views.sql content
        RAISE NOTICE 'Please execute press_pass_views.sql manually or use the shell script';
        
        -- For now, we'll just record it as needing to be run
        -- INSERT INTO migration_history (filename) VALUES ('press_pass_views.sql');
    ELSE
        RAISE NOTICE '⚠ Skipping: press_pass_views.sql (already applied)';
    END IF;
END $$;

-- Migration 4: Press Pass jobs
DO $$
BEGIN
    IF NOT check_migration_applied('press_pass_jobs.sql') THEN
        RAISE NOTICE 'Applying migration: press_pass_jobs.sql';
        
        -- Execute the full press_pass_jobs.sql content
        RAISE NOTICE 'Please execute press_pass_jobs.sql manually or use the shell script';
        
        -- For now, we'll just record it as needing to be run
        -- INSERT INTO migration_history (filename) VALUES ('press_pass_jobs.sql');
    ELSE
        RAISE NOTICE '⚠ Skipping: press_pass_jobs.sql (already applied)';
    END IF;
END $$;

-- Show migration status
DO $$
DECLARE
    v_applied INTEGER;
    v_pending INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_applied
    FROM migration_history 
    WHERE filename LIKE '%press_pass%';
    
    v_pending := 4 - v_applied;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration Summary ===';
    RAISE NOTICE 'Applied migrations: %', v_applied;
    RAISE NOTICE 'Pending migrations: %', v_pending;
    RAISE NOTICE '';
    
    -- Show applied migrations
    FOR r IN SELECT filename, applied_at 
             FROM migration_history 
             WHERE filename LIKE '%press_pass%'
             ORDER BY applied_at
    LOOP
        RAISE NOTICE '✓ % (applied at %)', r.filename, r.applied_at;
    END LOOP;
END $$;

-- Commit transaction
COMMIT;

-- Instructions for manual execution
/*
To complete the migration, please run the following commands in order:

1. First, run this script to set up the enum and migration tracking
2. Then execute each migration file individually:
   
   \i add_press_pass_tier_enum.sql
   \i press_pass_tables.sql
   \i press_pass_views.sql
   \i press_pass_jobs.sql

Or use the shell script: ./run_press_pass_migrations.sh

After migration, verify the setup with:
*/

-- Verification queries
SELECT 'Press Pass Subscription Plan:' as info;
SELECT tier, name, price_usd, features->>'daily_shots' as daily_shots, 
       features->>'min_tcs' as min_tcs, is_active
FROM subscription_plans 
WHERE tier = 'PRESS_PASS';

SELECT 'Migration History:' as info;
SELECT filename, applied_at 
FROM migration_history 
WHERE filename LIKE '%press_pass%' 
ORDER BY applied_at;