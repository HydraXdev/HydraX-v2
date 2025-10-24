# Firebase Projector Integration Guide

**Purpose**: Mirror Postgres trading truth to Firestore for PWA realtime UX
**Architecture**: CQRS read-model projection (event-driven)
**Status**: Production-ready, no mock data

---

## 🎯 Architecture Overview - CORRECTED

```
┌──────────────────────────────────────────────────────────────────────┐
│ PWA CLIENT (React/Next.js)                                           │
│                                                                       │
│ - Auth: Firebase Auth                                                │
│ - Reads: Firestore onSnapshot (realtime read-model)                  │
│ - Writes: HTTP POST to API Server (NOT Firestore)                    │
│                                                                       │
│     User clicks "Execute Trade"                                      │
│              ↓                                                        │
│     POST /api/v1/fires {uid, execId, signalId}                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ API SERVER (Source of Truth - Python/Node)                           │
│                                                                       │
│ Postgres: orders, fills, P&L, positions, audit                       │
│                                                                       │
│ POST /api/v1/fires Handler:                                          │
│   1. Load exec request from Postgres                                 │
│   2. Load signal from Postgres                                       │
│   3. ✅ FirebaseEnforcer.validate_and_enforce(exec_id, uid)           │
│      - Validates against /controls/{uid} in Firestore                │
│      - Checks slots, cooldown, caps, risk limits                     │
│      - Calculates server-enforced lot size                           │
│   4. If allowed: Execute via ZMQ to EA                               │
│   5. Emit domain events to Redis Pub/Sub                             │
│                                                                       │
│ Domain Events → Redis Pub/Sub → Firebase Projector                   │
└───────────────────────────────┬───────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FIREBASE PROJECTOR (Read-Model Sync - Service Account Only)          │
│                                                                       │
│ Consumes events, projects to Firestore:                              │
│ - /signals/{id} (read-only for clients)                              │
│ - /exec/{uid}/{execId} (read-only for clients)                       │
│ - /trades/{uid}/active/{tradeId} (read-only for clients)             │
│ - /controls/{uid} (service-only write, enforced in security rules)   │
│ - /presence/{uuid} (service-only write)                              │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FIRESTORE (Eventually Consistent Read-Models - CLIENT READ-ONLY)     │
│                                                                       │
│ PWA subscribes with onSnapshot() for realtime UX                     │
│ Security Rules: Clients CANNOT write to /controls, /exec, /signals   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**CRITICAL CORRECTIONS**:
1. ✅ PWA writes go to **HTTP API**, not Firestore
2. ✅ FirebaseEnforcer runs **server-side in API handler**, not client-side
3. ✅ Firestore is **read-model only** for PWA, written only by projector service
4. ✅ Controls in Firestore are **service-only write**, enforced by security rules

---

## 📦 What Was Delivered

### 1. Firebase Projector (`firebase_projector.py`)
**Location**: `/root/HydraX-v2/src/bitten_core/firebase_projector.py`

**Features**:
- ✅ Idempotent event processing (prevents duplicates)
- ✅ Dead-letter queue for failed projections
- ✅ Redis pub/sub consumption
- ✅ Direct function call API (in-process)
- ✅ 8 event handlers (signals, exec states, trades, presence)
- ✅ Graceful error handling with retry

**Event Handlers**:
```python
project_signal_generated()    # Elite Guard → /signals/{id}
project_exec_created()         # User execute → /exec/{uid}/{execId}
project_exec_validated()       # Enforcement → state + enforced/rejection
project_exec_sent()            # ZMQ send → state: SENT
project_exec_filled()          # EA confirm → state: FILLED + /trades
project_trade_updated()        # Tick stream → current price + P&L
project_trade_closed()         # TP/SL hit → archive to /closed
project_ea_presence()          # Heartbeat → /presence/{uuid}
```

### 2. Service Runner (`run_firebase_projector.py`)
**Location**: `/root/HydraX-v2/run_firebase_projector.py`

**Features**:
- ✅ Firebase Admin SDK initialization
- ✅ Redis pub/sub subscription
- ✅ Graceful shutdown (SIGINT/SIGTERM)
- ✅ Logging to file + stdout

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install firebase-admin redis
```

### 2. Set Environment Variables

```bash
# Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/root/bitten-firebase-sa.json"

# Redis (optional, for pub/sub)
export REDIS_URL="redis://localhost:6379/0"
```

### 3. Start Projector Service

```bash
cd /root/HydraX-v2
python run_firebase_projector.py
```

**With PM2**:
```bash
pm2 start run_firebase_projector.py --name firebase_projector --interpreter python3
pm2 save
```

---

## 🔌 Integration Methods

### Method 1: Redis Pub/Sub (Recommended)

**When to use**: Production, multiple services, async event processing

