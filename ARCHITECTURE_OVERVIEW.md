# BITTEN ARCHITECTURE OVERVIEW
**Generated**: August 12, 2025 03:55 UTC  
**State**: Live System Documentation (No Additions)

## Runtime Data Flow

```
[Market Data EAs] --PUSH--> (CC PULL :5556) --> [zmq_telemetry_bridge] --PUB--> (:5560)
                                                                                    |
                                                                                    v
                                                                           [Elite Guard :5560 SUB]
                                                                                    |
                                                                                    v
                              [Elite Guard] --PUB--> (:5557) --> [relay_to_telegram SUB] --POST--> /api/signals (webapp :8888)
                                                                                                              |
                                                                                                              v
                                                                                                       [missions DB]
                                                                                                              |
                                                                                                              v
       Telegram HUD link --> /brief --> [personalized mission HUD] --POST--> /api/fire --> (PUSH ipc:///tmp/bitten_cmdqueue)
                                                                                                              |
                                                                                                              v
                                                                                       [command_router (ROUTER :5555)]
                                                                                                              |
                                                                                                              v
                                                                         [EA DEALER (UUID=COMMANDER_DEV_001)] --PUSH--> (:5558)
                                                                                                              |
                                                                                                              v
                                                                                        [confirm_listener] --> [fires DB] --> /me
```

## Ordered Trade Sequence (1-10)

1. **Market Data Ingestion**: EA sends tick data via PUSH to 134.199.204.67:5556
2. **Bridge Relay**: zmq_telemetry_bridge receives on :5556, publishes to :5560
3. **Signal Generation**: Elite Guard subscribes to :5560, generates SMC patterns
4. **Signal Broadcast**: Elite Guard publishes signal on :5557
5. **Telegram Alert**: relay_to_telegram subscribes to :5557, POSTs to /api/signals
6. **Mission Creation**: webapp creates mission in DB, sends Telegram alert with HUD link
7. **User Execution**: User clicks HUD link → /brief → sees mission → clicks Execute
8. **Fire Command**: webapp POSTs to /api/fire → enqueues to ipc:///tmp/bitten_cmdqueue
9. **EA Routing**: command_router pulls from queue, routes to EA via ROUTER :5555
10. **Confirmation**: EA executes trade, sends confirmation to :5558 → updates fires DB

## Component Cards

### 1. zmq_telemetry_bridge_debug.py
- **Path**: /root/HydraX-v2/zmq_telemetry_bridge_debug.py
- **PID**: 2411770 (background)
- **Purpose**: Receives market data from EAs, republishes for consumption
- **Binds**: tcp://*:5556 (PULL), tcp://*:5560 (PUB)
- **Connects**: None
- **Inputs**: Market tick data from EAs
- **Outputs**: Republished tick data
- **DB Tables**: None
- **Env Vars**: None required

### 2. elite_guard_with_citadel.py
- **Path**: /root/HydraX-v2/elite_guard_with_citadel.py
- **PM2 Name**: elite_guard
- **PID**: 3102500
- **Purpose**: Generates trading signals from SMC patterns
- **Binds**: tcp://*:5557 (PUB)
- **Connects**: tcp://localhost:5560 (SUB)
- **Inputs**: Market tick data from :5560
- **Outputs**: ELITE_GUARD_SIGNAL messages
- **DB Tables**: None directly
- **Env Vars**: None required

### 3. elite_guard_zmq_relay.py
- **Path**: /root/HydraX-v2/elite_guard_zmq_relay.py
- **PM2 Name**: relay_to_telegram
- **PID**: 3100355
- **Purpose**: Relays Elite Guard signals to webapp for Telegram alerts
- **Binds**: None
- **Connects**: tcp://localhost:5557 (SUB)
- **Inputs**: ELITE_GUARD_SIGNAL from :5557
- **Outputs**: HTTP POST to localhost:8888/api/signals
- **DB Tables**: None directly
- **Env Vars**: None required

