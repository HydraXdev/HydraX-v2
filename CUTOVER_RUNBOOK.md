# BITTEN v2.0 Production Cutover Runbook

**Version**: 1.0
**Date**: October 8, 2025
**Estimated Duration**: 45-60 minutes
**Rollback Time**: < 5 minutes

---

## 🎯 Pre-Cutover Checklist

**24 Hours Before:**
- [ ] Notify all COMMANDER+ users of maintenance window
- [ ] Create complete backup of v1 SQLite database
- [ ] Export PostgreSQL schema and verify all tables exist
- [ ] Verify all 5 services compile without errors
- [ ] Run integration test suite (100% pass required)
- [ ] Verify rollback scripts tested and ready
- [ ] Confirm PostgreSQL disk space > 2x database size

**1 Hour Before:**
- [ ] Check all PM2 processes healthy in v1
- [ ] Verify EA connections fresh (< 30s heartbeat)
- [ ] Confirm no open positions (or document all)
- [ ] Create final v1 database backup
- [ ] Test database connection pooling (pgbouncer)
- [ ] Verify Firestore credentials valid

**T-Minus 30 Minutes:**
- [ ] Send final notification to users (system going down)
- [ ] Close Telegram bot to new commands
- [ ] Verify backup integrity (restore test)

---

## 🚀 Cutover Execution Steps

### Phase 1: Shutdown v1 System (T+0 to T+5 min)

**Step 1.1: Stop User-Facing Services** (T+0)
```bash
# Stop Telegram bot
pm2 stop bitten_production_bot

# Stop WebApp
pm2 stop webapp

# Stop dashboard
pm2 stop commander_throne

# Verify stopped
pm2 list | grep -E "bitten_production_bot|webapp|commander_throne"
```

**Expected Output**: All services showing "stopped" status
**Validation**: `curl http://localhost:8888/healthz` should fail

**Step 1.2: Stop Signal Processing** (T+2)
```bash
# Stop Elite Guard
pm2 stop elite_guard

# Stop signal relay
pm2 stop relay_to_telegram

# Stop signal processors
pm2 stop eg_signal_wrapper
pm2 stop signals_zmq_to_redis
pm2 stop signals_redis_to_webapp_fixed
```

**Expected Output**: No new signals generated
**Validation**: Check Redis stream length (should not increase)

**Step 1.3: Stop Fire Pipeline** (T+3)
```bash
# Stop command router
pm2 stop command_router

# Stop confirmation listener
pm2 stop confirm_listener_v207
```

**Expected Output**: ZMQ ports 5555, 5558 unbound
**Validation**: `ss -tulpen | grep -E ":(5555|5558)"` should return empty

**Step 1.4: Stop Infrastructure** (T+4)
```bash
# Stop telemetry bridge
pm2 stop zmq_telemetry_bridge_debug

# Stop analytics
pm2 stop canonical_tracker
pm2 stop ml_autofire_optimizer

# Verify all stopped
pm2 list
```

**Expected Output**: All v1 processes stopped
**Validation**: No BITTEN processes in `ps aux | grep bitten`

---

### Phase 2: Database Migration (T+5 to T+20 min)

**Step 2.1: Final Backup** (T+5)
```bash
cd /root/HydraX-v2/migration

# Create timestamped backup
BACKUP_FILE="bitten_v1_final_$(date +%Y%m%d_%H%M%S).db"
cp /root/HydraX-v2/bitten.db "backups/$BACKUP_FILE"

# Verify backup size
ls -lh "backups/$BACKUP_FILE"

# Test backup integrity
sqlite3 "backups/$BACKUP_FILE" "SELECT COUNT(*) FROM users;"
```

**Expected Output**: Backup file > 140MB, user count matches production
**Go/No-Go**: If backup fails or corrupted, **ABORT CUTOVER**

**Step 2.2: Run Migration** (T+7)
```bash
# Run full migration (all 9 tables)
python3 migrate_v1_to_v2.py 2>&1 | tee migration_output.log

# Monitor progress
tail -f migration_output.log
```

**Expected Duration**: 8-12 minutes for 147MB database
**Expected Output**:
```
✅ users                    12 →     12
✅ ea_instances              1 →      1
✅ signals                2076 →   2076
✅ missions               1543 →   1543
✅ fires                   892 →    892
✅ live_positions           12 →     12
✅ position_events         456 →    456
✅ xp_events              1234 →   1234
✅ signal_outcomes         892 →    892
```

**Validation Commands**:
```bash
# Check row counts match
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'fires', COUNT(*) FROM fires;
EOF

# Compare to v1
sqlite3 /root/HydraX-v2/bitten.db <<EOF
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'fires', COUNT(*) FROM fires;
EOF
```

**Go/No-Go**: Row counts must match exactly. If any mismatch > 1%, **STOP AND ROLLBACK**

