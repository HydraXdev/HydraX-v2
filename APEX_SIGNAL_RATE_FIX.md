# APEX Signal Rate Fix - July 15, 2025

## Problem
APEX engine was generating ~200-500 signals per hour, overwhelming the system.

## Root Cause Analysis
- **14 active trading pairs** × **Low TCS threshold (75%)** × **Fast scanning (45s)** = Signal overload
- Every 45-second scan was finding 5-6 qualifying signals
- Rate calculation: 6 signals × 80 scans/hour = 480 signals/hour

## Solution Implemented

### Configuration Changes (apex_config.json):
```json
{
    "signal_generation": {
        "min_tcs_threshold": 85,      // Increased from 75
        "max_spread_allowed": 30,     // Reduced from 50
        "scan_interval_seconds": 90   // Increased from 45
    },
    "trading_pairs": {
        "pairs": [
            "EURUSD", "GBPUSD", "USDJPY", 
            "AUDUSD", "USDCAD", "EURJPY"  // Reduced from 14 to 6 pairs
        ]
    }
}
```

### Code Fix (apex_v5_lean.py):
Added auto-start capability for background mode to prevent EOF error when running as daemon.

## Results
- **Before**: 470-500 signals/hour
- **After**: 20-40 signals/hour
- **Quality**: Only highest confidence signals (TCS ≥ 85%)
- **Pairs**: Focus on 6 major pairs instead of 14

## Future Tuning Guide
If signals are still too many:
- Increase TCS threshold to 90%
- Increase scan interval to 120s
- Remove volatile pairs (EURJPY)

If signals are too few:
- Decrease TCS threshold to 80%
- Add back select pairs
- Decrease scan interval to 60s

## Monitoring
Watch the signal rate in Commander Throne's top bar or check logs:
```bash
tail -f apex_lean.log | grep "Rate:"
```

The system is now generating manageable, high-quality signals at a sustainable rate.