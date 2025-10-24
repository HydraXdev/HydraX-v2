# BITTEN Firestore Setup Guide

Complete Firestore configuration for BITTEN v2.0 event-driven architecture.

## Directory Structure

```
/root/HydraX-v2/firestore/
├── firestore.rules             # Security rules
├── firestore.indexes.json      # Composite index definitions
├── init_firestore.py           # Initialize collections & sample data
├── test_firestore.py           # Comprehensive test suite
└── README.md                   # This file
```

## Collections Structure

### users/{user_id}
User account data and settings.

```python
{
  "user_id": str,           # Telegram user ID
  "balance": float,         # MT5 account balance
  "equity": float,          # Current equity
  "tier": str,              # RECRUIT, FANG, COMMANDER, COMMANDER+
  "fire_mode": str,         # MANUAL, SEMI_AUTO, FULL_AUTO
  "bitmode_enabled": bool,  # Hybrid position management
  "auto_fire_slots": int,   # Number of concurrent AUTO positions
  "last_updated": timestamp # Last sync time
}
```

### signals/{signal_id} (TTL: 24 hours)
Trading signals from Elite Guard.

```python
{
  "signal_id": str,         # Unique signal identifier
  "symbol": str,            # Trading pair (EURUSD, GBPJPY, etc.)
  "direction": str,         # BUY or SELL
  "entry_price": float,     # Entry price
  "sl_pips": float,         # Stop loss in pips
  "tp_pips": float,         # Take profit in pips
  "confidence": float,      # 0-100 confidence score
  "pattern_type": str,      # SMC pattern type
  "signal_type": str,       # RAPID_ASSAULT, PRECISION_STRIKE
  "citadel_score": float,   # 0-10 CITADEL Shield score
  "status": str,            # ACTIVE, EXPIRED, FIRED
  "created_at": timestamp,  # Signal generation time
  "expires_at": timestamp,  # 15-40 minute expiry
  "ttl": timestamp          # Auto-delete after 24 hours
}
```

### positions/{position_id}
Active trading positions.

```python
{
  "position_id": str,       # Unique position identifier
  "user_id": str,           # Owner user ID
  "ticket": int,            # MT5 ticket number
  "symbol": str,            # Trading pair
  "direction": str,         # BUY or SELL
  "volume": float,          # Position size (lots)
  "open_price": float,      # Entry fill price
  "sl": float,              # Stop loss price
  "tp": float,              # Take profit price
  "status": str,            # OPEN, CLOSED
  "profit": float,          # Current P&L
  "created_at": timestamp   # Position open time
}
```

### fire_history/{fire_id}
Complete fire command execution history.

```python
{
  "fire_id": str,           # Unique fire identifier
  "user_id": str,           # User who executed
  "signal_id": str,         # Source signal
  "mission_id": str,        # Mission reference
  "status": str,            # PENDING, FILLED, FAILED
  "ticket": int,            # MT5 ticket (if filled)
  "fill_price": float,      # Execution price
  "volume": float,          # Position size
  "created_at": timestamp   # Fire execution time
}
```

### system/{docId}
System-wide statistics and metrics.

```python
{
  "total_signals": int,     # All-time signal count
  "active_signals": int,    # Currently active
  "total_fires": int,       # All-time fire count
  "active_positions": int,  # Open positions
  "total_users": int,       # Registered users
  "last_updated": timestamp # Stats update time
}
```

## Security Rules

### Read Access
- **users**: User can read their own data only
- **signals**: All authenticated users can read active signals
- **positions**: User can read their own positions only
- **fire_history**: User can read their own history only
- **system**: All authenticated users can read stats

### Write Access
- **ALL COLLECTIONS**: Server-only writes via Admin SDK
- Client SDKs have NO write access (security)

## Indexes

### Composite Indexes
1. **signals**: `status` ASC + `created_at` DESC
2. **signals**: `symbol` ASC + `confidence` DESC
3. **signals**: `pattern_type` ASC + `created_at` DESC
4. **positions**: `user_id` ASC + `status` ASC
5. **positions**: `user_id` ASC + `created_at` DESC
6. **fire_history**: `user_id` ASC + `created_at` DESC
7. **fire_history**: `user_id` ASC + `status` ASC + `created_at` DESC

### Why These Indexes?
- Fast signal queries by status and recency
- Efficient symbol-specific signal searches
- Quick user position lookups
- Optimized fire history queries

## Installation

### 1. Initialize Firestore

```bash
cd /root/HydraX-v2/firestore
python3 init_firestore.py
```

This will:
- Initialize Firebase Admin SDK
- Create all collections
- Add sample documents
- Verify structure
- Test query performance

### 2. Deploy Security Rules

```bash
# Install Firebase CLI if needed
npm install -g firebase-tools

# Login to Firebase
firebase login

# Deploy rules
firebase deploy --only firestore:rules
```

### 3. Deploy Indexes

```bash
firebase deploy --only firestore:indexes
```

Note: Index deployment can take several minutes for large datasets.

### 4. Run Tests

```bash
python3 test_firestore.py
```

Expected output:
```
🔥 BITTEN FIRESTORE TEST SUITE
══════════════════════════════════════════════════════════════════════

🧪 Test 1: Write Access (Admin SDK)
  ✅ PASS: Write user document
  ✅ PASS: Write signal document
  ✅ PASS: Write position document

🧪 Test 2: Read Access (Admin SDK)
  ✅ PASS: Read user document
  ✅ PASS: Read signal document
  ✅ PASS: Read position document

🧪 Test 3: Security Rules Verification
  ✅ PASS: Security rules

🧪 Test 4: Signal TTL Configuration
  ✅ PASS: Signal TTL field set

🧪 Test 5: Index Performance
  ✅ PASS: Indexed query (status + created_at)
  ✅ PASS: Indexed query (user_id + status)

🧪 Test 6: Batch Operations
  ✅ PASS: Batch write (5 documents)
  ✅ PASS: Batch verification

🧪 Test 7: Transactions
  ✅ PASS: Transactional update

📊 TEST SUMMARY
══════════════════════════════════════════════════════════════════════
Total Tests: 12
Passed: 12 ✅
Failed: 0 ❌
Success Rate: 100.0%
```

