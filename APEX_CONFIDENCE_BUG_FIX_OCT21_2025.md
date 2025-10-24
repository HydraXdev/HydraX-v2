# APEX Confidence Scoring Bug - October 21, 2025

## Critical Issue Summary

**User Report**: "too many 100 percent and loosing"
**APEX Win Rate**: 31.4% (expected 68%) ❌
**Average Confidence**: 92.6% (massively inflated)
**100% Confidence Signals**: 13 out of last 20 signals
**100% Confidence Win Rate**: 15% (2 wins / 13 signals)

## Root Causes

### 1. ML Model Architecture Too Simple

**File**: `/root/apex_sentinel.py` (lines 63-70)

```python
class SimpleNet(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.fc = nn.Linear(input_size, 1)  # Single linear layer!
        self.sigmoid = nn.Sigmoid()
```

**Problem**: This is just logistic regression - way too simple for forex pattern recognition.
**Result**: Model overfits badly on minimal training data.

### 2. No Model Persistence

**Evidence**:
```bash
ls -lh /root/HydraX-v2/apex_*.pkl
# Output: No APEX model files found
```

**Problem**: Model retrains from scratch on every restart with minimal candles.
**Result**: Unstable predictions, no learning persistence.

### 3. Confidence Inflation Pipeline

**Step 1** - Base ML Probability (line 397):
```python
confidence = min(proba * 100, 95)  # Cap at 95%
```

**Step 2** - Memory-Lite Boost (lines 565-574):
```python
# Memory-Lite can boost by up to +5%
adjusted_conf = min(100, confidence + boost)
```

**Result**: 95% + 5% boost = 100% confidence signals that lose!

### 4. AUDUSD Specific Issue

**AUDUSD Signals (Last 20)**:
- 100% confidence: 8 signals
- Win Rate: 0% (0 wins, 8 losses!)

**Hypothesis**: ML model completely mislearned AUDUSD patterns due to insufficient training data or bad feature engineering.

## Performance Data (Last 7 Days)

```sql
SELECT
    pattern_type,
    COUNT(*) as total,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
    AVG(confidence) as avg_conf
FROM signals
WHERE pattern_type = 'APEX_ENGULFING'
AND created_at > strftime('%s', 'now', '-7 days')
AND outcome IN ('WIN', 'LOSS');
```

**Results**:
- Total: 86 signals
- Wins: 27
- Losses: 59
- Win Rate: **31.4%** (target was 68%!)
- Avg Confidence: **92.6%**

## Immediate Actions Taken

### 1. Stopped APEX Sentinel

```bash
pm2 stop apex_sentinel
```

**Reason**: Prevent further losses with 31% win rate.

### 2. Analysis of Recent Signals

```sql
SELECT signal_id, symbol, confidence, outcome
FROM signals
WHERE pattern_type LIKE '%ENGULFING%'
AND created_at > strftime('%s', 'now', '-48 hours')
ORDER BY created_at DESC
LIMIT 20;
```

**Findings**:
- 20 signals in last 48 hours
- 4 wins, 16 losses (20% win rate)
- 13 signals at 100% confidence (15% win rate)

## Proposed Fixes

### Fix 1: Lower Base Confidence Cap

**File**: `/root/apex_sentinel.py` (line 397)

**BEFORE**:
```python
confidence = min(proba * 100, 95)  # Cap at 95%
```

**AFTER**:
```python
confidence = min(proba * 100, 75)  # Cap at 75% until model proven
```

**Rationale**: With 31% win rate, model is clearly not calibrated. Lower cap prevents false confidence.

### Fix 2: Disable Memory-Lite Boost for APEX

**File**: `/root/apex_sentinel.py` (lines 565-574)

**BEFORE**:
```python
if signal and 'direction' in signal and 'confidence' in signal:
    should_fire, adj_conf, memory_reason = memory_system.should_fire(
        df, symbol, signal['direction'], signal['confidence']
    )
    if not should_fire:
        signal = None
    elif adj_conf != signal['confidence']:
        signal['confidence'] = adj_conf  # Apply boost
```

**AFTER**:
```python
if signal and 'direction' in signal and 'confidence' in signal:
    should_fire, adj_conf, memory_reason = memory_system.should_fire(
        df, symbol, signal['direction'], signal['confidence']
    )
    if not should_fire:
        signal = None  # Still filter bad signals
    # DO NOT apply confidence boost - model needs recalibration
```

### Fix 3: Add Model Performance Validation

**New Function** (add to apex_sentinel.py):
```python
def validate_model_performance(df: pd.DataFrame, model, mean, std, min_win_rate=0.55):
    """
    Validate model on recent candles before using it.

    Returns:
        (is_valid, win_rate, total_signals)
    """
    if len(df) < 200:
        return False, 0, 0

    # Test on last 100 candles
    test_candles = df.iloc[-100:]
    predictions = []
    actuals = []

    for i in range(len(test_candles) - 10):
        signal = generate_signal(test_candles.iloc[:i+1], model, mean, std, "TEST")
        if signal:
            # Check if TP was hit in next 10 candles
            entry = signal['entry']
            tp = signal['tp']
            sl = signal['sl']

            future_candles = test_candles.iloc[i+1:i+11]
            hit_tp = (future_candles['high'] >= tp).any() if signal['direction'] == 'BUY' else (future_candles['low'] <= tp).any()
            hit_sl = (future_candles['low'] <= sl).any() if signal['direction'] == 'BUY' else (future_candles['high'] >= sl).any()

            if hit_tp and not hit_sl:
                actuals.append(1)
            elif hit_sl:
                actuals.append(0)
            else:
                continue  # Skip inconclusive

            predictions.append(1)

    if len(actuals) < 10:
        return False, 0, 0

    win_rate = sum(actuals) / len(actuals)
    return win_rate >= min_win_rate, win_rate, len(actuals)
```

