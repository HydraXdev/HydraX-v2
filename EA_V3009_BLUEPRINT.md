# 🎯 BITTEN EA v3.009 - PRODUCTION BLUEPRINT

**Status**: ✅ LIVE IN PRODUCTION
**Date Deployed**: October 10, 2025
**File**: `/root/HydraX-v2/BITTEN_Streamlined_Pipe_v3.009.mq5`
**Version**: 3.009 (Streamlined Pipe - Production Hardened)

---

## 📋 TABLE OF CONTENTS

1. [Overview & Architecture](#overview--architecture)
2. [Critical Fixes in v3.009](#critical-fixes-in-v3009)
3. [ZMQ Communication Layer](#zmq-communication-layer)
4. [Fire Command Execution](#fire-command-execution)
5. [What The EA Needs From BITTEN v2.0](#what-the-ea-needs-from-bitten-v20)
6. [What BITTEN v2.0 Gets From The EA](#what-bitten-v20-gets-from-the-ea)
7. [Configuration & Deployment](#configuration--deployment)
8. [Testing & Safety Features](#testing--safety-features)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Version History](#version-history)

---

## 🏗️ OVERVIEW & ARCHITECTURE

### **Primary Purpose**
Bidirectional ZMQ bridge between MT5 terminal and BITTEN v2.0 server for:
- Receiving trade execution commands (FIRE, CLOSE, CLOSE_ALL)
- Streaming real-time market data (ticks, positions, heartbeats)
- Sending trade confirmations back to server

### **Core Design Philosophy**
1. **Production Hardened**: Zero-crash tolerance with comprehensive error handling
2. **Reentrancy Protected**: Static guards prevent overlapping command execution
3. **ZMQ-Native**: No file-based fallbacks, pure socket communication
4. **Rate Limited**: Prevents message flooding with configurable Hz limits
5. **Test Mode**: Can simulate full flow without executing real trades

### **Magic Number**
```cpp
ulong g_magic = 7176191872;  // CRITICAL: All BITTEN trades use this magic
```
**NEVER change this value** - it's used to identify BITTEN trades across system restarts.

---

## 🔧 CRITICAL FIXES IN v3.009

### **Fix #1: ZMQ_RCVMORE Buffer Corruption (Silent Crash)**
**Problem**: Using 4-byte buffer for ZMQ_RCVMORE option caused buffer corruption and silent crashes.

**Solution**:
```cpp
// CRITICAL FIX: Safe RCVMORE handling (8-byte buffer, boolean semantics)
uchar optbuf[8];
ArrayInitialize(optbuf, 0);
int optlen = 8;
if(zmq_getsockopt(sock, ZMQ_RCVMORE, optbuf, optlen) != 0) break;
int more = (int)optbuf[0];  // Treat as 0/1 boolean
if(more == 0) break;
```

### **Fix #2: Margin Constant Correction**
**Problem**: Used `ACCOUNT_MARGIN_FREE` (doesn't exist) instead of `ACCOUNT_FREEMARGIN`.

**Solution**:
```cpp
// FIX: Use ACCOUNT_FREEMARGIN (not ACCOUNT_MARGIN_FREE)
double free_mg=SafeNum(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2);
```

### **Fix #3: Ticket Handling in Netting Mode**
**Problem**: On netting accounts, order/deal/position tickets differ - EA was returning wrong ticket.

**Solution**:
```cpp
// FIX: Proper ticket handling (order/deal/position)
ulong order_ticket = g_trade.ResultOrder();
ulong deal_ticket  = g_trade.ResultDeal();

// Try to find active position ticket (netting-friendly)
ulong pos_ticket=0;
for(int i=PositionsTotal()-1; i>=0; --i){
   ulong t=PositionGetTicket(i);
   if(!PositionSelectByTicket(t)) continue;
   if(PositionGetInteger(POSITION_MAGIC)!=(long)g_magic) continue;
   if(PositionGetString(POSITION_SYMBOL)!=symbol) continue;
   pos_ticket=t;
   break;
}

ulong best_ticket = pos_ticket ? pos_ticket : (deal_ticket ? deal_ticket : order_ticket);
```

### **Fix #4: Reentrancy Guard**
**Problem**: Overlapping fire commands could cause race conditions.

**Solution**:
```cpp
void ExecuteFire(string json){
   // REENTRANCY GUARD: Prevent overlapping fire executions
   static bool s_executing=false;
   if(s_executing){
      Print("[FIRE] Busy; ignoring overlapping command");
      return;
   }
   s_executing=true;

   // ... execution code ...

   s_executing=false;  // Reset guard at all exit points
}
```

### **Fix #5: JSON Validation**
**Problem**: Malformed JSON caused silent failures or crashes.

**Solution**:
```cpp
bool ValidateFireJson(const string j){
   return HasKey(j,"fire_id") && HasKey(j,"symbol") && HasKey(j,"direction");
}

// JSON VALIDATION: Ensure required keys exist
if(!ValidateFireJson(json)){
   Print("[FIRE-ABORT] Malformed JSON: fire_id/symbol/direction required");
   SendConfirmation("fire", false, 0, 0, "Malformed JSON: fire_id/symbol/direction required", "", "");
   s_executing=false;
   return;
}
```

### **Fix #6: SL/TP Validation**
**Problem**: Orders with SL on wrong side (BUY with SL above entry) were sent to broker.

**Solution**: Complete pre-flight validation before calling `g_trade.Buy()`/`Sell()`:
- Check SL/TP are on correct side of entry price
- Check minimum distance from stops_level
- Check margin availability
- Check symbol trading is enabled

### **Fix #7: Clean Deinit with Linger**
**Problem**: Messages lost on EA shutdown.

**Solution**:
```cpp
void OnDeinit(const int reason){
   EventKillTimer();
   SendDisconnect();

   // Set linger for graceful shutdown
   if(InpEnableZmq && InpLingerOnExitMs > 0){
      // Set 250ms linger on all sockets
      Sleep(200);  // Allow messages to flush
   }

   // Close sockets and context
}
```

---

## 📡 ZMQ COMMUNICATION LAYER

### **Socket Architecture**

| Socket | Type | Port | Direction | Purpose |
|--------|------|------|-----------|---------|
| `g_tick_pub` | PUSH | 5556 | EA→Server | Market data + heartbeats + handshake |
| `g_cmd_dealer` | DEALER | 5555 | EA↔Server | Bidirectional commands (FIRE, CLOSE, PING) |
| `g_confirm_pub` | PUSH | 5558 | EA→Server | Trade confirmations + position events |
| `g_metrics_pub` | PUSH | 5560 | EA→Server | Position updates (rate-limited to 2Hz) |

### **ZMQ Configuration**
```cpp
input string InpBridgeHost    = "134.199.204.67";  // BITTEN v2.0 server
input int    InpTickPort      = 5556;
input int    InpCmdPort       = 5555;
input int    InpConfirmPort   = 5558;
input int    InpMetricsPort   = 5560;
input int    InpSndHWM        = 10000;  // Send high water mark
input int    InpRcvHWM        = 1000;   // Receive high water mark
input int    InpLingerMs      = 0;      // Normal operation linger
input int    InpLingerOnExitMs = 250;   // Shutdown linger
```

### **Message Flow Patterns**

#### **1. Handshake (On EA Startup)**
```json
{
  "type": "handshake",
  "node_id": "NODE_843859_1728555123",
  "uuid": "COMMANDER_DEV_001",
  "account": 843859,
  "broker": "XM Global Limited",
  "server": "XMGlobal-MT5 3",
  "currency": "USD",
  "balance": 10507.92,
  "equity": 10507.68,
  "symbols": 200,
  "version": "3.009",
  "reconnect": true,
  "test_mode": false,
  "open_positions": [
    {
      "ticket": 12345,
      "symbol": "EURUSD",
      "direction": "BUY",
      "fire_id": "ELITE_RAPID_EURUSD_123",
      "open_price": "1.08500",
      "volume": "0.10",
      "pnl": 5.25
    }
  ],
  "timestamp": 1728555123
}
```

**Critical Fields**:
- `reconnect`: `true` if EA has open positions (prevents resetting daily trade counter)
- `open_positions`: Array of currently open BITTEN trades (for position reconciliation)
- `test_mode`: `true` if `InpTestModeNoTrades=true`

#### **2. Heartbeat (Every 1 Second)**
```json
{
  "type": "heartbeat",
  "node_id": "NODE_843859_1728555123",
  "uuid": "COMMANDER_DEV_001",
  "balance": 10507.92,
  "equity": 10507.68,
  "margin": 50.00,
  "free_margin": 10457.68,
  "positions": 1,
  "ticks": 15234,
  "timestamp": 1728555125
}
```

**Purpose**: Keeps EA connection "fresh" for auto-fire eligibility (server checks `last_seen < 120 seconds`).

#### **3. DEALER Keepalive (Every 5 Seconds)**
```json
{
  "type": "dealer_heartbeat",
  "uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_1728555123",
  "timestamp": 1728555130
}
```

**Purpose**: Prevents ZMQ DEALER socket timeout on command_router.

#### **4. Tick Streaming (Continuous)**
```json
{
  "type": "tick",
  "uuid": "COMMANDER_DEV_001",
  "symbol": "EURUSD",
  "bid": "1.08500",
  "ask": "1.08502",
  "volume": 1,
  "timestamp": 1728555125
}
```

**Rate Control**: `InpTickScanSleepMs` (default 0) between symbols.

#### **5. Position Update (Max 2Hz)**
```json
{
  "type": "position_update",
  "uuid": "COMMANDER_DEV_001",
  "ticket": 12345,
  "fire_id": "ELITE_RAPID_EURUSD_123",
  "symbol": "EURUSD",
  "open_price": "1.08500",
  "current_price": "1.08525",
  "volume": "0.10",
  "pnl": 5.25,
  "timestamp": 1728555125
}
```

**Deduplication**: Only sends if price/PnL changed (controlled by `InpDedupPositions=true`).

---

## 🔥 FIRE COMMAND EXECUTION

### **Incoming Fire Command Format**
```json
{
  "type": "fire",
  "fire_id": "ELITE_RAPID_EURUSD_1760094186",
  "target_uuid": "COMMANDER_DEV_001",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry": 0,
  "sl": 1.08000,
  "tp": 1.09000,
  "lot": 0.42
}
```

**Field Specifications**:
- `type`: Must be exactly `"fire"`
- `fire_id`: Unique identifier (used as position comment in MT5)
- `target_uuid`: Must match EA's UUID (filters commands)
- `symbol`: MT5 symbol name (must be available)
- `direction`: "BUY" | "SELL" | "LONG" | "SHORT" | "B" | "S" | "L" (canonicalized to BUY/SELL)
- `entry`: 0 for market orders (EA uses current bid/ask)
- `sl`: Stop loss price (0 = no SL)
- `tp`: Take profit price (0 = no TP)
- `lot`: Position size (will be normalized to symbol's step/min/max)

### **Execution Flow (19 Steps)**

```cpp
void ExecuteFire(string json){
   // STEP 1-5: Parse and validate JSON
   // STEP 6: Select symbol and verify trading enabled
   // STEP 7: Get bid/ask quotes
   // STEP 8-9: Determine direction and normalize lot size
   // STEP 10: Log all parameters

   // TEST MODE BRANCH
   if(InpTestModeNoTrades){
      SendConfirmation("fire", true, 999999, price, "TEST MODE - NO TRADE EXECUTED", fire_id, symbol);
      return;
   }

   // STEP 11: Pre-flight checks
   //   11a: Margin availability (OrderCalcMargin + free_margin check)
   //   11b: SL/TP position validation (correct side + stops_level distance)
   //   11c: Configure CTrade object

   // STEP 12: Log all checks passed
   // STEP 13-14: Execute g_trade.Buy() or g_trade.Sell()
   // STEP 15-19: Handle result
   //   SUCCESS: Send confirmation + position_opened
   //   FAILURE: Send confirmation with error retcode
}
```

### **Success Response**
```json
{
  "type": "confirmation",
  "cmd_type": "fire",
  "fire_id": "ELITE_RAPID_EURUSD_1760094186",
  "uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_1728555123",
  "status": "success",
  "ticket": 12345,
  "price": "1.08502",
  "message": "Executed",
  "balance": 10507.92,
  "equity": 10507.68,
  "timestamp": 1728555125
}

{
  "type": "position_opened",
  "uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_EURUSD_1760094186",
  "ticket": 12345,
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry_price": "1.08502",
  "volume": "0.42",
  "balance": 10507.92,
  "equity": 10507.68,
  "open_positions": 1,
  "timestamp": 1728555125
}
```

### **Failure Response**
```json
{
  "type": "confirmation",
  "cmd_type": "fire",
  "fire_id": "ELITE_RAPID_EURUSD_1760094186",
  "uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_1728555123",
  "status": "failed",
  "ticket": 0,
  "price": "0.00000",
  "message": "Failed: retcode=10015 (Insufficient margin)",
  "balance": 10507.92,
  "equity": 10507.68,
  "timestamp": 1728555125
}
```

### **Position Closed Event (Automatic)**
```json
{
  "type": "position_closed",
  "uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_EURUSD_1760094186",
  "ticket": 12345,
  "symbol": "EURUSD",
  "close_price": "1.09000",
  "profit": 42.00,
  "reason": "TP",
  "balance": 10549.92,
  "equity": 10549.92,
  "timestamp": 1728555200
}
```

**Close Reasons**:
- `"TP"`: Take profit hit
- `"SL"`: Stop loss hit
- `"MANUAL"`: User closed manually
- `"STOPOUT"`: Margin call

---

## 📥 WHAT THE EA NEEDS FROM BITTEN v2.0

### **1. UUID Configuration File**
**File**: `<MT5_DATA_FOLDER>/MQL5/Files/bitten_deployment.cfg`

```
UUID=COMMANDER_DEV_001
```

**Hardcoded Exception**: Account 843859 automatically gets UUID `COMMANDER_DEV_001`.

**How EA Loads It**:
```cpp
bool LoadConfig(){
   if(AccountInfoInteger(ACCOUNT_LOGIN)==843859){
      g_user_uuid="COMMANDER_DEV_001";
      return true;
   }

   int fh=FileOpen("bitten_deployment.cfg", FILE_READ|FILE_TXT);
   // ... parse UUID= line ...
}
```

### **2. ZMQ Server Endpoints**
**Server**: `134.199.204.67` (hardcoded, can be changed via `InpBridgeHost`)

**Required Services**:
- `tcp://134.199.204.67:5556` - **PULL socket** for ticks/heartbeats/handshake
- `tcp://134.199.204.67:5555` - **ROUTER socket** for fire commands (EA connects as DEALER)
- `tcp://134.199.204.67:5558` - **PULL socket** for confirmations/position events
- `tcp://134.199.204.67:5560` - **PULL socket** for position updates

**Critical**: Server must BIND these ports, EA will CONNECT to them.

### **3. Fire Command Format (EXACT)**
**Order of fields matters** - EA parser expects fields in this order:

```json
{
  "type": "fire",
  "fire_id": "...",
  "target_uuid": "...",
  "symbol": "...",
  "direction": "...",
  "entry": 0,
  "sl": 0.0,
  "tp": 0.0,
  "lot": 0.01
}
```

**Common Mistakes**:
- ❌ Using `"target"` instead of `"target_uuid"`
- ❌ Using lowercase direction `"buy"` instead of `"BUY"`
- ❌ Sending `entry` as string `"0"` instead of number `0`
- ❌ Including extra fields like `user_id`, `mission_id`

### **4. Command Router Identity Mapping**
**Server Must**:
1. Store mapping: `UUID → ZMQ DEALER identity bytes`
2. Use this mapping to route fire commands to correct EA
3. Example (Python):
```python
identity_map = {}  # uuid -> raw identity bytes

# When EA sends hello:
identity, msg = router.recv_multipart()
data = json.loads(msg)
uuid = data['uuid']
identity_map[uuid] = identity

# When firing command:
target_uuid = fire_cmd['target_uuid']
identity = identity_map.get(target_uuid)
router.send_multipart([identity, b"", json.dumps(fire_cmd).encode()])
```

### **5. Position Reconciliation on Reconnect**
**When `reconnect=true` in handshake**:
- Server MUST NOT reset daily trade counter
- Server MUST sync `open_positions` array with database
- EA state is source of truth (not stale fires table)

### **6. Heartbeat Freshness Check**
**For auto-fire eligibility**:
```python
# Server should check:
if (current_time - ea_instances.last_seen) <= 120:
    # EA is fresh, allow auto-fire
else:
    # EA is stale, skip auto-fire
```

---

## 📤 WHAT BITTEN v2.0 GETS FROM THE EA

### **1. Real-Time Market Data**
- **Tick stream**: Bid/ask for all symbols (200 max)
- **Frequency**: Every `OnTimer()` call (1 second)
- **Volume**: ~200 messages/second during active markets
- **Purpose**: Elite Guard pattern detection

### **2. Account State**
- **Heartbeat every 1 second**: Balance, equity, margin, free margin
- **Purpose**: Calculate real-time lot sizes for auto-fire

### **3. Trade Execution Confirmations**
- **position_opened**: Immediate feedback when trade executes
- **confirmation**: Success/failure with ticket/price/error details
- **Purpose**: Update `fires` table with ticket/price/status

### **4. Position Lifecycle Events**
- **position_update**: Current price and PnL (max 2Hz per position)
- **position_closed**: Final PnL and close reason (TP/SL/MANUAL/STOPOUT)
- **Purpose**: Real-time tracking, signal outcome monitoring

### **5. Connection Status**
- **handshake**: EA startup with open positions reconciliation
- **disconnect**: EA shutdown notification
- **dealer_heartbeat**: DEALER socket keepalive (every 5 seconds)
- **Purpose**: Know when EA is online/offline

### **6. Node Identification**
```json
{
  "node_id": "NODE_843859_1728555123",  // Unique per EA session
  "uuid": "COMMANDER_DEV_001"           // Persistent user identifier
}
```

**Why Both**:
- `node_id`: Temporary session ID (changes on EA restart)
- `uuid`: Permanent user ID (maps to user_id 7176191872)

---

## ⚙️ CONFIGURATION & DEPLOYMENT

### **Input Parameters**

#### **Trading Behavior**
```cpp
input bool InpTestModeNoTrades = false;  // ✅ SET TRUE FOR TESTING
```
**When `true`**: EA parses fire commands and logs all steps, but **does NOT execute** `g_trade.Buy()`/`Sell()`. Returns fake confirmation with ticket 999999.

**Use Case**: Test entire fire pipeline without risking real money.

```cpp
input bool InpEnableZmq = true;  // ✅ ALWAYS TRUE IN PRODUCTION
```
**When `false`**: Disables entire ZMQ layer (for local testing without DLLs).

#### **Performance Tuning**
```cpp
input int InpMaxSymbols = 200;        // Max symbols to monitor
input int InpTickScanSleepMs = 0;     // Delay between symbol scans
input int InpEmitHzPositions = 2;     // Max position updates per second
input bool InpDedupPositions = true;  // Only send when price/PnL changed
```

**Recommended Settings**:
- **High-frequency**: `InpMaxSymbols=200, InpTickScanSleepMs=0, InpEmitHzPositions=2`
- **Low-bandwidth**: `InpMaxSymbols=50, InpTickScanSleepMs=10, InpEmitHzPositions=1`

#### **Network Tuning**
```cpp
input int InpSndHWM = 10000;     // Send buffer size
input int InpRcvHWM = 1000;      // Receive buffer size
input int InpLingerMs = 0;       // Normal operation linger
input int InpLingerOnExitMs = 250;  // Shutdown linger
```

**High Water Marks**:
- `InpSndHWM=10000`: Allows ~10,000 queued outbound messages before dropping
- `InpRcvHWM=1000`: Allows ~1,000 queued inbound messages before blocking

#### **Logging**
```cpp
input bool InpVerboseLogging = false;  // ✅ SET TRUE FOR DEBUGGING
```

**When `true`**: Logs every socket operation, heartbeat, command received, etc.

**Performance Impact**: Adds ~5-10% CPU overhead (acceptable for debugging).

### **Deployment Steps**

#### **1. Compile EA**
```bash
# On Windows with MT5 installed:
cd C:\Users\<username>\AppData\Roaming\MetaQuotes\Terminal\<instance>\MQL5\Experts
# Copy BITTEN_Streamlined_Pipe_v3.009.mq5 here
# Open MetaEditor and compile (F7)
```

#### **2. Create Config File**
```bash
# Create file at:
# C:\Users\<username>\AppData\Roaming\MetaQuotes\Terminal\<instance>\MQL5\Files\bitten_deployment.cfg
UUID=COMMANDER_DEV_001
```

#### **3. Attach to Chart**
- Open MT5, any chart (symbol doesn't matter - EA monitors all)
- Drag EA to chart
- **CRITICAL**: Set `InpTestModeNoTrades=false` for live trading
- Click OK

#### **4. Verify Connection**
```bash
# On server (134.199.204.67):
pm2 logs command_router --lines 10
# Should see: "DEALER hello from COMMANDER_DEV_001"

pm2 logs zmq_gateway --lines 10
# Should see: "handshake from COMMANDER_DEV_001"
```

#### **5. Test Fire Command**
```bash
# On server:
python3 test_fire_command.py --uuid COMMANDER_DEV_001 --symbol EURUSD --direction BUY --lot 0.01
```

---

## 🧪 TESTING & SAFETY FEATURES

### **Test Mode (Recommended for First Deployment)**

```cpp
input bool InpTestModeNoTrades = true;  // SAFE MODE
```

**What Happens**:
1. EA connects to server ✅
2. Receives fire commands ✅
3. Parses all fields ✅
4. Validates parameters ✅
5. Logs would-be execution ✅
6. **SKIPS** `g_trade.Buy()`/`Sell()` ⚠️
7. Sends fake confirmation (ticket=999999) ✅

**Use Case**: Test that fire pipeline works end-to-end without risking money.

**Expected Output in EA Logs**:
```
[FIRE-TEST] TEST MODE ENABLED - SKIPPING TRADE EXECUTION
[FIRE-TEST] Would execute: BUY 0.42 EURUSD
[FIRE-TEST] Sending fake success confirmation...
[FIRE-TEST] Fake confirmation sent
[FIRE-TEST] ========== TEST COMPLETE ==========
```

### **Reentrancy Protection**

```cpp
static bool s_executing=false;
if(s_executing){
   Print("[FIRE] Busy; ignoring overlapping command");
   return;
}
s_executing=true;
```

**Prevents**:
- Race conditions from simultaneous fire commands
- Buffer overflows from rapid-fire execution
- Double-execution of same command

**Limitation**: Only handles single-threaded overlaps (MQL5 is single-threaded, so this is sufficient).

### **Pre-Flight Validation**

**11-Point Checklist Before Execution**:
1. ✅ JSON has required fields (fire_id, symbol, direction)
2. ✅ Symbol is available and trading enabled
3. ✅ Bid/ask quotes exist
4. ✅ Direction parsed and canonicalized
5. ✅ Lot size normalized to symbol specs
6. ✅ Margin available (OrderCalcMargin check)
7. ✅ SL on correct side (BUY: SL < entry, SELL: SL > entry)
8. ✅ TP on correct side (BUY: TP > entry, SELL: TP < entry)
9. ✅ SL distance >= stops_level
10. ✅ TP distance >= stops_level
11. ✅ CTrade object configured correctly

**If ANY check fails**: Aborts and sends failure confirmation.

### **Graceful Degradation**

**If ZMQ connection lost**:
- EA continues monitoring positions
- Positions can still be closed manually in MT5
- Reconnect by restarting EA (handshake with `reconnect=true`)

**If server restarts**:
- EA sends handshake again
- Position reconciliation via `open_positions` array
- No trade data lost

---

## 🔍 TROUBLESHOOTING GUIDE

### **Issue: EA Not Connecting**

**Symptoms**:
- Chart shows "DLL NOT ALLOWED" or "MQL DLLs NOT ALLOWED"

**Solution**:
```
Tools → Options → Expert Advisors
✅ Allow DLL imports
✅ Allow WebRequest for listed URLs
```

**Symptoms**:
- Chart shows "CONFIG ERROR"

**Solution**:
- Check `bitten_deployment.cfg` exists in `MQL5/Files/` folder
- Verify UUID format (minimum 10 characters)

**Symptoms**:
- Chart shows "BITTEN v3.009 PIPE [LIVE]" but no handshake on server

**Solution**:
```bash
# Check server ports are listening:
ss -tulpen | grep -E ":(5555|5556|5558|5560)"

# Restart ZMQ services:
pm2 restart command_router zmq_gateway
```

### **Issue: Fire Commands Not Executing**

**Symptoms**:
- Server sends fire command but EA logs show nothing

**Debug Steps**:
1. Enable verbose logging: `InpVerboseLogging=true`
2. Check EA logs for `[Cmd] Type: fire`
3. If missing, check `target_uuid` matches EA's UUID exactly

**Symptoms**:
- EA logs show `[FIRE-ABORT] Malformed JSON`

**Debug**:
```bash
# Check fire command format:
pm2 logs command_router | grep "fire"
# Verify field names match exactly (case-sensitive)
```

**Symptoms**:
- EA logs show `[FIRE-ABORT] Invalid SL: must be below entry for BUY`

**Fix**:
```python
# In enqueue_fire.py or signals.py:
# Ensure SL calculation uses correct direction:
if direction == "BUY":
    sl = entry - (stop_pips * pip_size)  # SL below entry
    tp = entry + (target_pips * pip_size)
else:  # SELL
    sl = entry + (stop_pips * pip_size)  # SL above entry
    tp = entry - (target_pips * pip_size)
```

### **Issue: Confirmations Not Received**

**Symptoms**:
- Fire executes in MT5 but `fires` table shows `status=SENT`

**Debug**:
```bash
# Check confirm_listener is running:
pm2 list | grep confirm_listener

# Check port 5558:
ss -tulpen | grep 5558

# Check EA is sending:
# In MT5 Expert logs, look for:
# "[FIRE-17] Sending confirmation..."
# "[FIRE-18] Sending position_opened..."
```

**Solution**:
```bash
pm2 restart confirm_listener
```

### **Issue: Lot Size Stuck at 0.01**

**Symptoms**:
- All auto-fire trades execute with minimum lot size

**Root Cause**: Signals have `stop_pips` but missing `sl`/`tp` prices (see LOT_SIZE_FIX_DOCUMENTATION.md)

**Status**: ✅ **FIXED** October 10, 2025 (see earlier in this conversation)

---

## 📜 VERSION HISTORY

### **v3.009 (October 10, 2025) - CURRENT PRODUCTION**
✅ Fixed ZMQ_RCVMORE buffer corruption (8-byte buffer)
✅ Fixed margin constant (ACCOUNT_FREEMARGIN)
✅ Fixed ticket handling in netting mode
✅ Added reentrancy guard for fire execution
✅ Added comprehensive JSON validation
✅ Added SL/TP position validation
✅ Added clean deinit with linger
✅ Added test mode (InpTestModeNoTrades)
✅ Verbose logging throughout fire execution

**Breaking Changes**: None (backward compatible with v3.005)

### **v3.005 (October 2, 2025) - DEPRECATED**
- Added handshake position reconciliation
- Added DEALER keepalive messages
- Direction canonicalization (BUY/SELL only)
- SafeNum protection (NaN/Inf handling)
- Heartbeats moved to port 5556

**Why Deprecated**: Silent crashes from ZMQ_RCVMORE bug

### **v2.07 (September 22, 2025) - DEPRECATED**
- BITMODE hybrid position management
- Original ROUTER⇄DEALER implementation
- 6-10 pip scalping configuration

**Why Deprecated**: Missing production hardening

---

## 🚨 CRITICAL REMINDERS FOR FUTURE AGENTS

1. **NEVER change `g_magic = 7176191872`** - breaks position tracking
2. **NEVER remove reentrancy guard** - causes race conditions
3. **ALWAYS validate JSON before parsing** - prevents silent crashes
4. **ALWAYS use 8-byte buffer for ZMQ_RCVMORE** - 4-byte causes corruption
5. **ALWAYS set `InpTestModeNoTrades=true` for first deployment** - safe testing
6. **ALWAYS check SL/TP are on correct side** - broker rejects invalid orders
7. **ALWAYS use `ACCOUNT_FREEMARGIN`** - `ACCOUNT_MARGIN_FREE` doesn't exist
8. **ALWAYS handle netting mode tickets** - order ≠ deal ≠ position ticket

---

## 📋 INTEGRATION CHECKLIST

**Before deploying new EA version**:
- [ ] Compile successfully in MetaEditor
- [ ] Test with `InpTestModeNoTrades=true`
- [ ] Verify handshake arrives on server
- [ ] Send test fire command (0.01 lots)
- [ ] Verify confirmation received
- [ ] Check position_opened message
- [ ] Manually close position
- [ ] Verify position_closed message
- [ ] Switch to `InpTestModeNoTrades=false`
- [ ] Monitor first 3 live trades closely

---

**Document Version**: 1.0
**Last Updated**: October 10, 2025
**Maintained By**: BITTEN Systems
**Contact**: Use Claude Code for updates
