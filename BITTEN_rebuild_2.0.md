# BITTEN v2.0 REBUILD PLAN

**Created**: October 8, 2025
**Status**: Planning Phase
**Goal**: Eliminate 70% bloat, consolidate systems, improve performance
**Firebase Integration**: Use Firebase/Firestore as primary data layer

---

## 🎯 EXECUTIVE SUMMARY

BITTEN works but is drowning in bloat:
- **1,035 Python files** → Target: 300 files (71% reduction)
- **15 PM2 processes** → Target: 5 processes (67% reduction)
- **2.7GB disk usage** → Target: <1GB
- **Multiple broken systems** (Redis buffer, logger deadlocks, duplicate trackers)

**Firebase Changes Everything**: With Firebase/Firestore now available, we can:
- Replace SQLite + JSONL files with Firestore
- Use Firebase Auth instead of custom JWT
- Real-time updates via Firebase SDK (not custom WebSocket)
- Cloud Functions for background jobs (not separate processes)
- Automatic scaling and backups

**Timeline**: 12 weeks (3 months) with Firebase advantage
**Risk Level**: Medium (Firebase simplifies many hard parts)

---

## 🚀 THE FIREBASE ADVANTAGE

### What Firebase Solves Immediately

**1. Database Chaos → Firestore**
- **Current**: SQLite file, 35+ tables, JSONL tracking files, user_registry.json
- **Firebase**: Single Firestore database with collections
- **Benefit**: Real-time sync, automatic scaling, no migration scripts

**2. Authentication Mess → Firebase Auth**
- **Current**: Custom JWT, API keys, session management scattered
- **Firebase**: Built-in auth with Telegram provider
- **Benefit**: Secure, tested, no custom code needed

**3. Process Sprawl → Cloud Functions**
- **Current**: 15 PM2 processes, manual restarts, unclear dependencies
- **Firebase**: Serverless functions triggered by Firestore events
- **Benefit**: Auto-scaling, no process management, pay-per-use

**4. Real-time Updates → Firebase SDK**
- **Current**: Custom WebSocket with Flask-SocketIO, backpressure handling
- **Firebase**: Native real-time listeners in client
- **Benefit**: Battle-tested, offline support, automatic reconnection

**5. File Storage → Cloud Storage**
- **Current**: Local files, no backup strategy
- **Firebase**: Cloud Storage with CDN
- **Benefit**: Automatic backups, versioning, global distribution

---

## 📊 PRIORITIZED IMPLEMENTATION PLAN (BANG FOR BUCK)

### Priority Framework
1. **Quick Wins**: High impact, low effort (do first)
2. **Critical Fixes**: Must-have for stability
3. **Performance**: Speed improvements
4. **Technical Debt**: Long-term maintainability

---

## PHASE 0: PREPARATION (Week 1)
**Goal**: Set up Firebase, establish baseline, create safety nets

### Week 1 Tasks

**Day 1-2: Firebase Project Setup**
- [ ] Create Firebase project (bitten-production)
- [ ] Enable Firestore database (production mode)
- [ ] Enable Firebase Authentication
- [ ] Enable Cloud Functions
- [ ] Enable Cloud Storage
- [ ] Download service account key
- [ ] Test connection from server

**Day 3-4: Baseline Measurements**
- [ ] Document current system metrics:
  - Total files: `find . -name "*.py" | wc -l`
  - Total processes: `pm2 list`
  - Disk usage: `du -sh .`
  - Memory usage: `free -h`
  - Signal generation rate (24h sample)
  - Fire command latency (P95)
- [ ] Create complete backup:
  - Database: `cp bitten.db bitten_v1_backup.db`
  - Code: `tar -czf bitten_v1_backup.tar.gz .`
  - Configs: `cp -r config config_v1_backup`

**Day 5: Safety Infrastructure**
- [ ] Create `/root/HydraX-v2/DELETED_FILES/` directory for moved files
- [ ] Create rollback script (`rollback_to_v1.sh`)
- [ ] Test rollback procedure (practice restore)
- [ ] Set up separate Git branch: `git checkout -b v2.0-rebuild`

**Day 6-7: Documentation Audit**
- [ ] Read all critical docs (CLAUDE.md, ARCHITECTURE.md, SESSION_START.md)
- [ ] List all active processes and their purposes
- [ ] Map current data flow (signals → fires → confirmations)
- [ ] Identify Firebase integration points

**Deliverables**:
- ✅ Firebase project ready
- ✅ Complete baseline metrics documented
- ✅ Full system backup verified
- ✅ Rollback procedure tested

---

## PHASE 1: QUICK WINS (Weeks 2-3)
**Goal**: Eliminate obvious bloat, immediate impact, low risk

### Priority 1.1: Delete Abandoned Files (Week 2, Days 1-3)
**Impact**: HIGH | **Effort**: LOW | **Risk**: VERY LOW

**What to Delete** (700+ files):

**Category A: Version Files** (~200 files)
```bash
# Files ending in _v1, _v2, _v3, _old, _backup
elite_guard_v1.py
elite_guard_v2.py
webapp_old.py
fire_router_backup.py
```
**Action**: Move to DELETED_FILES/, verify system still works

**Category B: Test/Debug Scripts** (~150 files)
```bash
# One-off diagnostic scripts
test_fire_queue.py
debug_ea_connection.py
smoke_test_*.py
```
**Action**: Keep legitimate tests, delete one-offs

**Category C: Duplicate Functionality** (~100 files)
```bash
# Multiple implementations of same thing
REAL_signal_tracker.py       # Delete
comprehensive_signal_tracker.py  # Delete
simple_truth_tracker.py      # Delete
# Keep: definitive_signal_tracker.py
```
**Action**: Verify which one is actually running, delete others

