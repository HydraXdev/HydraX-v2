# BITTEN Mission Session - Operator Runbook

**Purpose**: Step-by-step manual testing guide for verifying the complete mission session flow
**Audience**: QA Engineers, DevOps, System Operators
**Status**: Production Ready
**Date**: October 5, 2025

---

## 🎯 Quick Reference

### Pre-Flight Checklist (5 min)

```bash
# 1. Verify all services running
pm2 list | grep -E "webapp|telegram|confirm"

# 2. Check database migration applied
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT * FROM schema_versions WHERE version = '002_mission_sessions';"

# 3. Verify JWT keys exist
ls -la /root/HydraX-v2/keys/jwt_*.pem

# 4. Run Go/No-Go validation
python3 /root/HydraX-v2/tests/go_no_go_validation.py

# All should show ✅ PASS
```

### Critical Endpoints

- **WebApp API**: http://localhost:8888 or https://www.joinbitten.com
- **Mission Page**: https://www.joinbitten.com/mission?ms=...&token=...
- **Status Page**: https://www.joinbitten.com/status
- **Stats Page**: https://www.joinbitten.com/stats

---

## 📋 Test Procedure

### Test 1: Generate Mission Session (Backend)

**Objective**: Create a test mission session with JWT token and deep link

**Steps**:

```bash
# 1. Create test session
python3 << 'EOF'
import sys
sys.path.append('/root/HydraX-v2')

from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager

# Create session
sm = get_session_manager()
session = sm.create_session(
    user_id='7176191872',  # Commander test account
    signal_id='TEST_SIGNAL_123',
    alert_id=999,
    pair='EURUSD',
    timeframe='M5',
    risk_max_usd=150.0,
    ttl_seconds=600  # 10 minutes
)

# Generate JWT token
jm = get_jwt_manager()
token = jm.generate_mission_token(
    user_id='7176191872',
    mission_session_id=session['mission_session_id'],
    alert_id=999,
    scopes=['mission:view', 'order:execute'],
    pair='EURUSD',
    timeframe='M5',
    risk_max_usd=150.0
)

# Print results
print("\n" + "="*70)
print("✅ Mission Session Created")
print("="*70)
print(f"\nSession ID: {session['mission_session_id']}")
print(f"Token: {token[:50]}...")
print(f"\nDeep Link:")
print(f"https://www.joinbitten.com/mission?ms={session['mission_session_id']}&token={token}")
print(f"\nExpires At: {session['expires_at']}")
print("="*70 + "\n")
EOF
```

**Expected Output**:

```
✅ Mission Session Created
Session ID: ms_01JXXXXXXXXX
Token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIs...
Deep Link: https://www.joinbitten.com/mission?ms=ms_01JXXXXXXXXX&token=eyJ...
Expires At: 1728123456
```

**Verification**:

- [ ] Session ID starts with `ms_`
- [ ] Token is a long JWT string
- [ ] Deep link is properly formatted
- [ ] Expires at timestamp is ~10 minutes from now

**Copy deep link for next tests**

---

### Test 2: Simulate Telegram Alert (Manual)

**Objective**: Verify alert message format and button link

**Steps**:

1. Open Telegram group where BITTEN posts alerts
2. **DO NOT POST REAL ALERT** - This is visual inspection only
3. Review what alert WOULD look like:

**Expected Alert Format**:

```
🎯 LIQUIDITY_SWEEP_REVERSAL Signal

Pair: EURUSD
Direction: BUY
Confidence: 85%
Session: LONDON
R:R: 1.5:1

Session expires in 10 minutes
```

**Button**: "📋 View Mission Brief" → `https://www.joinbitten.com/mission?ms=...&token=...`

**Verification**:

- [ ] Alert contains all required fields (pair, direction, confidence)
- [ ] Button URL matches deep link format
- [ ] Expiration warning visible

---

### Test 3: Mission Page Load (UI)

**Objective**: Verify mission page loads with token authentication

**Steps**:

