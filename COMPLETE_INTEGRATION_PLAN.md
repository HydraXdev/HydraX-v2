# BITTEN COMPLETE SYSTEM INTEGRATION PLAN
**Date**: October 1, 2025 02:52 UTC
**Agent**: Claude Code (Sonnet 4.5)
**Objective**: Wire up HydraSocket v1.0 (native TCP) with existing BITTEN infrastructure (ZMQ)

---

## 🎯 EXECUTIVE SUMMARY

**Goal**: Enable complete data flow from MT5 EA → Elite Guard → Telegram → Fire → Execution → Confirmation with full analytics and telemetry.

**Current State**:
- ✅ EA attached to chart, sending account data
- ❌ EA not sending market data (watchlist not initialized)
- ❌ EA cannot receive commands (TCP/ZMQ protocol mismatch on port 5555)
- ❌ Elite Guard starved for data (only 1 symbol has M1 data)

**Architecture Challenge**: Migration from ZMQ-based EA to native TCP socket EA requires protocol bridges.

---

## 🏗️ FINAL ARCHITECTURE DESIGN

### **Data Flow: EA → Brain**

```
┌─────────────────────────────────────────────────────────────────┐
│ MT5 EA (HydraSocket v1.0 - Native TCP Sockets)                  │
│ - Account: 843859                                                │
│ - Balance: $7,978.85 (live, updating every second)              │
│ - Sends: account_summary, position_heartbeat, bar_closed, tick  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Native TCP
┌─────────────────────────────────────────────────────────────────┐
│ Port 5559: Universal Bridge (TCP→ZMQ Translation Layer)         │
│ - Receives: All EA events via native TCP                        │
│ - Account State Manager: Captures balance/equity for sizing     │
│ - Forwards: Market data as ZMQ PUSH to port 5556                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ZMQ PUSH
┌─────────────────────────────────────────────────────────────────┐
│ Port 5556: zmq_telemetry_bridge (ZMQ PULL → PUB)                │
│ - Existing infrastructure component                              │
│ - Publishes to port 5560 for subscribers                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ZMQ PUB (port 5560)
┌─────────────────────────────────────────────────────────────────┐
│ Elite Guard v7.0 BALANCED (Pattern Detection Engine)            │
│ - Subscribes to port 5560                                        │
│ - Detects: 6 SMC patterns across 20 symbols                     │
│ - Publishes signals to port 5557                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Signals
┌─────────────────────────────────────────────────────────────────┐
│ Signal Distribution Pipeline                                     │
│ - signals_zmq_to_redis → Redis streams                          │
│ - signals_redis_to_webapp → WebApp API                          │
│ - athena_broadcaster → Telegram notifications                   │
└─────────────────────────────────────────────────────────────────┘
```

### **Command Flow: Brain → EA**

```
┌─────────────────────────────────────────────────────────────────┐
│ User Action (Telegram /fire or WebApp button)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ WebApp / Telegram Bot                                            │
│ - Position sizing with live balance from Account State Manager  │
│ - Creates fire command with proper lot size                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ZMQ PUSH
┌─────────────────────────────────────────────────────────────────┐
│ IPC Queue: ipc:///tmp/bitten_cmdqueue                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ZMQ PULL
┌─────────────────────────────────────────────────────────────────┐
│ Command Router (ZMQ ROUTER on port 5555)                        │
│ - Receives commands from IPC queue                              │
│ - Routes to connected dealers/bridges by target_uuid            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ZMQ multipart
┌─────────────────────────────────────────────────────────────────┐
│ NEW: Command Bridge (ZMQ→TCP Translation)                       │
│ - Subscribes as ZMQ DEALER with identity "COMMANDER_DEV_001"    │
│ - Runs TCP server on port 5557                                  │
│ - EA connects to port 5557 as TCP client                        │
│ - Translates: ZMQ JSON frames → TCP JSONL stream                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Native TCP (port 5557)
┌─────────────────────────────────────────────────────────────────┐
│ MT5 EA - Command Reception (PollCommandsTCP)                    │
│ - Connects to port 5557 via SocketConnect()                     │
│ - Reads commands via SocketReadAllCmd()                         │
│ - Processes: feed_set, fire, close, etc.                        │
│ - Executes trades via MT5 API                                   │
└─────────────────────────────────────────────────────────────────┘
```

### **Confirmation Flow: EA → Brain**

