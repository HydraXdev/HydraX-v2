# Cross-Asset Correlation System Documentation

## Overview

The Cross-Asset Correlation System is a comprehensive market analysis framework that monitors and analyzes correlations between various financial instruments including forex pairs, indices, commodities, and bonds. It provides real-time insights into market relationships, detects divergences, and generates trading signals based on intermarket analysis.

## Key Components

### 1. Bond Yield Differential Calculator
Analyzes bond yield spreads and yield curve dynamics to assess:
- Interest rate differentials between countries
- Yield curve slope (recession indicator)
- Bond market trends and their impact on currencies

**Key Features:**
- Tracks multiple government bond yields
- Calculates real-time yield spreads
- Monitors yield curve inversions
- Provides trend analysis for bond markets

### 2. Commodity Currency Correlation Analyzer
Monitors relationships between commodities and commodity-dependent currencies:
- **AUD** - Gold, Iron Ore, Coal
- **CAD** - Oil, Natural Gas, Lumber
- **NZD** - Dairy, Wool, Meat
- **NOK** - Oil, Natural Gas, Fish
- **ZAR** - Gold, Platinum, Diamonds
- **BRL** - Iron Ore, Soybeans, Coffee
- **RUB** - Oil, Natural Gas, Gold
- **CLP** - Copper, Lithium

**Signals Generated:**
- Strong positive/negative correlations
- Divergence warnings
- Optimal entry/exit points based on commodity moves

### 3. Equity Market Risk On/Off Detector
Identifies market risk sentiment by analyzing:
- Risk-on assets: SPX, NDX, DAX, Emerging Markets
- Risk-off assets: Gold, JPY, CHF, Bonds
- Volume patterns and momentum
- Sector rotation signals

**Output:**
- Current risk sentiment (Risk On/Off/Neutral/Mixed)
- Recommended sectors for current environment
- Position sizing adjustments

### 4. Dollar Index Analyzer
Calculates and analyzes the US Dollar Index (DXY):
- Real-time DXY calculation using official weights
- Trend analysis and momentum indicators
- Support/resistance levels
- Trading signals for USD pairs

**DXY Composition:**
- EUR: 57.6%
- JPY: 13.6%
- GBP: 11.9%
- CAD: 9.1%
- SEK: 4.2%
- CHF: 3.6%

### 5. Intermarket Divergence Detector
Monitors known correlations and detects divergences:
- GOLD vs DXY (negative correlation)
- OIL vs CAD (positive correlation)
- AUD vs GOLD (positive correlation)
- USDJPY vs US10Y (positive correlation)
- SPX vs VIX (negative correlation)
- EURUSD vs DXY (negative correlation)

**Divergence Analysis:**
- Severity scoring (0-100)
- Expected resolution predictions
- Confidence levels
- Trading opportunities

### 6. Correlation Matrix Calculator
Maintains rolling correlation matrices across all tracked assets:
- Real-time correlation updates
- Historical correlation tracking
- Strongest correlation identification
- Correlation volatility analysis

### 7. Predictive Correlation Models
Advanced features for correlation forecasting:
- Correlation trend prediction
- Regime change detection
- Mean reversion analysis
- Volatility-adjusted predictions

## API Endpoints

### Market Data Update
```
POST /api/correlation/update
{
    "symbol": "EURUSD",
    "asset_class": "forex",
    "price": 1.0850,
    "change_pct": 0.5,
    "volume": 1000000,
    "additional_data": {}
}
```

### Comprehensive Analysis
```
GET /api/correlation/analysis
Returns complete cross-asset analysis including risk sentiment, correlations, divergences, and trading signals
```

### Pair-Specific Analysis
```
GET /api/correlation/pair/{symbol}
Returns detailed analysis for a specific trading pair
```

### Correlation Matrix
```
GET /api/correlation/correlations/matrix?period=50
Returns current correlation matrix for specified period
```

### Market Divergences
```
GET /api/correlation/divergences
Returns list of active intermarket divergences
```

### Dollar Index
```
GET /api/correlation/dollar-index
Returns current DXY analysis and signals
```

### Risk Sentiment
```
GET /api/correlation/risk-sentiment
Returns current market risk sentiment and sector signals
```