**Category D: Unused Features** (~150 files)
```bash
# Features not in production
crypto_*.py                  # Not trading crypto
war_room_ultimate.py         # Redundant UI
normans_notebook.py          # Experiment
```
**Action**: Confirm not used, move to archive

**Category E: Deprecated Systems** (~100 files)
```bash
# Docker/Wine containers (using ForexVPS now)
mt5-*/
docker-compose.yml
# Redis buffer system (killed Oct 7, 2025)
signals_zmq_to_redis.py
signals_redis_to_webapp_fixed.py
```
**Action**: Delete entirely (documented as deprecated)

**Safety Protocol**:
1. Don't delete, MOVE to DELETED_FILES/
2. Test system after each category
3. If broken, move back immediately
4. Wait 24 hours before permanent deletion

**Expected Result**: 1,035 → ~350 files (66% reduction)

---

### Priority 1.2: Kill Dangerous Processes (Week 2, Days 4-5)
**Impact**: HIGH | **Effort**: VERY LOW | **Risk**: LOW

**Processes to Permanently Stop**:

```bash
# Already killed (Oct 7) but verify they stay dead
pm2 delete signals_zmq_to_redis        # Caused 20-hour signal delays
pm2 delete signals_redis_to_webapp     # Replayed stale signals

# Redundant processes (functionality absorbed elsewhere)
pm2 delete ml_autofire_optimizer       # Not actually used
pm2 delete enhanced_slot_manager       # Logic in webapp already

# Dangerous/broken
pm2 delete grokkeeper_ml               # ML training not needed live
```

**Actions**:
1. Stop processes
2. Monitor for 48 hours (ensure no breakage)
3. Delete files if all clear
4. Document why they were removed

**Expected Result**: 15 → 11 processes

---

### Priority 1.3: Consolidate Tracking Files (Week 2, Days 6-7)
**Impact**: HIGH | **Effort**: LOW | **Risk**: LOW

**Current Chaos**:
```
comprehensive_tracking.jsonl  (326 signals - claimed active)
truth_log.jsonl              (stopped Aug 22 - outdated)
signal_tracking.jsonl        (claimed "THE ONLY ONE")
optimized_tracking.jsonl     (status unknown)
```

**Firebase Solution**:
```
Firestore Collection: /signals/{signal_id}
{
  signal_id: "ELITE_GUARD_EURUSD_123",
  symbol: "EURUSD",
  direction: "BUY",
  pattern_type: "VCB_BREAKOUT",
  confidence: 85.5,
  outcome: "WIN",  // or "LOSS", "PENDING"
  pips_result: 15.2,
  created_at: Timestamp,
  completed_at: Timestamp,
  duration_seconds: 3600
}
```

**Migration Steps**:
1. Parse ALL jsonl files into single dataset
2. Deduplicate by signal_id (keep most recent)
3. Upload to Firestore `/signals` collection
4. Verify data integrity (row counts match)
5. Update tracker to write to Firestore only
6. Delete all jsonl files after 7 days confirmation

**Benefits**:
- Single source of truth
- Real-time queries (no file parsing)
- Automatic backups
- No file corruption issues

**Expected Result**: 4 tracking files → 1 Firestore collection

---

### Priority 1.4: Firebase Auth Integration (Week 3, Days 1-3)
**Impact**: MEDIUM | **Effort**: LOW | **Risk**: LOW

**Current Mess**:
- user_registry.json file
- Custom JWT tokens
- API key management scattered
- Session tracking unclear

**Firebase Solution**:
```
Firebase Auth + Custom Claims
User authenticated via Telegram
Custom claims store: {tier, fire_mode, risk_percent}
```

**Implementation**:
1. Enable Firebase Auth with custom auth provider
2. Create cloud function to sync Telegram users:
   ```javascript
   // Triggered when user first authenticates
   exports.onUserCreate = functions.auth.user().onCreate(async (user) => {
     // Set default custom claims
     await admin.auth().setCustomUserClaims(user.uid, {
       tier: 'NIBBLER',
       fire_mode: 'MANUAL',
       risk_percent: 2.0
     });

     // Create Firestore user document
     await admin.firestore().collection('users').doc(user.uid).set({
       telegram_id: user.providerData[0].uid,
       created_at: admin.firestore.FieldValue.serverTimestamp(),
       tier: 'NIBBLER'
     });
   });
   ```
3. Update webapp to verify Firebase tokens
4. Migrate existing users from user_registry.json
5. Delete user_registry.json after confirmation

**Benefits**:
- No custom JWT code
- Built-in security
- Easy tier management (custom claims)
- Automatic session handling

**Expected Result**: user_registry.json → Firebase Auth (delete 1 file, remove 500+ lines of auth code)

---

### Priority 1.5: Move User Data to Firestore (Week 3, Days 4-7)
**Impact**: MEDIUM | **Effort**: MEDIUM | **Risk**: MEDIUM

**Current**:
- user_registry.json
- fire_mode.db (SQLite)
- EA mapping in bitten.db

**Firebase Collections**:
```
/users/{user_id}
{
  telegram_id: 7176191872,
  tier: "COMMANDER",
  fire_mode: "FULL_AUTO",
  risk_percent: 2.0,
  max_concurrent_positions: 7,
  created_at: Timestamp,
  updated_at: Timestamp
}

/ea_instances/{uuid}
{
  uuid: "COMMANDER_DEV_001",
  user_id: "user_abc123",
  account_id: "843859",
  broker: "XM",
  last_heartbeat: Timestamp,
  balance: 8000.50,
  equity: 8100.25,
  status: "connected"
}

/user_stats/{user_id}
{
  total_fires: 150,
  wins: 95,
  losses: 45,
  pending: 10,
  total_pips: 1250.5,
  xp: 5000
}
```

