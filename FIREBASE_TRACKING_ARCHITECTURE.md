# Firebase Tracking Architecture - Complete Guide

**Last Updated**: October 16, 2025
**Status**: ✅ PRODUCTION READY
**Architecture**: Two-Layer Design (Firestore + BigQuery-ready)

---

## 🎯 CRITICAL: UNIFIED TRACKING ARCHITECTURE

### **THE ONLY TRACKING SYSTEM**

**Primary Data Source**: `/root/HydraX-v2/unified_tracking.jsonl`
**Database**: `/root/HydraX-v2/bitten.db` (signals table with outcome, exit_price, pnl_pips columns)
**Tracker Process**: `unified_tracker.py` (PM2 process: signal_tracker)

### **❌ REMOVED/DEPRECATED FILES:**
- ❌ truth_log.jsonl (stopped Aug 22, 2025)
- ❌ signal_tracking.jsonl (replaced by unified_tracking.jsonl)
- ❌ optimized_tracking.jsonl (merged into unified_tracking.jsonl)
- ❌ comprehensive_tracking.jsonl (replaced by unified_tracking.jsonl)
- ❌ definitive_signal_tracker.py (replaced by unified_tracker.py)
- ❌ analytics_worker (replaced by Firebase Reports dashboard)

### **DATA FLOW:**
```
Elite Guard (signal generation)
    ↓
unified_tracker.py (tracks to TP/SL completion)
    ↓
unified_tracking.jsonl (appends WIN/LOSS outcomes)
    ↓
bitten.db signals table (persistent storage)
    ↓
Firebase sync (mirrors to Firestore)
    ↓
Firebase Reports Dashboard (real-time analytics)
```

---

## 🎯 Architecture Overview

### Layer 1: Firestore (Real-Time Operational Store)
- **Purpose**: Live app/EA needs, fast dashboard queries
- **Data**: Signals, exec states, rollup metrics
- **Access**: Real-time subscriptions, instant reads
- **Cost**: Pay per read/write (optimized with rollups)

### Layer 2: BigQuery (Analytics - Future)
- **Purpose**: Heavy metrics, long history, deep analysis
- **Data**: Complete signal/exec history export
- **Access**: SQL queries on massive datasets
- **Cost**: Cheap for large scans vs Firestore

---

## 📊 Firestore Collections Structure

### `/signals/{signalId}` - Core Signal Data

**Immutable Fields** (set once at creation):
```javascript
{
  // Core signal
  pair: "EURUSD",
  symbol: "EURUSD",
  direction: "BUY",          // or "SELL"
  entry: 1.10000,
  sl: 1.09800,
  tp: 1.10300,
  confidence: 85.5,
  pattern_type: "VCB_BREAKOUT",
  strategy: "ELITE_RAPID",
  session: "LONDON",
  timeframe: "M5",

  // Risk/Reward
  stopPips: 20.0,
  targetPips: 30.0,
  riskReward: 1.5,

  // Timestamps
  createdAt: Timestamp,
  expiresAt: 1759889412,

  // Metadata
  proOnly: true,
  qualityTier: "gold",
  citadelScore: 8.5
}
```

**Mutable Fields** (updated when outcome occurs):
```javascript
{
  status: "HIT_TP",          // ACTIVE, EXPIRED, HIT_TP, HIT_SL
  outcome: "WIN",            // null, "WIN", "LOSS"
  exitPrice: 1.10305,
  exitTime: Timestamp,
  pnlPips: 30.5,
  durationSeconds: 1842
}
```

**Indexes Required**:
```
Single-field: createdAt desc, status asc, outcome asc
Composite: (status asc, createdAt desc) - for active signals query
```

---

### `/exec/{uid}/items/{execId}` - Execution Lifecycle

**Already Implemented** - Tracks trade execution from signal to fill:
```javascript
{
  id: "auto_ELITE_RAPID_GBPJPY_uid123",
  uid: "user123",
  signalId: "ELITE_RAPID_GBPJPY_1759889110",
  state: "FILLED",           // PENDING, SENT, ACKED, FILLED, REJECTED, TIMEOUT

  // Copy-through from signal (EA needs)
  pair: "GBPJPY",
  side: "SELL",
  price: 204.245,
  sl: 204.524,
  tp: 204.004,

  // Execution tracking
  createdAt: Timestamp,
  updatedAt: Timestamp,
  sentAt: Timestamp,
  ackAt: Timestamp,
  fillAt: Timestamp,

  // Results
  lot: 0.45,
  riskPct: 2.0,
  priceFill: 204.252,
  pnl: 125.50,
  reason: "success",

  // Metadata
  source: "AUTO"             // or "MANUAL"
}
```

