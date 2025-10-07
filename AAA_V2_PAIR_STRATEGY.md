# AAA v2.0 Pair Selection Strategy

## 🎯 The Smart Approach: Quality over Quantity

### Current Options:

#### Option 1: All 12 Pairs All The Time ❌

**Problems:**

- Some pairs too erratic for our filters (GBPJPY spikes)
- Some pairs too slow (EURGBP ranges)
- Dilutes focus and quality
- One-size-fits-all doesn't work

#### Option 2: Dynamic 8-Pair Focus ✅

**Benefits:**

- Focus on best performers
- Session-specific optimization
- Better quality control
- Same 15-20 signals/day target

## 📊 Recommended Strategy

### Session-Based Selection:

```
Asian (0:00-8:00 UTC):
- Focus: USDJPY, EURJPY, GBPJPY, AUDJPY
- Why: JPY pairs most active, your test showed 95% win rate

London (8:00-16:00 UTC):
- Focus: EURUSD, GBPUSD, EURGBP, EURJPY
- Why: EUR/GBP pairs have best liquidity

New York (13:00-21:00 UTC):
- Focus: EURUSD, GBPUSD, USDJPY, USDCAD
- Why: USD pairs most liquid
```

### Pair Characteristics:

**Best for Our Filters:**

- EURUSD: Smooth, technical, high liquidity ✅
- USDJPY: Trends well, 95% win rate in test ✅
- GBPUSD: Good volatility, clear patterns ✅
- EURJPY: Combines EUR stability + JPY trends ✅

**Use Carefully:**

- GBPJPY: 200+ pip daily moves, needs wider stops ⚠️
- AUDJPY: Commodity correlation adds complexity ⚠️
- NZDUSD: Lower liquidity, bigger spreads ⚠️

**Avoid During News:**

- USDCAD: Oil price sensitive ❌
- AUDUSD: China data sensitive ❌

## 💡 Implementation Options

### Conservative (Recommended):

- Scan top 8 pairs based on session
- 78% RAPID / 82% SNIPER thresholds
- Expected: 15 signals/day at 70%+ quality

### Moderate:

- Scan all 12 but only trade top 8 by performance
- Track weekly win rates, rotate bottom 2
- Expected: 18 signals/day at 65%+ quality

### Aggressive:

- Scan all 12 all the time
- 77% RAPID / 80% SNIPER thresholds
- Expected: 20-25 signals/day at 60%+ quality

## 📈 Why This Works

1. **Quality Focus**: Better to master 8 pairs than be mediocre at 12
2. **Session Alignment**: Trade pairs when they're most active
3. **Proven Winners**: Your test showed JPY pairs excel
4. **Adaptability**: Can adjust based on performance

## 🔧 Settings for Best Results

```python
# For 8-pair focus
'thresholds': {
    'rapid_tcs': 78,      # Perfect balance
    'sniper_tcs': 82,     # Quality focus
}

# For 12-pair scanning
'thresholds': {
    'rapid_tcs': 79,      # Slightly higher for quality
    'sniper_tcs': 83,     # More selective
}
```

## Bottom Line

**Recommended**: Focus on 8 best pairs per session rather than diluting with all 12. This maintains accuracy while achieving your 15-20 signals/day target.
