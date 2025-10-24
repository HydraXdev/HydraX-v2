# BITTEN v2.0 PHASE 2 - TEST EXECUTION QUICK GUIDE

**Purpose**: Fast-track test execution once v2 services are deployed
**Estimated Time**: 60-90 minutes total
**Prerequisites**: All 5 v2 services running in PM2

---

## ⚡ QUICK START (5 commands, 10 minutes)

```bash
# 1. Verify services are running (30 seconds)
pm2 list | grep -E "zmq_gateway|signal_engine|fire_service|api_server|analytics_worker"

# 2. Test health endpoints (1 minute)
for port in 9091 9092 8890 8888 9093; do curl -s http://localhost:$port/health* | jq; done

# 3. Run automated Phase 2 validation (5 minutes)
python3 /root/HydraX-v2/tests/phase2_greenlight_runner.py

# 4. Check overall status (instant)
cat /tmp/phase2_greenlight_*.json | jq '.overall_status'

# 5. If PASS, you're done! If FAIL, see detailed diagnostics below
```

**Expected Result**: `"overall_status": "PASS"` with 6/6 green checks

---

## 📊 DETAILED VALIDATION (6 checks, 60 minutes)

### **Check 1: Parity Suite (15 minutes)**

**Purpose**: Verify v2 produces identical results to v1

```bash
cd /root/HydraX-v2/tests/parity

# Run parity comparison
python3 parity_runner.py --output /tmp/parity_results.json

# Generate HTML report
python3 parity_report.py /tmp/parity_results.json --output /tmp/parity_report.html

# Check results
cat /tmp/parity_results.json | jq '{
  overall: .overall_status,
  signals: .signals_pass,
  fires: .fires_pass,
  positions: .positions_pass
}'
```

**Success Criteria**:
- `overall_status`: "PASS"
- `signals_pass`: true (100% match)
- `fires_pass`: true (100% match)
- `positions_pass`: true (100% match)

**If Failed**:
```bash
# Check mismatches
cat /tmp/parity_results.json | jq '.mismatches[] | {type, count}'

# View HTML report for visual diff
firefox /tmp/parity_report.html
```

---

### **Check 2: Load Tests (20 minutes)**

**Purpose**: Validate system meets SLO requirements under load

```bash
cd /root/HydraX-v2/tests/load

# Run load test suite
python3 load_runner.py --output /tmp/load_results.json

# Generate HTML report
python3 load_report.py /tmp/load_results.json --output /tmp/load_report.html

# Check SLO compliance
cat /tmp/load_results.json | jq '.summary.performance_summary | {
  fire_p95: .fire_p95_ms,
  signal_p95: .signal_p95_ms,
  websocket_p95: .websocket_p95_ms,
  fire_pass: (.fire_p95_ms < 100),
  signal_pass: (.signal_p95_ms < 50),
  websocket_pass: (.websocket_p95_ms < 250)
}'
```

**Success Criteria**:
- Fire P95 < 100ms
- Signal P95 < 50ms
- WebSocket P95 < 250ms
- No errors during sustained load

**If Failed**:
```bash
# Check error distribution
cat /tmp/load_results.json | jq '.tests[] | {test, errors, p95}'

# View HTML report for detailed charts
firefox /tmp/load_report.html

# Check database connection pool
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "
SELECT count(*) as active_connections, state
FROM pg_stat_activity
WHERE datname = 'bitten_v2'
GROUP BY state;"
```

---

### **Check 3: Service Health (2 minutes)**

**Purpose**: Verify all 5 services operational

```bash
# Test each health endpoint
echo "=== zmq_gateway ===" && curl -s http://localhost:9091/health/readiness | jq
echo "=== signal_engine ===" && curl -s http://localhost:9092/health/readiness | jq
echo "=== fire_service ===" && curl -s http://localhost:8890/health | jq
echo "=== api_server ===" && curl -s http://localhost:8888/health | jq
echo "=== analytics_worker ===" && curl -s http://localhost:9093/health/readiness | jq
```

**Success Criteria**:
- All endpoints return HTTP 200
- All responses show `{"status": "healthy"}` or similar
- No timeout errors

**If Failed**:
```bash
# Check PM2 logs for specific service
pm2 logs [service_name] --lines 50

# Check if service is actually running
pm2 status [service_name]

# Restart if needed
pm2 restart [service_name]
```

