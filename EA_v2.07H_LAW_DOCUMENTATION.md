# BITTEN v2.078 — LAW Documentation
## Logging • Audit • Workflows (LAW) Architecture

**Version**: 2.078 (PRO STABLE QUIET)
**Date**: September 23, 2025
**Status**: PRODUCTION READY
**Scope**: BITTEN_Universal_EA_v2.078_PRODUCTION.mq5 + Core Sockets (5555/5556/5558/5560)

---

## 0. Executive Summary

### Complete BITTEN Trading System Architecture

**BITTEN v2.078** is a distributed automated trading system that processes market signals through a sophisticated pipeline:

**Signal Flow Architecture:**
```
Elite Guard (Pattern Detection) → WebApp (Risk Management) → Auto-Fire Logic →
Command Router → EA v2.078 → MT5 Execution → Confirmation + Snapshots → Position Tracking
```

**ZMQ Communication Channels:**
- **DEALER 5555** (Core→EA): Fire commands with UUID routing - `{"type":"fire","target_uuid":"COMMANDER_DEV_001",...}`
- **PUSH 5556** (EA→Core): Market telemetry (ticks, candles, connection status)
- **PUSH 5558** (EA→Core): Trade confirmations + signal snapshots with OHLC data (v2.078)
- **PUSH 5560** (EA→Core): Enhanced HEARTBEAT_METRICS with complete position arrays

**Key System Features v2.078:**
- **Enhanced Signal Snapshots**: Captures OHLC data with pattern overlays on every fire command
- **Configurable Timeframes**: M1, M5, M15, M30, H1 snapshot support with configurable bar count
- **Robust JSON Parser**: Fixed CharToString encoding issues for enhanced reliability
- **Auto-Fire Pipeline**: 80-89% confidence signals fire automatically
- **Position Tracking**: Real-time open position monitoring with enhanced HEARTBEAT_METRICS
- **Risk Management**: 3% risk per trade with normalized lot size calculation
- **Multi-Symbol Support**: 16+ trading pairs with symbol-specific pip calculations
- **Hybrid Position Management**: 25%/25%/50% partial close strategy with trailing stops

### Architecture Design Principles (v2.07 → v2.078)

1. **Market Execution Priority** - entry=0 forces immediate market execution (no pending orders)
2. **Enhanced Signal Intelligence** - Automatic signal snapshots with OHLC data and pattern overlays
3. **Event-Driven Confirmations** - ZMQ PUSH confirms with status, ticket, price, and market context
4. **Configurable Market Analysis** - Timeframe and bar count configuration for optimal pattern recognition
5. **Identity-Based Routing** - UUID ensures commands reach correct EA instance with enhanced validation
6. **Production-Grade Reliability** - Handles failed trades, tracks positions, manages risk with improved error handling
7. **Real-Time Position Awareness** - Enhanced HEARTBEAT_METRICS with complete position arrays
8. **Intelligent Auto-Fire Logic** - Only fires when confidence ≥80-89% AND position slots available
9. **Robust Data Processing** - Fixed CharToString encoding issues for reliable JSON parsing

---

## 1. EA v2.078 Core Data Flow Blueprint

### 1.0 Visual System Flow

```
Router 5555 → Command Receiver (DEALER) ──> Validation Layer ──> Trade Execution
      │                                           │                      │
      │                                    [Rejected]                [MT5 OrderSend]
      │                                           │                      │
      ├── ping/wake ──> Pong Response ────────────┴──> Confirm (failed)  ├── success ──> Confirm (success)
      │                                                      │           │
OnTick ──> Symbol Scan ──> Tick JSON ──> 5556 Tick Publisher │           └── fail ──> Confirm (failed)
      │                                                      │
OnTimer ──> Heartbeat/Metrics ──> 5556 + 5560               │
      │                                                      │
OnTimer ──> Router Heartbeats ──> 5555                      │
      │                                                      │
Shutdown ──> Disconnect ──> 5556                            │
                                                             │
Signal Snapshots ──> 5558 Confirm Sender ◄──────────────────┤
All Confirmations ──> 5558 Confirm Sender ◄─────────────────┘
```

### 1.1 Execution Path Details

**Fire Command Path:**
1. Receive fire JSON from router (5555)
2. Parse + validate: Direction (BUY/SELL), SL/TP requirements, spread/hedge guards
3. **NEW v2.078**: Send signal snapshot JSON (before validation complete) with OHLC bars
4. If passed → build OrderSend with normalized lot size
5. On execution: send confirmation JSON with ticket, lot, status, enhanced telemetry

**Close Command Paths:**
- `close_all`: loops positions with correct magic, closes them, sends aggregated confirmation
- `close_ticket`: closes one ticket if valid, sends per-ticket confirmation

