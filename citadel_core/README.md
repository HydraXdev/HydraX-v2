# 🏰 CITADEL Shield System

**Intelligent Signal Protection & Education Platform for BITTEN**

CITADEL transforms signal filtering from restriction to protection, showing ALL signals while intelligently scoring and tagging them. This creates trust, transparency, and teaches users to think like institutions.

## 🎯 Core Philosophy

- **Show Everything**: All 20-25 daily signals visible (no FOMO)
- **Guide Intelligently**: Clear visual hierarchy with shield status
- **Teach Through Transparency**: Every score is explainable
- **Evolve Continuously**: Real-time updates as conditions change

## 📊 System Architecture

```
VENOM Signal → CITADEL Analysis → Shield Scoring → Enhanced Display → User Decision
     ↓              ↓                  ↓                ↓               ↓
  Raw Signal    7 Modules         Score + Tag      Telegram/HUD    Protected Trade
```

## 🛡️ Shield Classifications

| Classification | Score Range | Emoji | Meaning |
|----------------|-------------|-------|---------|
| SHIELD APPROVED | 8.0 - 10.0 | 🛡️ | High-confidence institutional setup |
| SHIELD ACTIVE | 6.0 - 7.9 | ✅ | Good setup with minor cautions |
| VOLATILITY ZONE | 4.0 - 5.9 | ⚠️ | Trade with caution |
| UNVERIFIED | 0.0 - 3.9 | 🔍 | Lacks confirmation |

## 🔧 Quick Integration

### 1. Install CITADEL

```bash
cd /root/HydraX-v2
# CITADEL is already installed in citadel_core/
```

### 2. Enhance VENOM Signals

In `apex_venom_v7_unfiltered.py`:

```python
from citadel_core.bitten_integration import enhance_signal_with_citadel

# After generating signal
signal = self.generate_venom_signal(pair, timestamp)
signal = enhance_signal_with_citadel(signal)  # Add CITADEL analysis
```

### 3. Update Bot Messages

In `bitten_production_bot.py`:

```python
from citadel_core.bitten_integration import format_mission_with_citadel

# In generate_mission method
mission_text = self._format_mission_briefing(signal)
mission_text = format_mission_with_citadel(signal, mission_text)
```

### 4. Add to WebApp HUD

In `webapp_server_optimized.py`:

```python
from citadel_core.bitten_integration import get_citadel_shield_data

# In HUD endpoint
shield_data = get_citadel_shield_data(signal_id)
response['shield'] = shield_data
```

## 📦 Module Overview

### Analyzers
- **signal_inspector.py** - Classifies signal type (breakout, reversal, etc.)
- **market_regime.py** - Detects market conditions (trending, ranging, volatile)
- **liquidity_mapper.py** - Identifies sweeps, traps, and order blocks
- **cross_tf_validator.py** - Validates alignment across M5/M15/H1/H4

### Scoring
- **shield_engine.py** - Core scoring algorithm (0-10 scale)

### Storage
- **shield_logger.py** - Performance tracking and analytics

### Formatting
- **telegram_formatter.py** - Beautiful Telegram message formatting

### Integration
- **citadel_analyzer.py** - Main orchestrator
- **bitten_integration.py** - Easy integration helpers

## 🎮 Signal Display Examples

### Before CITADEL
```
📍 EUR/USD SELL @ 1.0892
🎯 TP: 1.0852 | SL: 1.0912
```

### After CITADEL
```
📍 EUR/USD SELL @ 1.0892
🎯 TP: 1.0852 | SL: 1.0912
🛡️ SHIELD APPROVED [8.4/10]
✓ Post-sweep reversal confirmed
✓ Multi-TF alignment (M15/H1/H4)
⚠️ ECB speech in 2h (minor risk)
```

## 📈 Performance Tracking

CITADEL tracks all shield decisions and outcomes:

```python
from citadel_core.citadel_analyzer import get_citadel_analyzer

citadel = get_citadel_analyzer()

# Get performance report
report = citadel.get_performance_report(days=30)

# Get user-specific stats
user_stats = citadel.get_user_stats(user_id=12345)

# Log trade outcome
citadel.log_trade_outcome(
    signal_id='VENOM_EURUSD_001',
    user_id=12345,
    outcome='WIN',
    pips_result=25.5,
    followed_shield=True
)
```

## 🧠 Scoring Algorithm

The shield score (0-10) is calculated from multiple components:

### Positive Factors
- ✅ Liquidity sweep detected (+2.0)
- ✅ Multi-timeframe alignment (+1.5)
- ✅ Trend continuation (+1.0)
- ✅ Key level confluence (+1.0)
- ✅ Optimal session timing (+0.5)

