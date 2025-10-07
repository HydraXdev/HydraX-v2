# BITTEN Mission Flow Dry-Run Test Suite

## Overview

Comprehensive test suite that simulates the complete user journey from Telegram alert to trade execution and monitoring. This dry-run test validates all critical components of the mission flow WITHOUT executing real trades.

## Test Coverage

### ✅ Test 1: Generate Mission Session

- Creates mission session via session_manager
- Generates JWT with proper scopes
- Validates deep link URL format
- Verifies TTL and risk parameters

### ✅ Test 2: Simulate Telegram Alert

- Formats alert message
- Includes deep link URL
- Validates message structure

### ✅ Test 3: Mission Page Load

- Parses deep link parameters
- Validates JWT token
- Fetches mission data
- Verifies beacons (Operational/Secure/Latency)

### ✅ Test 4: Execute Action

- Generates clientRequestId
- Simulates POST to /api/fire
- Verifies 202 response with opId
- Checks redirect to /status page

### ✅ Test 5: Event Delivery

- Simulates SSE events (ARMING, FILLED)
- Validates latency < 250ms
- Checks P&L updates
- Verifies event sequence

### ✅ Test 6: Idempotency

- Re-sends identical clientRequestId
- Verifies same opId returned
- Confirms no duplicate orders
- Checks 202 or 409 response

### ✅ Test 7: Session Expiry

- Tests expired session rejection
- Validates "Session expired" message
- Checks 410 response code

### ✅ Test 8: Risk Fuse

- Tests risk limit enforcement
- Validates riskUsd > riskMaxUsd rejection
- Verifies 422 response
- Checks no order emission

### ✅ Test 9: Stats Page

- Verifies equity series updates
- Checks trade appears in recent events
- Validates stats endpoint data

## Prerequisites

### Required Modules

```bash
# Ensure these modules exist:
# - src/missions/session_manager.py
# - src/bitten_core/fire_mode_executor.py
# - src/bitten_core/fire_mode_database.py
```

### Python Dependencies

- Python 3.8+
- Standard library only (no external dependencies for dry-run)

## Usage

### Basic Execution

```bash
# Make script executable
chmod +x /root/HydraX-v2/tests/dry_run_mission_flow.py

# Run all tests
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py
```

### Check Exit Code

```bash
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py
if [ $? -eq 0 ]; then
    echo "All tests passed"
else
    echo "Some tests failed"
fi
```

### View Results

```bash
# Results saved to JSON automatically
cat /root/HydraX-v2/tests/dry_run_results.json | python3 -m json.tool
```

## Output Format

### Console Output

- **Green ✓**: Test passed
- **Red ✗**: Test failed
- **Timing**: Duration in milliseconds for each test
- **Details**: Key verification points and data

### JSON Output

Location: `/root/HydraX-v2/tests/dry_run_results.json`

```json
{
  "timestamp": "2025-10-05T12:34:56.789",
  "total_duration_ms": 1234,
  "total_tests": 9,
  "passed": 9,
  "failed": 0,
  "tests": [
    {
      "name": "Generate Mission Session",
      "passed": true,
      "duration_ms": 45,
      "error": null,
      "details": {
        "ms": "MS_1728123456_ABC123",
        "deep_link": "http://localhost:8888/mission?ms=...",
        "expires_at": "2025-10-05T12:44:56"
      }
    }
  ]
}
```

## Expected Behavior

### All Tests Pass

```
==================================================
🎯 BITTEN MISSION FLOW DRY-RUN TEST SUITE
==================================================

[STEP 1] Generate Test Mission Session
  ✓ PASS (45ms)
    ms: MS_1728123456_ABC123
    deep_link: http://localhost:8888/mission?ms=...
    expires_at: 2025-10-05T12:44:56

[STEP 2] Simulate Telegram Alert
  ✓ PASS (12ms)
    alert_length: 245
    deep_link_included: True

... (all tests pass)

📊 TEST SUMMARY
Total Tests: 9
Passed: 9
Failed: 0
Duration: 1234ms

🎉 ALL TESTS PASSED
```

### Some Tests Fail

```
[STEP 3] Mission Page Load
  ✗ FAIL (23ms)
  Error: session_manager not found

... (other tests may skip)

📊 TEST SUMMARY
Total Tests: 9
Passed: 6
Failed: 3
Duration: 987ms

❌ SOME TESTS FAILED
```

## Integration with CI/CD

### Pre-Deployment Check

```bash
#!/bin/bash
# Run before deploying mission system

cd /root/HydraX-v2/tests
python3 dry_run_mission_flow.py

if [ $? -ne 0 ]; then
    echo "❌ Dry-run tests failed - deployment blocked"
    exit 1
fi

echo "✅ Dry-run tests passed - proceeding with deployment"
```

### PM2 Process Check

```bash
# Run before PM2 restart
pm2 stop webapp_server_optimized
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py
if [ $? -eq 0 ]; then
    pm2 start webapp_server_optimized
else
    echo "Tests failed - manual intervention required"
fi
```

## Troubleshooting

### Test 1 Fails: session_manager not found

**Cause**: Mission session manager module doesn't exist yet
**Solution**: Implement `/root/HydraX-v2/src/missions/session_manager.py` first

### Test 3 Fails: Token validation error

**Cause**: JWT secret key mismatch or token format issue
**Solution**: Check JWT_SECRET in environment and token generation logic

### Test 5 Fails: Latency exceeds 250ms

**Cause**: Simulated timing issue (shouldn't happen in dry-run)
**Solution**: Review event simulation logic in test code

### Test 8 Fails: Risk check not triggered

**Cause**: Risk validation logic missing
**Solution**: Implement risk fuse in fire command handler

## Next Steps After Dry-Run

1. **Review Results**: Check `dry_run_results.json` for all test details
2. **Fix Failures**: Address any failed tests before live deployment
3. **Integration Test**: Run against actual webapp endpoints (not dry-run)
4. **Load Test**: Test with multiple concurrent users
5. **Production Deploy**: Only after 100% dry-run pass rate

## Maintenance

### Adding New Tests

1. Create new test method following naming convention: `test_*`
2. Add to `tests` list in `run_all_tests()`
3. Update this README with new test description
4. Increment total test count in documentation

### Modifying Tests

1. Update test logic in method
2. Update expected results in README
3. Re-run full suite to ensure no regressions
4. Update JSON schema if output format changes

## Support

For issues with test suite:

1. Check logs in `/root/HydraX-v2/tests/dry_run_results.json`
2. Review console output for specific error messages
3. Verify all prerequisite modules exist
4. Check Python version compatibility

## Performance Benchmarks

Expected timing (reference system):

- Test 1-3: < 100ms each (session operations)
- Test 4-6: < 50ms each (validation logic)
- Test 7-9: < 150ms each (includes sleep for expiry test)
- **Total Suite**: < 2000ms (2 seconds)

If tests exceed these benchmarks significantly, investigate:

- Database connection issues
- File I/O bottlenecks
- Network latency (if not fully mocked)
- CPU/memory constraints
