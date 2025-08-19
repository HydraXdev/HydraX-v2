# MONDAY EXPANSION PLAN - BITTEN ML SYSTEM

**Created**: August 15, 2025  
**Purpose**: Quick reference for expanding to additional pairs after Sunday testing

## CURRENT CONFIGURATION (SUNDAY TESTING)

### Active Pairs (Tier 1 - Auto-Fire)
- **EURUSD**: 80% threshold, max 3/hour
- **GBPUSD**: 80% threshold, max 2/hour

### Settings
- **R:R Ratio**: 1:1.25 (quick profits)
- **Pattern Filter**: 72% minimum
- **Auto-Fire**: 80% confidence minimum
- **Sessions**: LONDON, OVERLAP, NY active

## MONDAY EXPANSION OPTIONS

### 1. Add More Pairs to Tier 2 (Testing Only)
```python
# In elite_guard_with_citadel.py, add to TIER_2_TESTING:
'USDJPY_VCB_BREAKOUT_LONDON': {'confidence_min': 85, 'auto_fire': False},
'EURJPY_VCB_BREAKOUT_LONDON': {'confidence_min': 85, 'auto_fire': False},
'USDCAD_VCB_BREAKOUT_LONDON': {'confidence_min': 87, 'auto_fire': False},
```

### 2. Promote Winners to Tier 1
After analyzing Sunday data, if a pair/pattern combo shows >60% win rate:
```python
# Move from TIER_2 to TIER_1:
'USDJPY_VCB_BREAKOUT_LONDON': {'confidence_min': 82, 'auto_fire': True, 'max_hourly': 2},
```

### 3. Adjust Thresholds Based on Data
```bash
# Check Sunday performance
sqlite3 /root/HydraX-v2/bitten.db "
SELECT symbol, COUNT(*) as trades, 
       SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END) as wins,
       ROUND(100.0 * SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
FROM fires 
WHERE created_at > strftime('%s', 'now', '-2 days')
GROUP BY symbol;"
```

## ANALYSIS COMMANDS

### Check Pattern Performance
```bash
# View pattern win rates
cat /root/HydraX-v2/ml_performance_tracking.jsonl | \
jq -s 'group_by(.pattern) | 
  map({pattern: .[0].pattern, 
       trades: length, 
       wins: [.[] | select(.outcome=="WIN")] | length,
       win_rate: (([.[] | select(.outcome=="WIN")] | length) / length * 100)
      })'
```

### Check Session Performance
```bash
# View session win rates
cat /root/HydraX-v2/ml_performance_tracking.jsonl | \
jq -s 'group_by(.session) | 
  map({session: .[0].session, 
       trades: length,
       avg_runtime: ([.[].runtime_minutes] | add / length),
       win_rate: (([.[] | select(.outcome=="WIN")] | length) / length * 100)
      })'
```

### Check Confidence Correlation
```bash
# See if higher confidence = higher win rate
cat /root/HydraX-v2/ml_performance_tracking.jsonl | \
jq -s '[.[] | {conf_bucket: ((.confidence // 0) / 10 | floor * 10), outcome}] |
  group_by(.conf_bucket) |
  map({confidence: .[0].conf_bucket, 
       trades: length,
       win_rate: (([.[] | select(.outcome=="WIN")] | length) / length * 100)
      })'
```

## EXPANSION DECISION TREE

1. **If Sunday shows 60%+ win rate**: Keep current settings, add more pairs
2. **If Sunday shows 40-60% win rate**: Tighten thresholds to 85%
3. **If Sunday shows <40% win rate**: Raise thresholds to 90%, reduce pairs

## FILES TO MODIFY FOR EXPANSION

1. **Elite Guard Tiers**: `/root/HydraX-v2/elite_guard_with_citadel.py` (line 72-112)
2. **ML Filter Pairs**: `/root/HydraX-v2/ml_signal_filter.py` (line 34)
3. **Auto-Fire Threshold**: `/root/HydraX-v2/ml_signal_filter.py` (line 39)

## MONITORING DURING EXPANSION

```bash
# Real-time monitoring
watch -n 10 'echo "=== LAST HOUR STATS ===" && \
  sqlite3 /root/HydraX-v2/bitten.db "
  SELECT symbol, COUNT(*) as fires, 
         SUM(CASE WHEN status=\"WIN\" THEN 1 ELSE 0 END) as wins
  FROM fires 
  WHERE created_at > strftime(\"%s\", \"now\", \"-1 hour\")
  GROUP BY symbol;"'
```

## ROLLBACK IF NEEDED

If new pairs perform poorly:
```bash
# Restore Sunday config
cp /root/HydraX-v2/elite_guard_with_citadel_backup_20250815_*.py \
   /root/HydraX-v2/elite_guard_with_citadel.py
pm2 restart elite_guard
```

## SUCCESS METRICS

Target for Monday expansion:
- **Win Rate**: >55% across all pairs
- **Signals/Hour**: 3-5 during active sessions
- **Average Runtime**: <45 minutes to outcome
- **Risk/Reward Achievement**: 60%+ reaching full TP

## NOTES

- ML system will auto-adjust after 10 trades per pattern
- Patterns below 40% win rate auto-disable
- Keep XAUUSD in Tier 3 (probation) due to volatility
- ASIAN session stays high threshold (94%) due to low liquidity