### Negative Factors
- ❌ High-impact news nearby (-2.0)
- ❌ Trap probability high (-2.5)
- ❌ Extreme volatility (-1.5)
- ❌ Timeframe conflicts (-1.0)
- ❌ Low liquidity session (-0.5)

## 🎯 Market DNA Profiles

CITADEL includes specific profiles for each pair:

```json
{
  "EURUSD": {
    "trap_frequency": "medium",
    "sweep_reliability": 0.75,
    "optimal_sessions": ["london", "overlap_london_ny"]
  },
  "XAUUSD": {
    "trap_frequency": "very_high",
    "sweep_reliability": 0.85,
    "volatility_factor": 1.8
  }
}
```

## 📊 Database Schema

CITADEL uses SQLite for performance tracking:

```sql
-- Shield analyses
CREATE TABLE shield_analyses (
    signal_id TEXT PRIMARY KEY,
    timestamp DATETIME,
    pair TEXT,
    shield_score REAL,
    classification TEXT,
    ...
);

-- Trade outcomes
CREATE TABLE shield_outcomes (
    signal_id TEXT,
    user_id INTEGER,
    outcome TEXT,  -- WIN/LOSS/BE/SKIPPED
    pips_result REAL,
    user_followed_shield BOOLEAN
);
```

## 🚀 Advanced Features

### Real-Time Signal Evolution
Signals can evolve as market conditions change:
```python
# Signal starts as UNVERIFIED
Initial: 🔍 UNVERIFIED [3.2/10]

# After sweep confirmation
Updated: ✅ SHIELD ACTIVE [6.5/10]

# After multi-TF alignment
Final: 🛡️ SHIELD APPROVED [8.1/10]
```

### User Personalization
CITADEL learns from each user's patterns:
```python
# For users who ignore shields
"📊 You typically ignore shield advice. This signal has strong protection - consider following it."

# For disciplined users
"🎯 Your shield discipline is excellent. Another high-confidence setup for you."
```

### Educational Insights
Users can tap for detailed explanations:
```
🛡️ SHIELD ANALYSIS
Score: 8.4/10

✅ Positive Factors:
• Liquidity Sweep: +2.0 (Post-sweep rejection confirmed)
• TF Alignment: +1.5 (3/4 timeframes aligned)
• Entry Structure: +0.5 (Multi-timeframe confluence)

❌ Negative Factors:
• News Risk: -0.5 (ECB speech in 2 hours)

💡 What This Means:
This signal shows strong institutional characteristics. The post-sweep entry and multi-timeframe alignment suggest smart money positioning.
```

## 🔒 Configuration

### Market DNA (`config/market_dna.json`)
- Pair-specific profiles
- Session characteristics
- Liquidity patterns
- News impact matrix

### Scoring Weights (`config/scoring_weights.json`)
- Component weights
- Risk penalties
- Quality bonuses
- Classification thresholds

## 📈 Success Metrics

Expected improvements with CITADEL:
- **25-40%** reduction in trap trades
- **5-10%** win rate improvement
- **Better R:R** on shield-approved trades
- **Higher user trust** through transparency

## 🛠️ Troubleshooting

### Common Issues

1. **"Shield analysis not found"**
   - Signal may have expired from cache
   - Re-analyze the signal

2. **Low shield scores on all signals**
   - Check market data feed
   - Verify timeframe data availability

3. **Database errors**
   - Ensure `/root/HydraX-v2/data/` directory exists
   - Check write permissions

## 🚦 Production Checklist

- [ ] CITADEL modules installed in `/root/HydraX-v2/citadel_core/`
- [ ] Database directory created at `/root/HydraX-v2/data/`
- [ ] Integration patches applied to:
  - [ ] apex_venom_v7_unfiltered.py
  - [ ] bitten_production_bot.py
  - [ ] webapp_server_optimized.py
- [ ] Market data feed connected
- [ ] Shield logger database initialized
- [ ] Performance baseline established

## 📚 API Reference

### Main Analyzer
```python
from citadel_core.citadel_analyzer import get_citadel_analyzer

citadel = get_citadel_analyzer()
result = citadel.analyze_signal(signal, market_data, user_id)
```

### Integration Helpers
```python
from citadel_core.bitten_integration import (
    enhance_signal_with_citadel,
    format_mission_with_citadel,
    get_citadel_shield_data
)
```

## 🎯 Future Enhancements

1. **WebSocket Real-Time Updates** - Live score evolution
2. **Machine Learning Optimization** - Self-improving thresholds
3. **Advanced Backtesting** - Historical shield validation
4. **Mobile App Integration** - Native shield displays

## 📞 Support

For issues or questions:
- Check logs in `/root/HydraX-v2/logs/citadel.log`
- Review shield analyses in database
- Contact the HydraX team

---

**CITADEL Shield System v1.0.0** - Protecting traders through intelligent transparency 🏰