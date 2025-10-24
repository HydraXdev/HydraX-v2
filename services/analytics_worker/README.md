# BITTEN v2.0 Analytics Worker Service

Background job processing service for signal tracking, statistics aggregation, and Firestore mirroring.

## Overview

The Analytics Worker runs continuously in the background, performing critical tasks:

1. **Outcome Tracker** - Tracks signals to TP/SL completion via ZMQ market data
2. **Stats Aggregator** - Calculates user win rates and performance metrics
3. **Firestore Mirror** - Syncs PostgreSQL data to Firestore for real-time web access
4. **Reconciliation** - Detects and corrects data drift between PostgreSQL and Firestore
5. **Reports** - Generates nightly performance reports and leaderboards

## Architecture

```
Analytics Worker (main.py)
    ├── Outcome Tracker (continuous ZMQ subscriber)
    │   └── Subscribes to port 5560 for market data
    │   └── Tracks active signals to TP/SL hits
    │   └── Updates signal_outcomes table
    │
    ├── Stats Aggregator (every 15 minutes)
    │   └── Calculates user win rates
    │   └── Updates users table
    │
    ├── Firestore Mirror (hourly)
    │   └── Mirrors users, signals, positions to Firestore
    │   └── Batch writes (500 docs/batch)
    │
    ├── Reconciliation (nightly at 2 AM UTC)
    │   └── Compares PostgreSQL vs Firestore
    │   └── Auto-corrects discrepancies
    │   └── Alerts on critical issues
    │
    └── Reports (nightly at 3 AM UTC)
        └── Pattern performance report
        └── User leaderboard
        └── System health metrics
```

## Job Schedule

| Job | Frequency | Description |
|-----|-----------|-------------|
| **Outcome Tracker** | Continuous | ZMQ subscription to track signals to TP/SL |
| **Stats Aggregator** | Every 15 min | User statistics calculation |
| **Firestore Mirror** | Hourly | PostgreSQL → Firestore sync |
| **Reconciliation** | Daily 2 AM UTC | Data drift detection & correction |
| **Reports** | Daily 3 AM UTC | Performance reports & leaderboards |

## Installation

```bash
cd /root/HydraX-v2/services/analytics_worker
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to customize:

```python
# PostgreSQL Connection
DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/bitten_v2'

# ZMQ Market Data
ZMQ_MARKET_DATA_PORT = 5560

# Firebase Credentials
FIREBASE_CREDENTIALS_PATH = '/root/bitten-firebase-sa.json'

# Job Schedules
JOB_SCHEDULES = {
    'outcome_tracker': {'trigger': 'interval', 'minutes': 5},
    'stats_aggregator': {'trigger': 'interval', 'minutes': 15},
    'firestore_mirror': {'trigger': 'interval', 'hours': 1},
    'reconciliation': {'trigger': 'cron', 'hour': 2, 'minute': 0},
    'reports': {'trigger': 'cron', 'hour': 3, 'minute': 0}
}
```

## Running the Service

### Development Mode

```bash
cd /root/HydraX-v2/services/analytics_worker
python main.py
```

### Production Mode (PM2)

```bash
# Start with PM2
pm2 start main.py --name analytics_worker --interpreter python3

# Monitor logs
pm2 logs analytics_worker

# Restart
pm2 restart analytics_worker

# Stop
pm2 stop analytics_worker
```

### Docker Mode

```bash
# Build container
docker build -t bitten-analytics-worker .

# Run container
docker run -d --name analytics_worker \
  -e DATABASE_URL="postgresql://..." \
  -v /root/bitten-firebase-sa.json:/app/credentials.json \
  bitten-analytics-worker
```

## Testing Individual Jobs

```bash
# Test stats aggregator
python -c "from jobs import StatsAggregator; StatsAggregator().run()"

# Test Firestore mirror
python -c "from jobs import FirestoreMirror; FirestoreMirror().run()"

# Test reconciliation
python -c "from jobs import Reconciliation; Reconciliation().run()"

# Test reports
python -c "from jobs import Reports; Reports().run()"

# Run test suite
python test_worker.py
```

## Outcome Tracker Details

The Outcome Tracker is a continuous background task that:

1. **Subscribes to ZMQ port 5560** for real-time market data
2. **Caches ticks** (last 1000 per symbol)
3. **Tracks active signals** from PostgreSQL
4. **Detects TP/SL hits** based on bid/ask prices
5. **Writes outcomes** to `signal_outcomes` table
6. **Updates signal status** to 'EXPIRED' when complete

### Example Outcome

```json
{
  "signal_id": "ELITE_GUARD_EURUSD_1758000000",
  "outcome": "WIN",
  "exit_price": 1.10500,
  "exit_time": 1758003600,
  "pips_result": 15.0,
  "confidence": 85.0,
  "pattern_type": "LIQUIDITY_SWEEP_REVERSAL"
}
```

## Stats Aggregator Details

Calculates and updates user statistics:

```sql
-- Example stats calculation
SELECT
    COUNT(*) as total_fires,
    COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as wins,
    ROUND((wins * 100.0 / NULLIF(total_fires, 0)), 2) as win_rate,
    SUM(pips_result) as total_pips
