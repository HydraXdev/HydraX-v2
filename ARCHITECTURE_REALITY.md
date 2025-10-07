# ACTUAL SYSTEM ARCHITECTURE - October 1, 2025

## THE TRUTH ABOUT EA CONNECTIVITY

### EA Location & Connection

- **EA Location**: Remote server at 185.244.67.11
- **EA Connection Method**: Native TCP sockets (HydraSocket v1.0)
- **EA Does NOT connect to port 5555**: EA connects to ports 5559/6000 for events/metrics

### ACTUAL DATA FLOW (VERIFIED)

```
EA (185.244.67.11)
    │
    ├─> Port 5559 (Events) ──> hydrasocket_universal_bridge.py
    ├─> Port 6000 (Metrics) ──> hydrasocket_universal_bridge.py
    └─> Port 5555 (Commands) ──> ??? (EA expects TCP server here)

Universal Bridge:
    ├─> ZMQ PUSH → Port 5556 (zmq_telemetry_bridge)
    └─> Account state tracking

Telemetry Bridge (Port 5556):
    └─> ZMQ PUB → Port 5560 (Elite Guard subscribes)

Elite Guard:
    └─> SUB from Port 5560 → Pattern detection
```

### THE COMMAND PROBLEM

**Issue**: EA connects to port 5555 expecting a TCP server for commands
**Current State**: Port 5555 has ZMQ ROUTER (command_router) - incompatible with EA's native TCP

**Command Bridge Attempt**: Failed because:

1. Remote EA can't be redirected by local iptables
2. Command Bridge on port 5563 requires EA reconfiguration
3. EA is on remote server, not localhost

### WHAT'S ACTUALLY NEEDED

The EA needs `feed_set` command to initialize its watchlist. Since the EA connects to port 5555 expecting TCP, we have TWO options:

**Option 1**: Create a REAL TCP server on port 5555 that:

- Accepts native TCP connections from EA
- Translates to ZMQ for Brain communication
- **Problem**: Port 5555 already bound by ZMQ ROUTER

**Option 2**: Run TCP command server on different port (e.g., 5557) and:

- Update EA configuration to use new port
- **Problem**: Violates "don't change EA" requirement

**Option 3**: Send configure_feed command directly via Universal Bridge

- Use the existing TCP connection from EA
- Send command through the events port (5559)
- **Best option**: No port conflicts, no EA changes needed

## CURRENT STATUS

### What's Working ✅

- EA connected and sending account_summary, position_heartbeat
- Universal Bridge receiving and forwarding events
- Telemetry Bridge relaying to port 5560
- Elite Guard subscribed and waiting for market data

### What's NOT Working ❌

- EA watchlist not initialized (no market data being sent)
- feed_set command not reaching EA
- Command Bridge approach failed

### Next Steps

1. **IMMEDIATE**: Send configure_feed via Universal Bridge's existing EA connection
2. **THEN**: Verify market data starts flowing
3. **FINALLY**: Set up proper command routing for fire commands
