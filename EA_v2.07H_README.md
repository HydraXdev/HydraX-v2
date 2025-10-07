# BITTEN Universal EA v2.07H (FLAT) - Complete Integration Guide

**Version**: 2.07H FLAT JSON
**Release Date**: September 19, 2025
**Status**: PRODUCTION READY
**Architecture**: 4-Socket ZMQ (5555/5556/5558/5560)

---

## 🚀 Quick Start

### Prerequisites

- MetaTrader 5 (x64)
- Windows 10/11 or Windows Server
- libzmq.dll (x64) - [Download](https://github.com/zeromq/libzmq/releases)
- BITTEN Core running on 134.199.204.67

### Installation (5 minutes)

1. **Install Dependencies**

   ```
   Copy to MQL5\Libraries\:
   - libzmq.dll (x64)
   - libsodium-26.dll (if required)
   ```

2. **Configure UUID**
   Create `MQL5\Files\bitten_deployment.cfg`:

   ```
   UUID=COMMANDER_DEV_001
   ```

3. **Compile EA**
   - Open MetaEditor
   - File → Open → `BITTEN_Universal_EA_v2.07H_flat.mq5`
   - Compile (F7)

4. **Attach to Chart**
   - Open any chart in MT5
   - Enable: Tools → Options → Expert Advisors → Allow DLL imports
   - Drag EA to chart
   - Click OK

5. **Verify Connection**
   - Check EA comment shows: "BITTEN v2.07H (FLAT)"
   - Verify Core logs show handshake received

---

## 📊 What's New in v2.07H

### Major Enhancements

| Feature                    | Description                               | Impact                  |
| -------------------------- | ----------------------------------------- | ----------------------- |
| **Metrics Channel (5560)** | Dedicated position tracking stream        | Complete visibility     |
| **Flat JSON Parser**       | No external dependencies                  | Improved reliability    |
| **SL/TP Enforcement**      | Broker stops level validation             | Fewer rejections        |
| **Hedge Prevention**       | Blocks opposite positions                 | Risk control            |
| **Enhanced Hybrid Events** | PARTIAL_CLOSE, SL_BREAKEVEN, TRAIL_UPDATE | Full lifecycle tracking |
| **UUID Identity**          | DEALER socket identity routing            | Secure multi-EA support |

### Breaking Changes

- Port 5560 now required for metrics
- UUID configuration mandatory
- SL/TP both required on all trades

---

## 🔌 4-Socket Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BITTEN CORE (134.199.204.67)            │
├─────────────────────────────────────────────────────────────┤
│  Port 5555 (DEALER) ← Commands (fire, close, ping)          │
│  Port 5556 (PUSH)   → Market Data (ticks, OHLC, heartbeat)  │
│  Port 5558 (PUSH)   → Trade Events (confirmations, closes)  │
│  Port 5560 (PUSH)   → Metrics (positions, account snapshot) │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      MT5 EA (Your Terminal)                  │
├─────────────────────────────────────────────────────────────┤
│  DEALER connects → 5555 (receives commands)                  │
│  PUSH connects   → 5556 (sends market data)                  │
│  PUSH connects   → 5558 (sends trade events)                 │
│  PUSH connects   → 5560 (sends position metrics)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📨 Message Reference

### Commands (You Send → EA)

#### Open Position (fire)

```json
{
  "type": "fire",
  "target_uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "symbol": "XAUUSD",
  "direction": "BUY",
  "sl": 2425.1,
  "tp": 2437.6,
  "lot": 0.1,
  "hybrid_enabled": true,
  "hybrid_p1_trigger": 8.0,
  "hybrid_p1_percent": 25.0,
  "hybrid_p2_trigger": 12.0,
  "hybrid_p2_percent": 25.0,
  "hybrid_trail_distance": 10.0
}
```

#### Close Position

```json
{
  "type": "close_ticket",
  "target_uuid": "COMMANDER_DEV_001",
  "ticket": 12345678
}
```

#### Health Check

```json
{
  "type": "ping",
  "target_uuid": "COMMANDER_DEV_001",
  "ping_id": "health_check_123"
}
```

### Events (EA Sends → You)

#### Trade Confirmation (Port 5558)

```json
{
  "type": "confirmation",
  "command_type": "fire",
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "status": "success",
  "ticket": 12345678,
  "price": 2429.5,
  "lot": 0.1,
  "message": "Trade executed via DEALER"
}
```

#### Position Metrics (Port 5560) - Every 30s

```json
{
  "type": "HEARTBEAT_METRICS",
  "target_uuid": "COMMANDER_DEV_001",
  "balance": 10012.4,
  "equity": 10018.1,
  "margin_level": 498.0,
  "open_positions": 2,
  "positions": [
    {
      "ticket": 12345678,
      "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
      "symbol": "XAUUSD",
      "direction": "BUY",
      "open_price": 2429.5,
      "current_price": 2430.2,
      "volume": 0.1,
      "pnl": 7.0
    }
  ]
}
```

#### Hybrid Position Events (Port 5558)

```json
{
  "type": "hybrid_event",
  "event": "PARTIAL_CLOSE",
  "ticket": 12345678,
  "fire_id": "ELITE_RAPID_XAUUSD_1758296000",
  "volume": 0.03,
  "pips": 8.5
}
```

---

## 🔧 Configuration

### UUID Setup

The EA identifies itself via UUID for command routing:

1. **Development Account (843859)**
   - Automatically uses: `COMMANDER_DEV_001`
   - No configuration needed

2. **Production Accounts**
   - Create `MQL5\Files\bitten_deployment.cfg`
   - Add: `UUID=YOUR-UNIQUE-UUID-HERE`
   - Must match Core's user mapping

### Network Requirements

| Port | Direction | Protocol | Purpose            |
| ---- | --------- | -------- | ------------------ |
| 5555 | Outbound  | TCP      | Command reception  |
| 5556 | Outbound  | TCP      | Market data stream |
| 5558 | Outbound  | TCP      | Trade events       |
| 5560 | Outbound  | TCP      | Position metrics   |

### Firewall Configuration

```powershell
# Windows Firewall (PowerShell as Admin)
New-NetFirewallRule -DisplayName "BITTEN EA Outbound" `
  -Direction Outbound -Protocol TCP `
  -RemotePort 5555,5556,5558,5560 `
  -RemoteAddress 134.199.204.67 `
  -Action Allow
```

---

## 🎯 Hybrid Position Management

### How It Works

The EA implements sophisticated position management:

1. **Entry** → Full position opened
2. **+8 pips** → Close 25%, move SL to breakeven
3. **+12 pips** → Close another 25%, activate trailing
4. **Trailing** → 10-pip trailing stop on remaining 50%

### Configuration

Enable in fire command:

```json
{
  "hybrid_enabled": true,
  "hybrid_p1_trigger": 8.0, // First partial at +8 pips
  "hybrid_p1_percent": 25.0, // Close 25%
  "hybrid_p2_trigger": 12.0, // Second partial at +12 pips
  "hybrid_p2_percent": 25.0, // Close another 25%
  "hybrid_trail_distance": 10.0 // Trail remaining by 10 pips
}
```

### Events Generated

- `PARTIAL_CLOSE` - When partial executed
- `SL_BREAKEVEN` - When SL moved to entry
- `TRAIL_UPDATE` - When trailing stop adjusted

---

## 🛡️ Safety Features

### 1. SL/TP Validation

All trades validated for:

- Correct geometry (BUY: sl<price<tp, SELL: tp<price<sl)
- Minimum distance from market (broker stops level)
- Both SL and TP required

### 2. Hedge Prevention

EA prevents opposite positions on same symbol:

- If BUY open on XAUUSD, SELL blocked
- Returns: `HEDGE_BLOCKED` error
- Applies only to BITTEN positions (magic number)

### 3. UUID Routing

Commands only processed if:

- `target_uuid` matches EA's configured UUID
- Wrong UUID = silent drop (no confirmation)
- Prevents cross-contamination in multi-EA setups

### 4. Volume Normalization

All volumes adjusted to broker requirements:

- Aligned to SYMBOL_VOLUME_STEP
- Respects SYMBOL_VOLUME_MIN
- Partial closes safely calculated

---

## 📈 Monitoring & Metrics

### Real-Time Metrics (Port 5560)

Every 30 seconds, receive complete account snapshot:

```python
# Python consumer example
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://134.199.204.67:5560")
socket.setsockopt_string(zmq.SUBSCRIBE, "")

while True:
    message = socket.recv_string()
    data = json.loads(message)
    if data["type"] == "HEARTBEAT_METRICS":
        print(f"Equity: ${data['equity']}")
        print(f"Positions: {data['open_positions']}")
        for pos in data["positions"]:
            print(f"  {pos['symbol']}: {pos['pnl']}")
```

### Health Indicators

| Metric            | Healthy | Warning    | Critical |
| ----------------- | ------- | ---------- | -------- |
| Heartbeat Age     | <40s    | 40-60s     | >60s     |
| Ping Response     | <250ms  | 250-1000ms | >1000ms  |
| Confirmation Rate | >95%    | 90-95%     | <90%     |
| Margin Level      | >200%   | 150-200%   | <150%    |

---

## 🔍 Troubleshooting

### Common Issues

#### EA Won't Start

**Symptom**: Error 193 or 126 on attach
**Solution**:

```
1. Verify libzmq.dll is x64 (not x32)
2. Check dependencies: dumpbin /dependents libzmq.dll
3. Install Visual C++ Redistributable 2015-2022
4. Place ALL DLLs in MQL5\Libraries\
```

#### No Connection to Core

**Symptom**: No handshake in logs
**Solution**:

```
1. Test connectivity: telnet 134.199.204.67 5556
2. Check Windows Firewall outbound rules
3. Verify Core is running and binding ports
4. Check UUID configuration matches
```

#### Commands Ignored

**Symptom**: Send fire but no confirmation
**Solution**:

```
1. Verify target_uuid in command matches EA UUID
2. Check EA comment shows correct UUID
3. Test with ping command first
4. Monitor EA Experts tab for errors
```

#### Trade Rejected

**Symptom**: confirmation with status:"failed"
**Solution**:

```
1. Check SL/TP geometry (BUY: sl<price<tp)
2. Increase distance from market price
3. Verify symbol is in Market Watch
4. Check account has sufficient margin
5. Look for HEDGE_BLOCKED message
```

### Debug Checklist

```bash
☐ MT5 Allow DLL imports enabled?
☐ MT5 Allow automated trading enabled?
☐ libzmq.dll in MQL5\Libraries\?
☐ bitten_deployment.cfg has UUID?
☐ Core shows handshake received?
☐ Heartbeats arriving every 30s?
☐ Ping → Pong working?
☐ Fire → Confirmation working?
```

---

## 🧪 Testing

### Basic Connectivity Test

```python
# test_ea_connection.py
import zmq
import json
import time

# Setup
context = zmq.Context()
cmd = context.socket(zmq.DEALER)
cmd.setsockopt_string(zmq.IDENTITY, "TEST_CLIENT")
cmd.connect("tcp://134.199.204.67:5555")

events = context.socket(zmq.SUB)
events.connect("tcp://134.199.204.67:5558")
events.setsockopt_string(zmq.SUBSCRIBE, "")

# Send ping
ping = {
    "type": "ping",
    "target_uuid": "COMMANDER_DEV_001",
    "ping_id": f"test_{int(time.time())}"
}
cmd.send_json(ping)

# Wait for pong
poller = zmq.Poller()
poller.register(events, zmq.POLLIN)
if poller.poll(1000):
    response = events.recv_string()
    print(f"Received: {response}")
else:
    print("No response - check connection")
```

### Trade Execution Test

```python
# test_trade.py
# Send test trade
fire = {
    "type": "fire",
    "target_uuid": "COMMANDER_DEV_001",
    "fire_id": f"TEST_{int(time.time())}",
    "symbol": "EURUSD",
    "direction": "BUY",
    "sl": 1.0900,
    "tp": 1.1100,
    "lot": 0.01
}
cmd.send_json(fire)

# Check confirmation
if poller.poll(2000):
    confirm = json.loads(events.recv_string())
    if confirm["status"] == "success":
        print(f"Trade opened: Ticket {confirm['ticket']}")
    else:
        print(f"Trade failed: {confirm['message']}")
```

---

## 📊 Performance Specifications

### Latency Targets

| Operation              | Target | Maximum |
| ---------------------- | ------ | ------- |
| Command → Confirmation | <100ms | 500ms   |
| Tick → Publication     | <10ms  | 50ms    |
| Heartbeat Interval     | 30s    | 40s     |
| Metrics Update         | 30s    | 40s     |

### Throughput Capacity

| Stream        | Rate        | Notes            |
| ------------- | ----------- | ---------------- |
| Ticks         | 100-500/min | Market dependent |
| Commands      | 10/sec      | Rate limited     |
| Confirmations | 10/sec      | Matches commands |
| Metrics       | 2/min       | Fixed interval   |

### Resource Usage

- **Memory**: ~50-100 MB
- **CPU**: <5% average, 10% peaks
- **Network**: ~10 KB/s continuous
- **Disk**: Minimal (config + logs)

---

## 🔐 Security Considerations

### Transport Security

- ZMQ TCP within VPN recommended
- No built-in encryption (use VPN/tunnel)
- Identity-based routing via UUID

### Access Control

- UUID must match for command processing
- No commands accepted from wrong UUID
- Each EA has unique UUID

### Risk Controls

- Mandatory SL/TP on all positions
- Hedge prevention logic
- Position size validation
- Symbol availability checks

---

## 📚 Additional Resources

### Core Integration Files

Update these Core files for v2.07H:

```python
# command_router.py - No changes needed
# Already handles DEALER pattern correctly

# confirm_listener.py - Add new event types
HYBRID_EVENTS = ["PARTIAL_CLOSE", "SL_BREAKEVEN", "TRAIL_UPDATE"]

# telemetry_bridge.py - Add port 5560 binding
metrics_socket = context.socket(zmq.PULL)
metrics_socket.bind("tcp://*:5560")

# webapp_server.py - Consume metrics stream
def process_metrics(data):
    if data["type"] == "HEARTBEAT_METRICS":
        update_positions(data["positions"])
        update_account(data["balance"], data["equity"])
```

### Database Schema

```sql
-- Track hybrid events
CREATE TABLE hybrid_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket INTEGER NOT NULL,
    fire_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    volume REAL,
    pips REAL,
    timestamp INTEGER NOT NULL,
    uuid TEXT NOT NULL
);

-- Store position snapshots
CREATE TABLE position_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    positions_json TEXT NOT NULL,
    balance REAL,
    equity REAL,
    margin_level REAL
);
```

---

## 🚦 Production Checklist

### Pre-Production

```bash
☐ Test on demo account first
☐ Verify all 4 sockets connected
☐ Test fire → confirmation → metrics flow
☐ Test hybrid events generation
☐ Verify position tracking accuracy
☐ Test close commands
☐ Test error scenarios (wrong UUID, bad SL/TP)
```

### Go-Live

```bash
☐ Set production UUID in config
☐ Start with minimum lots (0.01)
☐ Monitor first few trades closely
☐ Verify confirmations arriving
☐ Check metrics updating
☐ Monitor margin level
☐ Set up alerts for socket health
```

### Post-Production

```bash
☐ Monitor 24h for stability
☐ Check log rotation working
☐ Verify no memory leaks
☐ Review trade execution times
☐ Analyze rejection reasons
☐ Optimize based on metrics
```

---

## 📞 Support

### Quick Diagnostics

```python
# diagnose.py - Run this to check EA health
import zmq
import json
import time

def check_ea_health(uuid):
    context = zmq.Context()

    # Check telemetry
    telemetry = context.socket(zmq.SUB)
    telemetry.connect("tcp://134.199.204.67:5556")
    telemetry.setsockopt_string(zmq.SUBSCRIBE, "")
    telemetry.setsockopt(zmq.RCVTIMEO, 5000)

    try:
        msg = telemetry.recv_string()
        data = json.loads(msg)
        print(f"✅ Telemetry active: {data['type']}")
    except:
        print("❌ No telemetry data")

    # Check metrics
    metrics = context.socket(zmq.SUB)
    metrics.connect("tcp://134.199.204.67:5560")
    metrics.setsockopt_string(zmq.SUBSCRIBE, "")
    metrics.setsockopt(zmq.RCVTIMEO, 35000)

    try:
        msg = metrics.recv_string()
        data = json.loads(msg)
        if data["type"] == "HEARTBEAT_METRICS":
            print(f"✅ Metrics active: {data['open_positions']} positions")
    except:
        print("❌ No metrics data")

    # Ping test
    cmd = context.socket(zmq.DEALER)
    cmd.setsockopt_string(zmq.IDENTITY, "DIAG")
    cmd.connect("tcp://134.199.204.67:5555")

    events = context.socket(zmq.SUB)
    events.connect("tcp://134.199.204.67:5558")
    events.setsockopt_string(zmq.SUBSCRIBE, "")
    events.setsockopt(zmq.RCVTIMEO, 1000)

    ping = {
        "type": "ping",
        "target_uuid": uuid,
        "ping_id": f"diag_{int(time.time())}"
    }
    cmd.send_json(ping)

    try:
        pong = events.recv_string()
        print(f"✅ Ping/Pong working")
    except:
        print("❌ No pong response")

check_ea_health("COMMANDER_DEV_001")
```

### Common Error Codes

| Code                 | Meaning                    | Solution               |
| -------------------- | -------------------------- | ---------------------- |
| HEDGE_BLOCKED        | Opposite position exists   | Close existing first   |
| Symbol not available | Symbol not in Market Watch | Add to Market Watch    |
| REJECTED: SL/TP      | Invalid price levels       | Check geometry         |
| No quotes            | Market closed              | Wait for market open   |
| DLL disabled         | DLL imports not allowed    | Enable in MT5 settings |

---

## 📝 Version History

### v2.07H (September 19, 2025)

- Added dedicated metrics channel (port 5560)
- Implemented flat JSON parser
- Added SL/TP enforcement
- Added hedge prevention
- Enhanced hybrid events
- UUID-based routing

### v2.06H (September 1, 2025)

- Basic hybrid support
- Initial DEALER implementation

### v2.05 (August 26, 2025)

- ZMQ integration
- Multi-symbol support

---

_End of README - BITTEN Universal EA v2.07H_
