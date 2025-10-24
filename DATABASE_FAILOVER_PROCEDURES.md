# BITTEN v2.0 Database Failover Procedures

**Version**: 1.0
**Date**: October 8, 2025
**Purpose**: Operational procedures for database recovery and failover

---

## 🗄️ Database Architecture

**Primary Database**: PostgreSQL 15.14
- **Host**: localhost
- **Port**: 5433
- **Database**: bitten_v2
- **User**: bitten_admin
- **Connection Pooler**: pgbouncer (port 6432)

**Backup Database**: SQLite (v1 archive)
- **Location**: `/root/HydraX-v2/bitten.db`
- **Purpose**: Rollback source, historical reference
- **Status**: Read-only after migration

**Read Mirror**: Firestore
- **Project**: bitten-production
- **Purpose**: Client-side read access, analytics
- **Sync**: Hourly via analytics_worker
- **Authority**: PostgreSQL (server-side only)

---

## 🚨 Database Failure Scenarios

### Scenario 1: PostgreSQL Connection Pool Exhaustion

**Symptoms:**
```
psycopg2.OperationalError: FATAL: sorry, too many clients already
```

**Root Cause**: Too many active connections (default limit: 100)

**Immediate Actions**:
```bash
# Check active connections
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT COUNT(*) as active_connections,
       max_conn as max_connections
FROM pg_stat_activity,
     (SELECT setting::int as max_conn FROM pg_settings WHERE name='max_connections') mc
GROUP BY max_conn;
EOF

# Identify long-running queries
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT pid, usename, application_name, state, query, now() - query_start as duration
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC
LIMIT 10;
EOF

# Kill idle connections older than 10 minutes
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND now() - state_change > interval '10 minutes'
AND pid != pg_backend_pid();
EOF
```

**Short-Term Fix**:
```bash
# Increase max_connections (requires restart)
sudo -u postgres psql -p 5433 <<EOF
ALTER SYSTEM SET max_connections = 200;
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql@15-main

# Verify new limit
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SHOW max_connections;"
```

**Long-Term Prevention**:
- Use connection pooler (pgbouncer) for all application connections
- Set `pool_size=20` and `max_overflow=10` in SQLAlchemy
- Implement connection timeout (30 seconds)
- Add connection pool monitoring to dashboards

---

### Scenario 2: Database Corruption

**Symptoms:**
```
ERROR: invalid page in block X of relation Y
ERROR: could not read block X in file "base/12345/67890": read only 0 of 8192 bytes
```

**Immediate Actions**:
```bash
# 1. Stop all services writing to database
pm2 stop fire_service
pm2 stop api_server
pm2 stop analytics_worker

# 2. Check database integrity
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
-- Check for corruption in all tables
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        BEGIN
            EXECUTE 'SELECT COUNT(*) FROM ' || quote_ident(r.tablename);
            RAISE NOTICE 'Table % is OK', r.tablename;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Table % is CORRUPTED: %', r.tablename, SQLERRM;
        END;
    END LOOP;
END $$;
EOF
```

**Recovery Options**:

**Option A: Restore from Latest Backup** (Recommended if < 24 hours old)
```bash
# 1. Stop PostgreSQL
sudo systemctl stop postgresql@15-main

# 2. Backup corrupted database
sudo -u postgres mv /var/lib/postgresql/15/main /var/lib/postgresql/15/main_corrupted_$(date +%Y%m%d)

# 3. Restore from backup
sudo -u postgres pg_basebackup -h localhost -p 5433 -D /var/lib/postgresql/15/main -U bitten_admin --wal-method=stream

# 4. Start PostgreSQL
sudo systemctl start postgresql@15-main

# 5. Verify restoration
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT COUNT(*) FROM users;"
```

**Option B: Re-import from SQLite** (If no recent PostgreSQL backup)
```bash
# 1. Create new clean database
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d postgres <<EOF
DROP DATABASE IF EXISTS bitten_v2_new;
CREATE DATABASE bitten_v2_new;
EOF

# 2. Recreate schema
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2_new < /root/HydraX-v2/db/schema/99_all_tables.sql

# 3. Re-run migration
cd /root/HydraX-v2/migration
python3 migrate_v1_to_v2.py --skip-clear

# 4. Validate data
python3 /root/HydraX-v2/tests/integration/validate_migration.py

# 5. Swap databases
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d postgres <<EOF
ALTER DATABASE bitten_v2 RENAME TO bitten_v2_corrupted;
ALTER DATABASE bitten_v2_new RENAME TO bitten_v2;
EOF

# 6. Restart services
pm2 restart fire_service api_server analytics_worker
```

