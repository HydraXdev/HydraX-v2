# 🎯 SIGNAL FLOW & AUTO-FIRE ARCHITECTURE - DEFINITIVE GUIDE

**Last Updated**: October 6, 2025
**Status**: ✅ PRODUCTION - All systems operational after emergency repairs
**Purpose**: Prevent future agents from debugging the same issues

---

## 📋 TABLE OF CONTENTS

1. [Complete Signal Flow](#complete-signal-flow)
2. [Auto-Fire System](#auto-fire-system)
3. [Telegram Alert System](#telegram-alert-system)
4. [Fire Execution Pipeline](#fire-execution-pipeline)
5. [EA Confirmation Flow](#ea-confirmation-flow)
6. [Database Status Management](#database-status-management)
7. [Common Issues & Debugging](#common-issues--debugging)

---

## 🔄 COMPLETE SIGNAL FLOW

### End-to-End Journey (Elite Guard → MT5 → Telegram → Database)

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: SIGNAL GENERATION (Elite Guard)                           │
└─────────────────────────────────────────────────────────────────────┘
Elite Guard (PID varies, check pm2 list)
  ↓ Subscribes to ZMQ port 5560 (market data)
  ↓ Detects pattern (6 integrated detectors)
  ↓ Calculates confidence (70-99%)
  ↓ Publishes to ZMQ port 5557
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: SIGNAL ROUTING (Redis Bridge)                             │
└─────────────────────────────────────────────────────────────────────┘
signals_zmq_to_redis.py
  ↓ Subscribes to ZMQ port 5557
  ↓ Strips "ELITE_GUARD_SIGNAL " prefix
  ↓ Pushes to Redis stream "signals"
  ↓
signals_redis_to_webapp_fixed.py
  ↓ Reads from Redis stream
  ↓ HTTP POST to http://localhost:8888/api/signals
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: WEBAPP PROCESSING (webapp_server_optimized.py)            │
└─────────────────────────────────────────────────────────────────────┘
POST /api/signals endpoint (line 417)
  ↓
  ├─ Line 449-474: INSERT signal to database (signals table)
  │  └─ For outcome tracking (WIN/LOSS analysis)
  ↓
  ├─ Line 447: BittenCore.process_venom_signal(signal_data)
  │  └─ src/bitten_core/bitten_core.py:738
  │     ├─ CITADEL Shield analysis
  │     └─ Line 938: dispatch_group_signal() ← TELEGRAM ALERT SENT HERE
  │        └─ athena_group_dispatcher.py:59
  │           └─ Sends to group -1002581996861
  ↓
  └─ Line 480-732: AUTO FIRE CHECK
     ├─ Line 482: Extract confidence from signal_data
     ├─ Line 502-516: Query fire_modes.db for AUTO users
     │  └─ SQL: WHERE current_mode = 'AUTO'
     │           AND confidence >= auto_fire_min_confidence
     │           AND confidence <= auto_fire_max_confidence
     │           AND subscription_tier = 'COMMANDER'
     ├─ Line 525: fire_mode_db.can_user_fire_trade() validation
     │  └─ Checks slots (max 10 for COMMANDER)
     │  └─ Checks daily limit (6 trades/day)
     ├─ Line 544-557: Cross-reference with fresh EA (< 120s heartbeat)
     └─ Line 563-720: Execute fire command via enqueue_fire()

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: FIRE EXECUTION (enqueue_fire.py → command_router → EA)    │
└─────────────────────────────────────────────────────────────────────┘
enqueue_fire.py:create_fire_command()
  ↓ Line 40: Round lot size to 2 decimals (0.09 not 0.094476)
  ↓ Line 464-500: Create OrderedDict with EXACT field order
  │  └─ CRITICAL: "type" MUST be first field
  │  └─ Order: type, target_uuid, fire_id, symbol, direction, entry, sl, tp, lot
  ↓ Step 1 (execute_fire_proper.py:52-88): Create database record FIRST
  │  └─ INSERT INTO fires (status='SENT')
  ↓ Step 2: Send to IPC queue (ipc:///tmp/bitten_cmdqueue)
  ↓
command_router.py (PID varies, port 5555)
  ↓ Pulls from IPC queue
  ↓ Routes to EA via ZMQ DEALER socket
  ↓
EA v3.005 (COMMANDER_DEV_001)
  ↓ Receives fire command
  ↓ Validates SL/TP positioning (BUY: SL < entry, TP > entry)
  ↓ Executes trade in MT5
  ↓ Sends confirmation to port 5558

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: CONFIRMATION HANDLING (confirm_listener_v207.py)          │
└─────────────────────────────────────────────────────────────────────┘
confirm_listener_v207.py (PID varies, port 5558)
  ↓ Receives TWO message types:
  │  1. type="confirmation" (status, ticket, price)
  │  2. type="position_opened" (ticket only)
  ↓ Line 474-476: Routes position_opened → handle_confirmation()
  ↓ Line 153-160: Maps status to database status
  │  └─ "success"|"filled"|"ok" → FILLED
  │  └─ "failed"|"rejected"|"error" → FAILED
  │  └─ Other → UNKNOWN
  ↓ Line 177-186: PROTECTION LOGIC (CRITICAL!)
  │  └─ Checks existing status before update
  │  └─ Line 184: Prevents downgrade FILLED → UNKNOWN/FAILED
  │  └─ "Don't downgrade FILLED with ticket to anything else"
  ↓ Line 189-193: UPDATE fires SET status, ticket, price
  └─ Line 201-217: INSERT into live_positions if FILLED
```

---

## ⚡ AUTO-FIRE SYSTEM

### Configuration (User 7176191872)

**Database**: `/root/HydraX-v2/data/fire_modes.db`
**Table**: `user_fire_modes`

```sql
user_id: 7176191872
current_mode: AUTO
auto_fire_enabled: 1
auto_fire_min_confidence: 80.0
auto_fire_max_confidence: 95.0
max_auto_slots: 10
subscription_tier: COMMANDER
trading_enabled: 1
```

### Auto-Fire Requirements (ALL must be TRUE)

1. ✅ **Signal confidence in range**: 80.0% ≤ confidence ≤ 95.0%
2. ✅ **User mode = AUTO**: Stored in fire_modes.db
3. ✅ **Tier = COMMANDER**: Only COMMANDER tier can auto-fire
4. ✅ **Slots available**: < 10 concurrent positions
5. ✅ **Daily limit**: < 6 trades per day
6. ✅ **Fresh EA connection**: Last heartbeat within 120 seconds
7. ✅ **No hedge conflict**: No opposing position on same symbol

### Auto-Fire Decision Logic

**Location**: `webapp_server_optimized.py` lines 480-732

```python
# Line 502-516: Find eligible users
fire_cursor.execute("""
    SELECT user_id, max_auto_slots, subscription_tier,
           auto_fire_min_confidence, auto_fire_max_confidence, auto_fire_enabled
    FROM user_fire_modes
    WHERE current_mode = 'AUTO'
    AND auto_fire_enabled = 1
    AND trading_enabled = 1
    AND subscription_tier = 'COMMANDER'
    AND ? >= auto_fire_min_confidence
    AND ? <= auto_fire_max_confidence
""", (signal_confidence, signal_confidence))

# Line 525: Validate slots and daily limits
fire_check = fire_mode_db.can_user_fire_trade(str(user_id), 'AUTO')

# Line 544-557: Verify fresh EA connection
auto_cursor.execute("""
    SELECT DISTINCT ea.user_id, ea.target_uuid, ea.last_balance
    FROM ea_instances ea
    WHERE ea.user_id = ?
    AND (strftime('%s','now') - ea.last_seen) <= 120
""", (user_id,))
```

### Why Auto-Fire Might Not Trigger

**Check in order**:

1. **Signal confidence outside range**:

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT signal_id, symbol, confidence FROM signals ORDER BY created_at DESC LIMIT 10;"
   ```

   If all signals show 70-79%, auto-fire WON'T trigger (below 80% min)

2. **Mode not set to AUTO**:

   ```bash
   sqlite3 /root/HydraX-v2/data/fire_modes.db "SELECT current_mode FROM user_fire_modes WHERE user_id = '7176191872';"
   ```

3. **Slots full** (10/10 used):

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM fires WHERE status IN ('FILLED', 'SENT', 'PENDING');"
   ```

4. **EA not fresh** (> 120s since heartbeat):
   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT (strftime('%s','now') - last_seen) AS age FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"
   ```

---

## 📱 TELEGRAM ALERT SYSTEM

### Architecture (SINGLE DISPATCH ONLY!)

**CRITICAL**: Telegram alerts are sent ONCE from BittenCore, NOT from webapp!

```
Signal → BittenCore.process_venom_signal()
       → Line 938: dispatch_group_signal(signal_data)
       → athena_group_dispatcher.py
       → Telegram API sendMessage
       → Group: -1002581996861
```

### The Duplicate Alert Bug (FIXED October 6, 2025)

**Root Cause**: Webapp was calling `dispatch_group_signal()` AFTER BittenCore already dispatched.

**Fix Applied**: `webapp_server_optimized.py` lines 476-478

```python
# BEFORE (BROKEN - caused duplicates):
athena_result = dispatch_group_signal(signal_data)

# AFTER (FIXED):
# ATHENA TELEGRAM ALERT - Handled by BittenCore.process_venom_signal()
# DO NOT dispatch here - would cause duplicate alerts
# BittenCore handles dispatch at line 938 in bitten_core.py
```

**Result**: Only ONE telegram message per signal (verified with message IDs 16691, 16692, 16693).

### Alert Message Format

**File**: `athena_group_dispatcher.py` lines 104-106

```python
message = f"""{mode_icon} {mode_tag} • {symbol} {direction} • {confidence}% • {pattern_type}
mission ready
📥 [Mission Brief]({hud_url})"""

# Example:
# ⚡ RAPID • EURJPY SELL • 77.6% • Kalman Quickfire
# mission ready
# 📥 [Mission Brief](http://134.199.204.67:8888/brief?signal_id=ELITE_RAPID_EURJPY_1759789385)
```

### Confidence Display Fix (October 6, 2025)

**Problem**: All alerts showed 0% confidence

**Root Cause**: `athena_group_dispatcher.py` line 70 looked for non-existent field:

```python
# BEFORE (BROKEN):
tcs_score = signal_data.get('tcs_score', 0)  # Always defaults to 0!
confidence = round(tcs_score, 1)

# AFTER (FIXED):
tcs_score = signal_data.get('tcs_score') or signal_data.get('confidence', 0)
confidence = round(float(tcs_score), 1) if tcs_score else 0
```

**Result**: Alerts now show correct confidence (70%, 77.6%, 83.1%, etc.)

---

## 🔥 FIRE EXECUTION PIPELINE

### Database-First Approach (CRITICAL!)

**File**: `execute_fire_proper.py`

**Rule**: ALWAYS create database record BEFORE sending to IPC queue!

```python
# STEP 1: Create database record FIRST (lines 52-88)
cursor.execute('''
    INSERT INTO fires (
        fire_id, mission_id, user_id, status,
        symbol, direction, sl, tp, lot,
        target_uuid, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (fire_id, mission_id, user_id, 'SENT', ...))

# STEP 2: Send to IPC queue (lines 90-146)
push.send_json(dict(fire_cmd))
```

**Why This Order Matters**: EA confirmations arrive asynchronously. If no database record exists, confirmations are dropped!

### Fire Command Format (EA v3.005 Contract)

**EXACT JSON structure** (field order MATTERS!):

```json
{
  "type": "fire",
  "target_uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_EURJPY_1759789385",
  "symbol": "EURJPY",
  "direction": "SELL",
  "entry": 0,
  "sl": 162.45,
  "tp": 162.1,
  "lot": 0.09
}
```

**CRITICAL RULES**:

1. **"type": "fire"** MUST be first field
2. **Direction**: UPPERCASE "BUY" or "SELL" (never "buy", "sell", "long")
3. **Numbers**: NOT quoted (use 0.09 not "0.09")
4. **Lot rounding**: Round to 2 decimals (`round(lot, 2)`)
5. **Entry = 0**: Market order (EA uses current price)
6. **SL/TP positioning**:
   - BUY: SL < entry price, TP > entry price
   - SELL: SL > entry price, TP < entry price

### SL/TP Validation (EA Pre-Flight Check)

**EA will reject trades** with invalid SL/TP positioning:

```mql5
// EA validation logic (lines 442-479)
if(is_buy && tp <= price){
    Print("[FIRE-ABORT] BUY order has TP <= entry price");
    SendConfirmation("fire", false, 0, 0, "Invalid TP", fire_id, symbol);
    return;
}
```

**Result**: Trade never reaches MT5, no ticket number, status stays "SENT"

---

## ✅ EA CONFIRMATION FLOW

### Confirmation Message Types

EA sends TWO types of confirmation messages:

1. **type="confirmation"**: Initial trade execution

   ```json
   {
     "type": "confirmation",
     "fire_id": "ELITE_RAPID_EURJPY_1759789385",
     "status": "success",
     "ticket": 22165337,
     "price": 162.425,
     "lot": 0.09
   }
   ```

2. **type="position_opened"**: Position lifecycle event
   ```json
   {
     "type": "position_opened",
     "fire_id": "ELITE_RAPID_EURJPY_1759789385",
     "ticket": 22165337,
     "symbol": "EURJPY",
     "direction": "SELL"
   }
   ```

### Confirmation Handler (confirm_listener_v207.py)

**Location**: Lines 471-476

```python
# Route to appropriate handler
if msg_type == "confirmation":
    handle_confirmation(m)
elif msg_type == "position_opened":
    # EA sends position_opened events - treat as confirmation
    handle_confirmation(m)  # ← CRITICAL: Don't drop these!
```

**Before Fix**: `position_opened` messages were dropped as "Unknown message type"
**After Fix**: Both message types update the fires table

### Status Downgrade Protection (CRITICAL!)

**Problem**: `position_opened` messages arrive AFTER confirmations and overwrite good data!

**Example Timeline**:

```
22:13:05 - confirmation arrives → UPDATE fires SET status='FILLED', ticket=22165337, price=162.425
22:13:06 - position_opened arrives → Would UPDATE to status='UNKNOWN', price=0.0
```

**Fix Applied**: Lines 180-186

```python
# Check existing status first
cur.execute("SELECT status, ticket FROM fires WHERE fire_id=?", (fire_id,))
existing = cur.fetchone()

should_update = True
if existing:
    existing_status, existing_ticket = existing
    # Don't downgrade FILLED with ticket to anything else (FAILED or UNKNOWN)
    if existing_status == "FILLED" and existing_ticket > 0 and db_status != "FILLED":
        should_update = False
        LOG.info(f"[CONFIRM] Ignoring {db_status} update for {fire_id} - already FILLED with ticket {existing_ticket}")
```

**Result**: Once a trade is FILLED with a ticket, it STAYS filled!

---

## 💾 DATABASE STATUS MANAGEMENT

### Status Flow (fires table)

```
SENT → FILLED → CLOSED
  ↓       ↓
FAILED  UNKNOWN (should not happen with protection)
```

### Status Definitions

| Status        | Meaning                                        | Set By                           |
| ------------- | ---------------------------------------------- | -------------------------------- |
| `SENT`        | Fire command sent to EA, awaiting confirmation | execute_fire_proper.py:66        |
| `FILLED`      | Trade executed in MT5, has ticket number       | confirm_listener.py:156          |
| `FAILED`      | EA rejected trade (validation failure)         | confirm_listener.py:157          |
| `UNKNOWN`     | Confirmation without status field              | confirm_listener.py:160          |
| `CLOSED`      | Position closed (TP/SL/manual)                 | position_closed handler          |
| `CLOSED_SYNC` | Manual cleanup (sync with MT5)                 | emergency_position_cleanup.py:54 |

### Database Sync Issues

**Problem**: Database shows 122 stale positions, MT5 only has 2 open

**Root Cause**: Position sync service not updating when trades close in MT5

**Fix**: `emergency_position_cleanup.py`

```python
# Close all FILLED positions (they're closed in MT5)
cursor.execute("""
    UPDATE fires
    SET status = 'CLOSED_SYNC',
        updated_at = ?,
        close_reason = 'CLOSED_IN_MT5_MANUAL_SYNC'
    WHERE status = 'FILLED'
""", (current_time,))
```

**When to Run**: If auto-fire fails with "slots full" but MT5 shows positions are closed

---

## 🔍 COMMON ISSUES & DEBUGGING

### Issue 1: Auto-Fire Not Triggering

**Symptoms**: Signals at 83% confidence not executing automatically

**Debug Steps**:

1. **Check signal confidence**:

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT signal_id, symbol, confidence FROM signals ORDER BY created_at DESC LIMIT 5;"
   ```

2. **Verify auto-fire config**:

   ```bash
   sqlite3 /root/HydraX-v2/data/fire_modes.db "SELECT auto_fire_min_confidence, auto_fire_max_confidence, current_mode FROM user_fire_modes WHERE user_id = '7176191872';"
   ```

3. **Check slot usage**:

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM fires WHERE status IN ('FILLED', 'SENT', 'PENDING');"
   ```

4. **Verify EA freshness**:

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"
   ```

5. **Check webapp logs for auto-fire logic**:
   ```bash
   grep "Checking AUTO fire\|AUTO FIRE CANDIDATES\|AUTO FIRE TRIGGERED" /tmp/webapp.log | tail -20
   ```

**Common Causes**:

- ❌ Signal confidence 70-79% (below 80% minimum)
- ❌ Slots full (10/10 used)
- ❌ EA heartbeat stale (> 120 seconds)
- ❌ Mode not set to AUTO

### Issue 2: Duplicate Telegram Alerts

**Symptoms**: Same signal sends TWO telegram messages

**Root Cause**: Both BittenCore AND webapp calling `dispatch_group_signal()`

**Fix Verification**:

```bash
grep "dispatch_group_signal" /root/HydraX-v2/webapp_server_optimized.py
# Should show: "# BittenCore handles dispatch" (commented out)
```

**Restart Webapp**:

```bash
ps aux | grep webapp_server_optimized.py | grep -v grep | awk '{print $2}' | xargs kill
nohup python3 webapp_server_optimized.py > /tmp/webapp.log 2>&1 &
```

### Issue 3: Confirmations Showing status=UNKNOWN

**Symptoms**: Trades execute (have ticket) but status shows UNKNOWN

**Root Cause**: `position_opened` messages overwriting good confirmations

**Fix Verification**:

```bash
grep "Don't downgrade FILLED" /root/HydraX-v2/confirm_listener_v207.py
# Should show: Line 183-186 protection logic
```

**Restart Confirm Listener**:

```bash
ps aux | grep confirm_listener_v207.py | grep -v grep | awk '{print $2}' | xargs kill
nohup python3 /root/HydraX-v2/confirm_listener_v207.py > /tmp/confirm_listener.log 2>&1 &
```

### Issue 4: Telegram Alerts Show 0% Confidence

**Symptoms**: All alerts display "0%" regardless of actual confidence

**Root Cause**: `athena_group_dispatcher.py` reading wrong field

**Fix Verification**:

```bash
grep -A 2 "tcs_score.*confidence" /root/HydraX-v2/athena_group_dispatcher.py
# Should show: "tcs_score = signal_data.get('tcs_score') or signal_data.get('confidence', 0)"
```

**No Restart Needed**: BittenCore loads dispatcher dynamically on each signal

### Issue 5: Fire Commands Not Reaching EA

**Symptoms**: Status stays "SENT", no ticket, no MT5 execution

**Debug Steps**:

1. **Check EA connection**:

   ```bash
   sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, last_seen, datetime(last_seen, 'unixepoch') FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"
   ```

2. **Check command_router logs**:

   ```bash
   pm2 logs command_router --lines 20
   ```

3. **Verify IPC queue**:

   ```bash
   ps aux | grep "ipc:///tmp/bitten_cmdqueue"
   ```

4. **Test DEALER processes** (kill any test processes intercepting commands):
   ```bash
   ps aux | grep -E "test.*dealer|dealer.*test"
   # Kill any found!
   ```

**Common Causes**:

- ❌ EA not connected (last_seen > 120s)
- ❌ Test DEALER process intercepting commands
- ❌ Invalid SL/TP positioning (EA pre-flight validation failure)
- ❌ Lot size not rounded (EA rejects 0.094476)

---

## 🚀 QUICK HEALTH CHECK COMMANDS

**Run these to verify complete system health**:

```bash
# 1. Check all critical processes
pm2 list | grep -E "command_router|elite_guard|confirm_listener"

# 2. Check port bindings
ss -tulpen | grep -E ":(5555|5556|5557|5558|8888)"

# 3. Verify webapp is running
ps aux | grep "python3 webapp_server_optimized.py" | grep -v grep

# 4. Check EA connection freshness
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"

# 5. Check auto-fire configuration
sqlite3 /root/HydraX-v2/data/fire_modes.db "SELECT user_id, current_mode, auto_fire_min_confidence, auto_fire_max_confidence, max_auto_slots FROM user_fire_modes WHERE user_id = '7176191872';"

# 6. Check recent signals
sqlite3 /root/HydraX-v2/bitten.db "SELECT signal_id, symbol, confidence, datetime(created_at, 'unixepoch') FROM signals ORDER BY created_at DESC LIMIT 5;"

# 7. Check recent fire executions
sqlite3 /root/HydraX-v2/bitten.db "SELECT fire_id, status, ticket, price, datetime(created_at, 'unixepoch') FROM fires ORDER BY created_at DESC LIMIT 5;"

# 8. Verify no duplicate telegram alerts
tail -50 /tmp/webapp.log | grep "Group signal dispatched"
# Should see ONE message per signal_id

# 9. Check slot usage
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) as active_positions FROM fires WHERE status IN ('FILLED', 'SENT', 'PENDING');"

# 10. Test complete fire path
python3 /root/HydraX-v2/test_webapp_fire_path.py
```

---

## 📝 CRITICAL FILES REFERENCE

| File                             | Purpose                      | Critical Lines                                                        |
| -------------------------------- | ---------------------------- | --------------------------------------------------------------------- |
| `webapp_server_optimized.py`     | Signal processing, auto-fire | 417 (POST /api/signals), 480-732 (auto-fire logic)                    |
| `src/bitten_core/bitten_core.py` | Signal processing core       | 738 (process_venom_signal), 938 (dispatch_group_signal)               |
| `athena_group_dispatcher.py`     | Telegram alerts              | 59 (dispatch_group_signal), 70 (confidence fix), 104 (message format) |
| `confirm_listener_v207.py`       | EA confirmations             | 474-476 (position_opened handler), 183-186 (downgrade protection)     |
| `execute_fire_proper.py`         | Fire execution               | 52-88 (database-first), 90-146 (IPC queue)                            |
| `enqueue_fire.py`                | Fire command creation        | 40 (lot rounding), 464-500 (OrderedDict)                              |
| `emergency_position_cleanup.py`  | Database sync                | 52-62 (FILLED cleanup)                                                |

---

## ✅ VERIFICATION CHECKLIST

**After ANY system changes**, verify:

- [ ] Elite Guard generating signals (check database: `SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s', 'now', '-1 hour')`)
- [ ] Telegram alerts working (check group -1002581996861)
- [ ] Confidence displaying correctly (not 0%)
- [ ] Only ONE telegram message per signal (no duplicates)
- [ ] Auto-fire configuration correct (80-95% range)
- [ ] EA connection fresh (< 120 seconds)
- [ ] Fire commands executing (check fires table)
- [ ] Confirmations storing tickets (status=FILLED with ticket > 0)
- [ ] No status downgrades (FILLED stays FILLED)
- [ ] Slot usage accurate (< 10 for COMMANDER)

---

## 🎯 FOR THE NEXT AGENT

**Read this FIRST** before debugging:

1. Signal confidence below 80%? **Auto-fire WON'T trigger** (working as designed)
2. Duplicate telegram alerts? **Check webapp line 476-478** (should be commented out)
3. Confirmations showing UNKNOWN? **Check confirm_listener line 183-186** (downgrade protection)
4. Confidence showing 0%? **Check athena_group_dispatcher line 70** (field lookup)
5. Slots showing full? **Run emergency_position_cleanup.py** (database sync)

**Test auto-fire**: Wait for signal with 80-95% confidence, or temporarily lower threshold:

```sql
UPDATE user_fire_modes
SET auto_fire_min_confidence = 70.0
WHERE user_id = '7176191872';
```

**Everything documented here was tested and verified October 6, 2025. Trust this document over old documentation.**
