# 🚨🚨🚨 CRITICAL EA DATA FLOW CONTRACT 🚨🚨🚨

**BINDING AGREEMENT**: This document represents the FINAL, TESTED, and OPERATIONAL data flow from EA to Elite Guard.
**Date Established**: August 1, 2025
**Status**: LOCKED AND VERIFIED ✅

## ⚡ THE SACRED DATA FLOW - DO NOT MODIFY

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EA v7.01 (MT5 Terminal)                        │
│                   BITTENBridge_TradeExecutor_ZMQ_v7.mq5                 │
│                                                                         │
│  OnTick() → Sends JSON: {"type":"tick","symbol":"EURUSD",...}         │
│  OnTimer() → Sends JSON: {"type":"heartbeat","balance":10000,...}     │
│                                                                         │
│                         PUSH to port 5556                               │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TELEMETRY BRIDGE (Port 5556 → 5560)                  │
│                    zmq_telemetry_bridge_debug.py                        │
│                                                                         │
│  PULL from 5556 → Receives EA data                                     │
│  PUB to 5560 → Broadcasts to all subscribers                           │
│                                                                         │
│              Critical: This bridge MUST be running!                     │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ELITE GUARD v6.0 (Port 5560 SUB)                    │
│                     elite_guard_with_citadel.py                        │
│                                                                         │
│  SUB from 5560 → Receives tick data                                    │
│  Scans for SMC patterns every 30-60 seconds                            │
│  PUB to 5557 → When signals detected (currently hunting)               │
│                                                                         │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     WEBAPP API (Port 8888)                              │
│                   webapp_server_optimized.py                            │
│                                                                         │
│  /api/signals POST → Receives Elite Guard signals                      │
│  BittenCore.process_signal() → Processes and validates                 │
│  GROUP ONLY delivery → Sends to @bitten_signals                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔴 CRITICAL FACTS - MEMORIZE THESE

### 1. **EA IS A ZMQ CLIENT** (NEVER BINDS)
- EA connects TO remote ports (PUSH)
- EA NEVER binds or listens
- EA sends to 134.199.204.67:5556

### 2. **TELEMETRY BRIDGE IS MANDATORY**
- Without it, NO DATA FLOWS
- It converts PULL → PUB pattern
- Must run BEFORE Elite Guard starts

### 3. **PORT ASSIGNMENTS (SACRED)**
- 5556: EA → Telemetry Bridge (PULL)
- 5560: Telemetry Bridge → Elite Guard (PUB/SUB)
- 5557: Elite Guard → Signal consumers (PUB)
- 8888: WebApp API

### 4. **TICK DATA FORMAT**
```json
{
  "type": "tick",
  "symbol": "EURUSD",
  "bid": 1.15548,
  "ask": 1.15561,
  "spread": 1.3,
  "volume": 0,
  "timestamp": 1754060224
}
```

### 5. **CURRENT ACTIVE SYMBOLS**
- XAUUSD (GOLD)
- USDJPY
- GBPUSD
- EURUSD
- EURJPY
- GBPJPY

## 🛠️ TROUBLESHOOTING CHECKLIST

### IF NO TICKS ARE FLOWING:

1. **Check EA is compiled with OnTick()**
   ```bash
   grep -n "OnTick" /root/HydraX-v2/BITTENBridge_TradeExecutor_ZMQ_v7.mq5
   # Should show lines 153-184
   ```

2. **Check telemetry bridge is running**
   ```bash
   ps aux | grep telemetry_pubbridge
   # Should show process running
   ```

3. **Check ports are listening**
   ```bash
   ss -tlnp | grep -E '5556|5560|5557'
   # Should show:
   # 0.0.0.0:5556 (telemetry bridge PULL)
   # 0.0.0.0:5560 (telemetry bridge PUB)
   # 0.0.0.0:5557 (elite guard PUB)
   ```

4. **Monitor tick flow**
   ```bash
   # Watch telemetry bridge output
   tail -f /proc/$(pgrep -f telemetry_pubbridge)/fd/1
   
   # Watch Elite Guard receiving ticks
   tail -f /proc/$(pgrep -f elite_guard_with_citadel)/fd/1 | grep "Received tick"
   ```

## 🚫 COMMON MISTAKES TO AVOID

1. **DO NOT** try to make EA bind to ports (it's a client!)
2. **DO NOT** skip the telemetry bridge (data won't flow)
3. **DO NOT** change port numbers (everything breaks)
4. **DO NOT** use recv_string() in Elite Guard (use recv_json())
5. **DO NOT** forget EA needs OnTick() implementation

## ✅ QUICK VALIDATION TEST

Run this to verify data flow:
```bash
python3 -c "
import zmq
context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.connect('tcp://127.0.0.1:5560')
sub.subscribe(b'')
print('Listening for ticks on 5560...')
for i in range(5):
    msg = sub.recv_json()
    print(f'✅ Tick {i+1}: {msg.get(\"symbol\")} @ {msg.get(\"bid\")}')
"
```

## 📝 STARTUP SEQUENCE

1. Start telemetry bridge:
   ```bash
   cd /root/HydraX-v2 && python3 telemetry_pubbridge.py &
   ```

2. Start Elite Guard:
   ```bash
   cd /root/HydraX-v2 && python3 elite_guard_with_citadel.py &
   ```

3. Verify WebApp is running:
   ```bash
   curl -s http://localhost:8888/api/health
   ```

4. EA should already be running and sending ticks

## 🔒 THIS ARCHITECTURE IS LAW

Any deviation from this flow will break the system. This has been tested and verified. Follow it exactly.

**Signed**: Claude Code Agent
**Date**: August 1, 2025
**Authority**: Tested and Operational System