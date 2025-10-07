# HYDRASOCKET v1 Rollback Playbook

## Emergency Rollback Decision Tree

### Rollback Triggers

- **P0 (Immediate)**: Service won't start, critical API failures
- **P1 (Within 5min)**: Performance degradation >50%, high error rates
- **P2 (Within 15min)**: Non-critical feature failures, minor bugs

### Decision Matrix

| Issue                    | Rollback    | Fix Forward     |
| ------------------------ | ----------- | --------------- |
| Service crash on startup | ✅ Rollback | ❌              |
| Schema migration failure | ✅ Rollback | ❌              |
| API error rate >5%       | ✅ Rollback | ❌              |
| Performance degradation  | ✅ Rollback | ⚠️ Case by case |
| Minor UI bugs            | ❌          | ✅ Fix forward  |

## Rollback Procedures

### 1. Code Rollback

```bash
# Identify last known good version
git log --oneline -10

# Rollback to previous tag
git checkout router-v1.0.0-prev

# Verify checkout
git describe --tags
```

### 2. Database Rollback (if migrations applied)

```bash
# Check if migration can be reversed
ls -la migrations/

# Apply rollback migration (if exists)
sqlite3 event_bus/bitten_events.db < migrations/001_add_sequencing_rollback.sql

# OR restore from backup
cp backups/bitten_events_$(date +%Y%m%d).db event_bus/bitten_events.db
```

### 3. Service Rollback

```bash
# Stop current service
pm2 stop hydrasocket-router
# OR
systemctl stop hydrasocket

# Restart with previous version
pm2 start ecosystem.config.js
# OR
systemctl start hydrasocket

# Verify rollback
curl http://localhost:8888/api/health
```

### 4. Artifact Pinning

```bash
# Pin to specific version in deployment config
echo "HYDRASOCKET_VERSION=router-v1.0.0-prev" > /opt/hydrasocket/.version

# Update deployment annotations
curl -X POST http://grafana:3000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{"text":"Rolled back to router-v1.0.0-prev","tags":["rollback","hydrasocket"]}'
```

## Schema Migration Rollback

### Safe Migration Rollback

```sql
-- Example rollback for 001_add_sequencing.sql
BEGIN TRANSACTION;

-- Remove columns (if possible)
ALTER TABLE events DROP COLUMN seq;
ALTER TABLE events DROP COLUMN account_id;
ALTER TABLE events DROP COLUMN ingest_time;

-- Drop tables
DROP TABLE account_sequences;
DROP TABLE idempotency;
DROP TABLE api_keys;

-- Drop indexes
DROP INDEX IF EXISTS idx_events_account_seq;
DROP INDEX IF EXISTS idx_events_account_ingest_time;

COMMIT;
```

### Unsafe Migration Recovery

```bash
# If schema cannot be rolled back, restore from backup
systemctl stop hydrasocket

# Restore database backup
cp backups/bitten_events_pre_migration.db event_bus/bitten_events.db

# Verify data integrity
python3 tools/verify_database_integrity.py

systemctl start hydrasocket
```

## Rollback Verification

### Health Checks

```bash
# Service health
curl http://localhost:8888/healthz

# Schema verification
EXPECTED_HASH=$(sha256sum openapi/openapi.yaml | cut -d' ' -f1)
ACTUAL_HASH=$(curl -s http://localhost:8888/api/health | jq -r .schema_sha256)

if [ "$EXPECTED_HASH" = "$ACTUAL_HASH" ]; then
  echo "✅ Schema hash matches"
else
  echo "❌ Schema hash mismatch - verify version"
fi
```

### Functionality Tests

```bash
# API endpoints
python3 tests/smoke/test_api_endpoints.py

# WebSocket connections
python3 tests/smoke/test_ws_connection.py

# Event processing
python3 tests/smoke/test_event_flow.py
```

## Recovery Time Objectives

| Rollback Type | Target RTO | Max RTO    |
| ------------- | ---------- | ---------- |
| Code only     | 2 minutes  | 5 minutes  |
| Code + DB     | 5 minutes  | 15 minutes |
| Full restore  | 15 minutes | 30 minutes |

## Post-Rollback Actions

### 1. Incident Documentation

```bash
# Create incident report
echo "Rollback completed at $(date)" >> /var/log/hydrasocket/incidents.log
echo "Rolled back from: $(git describe --tags HEAD~1)" >> /var/log/hydrasocket/incidents.log
echo "Rolled back to: $(git describe --tags)" >> /var/log/hydrasocket/incidents.log
```

### 2. Monitoring

```bash
# Monitor for 30 minutes post-rollback
watch -n 60 'curl -s http://localhost:8888/api/health | jq'

# Check error rates
grep -c "ERROR" /var/log/hydrasocket/err.log | tail -10
```

### 3. Communication

- Notify trading operations team
- Update incident tracking system
- Schedule post-mortem (if P0/P1 incident)

## Prevention Strategies

### Pre-Deployment

- Always test migrations on copy of production data
- Verify rollback scripts before deployment
- Maintain backup retention policy (7 days minimum)

### Deployment Automation

- Automated health checks post-deployment
- Automatic rollback triggers
- Blue/green deployment strategy

### Monitoring

- Real-time alerting on performance degradation
- Schema drift detection
- Database integrity monitoring
