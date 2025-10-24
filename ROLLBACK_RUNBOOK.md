# BITTEN v2.0 Rollback Runbook

**Version**: 1.0
**Date**: October 8, 2025
**Estimated Duration**: < 5 minutes
**Objective**: Restore v1 system to full operation

---

## 🚨 When to Execute Rollback

**IMMEDIATE ROLLBACK if:**
- v2 services fail to start after 3 attempts
- Database migration fails or row counts mismatch > 1%
- Integration test pass rate < 90%
- Critical ZMQ ports fail to bind
- PostgreSQL connection failures
- Data corruption detected
- Any abort condition from cutover runbook triggered

**DELAYED ROLLBACK (within 1 hour) if:**
- User-reported critical bugs > 5
- API response times P95 > 1000ms sustained
- Memory leaks causing service crashes
- Firestore sync failures causing data inconsistency

---

## 🔄 Rollback Execution Steps

### Phase 1: Stop v2 Services (R+0 to R+1 min)

**Step 1.1: Stop All v2 Services** (R+0)
```bash
# Stop all v2 processes immediately
pm2 stop zmq_gateway
pm2 stop signal_engine
pm2 stop fire_service
pm2 stop api_server
pm2 stop analytics_worker
pm2 stop telegram_bot  # If started

# Verify all stopped
pm2 list | grep -E "zmq_gateway|signal_engine|fire_service|api_server|analytics_worker"
```

**Expected Output**: All v2 services showing "stopped" status
**Validation**: `curl http://localhost:8888/healthz` should fail (connection refused)

**Step 1.2: Verify Ports Released** (R+0:30)
```bash
# Check ZMQ ports released
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"

# If ports still bound, force kill
lsof -ti:8888 | xargs kill -9
lsof -ti:5555 | xargs kill -9
lsof -ti:5556 | xargs kill -9
lsof -ti:5557 | xargs kill -9
lsof -ti:5558 | xargs kill -9
lsof -ti:5560 | xargs kill -9
```

**Expected Output**: No ports bound
**Critical**: Ports MUST be free before starting v1

---

### Phase 2: Restore v1 Database (R+1 to R+2 min)

**Step 2.1: Verify v1 Backup Exists** (R+1)
```bash
# Check latest backup
ls -lh /root/HydraX-v2/migration/backups/bitten_v1_final_*.db | tail -1

# Verify backup integrity
LATEST_BACKUP=$(ls -t /root/HydraX-v2/migration/backups/bitten_v1_final_*.db | head -1)
sqlite3 "$LATEST_BACKUP" "PRAGMA integrity_check;"
```

**Expected Output**: `ok`
**Go/No-Go**: If backup corrupted, escalate to DBA immediately

**Step 2.2: Restore v1 Database** (R+1:30)
```bash
# Backup current state (in case rollback fails)
cp /root/HydraX-v2/bitten.db /root/HydraX-v2/bitten_v2_failed_$(date +%Y%m%d_%H%M%S).db

# Restore v1 from backup
LATEST_BACKUP=$(ls -t /root/HydraX-v2/migration/backups/bitten_v1_final_*.db | head -1)
cp "$LATEST_BACKUP" /root/HydraX-v2/bitten.db

# Verify restoration
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM users;"
```

**Expected Output**: User count matches pre-migration count
**Validation**: Check critical tables have data

---

### Phase 3: Restart v1 Services (R+2 to R+4 min)

**Step 3.1: Start Infrastructure** (R+2)
```bash
# Start telemetry bridge first (foundation)
pm2 start zmq_telemetry_bridge_debug

# Wait for port binding
sleep 2
ss -tulpen | grep -E ":(5556|5560)"
```

**Expected Output**: Ports 5556 and 5560 bound

**Step 3.2: Start Signal Generation** (R+2:30)
```bash
# Start Elite Guard
pm2 start elite_guard

# Start signal relay chain
pm2 start eg_signal_wrapper
pm2 start signals_zmq_to_redis
pm2 start signals_redis_to_webapp_fixed

# Verify signal flow
sleep 3
pm2 logs elite_guard --lines 5 | grep "Pattern detectors loaded"
```