### Dashboard
```
GET /api/correlation/dashboard
Returns HTML dashboard with visualizations
```

## Usage Examples

### 1. Initialize and Update System
```python
from src.bitten_core.strategies.cross_asset_correlation import (
    CrossAssetCorrelationSystem,
    AssetData,
    AssetClass
)

# Initialize system
correlation_system = CrossAssetCorrelationSystem()

# Update with market data
asset_data = AssetData(
    symbol='EURUSD',
    asset_class=AssetClass.FOREX,
    price=1.0850,
    change_pct=0.5,
    volume=1000000,
    timestamp=datetime.now()
)
correlation_system.update_market_data(asset_data)
```

### 2. Get Comprehensive Analysis
```python
analysis = correlation_system.get_comprehensive_analysis()

print(f"Risk Sentiment: {analysis['risk_sentiment']}")
print(f"Dollar Signal: {analysis['dollar_analysis']['signal']}")
print(f"Trading Bias: {analysis['trading_bias']}")
```

### 3. Check for Divergences
```python
divergences = correlation_system.divergence_detector.detect_divergences()

for div in divergences:
    print(f"Divergence: {div.assets}")
    print(f"Severity: {div.severity}")
    print(f"Expected Resolution: {div.expected_resolution}")
```

### 4. Get Pair-Specific Analysis
```python
eurusd_analysis = correlation_system.get_pair_specific_analysis('EURUSD')

implications = eurusd_analysis['trading_implications']
print(f"Primary Drivers: {implications['primary_drivers']}")
print(f"Optimal Timeframe: {implications['optimal_timeframe']}")
```

## Trading Strategies

### 1. Divergence Trading
- Monitor for significant divergences (severity > 70)
- Enter positions expecting mean reversion
- Use tighter stops due to divergence risk

### 2. Risk Sentiment Trading
- **Risk On**: Long risk assets, short safe havens
- **Risk Off**: Short risk assets, long safe havens
- Adjust position sizes based on sentiment strength

### 3. Commodity Currency Trading
- Trade currencies based on commodity correlations
- Use commodity moves as leading indicators
- Monitor for correlation breakdowns

### 4. Dollar Index Trading
- Trade USD pairs based on DXY signals
- Use yield differentials for confirmation
- Monitor for trend changes at key levels

## Integration with HydraX

The correlation system integrates seamlessly with the existing HydraX trading infrastructure:

1. **Signal Generation**: Correlation signals feed into the main signal flow
2. **Risk Management**: Risk sentiment affects position sizing
3. **Strategy Selection**: Market conditions influence strategy choice
4. **Alert System**: Divergences trigger special alerts

## Visualization Features

The system includes a comprehensive dashboard with:
- Correlation heatmap
- Risk sentiment gauge
- Divergence charts
- Network graph of correlations
- Trading signal tables
- Historical correlation timelines

## Performance Considerations

- Data is stored in memory-efficient deque structures
- Correlation calculations are optimized for speed
- Caching is used for frequently accessed calculations
- Historical data is limited to prevent memory bloat

## Future Enhancements

1. **Machine Learning Integration**
   - Neural network correlation prediction
   - Anomaly detection for unusual correlations
   - Pattern recognition for regime changes

2. **Additional Asset Classes**
   - Cryptocurrency correlations
   - Volatility indices
   - Sector ETFs

3. **Advanced Analytics**
   - Lead-lag analysis
   - Granger causality testing
   - Dynamic correlation modeling

4. **Real-time Data Feeds**
   - Direct market data integration
   - WebSocket updates
   - Automated data validation

## Troubleshooting

### Common Issues

1. **Insufficient Data Error**
   - Ensure at least 50 data points for correlation calculation
   - Check data update frequency

2. **No Correlations Found**
   - Verify asset symbols are correct
   - Ensure data is being updated for all assets

3. **Divergence Not Detected**
   - Check divergence threshold settings
   - Verify correlation pairs are configured

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('cross_asset_correlation').setLevel(logging.DEBUG)
```

## Conclusion

The Cross-Asset Correlation System provides a powerful framework for understanding market relationships and generating trading signals based on intermarket analysis. By monitoring correlations, divergences, and regime changes across multiple asset classes, traders can make more informed decisions and identify opportunities that single-market analysis might miss.