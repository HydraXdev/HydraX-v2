# 🎯 APEX v5.0 LEAN Configuration

## Changes Made:

### 1. TCS Threshold: 85-95%
- Was: 35-95% (generating 400+ signals in 25 minutes)
- Now: 85-95% (premium signals only)
- Expected: ~60-80 signals per day

### 2. Reduced Pairs from 15 to 10
**Keeping (Top Performers):**
- EURUSD - Major pair
- GBPUSD - High volatility 
- USDJPY - Yen strength
- USDCHF - Top performer (10 signals)
- AUDUSD - Commodity currency
- NZDUSD - High performer (9 signals)
- GBPJPY - Volatile cross
- AUDJPY - Popular cross
- EURJPY - Liquid cross
- GBPCHF - Stable cross

**Removed (Lower 85%+ performance):**
- USDCAD (only 3 high signals)
- EURGBP (only 4 high signals)
- GBPNZD (only 3 high signals)
- GBPAUD (only 4 high signals)
- EURAUD (only 4 high signals)

### 3. Signal Generation Changes:
- Batch size: 3-7 signals (was 10-20)
- Frequency: Every 2-3 minutes (was every minute)
- Cooldown: 2 minutes between same pair/direction

### 4. Benefits:
- **Reduced spam risk** - ~3 signals/minute → ~2-3 signals every 2-3 minutes
- **Higher quality** - Only 85%+ confidence trades
- **Better user experience** - Not overwhelming with alerts
- **Telegram compliant** - Well below spam thresholds

## To Run LEAN Version:

```bash
# Stop current version
pkill -f apex

# Start lean engine
python3 apex_v5_lean.py &

# Start lean telegram connector
python3 apex_telegram_lean.py &
```

## Expected Output:
- ~40-60 premium signals per day
- 2-3 signals every few minutes during active periods
- Only highest confidence trades (85-95% TCS)
- Focused on best performing pairs