**Ping/Wake Paths:**
- Responds with pong including account metrics and hybrid status
- Wake also echoes AWAKE + triggers ping response

**Hybrid Management Path:**
- Attached per trade if hybrid_enabled in fire command
- Monitors: Partial closes at pip thresholds, breakeven move, trailing SL
- Sends hybrid_event JSON on each adjustment with enhanced metrics
- Purges state when position closed or EA removed

### 1.2 EA v2.078 Safety Gates

```mql5
// Pre-flight validation checks
✅ DLLs enabled check (TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
✅ Trading allowed check (AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
✅ UUID loaded from bitten_deployment.cfg or DEV override
✅ Rejects invalid UUIDs (length validation)
✅ Blocks invalid SL/TP structures (geometry + broker stops level)
✅ Hedge-block prevents opposite side stacking (InpBlockOppositeHedge)
✅ Spread-block prevents wide spread entries (InpMaxSpreadPoints)
✅ Volume normalization for MT5 compatibility (NormalizeLots function)
✅ Symbol availability check (SymbolSelect before execution)
```

### 1.3 Configuration Inputs (v2.078)

```mql5
input bool   InpVerboseLogging     = true;   // Toggle detailed logging and comments
input int    InpHybridFillingType  = -1;     // -1 omit type_filling on hybrid partials
input bool   InpBlockOppositeHedge = true;   // Block opposite side positions on same symbol
input double InpMaxSpreadPoints    = 0.0;    // 0=off; else reject if spread > limit (points)
input int    InpDeviationPoints    = 5;      // Slippage/deviation for market orders (points)
input int    InpTelemetryBeatSec   = 30;     // Heartbeat+metrics cadence (seconds)
input int    InpRouterBeatSec      = 5;      // Router heartbeat cadence (seconds)
input int    InpSnapshotBars       = 100;    // Number of bars to include in signal snapshots
input string InpSnapshotTF         = "M1";   // Default timeframe for snapshots ("M1","M5","M15","M30","H1")
```

### 1.4 Operational Specifications

**Magic Number**: `7176191872` (all BITTEN trades)

**Telemetry Cadence:**
- Router heartbeat: 5 seconds (configurable via InpRouterBeatSec)
- Dealer + Metrics heartbeat: 30 seconds (configurable via InpTelemetryBeatSec)

**Signal Snapshots (NEW v2.078):**
- Default: M1 timeframe, 100 bars
- Sent on every fire command before validation
- Includes pattern overlays and market metrics
- Configurable timeframe and bar count

**UUID Configuration:**
- DEV Account 843859 → "COMMANDER_DEV_001" (hardcoded override)
- Production: Load from MQL5\Files\bitten_deployment.cfg
- Format: UUID=COMMANDER_DEV_001

**Hybrid Management:**
- RAM-based (no persistence across EA restarts)
- 25% partial close at trigger pip levels
- Trailing stop with configurable distance
- Full lifecycle tracking via hybrid_event messages

---

## 1. Complete System Architecture

### 1.1 Signal Processing Pipeline (How It Actually Works)

```
[Elite Guard] → [Signal Generated 80-90% confidence]
       ↓
[WebApp Receives] → [BittenCore Validation] → [Risk Calculation]
       ↓
[Auto-Fire Check] → [Position Slots Available?] → [Confidence ≥80-89%?]
       ↓                                              ↓
[YES: Enqueue Fire]                          [NO: Manual Only]
       ↓
[IPC Queue] → [Command Router] → [ZMQ DEALER 5555]
       ↓
[EA v2.078] → [MT5 Market Execution] → [ZMQ PUSH 5558 Confirmation + Signal Snapshot]
       ↓
[Position Tracking Update] → [Event Bus Notification]
```

### 1.2 Network Topology & Purpose

```
[Core Server (134.199.204.67)]           [MT5 EA Client]
        |                                      |
   BINDS 5555 <---- DEALER (Commands) ----  CONNECTS  [Fire/Close Commands]
   BINDS 5556 <---- PUSH (Telemetry) ----  CONNECTS   [Market Data Feed]
   BINDS 5558 <---- PUSH (Events) -------  CONNECTS   [Trade Confirmations]
   BINDS 5560 <---- PUSH (Metrics) ------  CONNECTS   [Position Tracking]
```

**Why This Architecture:**
- **DEALER Socket**: Bi-directional, supports UUID routing for multi-EA environments
- **PUSH Sockets**: One-way, high-performance, no response needed
- **Separate Channels**: Prevents trade confirmations from blocking market data
- **Identity Routing**: Each EA has unique UUID, prevents command cross-contamination

