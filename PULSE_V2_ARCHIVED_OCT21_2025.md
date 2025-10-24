# Pulse Scalper v2 Archived - October 21, 2025

## Summary

**Status**: ✅ ARCHIVED - Only Pulse Scalper v3 Running

**Action Taken**: Stopped Pulse Scalper v2 and archived the file

**Reason**: User requested to run only v3, mark v2 as archived

## Changes Made

### 1. ✅ Stopped PM2 Process

**Command**:
```bash
pm2 stop pulse_scalper
```

**Result**:
- PM2 ID 33: pulse_scalper - **STOPPED** ✅
- PM2 ID 54: pulse_scalper_v3 - **RUNNING** ✅

### 2. ✅ Archived v2 File

**Old Location**: `/root/pulse_scalper.py`
**New Location**: `/root/pulse_scalper_v2_ARCHIVED_OCT21_2025.py`

**Command**:
```bash
mv /root/pulse_scalper.py /root/pulse_scalper_v2_ARCHIVED_OCT21_2025.py
```

### 3. ✅ Saved PM2 State

**Command**:
```bash
pm2 save
```

**Result**: PM2 configuration saved with v2 stopped

## Current System State

**Active Pulse Generator**:
- ✅ **Pulse Scalper v3** (PM2 ID 54, PID 3433016) - **ONLINE**
  - File: `/root/pulse_scalper_v3_optimized.py`
  - Uptime: 16+ hours
  - Memory: 227.7mb
  - Status: Operational

**Archived Pulse Generator**:
- ❌ **Pulse Scalper v2** (PM2 ID 33) - **STOPPED**
  - File: `/root/pulse_scalper_v2_ARCHIVED_OCT21_2025.py`
  - Status: Archived, not running

**Relays**:
- pulse_relay (v2) - STOPPED ✅
- pulse_relay_v3 - STOPPED ✅ (uses clean_relay instead)

## Signal Generator Status

**Active Generators** (as of Oct 21, 2025):
1. ✅ Elite Guard (PM2 ID 38) - SMC patterns (port 5557)
2. ✅ Pulse Scalper v3 (PM2 ID 54) - Momentum patterns (port 5559)
3. ✅ APEX Sentinel (PM2 ID 49) - ML/AI patterns (port 5561)

**Signal Flow**:
```
Elite Guard → Port 5557 ─┐
Pulse v3 → Port 5559 ────├─→ Generator Merger (5564) → Clean Relay → API
APEX Sentinel → Port 5561 ┘
```

## Why Only v3?

**Pulse Scalper v3 Improvements**:
- Relaxed pattern detection (2-bar confluence window)
- More realistic RSI thresholds (40/60 vs 30/70)
- Multi-timeframe validation (M5 instead of M1)
- Better volume confirmation (1.3x surge requirement)
- Enhanced risk/reward validation (1:1.5 minimum)

**v2 Issues**:
- Too strict pattern detection (same-bar confluence)
- Minimal signal generation on M1 timeframe
- Less sophisticated risk/reward analysis

## Future Actions

**If v2 Needed Again**:
1. Restore file: `mv /root/pulse_scalper_v2_ARCHIVED_OCT21_2025.py /root/pulse_scalper.py`
2. Start process: `pm2 start pulse_scalper`
3. Save state: `pm2 save`

**Current Recommendation**: Keep only v3 running, monitor performance

## Monitoring Commands

**Check Active Pulse Generator**:
```bash
pm2 list | grep pulse
pm2 logs pulse_scalper_v3 --lines 50
```

**Check Signal Generation**:
```bash
sqlite3 /root/HydraX-v2/bitten.db "
SELECT COUNT(*) as pulse_signals
FROM signals
WHERE pattern_type LIKE '%PULSE%'
AND created_at > strftime('%s', 'now', '-24 hours');
"
```

**Check Latest Pulse Signal**:
```bash
sqlite3 /root/HydraX-v2/bitten.db "
SELECT signal_id, symbol, confidence, created_at
FROM signals
WHERE pattern_type LIKE '%PULSE%'
ORDER BY created_at DESC
LIMIT 1;
"
```

---

**Date**: October 21, 2025 05:30 UTC
**Status**: ✅ COMPLETE - Pulse Scalper v2 archived, v3 running solo
**Next Review**: Monitor v3 signal generation and win rate