**Step 2.3: Validate Data Integrity** (T+18)
```bash
# Run validation script
python3 /root/HydraX-v2/tests/integration/validate_migration.py

# Check critical relationships
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 <<EOF
-- Orphaned fires check (should be 0)
SELECT COUNT(*) FROM fires f
LEFT JOIN users u ON f.user_id = u.user_id
WHERE u.user_id IS NULL;

-- Orphaned missions check (should be 0)
SELECT COUNT(*) FROM missions m
LEFT JOIN signals s ON m.signal_id = s.signal_id
WHERE s.signal_id IS NULL;
EOF
```

**Expected Output**: 0 orphaned records
**Go/No-Go**: If orphaned records > 0, investigate before proceeding

---

### Phase 3: Deploy v2 Services (T+20 to T+35 min)

**Step 3.1: Install Dependencies** (T+20)
```bash
cd /root/HydraX-v2

# Install Python packages
pip3 install -r requirements_v2.txt

# Verify installations
python3 -c "import fastapi, uvicorn, sqlalchemy, pyzmq, firebase_admin; print('✅ All packages installed')"
```

**Step 3.2: Configure Environment** (T+22)
```bash
# Set environment variables
cat > /root/HydraX-v2/.env <<EOF
DATABASE_URL=postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
FIREBASE_CREDENTIALS=/root/HydraX-v2/firebase-credentials.json
LOG_LEVEL=INFO
ZMQ_GATEWAY_ROUTER_PORT=5555
ZMQ_GATEWAY_PULL_PORT=5556
ZMQ_SIGNAL_PUB_PORT=5557
ZMQ_CONFIRM_PULL_PORT=5558
ZMQ_MARKET_PUB_PORT=5560
API_SERVER_PORT=8888
ANALYTICS_PORT=8890
EOF

# Verify environment
source /root/HydraX-v2/.env
echo "DATABASE_URL set: $(echo $DATABASE_URL | grep -o 'postgresql.*' | cut -d@ -f2)"
```

**Step 3.3: Start Services in Order** (T+25)

**Service 1: zmq_gateway** (Foundation - start first)
```bash
pm2 start /root/HydraX-v2/services/zmq_gateway/main.py \
  --name zmq_gateway \
  --interpreter python3 \
  --max-memory-restart 500M \
  --restart-delay 3000

# Wait for port bindings
sleep 3
ss -tulpen | grep -E ":(5555|5556|5558|5560)"
```

**Expected Output**: All 4 ports bound (5555, 5556, 5558, 5560)
**Go/No-Go**: If ports not bound, check logs and fix before continuing

**Service 2: signal_engine** (Pattern detection)
```bash
pm2 start /root/HydraX-v2/services/signal_engine/main.py \
  --name signal_engine \
  --interpreter python3 \
  --max-memory-restart 1G \
  --restart-delay 3000

# Wait for initialization
sleep 5
pm2 logs signal_engine --lines 20 | grep "Pattern detectors loaded"
```

**Expected Output**: "6 pattern detectors loaded successfully"

**Service 3: fire_service** (Trade execution)
```bash
pm2 start /root/HydraX-v2/services/fire_service/main.py \
  --name fire_service \
  --interpreter python3 \
  --max-memory-restart 500M \
  --restart-delay 3000

# Verify startup
pm2 logs fire_service --lines 20 | grep "Risk calculator initialized"
```

**Expected Output**: "Risk calculator initialized", "BITMODE manager ready"

**Service 4: api_server** (User interface)
```bash
pm2 start /root/HydraX-v2/services/api_server/main.py \
  --name api_server \
  --interpreter python3 \
  --instances 2 \
  --exec-mode cluster \
  --max-memory-restart 1G \
  --restart-delay 3000

# Wait for HTTP server
sleep 5
curl -s http://localhost:8888/healthz | jq
```

**Expected Output**: `{"status": "healthy", "version": "2.0.0", "database": "connected"}`

**Service 5: analytics_worker** (Background jobs)
```bash
pm2 start /root/HydraX-v2/services/analytics_worker/main.py \
  --name analytics_worker \
  --interpreter python3 \
  --max-memory-restart 500M \
  --restart-delay 3000 \
  --cron-restart="0 * * * *"  # Restart hourly

# Verify job scheduler
pm2 logs analytics_worker --lines 20 | grep "Job scheduler started"
```

**Expected Output**: "Firestore mirror job scheduled", "Job scheduler started"

**Step 3.4: Save PM2 Configuration** (T+32)
```bash
# Save all processes
pm2 save

# Configure startup script
pm2 startup systemd
# Follow the command output instructions

# Verify PM2 status
pm2 list
```

**Expected Output**: All 5 services showing "online" status with 0 restarts

---

### Phase 4: Integration Validation (T+35 to T+45 min)

**Step 4.1: Health Checks** (T+35)
```bash
# Run comprehensive health check
curl -s http://localhost:8888/api/health/detailed | jq

# Expected checks:
# - database: connected
# - zmq_ports: all bound
# - services: all online
# - firestore: connected
```

