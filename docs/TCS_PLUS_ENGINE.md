# TCS++ Engine Documentation

## Overview

The TCS++ (Trade Confidence Score Plus Plus) engine is a comprehensive multi-factor scoring system that evaluates trading opportunities across 8 key dimensions, producing a score from 0-100 points.

## Scoring Components

### 1. Market Structure Analysis (20 points max)
- **Trend Clarity** (0-8 points)
  - > 0.7: 8 points (strong trend)
  - > 0.5: 6 points (moderate trend)
  - > 0.3: 3 points (weak trend)

- **Support/Resistance Quality** (0-7 points)
  - > 0.8: 7 points (strong levels)
  - > 0.6: 5 points (moderate levels)
  - > 0.4: 3 points (weak levels)

- **Pattern Completion** (0-5 points)
  - Complete pattern: 5 points
  - Forming pattern: 3 points

### 2. Timeframe Alignment (15 points max)
- M15 aligned: 2 points
- H1 aligned: 4 points
- H4 aligned: 5 points
- D1 aligned: 4 points
- Perfect alignment bonus: 15 points total

### 3. Momentum Assessment (15 points max)
- **RSI Momentum** (0-5 points)
  - 25-35 or 65-75: 5 points (strong momentum)
  - 35-45 or 55-65: 3 points (good momentum)
  - 45-55: 2 points (neutral)

- **MACD** (0-5 points)
  - Aligned: 5 points
  - Divergence: 3 points

- **Volume Confirmation** (0-5 points)
  - > 1.5x average: 5 points
  - > 1.2x average: 3 points
  - > 1.0x average: 1 point

### 4. Volatility Analysis (10 points max)
- **ATR Range** (0-5 points)
  - 15-50 pips: 5 points (optimal)
  - 10-15 or 50-80 pips: 3 points

- **Spread Conditions** (0-3 points)
  - < 1.5x normal: 3 points
  - < 2.0x normal: 1 point

- **Volatility Stability** (0-2 points)
  - Stable conditions: 2 points

### 5. Session Weighting (10 points max)
- London: 10 points
- New York: 9 points
- Overlap: 8 points
- Tokyo: 6 points
- Sydney: 5 points
- Dead Zone: 2 points

### 6. Liquidity Patterns (10 points max)
- Liquidity grab detected: 5 points
- Stop hunt detected: 3 points
- Near institutional level: 2 points

### 7. Risk/Reward Quality (10 points max)
- RR >= 4.0: 10 points
- RR >= 3.5: 9 points
- RR >= 3.0: 8 points
- RR >= 2.5: 6 points
- RR >= 2.0: 4 points
- RR >= 1.5: 2 points

### 8. AI Sentiment Bonus (10 points max)
- Additional points based on AI analysis
- Capped at 10 points maximum

## Trade Classifications

Based on TCS score and risk/reward ratio:

### Hammer Trades (94+ TCS, 3.5+ RR)
- **hammer_elite**: Top 1% setups with momentum > 0.8 and structure > 0.9
- **hammer**: Standard elite setups

### Shadow Strike Trades (84-93 TCS)
- **shadow_strike_premium**: RR >= 3.0
- **shadow_strike**: Standard high probability trades

### Scalp Trades (75-83 TCS)
- **scalp_session**: Optimized for London/NY sessions
- **scalp**: Quick opportunity trades

### Watchlist Trades (65-74 TCS)
- Monitor but don't execute
- Wait for better conditions

### No Trade (< 65 TCS)
- Below minimum threshold
- Conditions not favorable

## Integration with Fire Modes

The TCS++ engine integrates seamlessly with the fire mode validation system:

- **Single Shot**: Requires minimum TCS based on tier
- **Chaingun**: Progressive TCS requirements (85, 87, 89, 91)
- **Auto-Fire**: Requires 91+ TCS
- **Semi-Auto**: Requires 75+ TCS
- **Midnight Hammer**: Requires 95+ TCS

## Usage Example

```python
from core.tcs_engine import score_tcs, classify_trade

signal_data = {
    "trend_clarity": 0.8,
    "sr_quality": 0.85,
    "pattern_complete": True,
    "H1_aligned": True,
    "H4_aligned": True,
    "rsi": 32,
    "macd_aligned": True,
    "volume_ratio": 1.6,
    "atr": 30,
    "spread_ratio": 1.3,
    "session": "london",
    "liquidity_grab": True,
    "rr": 3.5,
    "ai_sentiment_bonus": 5
}

# Calculate TCS score
score = score_tcs(signal_data)
trade_type = classify_trade(score, signal_data["rr"], signal_data)

print(f"TCS Score: {score}%")
print(f"Trade Type: {trade_type}")
print(f"Breakdown: {signal_data['tcs_breakdown']}")
```

## Benefits

1. **Transparency**: Full breakdown of scoring components
2. **Flexibility**: Easy to adjust weights and thresholds
3. **Comprehensive**: Evaluates all critical trading factors
4. **Integration**: Works seamlessly with existing systems
5. **Classification**: Clear trade type identification

The TCS++ engine provides a robust, transparent, and comprehensive scoring system that ensures only high-quality trades are executed while maintaining clear standards for different trading styles and risk profiles.