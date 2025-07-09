# Press Pass Migration Guide

This guide explains how to execute the Press Pass database migrations for the BITTEN trading platform.

## Overview

The Press Pass system introduces a free trial tier with the following features:
- 1 trade per day limit
- 60% minimum TCS (Trading Confidence Score)
- XP resets nightly at midnight UTC
- Comprehensive analytics and conversion tracking

## Migration Files

The migrations must be executed in this specific order:

1. **add_press_pass_tier_enum.sql** - Adds PRESS_PASS to database tier enums
2. **press_pass_tables.sql** - Creates core tables for trade logging and analytics
3. **press_pass_views.sql** - Creates analytics views and reporting functions
4. **press_pass_jobs.sql** - Sets up scheduled jobs and automation

## Prerequisites

- PostgreSQL database access with appropriate permissions
- Database user with CREATE TABLE, CREATE FUNCTION, and GRANT privileges
- Connection details for your database

## Migration Methods

### Method 1: Using the Shell Script (Recommended)

1. Set your database connection environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=bitten_db
export DB_USER=bitten_app
export DB_PASSWORD=your_password
```

2. Run the migration script:
```bash
cd /root/HydraX-v2/migrations
./run_press_pass_migrations.sh
```

The script will:
- Check for existing migrations to avoid duplicates
- Execute migrations in the correct order
- Show progress and any errors
- Display a summary of applied migrations

### Method 2: Manual SQL Execution

1. Connect to your PostgreSQL database:
```bash
psql -h localhost -p 5432 -d bitten_db -U bitten_app
```

2. Create the migration history table:
```sql
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

3. Execute each migration file in order:
```sql
\i add_press_pass_tier_enum.sql
\i press_pass_tables.sql
\i press_pass_views.sql
\i press_pass_jobs.sql
```

### Method 3: Using the SQL Runner Script

Execute the `run_press_pass_migrations.sql` file which includes basic migration tracking:
```bash
psql -h localhost -p 5432 -d bitten_db -U bitten_app -f run_press_pass_migrations.sql
```

## Post-Migration Setup

### 1. Schedule the Cron Jobs

The Press Pass system requires three scheduled jobs:

**Using pg_cron extension:**
```sql
SELECT cron.schedule('reset-press-pass-xp', '0 0 * * *', 'SELECT job_nightly_xp_reset();');
SELECT cron.schedule('xp-expiry-warnings', '0 23 * * *', 'SELECT job_xp_expiry_warnings();');
SELECT cron.schedule('engagement-signals', '0 */4 * * *', 'SELECT job_update_engagement_signals();');
```

**Using system cron:**
Add to crontab:
```bash
0 0 * * * psql -U bitten_app -d bitten_db -c "SELECT job_nightly_xp_reset();"
0 23 * * * psql -U bitten_app -d bitten_db -c "SELECT job_xp_expiry_warnings();"
0 */4 * * * psql -U bitten_app -d bitten_db -c "SELECT job_update_engagement_signals();"
```

### 2. Verify the Migration

Check that Press Pass tier was added:
```sql
SELECT tier, name, price_usd, features, limits, is_active
FROM subscription_plans 
WHERE tier = 'PRESS_PASS';
```

Verify all tables were created:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('trade_logs_all', 'press_pass_shadow_stats', 'conversion_signal_tracker');
```

Check migration history:
```sql
SELECT filename, applied_at 
FROM migration_history 
WHERE filename LIKE '%press_pass%' 
ORDER BY applied_at;
```

## Key Tables Created

1. **trade_logs_all** - Comprehensive trade logging for all users
2. **press_pass_shadow_stats** - Shadow XP tracking that resets nightly
3. **conversion_signal_tracker** - Analytics for Press Pass to paid tier conversions
4. **press_pass_job_history** - Tracks scheduled job execution

## Key Views Created

- **v_press_pass_overview** - User overview with engagement status
- **v_press_pass_daily_metrics** - Daily performance metrics
- **v_conversion_funnel** - Conversion analytics
- **v_press_pass_hot_leads** - Users ready for conversion
- **v_press_pass_trading_patterns** - Trading behavior analysis

## Troubleshooting

### Migration Already Applied Error
If you see "already applied" warnings, this is normal - the script checks for duplicates.

### Permission Errors
Ensure your database user has appropriate permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;
```

### Connection Issues
Verify your database connection:
```bash
psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "SELECT version();"
```

## Rollback Instructions

To rollback the migrations:
```sql
-- Remove from migration history
DELETE FROM migration_history WHERE filename LIKE '%press_pass%';

-- Drop views
DROP VIEW IF EXISTS v_press_pass_overview CASCADE;
DROP VIEW IF EXISTS v_press_pass_daily_metrics CASCADE;
DROP VIEW IF EXISTS v_conversion_funnel CASCADE;
DROP VIEW IF EXISTS v_press_pass_hot_leads CASCADE;
DROP VIEW IF EXISTS v_press_pass_trading_patterns CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS get_press_pass_metrics CASCADE;
DROP FUNCTION IF EXISTS get_press_pass_journey CASCADE;
-- ... (drop other functions)

-- Drop tables
DROP TABLE IF EXISTS press_pass_job_history CASCADE;
DROP TABLE IF EXISTS conversion_signal_tracker CASCADE;
DROP TABLE IF EXISTS press_pass_shadow_stats CASCADE;
DROP TABLE IF EXISTS trade_logs_all CASCADE;

-- Remove PRESS_PASS from subscription_plans
DELETE FROM subscription_plans WHERE tier = 'PRESS_PASS';
```

## Support

For issues or questions about the Press Pass migration:
1. Check the migration logs in `press_pass_job_history` table
2. Review PostgreSQL error logs
3. Ensure all prerequisites are met