**Migration Script**:
```python
# migrate_to_firestore.py
import json
import sqlite3
import firebase_admin
from firebase_admin import firestore

# Initialize Firebase
cred = firebase_admin.credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Migrate users from JSON
with open('user_registry.json') as f:
    users = json.load(f)
    for user_id, user_data in users.items():
        db.collection('users').document(user_id).set(user_data)

# Migrate EA instances from SQLite
conn = sqlite3.connect('bitten.db')
cursor = conn.execute("SELECT * FROM ea_instances")
for row in cursor:
    db.collection('ea_instances').document(row['uuid']).set({
        'user_id': row['user_id'],
        'account_id': row['account_login'],
        # ... map all fields
    })
```

**Testing**:
1. Run migration to Firebase
2. Run BOTH systems in parallel (SQLite + Firebase)
3. Verify data consistency for 48 hours
4. Switch to Firebase-only
5. Delete SQLite files after 7 days

**Expected Result**: 3 data sources → 3 Firestore collections

---

## PHASE 2: PROCESS CONSOLIDATION (Weeks 4-6)
**Goal**: 15 processes → 5 processes using Firebase

### Priority 2.1: Firebase-First Architecture Design (Week 4, Days 1-2)
**Impact**: HIGH | **Effort**: LOW | **Risk**: NONE (planning)

**New Architecture**:
```
┌─────────────────────────────────────────────────────┐
│                   MT5 EA (v3.005)                   │
│                                                     │
└───────────────┬─────────────────────────────────────┘
                │ ZMQ DEALER (unchanged)
                ▼
┌─────────────────────────────────────────────────────┐
│            ZMQ Gateway (Python Process)             │
│  - Ports 5555/5556/5558                             │
│  - Writes to Firestore on every message            │
│  - Publishes to Redis Pub/Sub for real-time        │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│                  FIRESTORE DATABASE                 │
│  Collections: signals, fires, positions, users      │
└───────────────┬─────────────────────────────────────┘
                │
                ├──────────────────┬──────────────────┐
                ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐
│ Cloud Functions  │  │  Flask WebApp    │  │ Telegram Bot   │
│ (Background)     │  │  (API + UI)      │  │ (User Commands)│
│                  │  │                  │  │                │
│ - Analytics      │  │ - REST API       │  │ - /fire        │
│ - Outcome track  │  │ - War Room UI    │  │ - /brief       │
│ - Pattern perf   │  │ - Admin dash     │  │ - /status      │
└──────────────────┘  └──────────────────┘  └────────────────┘
```

**5 Core Processes**:
1. **zmq_gateway**: ZMQ ↔ Firestore bridge
2. **signal_engine**: Elite Guard pattern detection
3. **webapp**: Flask API + UI (reads from Firestore)
4. **telegram_bot**: User commands (reads from Firestore)
5. **Firebase Cloud Functions**: Background jobs (auto-deploy)

**What Disappears**:
- ❌ command_router (absorbed by zmq_gateway)
- ❌ confirm_listener (absorbed by zmq_gateway)
- ❌ analytics_api (becomes Cloud Function)
- ❌ analytics_events (becomes Cloud Function)
- ❌ real_signal_tracker (becomes Cloud Function)
- ❌ athena_broadcaster (absorbed by telegram_bot)
- ❌ dashboard_v2 (absorbed by webapp)

---

### Priority 2.2: Create ZMQ Gateway (Week 4, Days 3-7)
**Impact**: HIGH | **Effort**: MEDIUM | **Risk**: MEDIUM

**Purpose**: Single process handles ALL ZMQ communication

**File**: `/root/HydraX-v2/src/gateway/zmq_gateway_firebase.py`

**Pseudo-code**:
```python
class ZMQGatewayFirebase:
    """
    Unified ZMQ handler that writes everything to Firestore
    """

    def __init__(self):
        # ZMQ sockets
        self.command_router = zmq.ROUTER(bind='tcp://*:5555')
        self.data_receiver = zmq.PULL(bind='tcp://*:5556')
        self.confirm_receiver = zmq.PULL(bind='tcp://*:5558')

        # Firebase
        self.db = firestore.client()

        # Redis for real-time pub/sub
        self.redis = redis.Redis()

    def run(self):
        """Main event loop"""
        poller = zmq.Poller()
        poller.register(self.command_router, zmq.POLLIN)
        poller.register(self.data_receiver, zmq.POLLIN)
        poller.register(self.confirm_receiver, zmq.POLLIN)

        while True:
            socks = dict(poller.poll(timeout=1000))

            if self.command_router in socks:
                self.handle_fire_command()

            if self.data_receiver in socks:
                self.handle_market_data()

            if self.confirm_receiver in socks:
                self.handle_confirmation()

    def handle_fire_command(self):
        """Receive fire command from webapp, send to EA"""
        # 1. Receive from webapp
        identity, empty, payload = self.command_router.recv_multipart()
        command = json.loads(payload)

        # 2. Write to Firestore (pending)
        fire_ref = self.db.collection('fires').document(command['fire_id'])
        fire_ref.set({
            'status': 'PENDING',
            'user_id': command['user_id'],
            'signal_id': command['signal_id'],
            'created_at': firestore.SERVER_TIMESTAMP
        })

        # 3. Forward to EA
        self.command_router.send_multipart([identity, b'', payload])

        # 4. Update status
        fire_ref.update({'status': 'SENT'})

    def handle_confirmation(self):
        """EA sent confirmation, update Firestore"""
        confirmation = self.confirm_receiver.recv_json()

        # Update fire record
        fire_ref = self.db.collection('fires').document(confirmation['fire_id'])
        fire_ref.update({
            'status': 'FILLED',
            'ticket': confirmation['ticket'],
            'fill_price': confirmation['price'],
            'filled_at': firestore.SERVER_TIMESTAMP
        })

        # Publish to Redis for real-time updates
        self.redis.publish('fires.confirmed', json.dumps(confirmation))
```

