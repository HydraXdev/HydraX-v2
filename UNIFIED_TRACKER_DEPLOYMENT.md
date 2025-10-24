# UNIFIED SIGNAL TRACKER - DEPLOYMENT DOCUMENTATION

**Created**: October 16, 2025
**Purpose**: Consolidate 7+ overlapping tracking systems into ONE unified tracker
**Status**: ✅ READY FOR PARALLEL TESTING

---

## 🎯 OVERVIEW

The unified signal tracker replaces the fragmented tracking infrastructure with a single, comprehensive system that tracks signals through their complete lifecycle:

```
Generation (ZMQ 5557) → Execution (fires table + ZMQ 5558) → Outcome (ZMQ 5560)
```

### **Key Features**

1. **3-Phase Tracking**:
   - Generation: Captures signal creation from Elite Guard
   - Execution: Records when/how signal was fired
   - Outcome: Tracks to actual TP/SL hit (no timeouts)

2. **Complete Metrics**:
   - Pattern performance, confidence calibration, session analysis
   - Execution vs non-execution comparison
   - Real P&L tracking (executed signals)
   - Theoretical P&L (all signals)

3. **Dual Output**:
   - Database: `signals` table with enhanced schema
   - JSONL: `unified_tracking.jsonl` (event-based audit log)

4. **Parallel Testing**:
   - Runs alongside `definitive_signal_tracker` for validation
   - Compare outputs for 1 week minimum
   - Report any discrepancies before cutover

---

## 📁 FILES CREATED

### **Core Tracker**
- `/root/HydraX-v2/unified_signal_tracker.py` (544 lines)
  - Complete 3-phase tracking implementation
  - Database schema migration (13 new columns)
  - JSONL event logging
  - ZMQ subscriptions to ports 5557, 5558, 5560

### **Testing**
- `/root/HydraX-v2/test_unified_tracker.py` (150 lines)
  - Startup validation script
  - Database schema verification
  - ZMQ availability check
  - Instantiation test

### **Documentation**
- `/root/HydraX-v2/UNIFIED_TRACKER_DEPLOYMENT.md` (this file)

---

## 📊 DATABASE SCHEMA ENHANCEMENTS

**New columns added to `signals` table** (automatically added on first run):

```sql
-- Signal Quality Metrics
quality_score REAL               -- ML-adjusted confidence (0-100)
signal_class TEXT                -- RAPID/SNIPER classification

-- Execution Tracking
was_executed INTEGER DEFAULT 0   -- 0=not executed, 1=executed
execution_method TEXT            -- AUTO/MANUAL/NULL
fire_id TEXT                     -- Link to fires table
user_id TEXT                     -- Who executed (Firebase UID)
mt5_ticket INTEGER               -- Actual MT5 position ticket
fill_price REAL                  -- Actual entry price from MT5
slippage_pips REAL               -- fill_price - entry_price in pips

-- P&L Tracking
actual_pnl_usd REAL              -- Real P&L if executed (USD)
theoretical_pnl_pips REAL        -- Predicted outcome for all signals
commission_usd REAL              -- Broker commission
swap_usd REAL                    -- Overnight swap fees

-- Indexes created:
-- idx_signals_outcome (outcome)
-- idx_signals_pattern (pattern_type)
-- idx_signals_executed (was_executed)
-- idx_signals_user (user_id)
-- idx_signals_session (session)
```

**Status**: ✅ All columns added successfully during test (see test output)

---

## 📋 OUTPUT FORMAT

### **JSONL Event Types**

**1. SIGNAL_GENERATION** (from ZMQ 5557):
```json
{
  "event_type": "SIGNAL_GENERATION",
  "timestamp": "2025-10-16T13:00:00.123456",
  "signal_id": "ELITE_RAPID_EURUSD_1760620000",
  "symbol": "EURUSD",
  "direction": "BUY",
  "pattern_type": "KALMAN_QUICKFIRE",
  "signal_class": "RAPID",
  "confidence": 85.2,
  "quality_score": 88.5,
  "entry_price": 1.16050,
  "sl_price": 1.15850,
  "tp_price": 1.16450,
  "stop_pips": 20.0,
  "target_pips": 40.0,
  "risk_reward": 2.0,
  "session": "LONDON",
  "created_at": 1760620000
}
```

