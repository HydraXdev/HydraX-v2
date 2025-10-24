# BITTEN v2.0 REBUILD - PHASE 0 EXECUTION CHECKLIST

**Status**: 🚀 READY TO START
**Timeline**: Week 1 (7 days)
**Goal**: Establish Firebase foundation and safety infrastructure

---

## 📋 DAY 1-2: FIREBASE PROJECT SETUP

### Firebase Console Setup
- [ ] Create Firebase project: `bitten-production`
- [ ] Enable Firestore database (production mode)
  - [ ] Set security rules (authenticated users only)
  - [ ] Create initial indexes
- [ ] Enable Firebase Authentication
  - [ ] Enable Custom Auth provider (for Telegram integration)
  - [ ] Configure user claims system
- [ ] Enable Cloud Functions
  - [ ] Set up Node.js environment
  - [ ] Configure deployment credentials
- [ ] Enable Cloud Storage
  - [ ] Create buckets for backups and logs
- [ ] Download service account key
  - [ ] Save to `/root/firebase-service-account.json`
  - [ ] Add to `.gitignore`
  - [ ] Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS`

### Local Firebase SDK Installation
```bash
# Install Firebase Admin SDK
pip install firebase-admin

# Install Firebase Functions SDK (for Cloud Functions)
npm install -g firebase-tools
firebase login
firebase init functions
```

### Test Firebase Connection
```bash
# Create test script to verify connection
python3 test_firebase_connection.py
```

**Checkpoint 1**: ✅ Firebase project accessible, service account working

---

## 📊 DAY 3-4: BASELINE MEASUREMENTS

### File System Analysis
```bash
# Total Python files
find /root/HydraX-v2 -name "*.py" | wc -l > /root/baseline_file_count.txt

# File size analysis
du -sh /root/HydraX-v2 > /root/baseline_disk_usage.txt

# Largest files
find /root/HydraX-v2 -name "*.py" -exec ls -lh {} \; | sort -k5 -hr | head -20 > /root/baseline_largest_files.txt

# Category breakdown
echo "Version files:" >> /root/baseline_categories.txt
find /root/HydraX-v2 -name "*_v[0-9]*.py" | wc -l >> /root/baseline_categories.txt
echo "Test files:" >> /root/baseline_categories.txt
find /root/HydraX-v2 -name "*test*.py" | wc -l >> /root/baseline_categories.txt
echo "Backup files:" >> /root/baseline_categories.txt
find /root/HydraX-v2 -name "*backup*.py" -o -name "*old*.py" | wc -l >> /root/baseline_categories.txt
```

### Process Analysis
```bash
# Current PM2 processes
pm2 list > /root/baseline_pm2_processes.txt
pm2 describe all > /root/baseline_pm2_details.txt

# Memory usage
free -h > /root/baseline_memory.txt
```

### Database Analysis
```bash
# Database size
ls -lh /root/HydraX-v2/bitten.db > /root/baseline_db_size.txt

# Table counts
sqlite3 /root/HydraX-v2/bitten.db "SELECT name FROM sqlite_master WHERE type='table';" > /root/baseline_db_tables.txt

# Row counts per table
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    name,
    (SELECT COUNT(*) FROM sqlite_master AS m WHERE m.name = t.name) AS row_count
FROM sqlite_master AS t
WHERE type='table';" > /root/baseline_db_rows.txt
```

### Performance Metrics (24-hour sample)
```bash
# Signal generation rate
echo "Monitoring signal generation for 24 hours..." > /root/baseline_signal_rate.txt
date >> /root/baseline_signal_rate.txt
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s', 'now', '-24 hours');" >> /root/baseline_signal_rate.txt

# Fire command latency (sample from recent fires)
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    AVG(updated_at - created_at) as avg_latency_seconds,
    MAX(updated_at - created_at) as max_latency_seconds
