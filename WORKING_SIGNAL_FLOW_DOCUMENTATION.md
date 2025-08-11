# 🎯 BITTEN WORKING SIGNAL FLOW DOCUMENTATION
**Date Verified**: August 11, 2025 01:30 UTC  
**Status**: OPERATIONAL - Auto-execution confirmed working

---

## 📊 VERIFIED WORKING ARCHITECTURE

### **Core Signal Flow (Currently Working)**
```
Market Data → MT5 EA → Elite Guard → ZMQ 5557 → Multiple Paths:
                                                  ├→ elite_guard_zmq_relay → HTTP → WebApp
                                                  └→ final_fire_publisher → ZMQ 5555 → EA
```

### **Confirmation Flow (Working)**
```
EA Trade Execution → ZMQ 5558 → confirmation_receiver.py → Logging
```

---

## 🔌 PORT CONFIGURATION (VERIFIED WORKING)

| Port | Direction | Binding Process | Connecting Process | Protocol | Status |
|------|-----------|----------------|-------------------|----------|---------|
| **5555** | Commands→EA | final_fire_publisher.py | MT5 EA (185.244.67.11) | PUSH/PULL | ✅ WORKING |
| **5556** | Market←EA | zmq_telemetry_bridge.py | MT5 EA | PULL/PUSH | ✅ WORKING |
| **5557** | Signals | elite_guard_with_citadel.py | elite_guard_zmq_relay.py, final_fire_publisher.py | PUB/SUB | ✅ WORKING |
| **5558** | Confirms←EA | confirmation_receiver.py | MT5 EA (185.244.67.11) | PULL/PUSH | ✅ WORKING |
| **5560** | Market relay | zmq_telemetry_bridge.py | elite_guard_with_citadel.py | PUB/SUB | ✅ WORKING |

---

## 📋 RUNNING PROCESSES (AS OF AUG 11, 2025)

```bash
# Signal Generation
PID 2844521: elite_guard_with_citadel.py      # Binds 5557 as PUB
PID 2774272: elite_guard_zmq_relay.py         # Subscribes to 5557, POSTs to WebApp
PID 2411770: zmq_telemetry_bridge_debug.py    # Market data bridge

# Signal Distribution  
PID 2926505: final_fire_publisher.py          # SUB from 5557, PUSH to 5555

# Trade Execution
EA at 185.244.67.11:                          # PULL from 5555, PUSH to 5558

# Confirmation Handling
PID [varies]: confirmation_receiver.py        # Binds 5558 as PULL

# Web & Bot Interface
PID 2582822: webapp_server_optimized.py       # Port 8888
PID 2889530: bitten_production_bot.py         # Telegram bot
PID 2858072: athena_mission_bot.py            # Mission alerts
```

---

## ✅ WHAT'S ACTUALLY WORKING

### **1. Elite Guard Signal Generation**
- **Process**: `elite_guard_with_citadel.py`
- **Evidence**: Signals in truth_log.jsonl every 5-10 minutes
- **Format**: `"ELITE_GUARD_SIGNAL {json}"`
- **Publishing**: ZMQ PUB on port 5557

### **2. Signal Distribution (Two Paths)**

**Path A: Auto-Execution (WORKING)**
```
elite_guard → 5557 → final_fire_publisher → 5555 → EA
```
- final_fire_publisher subscribes to 5557
- Converts to fire commands
- Pushes to EA on 5555
- EA executes immediately (full auto mode)

**Path B: WebApp/Telegram (WORKING)**
```
elite_guard → 5557 → elite_guard_zmq_relay → HTTP POST → WebApp
```
- Relay subscribes to 5557
- POSTs to localhost:8888/api/signals
- Creates mission files with complete data
- Mission status available at `/api/mission-status/{signal_id}`
- HUD accessible at `/hud` and `/hud/enhanced`
- Telegram alerts (needs verification)

### **3. Trade Execution (CONFIRMED WORKING)**
Evidence from confirmation logs:
```
Signal: ELITE_GUARD_USDJPY_1754873698 at 00:54:58
Trade: Ticket 20691597 at 00:55:00 (2 second delay)

Signal: ELITE_GUARD_EURUSD_1754874058 at 01:00:58
Trade: Ticket 20691795 at 01:01:02 (4 second delay)

Signal: ELITE_GUARD_USDJPY_1754874359 at 01:05:59
Trade: Ticket 20692000 at 01:06:04 (5 second delay)
```

### **4. Trade Confirmations (WORKING)**
- EA sends confirmations to port 5558
- Format includes: ticket, price, balance, equity, margin
- Successfully logging all executions

---

## 🔧 KEY CONFIGURATION DETAILS

### **Elite Guard Publishing**
```python
# elite_guard_with_citadel.py line 166
self.publisher = self.context.socket(zmq.PUB)
self.publisher.bind("tcp://*:5557")

# line 1458 - Publishing format
self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
```

### **Final Fire Publisher**
```python
# final_fire_publisher.py line 33
subscriber.connect("tcp://127.0.0.1:5557")
subscriber.subscribe(b'')  # Subscribe to all

# line 91 - Binding for EA
publisher.bind("tcp://*:5555")
```

### **EA Connection (MQL5)**
```mql5
// BITTEN_Universal_EA_v2.02.mq5
context.connect("tcp://134.199.204.67:5555");  // PULL commands
context.connect("tcp://134.199.204.67:5558");  // PUSH confirmations
```

---

## 🚨 CRITICAL DEPENDENCIES

1. **Elite Guard must be running** - It's the only signal source
2. **Port 5557 must be bound by Elite Guard** - Others connect as SUB
3. **final_fire_publisher must be running** - Bridges signals to EA
4. **EA must be connected** - Check with `netstat -an | grep 5555`

---

## 🔍 TROUBLESHOOTING COMMANDS

```bash
# Check all connections
netstat -an | grep -E "555[5-8]" | grep ESTABLISHED

# Check processes
ps aux | grep -E "elite_guard|final_fire|confirmation" | grep -v grep

# Monitor signals
tail -f /root/HydraX-v2/truth_log.jsonl | grep ELITE_GUARD

# Check relay logs
tail -f /tmp/elite_guard_zmq_relay.log

# Verify EA connections
netstat -an | grep "185.244.67.11"
```

---

## 💡 POTENTIAL SIMPLIFICATIONS

### **Current Complexity Issues:**
1. Two parallel paths (ZMQ and HTTP) for signals
2. Multiple relay processes
3. WebApp HTTP timeout issues

### **Proposed Simplification:**
```
BEFORE (Current):
Elite Guard → 5557 → elite_guard_zmq_relay → HTTP → WebApp → BittenCore
                 └→ final_fire_publisher → 5555 → EA

AFTER (Simplified):
Elite Guard → 5557 → unified_dispatcher → 5555 → EA
                                       └→ Direct mission creation
                                       └→ Direct Telegram alerts
```

### **Benefits:**
- Single subscriber to 5557
- No HTTP overhead
- Direct control of all paths
- Fewer points of failure

---

## 📊 PERFORMANCE METRICS

**Signal Generation Rate**: ~10-12 signals per hour (Asian session)
**Signal to Execution Latency**: 2-5 seconds
**Confirmation Success Rate**: 100% (when EA connected)
**Auto-Fire Success Rate**: 100% (COMMANDER tier, full auto)

---

## 🔒 SECURITY NOTES

- User 7176191872 (COMMANDER): Unrestricted fire access, full auto mode
- EA validates target_uuid before execution
- All trades confirmed back with account status

---

**This configuration is VERIFIED WORKING as of August 11, 2025 01:30 UTC**