---

### **Check 4: RBAC & Rate Limits (5 minutes)**

**Purpose**: Validate security controls enforced

```bash
# Test unauthenticated request (should be rejected)
curl -X POST http://localhost:8888/api/fire \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "test"}' \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: 401 Unauthorized

# Test rate limiting (100 rapid requests)
for i in {1..100}; do
  curl -s http://localhost:8888/api/signals -w "%{http_code}\n" -o /dev/null
done | sort | uniq -c
# Expected: At least one 429 Too Many Requests
```

**Success Criteria**:
- Unauthenticated requests blocked (401)
- Rate limits active (429 after threshold)
- Firebase Auth required for protected endpoints

**If Failed**:
```bash
# Check api_server logs for auth errors
pm2 logs api_server --lines 30 | grep -i "auth\|401\|429"

# Verify Firebase credentials loaded
pm2 env api_server | grep FIREBASE
```

---

### **Check 5: Nightly Reconciliation (5 minutes)**

**Purpose**: Verify PostgreSQL ↔ Firestore sync job

```bash
# Run reconciliation manually
python3 /root/HydraX-v2/tests/validation/reconciliation.py

# Check exit code
echo "Exit code: $?"
# Expected: 0 (success)

# Verify reconciliation scheduled in cron
crontab -l | grep reconciliation

# Check last reconciliation report
cat /tmp/reconciliation_$(date +%Y%m%d).json | jq '.status'
# Expected: "PASS"
```

**Success Criteria**:
- Reconciliation script exits 0
- Signal counts match (PostgreSQL == Firestore)
- Outcome counts match
- User stats match
- Zero errors in report

**If Failed**:
```bash
# Check reconciliation logs
tail -50 /var/log/reconciliation.log

# Compare counts manually
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "
SELECT COUNT(*) as pg_signal_count FROM signals WHERE created_at > extract(epoch from now() - interval '24 hours');"

# Check Firestore (requires Firebase CLI)
# firebase firestore:query signals --where created_at > $(date -d '24 hours ago' +%s)
```

---

### **Check 6: Archive Isolation (1 minute)**

**Purpose**: Verify no archive code in runtime

```bash
# Check for archive imports
grep -r "import.*archive" /root/HydraX-v2/services/ || echo "✅ No archive imports"

# Check for archive path references
grep -r "archive_v1" /root/HydraX-v2/services/ || echo "✅ No archive references"

# Verify archive directories not mounted
ls -la /root/HydraX-v2/services/*/archive* 2>&1 | grep "No such file" && echo "✅ Archive dark"
```

**Success Criteria**:
- Zero archive imports
- Zero archive path references
- Archive directories inaccessible to services

**Status**: ✅ Already verified in pre-deployment validation

---

## 🧪 INTEGRATION TESTS (Optional, 15 minutes)

**Purpose**: Test cross-service communication

```bash
cd /root/HydraX-v2

# Run all integration tests
python3 -m pytest tests/integration/ -v --tb=short > /tmp/integration_results.txt 2>&1

# Check pass rate
tail -10 /tmp/integration_results.txt

# View failures only
grep -A 10 "FAILED" /tmp/integration_results.txt
```

**Success Criteria**:
- >90% tests passing
- No critical failures (signal flow, fire execution)
- Minor failures acceptable (e.g., timing issues)

---

## 📋 VALIDATION CHECKLIST

**Before presenting to Commander**:

- [ ] All 5 services running in PM2
- [ ] All health endpoints returning green
- [ ] Parity tests: 100% match with v1
- [ ] Load tests: All SLOs met (fire <100ms, signal <50ms, ws <250ms)
- [ ] RBAC enforced: 401 for unauthenticated
- [ ] Rate limits active: 429 after threshold
- [ ] Reconciliation job passing
- [ ] Archive isolation verified
- [ ] Phase 2 green-light runner: overall_status = "PASS"
- [ ] HTML reports generated (parity + load)

---

## 📊 GENERATE COMMANDER REPORTS

**4 Green Reports Required**:

### **Report 1: Parity Validation**
```bash
python3 /root/HydraX-v2/tests/parity/parity_report.py \
  /tmp/parity_results.json \
  --output /tmp/parity_report.html

echo "✅ Report 1: file:///tmp/parity_report.html"
```