### 4. webapp_server_optimized.py (via start_webapp_gunicorn.sh)
- **Path**: /root/HydraX-v2/webapp_server_optimized.py
- **PM2 Name**: webapp
- **PID**: 3125334
- **Purpose**: Web interface for HUD, mission management, trade execution
- **Binds**: 0.0.0.0:8888 (HTTP)
- **Connects**: ipc:///tmp/bitten_cmdqueue (PUSH)
- **Inputs**: HTTP requests, signal POSTs from relay
- **Outputs**: Mission creation, fire commands to queue
- **DB Tables**: missions (RW), fires (R), users (R), ea_instances (R)
- **Env Vars**: BITTEN_DB=/root/HydraX-v2/bitten.db

### 5. command_router.py
- **Path**: /root/HydraX-v2/command_router.py
- **PM2 Name**: command_router
- **PID**: 3125079
- **Purpose**: Routes fire commands from queue to specific EAs
- **Binds**: tcp://*:5555 (ROUTER), ipc:///tmp/bitten_cmdqueue (PULL)
- **Connects**: None
- **Inputs**: Fire commands from IPC queue, EA heartbeats
- **Outputs**: Fire commands to EA DEALERs
- **DB Tables**: None
- **Env Vars**: BITTEN_ROUTER_ADDR, BITTEN_QUEUE_ADDR, BITTEN_EA_TTL_SEC

### 6. confirm_listener.py
- **Path**: /root/HydraX-v2/confirm_listener.py
- **PM2 Name**: confirm_listener
- **PID**: 3126882
- **Purpose**: Receives trade confirmations from EAs
- **Binds**: tcp://*:5558 (PULL)
- **Connects**: None
- **Inputs**: Confirmation messages from EAs
- **Outputs**: Updates to fires table
- **DB Tables**: fires (W)
- **Env Vars**: BITTEN_DB, CONFIRM_BIND

### 7. signal_outcome_monitor.py
- **Path**: /root/HydraX-v2/signal_outcome_monitor.py
- **PM2 Name**: outcome_daemon
- **PID**: 3120143
- **Purpose**: Monitors signal outcomes by tracking price vs SL/TP
- **Binds**: None
- **Connects**: tcp://localhost:5560 (SUB)
- **Inputs**: Tick data from :5560, mission data from DB
- **Outputs**: Outcome updates to signal_outcomes.jsonl
- **DB Tables**: missions (R)
- **Env Vars**: None required

### 8. commander_throne.py
- **Path**: /root/HydraX-v2/commander_throne.py
- **PID**: 2454259 (background)
- **Purpose**: Analytics dashboard on port 8899
- **Binds**: 0.0.0.0:8899 (HTTP)
- **Connects**: None
- **Inputs**: Database queries
- **Outputs**: Analytics web interface
- **DB Tables**: missions (R), fires (R), signals (R)
- **Env Vars**: None required

## Message Contracts

### ELITE_GUARD_SIGNAL (ZMQ :5557)
```json
{
  "signal_id": "ELITE_GUARD_EURUSD_1754828514",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry_price": 1.095,
  "stop_pips": 10,
  "target_pips": 20,
  "confidence": 73.0,
  "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
  "signal_type": "PRECISION_STRIKE",
  "citadel_score": 7.5,
  "timestamp": 1754828514
}
```

### Mission Create Payload (POST /api/signals)
```json
{
  "signal_id": "ELITE_GUARD_EURUSD_1754828514",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry_price": 1.095,
  "stop_pips": 10,
  "target_pips": 20,
  "confidence": 73.0,
  "pattern_type": "LIQUIDITY_SWEEP_REVERSAL"
}
```

### Fire Command (IPC Queue → Router → EA)
```json
{
  "type": "fire",
  "fire_id": "fir_abc123",
  "target_uuid": "COMMANDER_DEV_001",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry": 1.095,
  "sl": 1.094,
  "tp": 1.097,
  "lot": 0.01
}
```

### EA Confirmation (EA PUSH → :5558)
```json
{
  "type": "confirmation",
  "fire_id": "fir_abc123",
  "target_uuid": "COMMANDER_DEV_001",
  "status": "FILLED",
  "ticket": 19059064,
  "price": 1.095,
  "symbol": "EURUSD"
}
```