FROM fires
WHERE status = 'FILLED' AND created_at > strftime('%s', 'now', '-7 days');" > /root/baseline_fire_latency.txt
```

**Checkpoint 2**: ✅ Complete baseline metrics captured

---

## 🛡️ DAY 5: SAFETY INFRASTRUCTURE

### Complete System Backup
```bash
# Database backup
cp /root/HydraX-v2/bitten.db /root/HydraX-v2/bitten_v1_backup_$(date +%Y%m%d).db

# Code backup (exclude node_modules, __pycache__)
tar -czf /root/bitten_v1_backup_$(date +%Y%m%d).tar.gz \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    /root/HydraX-v2

# Configuration backup
cp -r /root/HydraX-v2/config /root/HydraX-v2/config_v1_backup_$(date +%Y%m%d)

# Tracking files backup
mkdir -p /root/tracking_backup_$(date +%Y%m%d)
cp /root/HydraX-v2/*.jsonl /root/tracking_backup_$(date +%Y%m%d)/
```

### Create Deleted Files Archive
```bash
# Directory for files we'll delete
mkdir -p /root/HydraX-v2/DELETED_FILES/phase_1
mkdir -p /root/HydraX-v2/DELETED_FILES/phase_2
mkdir -p /root/HydraX-v2/DELETED_FILES/phase_3
```

### Rollback Script
```bash
# Create comprehensive rollback script
cat > /root/rollback_to_v1.sh << 'EOF'
#!/bin/bash
# BITTEN v2.0 Rollback Script
# Emergency restore to v1.0 state

echo "🚨 ROLLING BACK TO BITTEN v1.0..."
date

# Stop all v2.0 processes
pm2 delete all

# Restore database
LATEST_DB=$(ls -t /root/HydraX-v2/bitten_v1_backup_*.db | head -1)
cp "$LATEST_DB" /root/HydraX-v2/bitten.db
echo "✅ Database restored from $LATEST_DB"

# Restore code
LATEST_TAR=$(ls -t /root/bitten_v1_backup_*.tar.gz | head -1)
cd /root
tar -xzf "$LATEST_TAR"
echo "✅ Code restored from $LATEST_TAR"

# Restore configs
LATEST_CONFIG=$(ls -td /root/HydraX-v2/config_v1_backup_* | head -1)
rm -rf /root/HydraX-v2/config
cp -r "$LATEST_CONFIG" /root/HydraX-v2/config
echo "✅ Config restored from $LATEST_CONFIG"

# Restart v1.0 processes
cd /root/HydraX-v2
pm2 start elite_guard_with_citadel.py --name elite_guard
pm2 start webapp_server_optimized.py --name webapp
pm2 start command_router.py --name command_router
pm2 start confirm_listener_v207.py --name confirm_listener
pm2 start zmq_telemetry_bridge_debug.py --name zmq_telemetry_bridge

echo "✅ ROLLBACK COMPLETE - v1.0 processes restarted"
pm2 list
EOF

chmod +x /root/rollback_to_v1.sh
```

### Health Check Script
```bash
# Create health check for ongoing monitoring
cat > /root/bitten_health_check.sh << 'EOF'
#!/bin/bash
# BITTEN System Health Check

echo "🏥 BITTEN HEALTH CHECK - $(date)"
echo "=================================="

# Check critical processes
echo ""
echo "📊 PROCESS STATUS:"
pm2 list | grep -E "elite_guard|webapp|command_router|confirm_listener|zmq_telemetry"

# Check port bindings
echo ""
echo "🔌 PORT BINDINGS:"
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"

# Check EA connection
echo ""
echo "🤖 EA CONNECTION:"
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"

# Check recent signals
echo ""
echo "📡 RECENT SIGNALS (last hour):"
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s', 'now', '-1 hour');"

# Check disk space
echo ""
echo "💾 DISK SPACE:"
df -h /root

# Check memory
echo ""
echo "🧠 MEMORY:"
free -h

echo ""
echo "=================================="
EOF

chmod +x /root/bitten_health_check.sh
```

**Checkpoint 3**: ✅ Safety infrastructure in place, rollback tested

---

## 📝 DAY 6-7: DOCUMENTATION & PLANNING REVIEW

### Document Current State
- [ ] Create `/root/HydraX-v2/CURRENT_STATE_SNAPSHOT.md`
  - [ ] List all active PM2 processes with PIDs
  - [ ] Document all port bindings
  - [ ] List all database tables with row counts
  - [ ] Document critical file locations
  - [ ] List all cron jobs and scheduled tasks

### Review Phase 1 Plan
- [ ] Review `/root/HydraX-v2/BITTEN_rebuild_2.0.md` Phase 1 tasks
- [ ] Identify any dependencies we missed
- [ ] Confirm file deletion categories are accurate
- [ ] Verify dangerous process list

### Create Phase 1 Execution Script
```bash
# Create automated Phase 1 execution helper
cat > /root/execute_phase_1.sh << 'EOF'
#!/bin/bash
# BITTEN v2.0 - Phase 1 Quick Wins Execution Script
# Automates the file deletion and process cleanup tasks

echo "🚀 PHASE 1: QUICK WINS - Starting..."
date

# Create progress log
PHASE1_LOG="/root/phase_1_execution_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$PHASE1_LOG") 2>&1

echo "📋 This script will:"
echo "  1. Delete 700+ abandoned files"
echo "  2. Kill dangerous processes"
echo "  3. Consolidate tracking files to Firestore"
echo "  4. Integrate Firebase Auth"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 1
fi

# Checkpoint system
checkpoint() {
    echo ""
    echo "✅ CHECKPOINT: $1"
    read -p "Continue to next step? (yes/no): " continue
    if [ "$continue" != "yes" ]; then
        echo "⏸️ Paused. Resume by running: $0 --resume-from=$2"
        exit 0
    fi
}

# TODO: Add actual Phase 1 execution steps here
echo "🎯 Phase 1 execution script ready for implementation"

EOF

chmod +x /root/execute_phase_1.sh
```

**Checkpoint 4**: ✅ Documentation complete, Phase 1 ready to execute

---

## ✅ PHASE 0 COMPLETION CRITERIA

**All checkpoints must pass before proceeding to Phase 1:**

- [ ] **Checkpoint 1**: Firebase project accessible, SDK installed and tested
- [ ] **Checkpoint 2**: Complete baseline metrics captured (files, processes, DB, performance)
- [ ] **Checkpoint 3**: Backup system operational, rollback script tested
- [ ] **Checkpoint 4**: Current state documented, Phase 1 plan reviewed

**Phase 0 Success Indicators:**
- Firebase connection verified: `✅ Connected to Firestore`
- Baseline files created: 6+ measurement files in `/root/`
- Backup files created: Database, code tarball, config directory
- Rollback script functional: Test run completes without errors
- Health check script functional: Runs and shows system status

**Estimated Time**: 5-7 days (part-time work)

---

## 🚦 GO/NO-GO DECISION POINT

**Before proceeding to Phase 1, verify:**

1. ✅ Firebase is operational and accessible
2. ✅ All baseline measurements are captured
3. ✅ Rollback capability is proven (test in non-production if possible)
4. ✅ Critical processes are running stable (no recent crashes)
5. ✅ Trading system is functional (recent successful fires)

**If ANY checkpoint fails**: STOP and resolve before continuing

**When all checkpoints pass**: Proceed to Phase 1 execution

---

## 📞 EMERGENCY CONTACTS

**If rollback needed:**
```bash
/root/rollback_to_v1.sh
```

**If system health check fails:**
```bash
/root/bitten_health_check.sh
```

**Current system state reference:**
- `/root/HydraX-v2/CLAUDE.md` - System documentation
- `/root/HydraX-v2/ARCHITECTURE.md` - Technical architecture
- `/root/HydraX-v2/BITTEN_rebuild_2.0.md` - Complete rebuild plan

---

**Created**: October 8, 2025
**Next Phase**: Phase 1 - Quick Wins (Weeks 2-3)
**Status**: 🟢 READY TO START
