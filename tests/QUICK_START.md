# BITTEN Mission Flow Dry-Run Tests - Quick Start

## 🚀 Run Tests (One Command)

```bash
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py
```

## 📊 View Results

```bash
# Pretty print JSON results
cat /root/HydraX-v2/tests/dry_run_results.json | python3 -m json.tool

# Quick pass/fail check
echo "Exit code: $?"  # 0 = all pass, 1 = some failed
```

## ✅ Expected Output (All Tests Pass)

```
======================================================================
🎯 BITTEN MISSION FLOW DRY-RUN TEST SUITE
======================================================================

[STEP 1] Generate Test Mission Session
  ✓ PASS (45ms)
    ms: MS_1728123456_ABC123
    deep_link: http://localhost:8888/mission?ms=MS_1728123456_ABC123&token=eyJ...
    expires_at: 2025-10-05T17:54:56

[STEP 2] Simulate Telegram Alert
  ✓ PASS (12ms)
    alert_length: 245
    deep_link_included: True

[STEP 3] Test Mission Page Load
  ✓ PASS (23ms)
    token_valid: True
    scopes: ['mission:view', 'order:execute']
    beacons: {'operational': True, 'secure': True, 'latency': 45}

[STEP 4] Test Execute Action
  ✓ PASS (18ms)
    client_request_id: f47ac10b-58cc-4372-a567-0e02b2c3d479
    op_id: OP_1728123456789
    response_code: 202
    redirect_to: /status?opId=OP_1728123456789

[STEP 5] Test Event Delivery
  ✓ PASS (34ms)
    event_count: 3
    latency_ms: 150
    latency_ok: True

[STEP 6] Test Idempotency
  ✓ PASS (8ms)
    original_op_id: OP_1728123456789
    duplicate_op_id: OP_1728123456789
    idempotency_preserved: True
    expected_response_code: 202 or 409

[STEP 7] Test Session Expiry
  ✓ PASS (1015ms)
    expired_session_rejected: True
    error_message: session expired
    expected_response_code: 410

[STEP 8] Test Risk Fuse
  ✓ PASS (5ms)
    risk_requested: 150.0
    risk_max: 100.0
    risk_exceeded: True
    expected_response_code: 422
    expected_error: Risk $150.0 exceeds maximum $100.0

[STEP 9] Test Stats Page
  ✓ PASS (7ms)
    equity_updated: True
    new_equity: 855.95
    trade_in_recent_events: True

📊 TEST SUMMARY
Total Tests: 9
Passed: 9
Failed: 0
Duration: 1234ms

🎉 ALL TESTS PASSED
```

## ❌ Current Status (Before Implementation)

```
📊 TEST SUMMARY
Total Tests: 9
Passed: 0
Failed: 9
Duration: 7ms

❌ SOME TESTS FAILED
```

**Reason**: session_manager.py module doesn't exist yet

## 🔧 Implementation Checklist

Before tests can pass, implement these components:

- [ ] `/root/HydraX-v2/src/missions/session_manager.py`
  - [ ] `create_mission_session()` - Generate session + JWT + deep link
  - [ ] `validate_session_token()` - Verify JWT and expiry
  - [ ] `get_mission_data()` - Fetch mission from database

- [ ] `/root/HydraX-v2/webapp_server_optimized.py` endpoints:
  - [ ] `GET /mission?ms=<id>&token=<jwt>` - Mission page load
  - [ ] `POST /api/fire` - Execute fire command with Authorization header
  - [ ] `GET /status?opId=<id>` - Status page with SSE events
  - [ ] `GET /stats` - Stats page with equity/trade history

- [ ] Database tables:
  - [ ] `mission_sessions` - Store session IDs, tokens, expiry
  - [ ] `fires` - Track fire operations with opId and clientRequestId
  - [ ] `idempotency_cache` - Prevent duplicate submissions

## 🎯 What Each Test Validates

| Test                        | What It Checks                                     | Required Components               |
| --------------------------- | -------------------------------------------------- | --------------------------------- |
| 1. Generate Mission Session | Session creation, JWT generation, deep link format | session_manager module            |
| 2. Simulate Telegram Alert  | Alert message format, deep link inclusion          | session_manager module            |
| 3. Mission Page Load        | Token validation, mission data fetch, beacons      | session_manager + webapp endpoint |
| 4. Execute Action           | Fire command creation, API response, redirect      | webapp /api/fire endpoint         |
| 5. Event Delivery           | SSE event streaming, latency < 250ms               | Event bus + WebSocket handler     |
| 6. Idempotency              | Duplicate prevention, same opId returned           | Idempotency cache system          |
| 7. Session Expiry           | Expired token rejection, 410 response              | session_manager validation        |
| 8. Risk Fuse                | Risk limit enforcement, 422 response               | Risk validation in /api/fire      |
| 9. Stats Page               | Equity updates, trade history display              | Stats endpoint + database         |

## 📁 Related Files

- **Test Script**: `/root/HydraX-v2/tests/dry_run_mission_flow.py`
- **Test Results**: `/root/HydraX-v2/tests/dry_run_results.json`
- **Documentation**: `/root/HydraX-v2/tests/README_DRY_RUN.md`
- **Setup Script**: `/root/HydraX-v2/tests/setup_test_env.sh`

## 🔄 Development Workflow

```bash
# 1. Implement session_manager.py
vim /root/HydraX-v2/src/missions/session_manager.py

# 2. Run tests to check progress
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py

# 3. Fix failures one by one (tests are sequential)
# Tests will show which component is missing

# 4. Repeat until all green
# Expected outcome: 9/9 tests passed
```

## 🎓 Understanding Test Output

### ✅ Green = PASS

```
  ✓ PASS (45ms)
    ms: MS_1728123456_ABC123
```

Component working correctly, data looks valid

### ❌ Red = FAIL

```
  ✗ FAIL (7ms)
  Error: session_manager not found
```

Component missing or broken, implement/fix required

### ⚠️ Yellow Details

```
    ms: MS_1728123456_ABC123
    deep_link: http://localhost:8888/mission?ms=...
```

Additional verification data from test

## 💡 Pro Tips

1. **Sequential Testing**: Tests run in order, later tests depend on earlier ones
2. **Fast Feedback**: Total run time < 2 seconds when all components exist
3. **No Side Effects**: Dry-run tests don't modify production data
4. **Exit Codes**: Script returns 0 only if ALL tests pass (CI/CD friendly)
5. **JSON Output**: Structured results for automated parsing

## 🚨 Troubleshooting

**Problem**: Tests hang or timeout
**Solution**: Check if session_manager has infinite loops

**Problem**: Import errors
**Solution**: Run `python3 /root/HydraX-v2/tests/setup_test_env.sh` first

**Problem**: Permission errors
**Solution**: Run `chmod +x /root/HydraX-v2/tests/dry_run_mission_flow.py`

**Problem**: Module not found
**Solution**: Verify `/root/HydraX-v2/src/missions/__init__.py` exists

## 📞 Support

For test suite issues:

1. Check `/root/HydraX-v2/tests/dry_run_results.json` for detailed error info
2. Review console output for stack traces
3. Verify all prerequisite directories exist
4. Confirm Python 3.8+ installed

---

**Remember**: These are DRY-RUN tests. They simulate the flow WITHOUT executing real trades or sending Telegram messages. Safe to run anytime!