## Allowed Components

### Allowed Processes (PM2)
- command_router
- confirm_listener
- elite_guard
- outcome_daemon
- relay_to_telegram
- webapp

### Allowed Background Processes
- zmq_telemetry_bridge_debug.py (PID 2411770)
- commander_throne.py (PID 2454259)

### Allowed Ports
- 5555: ROUTER (command_router binds)
- 5556: PULL (telemetry bridge binds)
- 5557: PUB (elite_guard binds)
- 5558: PULL (confirm_listener binds)
- 5560: PUB (telemetry bridge binds)
- 8888: HTTP (webapp binds)
- 8899: HTTP (commander_throne binds)

### Allowed IPC Sockets
- ipc:///tmp/bitten_cmdqueue (command_router binds PULL, webapp connects PUSH)

## Disallowed Components

### Disallowed Processes
- fire_router_service.py
- zmq_bitten_controller.py
- clone_farm (any variant)
- venom (any variant)
- duplicate outcome daemons
- duplicate zmq relays (except the PM2-managed one)
- bitten_production_bot.py (deprecated)

### Disallowed Paths
- /root/HydraX-v2/fire_router_service.py
- /root/HydraX-v2/zmq_bitten_controller.py
- /root/HydraX-v2/venom_*.py
- Any Docker/Wine related processes

## Immutable Files
- /root/HydraX-v2/bitten.db (schema only, data mutable)
- /root/HydraX-v2/command_router.py (critical SSOT)
- /root/HydraX-v2/confirm_listener.py (critical path)

## Runbook

### Start Order
1. zmq_telemetry_bridge_debug.py (if not running)
2. pm2 start elite_guard
3. pm2 start relay_to_telegram  
4. pm2 start webapp
5. pm2 start command_router
6. pm2 start confirm_listener
7. pm2 start outcome_daemon

### Stop Order (reverse)
1. pm2 stop outcome_daemon
2. pm2 stop confirm_listener
3. pm2 stop command_router
4. pm2 stop webapp
5. pm2 stop relay_to_telegram
6. pm2 stop elite_guard

### Quick Health Checks
```bash
# Check all PM2 processes
pm2 list

# Check port bindings
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"

# Check webapp health
curl -s http://localhost:8888/healthz

# Check EA heartbeats
pm2 logs command_router --lines 5 --nostream | grep HEARTBEAT

# Check signal flow
pm2 logs relay_to_telegram --lines 5 --nostream
```

### End-to-End Smoke Test
```bash
# 1. Verify telemetry bridge
ps aux | grep zmq_telemetry_bridge | grep -v grep

# 2. Check Elite Guard generating signals
pm2 logs elite_guard --lines 10 --nostream | grep "ELITE_GUARD"

# 3. Verify relay forwarding
pm2 logs relay_to_telegram --lines 5 --nostream

# 4. Test webapp endpoint
curl -s http://localhost:8888/api/missions | jq length

# 5. Send test fire command
python3 -c "import zmq; s=zmq.Context().socket(zmq.PUSH); s.connect('ipc:///tmp/bitten_cmdqueue'); s.send_json({'type':'fire','fire_id':'test','target_uuid':'COMMANDER_DEV_001','symbol':'EURUSD','direction':'BUY','entry':1.1,'sl':1.09,'tp':1.11,'lot':0.01})"

# 6. Check command routing
pm2 logs command_router --lines 3 --nostream | grep "CMD"

# 7. Verify confirmation listener
pm2 logs confirm_listener --lines 3 --nostream
```

## Unknown/Needs Decision
- bitten_production_bot.py: Shows in CLAUDE.md as PID 2588730 but not in current PM2 list
- Multiple zmq_relay processes (3099061, 3100355): Determine which is canonical
- Position tracker (PID 2409025 in CLAUDE.md): Not found in current processes
- Handshake processor (PID 2586467 in CLAUDE.md): Not found in current processes