**2. SIGNAL_EXECUTED** (from fires table or ZMQ 5558):
```json
{
  "event_type": "SIGNAL_EXECUTED",
  "timestamp": "2025-10-16T13:00:15.234567",
  "signal_id": "ELITE_RAPID_EURUSD_1760620000",
  "fire_id": "FIRE_EURUSD_1760620015",
  "user_id": "wlJ5lafBqRSLwHIUBxJQMr4SBtk1",
  "execution_method": "AUTO",
  "mt5_ticket": 20813456,
  "fill_price": 1.16055,
  "slippage_pips": 0.5,
  "lot": 0.10,
  "executed_at": 1760620015
}
```

**3. SIGNAL_OUTCOME** (from ZMQ 5560):
```json
{
  "event_type": "SIGNAL_OUTCOME",
  "timestamp": "2025-10-16T13:45:30.345678",
  "signal_id": "ELITE_RAPID_EURUSD_1760620000",
  "outcome": "WIN",
  "exit_price": 1.16450,
  "exit_reason": "TP_HIT",
  "duration_seconds": 2715,
  "theoretical_pnl_pips": 40.0,
  "actual_pnl_pips": 39.5,
  "actual_pnl_usd": 39.50,
  "completed_at": 1760622715
}
```

---

## 🚀 DEPLOYMENT STEPS

### **Phase 1: Parallel Testing (1 Week Minimum)**

**1. Start unified tracker** (non-breaking, runs alongside existing):
```bash
# Option A: Direct (for testing)
python3 /root/HydraX-v2/unified_signal_tracker.py

# Option B: PM2 (for production parallel test)
pm2 start /root/HydraX-v2/unified_signal_tracker.py --name unified_tracker
```

**2. Verify startup**:
```bash
# Check process is running
pm2 status unified_tracker

# Check logs
pm2 logs unified_tracker --lines 50

# Verify tracking file
tail -f /root/HydraX-v2/unified_tracking.jsonl
```

**3. Monitor for 1 week**:
```bash
# Daily check: Compare output counts
echo "Definitive tracker:"
wc -l /root/HydraX-v2/signal_tracking.jsonl

echo "Unified tracker:"
wc -l /root/HydraX-v2/unified_tracking.jsonl

# Check database updates
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN was_executed = 1 THEN 1 END) as executed,
    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses
FROM signals;"
```

**4. Validation criteria**:
- ✅ Both trackers record same signals
- ✅ Both trackers record same outcomes
- ✅ No crashes or errors for 7 days
- ✅ Database updates working correctly
- ✅ JSONL file growing consistently

### **Phase 2: Cutover (After Validation)**

**⚠️ DO NOT PROCEED UNTIL PHASE 1 COMPLETE AND VALIDATED**

**1. Stop old tracker**:
```bash
pm2 stop signal_tracker
```

**2. Verify unified tracker is primary**:
```bash
pm2 list | grep tracker
# Should show: unified_tracker (online), signal_tracker (stopped)
```

**3. Update consumers** (if needed):
```bash
# Update any scripts reading signal_tracking.jsonl to read unified_tracking.jsonl
# Most consumers should continue working as schema is compatible
```

**4. Monitor for 24 hours**:
```bash
# Check for any issues
pm2 logs unified_tracker --lines 100
```

### **Phase 3: Cleanup (After Successful Cutover)**

**1. Archive old tracking files**:
```bash
mkdir -p /root/archive_v1/tracking_files/
mv /root/HydraX-v2/signal_tracking.jsonl /root/archive_v1/tracking_files/
mv /root/HydraX-v2/optimized_tracking.jsonl /root/archive_v1/tracking_files/
```

**2. Remove old tracker code**:
```bash
# Archive definitive_signal_tracker.py
mv /root/HydraX-v2/definitive_signal_tracker.py /root/archive_v1/tracking_files/
```

**3. Update CLAUDE.md**:
- Document unified tracker as THE ONLY tracker
- Update all references to tracking files
- Add unified_tracking.jsonl as primary source

---

## 🔍 MONITORING & DEBUGGING

### **Check Tracker Status**

```bash
# PM2 status
pm2 status unified_tracker

# Recent logs
pm2 logs unified_tracker --lines 50

# Check for errors
pm2 logs unified_tracker --err

# Resource usage
pm2 show unified_tracker
```

### **Verify Data Flow**

```bash
# Check signal generation (should see GENERATION events)
tail -10 /root/HydraX-v2/unified_tracking.jsonl | grep SIGNAL_GENERATION

# Check execution tracking (should see EXECUTED events)
tail -10 /root/HydraX-v2/unified_tracking.jsonl | grep SIGNAL_EXECUTED

# Check outcome tracking (should see OUTCOME events)
tail -10 /root/HydraX-v2/unified_tracking.jsonl | grep SIGNAL_OUTCOME

# Database verification
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    outcome,
    COUNT(*) as count
FROM signals
WHERE was_executed = 1
GROUP BY outcome;"
```