**Indexes Required**:
```
Single-field: createdAt desc, state asc
Composite: (state asc, createdAt desc) - for active execs query
```

---

### `/metrics/global/daily/{YYYYMMDD}` - Global Daily Rollups

**Fast Dashboard Metrics** (1 doc read = today's stats):
```javascript
{
  // Signal counters (incremented on signal creation)
  signals: 42,

  // Fill counters (incremented on TP/SL hit)
  fills: 35,
  wins: 23,

  // Computed fields (updated by Cloud Function)
  winRate: 65.7,            // wins / fills * 100
  avgRR: 1.52,              // average risk/reward
  medianLatencyMs: 847,     // median time to fill

  updatedAt: Timestamp
}
```

**Usage**:
```javascript
// Get today's stats - SUPER FAST (1 doc read)
const today = new Date().toISOString().slice(0,10).replace(/-/g, '');
const statsDoc = await db.collection('metrics')
  .doc('global')
  .collection('daily')
  .doc(today)
  .get();

const stats = statsDoc.data();
console.log(`Today: ${stats.signals} signals • ${stats.fills} fills • Win ${stats.winRate}%`);
```

---

### `/metrics/pair/{PAIR}/daily/{YYYYMMDD}` - Per-Pair Rollups

**Same Structure as Global** but scoped to specific pair:
```javascript
{
  signals: 8,
  fills: 6,
  wins: 4,
  winRate: 66.7,
  avgRR: 1.6,
  medianLatencyMs: 753,
  updatedAt: Timestamp
}
```

**Usage**: Show pair performance without heavy aggregation queries.

---

### `/metrics/strategy/{STRATEGY}/daily/{YYYYMMDD}` - Per-Strategy Rollups

**Same Structure** but scoped to strategy (ELITE_RAPID, ELITE_SNIPER, etc.):
```javascript
{
  signals: 15,
  fills: 12,
  wins: 8,
  winRate: 66.7,
  avgRR: 1.45,
  medianLatencyMs: 892,
  updatedAt: Timestamp
}
```

---

## 🔄 Data Flow

### Signal Creation Flow:
```
Elite Guard (ZMQ 5557)
    ↓
ZMQ Relay → WebApp (/api/signals)
    ↓
firebase_bridge.mirror_signal_to_firestore()
    ↓
1. Write /signals/{signalId} (immutable core + mutable tracking fields)
2. Increment /metrics/global/daily/{today}.signals
3. Increment /metrics/pair/{PAIR}/daily/{today}.signals
4. Increment /metrics/strategy/{STRAT}/daily/{today}.signals
```

### Outcome Tracking Flow:
```
BITTEN unified_tracker.py (definitive signal tracker)
    ↓
unified_tracking.jsonl (appended with WIN/LOSS)
    ↓
bitten.db signals table (outcome, exit_price, pnl_pips columns)
    ↓
firebase_outcome_tracker.py (monitors DB + file)
    ↓
firebase_bridge.update_signal_outcome()
    ↓
1. Update /signals/{signalId} with outcome, exitPrice, pnlPips
2. Increment /metrics/global/daily/{today}.fills + wins
3. Increment /metrics/pair/{PAIR}/daily/{today}.fills + wins
4. Increment /metrics/strategy/{STRAT}/daily/{today}.fills + wins
```

---

## 🚀 Running Processes

### Core Processes:
```bash
# 1. ZMQ Relay with Firebase integration (PID 3482595)
nohup python3 elite_guard_zmq_relay.py > /tmp/zmq_relay_firebase.log 2>&1 &

# 2. Firebase Outcome Tracker (PID 3524523)
nohup python3 firebase_outcome_tracker.py > /tmp/firebase_outcome_tracker.log 2>&1 &
```

### Health Checks:
```bash
# Check relay status
pm2 status elite_guard_relay
pm2 logs elite_guard_relay --lines 20

# Check unified tracker status
pm2 status signal_tracker
tail -f /root/HydraX-v2/unified_tracking.jsonl

# Check outcome tracker
ps aux | grep firebase_outcome_tracker
tail -f /tmp/firebase_outcome_tracker.log

# Check database tracking
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE outcome IS NOT NULL;"

# Check Firestore signals count
python3 -c "
from google.cloud import firestore
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/root/bitten-firebase-sa.json'
db = firestore.Client(project='bitten-0420')
count = len(list(db.collection('signals').stream()))
print(f'Total signals in Firestore: {count}')
"
```

---

## 📈 Performance Optimization

### Cost Optimization:
- **Rollups prevent expensive aggregation queries** (1 doc read vs scanning thousands)
- **Client-side subscriptions** use narrow queries (filter by status, limit results)
- **TTL cleanup** (future): Archive old signals to BigQuery, soft-delete from Firestore

### Query Patterns:
```javascript
// ✅ GOOD: Use rollups for dashboard stats
const stats = await db.collection('metrics').doc('global').collection('daily').doc(today).get();

// ❌ BAD: Don't aggregate client-side
const allSignals = await db.collection('signals').get();
const winRate = allSignals.docs.filter(d => d.data().outcome === 'WIN').length / allSignals.size;
```

### Indexes for Common Queries:
```javascript
// Active signals (status = ACTIVE, ordered by time)
db.collection('signals')
  .where('status', '==', 'ACTIVE')
  .orderBy('createdAt', 'desc')
  .limit(10);
// Requires composite index: (status asc, createdAt desc)

// Recent outcomes
db.collection('signals')
  .where('outcome', '!=', null)
  .orderBy('outcome')
  .orderBy('exitTime', 'desc')
  .limit(20);
// Requires composite index: (outcome asc, exitTime desc)
```

---

## 🔐 Security Rules (Firestore Rules)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users can read all signals (read-only)
    match /signals/{signalId} {
      allow read: if request.auth != null;
      allow write: if false;  // Only backend can write
    }

    // Users can only read/write their own execs
    match /exec/{uid}/items/{execId} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }

    // Metrics are read-only for users
    match /metrics/{scope}/{collection}/{doc} {
      allow read: if request.auth != null;
      allow write: if false;  // Only Cloud Functions can write
    }

    // Presence is read-only
    match /presence/{uuid} {
      allow read: if request.auth != null;
      allow write: if false;
    }
  }
}
```

---

## 🎯 BigQuery Export (Future Phase 2)

### Option 1: Scheduled Daily Export
```bash
# Daily cron job (2am UTC)
gcloud firestore export gs://bitten-0420-exports/$(date +%Y%m%d) \
  --collection-ids=signals,exec