**Testing Plan**:
1. Run alongside existing command_router + confirm_listener
2. Compare outputs (should be identical)
3. Verify Firestore writes
4. Switch traffic to new gateway
5. Monitor for 48 hours
6. Delete old processes if stable

---

### Priority 2.3: Refactor Elite Guard (Week 5)
**Impact**: MEDIUM | **Effort**: HIGH | **Risk**: HIGH

**Goal**: Break 292KB file into modules, write signals to Firestore

**Current**: elite_guard_with_citadel.py (4,000+ lines)

**New Structure**:
```
src/signal_engine/
├── elite_guard.py              # Main orchestrator (200 lines)
├── patterns/
│   ├── liquidity_sweep.py      # 150 lines
│   ├── order_block.py          # 150 lines
│   ├── fair_value_gap.py       # 150 lines
│   ├── vcb_breakout.py         # 150 lines
│   ├── sweep_return.py         # 150 lines
│   └── momentum_burst.py       # 150 lines
├── scoring/
│   ├── ml_filter.py            # XGBoost scoring
│   └── citadel_shield.py       # Consensus scoring
└── publishers/
    ├── firestore_publisher.py  # Write to Firestore
    └── zmq_publisher.py        # Publish to ZMQ (legacy)
```

**Refactoring Strategy**:
1. **Week 5, Day 1-2**: Extract patterns (copy-paste to new files)
2. **Week 5, Day 3-4**: Add Firestore publisher
3. **Week 5, Day 5**: Test each pattern in isolation
4. **Week 5, Day 6-7**: Integration testing, parallel run

**Pattern Example**:
```python
# src/signal_engine/patterns/vcb_breakout.py
class VCBBreakout:
    """Volatility Compression Breakout detector"""

    def detect(self, candles: List[Candle]) -> Optional[Signal]:
        # 1. Calculate ATR
        atr = self.calculate_atr(candles)

        # 2. Check for compression (ATR < 70% of avg)
        if atr > self.avg_atr * 0.7:
            return None  # Not compressed

        # 3. Check for breakout
        latest = candles[-1]
        if latest.range < atr * 1.5:
            return None  # No breakout

        # 4. Confirm with volume
        if latest.volume < self.avg_volume * 1.5:
            return None  # Weak volume

        # 5. Generate signal
        return Signal(
            pattern_type="VCB_BREAKOUT",
            symbol=candles[0].symbol,
            direction="BUY" if latest.close > latest.open else "SELL",
            confidence=self.calculate_confidence(),
            entry_price=latest.close,
            sl_price=self.calculate_sl(latest),
            tp_price=self.calculate_tp(latest)
        )
```

**Benefits**:
- Each pattern testable independently
- Easy to add new patterns
- Easy to disable broken patterns
- Clear ownership (one pattern per file)

**Risk Mitigation**:
- Keep old elite_guard.py running in parallel
- Compare signal outputs (should match)
- Gradual cutover (1 pattern at a time)

---

### Priority 2.4: Create Cloud Functions (Week 6)
**Impact**: MEDIUM | **Effort**: MEDIUM | **Risk**: LOW

**Purpose**: Replace background processes with serverless functions

**Functions to Create**:

**1. Signal Outcome Tracker**
```javascript
// functions/trackSignalOutcome.js
// Triggered: Every 1 minute (Cloud Scheduler)
exports.trackSignalOutcomes = functions.pubsub
  .schedule('every 1 minutes')
  .onRun(async (context) => {
    const db = admin.firestore();

    // Get pending signals
    const pendingSignals = await db.collection('signals')
      .where('outcome', '==', 'PENDING')
      .get();

    for (const signal of pendingSignals.docs) {
      const data = signal.data();

      // Check if TP or SL hit (compare with market data)
      const outcome = await checkOutcome(data);

      if (outcome) {
        await signal.ref.update({
          outcome: outcome.result,  // "WIN" or "LOSS"
          pips_result: outcome.pips,
          completed_at: admin.firestore.FieldValue.serverTimestamp()
        });
      }
    }
  });
```

**2. Pattern Performance Aggregator**
```javascript
// functions/aggregatePerformance.js
// Triggered: Every 5 minutes
exports.aggregatePerformance = functions.pubsub
  .schedule('every 5 minutes')
  .onRun(async (context) => {
    const db = admin.firestore();

    // Calculate win rates by pattern
    const signals = await db.collection('signals')
      .where('outcome', 'in', ['WIN', 'LOSS'])
      .get();

    const stats = {};
    signals.forEach(doc => {
      const data = doc.data();
      if (!stats[data.pattern_type]) {
        stats[data.pattern_type] = {wins: 0, losses: 0};
      }
      if (data.outcome === 'WIN') stats[data.pattern_type].wins++;
      else stats[data.pattern_type].losses++;
    });

    // Write aggregated stats
    for (const [pattern, counts] of Object.entries(stats)) {
      await db.collection('pattern_performance').doc(pattern).set({
        pattern_type: pattern,
        total_signals: counts.wins + counts.losses,
        wins: counts.wins,
        losses: counts.losses,
        win_rate: counts.wins / (counts.wins + counts.losses),
        updated_at: admin.firestore.FieldValue.serverTimestamp()
      });
    }
  });
```

