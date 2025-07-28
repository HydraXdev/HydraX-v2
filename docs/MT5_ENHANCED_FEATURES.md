# MT5 Enhanced Features Documentation

## Overview

The BITTEN system now includes advanced two-way communication with MT5, enabling sophisticated trade management and account-aware decision making without requiring a separate hybrid bridge.

## Key Features Added

### 1. **Two-Way Account Data Communication**

The enhanced EA (v3) now provides comprehensive account data:

```json
{
  "balance": 10000.00,
  "equity": 10150.00,
  "margin": 200.00,
  "free_margin": 9950.00,
  "margin_level": 5075.00,
  "daily_pl": -50.00,
  "daily_pl_percent": -0.50,
  "positions": {
    "total": 2,
    "buy": 1,
    "sell": 1,
    "buy_volume": 0.10,
    "sell_volume": 0.05
  }
}
```

This data is updated every 2 seconds and used for:
- Risk management decisions
- Daily loss limit enforcement (-7%)
- Position limit checking
- Margin level monitoring

### 2. **Risk-Based Lot Calculation**

Instead of fixed lot sizes, trades can now be executed with automatic lot calculation based on risk percentage:

```python
# Execute with 2% risk
result = adapter.execute_trade_with_risk(
    symbol="EURUSD",
    direction="BUY",
    risk_percent=2.0,
    sl=1.0900,
    tp=1.1100
)
```

The EA calculates the exact lot size based on:
- Account balance
- Stop loss distance
- Symbol's tick value
- Risk percentage

### 3. **Advanced Trade Management**

#### Break-Even Management
- Automatically moves SL to break-even + buffer when trade is profitable
- Configurable trigger points (default: 20 points profit)
- Protects profits while allowing upside

#### Partial Close
- Take profits on portions of the position
- Default: Close 50% at first target
- Keep the rest running with trailing stop

#### Multi-Step Take Profit
- Set up to 3 take profit levels
- Customizable volume percentages at each level
- Example: 30% at TP1, 30% at TP2, 40% at TP3

#### Trailing Stop
- Dynamic stop loss that follows price
- Configurable distance and step
- Only trails when position is profitable

### 4. **Live Market Data**

The EA provides real-time market data for major pairs:

```json
{
  "timestamp": "2025-01-07 14:30:00",
  "pairs": {
    "EURUSD": {"bid": 1.09500, "ask": 1.09510, "spread": 1.0},
    "GBPUSD": {"bid": 1.26500, "ask": 1.26515, "spread": 1.5},
    "XAUUSD": {"bid": 1950.00, "ask": 1950.50, "spread": 5.0}
  }
}
```

### 5. **Enhanced Position Tracking**

Positions now include additional data:

```json
{
  "ticket": 12345678,
  "symbol": "EURUSD",
  "type": "BUY",
  "volume": 0.10,
  "initial_volume": 0.20,
  "open_price": 1.09500,
  "sl": 1.09450,
  "tp": 1.09700,
  "profit": 25.50,
  "pnl_percent": 0.23,
  "break_even_set": true,
  "partial_closed": true,
  "partial_close_step": 1
}
```

## Usage Examples

### 1. Basic Trade with Risk Management

```python
from bitten_core.mt5_enhanced_adapter import MT5EnhancedAdapter

adapter = MT5EnhancedAdapter()

# Check if we can trade
can_trade, reason = adapter.should_take_trade("EURUSD", 2.0)

if can_trade:
    result = adapter.execute_trade_with_risk(
        symbol="EURUSD",
        direction="BUY",
        risk_percent=2.0,
        sl=1.0900,
        tp=1.1000,
        break_even=True,
        trailing=False
    )
```

### 2. Advanced Multi-TP Setup

```python
# Commander tier feature
result = adapter.execute_trade_with_risk(
    symbol="XAUUSD",
    direction="SELL",
    risk_percent=2.0,
    sl=1960.00,
    tp1=1945.00,  # First target (30%)
    tp2=1940.00,  # Second target (30%)
    tp3=1935.00,  # Final target (40%)
    volume1=30,   # Take 30% at TP1
    volume2=30,   # Take 30% at TP2
    volume3=40,   # Take 40% at TP3
    break_even=True,
    trailing=True
)
```

### 3. Position Management

```python
# After trade is open
ticket = result['data']['ticket']

# Set break-even when ready
adapter.set_break_even(ticket, buffer=5)

# Or activate trailing stop
adapter.set_trailing_stop(ticket, distance=30, step=10)

# Or take partial profits
adapter.close_partial(ticket, percent=50)
```

### 4. Account Monitoring

```python
from bitten_core.mt5_enhanced_adapter import MT5AccountMonitor

monitor = MT5AccountMonitor(adapter)

# Get session statistics
stats = monitor.get_session_stats()

print(f"Session P&L: ${stats['session_pl']:.2f}")
print(f"Daily P&L: {stats['daily_pl_percent']:.2f}%")
print(f"Can Trade: {stats['can_trade']}")
print(f"Risk Status: {stats['risk_status']}")
```

## Integration with Signal Flow

The enhanced signal flow (v2) automatically uses these features:

1. **Pre-Trade Checks**
   - Account balance and margin
   - Daily loss limits
   - Position limits
   - Symbol exposure

2. **Trade Execution**
   - Automatic lot sizing based on risk
   - Multi-TP setup for advanced tiers
   - Break-even and trailing activation

3. **Post-Trade Management**
   - Automatic break-even at profit targets
   - Partial close at key levels
   - Trailing stop for trend following

## File Communication

All communication happens through secure files:

- `bitten_instructions_secure.txt` - Trade instructions (JSON format)
- `bitten_commands_secure.txt` - Management commands
- `bitten_results_secure.txt` - Trade results
- `bitten_status_secure.txt` - EA status
- `bitten_positions_secure.txt` - Position data
- `bitten_account_secure.txt` - Account data
- `bitten_market_secure.txt` - Market data

## Security Features

1. **Input Validation** - All inputs are validated and sanitized
2. **Risk Limits** - Maximum lot size and risk percentage enforced
3. **Daily Limits** - Maximum trades per day
4. **Concurrent Limits** - Maximum open positions
5. **File Size Limits** - Prevent DOS attacks

## Performance

- Account data updates: Every 2 seconds
- Position updates: Every 1 second
- Market data updates: Every 1 second
- Command processing: 100ms intervals
- Trade timeout: 30 seconds

## Tier-Based Features

| Feature | Nibbler | Fang | Commander | |
|---------|---------|------|-----------|------|
| Basic Trading | ✅ | ✅ | ✅ | ✅ |
| Risk-Based Sizing | ✅ | ✅ | ✅ | ✅ |
| Break-Even | ❌ | ✅ | ✅ | ✅ |
| Partial Close | ❌ | ✅ | ✅ | ✅ |
| Trailing Stop | ❌ | ❌ | ✅ | ✅ |
| Multi-TP | ❌ | ❌ | ✅ | ✅ |
| Advanced Management | ❌ | ❌ | ❌ | ✅ |

## Conclusion

These enhancements eliminate the need for a separate hybrid bridge by providing:
- Full account visibility
- Advanced trade management
- Real-time decision making
- Tier-based feature access

The system can now make intelligent decisions based on account state and manage trades professionally throughout their lifecycle.