### Fix 4: Model Persistence

**Add to apex_sentinel.py** (after training):
```python
import pickle

def save_model(symbol, model, mean, std):
    """Save trained model to disk."""
    model_path = f"/root/HydraX-v2/apex_models/{symbol}_apex.pkl"
    os.makedirs("/root/HydraX-v2/apex_models", exist_ok=True)

    with open(model_path, 'wb') as f:
        pickle.dump({
            'model_state': model.state_dict(),
            'mean': mean,
            'std': std,
            'timestamp': time.time()
        }, f)

    logger.info(f"✅ Saved {symbol} model to {model_path}")

def load_model(symbol, input_size):
    """Load trained model from disk."""
    model_path = f"/root/HydraX-v2/apex_models/{symbol}_apex.pkl"

    if not os.path.exists(model_path):
        return None

    with open(model_path, 'rb') as f:
        data = pickle.load(f)

    model = SimpleNet(input_size)
    model.load_state_dict(data['model_state'])
    model.eval()

    logger.info(f"✅ Loaded {symbol} model from {model_path}")
    return model, data['mean'], data['std']
```

### Fix 5: Better ML Model Architecture

**Long-term fix** (not urgent):
```python
class ImprovedNet(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 16)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        return self.sigmoid(self.fc3(x))
```

## Deployment Plan

### Phase 1: Emergency Fixes (Immediate)

1. ✅ **Stop APEX** - Already done
2. **Lower confidence cap** - 95% → 75%
3. **Disable Memory-Lite boost** - Keep filtering but no confidence boost
4. **Add model validation** - Check 55%+ win rate before deployment
5. **Add model persistence** - Save/load models instead of retraining

**Files to modify**:
- `/root/apex_sentinel.py` (lines 397, 565-574, add validation function)

### Phase 2: Testing (Before Restart)

1. **Retrain models with validation**:
   ```bash
   # Restart APEX, let it train on current candle cache
   pm2 restart apex_sentinel

   # Monitor logs for validation results
   pm2 logs apex_sentinel --lines 50 | grep -E "validation|win_rate"
   ```

2. **Wait for model validation to pass** (55%+ win rate on test data)

3. **Monitor first 10 signals** without auto-fire:
   - Check confidence distribution
   - Verify no 100% signals
   - Track outcomes manually

### Phase 3: Gradual Rollout

1. **Week 1**: APEX signals visible but no auto-fire
2. **Week 2**: Enable auto-fire at 85%+ confidence only (if week 1 shows 55%+ win rate)
3. **Week 3**: Lower threshold to 80% if performance holds
4. **Week 4**: Full deployment with 75%+ threshold

## Monitoring Commands

**Check APEX win rate**:
```bash
sqlite3 /root/HydraX-v2/bitten.db "
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
    AVG(confidence) as avg_conf
FROM signals
WHERE pattern_type = 'APEX_ENGULFING'
AND created_at > strftime('%s', 'now', '-24 hours')
AND outcome IN ('WIN', 'LOSS');
"
```

**Check confidence distribution**:
```bash
sqlite3 /root/HydraX-v2/bitten.db "
SELECT
    CASE
        WHEN confidence >= 95 THEN '95-100%'
        WHEN confidence >= 85 THEN '85-95%'
        WHEN confidence >= 75 THEN '75-85%'
        ELSE '<75%'
    END as conf_bucket,
    COUNT(*) as count,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
FROM signals
WHERE pattern_type = 'APEX_ENGULFING'
AND created_at > strftime('%s', 'now', '-7 days')
AND outcome IN ('WIN', 'LOSS')
GROUP BY conf_bucket
ORDER BY conf_bucket DESC;
"
```

## Lessons Learned

1. **Never trust ML without validation** - 31% win rate vs 68% expected is catastrophic
2. **Confidence != Win Rate** - High confidence with low win rate is worse than no signal
3. **Simple models can overfit** - Single linear layer is not enough
4. **Always persist models** - Retraining from scratch on every restart is unstable
5. **Test before deploy** - Should have validated on historical data first

## Current Status

**APEX Sentinel**: ✅ STOPPED (PM2 ID 49)
**Relay**: ✅ STOPPED (PM2 ID 50)
**Active Generators**: Elite Guard (port 5557), Pulse Scalper (port 5559)

**Next Steps**:
1. Apply Phase 1 fixes
2. Test with validation
3. Monitor performance for 1 week before enabling auto-fire

---

**Date**: October 21, 2025 04:29 UTC
**Status**: ✅ APEX STOPPED - Awaiting fixes before restart
**Win Rate**: 31.4% (needs to reach 55%+ before re-enabling)
