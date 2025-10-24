-- BITTEN v2.0 Master Schema Initialization
-- Execute all schema files in correct dependency order
-- Run with: psql -U bitten_user -d bitten_db -f 99_all_tables.sql

-- Display banner
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║         BITTEN v2.0 PostgreSQL Schema Installation            ║'
\echo '║                                                                ║'
\echo '║  Bot-Integrated Tactical Trading Engine/Network               ║'
\echo '║  Production Schema - PostgreSQL + TimescaleDB                 ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''

-- Enable required extensions
\echo '→ Enabling PostgreSQL extensions...'
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
\echo '✓ Extensions enabled'
\echo ''

-- 01: Users table (no dependencies)
\echo '→ Creating users table...'
\i 01_users.sql
\echo '✓ Users table created'
\echo ''

-- 02: Signals table (no dependencies)
\echo '→ Creating signals table...'
\i 02_signals.sql
\echo '✓ Signals table created'
\echo ''

-- 03: Fires table (depends on users, signals)
\echo '→ Creating fires table...'
\i 03_fires.sql
\echo '✓ Fires table created'
\echo ''

-- 04: Positions table (depends on fires, users)
\echo '→ Creating positions table...'
\i 04_positions.sql
\echo '✓ Positions table created'
\echo ''

-- 05: Signal outcomes table (depends on signals) + TimescaleDB hypertable
\echo '→ Creating signal_outcomes table with TimescaleDB...'
\i 05_signal_outcomes.sql
\echo '✓ Signal outcomes table created with time-series optimization'
\echo ''

-- 06: EA instances table (depends on users)
\echo '→ Creating ea_instances table...'
\i 06_ea_instances.sql
\echo '✓ EA instances table created'
\echo ''

-- 07: Missions table (depends on signals)
\echo '→ Creating missions table...'
\i 07_missions.sql
\echo '✓ Missions table created'
\echo ''

-- Verify installation
\echo '→ Verifying schema installation...'
\echo ''
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║                  Schema Installation Complete                  ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''
\echo 'Tables created:'
\echo '  ✓ users           - User accounts and tier management'
\echo '  ✓ signals         - Elite Guard generated signals'
\echo '  ✓ fires           - Fire command execution tracking'
\echo '  ✓ positions       - MT5 position tracking'
\echo '  ✓ signal_outcomes - Time-series outcome tracking (TimescaleDB)'
\echo '  ✓ ea_instances    - EA heartbeat monitoring'
\echo '  ✓ missions        - User mission briefings'
\echo ''
\echo 'Next steps:'
\echo '  1. Create database user: CREATE USER bitten_app WITH PASSWORD ''your_password'';'
\echo '  2. Grant permissions: GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;'
\echo '  3. Update connection string in application config'
\echo '  4. Run migrations for data import from SQLite'
\echo ''