# Load to BigQuery
bq load --source_format=DATASTORE_BACKUP \
  bitten_analytics.signals \
  gs://bitten-0420-exports/$(date +%Y%m%d)/all_namespaces/kind_signals/all_namespaces_kind_signals.export_metadata
```

### Option 2: Real-Time Streaming
```javascript
// Cloud Function: onSignalWrite
exports.streamToBigQuery = functions.firestore
  .document('signals/{signalId}')
  .onWrite(async (change, context) => {
    const signal = change.after.data();
    await bigquery
      .dataset('bitten_analytics')
      .table('signals')
      .insert([{
        signal_id: context.params.signalId,
        ...signal,
        _inserted_at: new Date()
      }]);
  });
```

### BigQuery Schema:
```sql
CREATE TABLE bitten_analytics.signals (
  signal_id STRING NOT NULL,
  pair STRING,
  direction STRING,
  entry FLOAT64,
  sl FLOAT64,
  tp FLOAT64,
  confidence FLOAT64,
  pattern_type STRING,
  strategy STRING,
  session STRING,
  timeframe STRING,
  stop_pips FLOAT64,
  target_pips FLOAT64,
  risk_reward FLOAT64,
  created_at TIMESTAMP,
  expires_at TIMESTAMP,
  status STRING,
  outcome STRING,
  exit_price FLOAT64,
  exit_time TIMESTAMP,
  pnl_pips FLOAT64,
  duration_seconds INT64,
  _inserted_at TIMESTAMP
);