## Usage Examples

### Write Signal (Server-side)

```python
from firebase_admin import firestore
from datetime import datetime, timedelta

db = firestore.client()

signal_data = {
    'signal_id': 'ELITE_GUARD_EURUSD_12345',
    'symbol': 'EURUSD',
    'direction': 'BUY',
    'confidence': 85.5,
    'status': 'ACTIVE',
    'created_at': datetime.utcnow(),
    'expires_at': datetime.utcnow() + timedelta(minutes=15),
    'ttl': datetime.utcnow() + timedelta(hours=24)
}

db.collection('signals').document(signal_data['signal_id']).set(signal_data)
```

### Query Active Signals

```python
from google.cloud.firestore_v1 import FieldFilter

signals = db.collection('signals')\
    .where(filter=FieldFilter('status', '==', 'ACTIVE'))\
    .order_by('created_at', direction=firestore.Query.DESCENDING)\
    .limit(10)\
    .stream()

for signal in signals:
    data = signal.to_dict()
    print(f"{data['symbol']} {data['direction']} @ {data['confidence']}%")
```

### Query User Positions

```python
positions = db.collection('positions')\
    .where(filter=FieldFilter('user_id', '==', '7176191872'))\
    .where(filter=FieldFilter('status', '==', 'OPEN'))\
    .stream()

for position in positions:
    data = position.to_dict()
    print(f"Ticket {data['ticket']}: {data['symbol']} {data['profit']} USD")
```

### Batch Write Positions

```python
batch = db.batch()

for i in range(10):
    position_ref = db.collection('positions').document(f'position_{i}')
    batch.set(position_ref, {
        'position_id': f'position_{i}',
        'user_id': '7176191872',
        'status': 'OPEN',
        'created_at': firestore.SERVER_TIMESTAMP
    })

batch.commit()
```

### Transaction Example

```python
@firestore.transactional
def update_stats(transaction, stats_ref):
    snapshot = stats_ref.get(transaction=transaction)
    current_count = snapshot.get('total_signals')
    transaction.update(stats_ref, {'total_signals': current_count + 1})

stats_ref = db.collection('system').document('stats')
transaction = db.transaction()
update_stats(transaction, stats_ref)
```

## TTL Configuration

### Signal Auto-Deletion
Signals automatically delete after 24 hours using the `ttl` field.

**Firebase Console Setup:**
1. Go to Firestore console
2. Navigate to signals collection
3. Create TTL policy on `ttl` field
4. Set expiration to 24 hours

**Code Implementation:**
```python
signal_data['ttl'] = datetime.utcnow() + timedelta(hours=24)
```

## Performance Optimization

### Best Practices
1. **Use indexed queries**: All production queries use composite indexes
2. **Batch writes**: Group multiple writes into batches (up to 500 ops)
3. **Limit query results**: Always use `.limit()` for large collections
4. **Cache locally**: Cache frequently accessed documents client-side
5. **Use transactions**: For atomic updates to multiple documents

### Query Performance
- Indexed queries: < 100ms for 10,000+ documents
- Single document reads: < 50ms
- Batch writes (10 docs): < 200ms
- Transactions: < 300ms

## Monitoring

### Firestore Console
- Active connections
- Read/write operations per second
- Index usage statistics
- Storage size

### Query Performance
```python
import time

start = time.time()
results = list(query.stream())
elapsed = (time.time() - start) * 1000
print(f"Query: {len(results)} results in {elapsed:.2f}ms")
```

## Troubleshooting

### Index Not Found Error
```
Error: The query requires an index
```

**Solution**: Deploy missing index
```bash
firebase deploy --only firestore:indexes
```

### Permission Denied
```
Error: Missing or insufficient permissions
```

**Solution**: Check security rules and user authentication

### Slow Queries
```
Query taking > 1 second
```

**Solution**:
1. Add composite index
2. Reduce query complexity
3. Use pagination with `.limit()`

## Migration from SQLite

### Current SQLite → Firestore Mapping

| SQLite Table | Firestore Collection | Notes |
|--------------|---------------------|-------|
| ea_instances | users | Combined with user data |
| signals | signals | Added TTL field |
| missions | signals | Merged into signals |
| fires | fire_history | Complete fire audit trail |
| (none) | positions | New: active positions |
| (none) | system | New: system stats |

### Migration Script
```python
import sqlite3
from firebase_admin import firestore

db_firestore = firestore.client()
db_sqlite = sqlite3.connect('/root/HydraX-v2/bitten.db')

# Migrate signals
cursor = db_sqlite.execute("SELECT * FROM signals")
for row in cursor:
    signal_data = {
        'signal_id': row[0],
        'symbol': row[1],
        # ... map all fields
    }
    db_firestore.collection('signals').document(row[0]).set(signal_data)
```

## Firebase Project Info

**Credentials**: `/root/bitten-firebase-sa.json`
**Project**: Check firebase.json or .firebaserc for project ID

## Support

**Documentation**: https://firebase.google.com/docs/firestore
**Admin SDK**: https://firebase.google.com/docs/admin/setup
**Security Rules**: https://firebase.google.com/docs/firestore/security/get-started

---

**Last Updated**: 2025-10-08
**Version**: 1.0.0
**Status**: Production Ready
