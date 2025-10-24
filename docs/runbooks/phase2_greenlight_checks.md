# BITTEN v2.0 PHASE 2 - GREEN LIGHT VALIDATION CHECKLIST

**Purpose:** Execute all Commander-requested validation checks before Phase 2 deployment approval.
**Execution Time:** ~30 minutes
**Pass Criteria:** 100% green on all checks

---

## 🎯 PRE-FLIGHT CHECKS

### **1. Run Parity Suite Against v1 Logs** ✅

**Requirement:** 100% match on golden cases

```bash
# Run parity comparison
cd /root/HydraX-v2/tests/parity

# Compare signals
python3 compare_signals.py --hours 24 --output /tmp/signals_parity.json

# Compare fires
python3 compare_fires.py --hours 24 --output /tmp/fires_parity.json

# Compare positions
python3 compare_positions.py --hours 24 --output /tmp/positions_parity.json

# Generate full report
python3 parity_runner.py --output /tmp/parity_full_report.json

# Expected: 100% match on signal generation logic
# Expected: 100% match on fire execution flow
# Expected: 100% match on position tracking
```

**Pass Criteria:**
- Signal generation parity ≥ 99.9%
- Fire execution parity = 100%
- Position tracking parity = 100%

---

### **2. Run Load Suite to SLOs** ⚡

**Requirements:**
- P95 fire < 100ms
- Signal gen < 50ms
- Capture HTML reports

```bash
cd /root/HydraX-v2/tests/load

# Run full load test suite
python3 load_runner.py --output /tmp/load_test_results.json

# Generate HTML report
python3 load_report.py /tmp/load_test_results.json --output /tmp/load_test_report.html

# View report
firefox /tmp/load_test_report.html
```

**Pass Criteria:**
- **Fire P95 < 100ms** ✅ REQUIRED
- **Signal gen P95 < 50ms** ✅ REQUIRED
- **WebSocket P95 < 250ms** ✅ REQUIRED
- **DB pool never exhausted** ✅ REQUIRED
- No failures during 60s sustained load

---

### **3. Health/Readiness Endpoints** 🏥

**Requirement:** All 5 services up with alerting wired

```bash
# Check all service health endpoints
echo "=== zmq_gateway ==="
curl -s http://localhost:9091/health/readiness | jq

echo "=== signal_engine ==="
curl -s http://localhost:9092/health/readiness | jq

echo "=== fire_service ==="
curl -s http://localhost:8890/health | jq

echo "=== api_server ==="
curl -s http://localhost:8888/health | jq

echo "=== analytics_worker ==="
curl -s http://localhost:9093/health/readiness | jq

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'

# Check alert rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | .name'
```

**Pass Criteria:**
- All 5 services return `{\"status\": \"healthy\"}`
- All services `up==1` in Prometheus
- Alert rules loaded (bitten_service_health, bitten_database, bitten_trading, bitten_system)

---

### **4. RBAC + Rate Limits** 🔒

**Requirement:** Firebase Auth at boundary, rate limits enforced

```bash
# Test unauthenticated request (should fail)
curl -X POST http://localhost:8888/api/fire \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD"}' \
  -w "\nStatus: %{http_code}\n"
# Expected: 401 Unauthorized

# Test rate limiting (100 rapid requests)
for i in {1..100}; do
  curl -s http://localhost:8888/api/signals -w "%{http_code}\n" -o /dev/null
done | sort | uniq -c
# Expected: At least one 429 Too Many Requests

# Test Firebase Auth integration
curl -X GET http://localhost:8888/api/user/stats \
  -H "Authorization: Bearer INVALID_TOKEN" \
  -w "\nStatus: %{http_code}\n"
# Expected: 401 Unauthorized
```

**Pass Criteria:**
- Unauthenticated requests rejected (401)
- Rate limits active (429 after threshold)
- Firebase Auth required for protected endpoints

---

### **5. Nightly Postgres ↔ Firestore Reconciliation** 🌙