**3. Telegram Alert Sender**
```javascript
// functions/sendTelegramAlert.js
// Triggered: When new signal created in Firestore
exports.onSignalCreated = functions.firestore
  .document('signals/{signalId}')
  .onCreate(async (snap, context) => {
    const signal = snap.data();

    // Get all users who should receive alert
    const users = await admin.firestore()
      .collection('users')
      .where('telegram_notifications', '==', true)
      .get();

    const telegram = require('node-telegram-bot-api');
    const bot = new telegram(functions.config().telegram.token);

    for (const user of users.docs) {
      const userData = user.data();

      // Check if user has access to this pattern
      if (canAccessPattern(userData.tier, signal.pattern_type)) {
        await bot.sendMessage(userData.telegram_id,
          formatSignalMessage(signal)
        );
      }
    }
  });
```

**Deployment**:
```bash
cd functions/
npm install
firebase deploy --only functions
```

**Benefits**:
- Auto-scaling (Firebase handles it)
- No process management (PM2)
- Pay only for executions
- Automatic retries on failure

**What This Replaces**:
- ❌ analytics_api (becomes HTTP function)
- ❌ analytics_events (becomes scheduled function)
- ❌ real_signal_tracker (becomes scheduled function)
- ❌ athena_broadcaster (becomes Firestore trigger)

**Expected Result**: 11 processes → 7 processes

---

## PHASE 3: DATABASE CONSOLIDATION (Weeks 7-8)
**Goal**: Everything in Firestore, delete SQLite/JSONL

### Priority 3.1: Signal Data Migration (Week 7, Days 1-3)
**Impact**: HIGH | **Effort**: MEDIUM | **Risk**: MEDIUM

**Current State**:
- comprehensive_tracking.jsonl (326 signals)
- bitten.db signals table
- Multiple outcome files

**Migration Script**:
```python
# scripts/migrate_signals_to_firestore.py

import json
import sqlite3
import firebase_admin
from firebase_admin import firestore, credentials

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# 1. Parse JSONL files
signals_data = {}

# Read comprehensive_tracking.jsonl
with open('comprehensive_tracking.jsonl') as f:
    for line in f:
        signal = json.loads(line)
        signal_id = signal['signal_id']

        # Deduplicate (keep most complete record)
        if signal_id not in signals_data or signal.get('outcome'):
            signals_data[signal_id] = signal

# 2. Read SQLite signals table
conn = sqlite3.connect('bitten.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT * FROM signals")

for row in cursor:
    signal_id = row['signal_id']

    # Merge with JSONL data
    if signal_id not in signals_data:
        signals_data[signal_id] = dict(row)
    else:
        # JSONL has priority, but fill missing fields from DB
        for key in row.keys():
            if key not in signals_data[signal_id]:
                signals_data[signal_id][key] = row[key]

# 3. Upload to Firestore
batch = db.batch()
count = 0

for signal_id, signal_data in signals_data.items():
    # Convert timestamp fields
    if 'created_at' in signal_data:
        signal_data['created_at'] = firestore.SERVER_TIMESTAMP

    ref = db.collection('signals').document(signal_id)
    batch.set(ref, signal_data)

    count += 1
    if count % 500 == 0:
        batch.commit()
        batch = db.batch()
        print(f"Migrated {count} signals...")

batch.commit()
print(f"Total signals migrated: {count}")

# 4. Verify
firestore_count = len(db.collection('signals').get())
print(f"Firestore count: {firestore_count}")
print(f"Expected count: {len(signals_data)}")
assert firestore_count == len(signals_data), "Count mismatch!"
```

**Testing**:
1. Run migration script
2. Verify counts match
3. Spot-check random signals (data integrity)
4. Run queries on Firestore (performance test)
5. Keep old files for 7 days (rollback safety)

---

### Priority 3.2: Fire Execution Migration (Week 7, Days 4-7)
**Impact**: HIGH | **Effort**: MEDIUM | **Risk**: HIGH

**Current**: fires table in bitten.db

**Firestore Collection**:
```
/fires/{fire_id}
{
  fire_id: "ELITE_GUARD_EURUSD_123",
  user_id: "user_abc",
  signal_id: "ELITE_GUARD_EURUSD_123",
  status: "FILLED",  // PENDING/SENT/FILLED/FAILED
  ticket: 12345678,
  fill_price: 1.0950,
  lot_size: 0.10,
  created_at: Timestamp,
  filled_at: Timestamp
}

/positions/{ticket}  (for open trades only)
{
  ticket: 12345678,
  fire_id: "ELITE_GUARD_EURUSD_123",
  user_id: "user_abc",
  symbol: "EURUSD",
  direction: "BUY",
  open_price: 1.0950,
  current_price: 1.0980,
  sl: 1.0920,
  tp: 1.1000,
  lot_size: 0.10,
  pnl: 30.00,
  status: "open",
  opened_at: Timestamp
}
```

**Migration**:
```python
# Migrate fires
cursor = conn.execute("SELECT * FROM fires")
for row in cursor:
    db.collection('fires').document(row['fire_id']).set({
        'user_id': row['user_id'],
        'signal_id': row.get('mission_id') or row.get('signal_id'),
        'status': row['status'],
        'ticket': row.get('ticket'),
        'fill_price': row.get('price'),
        'lot_size': row.get('lot_size', 0.01),
        'created_at': firestore.SERVER_TIMESTAMP
    })

# Migrate open positions (if any)
cursor = conn.execute("""
    SELECT * FROM fires
    WHERE status = 'FILLED'
    AND ticket IS NOT NULL
""")
for row in cursor:
    # Check if still open (would need EA confirmation)
    db.collection('positions').document(str(row['ticket'])).set({
        'fire_id': row['fire_id'],
        'user_id': row['user_id'],
        'status': 'open',
        'opened_at': firestore.SERVER_TIMESTAMP
    })
```

