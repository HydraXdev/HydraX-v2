# BITTEN v2.0 PostgreSQL Schema

Complete production database schema for BITTEN trading system migration from SQLite to PostgreSQL + TimescaleDB.

## Quick Start

```bash
# Install TimescaleDB extension (run as postgres superuser)
psql -U postgres -c "CREATE EXTENSION timescaledb CASCADE;"

# Create database and run schema
createdb -U postgres bitten_db
cd /root/HydraX-v2/db/schema
psql -U postgres -d bitten_db -f 99_all_tables.sql
```

## Schema Files

| File | Lines | Description |
|------|-------|-------------|
| `01_users.sql` | 43 | User accounts, tier system, fire mode configuration |
| `02_signals.sql` | 34 | Elite Guard generated signals with SMC patterns |
| `03_fires.sql` | 42 | Fire command execution tracking |
| `04_positions.sql` | 36 | MT5 position tracking with P&L |
| `05_signal_outcomes.sql` | 40 | Time-series outcome tracking (TimescaleDB) |
| `06_ea_instances.sql` | 40 | EA heartbeat monitoring |
| `07_missions.sql` | 27 | User mission briefings |
| `99_all_tables.sql` | 93 | Master installation script |

**Total:** 355 lines

## Database Structure

```
users (core accounts)
├── fires (execution tracking)
│   └── positions (MT5 trades)
├── ea_instances (EA monitoring)
└── (user_id references)

signals (Elite Guard)
├── fires (which signals were fired)
├── missions (user briefings)
└── signal_outcomes (performance tracking - TimescaleDB)
```

## Key Features

### 1. User Management
- Tier system: RECRUIT, FANG, COMMANDER, COMMANDER+
- Fire modes: MANUAL, SEMI_AUTO, FULL_AUTO
- BITMODE hybrid position management toggle
- Multi-broker account support

### 2. Signal Generation
- Elite Guard SMC pattern detection
- Total Confluence Score (TCS) 0-100%
- CITADEL Shield validation 0-10
- Session tracking (LONDON, NY, ASIAN, OVERLAP)
- Pattern types: LIQUIDITY_SWEEP_REVERSAL, ORDER_BLOCK_BOUNCE, FAIR_VALUE_GAP_FILL, VCB_BREAKOUT, SWEEP_RETURN, MOMENTUM_BURST

### 3. Execution Tracking
- Fire command lifecycle: QUEUED → SENT → FILLED
- Real-time risk management (2% or 5%)
- EA confirmation integration
- Multi-terminal support

### 4. Performance Analytics
- TimescaleDB hypertable for signal outcomes
- Automatic 90-day data retention
- Real-time win rate tracking
- Pattern performance analytics
- ML training data pipeline

### 5. EA Monitoring
- Heartbeat freshness tracking (120-second threshold)
- Active EA view (last_seen < 2 minutes)
- Version tracking
- User-to-EA mapping

## Indexes & Performance

All tables include:
- Primary key indexes
- Foreign key indexes
- Composite indexes for common queries
- Partial indexes for filtered queries

TimescaleDB optimization:
- Hypertable for `signal_outcomes`
- Automatic chunk management
- Retention policy (90 days)
- Time-series compression

## Triggers

- `update_updated_at_column()`: Auto-update timestamps on users, fires, ea_instances

## Views

- `active_ea_instances`: EAs with heartbeat < 2 minutes ago

## Data Migration

To migrate from SQLite:

```bash
# Export from SQLite
sqlite3 /root/HydraX-v2/bitten.db ".dump users" > users_dump.sql

# Import to PostgreSQL (after schema creation)
psql -U bitten_app -d bitten_db -f users_dump.sql
```

## Application Integration

Update connection string:

```python
# Old SQLite
DATABASE_URL = "sqlite:///bitten.db"

# New PostgreSQL
DATABASE_URL = "postgresql://bitten_app:password@localhost:5432/bitten_db"
```

## Production Checklist

- [ ] PostgreSQL 14+ installed
- [ ] TimescaleDB extension enabled
- [ ] Database created: `bitten_db`
- [ ] Schema installed: `psql -f 99_all_tables.sql`
- [ ] Application user created with permissions
- [ ] Connection string updated in config
- [ ] Data migrated from SQLite
- [ ] Indexes verified: `\di` in psql
- [ ] TimescaleDB hypertable confirmed: `SELECT * FROM timescaledb_information.hypertables;`

## Maintenance

```sql
-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size DESC;

-- Check TimescaleDB chunks
SELECT * FROM timescaledb_information.chunks WHERE hypertable_name = 'signal_outcomes';

-- Verify retention policy
SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_retention';

-- Check active EAs
SELECT * FROM active_ea_instances;
```

## Support

For schema issues or migration questions, see:
- `/root/HydraX-v2/CLAUDE.md` - System documentation
- `/root/HydraX-v2/ARCHITECTURE.md` - Technical architecture
