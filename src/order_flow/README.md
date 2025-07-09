# Order Flow Analysis Component

A comprehensive order flow analysis system that connects to multiple exchanges and provides real-time detection of market microstructure patterns.

## Features

### 1. **Order Book Reader**
- Real-time order book maintenance with efficient updates
- Multi-exchange aggregation
- Historical snapshot storage
- WebSocket and REST API support

### 2. **Imbalance Detector**
- Detects bid/ask volume imbalances
- Dynamic level adjustment
- Strength classification (weak to extreme)
- Trend analysis over time

### 3. **Absorption Pattern Detector**
- Identifies accumulation and distribution patterns
- Detects support/resistance absorption
- Pattern confidence scoring
- Time-based pattern formation

### 4. **Liquidity Void Detector**
- Identifies gaps in order book liquidity
- Severity classification
- Slippage estimation
- Liquidity scoring system

### 5. **Cumulative Delta Calculator**
- Time and volume-based delta bars
- Buy/sell volume classification
- Price/delta divergence detection
- Historical delta extremes tracking

### 6. **Dark Pool Activity Scanner**
- Simulated dark pool detection (ready for real feeds)
- Multiple detection patterns
- Flow analysis and scoring
- Large print identification

### 7. **Order Flow Scoring System**
- Combines all indicators into actionable scores
- Signal strength classification
- Trading opportunity detection
- Confidence-based filtering

## Installation

```bash
cd /root/HydraX-v2/src/order_flow
pip install -r requirements.txt
```

## Quick Start

```python
import asyncio
from order_flow.example_usage import OrderFlowAnalysisSystem

async def main():
    # Create system
    system = OrderFlowAnalysisSystem()
    
    # Start analysis
    await system.start(['BTC/USDT', 'ETH/USDT'])
    
    # Run for desired duration
    await asyncio.sleep(300)  # 5 minutes
    
    # Stop system
    await system.stop()

asyncio.run(main())
```

## Exchange Configuration

### Adding an Exchange

```python
from order_flow.exchange_manager import ExchangeConfig, RateLimitConfig

config = ExchangeConfig(
    name='binance',
    api_key='your_api_key',  # Optional
    api_secret='your_secret',  # Optional
    rate_limits=RateLimitConfig(
        requests_per_second=10,
        requests_per_minute=1200,
        burst_capacity=20
    )
)

await system.exchange_manager.add_exchange(config)
```

### Supported Exchanges

All exchanges supported by CCXT library, including:
- Binance
- Coinbase
- Kraken
- Bitfinex
- OKX
- And 100+ more

## Component Usage

### Imbalance Detection

```python
from order_flow import ImbalanceDetector

detector = ImbalanceDetector(
    levels_to_analyze=20,
    imbalance_threshold=1.5
)

signal = detector.detect_imbalance(order_book_snapshot)
if signal:
    print(f"Imbalance: {signal.direction} ({signal.strength})")
```

### Absorption Pattern Detection

```python
from order_flow import AbsorptionPatternDetector

detector = AbsorptionPatternDetector(
    min_volume_threshold=100.0,
    max_price_movement=0.001
)

pattern = detector.analyze_snapshot(order_book, trades)
if pattern:
    print(f"Pattern: {pattern.pattern_type}, Volume: {pattern.total_volume}")
```

### Order Flow Scoring

```python
from order_flow import OrderFlowScorer

scorer = OrderFlowScorer(min_confidence=0.7)

score = scorer.calculate_score(
    symbol='BTC/USDT',
    exchange='binance',
    order_book=order_book,
    imbalance=imbalance_signal,
    # ... other indicators
)

print(f"Signal: {score.signal_strength.value}")
print(f"Confidence: {score.confidence:.0%}")
```

## API Reference

### OrderBookSnapshot
- `get_spread()`: Calculate bid-ask spread
- `get_mid_price()`: Get mid price
- `get_depth(levels)`: Get total depth at N levels
- `get_weighted_mid_price(levels)`: Volume-weighted mid price

### ImbalanceSignal
- `direction`: 'bullish' or 'bearish'
- `strength`: 'weak', 'moderate', 'strong', 'extreme'
- `imbalance_ratio`: Bid/ask volume ratio
- `weighted_imbalance`: Price-weighted imbalance

### LiquidityProfile
- `liquidity_score`: 0-100 score
- `bid_void_count`: Number of bid-side voids
- `ask_void_count`: Number of ask-side voids
- `effective_spread`: Spread considering liquidity

### OrderFlowScore
- `composite_score`: -100 to 100
- `signal_strength`: Signal enum
- `confidence`: 0-1 confidence level
- `insights`: List of key insights
- `warnings`: List of warnings

## Rate Limiting

The system includes sophisticated rate limiting:

1. **Token Bucket Algorithm**: Smooth request distribution
2. **Burst Capacity**: Handle temporary spikes
3. **Per-Minute Limits**: Comply with exchange requirements
4. **Automatic Backoff**: Exponential backoff on errors

## Performance Considerations

- **Async Architecture**: Non-blocking I/O for all operations
- **Efficient Updates**: Incremental order book updates
- **Memory Management**: Circular buffers with size limits
- **Connection Pooling**: Reuse HTTP connections

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=order_flow --cov-report=html
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all classes and methods
4. Write tests for new features
5. Update documentation as needed

## License

This component is part of the HydraX-v2 project and follows the same license terms.