**Update Code to Use Firestore**:
```python
# OLD: SQLite
def get_user_fires(user_id):
    cursor = db.execute(
        "SELECT * FROM fires WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    return cursor.fetchall()

# NEW: Firestore
def get_user_fires(user_id):
    fires = firestore_db.collection('fires') \
        .where('user_id', '==', user_id) \
        .order_by('created_at', direction=firestore.Query.DESCENDING) \
        .limit(50) \
        .get()

    return [fire.to_dict() for fire in fires]
```

**Critical**: Test fire execution end-to-end before going live

---

### Priority 3.3: Delete Old Databases (Week 8)
**Impact**: HIGH | **Effort**: LOW | **Risk**: LOW

**After 7 days of successful Firestore operation**:

```bash
# Verify Firestore has all data
python3 verify_migration.py

# Create final backup
cp bitten.db bitten_v1_final_backup.db
tar -czf jsonl_files_backup.tar.gz *.jsonl

# Move to archive
mkdir -p /root/BITTEN_V1_ARCHIVE
mv bitten.db /root/BITTEN_V1_ARCHIVE/
mv fire_mode.db /root/BITTEN_V1_ARCHIVE/
mv *.jsonl /root/BITTEN_V1_ARCHIVE/
mv user_registry.json /root/BITTEN_V1_ARCHIVE/

# Delete after 30 days confirmation
# (set calendar reminder)
```

**Expected Result**: 0 SQLite files, 0 JSONL files in production

---

## PHASE 4: WEBAPP SIMPLIFICATION (Weeks 9-10)
**Goal**: Clean API, modular code, Firebase SDK integration

### Priority 4.1: API Modernization (Week 9)
**Impact**: MEDIUM | **Effort**: HIGH | **Risk**: MEDIUM

**Current**: webapp_server_optimized.py (208KB, 200+ routes)

**New Structure**:
```
src/api/
├── app.py                  # Flask factory (100 lines)
├── routes/
│   ├── signals.py          # GET/POST /api/v1/signals
│   ├── fires.py            # POST /api/v1/fires
│   ├── users.py            # GET /api/v1/users
│   └── analytics.py        # GET /api/v1/analytics
├── middleware/
│   ├── firebase_auth.py    # Verify Firebase tokens
│   └── rate_limit.py       # Request throttling
└── services/
    ├── fire_service.py     # Business logic
    ├── signal_service.py   # Signal queries
    └── user_service.py     # User management
```

**Example Refactor**:
```python
# OLD: routes + logic mixed (webapp_server_optimized.py)
@app.route('/api/signals', methods=['POST'])
def create_signal():
    data = request.get_json()

    # Validation inline
    if not data.get('symbol'):
        return jsonify({"error": "Missing symbol"}), 400

    # Business logic inline
    confidence = data.get('confidence', 0)
    if confidence < 70:
        return jsonify({"error": "Low confidence"}), 400

    # Database write inline
    conn = sqlite3.connect('bitten.db')
    cursor = conn.execute(
        "INSERT INTO signals (...) VALUES (...)",
        (data['signal_id'], data['symbol'], ...)
    )
    conn.commit()

    return jsonify({"success": True})

# NEW: Separation of concerns
# routes/signals.py
@signals_bp.route('/api/v1/signals', methods=['POST'])
@require_firebase_auth
def create_signal():
    # Parse and validate
    signal_req = SignalRequest(**request.json)

    # Call service layer
    result = signal_service.create_signal(signal_req)

    return jsonify(result.to_dict())

# services/signal_service.py
class SignalService:
    def __init__(self, firestore_db):
        self.db = firestore_db

    def create_signal(self, signal_req: SignalRequest) -> Signal:
        # Validation
        if signal_req.confidence < 70:
            raise ValidationError("Confidence too low")

        # Business logic
        signal = Signal(
            signal_id=signal_req.signal_id,
            symbol=signal_req.symbol,
            confidence=signal_req.confidence,
            created_at=firestore.SERVER_TIMESTAMP
        )

        # Persist
        self.db.collection('signals').document(signal.signal_id).set(
            signal.to_dict()
        )

        return signal
```

**Benefits**:
- Testable (can mock service layer)
- Clear responsibilities
- Easy to find code
- Reusable business logic

---

### Priority 4.2: Frontend Firebase SDK (Week 10)
**Impact**: MEDIUM | **Effort**: MEDIUM | **Risk**: LOW

**Current**: Custom WebSocket with Flask-SocketIO

**New**: Firebase SDK for real-time updates

**War Room Dashboard Update**:
```javascript
// OLD: Custom WebSocket
const socket = io();
socket.on('signal_update', (data) => {
    updateSignalCard(data);
});

// NEW: Firebase SDK
import { initializeApp } from "firebase/app";
import { getFirestore, collection, onSnapshot, query, where } from "firebase/firestore";

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Real-time signal updates
const signalsQuery = query(
    collection(db, 'signals'),
    where('created_at', '>', Date.now() - 86400000)  // Last 24 hours
);

onSnapshot(signalsQuery, (snapshot) => {
    snapshot.docChanges().forEach((change) => {
        if (change.type === 'added') {
            addSignalCard(change.doc.data());
        }
        if (change.type === 'modified') {
            updateSignalCard(change.doc.data());
        }
    });
});

// Real-time position updates
const positionsQuery = query(
    collection(db, 'positions'),
    where('user_id', '==', currentUserId),
    where('status', '==', 'open')
);

onSnapshot(positionsQuery, (snapshot) => {
    updatePositionsList(snapshot.docs.map(d => d.data()));
});
```

**Benefits**:
- No custom WebSocket code
- Offline support (built-in)
- Automatic reconnection
- Optimistic updates

---

## PHASE 5: TESTING & MONITORING (Weeks 11-12)
**Goal**: Automated tests, production monitoring

### Priority 5.1: Add Tests (Week 11)
**Impact**: HIGH | **Effort**: HIGH | **Risk**: NONE