---

### Scenario 3: Disk Space Exhaustion

**Symptoms:**
```
ERROR: could not extend file "base/12345/67890": No space left on device
HINT: Check free disk space.
```

**Immediate Actions**:
```bash
# Check disk usage
df -h /var/lib/postgresql

# Find largest database objects
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF
```

**Emergency Cleanup**:
```bash
# 1. Archive old data
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
-- Archive signals older than 90 days
COPY (SELECT * FROM signals WHERE created_at < NOW() - INTERVAL '90 days')
TO '/tmp/archived_signals.csv' CSV HEADER;

DELETE FROM signals WHERE created_at < NOW() - INTERVAL '90 days';

-- Vacuum to reclaim space
VACUUM FULL signals;
EOF

# 2. Clean up WAL files
sudo -u postgres pg_archivecleanup /var/lib/postgresql/15/main/pg_wal 000000010000000000000010

# 3. Check recovered space
df -h /var/lib/postgresql
```

**Long-Term Prevention**:
- Set up automated archival of data > 90 days old
- Configure WAL archiving to separate disk
- Monitor disk usage (alert at 70% full)
- Implement table partitioning for high-volume tables (signals, fires, position_events)

---

### Scenario 4: PostgreSQL Service Crash

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
Is the server running on host "localhost" (127.0.0.1) and accepting TCP/IP connections on port 5433?
```

**Diagnosis**:
```bash
# Check service status
sudo systemctl status postgresql@15-main

# Check logs
sudo journalctl -u postgresql@15-main -n 100 --no-pager

# Check for crashed PostgreSQL processes
ps aux | grep postgres
```

**Resolution**:
```bash
# 1. Attempt normal restart
sudo systemctl restart postgresql@15-main

# 2. If restart fails, check port conflict
sudo lsof -i:5433

# 3. If corrupted, rebuild from backup (see Scenario 2)

# 4. Verify service running
sudo systemctl status postgresql@15-main

# 5. Test connection
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT 1;"
```

**Post-Recovery**:
```bash
# Restart all BITTEN services
pm2 restart all

# Verify database connectivity from each service
pm2 logs api_server --lines 20 | grep "Database connected"
pm2 logs fire_service --lines 20 | grep "Database connected"
pm2 logs analytics_worker --lines 20 | grep "Database connected"
```

---

### Scenario 5: Firestore Sync Failure

**Symptoms:**
- Firestore data stale (> 2 hours old)
- analytics_worker logs show authentication errors
- Mobile app shows outdated signals

**Root Cause**: Firestore credentials expired or quota exceeded

**Diagnosis**:
```bash
# Check analytics_worker logs
pm2 logs analytics_worker --lines 50 | grep -i firestore

# Test Firestore connectivity
python3 <<EOF
import firebase_admin
from firebase_admin import credentials, firestore

try:
    cred = credentials.Certificate('/root/HydraX-v2/firebase-credentials.json')
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Test read
    doc = db.collection('signals').limit(1).get()
    print(f"✅ Firestore connected: {len(doc)} document(s) found")

    firebase_admin.delete_app(app)
except Exception as e:
    print(f"❌ Firestore connection failed: {e}")
EOF
```

**Resolution**:
```bash
# 1. Verify credentials file exists and is valid
ls -lh /root/HydraX-v2/firebase-credentials.json

# 2. Regenerate credentials from Firebase Console if needed
# (Download new service account key)

# 3. Update environment variable
export FIREBASE_CREDENTIALS=/root/HydraX-v2/firebase-credentials.json

# 4. Restart analytics_worker
pm2 restart analytics_worker

# 5. Force full sync
curl -X POST http://localhost:8888/api/internal/firestore/sync_all
```

**Fallback**: Disable Firestore mirroring temporarily
```bash
# Set environment flag
export FIRESTORE_ENABLED=false

# Restart services
pm2 restart analytics_worker