FROM positions
WHERE user_id = '7176191872'
```

## Firestore Mirror Details

Syncs data to Firestore collections:

```javascript
// users/{user_id}
{
  balance: 10000.00,
  equity: 10250.50,
  tier: "COMMANDER",
  fire_mode: "AUTO",
  bitmode_enabled: true,
  wins: 45,
  losses: 15,
  win_rate: 75.0,
  total_pips: 450.5,
  last_updated: Timestamp
}

// signals/{signal_id}
{
  symbol: "EURUSD",
  direction: "BUY",
  confidence: 85.0,
  pattern_type: "LIQUIDITY_SWEEP_REVERSAL",
  status: "ACTIVE",
  created_at: Timestamp,
  expires_at: 1758003600
}

// positions/{position_id}
{
  user_id: "7176191872",
  symbol: "GBPUSD",
  ticket: 12345678,
  status: "OPEN",
  open_price: 1.25000,
  current_price: 1.25150,
  profit: 15.00,
  lot_size: 0.10,
  created_at: Timestamp
}
```

## Reconciliation Details

Nightly drift detection and correction:

1. **Compares** PostgreSQL vs Firestore
2. **Detects**:
   - Missing records in Firestore
   - Data mismatches (balance, tier, status)
3. **Auto-corrects** simple discrepancies
4. **Alerts** on critical issues (>100 missing/mismatched)
5. **Reports** to `reconciliation_reports` table

## Reports Details

Generates three nightly reports:

### 1. Pattern Performance Report

```json
{
  "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
  "total_signals": 150,
  "wins": 105,
  "losses": 45,
  "win_rate": 70.0,
  "avg_confidence": 82.5,
  "avg_win_pips": 18.2,
  "avg_loss_pips": 12.5,
  "total_pips": 1347.5
}
```

### 2. User Leaderboard

Top users by win rate and total pips.

### 3. System Health Report

```json
{
  "signals": {
    "total": 250,
    "active": 45,
    "expired": 205,
    "avg_confidence": 78.5
  },
  "fires": {
    "total": 180,
    "filled": 165,
    "pending": 15
  },
  "positions": {
    "open": 12,
    "total_unrealized_pl": 450.25
  },
  "users": {
    "active_24h": 67
  }
}
```

## Logging

All jobs log to stdout with structured format:

```
2025-10-08 12:00:00 [INFO] outcome_tracker: Signal ELITE_GUARD_EURUSD_123 completed: WIN (+15.0 pips, exit=1.10500)
2025-10-08 12:15:00 [INFO] stats_aggregator: Updated stats for user 7176191872: 45W/15L (75.0% WR, +450.5 pips)
2025-10-08 13:00:00 [INFO] firestore_mirror: Mirrored 125 users, 45 signals, 12 positions to Firestore
2025-10-08 02:00:00 [INFO] reconciliation: Reconciliation complete: 5 missing, 2 mismatched, 7 auto-corrected
2025-10-08 03:00:00 [INFO] reports: Nightly reports complete: 3 reports generated
```

## Error Handling

All jobs include:

- **Retry logic** (max 3 retries with 5s delay)
- **Error logging** with full tracebacks
- **Graceful degradation** (one job failure doesn't stop others)
- **Database connection pooling** with auto-reconnect

## Dependencies

- `apscheduler` - Job scheduling
- `psycopg2-binary` - PostgreSQL driver
- `pyzmq` - ZMQ messaging
- `firebase-admin` - Firestore SDK
- `asyncio` - Async event loop

## Performance

- **Outcome Tracker**: Handles 1000+ ticks/second, tracks 100+ simultaneous signals
- **Stats Aggregator**: Processes 1000+ users in <5 seconds
- **Firestore Mirror**: Syncs 500 docs/batch, ~5000 docs/minute
- **Reconciliation**: Checks 10000+ records in <30 seconds
- **Reports**: Generates all reports in <10 seconds

## Monitoring

```bash
# Check job status
pm2 logs analytics_worker --lines 50

# Check last job runs
sqlite3 /root/HydraX-v2/bitten.db "SELECT * FROM reports ORDER BY created_at DESC LIMIT 5;"

# Check discrepancies
sqlite3 /root/HydraX-v2/bitten.db "SELECT * FROM reconciliation_reports WHERE created_at > strftime('%s', 'now', '-1 day');"
```

## Troubleshooting

### Jobs not running

```bash
# Check PM2 status
pm2 status

# Restart analytics worker
pm2 restart analytics_worker

# Check logs
pm2 logs analytics_worker --err
```

### Firestore connection issues

```bash
# Verify credentials file exists
ls -la /root/bitten-firebase-sa.json

# Test Firebase connection
python -c "from firebase_admin import credentials, initialize_app; initialize_app(credentials.Certificate('/root/bitten-firebase-sa.json'))"
```

### PostgreSQL connection issues

```bash
# Test database connection
psql -h localhost -U postgres -d bitten_v2 -c "SELECT COUNT(*) FROM signals;"

# Check DATABASE_URL environment variable
echo $DATABASE_URL
```

### ZMQ subscription issues

```bash
# Check if market data is flowing
python -c "import zmq; ctx = zmq.Context(); sub = ctx.socket(zmq.SUB); sub.connect('tcp://127.0.0.1:5560'); sub.subscribe(b''); print(sub.recv_string())"
```

## License

Proprietary - BITTEN Trading System v2.0
