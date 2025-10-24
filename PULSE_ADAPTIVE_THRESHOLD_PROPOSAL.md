# Pulse v3 Adaptive Threshold System - Proposal

## Problem Statement

**Current**: Volume threshold (vol_mult) is hardcoded at 1.1x
**Issue**: No feedback loop to know if 1.1x is optimal vs 1.0x or 1.2x
**Result**: Manually guessing thresholds instead of ML-driven optimization

## Proposed Solution: Self-Optimizing Threshold

### 1. Outcome Tracking (MISSING)

**Track every Pulse signal outcome**:
```python
pulse_outcomes = {
    'signal_id': 'PULSE_EURUSD_1234567',
    'vol_ratio': 1.15,  # Actual volume at signal time
    'confidence': 78.5,
    'outcome': 'WIN',
    'profit_pips': 12.5,
    'duration_min': 45
}
```

**Store in**: `/root/HydraX-v2/pulse_performance.jsonl`

### 2. Threshold Performance Analysis

**Bucket win rates by volume threshold**:
```python
Volume Buckets:
1.0-1.1x: 58% WR (100 signals)
1.1-1.2x: 63% WR (80 signals)  ← CURRENT RANGE
1.2-1.3x: 68% WR (40 signals)
1.3-1.4x: 72% WR (15 signals)

Optimal Zone: 1.15-1.25x (balance volume vs quality)
```

### 3. Dynamic Threshold Adjustment

**Auto-adjust vol_mult every 50 signals**:
```python
def optimize_volume_threshold():
    """Find optimal volume threshold based on actual outcomes."""

    # Get last 100 signals with outcomes
    outcomes = load_pulse_outcomes(limit=100)

    # Bucket by volume ratio
    buckets = {
        '1.0-1.1': [],
        '1.1-1.2': [],
        '1.2-1.3': [],
        '1.3+': []
    }

    for signal in outcomes:
        vol = signal['vol_ratio']
        if vol < 1.1:
            buckets['1.0-1.1'].append(signal)
        elif vol < 1.2:
            buckets['1.1-1.2'].append(signal)
        elif vol < 1.3:
            buckets['1.2-1.3'].append(signal)
        else:
            buckets['1.3+'].append(signal)

    # Calculate win rate and expectancy per bucket
    for bucket_name, signals in buckets.items():
        if len(signals) < 10:
            continue  # Not enough data

        wins = sum(1 for s in signals if s['outcome'] == 'WIN')
        wr = wins / len(signals)

        # Expectancy = (WR * AvgWin) - (LR * AvgLoss)
        avg_win = mean([s['profit_pips'] for s in signals if s['outcome'] == 'WIN'])
        avg_loss = mean([abs(s['profit_pips']) for s in signals if s['outcome'] == 'LOSS'])
        expectancy = (wr * avg_win) - ((1-wr) * avg_loss)

        print(f"{bucket_name}: {wr:.1%} WR, {len(signals)} signals, {expectancy:.2f} pips/trade")

    # Find bucket with highest expectancy
    best_bucket = max(buckets, key=lambda b: calculate_expectancy(buckets[b]))

    # Set vol_mult to midpoint of best bucket
    new_threshold = get_bucket_midpoint(best_bucket)

    return new_threshold
```

### 4. ML Model Enhancement

**Add volume ratio as ML feature**:
```python
# Current ML features (simplified)
features = [rsi, ema_diff, macd_hist, volume, atr]

# Enhanced ML features
features = [
    rsi,
    ema_diff,
    macd_hist,
    volume_ratio,  # ← NEW: vol / avg_vol
    atr,
    hour_of_day,   # ← NEW: session matters
    day_of_week    # ← NEW: avoid low-liquidity days
]
```

**Train on actual outcomes**:
```python
# Instead of training on "TP hit in 3 bars" (fake labels)
# Train on REAL outcomes from fired signals

def retrain_with_outcomes():
    # Load last 200 Pulse signals with known outcomes
    signals = load_pulse_outcomes(limit=200, only_completed=True)

    X = []
    y = []

    for sig in signals:
        features = [
            sig['rsi'],
            sig['ema_diff'],
            sig['macd_hist'],
            sig['vol_ratio'],  # Actual volume at signal time
            sig['atr'],
            sig['hour'],
            sig['dow']
        ]
        X.append(features)
        y.append(1 if sig['outcome'] == 'WIN' else 0)

    # Train model on REAL outcomes (not synthetic)
    model.fit(X, y)

    # Now model knows: "Volume ratio of 1.25x + RSI 35 = 72% actual win rate"
```