### 1.2 Port Assignments

| Port | Type | Direction | Purpose | Messages | Update Frequency |
|------|------|-----------|---------|----------|------------------|
| 5555 | DEALER | Core→EA | Commands | fire, close_ticket, close_all, ping, wake | On-demand |
| 5556 | PUSH | EA→Core | Telemetry | handshake, heartbeat, TICK, OHLC, disconnect | Every tick + 30s heartbeat |
| 5558 | PUSH | EA→Core | Events | confirmation, position_closed, pong, signal_snapshot | Immediate on events |
| 5560 | PUSH | EA→Core | Metrics | HEARTBEAT_METRICS with enhanced positions[] | Every 30s |

**Critical System Dependencies:**
- **Port 5555**: Must be available for trade execution (fire commands)
- **Port 5558**: Required for confirmation tracking and position updates
- **Port 5560**: Required for real-time position monitoring and auto-fire decisions
- **IPC Queue**: `/tmp/bitten_cmdqueue` for webapp→command_router communication

### 1.3 Auto-Fire Logic & Position Management

**Auto-Fire Decision Tree:**
```
1. Signal arrives with confidence X%
2. Check: X ≥ 80% AND X ≤ 89% ? → Proceed to step 3 : Manual only
3. Check: User 7176191872 in AUTO mode? → Proceed to step 4 : Manual only
4. Check: Open positions < 3 slots? → FIRE : Skip (position limit)
5. Calculate lot size: 3% risk ÷ (SL_pips × pip_value)
6. Adjust R:R: If R:R < 1.5, extend TP to achieve 1.5:1
7. Create fire command → IPC queue → Command router → EA
8. Await confirmation → Update position tracking
```

**Identity & Routing Protocol:**
```
EA UUID Loading:
1. Account 843859 → UUID = "COMMANDER_DEV_001" (hardcoded)
2. Fallback: Load from MQL5\Files\bitten_deployment.cfg
3. Set DEALER socket identity = UUID via ZMQ_IDENTITY
4. Command Validation: Reject if target_uuid != EA's UUID
5. Position Tracking: Update open_positions count in database
```

**Current Production Status:**
- **User 7176191872**: AUTO mode enabled, 3 position slots
- **Current Open**: 1 position (tracked in ea_instances.open_positions)
- **Auto-Fire Range**: 80-89% confidence signals only

---

## 2. Security Model

### 2.1 Transport Security

- **Protocol**: ZMQ TCP (cleartext within VPN)
- **Network**: Private VPC/VNet recommended
- **Firewall Rules**:
  ```
  Allow Inbound: TCP 5555,5556,5558,5560 from EA IPs only
  Block All Other Inbound
  EA Outbound: Allow TCP to Core IP
  ```

### 2.2 Authorization & Routing

```python
# Command Authorization Flow
if command.target_uuid != ea.loaded_uuid:
    drop_command()  # Silent drop, no confirmation
else:
    process_command()
```

### 2.3 Data Protection

- **PII Minimization**: Only account ID, no customer names
- **Comment Truncation**: fire_id ≤ 28 chars (MT5 limit)
- **Monetary Precision**: 2 decimal places for amounts
- **Price Precision**: Symbol-specific digits

### 2.4 Trade Safety Controls

1. **SL/TP Validation**: Geometry + broker stops level
2. **Hedge Prevention**: No opposite positions on same symbol
3. **Volume Normalization**: Step-aligned to broker requirements
4. **Symbol Availability**: SymbolSelect() before trade

---

## 3. Complete Message Contracts & Real Examples (v2.07)

### Auto-Fire vs Manual Fire Examples

**Recent System Activity (September 22, 2025):**
- **ELITE_RAPID_USDJPY_1758502680**: Manual fire → FILLED (ticket: 21754192)
- **ELITE_RAPID_USDCNH_1758503291**: Auto-fire attempted → FAILED (position limit?)
- **ELITE_RAPID_EURUSD_1758502385**: Auto-fire attempted → FAILED

### 3.1 Commands (→ 5555 DEALER)

#### FIRE Command
```json
{
  "type": "fire",
  "target_uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_USDJPY_1758502680",
  "symbol": "USDJPY",
  "direction": "SELL",
  "entry": 0,
  "sl": 148.364,
  "tp": 147.989,
  "lot": 0.5
}
```

**Field Requirements & Processing Logic:**
- **type**: Must be "fire" (validated in command_router.py)
- **target_uuid**: "COMMANDER_DEV_001" (UUID routing validation)
- **fire_id**: Unique signal identifier (links to original Elite Guard signal)
- **symbol**: Trading pair (e.g., USDJPY, USDCNH, EURUSD)
- **direction**: "BUY" or "SELL" (affects SL/TP price validation)
- **entry**: Always 0 in production (immediate market execution)
- **sl**: Stop loss price (validated against broker stops level)
- **tp**: Take profit price (auto-adjusted to achieve 1.5:1 R:R minimum)
- **lot**: Position size (calculated: 3% risk ÷ SL_distance)

