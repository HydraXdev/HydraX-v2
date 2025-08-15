# MT5 Integration for AAA Signal Engine

## Overview
The AAA Signal Engine can now use live MT5 data instead of relying on external APIs. Since we already have two-way communication with MT5, we can leverage it for real-time OHLCV data.

## Setup Instructions

### 1. Install the OHLCV Provider EA
1. Copy `/mq5/BITTEN_OHLCV_Provider.mq5` to your MT5 Experts folder
2. Compile it in MetaEditor
3. Attach to any chart (preferably EURUSD M1)
4. Set the data path to match your BITTEN bridge path

### 2. Configure File Paths
Update the paths in `/bitten/core/mt5_market_data_collector.py`:
```python
self.mt5_dir = "/path/to/your/mt5/files"  # Same as your bridge path
```

### 3. How It Works
1. **Python → MT5**: AAA engine writes OHLCV request to `bitten_ohlcv_request.txt`
2. **MT5 → Python**: EA reads request, gets data, writes to `bitten_ohlcv_response.json`
3. **Live Updates**: EA continuously updates `bitten_market_data.json` with current prices

### 4. Data Flow
```
AAA Signal Engine
    ↓
MT5MarketDataCollector
    ↓
File: bitten_ohlcv_request.txt
    ↓
MT5 EA (BITTEN_OHLCV_Provider)
    ↓
File: bitten_ohlcv_response.json
    ↓
AAA Signal Engine (processes data)
```

## Benefits Over External APIs

1. **No Additional Costs**: Uses your existing MT5 connection
2. **Real Broker Data**: Gets actual spreads and prices from your broker
3. **Lower Latency**: Direct connection, no internet API calls
4. **Historical Data**: Can get up to 10,000 bars of history
5. **Multiple Timeframes**: M1, M5, M15, M30, H1, H4, D1

## Data Available

- **OHLCV**: Open, High, Low, Close, Volume for any timeframe
- **Current Prices**: Real-time bid/ask/spread
- **Technical Indicators**: Calculated in Python (no TA-Lib needed)
- **Multiple Pairs**: All 10 pairs monitored simultaneously

## Fallback System

If MT5 is not available, the system automatically falls back to:
1. Demo data generation (for testing)
2. Cached data (if available)

## Testing

To test the MT5 connection:
```python
from bitten.core.mt5_market_data_collector import MT5AAAIntegration

# Test data retrieval
integration = MT5AAAIntegration()
pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
data = integration.get_aaa_market_data(pairs)

for pair, df in data.items():
    print(f"{pair}: {len(df)} bars retrieved")
```

## Monitoring

The EA provides continuous updates to:
- `bitten_market_data.json`: Current prices (updated every 100ms)
- System logs show when live MT5 data is being used vs demo data

## No External Dependencies!

This setup eliminates the need for:
- TraderMade API ($50/month)
- Polygon.io subscription
- Any other market data provider

Your MT5 terminal becomes your data provider!