**Expected Output**: "Pattern detectors loaded successfully"

**Step 3.3: Start Fire Pipeline** (R+3)
```bash
# Start command router
pm2 start command_router

# Start confirmation listener
pm2 start confirm_listener_v207

# Verify ZMQ bindings
ss -tulpen | grep -E ":(5555|5558)"
```

**Expected Output**: Ports 5555 and 5558 bound

**Step 3.4: Start User Services** (R+3:30)
```bash
# Start WebApp
pm2 start webapp

# Start Telegram bot
pm2 start bitten_production_bot

# Start dashboard
pm2 start commander_throne

# Verify all online
pm2 list
```

**Expected Output**: All v1 services showing "online" status

---

### Phase 4: Validation (R+4 to R+5 min)

**Step 4.1: Health Checks** (R+4)
```bash
# Test WebApp
curl -s http://localhost:8888/healthz

# Test dashboard
curl -s http://localhost:8899/healthz

# Check database
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM ea_instances WHERE last_seen > strftime('%s', 'now', '-60 seconds');"
```

**Expected Output**: HTTP 200, EA heartbeats recent

**Step 4.2: EA Connection Check** (R+4:30)
```bash
# Verify EA connected
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) as age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"
```

**Expected Output**: Age < 60 seconds
**Critical**: EA must reconnect within 60 seconds

**Step 4.3: Send Test Command** (R+4:45)
```bash
# Test fire pipeline with safe command
python3 <<EOF
import zmq
import json
from collections import OrderedDict

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('ipc:///tmp/bitten_cmdqueue')

cmd = OrderedDict([
    ('type', 'ping'),
    ('target_uuid', 'COMMANDER_DEV_001'),
    ('timestamp', 1759942800)
])

socket.send_json(cmd)
socket.close()
context.term()
print("✅ Test command sent")
EOF

# Check command router logs
pm2 logs command_router --lines 5 | grep ping
```

**Expected Output**: "ping command routed successfully"

---

## 📊 Rollback Success Criteria

**All must be true to declare rollback successful:**

- [ ] All v1 PM2 processes online with 0 errors
- [ ] v1 database restored and integrity check passed
- [ ] WebApp responding on port 8888
- [ ] Telegram bot responding to commands
- [ ] ZMQ ports 5555-5558, 5560 bound
- [ ] EA heartbeat age < 60 seconds
- [ ] Fire pipeline test command successful
- [ ] No errors in PM2 logs (last 50 lines)
- [ ] Dashboard accessible on port 8899

---

## ⏱️ Rollback Timeline

| Time | Phase | Duration | Checkpoint |
|------|-------|----------|------------|
| R+0 | Stop v2 | 1 min | All v2 services stopped |
| R+1 | Restore database | 1 min | v1 database restored |
| R+2 | Restart v1 services | 2 min | All v1 services online |
| R+4 | Validation | 1 min | System healthy |

**Total Duration**: < 5 minutes

---

## 🔧 Troubleshooting Common Rollback Issues

### Issue 1: Ports Still Bound After v2 Shutdown

**Symptom**: `Address already in use` errors when starting v1

**Solution**:
```bash
# Find and kill processes on critical ports
for port in 5555 5556 5557 5558 5560 8888; do
    echo "Checking port $port"
    lsof -ti:$port | xargs -r kill -9
done

# Verify ports released
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"
```

### Issue 2: Database Backup Corrupted

**Symptom**: `PRAGMA integrity_check` fails

**Solution**:
```bash
# List all available backups
ls -lht /root/HydraX-v2/migration/backups/

# Try previous backup
PREV_BACKUP=$(ls -t /root/HydraX-v2/migration/backups/bitten_v1_*.db | sed -n '2p')
sqlite3 "$PREV_BACKUP" "PRAGMA integrity_check;"

# If OK, restore from previous backup
cp "$PREV_BACKUP" /root/HydraX-v2/bitten.db
```