```
┌─────────────────────────────────────────────────────────────────┐
│ MT5 EA - Trade Execution                                         │
│ - OrderSend() returns ticket                                     │
│ - Emits confirmation event                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Native TCP
┌─────────────────────────────────────────────────────────────────┐
│ Port 5558: confirm_listener_v207                                │
│ - Receives confirmations (MUST support native TCP from EA)      │
│ - Parses: fire_id, ticket, price, status                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Database write
┌─────────────────────────────────────────────────────────────────┐
│ fires Table (bitten.db)                                          │
│ - UPDATE fires SET status='FILLED', ticket=X, price=Y           │
│ - WebApp /me endpoint shows updated status                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 IMPLEMENTATION PHASES

### **PHASE 1: Initialize EA Watchlist (15 minutes)**

**Objective**: Get market data flowing from EA to Elite Guard

**Critical Issue**: EA has no watchlist configured, sends no market data.

**Solution Options**:

**Option A - TCP Command Bridge (Proper, Long-term)**
1. Create TCP server on port 5557 for EA command connection
2. Bridge to ZMQ command_router for command delivery
3. Send feed_set command through bridge
4. EA initializes watchlist and starts streaming data

**Option B - Manual Config File (Quick, Temporary)**
1. User creates `HydraFeed.cfg` in MT5's `MQL5/Files/` directory:
   ```
   symbols=XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF
   tfs=M1,M5,H1
   lookback=200
   ```
2. Restart EA (or wait for next OnInit trigger)
3. EA calls BuildWatchlist() and EmitBootstrap()
4. Market data starts flowing immediately

**Option C - EA Code Fix (Permanent, Requires Recompile)**
1. Modify EA OnInit() to use input defaults when no config file exists
2. Recompile and redeploy EA
3. EA initializes automatically on attach

**Recommended**: Option A (proper architecture) with Option B as immediate workaround.

**Actions**:
1. ✅ Universal Bridge already fixed to forward to port 5556 (done)
2. Create TCP Command Bridge (port 5557)
3. Send feed_set command
4. Verify market data appears in logs within 30 seconds

**Validation**:
```bash
# Should show bar_closed, custom_bar_closed events
tail -f /var/log/hydrasocket_universal_bridge.log | grep -E "bar_closed|custom_bar"

# Elite Guard should show 20 symbols with data
pm2 logs elite-guard | grep "PATTERN SCAN"
```

---

### **PHASE 2: Fire Command Infrastructure (30 minutes)**

**Objective**: Enable Brain to send fire commands to EA for trade execution

**Components**:

**A. TCP Command Bridge (NEW)**
```python
# File: /root/HydraX-v2/zmq_to_tcp_command_bridge.py

import zmq
import socket
import json
import threading

class CommandBridge:
    """
    Bridges ZMQ command_router to TCP server for EA connections

    ZMQ Side:
    - Connects as DEALER to command_router (port 5555)
    - Identity: b"COMMANDER_DEV_001"
    - Receives commands routed by target_uuid

    TCP Side:
    - Binds TCP server on port 5557
    - Accepts EA client connection
    - Sends commands as JSONL (JSON + newline)
    """

    def __init__(self):
        # ZMQ side
        self.zmq_context = zmq.Context()
        self.dealer = self.zmq_context.socket(zmq.DEALER)
        self.dealer.identity = b"COMMANDER_DEV_001"
        self.dealer.connect("tcp://127.0.0.1:5555")

        # TCP side
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server.bind(('0.0.0.0', 5557))
        self.tcp_server.listen(1)

        self.ea_connection = None

    def accept_ea_connection(self):
        """Accept EA TCP connection (blocking)"""
        print("⏳ Waiting for EA connection on port 5557...")
        self.ea_connection, addr = self.tcp_server.accept()
        print(f"✅ EA connected from {addr}")

    def zmq_to_tcp_loop(self):
        """Forward commands from ZMQ to TCP"""
        while True:
            # Receive from command_router
            frames = self.dealer.recv_multipart()

            # Last frame is the command JSON
            command_json = frames[-1].decode('utf-8')

            # Send to EA as JSONL
            if self.ea_connection:
                try:
                    self.ea_connection.send((command_json + '\n').encode('utf-8'))
                    print(f"→ Sent to EA: {command_json[:100]}")
                except BrokenPipeError:
                    print("❌ EA disconnected")
                    self.ea_connection = None