**How it works**:
1. Trading core publishes events to Redis channels
2. Projector subscribes and processes events
3. Decoupled, scalable, reliable

**Example - Elite Guard emits signal**:

```python
# In elite_guard_with_citadel.py (your existing signal generator)
import redis
import json
from uuid import uuid4
from datetime import datetime

redis_client = redis.from_url('redis://localhost:6379/0')

def emit_signal_generated(signal_data):
    """Emit signal generated event to Redis"""
    event = {
        'event_id': str(uuid4()),
        'event_type': 'SIGNAL_GENERATED',
        'timestamp': datetime.utcnow().isoformat(),
        'signal': {
            'signal_id': signal_data['signal_id'],
            'pattern_type': signal_data['pattern_type'],
            'pair': signal_data['pair'],
            'confidence': signal_data['confidence'],
            'entry_price': signal_data['entry'],
            'tp_price': signal_data['tp'],
            'sl_price': signal_data['sl'],
            'tp_pips': signal_data['tp_pips'],
            'sl_pips': signal_data['sl_pips'],
            'rr_ratio': signal_data['rr_ratio'],
            'timeframe': signal_data['timeframe'],
            'session': signal_data['session'],
            'expires_at': signal_data['expires_at'].isoformat(),
            'created_by': 'ELITE_GUARD',
        }
    }

    redis_client.publish('bitten:signals', json.dumps(event))
```

**Add this after signal creation**:
```python
# In elite_guard_with_citadel.py, after creating signal
signal = {...}  # Your existing signal dict

# Emit to Redis for projection
emit_signal_generated(signal)
```

---

### Method 2: Direct Function Calls (In-Process)

**When to use**: Same process, synchronous, simpler setup

**How it works**:
1. Import projector in your code
2. Call projection methods directly
3. No Redis needed

**Example - Execution handler emits events**:

```python
# In execution_handler.py (your existing exec processor)
from firebase_admin import firestore
from src.bitten_core.firebase_projector import FirebaseProjector
from uuid import uuid4
from datetime import datetime

# Initialize once
db = firestore.client()
projector = FirebaseProjector(db)

async def process_execution(uid, exec_id, signal_id):
    """Your existing execution logic"""

    # 1. User created execution
    await projector.project_exec_created({
        'event_id': str(uuid4()),
        'event_type': 'EXEC_CREATED',
        'timestamp': datetime.utcnow(),
        'exec': {
            'exec_id': exec_id,
            'uid': uid,
            'signal_id': signal_id,
            'requested': {...},  # User's requested values
            'created_at': datetime.utcnow(),
        }
    })

    # 2. Validate with enforcer
    result = await enforcer.validate_and_enforce(exec_id, uid)

    await projector.project_exec_validated({
        'event_id': str(uuid4()),
        'event_type': 'EXEC_VALIDATED',
        'timestamp': datetime.utcnow(),
        'exec_id': exec_id,
        'uid': uid,
        'allowed': result['allowed'],
        'enforced': result.get('enforced'),
        'rejection': result.get('rejection'),
    })

    if not result['allowed']:
        return

    # 3. Send to EA
    await send_to_ea_via_zmq(result['enforced'])

    await projector.project_exec_sent({
        'event_id': str(uuid4()),
        'event_type': 'EXEC_SENT',
        'timestamp': datetime.utcnow(),
        'exec_id': exec_id,
        'uid': uid,
        'target_uuid': get_user_ea_uuid(uid),
        'sent_at': datetime.utcnow(),
    })

    # 4. Wait for EA confirmation...
    # (handled in confirm_listener)
```

---

### Method 3: Postgres NOTIFY/LISTEN (Alternative)

**When to use**: No Redis, want event sourcing from Postgres

**How it works**:
1. Postgres triggers emit NOTIFY on INSERT/UPDATE
2. Projector listens to notifications
3. Processes events from Postgres

**Example Postgres Trigger**:

```sql
CREATE OR REPLACE FUNCTION notify_signal_generated()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'bitten_signals',
        json_build_object(
            'event_id', gen_random_uuid()::text,
            'event_type', 'SIGNAL_GENERATED',
            'timestamp', now(),
            'signal', row_to_json(NEW)
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER signal_generated_trigger
AFTER INSERT ON signals
FOR EACH ROW
EXECUTE FUNCTION notify_signal_generated();
```

**Projector listens**:
```python
import psycopg2
import select

conn = psycopg2.connect("dbname=bitten")
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()
cursor.execute("LISTEN bitten_signals;")

while True:
    if select.select([conn], [], [], 5) == ([], [], []):
        continue
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        event = json.loads(notify.payload)
        await projector.route_event(event)
```

---

## 📝 Event Schema Reference