**Dynamic R:R Processing Example (USDCNH):**
```
Original: SL=30.0p, TP=21.0p (R:R=0.70)
System detects R:R < 1.5, adjusts TP to achieve 1.5:1
Final: SL=30.0p, TP=45.0p (R:R=1.50)
```

#### CLOSE_TICKET Command
```json
{
  "type": "close_ticket",
  "target_uuid": "COMMANDER_DEV_001",
  "ticket": 12345678
}
```

#### CLOSE_ALL Command
```json
{
  "type": "close_all",
  "target_uuid": "COMMANDER_DEV_001"
}
```

#### PING Command
```json
{
  "type": "ping",
  "target_uuid": "COMMANDER_DEV_001",
  "ping_id": "health_check_1758296000"
}
```

### 3.2 Events (← 5558 PUSH)

#### CONFIRMATION (Fire Response - Enhanced v2.078)
```json
{
  "type": "confirmation",
  "version": "2.078",
  "command_type": "fire",
  "fire_id": "ELITE_RAPID_USDJPY_1758502680",
  "node_id": "NODE_843859_123456",
  "user_uuid": "COMMANDER_DEV_001",
  "status": "success",
  "ticket": 21173957,
  "price": 148.215,
  "lot": 0.5,
  "message": "OK SELL",
  "account": 843859,
  "currency": "USD",
  "balance": 10000.00,
  "equity": 10005.50,
  "floating_pnl": 5.50,
  "timestamp": "2025.09.23 00:58:58"
}
```

#### SIGNAL_SNAPSHOT (NEW v2.078 - Before Every Fire)
```json
{
  "type": "signal_snapshot",
  "user_uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_123456",
  "symbol": "USDJPY",
  "timeframe": "M1",
  "t0": "2025.09.23 00:58:55",
  "pattern": "LIQUIDITY_SWEEP_REVERSAL",
  "fire_id": "ELITE_RAPID_USDJPY_1758502680",
  "spread_pts": 1.2,
  "overlays": {
    "entry": 148.215,
    "sl": 148.364,
    "tp": 147.989
  },
  "bars": [
    {
      "t": 1758502800,
      "o": 148.220,
      "h": 148.245,
      "l": 148.198,
      "c": 148.215
    },
    {
      "t": 1758502740,
      "o": 148.185,
      "h": 148.230,
      "l": 148.175,
      "c": 148.220
    }
  ],
  "metrics": {
    "dir": "SELL",
    "lot": 0.5,
    "sl": 148.364,
    "tp": 147.989
  }
}
```

**Status Values & Meanings:**
- **FILLED**: Trade successfully executed on MT5 (ticket number provided)
- **FAILED**: Generic failure (could be position limit, connection, or validation)
- **REJECTED**: Broker rejected trade (insufficient margin, invalid stops, market closed)
- **INSUFFICIENT_MARGIN**: Specific margin requirement not met
- **INVALID_STOPS**: SL/TP distances violate broker minimum stops level

**Production Status Analysis (September 22, 2025):**
- **Manual Fires**: ✅ Working (USDJPY FILLED - ticket: 21754192)
- **Auto-Fire Logic**: ✅ Working (commands reach command router)
- **Auto-Fire Execution**: ❌ Failing (USDCNH, EURUSD = FAILED status)
- **Position Tracking**: ✅ Working (ea_instances.open_positions = 1)
- **Confidence Filtering**: ❌ Issue found (91.9% XAUUSD blocked, above 89% threshold)

**Auto-Fire Troubleshooting:**
```
Signal Flow Analysis:
1. ELITE_RAPID_USDCNH_1758503597 @ 84.3% → AUTO fire attempted → FAILED
2. ELITE_RAPID_XAUUSD_1758503581 @ 91.9% → AUTO fire blocked (>89% threshold)
3. Commands reach command_router.py successfully
4. Fire records created in database with FAILED status
5. No confirmations received from EA (suggests EA-side failure)

Possible Causes:
- EA connection issue (not processing commands)
- Broker rejection (insufficient margin, market hours)
- Position limit reached (system shows 1/3 positions used)
- EA timeout or processing error
```

#### POSITION_CLOSED
```json
{
  "type": "position_closed",
  "ticket": 12345678,
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "symbol": "XAUUSD",
  "volume": 0.10,
  "close_price": 2431.20,
  "profit": 17.40,
  "reason": "TP_HIT",
  "uuid": "COMMANDER_DEV_001",
  "timestamp": 1758296061
}
```