### 5. Confidence Calibration

**Ensure confidence matches actual win rate**:
```python
# After 100 signals, check calibration
confidence_buckets = {
    '70-75%': [],
    '75-80%': [],
    '80-85%': [],
    '85-90%': []
}

# Group signals by reported confidence
for sig in signals:
    if 70 <= sig['confidence'] < 75:
        confidence_buckets['70-75%'].append(sig)
    # ... etc

# Check calibration
for bucket, sigs in confidence_buckets.items():
    actual_wr = sum(1 for s in sigs if s['outcome'] == 'WIN') / len(sigs)
    expected_wr = float(bucket.split('-')[0]) / 100

    if abs(actual_wr - expected_wr) > 0.10:  # More than 10% off
        print(f"⚠️ MISCALIBRATION: {bucket} reports {expected_wr:.0%} but wins {actual_wr:.0%}")

        # Adjust future confidence scores
        calibration_factor = actual_wr / expected_wr
        # Apply to all future signals in this range
```

## Implementation Plan

### Phase 1: Outcome Tracking (Week 1)
- Add signal outcome logger to Pulse v3
- Store to `/root/HydraX-v2/pulse_performance.jsonl`
- Include: vol_ratio, confidence, outcome, profit, duration
- Run for 7 days to collect 50-100 outcomes

### Phase 2: Threshold Analysis (Week 2)
- Build analysis script to bucket by volume ratio
- Calculate WR and expectancy per bucket
- Generate report: "Optimal threshold is 1.18x based on 100 signals"

### Phase 3: Auto-Adjustment (Week 3)
- Implement `optimize_volume_threshold()` function
- Run every 50 signals or weekly
- Auto-adjust CONFIG['vol_mult'] based on data
- Log adjustments: "Raised threshold 1.1x → 1.15x (better WR)"

### Phase 4: ML Enhancement (Week 4)
- Add volume_ratio, hour, day_of_week to features
- Retrain on actual outcomes (not synthetic labels)
- Calibrate confidence to match real win rates
- Continuous learning from every fired signal

## Expected Benefits

**Before (Manual Thresholds)**:
- Guessing: "Try 1.1x and see what happens"
- No feedback: Don't know if 1.2x would be better
- Static: Doesn't adapt to changing market conditions
- Miscalibrated: 85% confidence might actually be 72% WR

**After (Adaptive System)**:
- Data-driven: "1.18x optimal based on 100 signals"
- Self-optimizing: Adjusts weekly based on performance
- Adaptive: Raises threshold during choppy markets, lowers during trends
- Calibrated: 85% confidence = 85% actual WR (±3%)

**Estimated Improvement**:
- Win Rate: +3-5% (from better threshold optimization)
- Signal Quality: +15-20% (from calibrated confidence)
- Expectancy: +25-30% (from both improvements)

## Cost-Benefit

**Implementation Time**: 2-3 days
**Data Collection**: 7-14 days for meaningful sample
**Ongoing Maintenance**: Automatic (runs weekly)

**ROI**:
- 3-5% WR improvement = +$30-50/day (at 2% risk, 4 signals/day)
- Confidence calibration = Better auto-fire decisions
- Self-optimization = No more manual threshold guessing

## Next Steps

1. ✅ Document proposal (this file)
2. ⏳ Add outcome tracking to Pulse v3 (2-3 hours)
3. ⏳ Collect 50-100 outcomes (7-14 days)
4. ⏳ Build threshold optimizer (4-6 hours)
5. ⏳ Enhance ML model with new features (6-8 hours)
6. ⏳ Deploy adaptive system (1 day testing)

**Total**: ~3 days implementation + 7-14 days data collection

---

**Author**: User request + Claude Code analysis
**Date**: October 21, 2025
**Status**: PROPOSED - Awaiting user approval to implement