### SIGNAL_GENERATED
```python
{
    'event_id': str,              # UUID, idempotency key
    'event_type': 'SIGNAL_GENERATED',
    'timestamp': datetime,
    'signal': {
        'signal_id': str,
        'pattern_type': str,      # 'LIQUIDITY_SWEEP_REVERSAL', etc.
        'pair': str,              # 'EURUSD'
        'confidence': float,      # 0-100
        'entry_price': float,
        'tp_price': float,
        'sl_price': float,
        'tp_pips': int,
        'sl_pips': int,
        'rr_ratio': float,
        'timeframe': str,         # 'M15'
        'session': str,           # 'LONDON', 'NY', etc.
        'expires_at': datetime,
        'created_by': str,        # 'ELITE_GUARD'
    }
}
```

### EXEC_CREATED
```python
{
    'event_id': str,
    'event_type': 'EXEC_CREATED',
    'timestamp': datetime,
    'exec': {
        'exec_id': str,
        'uid': str,
        'signal_id': str,
        'requested': {
            'riskPct': float,
            'previewLot': float,
            'pair': str,
            'direction': str,
            'entry': float,
            'sl': float,
            'tp': float,
        },
        'created_at': datetime,
    }
}
```

### EXEC_VALIDATED
```python
{
    'event_id': str,
    'event_type': 'EXEC_VALIDATED',
    'timestamp': datetime,
    'exec_id': str,
    'uid': str,
    'allowed': bool,

    # If allowed:
    'enforced': {
        'riskPct': float,
        'lot': float,
        'risk': float,
        'caps': {...},
        'pair': str,
        'direction': str,
        'entry': float,
        'sl': float,
        'tp': float,
    },

    # If rejected:
    'rejection': {
        'reason': str,
        'message': str,
    }
}
```

### EXEC_SENT
```python
{
    'event_id': str,
    'event_type': 'EXEC_SENT',
    'timestamp': datetime,
    'exec_id': str,
    'uid': str,
    'target_uuid': str,
    'sent_at': datetime,
}
```

### EXEC_FILLED
```python
{
    'event_id': str,
    'event_type': 'EXEC_FILLED',
    'timestamp': datetime,
    'exec_id': str,
    'uid': str,
    'ticket': int,              # MT5 order ticket
    'fill_price': float,
    'fill_time': datetime,
    'slippage': float,
}
```

### TRADE_UPDATED
```python
{
    'event_id': str,
    'event_type': 'TRADE_UPDATED',
    'timestamp': datetime,
    'uid': str,
    'ticket': int,
    'current_price': float,
    'equity': float,            # Current P&L
    'pips': float,              # Pips gained/lost
}
```

### TRADE_CLOSED
```python
{
    'event_id': str,
    'event_type': 'TRADE_CLOSED',
    'timestamp': datetime,
    'uid': str,
    'ticket': int,
    'close_price': float,
    'close_time': datetime,
    'final_pl': float,
    'reason': str,              # 'TP' | 'SL' | 'MANUAL'
}
```

### EA_PRESENCE
```python
{
    'event_id': str,
    'event_type': 'EA_PRESENCE',
    'timestamp': datetime,
    'uuid': str,                # EA UUID
    'status': str,              # 'ONLINE' | 'OFFLINE'
    'last_seen': datetime,
    'balance': float,
    'equity': float,
}
```

---

## 🔍 Where to Add Event Emissions

### 1. Elite Guard (Signal Generation)

**File**: `/root/HydraX-v2/elite_guard_with_citadel.py`

**Location**: After creating signal dict (before publishing to ZMQ)

```python
# Existing code:
signal = {
    'signal_id': f"ELITE_GUARD_{pair}_{int(time.time())}",
    'pattern_type': 'LIQUIDITY_SWEEP_REVERSAL',
    # ... other fields
}

# ADD: Emit to Redis
emit_signal_generated(signal)

# Existing ZMQ publish:
self.publisher.send_string(f"ELITE_GUARD_SIGNAL {json.dumps(signal)}")
```

### 2. Execution Handler

**File**: `/root/HydraX-v2/execution_handler.py` (or wherever you process /exec requests)

**Add after each state transition**:
- User creates → `emit_exec_created`
- Validation → `emit_exec_validated`
- ZMQ send → `emit_exec_sent`

### 3. Confirmation Listener

**File**: `/root/HydraX-v2/confirm_listener.py`

**Location**: After receiving EA confirmation (port 5558)

```python
# Existing code:
confirmation = receive_from_ea()
ticket = confirmation['ticket']
fill_price = confirmation['price']

# ADD: Emit to Redis
emit_exec_filled({
    'exec_id': confirmation['fire_id'],
    'uid': get_uid_for_ticket(ticket),
    'ticket': ticket,
    'fill_price': fill_price,
    'fill_time': datetime.utcnow(),
    'slippage': calculate_slippage(...),
})
```

### 4. Tick Stream (Trade Updates)

**File**: `/root/HydraX-v2/zmq_telemetry_bridge_debug.py`