### **Performance Metrics**

```bash
# Count events by type
cat /root/HydraX-v2/unified_tracking.jsonl | jq -r '.event_type' | sort | uniq -c

# Check win rate
sqlite3 /root/HydraX-v2/bitten.db "SELECT
    ROUND(CAST(COUNT(CASE WHEN outcome='WIN' THEN 1 END) AS FLOAT) /
          COUNT(*) * 100, 1) as win_rate_pct,
    COUNT(*) as total,
    COUNT(CASE WHEN outcome='WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome='LOSS' THEN 1 END) as losses
FROM signals
WHERE outcome IN ('WIN', 'LOSS');"
```

### **Common Issues**

**Issue**: Tracker not recording signals
- Check: `pm2 logs unified_tracker` for ZMQ connection errors
- Verify: Elite Guard is running and publishing to port 5557
- Test: `curl http://localhost:5557` or check with `ss -tulpen | grep 5557`

**Issue**: No execution tracking
- Check: fires table has recent entries
- Verify: Port 5558 is active (EA confirmations)
- Check: `fire_id` fields are being populated

**Issue**: No outcome tracking
- Check: Market data flowing on port 5560
- Verify: `zmq_telemetry_bridge` is running
- Check: Pending signals have valid entry/sl/tp prices

---

## 📈 EXPECTED RESULTS

### **After 1 Week of Parallel Testing**

**Database state**:
- ~500-1000 new signals with complete tracking data
- All 13 new columns populated correctly
- Execution correlation working (fire_id → signal_id)
- Outcomes matching definitive_signal_tracker

**JSONL file**:
- ~1500-3000 events (3 events per signal average)
- All event types present (GENERATION, EXECUTED, OUTCOME)
- No parse errors when replaying

**Statistics should match**:
- Win rate: 45-50% (Elite Guard v7.0 BALANCED target)
- Signal count: Same as definitive_signal_tracker
- Execution rate: ~10-20% of signals (AUTO + manual fires)

---

## ✅ SUCCESS CRITERIA

**Phase 1 (Parallel Testing) Complete When**:
1. ✅ Runs for 7 days without crashes
2. ✅ Signal counts match definitive tracker (±5%)
3. ✅ Outcome accuracy matches (±2% win rate)
4. ✅ Database updates working (all new columns populated)
5. ✅ JSONL file growing consistently
6. ✅ No duplicate tracking (same signal not tracked twice)
7. ✅ Execution correlation working (fire_id links)

**Phase 2 (Cutover) Complete When**:
1. ✅ Old tracker stopped successfully
2. ✅ Unified tracker is only active tracker
3. ✅ All consumers updated (if needed)
4. ✅ 24 hours of stable operation

**Phase 3 (Cleanup) Complete When**:
1. ✅ Old tracking files archived
2. ✅ Documentation updated
3. ✅ CLAUDE.md reflects new architecture
4. ✅ No references to old tracking systems

---

## 🚨 ROLLBACK PLAN

**If Issues Found During Parallel Testing**:

```bash
# Stop unified tracker
pm2 stop unified_tracker

# Verify old tracker still running
pm2 status signal_tracker

# Report discrepancies with evidence
```

**DO NOT PROCEED TO PHASE 2 IF**:
- Signal counts differ by >10%
- Win rates differ by >5%
- Crashes occur more than once per day
- Database updates are inconsistent
- Memory/CPU usage is excessive (>500MB RAM, >50% CPU sustained)

---

## 📞 SUPPORT

**For Issues or Questions**:
1. Check this documentation first
2. Review `/root/TRACKING_INFRASTRUCTURE_COMPLETE_ANALYSIS.md`
3. Examine logs: `pm2 logs unified_tracker`
4. Test with: `python3 /root/HydraX-v2/test_unified_tracker.py`

**Key Files**:
- Tracker: `/root/HydraX-v2/unified_signal_tracker.py`
- Output: `/root/HydraX-v2/unified_tracking.jsonl`
- Database: `/root/HydraX-v2/bitten.db` (signals table)
- Test: `/root/HydraX-v2/test_unified_tracker.py`

---

**END OF DEPLOYMENT DOCUMENTATION**

**Remember**: This tracker runs IN PARALLEL with existing systems. DO NOT stop or replace definitive_signal_tracker until Phase 1 validation is complete (minimum 1 week).
