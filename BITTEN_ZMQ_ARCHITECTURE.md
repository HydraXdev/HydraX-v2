# 📡 BITTEN ZMQ Architecture: 3-Way Communication Overview

**Last Updated**: October 16, 2025
**Tracking System**: Unified Tracker (bitten.db + unified_tracking.jsonl)

The BITTEN trading system uses a 3-way ZeroMQ socket architecture to ensure real-time, reliable, and scalable communication between the Core Engine (Elite Guard) and the MT5 Execution Bridge (EA).

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
- Trade results update database (bitten.db) and unified tracker (unified_tracking.jsonl)

---

## 📊 Signal Tracking & Performance Analysis

### **Unified Tracking System**

**Primary Database**: `/root/HydraX-v2/bitten.db`
- `signals` table with `outcome`, `exit_price`, `duration_seconds` columns
- Single source of truth for all signal data
- Updated in real-time by unified_tracker process

**Tracking Log**: `/root/HydraX-v2/unified_tracking.jsonl`
- JSON Lines format for every completed signal
- Includes: signal_id, symbol, direction, pattern_type, confidence, outcome, duration
- Used for ML training and performance analysis

### **Quick Performance Check**

```bash
# Check recent signals
tail -20 /root/HydraX-v2/unified_tracking.jsonl

# Query win rate from database
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
    ROUND(CAST(COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) AS FLOAT) /
          COUNT(*) * 100, 1) as win_rate_pct
FROM signals WHERE outcome IS NOT NULL;"

# Check tracking process
pm2 status unified_tracker
```

---

## 📋 Next Steps

1. **Deploy Controller**: Run `python3 zmq_trade_controller.py` on Linux server
2. **Verify Connection**: EA should show "Connected to backend controller"
3. **Test Trade Flow**: Send test signal and verify all 3 channels working
4. **Integrate with Elite Guard**: Connect signal generation to command channel
5. **Risk Integration**: Use telemetry for dynamic position sizing
6. **Monitor Tracking**: Verify unified_tracker is recording all signal outcomes