#### HYBRID_EVENT
```json
{
  "type": "hybrid_event",
  "target_uuid": "COMMANDER_DEV_001",
  "event": "PARTIAL_CLOSE",
  "ticket": 12345678,
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "volume": 0.03,
  "pips": 125.4,
  "node_id": "NODE_843859_123456",
  "timestamp": "2025.09.19 15:34:21"
}
```

### 3.3 Telemetry (← 5556 PUSH)

#### HANDSHAKE (On Init)
```json
{
  "type": "handshake",
  "deployment_mode": "universal_dealer_hybrid",
  "node_id": "NODE_843859_123456",
  "user_uuid": "COMMANDER_DEV_001",
  "account": 843859,
  "broker": "MetaQuotes-Demo",
  "server": "MetaQuotes-Demo",
  "chart_symbol": "XAUUSD",
  "monitored_symbols": 53,
  "symbol_list": "XAUUSD,GBPJPY,EURUSD,USDJPY,...",
  "currency": "USD",
  "balance": 10000.00,
  "equity": 10005.50,
  "leverage": 500,
  "version": "2.07H",
  "hybrid_enabled": true,
  "socket_type": "DEALER",
  "timestamp": "2025.09.19 15:20:45"
}
```

#### HEARTBEAT (Every ~30s)
```json
{
  "type": "heartbeat",
  "node_id": "NODE_843859_123456",
  "user_uuid": "COMMANDER_DEV_001",
  "account": 843859,
  "currency": "USD",
  "balance": 10005.50,
  "equity": 10005.50,
  "leverage": 500,
  "free_margin": 9890.00,
  "margin_level": 460.00,
  "symbols_monitored": 53,
  "ticks_processed": 1234,
  "hybrid_positions": 1,
  "socket_type": "DEALER_HYBRID",
  "timestamp": "2025.09.19 15:21:15"
}
```

### 3.4 Metrics (← 5560 PUSH)

#### HEARTBEAT_METRICS (Every ~30s)
```json
{
  "type": "HEARTBEAT_METRICS",
  "target_uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_123456",
  "currency": "USD",
  "balance": 10012.40,
  "equity": 10018.10,
  "leverage": 500,
  "margin": 200.50,
  "free_margin": 9817.60,
  "margin_level": 498.00,
  "ticks_processed": 1875,
  "hybrid_positions": 1,
  "open_positions": 2,
  "positions": [
    {
      "ticket": 12345678,
      "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
      "symbol": "XAUUSD",
      "direction": "BUY",
      "open_price": 2429.50,
      "current_price": 2430.20,
      "volume": 0.10,
      "pnl": 7.00
    }
  ],
  "timestamp": "2025.09.19 15:22:00"
}
```

---

## 4. Event Bus & Position Tracking System

### 4.1 Real-Time Position Monitoring

**Database Tracking:**
```sql
-- EA instances table tracks open positions
SELECT target_uuid, user_id, open_positions FROM ea_instances;
-- Result: COMMANDER_DEV_001 | 7176191872 | 1

-- Fires table tracks execution status
SELECT fire_id, status, ticket, price FROM fires ORDER BY created_at DESC;
-- Shows: FILLED (successful), FAILED (EA rejection), etc.
```

**Event Bus Architecture:**
```
EA v2.07 → ZMQ 5558 → confirm_listener → Database Update → Event Bus Notification
                                              ↓
Position Count Update → Auto-Fire Decision Logic → Slot Availability Check
```

**Position Slot Management:**
- **Total Slots**: 3 concurrent positions per user
- **Current Usage**: 1/3 positions occupied (tracked in real-time)
- **Auto-Fire Check**: Only fires if slots available
- **Manual Override**: Manual fires may exceed limits (user decision)

### 4.2 State Machines & Lifecycle

### 4.1 EA Lifecycle State Machine

```
[INIT] → Load UUID → Check Permissions → Open Sockets → Set Identity
  ↓
[HANDSHAKE] → Send HELLO (5555) + Handshake (5556)
  ↓
[ACTIVE] → Timer(1s) + OnTick + Commands
  ├─→ [HEARTBEAT] every 30s → 5556 & 5560
  ├─→ [TICK_STREAM] on price change → 5556
  ├─→ [COMMAND_RECV] non-blocking → Process
  └─→ [HYBRID_MONITOR] check positions → Events
  ↓
[DEINIT] → Send DISCONNECT → Close Sockets
```

### 4.2 Command Processing State Machine

