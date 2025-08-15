# BITTEN Press Pass Manager - Database Setup Guide

This guide explains how to set up the database for the Press Pass Manager system.

## Prerequisites

1. PostgreSQL 12+ installed and running
2. Python 3.8+ with pip
3. Access to create databases and users in PostgreSQL

## Installation Steps

### 1. Install Database Dependencies

```bash
pip install -r requirements_db.txt
```

### 2. Create Database and User

Connect to PostgreSQL as a superuser and run:

```sql
-- Create database user
CREATE USER bitten_app WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE bitten_db OWNER bitten_app;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bitten_db TO bitten_app;
```

### 3. Set Up Environment Variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set your database credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bitten_db
DB_USER=bitten_app
DB_PASSWORD=your_secure_password_here
```

### 4. Run Database Migrations

Execute the SQL migration file to create the required tables:

```bash
psql -U bitten_app -d bitten_db -f migrations/press_pass_tables.sql
```

### 5. Test Database Connection

Run the test script to verify everything is working:

```bash
python test_press_pass_db.py
```

## Database Schema Overview

The Press Pass Manager uses the following main tables:

### `press_pass_weekly_limits`
- Tracks weekly limits for Press Pass account creation (max 200/week)
- Automatically resets each Monday

### `press_pass_shadow_stats`
- Tracks XP for Press Pass users
- XP resets nightly at midnight UTC
- Only current day's XP is preserved when upgrading to paid tier

### `trade_logs_all`
- Comprehensive trade logging for all users
- Includes Press Pass demo account activations
- Tracks tier upgrades

### `conversion_signal_tracker`
- Analytics for Press Pass to paid tier conversions
- Tracks conversion rates and user journey

## Key Features

### Weekly Limit Management
- Maximum 200 Press Pass accounts per week
- Automatic tracking and enforcement
- Monday-to-Sunday week cycle

### XP Reset System
- Press Pass users' XP resets nightly at midnight UTC
- Only current day's XP is preserved when upgrading
- 50 XP enlistment bonus when upgrading to paid tier

### Database Connection Pooling
- Async connection pool for high performance
- Configurable pool size (default: 10-20 connections)
- Automatic connection management

### Error Handling
- Graceful fallbacks for database errors
- Transaction support for data integrity
- Comprehensive logging

## Maintenance

### Daily Tasks
- XP resets run automatically at midnight UTC
- Monitor `press_pass_shadow_stats` for active users

### Weekly Tasks
- Check `press_pass_weekly_limits` for usage patterns
- Review conversion rates in `conversion_signal_tracker`

### Database Functions

The system includes several PostgreSQL functions:

- `check_weekly_press_pass_limit()` - Check if weekly limit is reached
- `increment_weekly_press_pass_count()` - Increment weekly counter
- `reset_daily_press_pass_xp()` - Reset all Press Pass users' XP

## Troubleshooting

### Connection Issues
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify credentials in `.env` file
3. Test connection: `psql -U bitten_app -d bitten_db -c "SELECT 1"`

### Migration Issues
1. Check user has CREATE privileges
2. Run migrations as database owner
3. Check migration history table

### Performance Issues
1. Monitor connection pool usage
2. Check for slow queries in PostgreSQL logs
3. Ensure indexes are being used

## Security Considerations

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use strong passwords** - Minimum 16 characters
3. **Limit database access** - Only from application servers
4. **Regular backups** - Set up automated PostgreSQL backups
5. **Monitor access logs** - Check for unauthorized access attempts

## Support

For issues or questions:
1. Check application logs in `/var/log/bitten/`
2. Review PostgreSQL logs
3. Run test script for diagnostics