**Requirement:** Job scheduled, first report clean

```bash
# Run reconciliation manually
python3 /root/HydraX-v2/tests/validation/reconciliation.py

# Check cron schedule
crontab -l | grep reconciliation

# Verify first report
cat /tmp/reconciliation_$(date +%Y%m%d).json | jq '.status'
# Expected: "PASS"
```

**Pass Criteria:**
- Reconciliation job scheduled in cron
- Signal count matches (PostgreSQL == Firestore)
- Outcome count matches
- User stats match
- Zero errors in first report

---

### **6. Archive Imports Verification** 📦

**Requirement:** No archive imports in runtime (/archive_v1/ dark)

```bash
# Check for archive imports in service code
grep -r "import.*archive" /root/HydraX-v2/services/ || echo "✅ No archive imports"

# Check for archive path references
grep -r "archive_v1" /root/HydraX-v2/services/ || echo "✅ No archive references"

# Verify archive directories not mounted/accessible
ls -la /root/HydraX-v2/services/*/archive* 2>&1 | grep "No such file" && echo "✅ Archive dark"

# Check running processes aren't loading archive code
ps aux | grep -E "archive|ARCHIVE" | grep -v grep || echo "✅ No archive processes"
```

**Pass Criteria:**
- Zero archive imports in service code
- Zero archive path references in runtime code
- Archive directories inaccessible to services
- No running processes loading archive code

---

## 📊 VALIDATION REPORT GENERATION

```bash
# Create comprehensive validation report
cat > /tmp/phase2_greenlight_report.md << 'EOF'
# BITTEN v2.0 PHASE 2 GREEN-LIGHT VALIDATION

**Date:** $(date -u +"%Y-%m-%d %H:%M UTC")
**Validator:** $(whoami)

## Results

### 1. Parity Suite
- [ ] Signals: __% match
- [ ] Fires: __% match
- [ ] Positions: __% match

### 2. Load Tests
- [ ] Fire P95: __ms (target: <100ms)
- [ ] Signal P95: __ms (target: <50ms)
- [ ] WebSocket P95: __ms (target: <250ms)

### 3. Service Health
- [ ] zmq_gateway: __ (healthy/unhealthy)
- [ ] signal_engine: __ (healthy/unhealthy)
- [ ] fire_service: __ (healthy/unhealthy)
- [ ] api_server: __ (healthy/unhealthy)
- [ ] analytics_worker: __ (healthy/unhealthy)

### 4. Security
- [ ] RBAC enforced: __ (yes/no)
- [ ] Rate limits active: __ (yes/no)
- [ ] Firebase Auth required: __ (yes/no)

### 5. Reconciliation
- [ ] Job scheduled: __ (yes/no)
- [ ] First report status: __ (PASS/FAIL)

### 6. Archive Isolation
- [ ] No archive imports: __ (yes/no)
- [ ] Archive dark: __ (yes/no)

## Overall Status: __ (PASS/FAIL)

**Commander Sign-Off:** _______________
**Date:** _______________
EOF

cat /tmp/phase2_greenlight_report.md
```

---

## ✅ FINAL CHECKLIST

Before presenting to Commander:

- [ ] All parity tests at 100% (or explained variances)
- [ ] All load tests meeting SLOs
- [ ] All 5 services healthy
- [ ] Alerting operational in Prometheus
- [ ] RBAC + rate limits confirmed
- [ ] Reconciliation job clean
- [ ] Archive isolation verified
- [ ] HTML reports generated and saved
- [ ] Validation report completed

---

## 🚀 DEPLOYMENT APPROVAL

**If all checks pass:**
- Present validation report to Commander
- Get sign-off for Phase 2 deployment
- Proceed with cutover plan

**If any checks fail:**
- Document failures in validation report
- Fix identified issues
- Re-run failed checks
- Do NOT proceed until 100% green

---

**Document Owner:** Claude Code (Sonnet 4.5)
**Last Updated:** 2025-10-08
**Status:** Ready for execution
