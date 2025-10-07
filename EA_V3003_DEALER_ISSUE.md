# 🔴 EA v3.003 DEALER SOCKET CONNECTION ISSUE

**Timestamp**: October 2, 2025 05:19 UTC
**EA Version**: 3.003 CONFIRMED
**Issue**: DEALER socket not registering with command router

## 🔍 CURRENT STATUS

### ✅ WHAT'S WORKING

1. **Handshake Received**: Successfully captured initial connection
   - Account: 843859
   - Balance: $7,765.21
   - UUID: COMMANDER_DEV_001

2. **Tick Streaming**: 26 symbols actively streaming on port 5560
   - ~26 ticks per second
   - Elite Guard building candles successfully

3. **Command Router**: Ready and accepting commands
   - Fire commands queued successfully
   - IPC bridge operational

### ❌ WHAT'S NOT WORKING

1. **DEALER Socket Not Connected**
   - EA shows "SUCCESS" for connection but hasn't sent identity
   - Router only knows "TEST_CLIENT_001" (old test client)
   - Commands queued but cannot be delivered

2. **No Heartbeats**
   - Should send every second via OnTimer()
   - Ticks flowing but heartbeats missing
   - Suggests timer may not be firing

3. **Fire Commands Blocked**
   - Commands accepted: TEST_FIRE_1759382306
   - Status: Queued indefinitely
   - Cannot route to unknown identity

## 📊 EVIDENCE

### Command Router Logs

```
[IPC_IN] fire TEST_FIRE_1759382306 target_uuid='COMMANDER_DEV_001'
[IPC_BRIDGE] ACCEPTED fire TEST_FIRE_1759382306 → queue
```

But no:

- `[ROUTER] learned COMMANDER_DEV_001`
- `[EA] fire COMMANDER_DEV_001`

### Missing DEALER Registration

The EA hasn't sent its first message on the DEALER socket, so the router doesn't know its identity.

## 🎯 ROOT CAUSE

**ZMQ DEALER sockets are lazy-connect**: They don't register their identity until they send their first message.

The EA has:

1. Connected DEALER socket to port 5555 ✅
2. NOT sent any message yet ❌
3. Therefore router doesn't know COMMANDER_DEV_001 exists ❌

## 💡 SOLUTIONS

### Option 1: EA Code Fix (Recommended)

The EA needs to send an initial message after connecting the DEALER socket:

```mql5
// After successful DEALER connection
string init_msg = "{\"type\":\"hello\",\"uuid\":\"COMMANDER_DEV_001\"}";
ZmqSend(dealer_socket, init_msg);
```

### Option 2: Force Registration

The EA should respond to ping commands, but it's not receiving them because the router can't route to an unknown identity (chicken-egg problem).

### Option 3: Check EA Configuration

Verify in MT5 Experts tab:

1. All 4 sockets connected successfully
2. No errors on DEALER socket connection
3. Identity string is exactly "COMMANDER_DEV_001"

## 📋 VERIFICATION COMMANDS

```bash
# Check queued commands
pm2 logs command_router --lines 20 | grep "queue"

# Monitor for EA registration
pm2 logs command_router --lines 100 | grep "learned"

# Check for any EA responses
pm2 logs confirm_listener_v207 --lines 20
```

## 🚨 IMPACT

Without DEALER registration:

- ❌ No fire command execution
- ❌ No live trading possible
- ❌ Commands pile up in queue
- ✅ Market data and analysis still work

## 📌 NEXT STEPS

1. **Check MT5 Experts tab** for DEALER socket errors
2. **Verify EA identity string** is exactly "COMMANDER_DEV_001"
3. **Consider EA recompilation** with initial hello message
4. **Test with different EA** if available

---

**STATUS: Awaiting DEALER socket registration for trading capability**
