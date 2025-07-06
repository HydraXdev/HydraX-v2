# 🗄️ BITTEN Database Setup

This directory contains the PostgreSQL database schema and setup instructions for BITTEN.

## 📋 Prerequisites

- PostgreSQL 12+ installed
- Python 3.8+ with pip
- Required Python packages: `sqlalchemy`, `psycopg2-binary`, `alembic`

## 🚀 Quick Setup

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql
```

### 2. Create Database and User

```bash
# Login as postgres superuser
sudo -u postgres psql

# Create database
CREATE DATABASE bitten_production;

# Create user
CREATE USER bitten_app WITH PASSWORD 'your_secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bitten_production TO bitten_app;

# Enable extensions
\c bitten_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

# Exit
\q
```

### 3. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bitten_production
DB_USER=bitten_app
DB_PASSWORD=your_secure_password_here
DB_SSL_MODE=prefer  # Use 'require' for production

# Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Debug
DB_ECHO=false  # Set to true for SQL debugging
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Run the schema creation
psql -U bitten_app -d bitten_production -f database/schema.sql

# Or use Python
python -c "from src.database.connection import init_database; init_database()"
```

## 🔄 Database Migrations

We use Alembic for database migrations.

### Initialize Alembic (first time only)

```bash
alembic init migrations
```

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new feature"

# Or create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade +1

# View current revision
alembic current

# View history
alembic history
```

### Rollback Migrations

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123
```

## 📊 Database Schema Overview

### Core Tables

1. **users** - User authentication and subscription data
2. **user_profiles** - Extended user information, XP, stats
3. **trades** - All trading history
4. **risk_sessions** - Daily risk tracking
5. **xp_transactions** - XP earning/spending history
6. **achievements** - Achievement definitions
7. **news_events** - Economic calendar data
8. **subscription_plans** - Tier definitions
9. **payment_transactions** - Payment history

### Key Relationships

```
users (1) ─── (1) user_profiles
  │
  ├─── (many) trades
  ├─── (many) risk_sessions
  ├─── (many) xp_transactions
  └─── (many) user_achievements
```

## 🔧 Common Operations

### Connect to Database

```python
from src.database.connection import get_db_manager

# Get database session
db = get_db_manager()
with db.session_scope() as session:
    # Your queries here
    users = session.query(User).all()
```

### Create a New User

```python
from src.database.models import User, UserProfile
from src.database.connection import get_db_manager

db = get_db_manager()
with db.session_scope() as session:
    # Create user
    user = User(
        telegram_id=123456789,
        username="bitten_trader",
        tier="NIBBLER"
    )
    session.add(user)
    session.flush()  # Get user_id
    
    # Create profile
    profile = UserProfile(
        user_id=user.user_id,
        referral_code=f"REF_{user.user_id}"
    )
    session.add(profile)
    session.commit()
```

### Query Examples

```python
# Get user by telegram ID
user = session.query(User).filter_by(telegram_id=123456789).first()

# Get user's trades
trades = session.query(Trade).filter_by(
    user_id=user.user_id,
    status='closed'
).order_by(Trade.close_time.desc()).limit(10).all()

# Get today's risk session
from datetime import date
risk_session = session.query(RiskSession).filter_by(
    user_id=user.user_id,
    session_date=date.today()
).first()

# Get leaderboard
from sqlalchemy import func
leaderboard = session.query(
    UserProfile.user_id,
    User.username,
    UserProfile.total_profit_usd
).join(User).order_by(
    UserProfile.total_profit_usd.desc()
).limit(10).all()
```

## 🔒 Security Best Practices

1. **Never commit passwords** to version control
2. **Use environment variables** for sensitive data
3. **Enable SSL** for production connections
4. **Limit user privileges** - bitten_app should not be superuser
5. **Regular backups** - Set up automated backups
6. **Monitor connections** - Watch for connection leaks

## 🚨 Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check listening ports
sudo netstat -plnt | grep postgres
```

### Permission Denied

```sql
-- Grant schema permissions
GRANT ALL ON SCHEMA public TO bitten_app;
GRANT ALL ON ALL TABLES IN SCHEMA public TO bitten_app;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
```

### Too Many Connections

```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Increase max connections (requires restart)
ALTER SYSTEM SET max_connections = 200;
```

## 📈 Performance Optimization

1. **Indexes** - Already created on foreign keys and common queries
2. **Connection pooling** - Configured in DatabaseManager
3. **Query optimization** - Use EXPLAIN ANALYZE for slow queries
4. **Partitioning** - Consider partitioning trades table by month
5. **Vacuum** - Set up regular VACUUM ANALYZE

## 🔄 Backup and Recovery

### Manual Backup

```bash
# Backup entire database
pg_dump -U bitten_app -h localhost bitten_production > backup_$(date +%Y%m%d).sql

# Backup specific tables
pg_dump -U bitten_app -h localhost bitten_production -t users -t trades > users_trades_backup.sql
```

### Restore from Backup

```bash
# Restore entire database
psql -U bitten_app -h localhost bitten_production < backup_20240107.sql

# Restore specific tables
psql -U bitten_app -h localhost bitten_production < users_trades_backup.sql
```

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * pg_dump -U bitten_app bitten_production > /backups/bitten_$(date +\%Y\%m\%d).sql
```

---

*Remember: The database is the heart of BITTEN. Treat it with respect, back it up regularly, and monitor its health constantly.*