```
[IDLE] → Receive Command → [VALIDATE_UUID]
           ↓                    ↓
      UUID Match?          No → [DROP]
           ↓
         Yes → [PARSE_TYPE]
                    ↓
    ┌──────────────┼──────────────┐
    ↓              ↓              ↓
  [FIRE]    [CLOSE_TICKET]   [CLOSE_ALL]
    ↓              ↓              ↓
[VALIDATE]    [EXECUTE]      [EXECUTE]
    ↓              ↓              ↓
[EXECUTE]   [CONFIRMATION]  [CONFIRMATION]
    ↓
[CONFIRMATION]
```

### 4.3 Position Lifecycle Tracking

```
[OPEN] → fire command → confirmation{success}
  ↓
[TRACKED] → HEARTBEAT_METRICS{positions[]}
  ↓
[HYBRID_ACTIVE] → Monitor pips
  ├─→ +8 pips → PARTIAL_CLOSE(25%) → hybrid_event
  ├─→ +12 pips → PARTIAL_CLOSE(25%) + SL_BREAKEVEN → hybrid_event
  └─→ Trailing → TRAIL_UPDATE → hybrid_event
  ↓
[CLOSED] → position_closed{reason}
```

---

## 5. Observability & Logging

### 5.1 Event Categories

| Category | Events | Log Level | Retention |
|----------|--------|-----------|-----------|
| SECURITY | UUID mismatch, DLL disabled, trade blocked | ERROR | 1 year |
| EXECUTION | confirmations, closes, hybrid events | INFO | 90 days |
| TELEMETRY | handshake, heartbeat, ticks, metrics | DEBUG | 7 days |
| ERRORS | DLL load, symbol unavailable, SL/TP invalid | ERROR | 90 days |

### 5.2 Structured Log Format

```json
{
  "ts": 1758296000,
  "category": "EXECUTION",
  "level": "INFO",
  "uuid": "COMMANDER_DEV_001",
  "node_id": "NODE_843859_123456",
  "account": 843859,
  "event_type": "confirmation",
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "ticket": 12345678,
  "status": "success",
  "payload_hash": "sha256:abcd1234..."
}
```

### 5.3 Key Metrics to Track

```python
# Per-UUID Metrics
open_positions_count
total_volume
account_equity
margin_level
win_rate
avg_pips_per_trade

# Socket Health
last_message_age{socket=5556/5558/5560}
messages_per_minute{type=TICK/heartbeat/confirmation}

# Command Performance
command_latency_p95{type=fire/close}
confirmation_success_rate
hedge_block_rate
```

---

## 6. Validation Test Matrix

| Test Case | Input | Expected Output | Socket |
|-----------|-------|-----------------|---------|
| EA Init | Attach EA | handshake within 3s | 5556 |
| Heartbeat | Wait 30s | heartbeat + HEARTBEAT_METRICS | 5556, 5560 |
| Ping Test | {"type":"ping","target_uuid":"..."} | pong with ping_id | 5558 |
| Fire Valid | BUY with valid SL/TP | confirmation{success} | 5558 |
| Fire Invalid SL | BUY with tp<price | confirmation{failed,"REJECTED"} | 5558 |
| Hedge Block | SELL when BUY exists | confirmation{failed,"HEDGE_BLOCKED"} | 5558 |
| Close Ticket | Valid ticket | close_confirmation{success} | 5558 |
| Close All | Any positions | close_confirmation summary | 5558 |
| UUID Wrong | Wrong target_uuid | No response (dropped) | None |
| TP Hit | Position hits TP | position_closed{reason:"TP_HIT"} | 5558 |
| Hybrid +8p | Position +8 pips | hybrid_event{PARTIAL_CLOSE} | 5558 |
| Disconnect | Detach EA | DISCONNECT message | 5556 |

---

## 7. Operations Runbook

### 7.1 Deployment Checklist

```bash
# 1. Prepare MT5 Environment
☐ MT5 x64 installed
☐ Allow DLL imports enabled
☐ Allow algo trading enabled
☐ Account has trading permissions

# 2. Install Dependencies
☐ Copy libzmq.dll (x64) → MQL5\Libraries\
☐ Copy libsodium-*.dll if required
☐ Verify MSVC runtime installed

# 3. Configure UUID
☐ Create MQL5\Files\bitten_deployment.cfg
☐ Add line: UUID=COMMANDER_DEV_001

# 4. Compile & Attach
☐ Compile BITTEN_Universal_EA_v2.07H_flat.mq5
☐ Attach to any chart
☐ Verify handshake received

# 5. Verify Connectivity
☐ Check Core logs for handshake on 5556
☐ Confirm heartbeats every 30s
☐ Test ping → pong roundtrip
```

### 7.2 Health Monitoring