**Location**: When processing tick updates for active positions

```python
# When tick updates active trade
for trade in active_trades:
    new_price = get_current_price(trade.pair)
    new_pl = calculate_pl(trade, new_price)

    # ADD: Emit trade update
    emit_trade_updated({
        'uid': trade.uid,
        'ticket': trade.ticket,
        'current_price': new_price,
        'equity': new_pl,
        'pips': calculate_pips(trade, new_price),
    })
```

### 5. EA Heartbeat

**File**: `/root/HydraX-v2/command_router.py` (where EA heartbeats are received)

**Location**: After processing heartbeat

```python
# Existing heartbeat processing:
ea_uuid = heartbeat['uuid']
balance = heartbeat['balance']
equity = heartbeat['equity']

# ADD: Emit presence
emit_ea_presence({
    'uuid': ea_uuid,
    'status': 'ONLINE',
    'last_seen': datetime.utcnow(),
    'balance': balance,
    'equity': equity,
})
```

---

## 🛡️ Error Handling & Reliability

### Idempotency

**Problem**: Same event processed twice
**Solution**: Every event has `event_id` (UUID), projector checks cache

```python
# Projector automatically handles this
if event_id in self.processed_events:
    return False  # Skip duplicate
```

### Dead-Letter Queue

**Problem**: Projection fails (network, Firebase error)
**Solution**: Event saved to DLQ for manual retry

```python
# Access dead letters
dead_letters = projector.get_dead_letters()

# Retry manually
for dl in dead_letters:
    await projector.route_event(dl['event'])

# Clear after successful retry
projector.clear_dead_letters()
```

### Reconciliation

**Problem**: Events missed, Firestore out of sync
**Solution**: Nightly reconciliation compares Postgres to Firestore

```python
# Run nightly
await projector.reconcile_nightly()

# Compares:
# - Signal counts
# - Exec state distributions
# - Active trade counts
# - Alerts on discrepancies
```

---

## 📊 Monitoring

### Key Metrics

**Event Processing**:
```python
# Events processed per second
# Events in dead-letter queue
# Idempotency cache hit rate
# Average projection latency
```

**Firestore Operations**:
```python
# Writes per minute
# Read queries from PWA
# Document counts by collection
# Cost estimation
```

### Logging

**Projector logs to**:
- `/root/HydraX-v2/logs/firebase_projector.log`
- stdout (for PM2/systemd)

**Log levels**:
```python
INFO  - Normal operation
WARN  - Duplicate events, missing data
ERROR - Projection failures, Firebase errors
```

---

## ✅ Testing

### Unit Test Individual Projections

```python
from src.bitten_core.firebase_projector import FirebaseProjector

projector = FirebaseProjector(firestore_client)

# Test signal projection
event = {
    'event_id': 'test-123',
    'event_type': 'SIGNAL_GENERATED',
    'timestamp': datetime.utcnow(),
    'signal': {...}
}

success = await projector.project_signal_generated(event)
assert success

# Verify in Firestore
signal_doc = db.collection('signals').document('test-signal-id').get()
assert signal_doc.exists
```

### Integration Test Full Flow

```python
# 1. Emit event
redis_client.publish('bitten:signals', json.dumps(event))

# 2. Wait for projection
await asyncio.sleep(1)

# 3. Verify in Firestore
signal_doc = db.collection('signals').document(signal_id).get()
assert signal_doc.exists
```

---

## 🚀 Production Deployment

### PM2 Configuration

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'firebase-projector',
    script: '/root/HydraX-v2/run_firebase_projector.py',
    interpreter: 'python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      GOOGLE_APPLICATION_CREDENTIALS: '/root/bitten-firebase-sa.json',
      REDIS_URL: 'redis://localhost:6379/0'
    }
  }]
}
```

### Systemd Service

```ini
# /etc/systemd/system/firebase-projector.service
[Unit]
Description=BITTEN Firebase Projector
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment="GOOGLE_APPLICATION_CREDENTIALS=/root/bitten-firebase-sa.json"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/usr/bin/python3 /root/HydraX-v2/run_firebase_projector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📝 Summary

**What This Gives You**:
- ✅ Postgres remains source of truth (orders, fills, audit)
- ✅ Firestore mirrors for PWA realtime UX (onSnapshot)
- ✅ Decoupled: Firebase outage doesn't stop trading
- ✅ Scalable: Add more projectors if needed
- ✅ Auditable: Full event log + idempotency
- ✅ Reliable: Dead-letter queue + nightly reconciliation

**Next Steps**:
1. Start projector service
2. Add event emissions to existing code
3. Update PWA to subscribe to Firestore
4. Monitor logs and dead-letter queue
5. Run nightly reconciliation

---

**NO MOCK DATA - Production-ready CQRS projection system** 🚀