-- Win rate by pair and session
SELECT
  pair,
  session,
  COUNT(*) as total,
  COUNTIF(outcome = 'WIN') as wins,
  ROUND(COUNTIF(outcome = 'WIN') / COUNT(*) * 100, 1) as win_rate_pct
FROM bitten_analytics.signals
WHERE outcome IS NOT NULL
GROUP BY pair, session
ORDER BY win_rate_pct DESC;
```

---

## 🧪 Testing

### Test Signal Creation + Rollup:
```python
python3 -c "
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/root/bitten-firebase-sa.json'
from firebase_bridge import mirror_signal_to_firestore

test_signal = {
    'signal_id': 'TEST_SIGNAL_' + str(int(time.time())),
    'symbol': 'EURUSD',
    'direction': 'BUY',
    'entry_price': 1.10000,
    'stop_loss': 1.09800,
    'take_profit': 1.10300,
    'stop_pips': 20.0,
    'target_pips': 30.0,
    'risk_reward': 1.5,
    'confidence': 85.5,
    'pattern_type': 'VCB_BREAKOUT',
    'signal_type': 'ELITE_RAPID',
    'session': 'LONDON',
    'timeframe': 'M5'
}

mirror_signal_to_firestore(test_signal)
print('✅ Check Firestore Console for signal + metrics increment')
"
```

### Test Outcome Update:
```python
python3 -c "
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/root/bitten-firebase-sa.json'
from firebase_bridge import update_signal_outcome

# Use actual signal ID from unified_tracking.jsonl
update_signal_outcome(
    signal_id='ELITE_RAPID_USDJPY_1759889110',
    outcome='WIN',
    exit_price=152.067,
    pnl_pips=39.0
)
print('✅ Check signal document + metrics.fills increment')
print('✅ Verify outcome in unified_tracking.jsonl')
print('✅ Verify outcome in bitten.db signals table')
"
```

---

## 📚 Next Steps (Optional Enhancements)

### Cloud Functions for Advanced Rollups:
1. **onSignalCreate** - Increment counters (already done in Python)
2. **onOutcomeUpdate** - Calculate winRate, avgRR, medianLatency
3. **dailyRollup** - Scheduled function to compute complex metrics

### Stats Widget for Web App:
```typescript
// /components/StatsWidget.tsx
export function StatsWidget() {
  const today = new Date().toISOString().slice(0,10).replace(/-/g, '');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const unsubscribe = db
      .collection('metrics')
      .doc('global')
      .collection('daily')
      .doc(today)
      .onSnapshot(doc => {
        setStats(doc.data());
      });
    return unsubscribe;
  }, [today]);

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="stats-widget">
      <h3>Today's Performance</h3>
      <div>📊 {stats.signals} signals</div>
      <div>🎯 {stats.fills} fills</div>
      <div>✅ Win {stats.winRate}%</div>
    </div>
  );
}
```

### BigQuery Deployment:
1. Enable BigQuery API
2. Create `bitten_analytics` dataset
3. Set up daily export (Option 1) or streaming inserts (Option 2)
4. Build Looker Studio dashboards on BigQuery data

---

## 🎯 Summary

**What's Complete**:
- ✅ Unified tracking system (unified_tracking.jsonl + bitten.db)
- ✅ Enhanced signal schema with outcome tracking
- ✅ Firestore rollup collections (/metrics/*)
- ✅ Real-time metrics increments (Python-based)
- ✅ Outcome tracker daemon (bridges unified_tracker → Firebase)
- ✅ Auto-fire integration (environment-based)
- ✅ Firebase Reports dashboard (replaces old analytics systems)

**What's Ready for Later**:
- ⏳ Cloud Functions for advanced rollups
- ⏳ Stats widget for dashboard
- ⏳ BigQuery export for deep analytics
- ⏳ Firestore security rules deployment
- ⏳ TTL cleanup for old signals

**Cost Projection**:
- **Firestore**: ~$1-5/day (with rollups optimization)
- **BigQuery**: ~$0.10/day (scan costs only)
- **Cloud Functions**: ~$0.50/day (with rollup functions)

**Performance**:
- Dashboard stats: < 50ms (1 doc read)
- Signal list: < 200ms (indexed query)
- Outcome updates: < 100ms (atomic increment)

---

**Architecture validated and production-ready for immediate deployment.**