```

**B. Integration with Existing Systems**
- command_router already routes by target_uuid
- Fire commands from IPC queue → command_router → CommandBridge → EA
- No changes needed to webapp or enqueue_fire.py

**Actions**:
1. Create `/root/HydraX-v2/zmq_to_tcp_command_bridge.py`
2. Start as background process or PM2
3. Verify EA connects successfully
4. Test fire command delivery

**Validation**:
```bash
# Bridge should show EA connection
tail -f /var/log/command_bridge.log | grep "EA connected"

# Test command with existing tools
python3 /root/HydraX-v2/test_fire_queue.py

# EA should execute and send confirmation
pm2 logs confirm_listener | grep "FILLED"
```

---

### **PHASE 3: Confirmation Reception (15 minutes)**

**Objective**: Ensure EA confirmations reach Brain and update database

**Current Status**: `confirm_listener_v207` running on port 5558

**Requirement**: Verify listener supports native TCP from EA (not just ZMQ)

**Actions**:
1. Check confirm_listener code for TCP support
2. If ZMQ-only, add TCP socket listener
3. Test with manual fire command
4. Verify fires table updates with ticket/price

**Validation**:
```bash
# Database should show FILLED status
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT fire_id, status, ticket, price FROM fires ORDER BY created_at DESC LIMIT 5;"

# Should see recent fill
# ELITE_GUARD_EURUSD_123456 | FILLED | 20813351 | 1.09543
```

---

### **PHASE 4: Signal Generation Pipeline (20 minutes)**

**Objective**: Verify complete signal flow from Elite Guard to Telegram

**Components to Verify**:
1. Elite Guard scanning with 20 symbols of live data
2. Signal publishing to port 5557 (ZMQ PUB)
3. signals_zmq_to_redis capturing and storing
4. signals_redis_to_webapp feeding webapp API
5. athena_broadcaster sending Telegram notifications

**Actions**:
1. Monitor Elite Guard for pattern detections
2. Check Redis stream for signals
3. Verify webapp /api/signals endpoint
4. Check Telegram group for alerts

**Validation**:
```bash
# Elite Guard should detect patterns
pm2 logs elite-guard | grep "PATTERN DETECTED"

# Redis should have signals
redis-cli XLEN signals_stream

# Telegram should show alerts
# Check group -1002581996861 for messages
```

---

### **PHASE 5: Analytics & Telemetry (15 minutes)**

**Objective**: Ensure all events logged and tracked properly

**Components**:
1. Event Bus - Receives all EA events
2. comprehensive_tracking.jsonl - Signal tracking
3. canonical_tracker - Performance metrics
4. Database tables - Complete schema

**Actions**:
1. Verify event_bus receiving EA events
2. Check comprehensive_tracking.jsonl for new signals
3. Verify canonical_tracker updating metrics
4. Audit database schema completeness

**Validation**:
```bash
# Event bus should show EA events
pm2 logs event_bus | grep "843859"

# Tracking should log signals
tail -f /root/HydraX-v2/comprehensive_tracking.jsonl | jq .

# Canonical tracker should update
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s','now','-1 hour');"
```

---

### **PHASE 6: User Risk & Position Sizing (20 minutes)**

**Objective**: Integrate user-specific risk preferences with live balance

**Current State**:
- Account State Manager captures live balance ($7,978.85)
- Position sizing uses hardcoded 2% risk
- User preferences NOT in database

**Required Changes**:

**A. Database Schema**
```sql
-- Add to users table or create user_settings
ALTER TABLE users ADD COLUMN risk_percent REAL DEFAULT 0.02;
ALTER TABLE users ADD COLUMN max_position_size REAL DEFAULT 10.0;
ALTER TABLE users ADD COLUMN min_position_size REAL DEFAULT 0.01;
```

**B. Position Sizing Integration**
```python
# In enqueue_fire.py or fire command handler

# Get user risk preference
user_risk = get_user_risk_percent(user_id) or 0.02

# Get live balance from Account State Manager
account_data = account_manager.get_account(account_id)
balance = account_data['balance']

# Calculate position size
risk_amount = balance * user_risk
sl_pips = abs(signal['entry'] - signal['sl']) / pip_size
lot_size = risk_amount / (sl_pips * pip_value_per_lot)
lot_size = round(max(0.01, min(lot_size, 10.0)), 2)
```

**Actions**:
1. Add risk_percent column to database
2. Create user settings management functions
3. Update position sizing in enqueue_fire.py
4. Add UI controls in webapp/Telegram for risk adjustment

**Validation**:
```bash
# Database should have user risk settings
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT user_id, risk_percent FROM users WHERE user_id='7176191872';"

