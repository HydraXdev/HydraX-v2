# EA STATUS - SINGLE SOURCE OF TRUTH

**Date**: October 3, 2025
**Problem Solved**: Systems were checking stale database instead of real-time heartbeats

## 🎯 THE TRUTH SOURCE

**PRIMARY**: Port 5556 telemetry bridge receives EA heartbeats EVERY SECOND

- EA sends heartbeat with balance, equity, open positions
- Telemetry bridge republishes to port 5560 (ZMQ)
- Telemetry bridge publishes to event bus: `ea.status.heartbeat`
- Telemetry bridge updates database with SERVER RECEIVE TIME (not EA time)

## ✅ HOW TO CHECK EA STATUS (CORRECT WAY)

### Option 1: Event Bus (REAL-TIME - BEST)

```python
from event_bus.consumer import EventConsumer

consumer = EventConsumer()
consumer.subscribe('ea.status.heartbeat', lambda data: print(f"EA: {data['open_positions']} positions"))
consumer.start()
```

### Option 2: Database (ACCEPTABLE - 1 second lag)

```python
cursor.execute("""
    SELECT target_uuid, last_balance, last_equity, open_positions,
           (strftime('%s','now') - last_seen) as age_sec
    FROM ea_instances
    WHERE target_uuid = ?
""", (ea_uuid,))

result = cursor.fetchone()
is_connected = result[4] < 5  # Connected if heartbeat within 5 seconds
```

### Option 3: Direct Telemetry Logs (DEBUG ONLY)

```bash
tail -f /root/.pm2/logs/zmq-telemetry-bridge-error.log | grep "Heartbeat"
```

## ❌ WRONG WAYS (CAUSES FALSE NEGATIVES)

```python
# ❌ WRONG: Assuming EA disconnected based on old timestamp
# Problem: EA might send future timestamps (timezone issues)
age = now - ea_timestamp  # Can be negative!

# ❌ WRONG: Using HTTP polling to check status
# Problem: Database may be 1-5 seconds behind

# ❌ WRONG: Checking only on fire command
# Problem: Need real-time status for AUTO fire decisions
```

## 🔧 BUG THAT WAS FIXED

**Before Fix**:

```python
# zmq_telemetry_bridge_debug.py line 34:
timestamp = heartbeat_data.get('timestamp', int(time.time()))
# EA sent timestamp from future → database age calculation broken
```

**After Fix**:

```python
# zmq_telemetry_bridge_debug.py line 35:
timestamp = int(time.time())  # SERVER RECEIVE TIME = TRUTH
```

**Impact**: Database `last_seen` is now accurate, age calculation works correctly

## 📊 REAL-TIME SLOT TRACKING

**Enhanced Slot Manager** subscribes to:

- `ea.status.heartbeat` → Updates position counts from EA
- `trade.closed` → Releases slots immediately

**Webapp AUTO Fire** checks:

```python
# Before sending fire command:
ea_age = get_ea_age(target_uuid)
if ea_age > 120:  # 2 minutes stale
    logger.warning("EA not fresh, skipping AUTO fire")
    return
```

## 🎯 STREAMLINED DATA FLOW

```
EA (MT5)
   │ Heartbeat every 1s
   ▼
Port 5556 (PULL) ← Telemetry Bridge
   │
   ├─► Port 5560 (PUB) → Elite Guard (market data)
   ├─► Event Bus: ea.status.heartbeat → Slot Manager, Monitoring
   └─► Database: ea_instances (last_seen = SERVER TIME)
         │
         └─► Webapp checks age < 120s for AUTO fire eligibility
```

## 📋 QUICK STATUS CHECK

```bash
# Check database age (should be <5 seconds)
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) as age FROM ea_instances;"

# Check event bus (should see events flowing)
pm2 logs zmq_telemetry_bridge --lines 5 | grep "ea.status"

# Check slot manager (should track real-time positions)
pm2 logs enhanced_slot_manager --lines 5
```