```python
# Socket Liveness Check
def check_socket_health():
    thresholds = {
        5556: 40,  # heartbeat age seconds
        5560: 40,  # metrics age seconds
        5558: 300  # last event age seconds
    }
    for port, max_age in thresholds.items():
        if time() - last_message[port] > max_age:
            alert(f"Socket {port} stale")

# Command Health Check
def check_command_health():
    ping_id = f"health_{time()}"
    send_ping(ping_id)
    if not wait_for_pong(ping_id, timeout=1):
        alert("Command path unhealthy")
```

### 7.3 Incident Response

| Symptom | Check | Fix |
|---------|-------|-----|
| No handshake | Core binding? | Start Core before EA |
| No commands processed | UUID match? | Verify bitten_deployment.cfg |
| DLL error 193 | Architecture? | Use x64 DLL for x64 MT5 |
| DLL error 126 | Dependencies? | Add libsodium/MSVC runtime |
| Trade rejected | SL/TP valid? | Check geometry and stops level |
| Hedge blocked | Opposite position? | Close existing or use different symbol |

---

## 8. Change Management

### 8.1 Version Migration (v2.06 → v2.07)

```diff
+ Enhanced fire command format with entry=0 market execution
+ Real-time FILLED confirmation status
+ Improved error handling and status codes
+ Dynamic R:R adjustment system
+ Production-tested stability
+ Strict SL/TP enforcement with broker stops level
+ DEALER identity = UUID (strict routing)
+ Complete position lifecycle tracking
- Removed legacy static entry requirements
- Removed outdated confirmation formats
```

### 8.2 Backward Compatibility

- Ports 5556/5558 message formats unchanged
- Port 5560 is additive (new consumers only)
- Existing Core can ignore 5560 if not needed
- UUID routing is backward compatible

---

## 9. Compliance & Risk

### 9.1 Data Classification

| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Account ID | Operational | Log retention 90 days |
| Balances | Operational | Encrypted at rest |
| Positions | Operational | Real-time tracking |
| fire_id | Operational | ≤28 chars, no PII |

### 9.2 Risk Register

| ID | Risk | Impact | Mitigation |
|----|------|--------|------------|
| R-01 | DLL load failure | No automation | Pre-flight checks |
| R-02 | UUID collision | Misrouted commands | UUID uniqueness validation |
| R-03 | Tight broker stops | Trade rejections | Dynamic distance calculation |
| R-04 | Network partition | Data loss | Health monitors + restart |
| R-05 | Over-partial close | Position errors | Volume step validation |

### 9.3 Audit Requirements

- All commands logged with UUID + timestamp
- All confirmations tracked with success/failure
- Position lifecycle fully traceable
- 90-day hot storage, 1-year cold archive

---

## 10. Production Troubleshooting Guide (September 22, 2025)

### Auto-Fire Diagnosis Process

**Step 1: Check Signal Processing**
```bash
# Verify signals reaching webapp
tail -f /root/.pm2/logs/webapp-main-out.log | grep "AUTO fire check"
# Should show: "HIGH CONFIDENCE - checking AUTO fire users"

# Check confidence thresholds
# Expected: 80-89% = AUTO fire, 90%+ = Manual only
```

**Step 2: Check Command Router Flow**
```bash
# Verify commands reaching command router
tail -f /root/.pm2/logs/command-router-error.log
# Should show: "DEQ ELITE_RAPID_SYMBOL_ID | fire | SYMBOL"
# Should show: "→ COMMANDER_DEV_001 | FIRE_ID | fire | SYMBOL"
```

**Step 3: Check EA Response**
```bash
# Check for confirmations from EA
# If no confirmations = EA-side issue
# If confirmations with FAILED = broker/validation issue

# Check position tracking
sqlite3 /root/HydraX-v2/bitten.db "SELECT open_positions FROM ea_instances WHERE target_uuid='COMMANDER_DEV_001';"
```

### Current Production Issues

**Issue: Auto-Fire Commands Reaching EA but FAILING**
- **Symptoms**: Commands in router logs, FAILED status in database
- **Root Cause**: EA processing but broker rejecting
- **Evidence**: Manual fire works, auto-fire fails
- **Resolution**: Check EA logs, broker connection, margin requirements

**Issue: 90%+ Confidence Signals Not Auto-Firing**
- **Symptoms**: 91.9% XAUUSD signal not auto-fired
- **Root Cause**: Auto-fire threshold capped at 89%
- **By Design**: High confidence signals require manual decision
- **Resolution**: Adjust threshold or manual fire high-confidence signals

### Common Issues & Solutions