# Fire commands should use custom risk
python3 -c "from enqueue_fire import calculate_position_size; \
  print(calculate_position_size(7978.85, 1.09, 1.08, 0.03))"  # 3% risk
```

---

### **PHASE 7: End-to-End Validation (15 minutes)**

**Objective**: Verify complete system integration with real trade

**Test Scenario**:
1. EA sending market data (20 symbols, M1/M5/H1)
2. Elite Guard detects pattern → generates signal
3. Signal published to Redis/WebApp
4. Telegram alert sent to user
5. User clicks /fire button
6. Fire command created with live balance sizing
7. Command routed through bridge to EA
8. EA executes trade on MT5
9. Confirmation sent back through port 5558
10. Database updated with ticket/price
11. Webapp /me shows FILLED status
12. Analytics logged in comprehensive_tracking.jsonl

**Validation Checklist**:
```bash
# 1. Market Data
tail -f /var/log/hydrasocket_universal_bridge.log | head -10

# 2. Elite Guard
pm2 logs elite-guard --lines 20

# 3. Signals
curl -s http://localhost:8888/api/signals | jq .

# 4. Telegram
# Check group -1002581996861

# 5-6. Fire Command
python3 /root/HydraX-v2/test_fire_queue.py

# 7-8. EA Execution
pm2 logs command_router | grep "Sent.*COMMANDER"

# 9. Confirmation
pm2 logs confirm_listener | grep "FILLED"

# 10. Database
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT fire_id, status, ticket, price FROM fires ORDER BY created_at DESC LIMIT 1;"

# 11. Webapp
curl -s http://localhost:8888/me?user_id=7176191872 | jq .recent_fires

# 12. Analytics
tail -1 /root/HydraX-v2/comprehensive_tracking.jsonl | jq .
```

---

## 🔧 CRITICAL FILES TO CREATE/MODIFY

### **NEW FILES (Must Create)**

1. `/root/HydraX-v2/zmq_to_tcp_command_bridge.py`
   - TCP server on port 5557 for EA commands
   - ZMQ DEALER to command_router
   - Bidirectional translation layer

2. `/root/HydraX-v2/verify_system_integration.sh`
   - Automated validation script
   - Runs all health checks
   - Reports system status

### **MODIFIED FILES**

1. `/root/HydraX-v2/hydrasocket_universal_bridge.py`
   - ✅ ALREADY FIXED: Now uses ZMQ PUSH to port 5556
   - Forwards market data to telemetry bridge

2. `/root/HydraX-v2/enqueue_fire.py`
   - Add user risk_percent lookup
   - Use live balance from Account State Manager
   - Calculate position size per user preferences

3. `/root/HydraX-v2/bitten.db` (schema)
   - Add risk_percent, max_position_size to users table

4. `/root/HydraX-v2/confirm_listener_v207.py`
   - Verify TCP support for EA confirmations
   - Add if needed

---

## 🎯 SUCCESS CRITERIA

**System is fully wired when:**

✅ **Data Flow**:
- [ ] EA sending bar_closed/custom_bar_closed (20 symbols × 3 timeframes)
- [ ] Elite Guard receiving data (logs show "20 symbols have M1 data")
- [ ] Pattern scanning active (detecting 6 pattern types)
- [ ] Signals publishing to Redis and webapp

✅ **Command Flow**:
- [ ] Fire commands reach EA within 100ms
- [ ] EA executes trades on MT5
- [ ] Trades appear in MT5 terminal

✅ **Confirmation Flow**:
- [ ] EA confirmations received on port 5558
- [ ] fires table updates with ticket/price
- [ ] Webapp shows FILLED status

✅ **Analytics**:
- [ ] Event bus receiving all EA events
- [ ] comprehensive_tracking.jsonl logging signals
- [ ] canonical_tracker showing metrics
- [ ] All databases updating correctly

✅ **User Experience**:
- [ ] Telegram alerts within 2 seconds of signal
- [ ] Fire button works reliably
- [ ] Position sizing uses live balance + user risk
- [ ] Execution confirmed visibly in webapp

---

## ⚡ QUICK START SEQUENCE

**For immediate results, execute in this order:**

```bash
# 1. Create Command Bridge (15 min)
cd /root/HydraX-v2
# Create zmq_to_tcp_command_bridge.py from template above
python3 zmq_to_tcp_command_bridge.py > /var/log/command_bridge.log 2>&1 &

