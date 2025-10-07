# 📡 BITTEN ZMQ Architecture: 3-Way Communication Overview

The BITTEN trading system uses a 3-way ZeroMQ socket architecture to ensure real-time, reliable, and scalable communication between the Core Engine (VENOM/CITADEL) and the MT5 Execution Bridge (EA).

---

## 🔁 1. Command Stream (Core ➜ EA)

**Socket Type:** ZMQ_PUSH or ZMQ_PUB → ZMQ_PULL or ZMQ_SUB
**Purpose:** Sends trade signals to the EA for execution.

```json
{
  "type": "signal",
  "action": "buy",
  "symbol": "XAUUSD",
  "lot": 0.1,
  "tp": 40,
  "sl": 20,
  "signal_id": "VENOM_XAU_001"
}
```

> ✅ This is how the core tells the EA what to do.

---

## 📊 2. Telemetry Stream (EA ➜ Core)

**Socket Type:** ZMQ_PUSH → ZMQ_PULL
**Purpose:** Sends real-time account info back to the core (balance, equity, margin).

```json
{
  "type": "telemetry",
  "uuid": "user-001",
  "balance": 834.22,
  "equity": 818.9,
  "margin": 112.12
}
```

> ✅ This allows the core to make decisions based on live broker data.

---

## 🎯 3. Execution Feedback (EA ➜ Core)

**Socket Type:** ZMQ_PUSH or ZMQ_REQ → ZMQ_PULL or ZMQ_REP
**Purpose:** Confirms whether trades were accepted or failed.

**On success:**

```json
{
  "type": "trade_result",
  "signal_id": "VENOM_XAU_001",
  "status": "success",
  "ticket": 8412389,
  "price": 2341.22
}
```

**On failure:**

```json
{
  "type": "error",
  "signal_id": "VENOM_XAU_001",
  "error": "Trade is not allowed"
}
```

> ✅ This gives the core proof of execution or insight into broker failure.

---

## 🔐 Why All 3 Are Required

| Channel               | Purpose             | Without it                       |
| --------------------- | ------------------- | -------------------------------- |
| Core ➜ EA             | Trade command       | No trades fire                   |
| EA ➜ Core (telemetry) | Risk logic, XP sync | Core is blind                    |
| EA ➜ Core (feedback)  | Confirm execution   | No accountability or post-mortem |

---

## ✅ Summary

BITTEN's ZMQ communication system uses three dedicated sockets per bridge:

1. **🔥 Command Channel** – fires structured trade packets.
2. **📡 Telemetry Channel** – streams real-time broker/account data.
3. **✅ Feedback Channel** – returns trade execution results.

> This 3-way system ensures BITTEN is not just reactive — it's aware, self-correcting, and battle-ready at scale.

---

## 🚀 Implementation Status

### EA Side (MT5)

- **BITTENBridge_TradeExecutor_ZMQ_v7.mq5** - Complete implementation
  - PULL commands from port 5555
  - PUSH telemetry/feedback to port 5556
  - Handles all message types with robust error handling

### Linux Side (Core)

- **zmq_trade_controller.py** - Basic controller implementation
  - PUSH commands on port 5555
  - PULL telemetry/feedback on port 5556
  - Ready for VENOM/CITADEL integration

### Integration Points

- Fire Router can use `execute_zmq_fire()` to send commands
- Telemetry data feeds into risk calculations
- Trade results update user statistics and XP

---

## 📋 Next Steps

1. **Deploy Controller**: Run `python3 zmq_trade_controller.py` on Linux server
2. **Verify Connection**: EA should show "Connected to backend controller"
3. **Test Trade Flow**: Send test signal and verify all 3 channels working
4. **Integrate with VENOM**: Connect signal generation to command channel
5. **Risk Integration**: Use telemetry for dynamic position sizing