### **Report 2: Load Test Performance**
```bash
python3 /root/HydraX-v2/tests/load/load_report.py \
  /tmp/load_results.json \
  --output /tmp/load_report.html

echo "✅ Report 2: file:///tmp/load_report.html"
```

### **Report 3: Phase 2 Green-Light Summary**
```bash
cat /tmp/phase2_greenlight_*.json | jq '{
  timestamp: .timestamp,
  overall_status: .overall_status,
  checks: .checks | to_entries | map({
    check: .key,
    status: .value.status
  }),
  failures: .failures
}' > /tmp/greenlight_summary.json

echo "✅ Report 3: /tmp/greenlight_summary.json"
```

### **Report 4: Integration Validation Report**
```bash
# Already created
echo "✅ Report 4: /root/HydraX-v2/PHASE2_INTEGRATION_VALIDATION_REPORT.md"
```

---

## 🚨 TROUBLESHOOTING

### **If Parity Tests Fail**

**Problem**: v2 signals don't match v1 signals

**Debug Steps**:
1. Check signal_engine logs: `pm2 logs signal_engine --lines 100`
2. Verify market data flowing: `pm2 logs zmq_gateway --lines 50`
3. Compare signal generation logic between v1 and v2
4. Check pattern detector thresholds (may differ intentionally)

**Acceptable Variances**:
- Timestamp differences <1 second (OK)
- Confidence differences <0.5% (OK)
- Entry price differences <0.00001 (OK)

**Unacceptable Variances**:
- Different patterns detected
- Missing signals (v1 has, v2 doesn't)
- Extra signals (v2 has, v1 doesn't)

---

### **If Load Tests Fail**

**Problem**: P95 latencies exceed SLOs

**Debug Steps**:
1. Check database connection pool: `PGPASSWORD='bitten_secure_2025' psql ... -c "SELECT * FROM pg_stat_activity;"`
2. Check CPU/memory usage: `top -b -n 1 | head -20`
3. Check disk I/O: `iostat -x 1 5`
4. Check network latency: `ping -c 10 localhost`

**Common Causes**:
- Database connection pool exhausted (increase max_connections)
- Slow queries (add indexes, optimize queries)
- CPU bottleneck (scale up, optimize code)
- Memory pressure (increase RAM, optimize caching)

---

### **If Services Won't Start**

**Problem**: PM2 shows service crashed or error

**Debug Steps**:
1. Check logs: `pm2 logs [service_name] --lines 100 --err`
2. Check dependencies: `cd /root/HydraX-v2/services/[service] && pip list | grep [package]`
3. Check port conflicts: `ss -tulpen | grep [port]`
4. Check environment variables: `pm2 env [service_name]`

**Common Causes**:
- Missing dependencies (run `pip install -r requirements.txt`)
- Port already in use (kill conflicting process)
- Database connection failed (check DATABASE_URL)
- Firebase credentials missing (check FIREBASE_CREDENTIALS_PATH)

---

## ⏱️ TIME ESTIMATES

| Task | Duration | Notes |
|------|----------|-------|
| Service health checks | 2 min | Quick endpoint tests |
| Parity tests | 15 min | Depends on data volume |
| Load tests | 20 min | Includes 60s soak tests |
| RBAC validation | 5 min | Security controls test |
| Reconciliation | 5 min | Manual run + verification |
| Archive isolation | 1 min | Static code check |
| Integration tests | 15 min | Optional, comprehensive |
| Report generation | 5 min | HTML reports for Commander |
| **TOTAL** | **68 min** | ~1 hour 10 minutes |

---

## 🎯 SUCCESS CRITERIA SUMMARY

**Phase 2 validation passes when**:

✅ **Overall Status**: phase2_greenlight_runner.py exits 0
✅ **Parity**: 100% match on signals, fires, positions
✅ **Performance**: Fire P95 <100ms, Signal P95 <50ms, WS P95 <250ms
✅ **Security**: 401 for unauth, 429 for rate limit
✅ **Data Sync**: Reconciliation passes
✅ **Isolation**: No archive imports found
✅ **Reports**: 4 green reports generated

**If all criteria met → Present to Commander for Phase 3 approval**

---

**Document Owner**: Claude Code (Sonnet 4.5)
**Last Updated**: 2025-10-08
**Version**: 1.0

**END OF TEST EXECUTION GUIDE**