**Test Structure**:
```
tests/
├── unit/
│   ├── test_patterns.py           # Each pattern detector
│   ├── test_fire_service.py       # Business logic
│   └── test_validators.py         # Validation rules
├── integration/
│   ├── test_firestore_ops.py      # Database operations
│   ├── test_zmq_gateway.py        # ZMQ communication
│   └── test_api_endpoints.py      # API routes
└── e2e/
    ├── test_signal_flow.py        # Signal generation → DB
    └── test_fire_flow.py          # Fire command → EA → confirmation
```

**Example Tests**:
```python
# tests/unit/test_patterns.py
def test_vcb_breakout_detection():
    # Arrange
    detector = VCBBreakout()
    candles = create_test_candles(compressed=True, breakout=True)

    # Act
    signal = detector.detect(candles)

    # Assert
    assert signal is not None
    assert signal.pattern_type == "VCB_BREAKOUT"
    assert signal.confidence > 65

def test_vcb_no_compression():
    detector = VCBBreakout()
    candles = create_test_candles(compressed=False)

    signal = detector.detect(candles)

    assert signal is None  # Should not trigger

# tests/integration/test_fire_service.py
def test_execute_fire_success(firestore_db):
    # Arrange
    fire_service = FireService(firestore_db)
    user = create_test_user(tier="COMMANDER", balance=10000)
    signal = create_test_signal(symbol="EURUSD")

    # Act
    result = fire_service.execute_fire(user.id, signal.id)

    # Assert
    assert result.status == "SENT"
    fire_doc = firestore_db.collection('fires').document(result.fire_id).get()
    assert fire_doc.exists
    assert fire_doc.to_dict()['status'] == 'SENT'

# tests/e2e/test_signal_flow.py
def test_full_signal_flow(firestore_db, zmq_gateway):
    # 1. Generate signal
    signal = elite_guard.generate_signal("EURUSD")

    # 2. Verify Firestore
    signal_doc = firestore_db.collection('signals').document(signal.signal_id).get()
    assert signal_doc.exists

    # 3. Verify Telegram alert sent
    assert telegram_bot.last_message_contains(signal.signal_id)

    # 4. Verify available in API
    response = requests.get(f'/api/v1/signals/{signal.signal_id}')
    assert response.status_code == 200
```

**Run Tests**:
```bash
# Unit tests (fast)
pytest tests/unit/ -v

# Integration tests (requires Firebase emulator)
firebase emulators:start
pytest tests/integration/ -v

# E2E tests (requires running system)
pytest tests/e2e/ -v --slow

# Coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**Target**: 80% coverage

---

### Priority 5.2: Production Monitoring (Week 12)
**Impact**: HIGH | **Effort**: MEDIUM | **Risk**: NONE

**Firebase Monitoring Setup**:

**1. Performance Monitoring**
```javascript
// Add to webapp
import { initializeApp } from 'firebase/app';
import { getPerformance } from 'firebase/performance';

const app = initializeApp(firebaseConfig);
const perf = getPerformance(app);

// Automatically tracks:
// - Page load times
// - Network requests
// - Firebase operations
```

**2. Crashlytics** (for Python processes)
```python
# Add to each process
from firebase_admin import crashlytics

try:
    # Process code
    run_zmq_gateway()
except Exception as e:
    # Report crash
    crashlytics.log(f"ZMQ Gateway crashed: {e}")
    crashlytics.set_custom_key("process", "zmq_gateway")
    crashlytics.report_exception()
    raise
```

**3. Cloud Logging**
```python
# Replace print() and logger with Cloud Logging
from google.cloud import logging

logging_client = logging.Client()
logger = logging_client.logger('bitten-v2')

# Structured logging
logger.log_struct({
    'event': 'fire_executed',
    'user_id': user_id,
    'signal_id': signal_id,
    'status': 'success',
    'latency_ms': 150
}, severity='INFO')
```

**4. Alerting Rules** (Firebase Console)
```
Alert: High Fire Latency
Condition: 95th percentile > 100ms
Window: 5 minutes
Action: Email + Slack notification

Alert: Pattern Win Rate Drop
Condition: VCB_BREAKOUT win_rate < 45% over 24h
Action: Disable pattern + notify