1. **Open deep link from Test 1** in browser (incognito mode recommended)
2. **Observe page load sequence**:
   - Initial load (HTML/CSS/JS)
   - WebSocket connection attempt
   - Authentication handshake
   - Mission data population

**Expected Behavior**:

**A. Page Structure Loads**:

- [ ] Dark military theme (#0a0e1a background)
- [ ] "MISSION BRIEF" header visible
- [ ] Loading indicators show briefly

**B. WebSocket Connection (Check Browser Console F12)**:

```javascript
// Should see in console:
WebSocket connecting to wss://www.joinbitten.com/socket.io?t=eyJ...
✅ Authenticated: {user_id: "7176191872", scopes: ["mission:view", "order:execute"]}
Subscribed to topics: ["user.profile", "mission.alert/999", ...]
```

**C. Beacons Update**:

- [ ] **🟢 OPERATIONAL** beacon (system status)
- [ ] **🔒 SECURE** beacon (authenticated)
- [ ] **⚡ XX ms** beacon (latency < 100ms is good)

**D. Mission Dossier Populated**:

- [ ] Pair: EURUSD
- [ ] Direction: BUY arrow
- [ ] Entry price displayed
- [ ] Stop Loss shown
- [ ] Take Profit shown
- [ ] Risk amount calculated
- [ ] Position size calculated

**Troubleshooting**:

- **Stuck on "Loading"**: Check console for WebSocket errors
- **"Session Expired"**: Token TTL passed, generate new link
- **"Access Denied"**: Token validation failed, check JWT keys
- **No data**: Mission alert not published to event bus yet

---

### Test 4: Execute Action (Critical)

**Objective**: Fire a trade via mission session with validation

**Steps**:

**A. Review Pre-Execute State**:

- [ ] Mission data fully loaded
- [ ] Risk amount shown (should be ≤ $150 from riskMaxUsd)
- [ ] "🔫 EXECUTE" button enabled
- [ ] No error messages visible

**B. Click EXECUTE Button**:

1. Click the "🔫 EXECUTE" button
2. **DO NOT** confirm system dialog yet
3. Review calculated values:
   - Risk USD should match user's 2% of balance
   - Lot size should be appropriate for pair
   - TP/SL values should match mission dossier

4. **Confirm execution**

**Expected HTTP Flow** (Check Network Tab F12):

```
POST /api/fire
Headers:
  Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
  Content-Type: application/json

Body:
{
  "clientRequestId": "crid_a1b2c3d4-...",  // Random UUID
  "missionSessionId": "ms_01JXXXXXXXXX",
  "alertId": 999,
  "entry": 1.05234,
  "stopLoss": 1.05134,
  "takeProfit": 1.05382,
  "riskUsd": 100
}

Response: 202 Accepted
{
  "success": true,
  "opId": "op_xyz789",
  "status": "ACCEPTED"
}
```

**Expected UI Behavior**:

- [ ] **Immediate redirect** to `/status` page
- [ ] **OR** Show "Arming..." indicator briefly
- [ ] No error dialogs

**If Error Response**:

**401 Unauthorized**:

```json
{ "error": "Token expired", "success": false }
```

→ Expected: "Session Expired" screen with "Request New Link" button

**403 Forbidden**:

```json
{ "error": "Insufficient permissions", "success": false }
```

→ Expected: "Access Denied" screen

**409 Conflict**:

```json
{ "error": "Session already executed", "success": false }
```

→ Expected: "Order Already Executed" screen with "View Status" button

**410 Gone**:

```json
{ "error": "Session expired", "success": false }
```

→ Expected: "Mission Session Expired" screen

**422 Unprocessable**:

```json
{ "error": "Risk exceeds maximum (150 USD)", "success": false }
```

→ Expected: Error message with "Try Again" option

**Database Verification**:

```bash
# Check fire was created
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT fire_id, status, ticket, user_id FROM fires ORDER BY created_at DESC LIMIT 1;"

# Check session marked as EXECUTED
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT mission_session_id, status, executed_at FROM mission_sessions ORDER BY created_at DESC LIMIT 1;"
```

**Expected**:

```
fire_id              status    ticket    user_id
-------------------  --------  --------  -----------
FIRE_TEST_123_...    SENT      NULL      7176191872

mission_session_id   status     executed_at
-------------------  ---------  ------------
ms_01JXXXXXXXXX      EXECUTED   1728123456
```

---

### Test 5: Observe Events (Real-Time)

**Objective**: Verify WebSocket events delivered in real-time

**Steps**:

**A. Status Page Opens** (after redirect from Test 4)

**B. Open Browser Console** (F12 → Console tab)

**C. Watch for Events**:

**Event 1: trades.delta (ARMING)**:

```javascript
{
  type: "trades.delta",
  id: "temp_op_xyz789",
  pair: "EURUSD",
  status: "ARMING",
  entry: 1.05234,
  current: 1.05234,
  pnl: 0,
  timestamp: 1728123456
}
```

**Timing**: Should arrive within **50-100ms** of execute

**Event 2: ops.confirmation (FILLED)**:

```javascript
{
  type: "ops.confirmation",
  opId: "op_xyz789",
  status: "FILLED",
  ticket: 123456,
  filledPrice: 1.05236,
  timestamp: 1728123457
}
```

**Timing**: Should arrive within **100-250ms** of ARMING

**Event 3: trades.delta (FILLED)**:

```javascript
{
  type: "trades.delta",
  id: "fire_123",
  ticket: 123456,
  status: "FILLED",
  current: 1.05236,
  pnl: 0,
  timestamp: 1728123457
}
```

**Timing**: Immediately after confirmation

**D. Status Page UI Updates**:

- [ ] **Position tile appears** with:
  - Pair: EURUSD
  - Direction: BUY (green)
  - Entry: 1.05236
  - Current: (live price updates)
  - P&L: (updates in real-time)
  - Status: OPEN

- [ ] **Latency badge updates**: Should show ~50-80ms

**E. Performance Check**:

```javascript
// In browser console
performance.getEntriesByType("navigation")[0].loadEventEnd -
  performance.getEntriesByType("navigation")[0].fetchStart;
// Should be < 2000ms
```

**Verification**:

- [ ] ARMING event received < 100ms
- [ ] FILLED event received < 250ms
- [ ] UI updates smoothly
- [ ] No JavaScript errors in console
- [ ] P&L updates in real-time

---

### Test 6: Idempotency Probe (Security)

**Objective**: Verify duplicate requests don't create duplicate orders

**Steps**:

**A. Go Back to Mission Page**:

- Use browser back button
- **OR** Open same deep link from Test 1 in new tab

**B. Click EXECUTE Again**:

**Expected Behavior - Option 1 (Session Already Executed)**:

```
HTTP 409 Conflict
{
  "error": "Session already executed",
  "success": false
}
```

→ UI shows: "Order Already Executed" screen with "View Status" button

**Expected Behavior - Option 2 (Cached Response)**:

```
HTTP 202 Accepted
{
  "success": true,
  "opId": "op_xyz789",  // SAME opId as before
  "status": "ACCEPTED"
}
```

→ UI redirects to /status (no new trade created)

**Database Verification**:

```bash
# Count fires for this user
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) FROM fires WHERE user_id = '7176191872' AND created_at > strftime('%s', 'now', '-1 hour');"
```

**Expected**: Count should be **1** (not 2)

**Idempotency Cache Check**:

```bash
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT cache_key, op_id, created_at FROM idempotency_cache ORDER BY created_at DESC LIMIT 1;"
```

**Expected**: Entry exists with matching opId

**Verification**:

- [ ] Second execute does NOT create duplicate trade
- [ ] Same opId returned
- [ ] Idempotency cache has entry
- [ ] UI handles gracefully (no error shown or shows "already executed")

---

### Test 7: Expiry Probe (Security)

**Objective**: Verify expired sessions cannot be executed

**Steps**:

**A. Generate Expired Session**:

```bash
# Create session with 10 second TTL
python3 << 'EOF'
import sys, time
sys.path.append('/root/HydraX-v2')

from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager

sm = get_session_manager()
session = sm.create_session(
    user_id='7176191872',
    signal_id='EXPIRE_TEST',
    alert_id=998,
    pair='GBPUSD',
    ttl_seconds=10  # 10 seconds only
)

jm = get_jwt_manager()
token = jm.generate_mission_token(
    user_id='7176191872',
    mission_session_id=session['mission_session_id'],
    alert_id=998,
    scopes=['mission:view', 'order:execute'],
    ttl_seconds=10
)

deep_link = f"https://www.joinbitten.com/mission?ms={session['mission_session_id']}&token={token}"
print(f"\nDeep Link (expires in 10 seconds):\n{deep_link}\n")
EOF
```

**B. Wait for Expiry**:

```bash
echo "Waiting 15 seconds for session to expire..."
sleep 15
echo "✅ Session should now be expired"
```

**C. Open Expired Link**:

1. Open the deep link in browser
2. Page should load normally
3. Click EXECUTE button

**Expected Behavior**:

**HTTP Response**:

```
POST /api/fire
Response: 410 Gone
{
  "error": "Session expired",
  "success": false
}
```

**UI Behavior**:

- [ ] Shows "Mission Session Expired" screen
- [ ] Message: "This mission session has expired. Please request a new link."
- [ ] "Return to Dashboard" button visible
- [ ] No execute button visible

**Database Verification**:

```bash
# Check session status
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT mission_session_id, status, expires_at, (expires_at - strftime('%s', 'now')) as seconds_until_expiry FROM mission_sessions WHERE signal_id = 'EXPIRE_TEST';"
```

**Expected**:

```
mission_session_id   status    expires_at  seconds_until_expiry
-------------------  --------  ----------  --------------------
ms_01JXXXXXXXXX      PENDING   1728123456  -5 (negative = expired)
```

**Verification**:

- [ ] Expired session rejected with 410
- [ ] UI shows expiry message
- [ ] No trade created
- [ ] Session status remains PENDING (not EXECUTED)

---

### Test 8: Risk Fuse (Security)

**Objective**: Verify risk limits enforced server-side

**Steps**:

**A. Generate Session with Low Risk Limit**:

```bash
python3 << 'EOF'
import sys
sys.path.append('/root/HydraX-v2')

from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager

sm = get_session_manager()
session = sm.create_session(
    user_id='7176191872',
    signal_id='RISK_TEST',
    alert_id=997,
    pair='EURUSD',
    risk_max_usd=50.0  # Very low limit
)

jm = get_jwt_manager()
token = jm.generate_mission_token(
    user_id='7176191872',
    mission_session_id=session['mission_session_id'],
    alert_id=997,
    scopes=['mission:view', 'order:execute'],
    risk_max_usd=50.0  # Limit $50
)

deep_link = f"https://www.joinbitten.com/mission?ms={session['mission_session_id']}&token={token}"
print(f"\nDeep Link (risk limit: $50):\n{deep_link}\n")
EOF
```

**B. Open Link and Attempt Execute**:

1. Open deep link
2. **Manually modify** request in browser dev tools:
   - Open Network tab
   - Click EXECUTE
   - **Before** request sends, right-click → Edit and Resend
   - Change `riskUsd` to `100` (exceeds limit of 50)
   - Send modified request

**Expected Behavior**:

**HTTP Response**:

```
POST /api/fire
Body: {"riskUsd": 100, ...}  // Exceeds limit of 50

Response: 422 Unprocessable Entity
{
  "error": "Risk exceeds maximum (50 USD)",
  "success": false
}
```

**UI Behavior**:

- [ ] Shows validation error message
- [ ] Error clearly states: "Risk exceeds maximum ($50)"
- [ ] "Try Again" button allows retry
- [ ] NO trade created

**Database Verification**:

```bash
# Should be NO fire record for this session
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) FROM fires WHERE user_id = '7176191872' AND created_at > strftime('%s', 'now', '-1 minute');"
```

**Expected**: Count = **0** (no trade created)

**Audit Log Check**:

```bash
tail -5 /var/log/bitten/audit.log | jq 'select(.event_type == "fire.risk_violation")'
```

**Expected**:

```json
{
  "timestamp": "2025-10-05T...",
  "level": "WARNING",
  "event_type": "fire.risk_violation",
  "message": "Risk guardrail violation",
  "sub": "7176191872",
  "ms": "ms_01JXXXXXXXXX",
  "requested_risk": 100.0,
  "max_risk": 50.0
}
```

**Verification**:

- [ ] Request rejected with 422
- [ ] Clear error message shown
- [ ] No trade created
- [ ] Audit log entry created

---

### Test 9: Stats Page (Integration)

**Objective**: Verify stats page reflects executed trades

**Steps**:

**A. Navigate to Stats Page**:

```
https://www.joinbitten.com/stats
```

**B. Check Components Updated**:

**1. Equity Chart**:

- [ ] New data point appears for trade execution
- [ ] Chart updates in real-time
- [ ] Smooth animation

**2. Recent Events Feed**:

- [ ] Trade execution event visible:
  ```
  🔫 FIRE - EURUSD BUY @ 1.05234
  ```
- [ ] Timestamp recent (< 1 minute ago)

**3. KPIs Section**:

- [ ] Total Trades count increased by 1
- [ ] Win Rate updated (if trade closed)
- [ ] Total P&L updated

**4. Distribution Charts**:

- [ ] Pair Distribution shows EURUSD
- [ ] Session Distribution shows session (LONDON/NY/etc)

**WebSocket Events** (Check Console):

```javascript
{
  type: "stats.equity",
  equity: 10015.00,
  timestamp: 1728123456
}

{
  type: "stats.events",
  event: {
    type: "FIRE",
    pair: "EURUSD",
    direction: "BUY",
    price: 1.05234
  }
}
```

**Verification**:

- [ ] Stats page reflects new trade
- [ ] Real-time updates working
- [ ] Charts render correctly
- [ ] No console errors

---

## 🎯 Success Criteria

### All Tests Must Pass

- [ ] **Test 1**: Session created with valid JWT ✅
- [ ] **Test 2**: Alert format verified ✅
- [ ] **Test 3**: Mission page loads and authenticates ✅
- [ ] **Test 4**: Execute creates trade successfully ✅
- [ ] **Test 5**: Events delivered < 250ms ✅
- [ ] **Test 6**: Idempotency prevents duplicates ✅
- [ ] **Test 7**: Expired sessions rejected ✅
- [ ] **Test 8**: Risk limits enforced ✅
- [ ] **Test 9**: Stats page updated ✅

### Performance Benchmarks

- [ ] Page load < 2000ms
- [ ] WebSocket auth < 100ms
- [ ] ARMING event < 100ms
- [ ] FILLED event < 250ms
- [ ] No errors in browser console
- [ ] No errors in server logs

---

## 🚨 Rollback Procedure

**If any test fails critically**:

```bash
# 1. Stop webapp
pm2 stop webapp

# 2. Revert to previous version
cd /root/HydraX-v2
git checkout HEAD~1 webapp_server_optimized.py

# 3. Restart webapp
pm2 restart webapp

# 4. Verify legacy flow still works
curl http://localhost:8888/healthz

# 5. Create incident report
echo "Mission session rollback: $(date)" >> /var/log/bitten/incidents.log
```

---

## 📞 Support

**Issue Reporting**:

- Logs: `/var/log/bitten/audit.log`
- Results: `/root/HydraX-v2/tests/dry_run_results.json`
- Database: `/root/HydraX-v2/bitten.db`

**Contact**: Escalate to development team with:

- Test number that failed
- Screenshots of UI state
- Browser console logs
- Server logs from pm2

---

**This runbook provides complete manual testing coverage for QA sign-off before production deployment.**