### Issue 3: EA Not Reconnecting

**Symptom**: EA heartbeat age > 120 seconds

**Solution**:
```bash
# Check command router logs
pm2 logs command_router --lines 20

# Restart command router
pm2 restart command_router

# If still failing, check EA-side logs in MT5
# EA should auto-reconnect within 30 seconds
```

### Issue 4: PM2 Processes Failing to Start

**Symptom**: Services show "errored" status

**Solution**:
```bash
# Check error logs
pm2 logs <process_name> --err --lines 20

# Common fixes:
# 1. Port already bound → kill process on that port
# 2. Missing dependencies → verify Python packages installed
# 3. File permissions → check log file write permissions

# Reset PM2 if needed
pm2 delete all
pm2 flush

# Restart from ecosystem file
pm2 start /root/HydraX-v2/ecosystem.config.js
```

---

## 📝 Post-Rollback Actions

**Immediate (within 1 hour):**
- [ ] Notify users that service is restored (v1)
- [ ] Create incident report with rollback details
- [ ] Preserve v2 failure logs for analysis
- [ ] Document root cause of cutover failure
- [ ] Schedule post-mortem meeting

**Within 24 hours:**
- [ ] Analyze why v2 cutover failed
- [ ] Fix identified issues in v2 codebase
- [ ] Re-run integration tests against fixes
- [ ] Update cutover runbook with lessons learned
- [ ] Plan next cutover attempt timeline

**Before next cutover attempt:**
- [ ] Conduct full dry-run in staging environment
- [ ] Add missing test cases for failure scenarios
- [ ] Implement additional monitoring/alerting
- [ ] Review and approve updated runbooks
- [ ] Train backup personnel on cutover process

---

## 🔒 Data Preservation

**DO NOT DELETE after rollback:**
- v2 PostgreSQL database (keep for analysis)
- v2 service logs (preserve in `/var/log/bitten_v2/`)
- Migration output logs
- Integration test results
- Failed cutover timeline notes

**Archive Location**: `/root/HydraX-v2/FAILED_CUTOVER_$(date +%Y%m%d)/`

```bash
# Create archive
mkdir -p /root/HydraX-v2/FAILED_CUTOVER_$(date +%Y%m%d)
cd /root/HydraX-v2/FAILED_CUTOVER_$(date +%Y%m%d)

# Copy critical artifacts
pg_dump -h localhost -p 5433 -U bitten_admin bitten_v2 > bitten_v2_dump.sql
cp /root/HydraX-v2/migration/migration_output.log .
cp /root/HydraX-v2/tests/results/*.json .
pm2 logs --lines 1000 > pm2_logs_all.txt
```

---

## 📞 Emergency Escalation

**If rollback fails or takes > 10 minutes:**

1. **Escalate to DBA**: Database team on-call (+1-XXX-XXX-XXXX)
2. **Notify Commander**: Telegram @commander_username
3. **Infrastructure Team**: Slack #bitten-critical
4. **Document timeline**: Keep detailed notes of all actions

**Critical Failure Scenarios:**
- v1 database cannot be restored → Escalate to DBA (Priority 1)
- EA cannot reconnect after 5 min → Check EA logs, restart EA if needed
- PM2 completely broken → Manual service start with `python3 <service>.py`

---

## ✅ Rollback Completion Checklist

**Before declaring rollback complete:**

- [ ] All v1 services online and healthy
- [ ] Database integrity verified
- [ ] Users can access system normally
- [ ] At least 1 successful fire command executed
- [ ] No critical errors in logs
- [ ] EA connected and heartbeating
- [ ] Incident report created
- [ ] Team notified of rollback status
- [ ] Archive of v2 failure created
- [ ] Post-mortem scheduled

---

**Last Updated**: October 8, 2025
**Tested By**: Rollback Dry-Run (Staging)
**Approved By**: Pending Commander Sign-off
