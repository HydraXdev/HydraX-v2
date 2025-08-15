# 🎯 BITTEN SYSTEM BLUEPRINT - PRODUCTION OPERATIONAL STATE
**Date**: August 8, 2025  
**Time**: 02:45 UTC  
**Status**: 100% OPERATIONAL - DO NOT MODIFY  
**Version**: ZMQ_COMPLETE_PIPELINE_v1.0

---

## 🔥 EXECUTIVE SUMMARY

The BITTEN trading system is now fully operational with complete ZMQ-based communication between all components. The system executes trades with proper risk management (SL/TP), tracks real-time balance updates, and maintains user-specific execution contexts.

**Current Account Status**: $850.47  
**Latest Successful Trade**: Ticket #20658628  
**Active User**: COMMANDER_DEV_001

---

## 🏗️ SYSTEM ARCHITECTURE

### **Core Data Flow**
```
MT5 EA (185.244.67.11) ←→ Linux Server (134.199.204.67) ←→ Signal Engines ←→ User Interfaces
```

### **Complete Pipeline**
```
1. Market Data Flow:
   MT5 EA → Port 5556 → Telemetry Bridge → Port 5560 → Elite Guard → Signal Generation

2. Signal Distribution:
   Elite Guard → Port 5557 → Signal Relay → Telegram/WebApp → Users

3. Trade Execution Flow:
   User Command → Port 5555 → MT5 EA → Trade Execution → Market

4. Confirmation Flow:
   Trade Result → Port 5558 → Confirmation Consumer → Balance Update → User Display
```

---

## 📡 ZMQ PORT ARCHITECTURE

### **Active Ports & Their Roles**

| Port | Direction | Component | Purpose | Status |
|------|-----------|-----------|---------|--------|
| **5555** | CC→EA | Fire Commands | Trade execution orders | ❌ Not bound (sent on demand) |
| **5556** | EA→CC | Market Data | Tick/candle data from MT5 | ✅ ESTABLISHED (185.244.67.11) |
| **5557** | Internal | Elite Guard Signals | Signal publishing | ✅ ACTIVE (local) |
| **5558** | EA→CC | Confirmations | Trade results & balance | ❌ Not bound (listened on demand) |
| **5560** | Internal | Data Relay | Market data distribution | ✅ ACTIVE (local) |
| **8888** | HTTP | WebApp | User interface | ✅ LISTENING |
| **8899** | HTTP | Commander Throne | Analytics dashboard | ✅ LISTENING |

### **Connection Details**
- **EA IP**: 185.244.67.11 (ForexVPS)
- **Server IP**: 134.199.204.67 (Command Center)
- **EA connects TO server** (never binds)
- **Server BINDS ports** (EA connects)

---

## 🔧 RUNNING PROCESSES & ROLES

### **Critical Processes (DO NOT KILL)**

| PID | Process | Role | Port Usage |
|-----|---------|------|------------|
| **2411770** | `zmq_telemetry_bridge_debug.py` | Receives market data from EA, redistributes | IN: 5556, OUT: 5560 |
| **2454558** | `elite_guard_zmq_relay.py` | Signal relay and distribution | IN: 5557 |
| **2472623** | `elite_guard_with_citadel.py` | SMC pattern detection, signal generation | IN: 5560, OUT: 5557 |
| **2474126** | `bitten_production_bot.py` | Main Telegram bot interface | Various |
| **2474376** | `bitten_voice_personality_bot.py` | Voice/personality bot | Telegram API |
| **2456496** | `webapp_server_optimized.py` | Web interface | 8888 |
| **2454259** | `commander_throne.py` | Analytics dashboard | 8899 |

---

## 🔥 FIRE COMMAND EXECUTION FLOW

### **Exact Data Flow for Trade Execution**

1. **User Initiates** (Telegram or WebApp)
   ```
   /fire SIGNAL_ID or Button Click
   ```

2. **Fire Command Format** (Port 5555)
   ```json
   {
     "type": "fire",
     "target_uuid": "COMMANDER_DEV_001",
     "symbol": "EURUSD",
     "entry": 0,        // 0 = market price
     "sl": 1.1550,      // Absolute price
     "tp": 1.1750,      // Absolute price
     "lot": 0.01
   }
   ```

3. **EA Receives & Executes**
   - EA (PULL socket) receives from port 5555
   - Executes market order with SL/TP
   - Trade hits broker

4. **Confirmation Sent Back** (Port 5558)
   ```json
   {
     "type": "confirmation",
     "node_id": "NODE_843859_1148967296",
     "user_uuid": "COMMANDER_DEV_001",
     "symbol": "EURUSD",
     "status": "success",
     "ticket": 20658628,
     "price": 1.16631,
     "lot": 0.01,
     "message": "Trade executed successfully",
     "account": 843859,
     "balance": 850.47,
     "equity": 847.26,
     "free_margin": 828.61,
     "margin_level": 5196.38,
     "timestamp": "2025.08.08 05:27:29"
   }
   ```