# 2. Wait for EA to connect
sleep 5
tail -f /var/log/command_bridge.log | grep "EA connected"

# 3. Send feed_set command
python3 send_feed_set_command.py

# 4. Verify market data (30 sec)
sleep 30
tail -f /var/log/hydrasocket_universal_bridge.log | grep bar_closed

# 5. Check Elite Guard
pm2 logs elite-guard --lines 10

# 6. Test fire command
python3 test_fire_queue.py

# 7. Verify execution
pm2 logs confirm_listener | grep FILLED

# 8. Check database
sqlite3 bitten.db "SELECT * FROM fires ORDER BY created_at DESC LIMIT 1;"
```

---

## 📊 MONITORING DASHBOARD

**Key Logs to Monitor**:

```bash
# Market Data Flow
watch -n5 'tail -20 /var/log/hydrasocket_universal_bridge.log | grep -c bar_closed'

# Elite Guard Patterns
watch -n5 'pm2 logs elite-guard --lines 1 --nostream | grep "PATTERN SCAN"'

# Command Delivery
watch -n2 'pm2 logs command_router --lines 1 --nostream | grep "Sent"'

# Confirmations
watch -n2 'pm2 logs confirm_listener --lines 1 --nostream | grep "FILLED"'

# Signal Activity
watch -n5 'redis-cli XLEN signals_stream'
```

---

## 🚨 TROUBLESHOOTING GUIDE

**Issue**: No market data from EA
- Check: Universal Bridge logs for bar_closed events
- Fix: Send feed_set command via Command Bridge
- Verify: EA has HydraFeed.cfg or received feed_set

**Issue**: Fire commands not reaching EA
- Check: Command Bridge connection status
- Fix: Restart bridge, verify EA reconnects
- Verify: command_router logs show "Sent to COMMANDER_DEV_001"

**Issue**: Confirmations not received
- Check: confirm_listener supports TCP (not just ZMQ)
- Fix: Add TCP socket listener to confirm_listener
- Verify: EA logs show "sent confirmation to port 5558"

**Issue**: Elite Guard not detecting patterns
- Check: Receiving market data from telemetry bridge?
- Fix: Verify port 5560 subscription
- Verify: Elite Guard logs show "X symbols have M1 data"

---

## 🎯 FINAL ARCHITECTURE DIAGRAM

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          MT5 TERMINAL (EA)                                │
│  HydraSocket v1.0 Native TCP - Account 843859 - $7,978.85 Balance       │
└────────┬─────────────────────────────────────────────────────┬───────────┘
         │ TCP 5559 (events)                                    │ TCP 5557 (commands)
         ↓                                                       ↓
┌─────────────────────────┐                         ┌─────────────────────────┐
│   Universal Bridge      │                         │   Command Bridge        │
│   TCP→ZMQ Translation   │                         │   ZMQ→TCP Translation   │
│   - Account data        │                         │   - ZMQ DEALER          │
│   - Market data         │                         │   - TCP Server 5557     │
│   - PUSH to port 5556   │                         │   - Routes to EA        │
└────────┬────────────────┘                         └─────────┬───────────────┘
         │ ZMQ PUSH                                           │ ZMQ from 5555
         ↓                                                     ↓
┌─────────────────────────┐                         ┌─────────────────────────┐
│  zmq_telemetry_bridge   │                         │   command_router        │
│  PULL 5556 → PUB 5560   │                         │   ROUTER on port 5555   │
└────────┬────────────────┘                         └─────────┬───────────────┘
         │ ZMQ PUB                                            │ IPC PULL
         ↓                                                     ↓
┌─────────────────────────┐                         ┌─────────────────────────┐
│   Elite Guard v7.0      │                         │  IPC Queue (cmdqueue)   │
│   SUB 5560              │                         │  Fire commands          │
│   Pattern Detection     │──── Signals ────→       └─────────┬───────────────┘
│   PUB 5557              │                                   │
└─────────────────────────┘                                   │
         │                                                     │
         ↓                                                     │
┌─────────────────────────┐                                   │
│  Signal Distribution    │                                   │
│  - Redis                │                                   │
│  - WebApp               │←──────────────────────────────────┘
│  - Telegram (Athena)    │         Fire button press
└─────────────────────────┘
```

---

**END OF INTEGRATION PLAN**

This plan provides a complete roadmap for wiring up the entire BITTEN system with HydraSocket v1.0 EA. Execute phases sequentially for best results.