**Step 4.2: End-to-End Tests** (T+37)
```bash
# Run integration test suite
cd /root/HydraX-v2/tests/integration

python3 test_signal_generation.py
python3 test_fire_execution.py
python3 test_ea_confirmations.py
```

**Expected Output**: All tests pass (100%)
**Go/No-Go**: If any critical test fails, **STOP AND ROLLBACK**

**Step 4.3: Smoke Test** (T+40)
```bash
# Test 1: Create test user
curl -X POST http://localhost:8888/api/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "smoke_test", "telegram_id": 111111111, "tier": "RECRUIT"}'

# Test 2: Verify user created
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 \
  -c "SELECT * FROM users WHERE user_id = 'smoke_test';"

# Test 3: Generate test signal (via signal_engine)
curl -X POST http://localhost:8888/api/internal/test_signal

# Test 4: Verify signal stored
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 \
  -c "SELECT * FROM signals ORDER BY created_at DESC LIMIT 1;"

# Cleanup smoke test
curl -X DELETE http://localhost:8888/api/users/smoke_test
```

**Expected Output**: User created, signal generated and stored, cleanup successful

---

### Phase 5: Go-Live (T+45 to T+60 min)

**Step 5.1: Enable User Access** (T+45)
```bash
# Start Telegram bot
pm2 start /root/HydraX-v2/services/api_server/telegram/bot.py \
  --name telegram_bot \
  --interpreter python3

# Verify bot responding
# (Send /start to bot via Telegram)
```

**Step 5.2: Notify Users** (T+47)
```bash
# Send all-users announcement
python3 /root/HydraX-v2/scripts/send_announcement.py \
  --message "🚀 BITTEN v2.0 is now LIVE! Faster signals, better analytics, new features. Type /help for commands."
```

**Step 5.3: Monitor Initial Traffic** (T+50)
```bash
# Watch logs for errors
pm2 logs --lines 100 --nostream | grep -i error

# Monitor metrics
watch -n 5 'curl -s http://localhost:8888/api/metrics | jq .active_users'

# Check database connections
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 \
  -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'bitten_v2';"
```

**Step 5.4: Final Validation** (T+55)
```bash
# Generate health snapshot
python3 /root/HydraX-v2/scripts/generate_health_report.py > health_snapshot_postlive.html

# Verify all systems operational
curl -s http://localhost:8888/api/health/detailed | jq .status
```

**Expected Output**: `"status": "healthy"`

---

## 📊 Success Criteria

**All must be true to declare cutover successful:**

- [ ] All 5 services online with 0 restarts
- [ ] Database row counts match v1 exactly
- [ ] Integration tests: 100% pass rate
- [ ] ZMQ ports: All 5 bound and accepting connections
- [ ] API response times: P95 < 200ms
- [ ] Telegram bot: Responding to commands
- [ ] No errors in PM2 logs (last 100 lines)
- [ ] PostgreSQL connections: < 50 active
- [ ] Firestore: Connected and mirroring
- [ ] First live signal: Generated and stored within 30 min

---

## ⏱️ Timeline Summary

| Time | Phase | Duration | Checkpoint |
|------|-------|----------|------------|
| T+0 | Shutdown v1 | 5 min | All processes stopped |
| T+5 | Database migration | 15 min | Data migrated, validated |
| T+20 | Deploy v2 services | 15 min | All services online |
| T+35 | Integration validation | 10 min | Tests pass 100% |
| T+45 | Go-live | 15 min | Users can access |
| T+60 | Final validation | - | System healthy |

---

## 🔴 Abort Conditions

**STOP CUTOVER IMMEDIATELY IF:**

1. Database migration row count mismatch > 1%
2. More than 100 orphaned records detected
3. Any v2 service fails to start after 3 attempts
4. Integration tests fail rate > 10%
5. ZMQ ports fail to bind
6. PostgreSQL connection errors
7. Critical data corruption detected

**If aborting, proceed to ROLLBACK_RUNBOOK.md**

---

## 📞 Emergency Contacts

**System Owner**: Commander (Telegram: @commander_username)
**Database Admin**: DBA Team (on-call: +1-XXX-XXX-XXXX)
**Infrastructure**: DevOps Lead (Slack: @devops-lead)

---

## 📝 Post-Cutover Tasks (Within 24 hours)

- [ ] Generate and review parity test report
- [ ] Set up alerting thresholds in monitoring
- [ ] Document any deviations from runbook
- [ ] Archive v1 processes (do not delete backups)
- [ ] Schedule v1 database retention review (30 days)
- [ ] Send post-mortem report to stakeholders
- [ ] Update system documentation with v2 details
- [ ] Review and optimize PostgreSQL query performance
- [ ] Tune PM2 memory limits based on actual usage
- [ ] Schedule first Firestore reconciliation check

---

**Last Updated**: October 8, 2025
**Tested By**: Integration Test Suite
**Approved By**: Pending Commander Sign-off
