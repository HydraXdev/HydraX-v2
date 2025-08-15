# ZMQ GOLD ROUTING GUIDE

## Overview

The ZMQ tick receiver is future-proofed to handle XAUUSD (Gold) differently from other pairs. This allows for specialized gold trading strategies, risk management, and analysis.

## Architecture

```
MT5 EA (Publisher)
    ↓
Topic-Prefixed Messages: "XAUUSD {...}"
    ↓
ZMQ SUB Socket (tcp://ea_ip:5555)
    ↓
Parse & Route
    ├─→ Gold Handler (if symbol in gold_symbols)
    └─→ Regular Handler (all other pairs)
```

## Key Features

### 1. Topic-Prefixed Messages
Each message from the EA is prefixed with the symbol:
```
EURUSD {"symbol":"EURUSD","bid":1.12345,...}
XAUUSD {"symbol":"XAUUSD","bid":2010.50,...}
```

### 2. Gold Tagging
Gold symbols are automatically tagged:
```python
if symbol in self.gold_symbols:
    data['gold'] = True
```

### 3. Future-Proofed Routing
```python
# Currently: All symbols go through same handler
process_market_data(payload)

# Future: Enable separate routing
receiver.enable_gold_routing(True)
# Now XAUUSD → gold_handler()
# Others → market_handler()
```

### 4. Topic Filtering
Subscribe to specific symbols only:
```python
# Subscribe to GOLD only
socket.setsockopt(zmq.SUBSCRIBE, b"XAUUSD")

# Subscribe to multiple
socket.setsockopt(zmq.SUBSCRIBE, b"XAUUSD")
socket.setsockopt(zmq.SUBSCRIBE, b"XAGUSD")
```

## Usage Examples

### Basic Integration
```python
from zmq_tick_receiver import ZMQTickReceiver

# Create receiver
receiver = ZMQTickReceiver("tcp://192.168.1.100:5555")

# Set handler
def process_tick(data):
    if data.get('gold'):
        print(f"⚡ GOLD: {data['symbol']}")
    else:
        print(f"📈 Regular: {data['symbol']}")
        
receiver.set_market_handler(process_tick)
receiver.run()
```

### Gold-Specific Processing
```python
from zmq_venom_integration import VenomMarketProcessor

processor = VenomMarketProcessor()

# Gold gets special treatment:
# - Higher TCS threshold (85 vs 75)
# - Lower risk multiplier (0.5x)
# - Different signal validation

receiver = ZMQTickReceiver("tcp://mt5:5555")
receiver.set_market_handler(processor.process_market_tick)
receiver.run()
```

### Testing Gold Routing
```bash
# Test with all symbols
python3 test_zmq_gold_routing.py

# Test GOLD only subscription
python3 test_zmq_gold_routing.py --gold-only
```

## Gold Trading Considerations

### Why Special Gold Processing?

1. **Volatility**: Gold moves differently than forex
2. **Liquidity**: Different liquidity patterns
3. **Sessions**: Gold has specific active hours
4. **Correlations**: Inverse USD, bond yields matter
5. **News Impact**: Fed meetings, inflation data

### Gold-Specific Metrics

The gold analyzer tracks:
- Spread volatility
- Liquidity events (tight spreads)
- Price spikes
- Session patterns

### Future Enhancements

1. **Separate TCS Model**: Gold-specific signal scoring
2. **Risk Sizing**: Dynamic position sizing for gold volatility
3. **Correlation Analysis**: DXY inverse correlation
4. **News Filter**: Fed meeting blackouts
5. **Session Optimizer**: London fix, NY open strategies

## Production Deployment

### Enable Gold Routing
```python
# In production config
GOLD_ROUTING_ENABLED = True
GOLD_SYMBOLS = ["XAUUSD", "XAGUSD"]
GOLD_MIN_TCS = 85
GOLD_RISK_MULTIPLIER = 0.5
```

### Monitor Gold Performance
```python
# Gold-specific logging
logger.info(f"⚡ GOLD tick received - {symbol}")
logger.info(f"🏆 GOLD signal generated - TCS: {tcs}")
```

### Separate Gold Strategies
```python
if data.get('gold'):
    # Route to specialized gold strategy
    signal = gold_strategy.process(data)
else:
    # Standard VENOM processing
    signal = venom_engine.process(data)
```

## Performance Metrics

Expected performance with gold routing:
- **Latency**: No additional overhead
- **Memory**: Minimal (tags added to existing data)
- **CPU**: <1% increase for routing logic
- **Flexibility**: Can enable/disable per symbol

## Summary

The ZMQ architecture is ready for gold-specific processing:
1. EA sends topic-prefixed messages
2. Receiver tags gold symbols
3. Future routing can separate gold completely
4. Topic filtering allows gold-only subscriptions
5. Production-ready with no performance impact

This design allows HydraX to evolve gold trading strategies independently while maintaining the existing infrastructure.