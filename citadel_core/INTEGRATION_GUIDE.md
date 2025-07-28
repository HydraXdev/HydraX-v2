# 🏰 CITADEL Integration Guide

## Quick Integration Steps

### Step 1: Add to VENOM Signal Generation

Edit `/root/HydraX-v2/apex_venom_v7_unfiltered.py`:

Find the `generate_venom_signal` method and add CITADEL enhancement:

```python
# Add this import at the top
from citadel_core.bitten_integration import enhance_signal_with_citadel

# In the generate_venom_signal method, after creating the signal:
def generate_venom_signal(self, pair, timestamp):
    # ... existing signal generation code ...
    
    signal_packet = {
        "signal_id": signal_id,
        "symbol": pair,
        "direction": direction,
        # ... rest of signal data ...
    }
    
    # ADD THIS LINE - Enhance with CITADEL analysis
    signal_packet = enhance_signal_with_citadel(signal_packet)
    
    return signal_packet
```

### Step 2: Update BittenProductionBot

Edit `/root/HydraX-v2/bitten_production_bot.py`:

1. Add import:
```python
from citadel_core.bitten_integration import format_mission_with_citadel
```

2. In the `generate_mission` method:
```python
def generate_mission(self, signal, user_id):
    # ... existing mission generation code ...
    
    # Create mission briefing
    mission_text = self._format_mission_briefing(signal)
    
    # ADD THIS LINE - Enhance with CITADEL shield
    mission_text = format_mission_with_citadel(signal, mission_text)
    
    return mission_text
```

### Step 3: Add to WebApp HUD

Edit `/root/HydraX-v2/webapp_server_optimized.py`:

1. Add import:
```python
from citadel_core.bitten_integration import get_citadel_shield_data
```

2. In the `/api/signals/<signal_id>` endpoint:
```python
@app.route('/api/signals/<signal_id>')
def get_signal_details(signal_id):
    # ... existing code ...
    
    # ADD THESE LINES - Get shield data
    shield_data = get_citadel_shield_data(signal_id)
    
    response = {
        'signal': signal_info,
        'shield': shield_data,  # ADD THIS
        # ... rest of response ...
    }
    
    return jsonify(response)
```

### Step 4: Log Trade Outcomes

When a trade completes, log the outcome for shield learning:

```python
from citadel_core.citadel_analyzer import get_citadel_analyzer

citadel = get_citadel_analyzer()

# After trade completion
citadel.log_trade_outcome(
    signal_id='VENOM_EURUSD_001',
    user_id=user_id,
    outcome='WIN',  # or 'LOSS', 'BE', 'SKIPPED'
    pips_result=25.5,
    followed_shield=True  # Did user follow shield advice?
)
```

## Enhanced Signal Format

After integration, signals will have this structure:

```json
{
  "signal_id": "VENOM_EURUSD_001",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry": 1.0850,
  "sl": 1.0820,
  "tp": 1.0900,
  
  "citadel_shield": {
    "score": 8.5,
    "classification": "SHIELD_APPROVED",
    "emoji": "🛡️",
    "label": "SHIELD APPROVED",
    "explanation": "Post-sweep entry with multi-TF alignment",
    "recommendation": "High-quality setup - Standard position size",
    "risk_factors": [],
    "quality_factors": [
      {
        "factor": "post_sweep_entry",
        "description": "Entry after liquidity sweep"
      }
    ]
  }
}
```

## Telegram Message Format

Missions will automatically include shield analysis:

```
📍 MISSION BRIEFING: EUR/USD
Target: BUY @ 1.0850
📐 Risk: 30 pips | Reward: 60 pips

🛡️ CITADEL SHIELD ANALYSIS
Protection Score: 8.5/10
Status: SHIELD APPROVED

Post-sweep entry with multi-TF alignment

💡 High-quality setup - Standard position size
```

## Testing Your Integration

Run the test script to verify:

```bash
cd /root/HydraX-v2
python3 test_citadel.py
```

## Performance Monitoring

Check CITADEL performance:

```python
from citadel_core.citadel_analyzer import get_citadel_analyzer

citadel = get_citadel_analyzer()

# Get 30-day performance report
report = citadel.get_performance_report(days=30)

# Get user-specific stats
user_stats = citadel.get_user_stats(user_id=12345)
```

## Configuration

Adjust settings in:
- `/root/HydraX-v2/citadel_core/config/market_dna.json` - Pair profiles
- `/root/HydraX-v2/citadel_core/config/scoring_weights.json` - Scoring logic

## Troubleshooting

### Issue: "Shield analysis not found"
**Solution**: Signal may have expired from cache. Re-analyze or check database.

### Issue: Low scores on all signals
**Solution**: Verify market data is being fetched correctly in `_get_market_data()`.

### Issue: Database errors
**Solution**: Ensure `/root/HydraX-v2/data/` directory exists with write permissions.

## Production Checklist

- [ ] VENOM signals enhanced with CITADEL
- [ ] Bot messages show shield analysis
- [ ] WebApp displays shield data
- [ ] Trade outcomes being logged
- [ ] Database initialized at `/root/HydraX-v2/data/citadel_shield.db`
- [ ] Test script runs successfully

## Support

For issues:
1. Check logs for errors
2. Run test script for diagnosis
3. Verify all integration points
4. Check database for shield analyses

---

**CITADEL is now protecting your traders!** 🏰