Alert: Process Crash
Condition: Crashlytics error count > 5 in 1 hour
Action: Auto-restart + page on-call
```

**5. Custom Dashboards** (Grafana with Firebase data source)
```
Dashboard: Trading Performance
- Signals generated per hour
- Fire execution success rate
- Pattern win rates (live)
- User activity (fires by tier)
- System health (process uptime)
```

---

## SUMMARY: FINAL STATE

### Before (v1.0)
- **Files**: 1,035 Python files
- **Processes**: 15 PM2 processes
- **Database**: SQLite + JSONL files + JSON files
- **Auth**: Custom JWT, scattered
- **Real-time**: Custom WebSocket
- **Monitoring**: Manual log checking
- **Deployment**: Manual PM2 commands

### After (v2.0)
- **Files**: ~300 Python files (71% reduction)
- **Processes**: 5 Python + Cloud Functions (67% reduction)
- **Database**: Firestore only
- **Auth**: Firebase Auth
- **Real-time**: Firebase SDK
- **Monitoring**: Firebase Performance + Crashlytics
- **Deployment**: `firebase deploy` (automated)

### Key Improvements
1. ✅ **Single Source of Truth**: Firestore (no SQLite, no JSONL files)
2. ✅ **Automatic Scaling**: Cloud Functions scale to zero
3. ✅ **Real-time Everything**: Firebase SDK handles it
4. ✅ **Built-in Security**: Firebase Auth + Rules
5. ✅ **Production Monitoring**: Firebase suite
6. ✅ **Automatic Backups**: Firebase handles daily backups
7. ✅ **Global CDN**: Firebase Hosting for webapp
8. ✅ **Cost Efficiency**: Pay only for what you use

---

## RISK MANAGEMENT

### High-Risk Items
1. **Elite Guard Refactor** (Week 5)
   - **Risk**: Breaking signal generation
   - **Mitigation**: Parallel run, gradual cutover

2. **Fire Execution Migration** (Week 7)
   - **Risk**: Lost trades during migration
   - **Mitigation**: Read-only migration first, then switch writes

3. **ZMQ Gateway** (Week 4)
   - **Risk**: EA communication failure
   - **Mitigation**: Run alongside old system, compare outputs

### Medium-Risk Items
1. **File Deletion** (Week 2)
   - **Risk**: Delete something still needed
   - **Mitigation**: Move to DELETED_FILES/, wait 7 days

2. **Process Consolidation** (Weeks 4-6)
   - **Risk**: Missing functionality
   - **Mitigation**: Feature parity checklist, testing

### Low-Risk Items
1. **Tracking File Consolidation** (Week 2)
   - **Risk**: Data loss
   - **Mitigation**: Migrate all data, verify counts

2. **Cloud Functions** (Week 6)
   - **Risk**: Function failures
   - **Mitigation**: Firebase has built-in retries

---

## SUCCESS CRITERIA

### Week 4 Checkpoint
- [ ] Firebase project fully configured
- [ ] 700+ files deleted (moved to archive)
- [ ] User data migrated to Firestore
- [ ] Firebase Auth working

### Week 8 Checkpoint
- [ ] ZMQ Gateway operational
- [ ] Elite Guard refactored and tested
- [ ] All signal data in Firestore
- [ ] SQLite files archived

### Week 12 Checkpoint (DONE)
- [ ] All tests passing (80%+ coverage)
- [ ] Production monitoring active
- [ ] Performance targets met:
  - Fire latency < 100ms P95
  - Signal generation < 50ms
  - Zero process hangs
- [ ] Documentation complete

---

## ROLLBACK PLAN

**If things go wrong**:

1. **Immediate Rollback** (< 5 minutes)
   ```bash
   # Stop v2.0 processes
   pm2 stop all

   # Restore v1.0 backup
   cd /root/HydraX-v2
   git checkout main
   git reset --hard v1.0-tag

   # Restart v1.0
   pm2 start ecosystem.config.js
   ```

2. **Data Rollback** (< 30 minutes)
   ```bash
   # Restore SQLite database
   cp /root/BITTEN_V1_ARCHIVE/bitten_v1_final_backup.db bitten.db

   # Restore JSONL files
   tar -xzf /root/BITTEN_V1_ARCHIVE/jsonl_files_backup.tar.gz
   ```

3. **Gradual Rollback** (phased)
   - Roll back one component at a time
   - Identify which component failed
   - Fix and redeploy

---

## COST ANALYSIS (Firebase)

**Firebase Free Tier** (Spark Plan):
- Firestore: 1GB storage, 50K reads/day, 20K writes/day
- Auth: Unlimited users
- Cloud Functions: 125K invocations/month
- Hosting: 10GB/month

**Estimated Usage** (100 active users):
- Firestore: ~500MB storage, ~100K reads/day, ~10K writes/day
- Cloud Functions: ~50K invocations/month
- **Cost**: $0/month (within free tier)

**At Scale** (1,000 users):
- Firestore: ~2GB storage, ~500K reads/day, ~50K writes/day
- Cloud Functions: ~200K invocations/month
- **Cost**: ~$25/month (Blaze plan)

**Comparison**:
- Current VPS: $80/month (DigitalOcean/equivalent)
- Firebase at scale: $25/month
- **Savings**: $55/month (69% reduction)

---

## NEXT STEPS

1. **Review this document** with team
2. **Set up Firebase project** (Day 1)
3. **Create backups** (Day 2)
4. **Start Week 1 tasks** (Day 3)
5. **Daily standups** to track progress
6. **Weekly demos** to show progress

---

## APPENDIX: CRITICAL FILES TO KEEP

**DO NOT DELETE THESE**:
```
# Core system
/root/HydraX-v2/elite_guard_with_citadel.py  (until refactored)
/root/HydraX-v2/webapp_server_optimized.py   (until refactored)
/root/HydraX-v2/bitten_production_bot.py     (until simplified)
/root/HydraX-v2/command_router.py            (until replaced by gateway)
/root/HydraX-v2/enqueue_fire.py              (until absorbed)

# Configuration
/root/HydraX-v2/.env
/root/HydraX-v2/config_loader.py

# Documentation
/root/HydraX-v2/CLAUDE.md
/root/HydraX-v2/ARCHITECTURE.md
/root/HydraX-v2/SESSION_START.md
/root/HydraX-v2/BITTEN_rebuild_2.0.md  (this file)

# Data (until migrated)
/root/HydraX-v2/bitten.db
/root/HydraX-v2/comprehensive_tracking.jsonl
/root/HydraX-v2/user_registry.json
```

---

**Document Version**: 1.0
**Last Updated**: October 8, 2025
**Next Review**: After each phase completion
**Owner**: Development Team

---

## QUICK REFERENCE: COMMANDS

```bash
# Start Firebase emulator
firebase emulators:start

# Deploy Cloud Functions
cd functions && firebase deploy --only functions

# Run tests
pytest tests/ -v --cov=src

# Check file count
find . -name "*.py" | wc -l

# Check process count
pm2 list | grep -v "stopped" | wc -l

# Firestore data export
firebase firestore:export gs://bitten-backup/$(date +%Y%m%d)

# Rollback to v1.0
git checkout main && pm2 restart ecosystem.config.js
```
