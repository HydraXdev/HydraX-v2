# HYDRASOCKET INTEGRATION - CURRENT STATE

**Date**: October 1, 2025 03:45 UTC
**Status**: 🟡 Waiting for EA Reconnection

## ✅ WHAT'S COMPLETED

### 1. Hybrid Command Server (Port 5555)

- **File**: `/root/HydraX-v2/hybrid_command_server.py`
- **Status**: ✅ RUNNING (PID 1164571)
- **Purpose**: Accepts native TCP connections from HydraSocket EA
- **Features**:
  - TCP server on port 5555 (for EA command socket)
  - ZMQ ROUTER on port 5554 (for Brain communication)
  - IPC PULL from `/tmp/bitten_cmdqueue` (for WebApp/Fire commands)
  - Automatic forwarding: IPC → TCP → EA

### 2. Command Flow Integration

```
WebApp / Brain
    ↓ (ZMQ PUSH)
IPC Queue (ipc:///tmp/bitten_cmdqueue)
    ↓ (ZMQ PULL)
Hybrid Command Server
    ↓ (Native TCP JSONL)
EA Command Socket (185.244.67.11 connecting to 134.199.204.67:5555)
    ↓
MT5 Terminal
```

### 3. Data Flow (Already Working)

```
EA (185.244.67.11)
    ↓ Port 5559 (Events - TCP)
Universal Bridge
    ↓ ZMQ PUSH Port 5556
Telemetry Bridge
    ↓ ZMQ PUB Port 5560
Elite Guard (Waiting for market data)
```

### 4. Test Command Sent

- ✅ feed_set command sent via IPC queue
- ✅ Hybrid server received the command
- ⏳ Command queued, waiting for EA connection to send

## 🟡 WHAT'S PENDING

### EA Reconnection

**Issue**: EA's command socket needs to reconnect to port 5555
**Why**: Old command_router used incompatible ZMQ protocol
**Now**: Proper TCP server ready on port 5555
**Expected**: EA will connect on next retry attempt

**EA Configuration** (from EA code):

- `InpRouterHost = "134.199.204.67"` ✅ Matches current server
- `InpCommandPort = 5555` ✅ Matches our TCP server
- Connection method: Native TCP `SocketConnect()`
- Retry behavior: Unknown interval (possibly 1-5 minutes)

### Current EA Status

- ✅ Running and operational
- ✅ Sending events to port 5559 (Universal Bridge)
- ✅ Sending account_summary, position_heartbeat every ~1 second
- ❌ Command socket not connected to port 5555 yet

## 📊 VERIFICATION CHECKLIST

Once EA connects, we should see:

1. **Hybrid Server Logs**:

   ```
   📡 EA connected from (185.244.67.11, XXXXX)
   📤 Sent to EA: feed_set
   ```

2. **EA Response** (via Universal Bridge):
   - Bootstrap messages with historical bars
   - `bar_closed` events for M1/M5/H1
   - `custom_bar_closed` events every 15 seconds

3. **Elite Guard**:
   - Candle count increases for all 19 symbols
   - Pattern scanning activates
   - Signals generated

## 🔧 ARCHITECTURE CHANGES MADE

### Replaced Components

- ❌ **OLD**: `command_router.py` (ZMQ ROUTER on port 5555)
- ✅ **NEW**: `hybrid_command_server.py` (TCP server on port 5555)

### Why This Works

- EA uses native TCP sockets (MQL5 `SocketConnect()`)
- Cannot connect to ZMQ sockets (incompatible protocols)
- New hybrid server speaks both:
  - TCP for EA communication
  - ZMQ for Brain/IPC integration

### No EA Changes Required

- EA still connects to 134.199.204.67:5555
- EA still sends JSONL commands
- EA configuration untouched

## 🚀 NEXT STEPS (Automatic)

When EA connects to port 5555:

1. **Hybrid server automatically**:
   - Accepts connection
   - Sends queued feed_set command
   - Logs: `📡 EA connected` + `📤 Sent to EA: feed_set`

2. **EA automatically**:
   - Processes feed_set command
   - Calls BuildWatchlist() with 19 symbols
   - Calls EmitBootstrap() to send historical bars
   - Starts emitting market data every 15 seconds

3. **System automatically**:
   - Universal Bridge receives market data
   - Forwards to port 5556
   - Telemetry bridge relays to port 5560
   - Elite Guard builds candles and scans for patterns

4. **Signals automatically**:
   - Elite Guard generates signals
   - Signals flow to Redis → WebApp → Telegram
   - Users can execute trades via /fire

## 📝 MONITORING COMMANDS

```bash
# Watch for EA connection
tail -f /var/log/hybrid_command_server.log | grep "EA connected"

# Watch for market data from EA
tail -f /var/log/hydrasocket_universal_bridge.log | grep "bar_closed"

# Watch Elite Guard candle building
pm2 logs elite_guard --lines 50 | grep "have M1 data"

# Check if port 5555 has connection
ss -tn | grep :5555
```

## ⏱️ ESTIMATED TIME

**EA Reconnection**: 1-5 minutes (retry interval unknown)
**Market Data Flow**: Immediate once connected
**Pattern Scanning**: Starts within 30 seconds of receiving data

**Total**: System should be fully operational within 5-10 minutes of EA reconnection.