```bash
# Issue: Auto-fire not working
1. Check logs: webapp → command_router → EA response chain
2. Verify confidence in 80-89% range (not 90%+)
3. Check position slots: open_positions < 3
4. Verify user 7176191872 in AUTO mode

# Issue: Commands reach router but FAIL
1. Check EA connection and response
2. Verify broker margin requirements
3. Check market hours and symbol availability
4. Review SL/TP distance validation

# Issue: Manual fire works, auto-fire doesn't
1. Check auto-fire confidence range (80-89%)
2. Verify position slot availability
3. Check user auto-fire permissions
4. Review risk calculation differences

# Issue: Position tracking inaccurate
1. Check confirm_listener processing ZMQ 5558
2. Verify database updates from confirmations
3. Check HEARTBEAT_METRICS on port 5560
4. Validate position count in ea_instances table
```

### EA Connection Diagnostics

```bash
# Check EA heartbeat freshness
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances;"
# Should be < 120 seconds for active EA

# Test fire command manually
python3 /root/test_fire_command.py
# Verifies complete pipeline: signal → fire → EA → confirmation

# Check ZMQ port bindings
ss -tulpen | grep -E ":(5555|5556|5558|5560)"
# All ports should be bound and listening
```

---

## 11. Performance Benchmarks

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Handshake time | <1s | <3s | >5s |
| Ping roundtrip | <50ms | <250ms | >1s |
| Fire → Confirmation | <100ms | <500ms | >2s |
| Heartbeat interval | 30s | 30-40s | >60s |
| Metrics interval | 30s | 30-40s | >60s |
| Tick rate | Market dependent | 1-100/s | 0/s |

---

## 12. Integration Points

### Core System Integration

```python
# Command Router (port 5555)
- Receives fire commands from webapp/bot
- Routes by target_uuid to correct EA
- Must preserve field order for EA

# Telemetry Bridge (port 5556)
- Consumes handshake, heartbeat, ticks, OHLC
- Feeds Elite Guard pattern detection
- Archives for analysis

# Confirmation Listener (port 5558)
- Updates fires table with execution results
- Processes position_closed events
- Handles hybrid events for tracking

# Metrics Consumer (port 5560) - NEW
- Real-time position tracking
- Account snapshot every 30s
- Complete positions[] array
```

### Database Schema Updates

```sql
-- New fields for v2.07H tracking
ALTER TABLE fires ADD COLUMN hybrid_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE fires ADD COLUMN partial_closes TEXT; -- JSON array
ALTER TABLE fires ADD COLUMN trail_updates TEXT;  -- JSON array

-- New table for position snapshots
CREATE TABLE IF NOT EXISTS position_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    positions_json TEXT NOT NULL,
    equity REAL,
    margin_level REAL,
    INDEX idx_uuid_time (uuid, timestamp)
);
```

---

## Appendix A: File Locations

```
MQL5/
├── Experts/
│   └── BITTEN_Universal_EA_v2.078_PRODUCTION.mq5
├── Files/
│   └── bitten_deployment.cfg
└── Libraries/
    ├── libzmq.dll (x64)
    └── libsodium-26.dll (if required)

HydraX-v2/
├── BITTEN_Universal_EA_v2.078_PRODUCTION.mq5 (production EA)
├── EA_v2.07H_LAW_DOCUMENTATION.md (this file - updated for v2.078)
├── ARCHITECTURE.md (system architecture with v2.078 specifications)
├── command_router.py (handles v2.078 commands)
├── confirm_listener_v207.py (enhanced for signal snapshots)
├── zmq_telemetry_bridge_v207.py (with enhanced port 5560 processing)
└── webapp_server_optimized.py (position tracking with v2.078 integration)
```

---

## Appendix B: Quick Reference Card

```
Version: 2.078 (PRO STABLE QUIET)
Ports: 5555 (commands) | 5556 (telemetry) | 5558 (events+snapshots) | 5560 (metrics)
UUID: MQL5\Files\bitten_deployment.cfg → UUID=COMMANDER_DEV_001
Test: ping → pong | fire → confirmation+snapshot | close → close_confirmation
Hybrid: +8p → PARTIAL(25%) | +12p → PARTIAL(25%)+BE | Trail active
Events: confirmation | position_closed | hybrid_event | pong | signal_snapshot
Metrics: Enhanced HEARTBEAT_METRICS with complete positions[] every 30s
Snapshots: Configurable timeframe (M1/M5/M15/M30/H1) with OHLC bars + pattern overlays
Safety: Spread blocking | Hedge blocking | Volume normalization | Enhanced error handling
Config: InpVerboseLogging | InpSnapshotBars | InpSnapshotTF | InpTelemetryBeatSec
```

---

*End of LAW Documentation v2.078 - Updated September 23, 2025*