5. **Balance Update Processing**
   - Confirmation consumer receives data
   - Updates user balance: $850.47
   - Updates risk calculations for next trade
   - Broadcasts to user displays

---

## 📊 MARKET DATA FLOW

### **Tick Data Pipeline**

1. **EA Sends** (Every tick)
   ```json
   {
     "type": "tick",
     "symbol": "EURUSD",
     "bid": 1.16630,
     "ask": 1.16632,
     "spread": 2,
     "volume": 250,
     "timestamp": 1754613325
   }
   ```

2. **Telemetry Bridge** (Port 5556 → 5560)
   - Receives from EA on 5556
   - Validates and cleans data
   - Republishes to 5560

3. **Elite Guard Consumes** (Port 5560)
   - Builds OHLC candles
   - Detects SMC patterns
   - Generates signals

---

## 🎯 SIGNAL GENERATION FLOW

### **Elite Guard Signal Pipeline**

1. **Pattern Detection**
   - Liquidity Sweep Reversal
   - Order Block Bounce
   - Fair Value Gap Fill

2. **Signal Format** (Port 5557)
   ```json
   {
     "signal_id": "ELITE_GUARD_EURUSD_1754613325",
     "symbol": "EURUSD",
     "direction": "BUY",
     "entry_price": 1.16630,
     "sl": 1.16530,
     "tp": 1.16830,
     "confidence": 75.0,
     "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
     "citadel_score": 8.5
   }
   ```

3. **Distribution**
   - Published to port 5557
   - Relayed to Telegram groups
   - Displayed in WebApp

---

## 🔐 USER CONTEXT MANAGEMENT

### **UUID-Based Execution**

Each user has a unique UUID that tracks:
- Account balance
- Risk parameters
- Trade history
- Position status

**Example**: COMMANDER_DEV_001
- Current Balance: $850.47
- Risk Per Trade: 2% ($17.01)
- Active Positions: 2
- Last Update: 2025-08-08 02:45:00

---

## 🔌 INTEGRATION POINTS

### **Available for Enhancement**

1. **Signal Consumption** (Port 5557)
   - Can add more signal consumers
   - Can add signal filters/enhancers

2. **Balance Updates** (Port 5558)
   - Can add database persistence
   - Can add risk management layers

3. **Market Data** (Port 5560)
   - Can add more pattern detectors
   - Can add ML models

4. **User Interfaces**
   - WebApp (Port 8888) - Can add features
   - Throne (Port 8899) - Can add analytics

### **DO NOT MODIFY**
- Fire command format
- Port bindings
- EA communication protocol
- Confirmation format

---

## ✅ VERIFIED FUNCTIONALITY

### **What's Working**
1. ✅ Market data flow from EA
2. ✅ Signal generation from patterns
3. ✅ Fire command execution
4. ✅ Stop Loss/Take Profit setting
5. ✅ Trade confirmations
6. ✅ Real-time balance updates
7. ✅ User UUID tracking
8. ✅ Multi-bot ecosystem

### **Known Constraints**
- EA is purely a conduit (no position management)
- All risk management happens server-side
- Firewall must allow ports 5555-5560

---

## 🚀 NEXT INTEGRATION OPPORTUNITIES

With this solid foundation, we can now:

1. **Add Database Layer**
   - Persist confirmations
   - Track user history
   - Analyze performance

2. **Enhance Risk Management**
   - Dynamic position sizing
   - Drawdown protection
   - Correlation analysis

3. **Expand Signal Sources**
   - Add more pattern detectors
   - Integrate external signals
   - ML model predictions

4. **Improve User Experience**
   - Real-time dashboards
   - Performance analytics
   - Social features

---

## 📝 CRITICAL NOTES

1. **EA Version**: BITTEN Universal EA v2 (with SL/TP fix applied Aug 8)
2. **Broker**: MetaQuotes-Demo (Account 843859)
3. **Server Location**: 134.199.204.67
4. **EA Location**: 185.244.67.11 (ForexVPS)
5. **Firewall**: Ports 5555-5560 MUST remain open

---

## 🔒 SYSTEM FREEZE DECLARATION

**This blueprint represents the WORKING PRODUCTION STATE as of August 8, 2025 02:45 UTC.**

**DO NOT MODIFY:**
- Running processes
- Port configurations  
- Message formats
- ZMQ socket types

**This is the foundation. Build on top, don't rebuild.**

---

**Signed**: Claude Code Agent  
**Authority**: BITTEN System Architecture Documentation  
**Status**: PRODUCTION OPERATIONAL - FROZEN STATE