# Users will use PostgreSQL for reads (API server handles this)
```

---

## 🔄 Database Backup Strategy

### Automated Backups

**Daily Full Backup** (Cron: 2 AM UTC)
```bash
#!/bin/bash
# /root/HydraX-v2/scripts/backup_database.sh

BACKUP_DIR="/root/HydraX-v2/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bitten_v2_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
PGPASSWORD='bitten_secure_2025' pg_dump \
    -h localhost \
    -p 5433 \
    -U bitten_admin \
    -d bitten_v2 \
    -F c \
    -f "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Verify backup size
SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
echo "Backup created: ${BACKUP_FILE}.gz ($SIZE)"

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# aws s3 cp "${BACKUP_FILE}.gz" s3://bitten-backups/postgresql/
```

**Add to crontab**:
```bash
0 2 * * * /root/HydraX-v2/scripts/backup_database.sh >> /var/log/bitten_backup.log 2>&1
```

### Point-in-Time Recovery (PITR)

**Enable WAL Archiving** (in postgresql.conf):
```conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/15/wal_archive/%f'
archive_timeout = 300  # 5 minutes
```

**Restore to Specific Timestamp**:
```bash
# 1. Stop PostgreSQL
sudo systemctl stop postgresql@15-main

# 2. Restore base backup
sudo -u postgres pg_basebackup -D /var/lib/postgresql/15/main_restore -F tar -z

# 3. Create recovery.conf
cat > /var/lib/postgresql/15/main_restore/recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/15/wal_archive/%f %p'
recovery_target_time = '2025-10-08 14:30:00 UTC'
recovery_target_action = 'promote'
EOF

# 4. Start PostgreSQL in recovery mode
sudo -u postgres pg_ctl -D /var/lib/postgresql/15/main_restore start

# 5. Verify recovery timestamp
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT pg_last_wal_replay_lsn();"
```

---

## 📊 Database Health Monitoring

**Real-Time Monitoring Script**:
```bash
#!/bin/bash
# /root/HydraX-v2/scripts/db_health_check.sh

echo "=== BITTEN v2.0 Database Health Check ==="
echo "Timestamp: $(date)"

# 1. Check PostgreSQL service
if systemctl is-active --quiet postgresql@15-main; then
    echo "✅ PostgreSQL service: RUNNING"
else
    echo "❌ PostgreSQL service: STOPPED"
fi

# 2. Check connection count
CONN_COUNT=$(PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'bitten_v2';" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Active connections: $CONN_COUNT"
    if [ $CONN_COUNT -gt 80 ]; then
        echo "⚠️  Connection count high (>80)"
    fi
else
    echo "❌ Cannot query connection count"
fi

# 3. Check disk space
DISK_USAGE=$(df -h /var/lib/postgresql | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 70 ]; then
    echo "✅ Disk usage: ${DISK_USAGE}%"
elif [ $DISK_USAGE -lt 85 ]; then
    echo "⚠️  Disk usage: ${DISK_USAGE}% (warning threshold)"
else
    echo "❌ Disk usage: ${DISK_USAGE}% (critical threshold)"
fi

# 4. Check replication lag (if replica configured)
# LAG=$(PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -t -c "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()));" 2>/dev/null)

# 5. Check table row counts
echo ""
echo "Table row counts:"
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT
    schemaname,
    tablename,
    n_live_tup as rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;
EOF
```

**Add to monitoring dashboard** (Prometheus/Grafana):
- Connection pool usage
- Query latency (P50, P95, P99)
- Table sizes
- Disk I/O
- Replication lag

---

## 📞 Escalation Matrix

| Issue Severity | Response Time | Contact | Action |
|----------------|---------------|---------|--------|
| P1 (Service Down) | < 15 min | DBA On-Call: +1-XXX-XXX-XXXX | Page immediately |
| P2 (Degraded) | < 1 hour | DevOps Slack: #bitten-database | Alert in channel |
| P3 (Minor) | < 4 hours | Create Jira ticket | Standard process |
| P4 (Info) | Next business day | Email: dba-team@company.com | Log for review |

**P1 Criteria**: Database completely unavailable, data corruption, unrecoverable service crash

---

**Last Updated**: October 8, 2025
**Maintained By**: Database Administration Team
**Review Frequency**: Quarterly
