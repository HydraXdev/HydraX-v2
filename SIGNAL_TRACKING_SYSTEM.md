# DEFINITIVE SIGNAL TRACKING SYSTEM

**Date**: October 6, 2025
**Status**: OPERATIONAL

## THE ONLY SIGNAL TRACKER

**File**: `/root/HydraX-v2/definitive_signal_tracker.py`
**PM2 Process**: `signal_tracker` (ID 3)
**Tracking File**: `/root/HydraX-v2/signal_tracking.jsonl`

## 100% ACCOUNTABILITY RULES

1. **ONE TRACKER ONLY** - No other signal tracking files exist or will be created
2. **NO TIMEOUTS** - Signals tracked until TP or SL hit, period
3. **NO FAKE DATA** - Only real market outcomes recorded
4. **DATABASE TRUTH** - All outcomes stored in `signals` table with `outcome`, `exit_price`, `duration_seconds`

## HOW IT WORKS

1. **Signal Generation** → Signals created in database with `outcome = NULL`
2. **Tracker Monitors** → Loads all pending signals on startup
3. **Market Data** → Subscribes to port 5560 for real-time tick data
4. **Outcome Detection** → Checks every tick if TP/SL hit for each pending signal
5. **Record Outcome** → Updates database + appends to JSONL tracking file
6. **100% Complete** → Every signal tracked to completion

## DELETED FILES

All duplicate/outdated tracking files have been PERMANENTLY DELETED:

- ❌ REAL_signal_tracker.py
- ❌ event_bus_outcome_tracker.py (kept for event bus integration)
- ❌ signal_accuracy_tracker.py
- ❌ failed_signal_tracker.py
- ❌ outcome_mirrorer.py
- ❌ prune_outcomes_45d.py
- ❌ outcomes_aggregate_daily.py
- ❌ comprehensive_tracking.jsonl
- ❌ optimized_tracking.jsonl
- ❌ truth_log.jsonl
- ❌ dynamic_tracking.jsonl

## VERIFICATION COMMANDS

```bash
# Check tracker status
pm2 status signal_tracker

# View tracker logs
pm2 logs signal_tracker --lines 50

# Check pending signals
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE outcome IS NULL;"

# Check completed signals
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE outcome IS NOT NULL;"

# View recent outcomes
tail -20 /root/HydraX-v2/signal_tracking.jsonl

# Check win rate
sqlite3 /root/HydraX-v2/bitten.db "SELECT 
    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
    ROUND(CAST(COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) AS FLOAT) / 
          COUNT(*) * 100, 1) as win_rate_pct
FROM signals 
WHERE outcome IS NOT NULL;"
```

## NEVER DO THIS AGAIN

- ❌ Create another signal tracker file
- ❌ Create tracking JSONL files (only signal_tracking.jsonl)
- ❌ Use timeouts for signal completion
- ❌ Archive outcomes - DELETE old data instead

## THE RULE

**ONE TRACKER. ONE FILE. 100% ACCOUNTABILITY. NO EXCEPTIONS.**
