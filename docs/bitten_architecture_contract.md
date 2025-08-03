# 📋 BITTEN Architecture Contract

**STATUS**: PERMANENT CONTRACT - This document defines the immutable architecture of BITTEN  
**AUTHORITY**: System Architecture Authority  
**ENFORCEMENT**: All code must comply with this contract  
**LAST UPDATED**: August 1, 2025

---

## 🏛️ ARCHITECTURAL PRINCIPLES

### Core Truth
**BITTEN is a live execution platform powered by ZMQ sockets, not a script collection.**

### Fundamental Rules
1. **ZMQ is the nervous system** - It is NOT optional, NOT a plugin, it IS the protocol
2. **No file-based fallbacks** - fire.txt/trade_result.txt are DEPRECATED PERMANENTLY
3. **No HTTP signal dispatch** - All signals flow through ZMQ sockets
4. **Direct EA connection** - EA v7 connects via libzmq.dll, no middleware allowed
5. **Persistent socket architecture** - All components maintain live socket connections

---

## 🔌 ZMQ Port Map

```
┌─────────────────────────────────────────────────────────────┐
│ PORT 5555 - COMMAND CHANNEL (PUSH/PULL)                     │
│ Direction: Core → EA                                        │
│ Purpose: Trade signals, control commands                    │
│ Protocol: JSON messages                                     │
├─────────────────────────────────────────────────────────────┤
│ PORT 5556 - FEEDBACK CHANNEL (PUB/SUB)                     │
│ Direction: EA → Core                                        │
│ Purpose: Telemetry, trade results, heartbeats              │
│ Protocol: JSON messages                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 System Architecture Diagram

```
┌──────────────────┐     ZMQ Sockets      ┌─────────────────────┐
│                  │ ←─────────────────→  │                     │
│   EA v7 on VPS   │    Port 5555/5556    │  BITTEN Platform   │
│   (libzmq.dll)   │  134.199.204.67      │  (ZMQ Controller)   │
│                  │                       │                     │
└──────────────────┘                       └─────────────────────┘
         ↓                                           ↓
    MT5 Terminal                              ┌──────────────┐
    Trade Execution                           │ Signal Engine│
                                             │    (VENOM)   │
                                             ├──────────────┤
                                             │   CITADEL    │
                                             │   (Shield)   │
                                             ├──────────────┤
                                             │ Fire Router  │
                                             │  (Execution) │
                                             ├──────────────┤
                                             │ XP & Risk    │
                                             │  (Telemetry) │
                                             └──────────────┘
```

---

## 📦 JSON Message Specifications

### Fire Command (Port 5555)
```json
{
  "type": "signal",
  "signal_id": "VENOM_EURUSD_1234567890",
  "symbol": "EURUSD",
  "action": "buy",
  "lot": 0.01,
  "sl": 50,
  "tp": 100,
  "timestamp": "2025-08-01T12:34:56.789Z"
}
```

### Telemetry Packet (Port 5556)
```json
{
  "type": "telemetry",
  "uuid": "mt5_user_7176191872",
  "account": {
    "balance": 3000.00,
    "equity": 3000.00,
    "margin": 0.00,
    "free_margin": 3000.00,
    "profit": 0.00
  },
  "timestamp": "2025-08-01T12:34:56.789Z"
}
```

### Trade Result (Port 5556)
```json
{
  "type": "trade_result",
  "signal_id": "VENOM_EURUSD_1234567890",
  "status": "success",
  "ticket": 123456789,
  "price": 1.17485,
  "message": "Trade executed successfully",
  "timestamp": "2025-08-01T12:34:57.123Z"
}
```

---

## 🚫 FORBIDDEN PRACTICES (DO NOTs)

### NEVER implement:
1. **File-based execution** - No fire.txt, trade_result.txt, or any file communication
2. **HTTP POST for signals** - No webhook-style signal dispatch
3. **Wine/Docker containers** - ForexVPS hosts all MT5 terminals
4. **API middleware layers** - EA connects directly to ZMQ, no abstraction
5. **Synchronous blocking calls** - All socket operations must be async-ready
6. **Single-shot connections** - Maintain persistent socket connections

### NEVER remove:
1. **ZMQ daemon processes** - They are the core infrastructure
2. **Port bindings 5555/5556** - Essential for EA communication
3. **Telemetry processing** - Real-time account monitoring is mandatory
4. **XP/Risk integration** - Core gamification and risk management

---

## ✅ Checklist for Adding New Modules

When adding ANY new module to BITTEN, verify:

### 1. **Does it use ZMQ for communication?**
   - [ ] Uses existing ZMQ controller for signals
   - [ ] Subscribes to telemetry feed if needed
   - [ ] No file-based communication introduced

### 2. **Does it respect the architecture?**
   - [ ] No HTTP endpoints for trading signals
   - [ ] No file watchers for execution
   - [ ] No synchronous blocking operations

### 3. **Does it integrate properly?**
   - [ ] Connects to existing ZMQ infrastructure
   - [ ] Uses standard JSON message formats
   - [ ] Handles disconnections gracefully

### 4. **Is it documented?**
   - [ ] Architecture diagram updated
   - [ ] Message specs documented
   - [ ] Integration points clear

---

## 🔒 Enforcement Mechanisms

### Environment Variables
```bash
ZMQ_MODE=true       # Enables ZMQ mode
ZMQ_ENFORCE=true    # Enforces ZMQ-only operation
ZMQ_STRICT=1        # Blocks all legacy fallbacks
```

### Code Enforcement
```python
# Add to any module that might use legacy methods:
if os.getenv("ZMQ_STRICT") == "1" and legacy_file_path.exists():
    raise RuntimeError("❌ File-based execution blocked in ZMQ_STRICT mode")
```

### Startup Banner
```python
# Add to main components:
print("🧠 BITTEN ZMQ MODE ENABLED — File fallback disabled.")
print("📡 EA connects to 134.199.204.67:5555/5556")
```

---

## 📚 Reference Implementation

### Correct Signal Flow
```python
# ✅ CORRECT - Using ZMQ
from zmq_bitten_controller import BITTENZMQController

controller = BITTENZMQController()
controller.send_signal({
    "symbol": "EURUSD",
    "action": "buy",
    "lot": 0.01
})
```

### Incorrect Signal Flow
```python
# ❌ FORBIDDEN - File-based
with open("fire.txt", "w") as f:
    f.write(json.dumps(signal))  # NEVER DO THIS

# ❌ FORBIDDEN - HTTP POST
requests.post("http://localhost:8888/api/fire", json=signal)  # NEVER DO THIS
```

---

## 🎯 Final Word

This architecture contract is **PERMANENT**. Any deviation requires:
1. Written justification from system owner
2. Complete impact analysis
3. Migration plan for existing infrastructure
4. Update to this contract document

**Remember**: If Claude can forget, the system must be designed not to. This document ensures BITTEN's architecture remains consistent regardless of who maintains it.

---

**Contract Authority**: BITTEN Architecture Board  
**Effective Date**: August 1, 2025  
**Status**: IMMUTABLE CONTRACT