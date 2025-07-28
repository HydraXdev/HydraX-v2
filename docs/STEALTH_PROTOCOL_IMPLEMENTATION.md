# BITTEN Stealth Protocol Implementation

## Overview

The BITTEN Stealth Protocol is an advanced anti-detection system designed to make trading patterns appear more human-like and avoid regulatory scrutiny. It implements six core stealth functions that work together to obfuscate trading behavior.

## Core Components

### 1. Stealth Functions

#### `entry_delay()`
- **Purpose**: Adds randomized delay before trade execution
- **Range**: 1-12 seconds (configurable by stealth level)
- **Implementation**: Uses cryptographically secure random numbers
- **Benefit**: Prevents instant execution patterns that could trigger detection

#### `lot_size_jitter()`
- **Purpose**: Applies random variation to position sizes
- **Range**: ±3-7% (up to ±15% in GHOST mode)
- **Implementation**: Randomly increases or decreases lot size
- **Benefit**: Avoids consistent position sizing that looks algorithmic

#### `tp_sl_offset()`
- **Purpose**: Shifts Take Profit and Stop Loss levels by small amounts
- **Range**: ±1-3 pips (up to ±7 pips in GHOST mode)
- **Implementation**: Random pip adjustments in either direction
- **Benefit**: Makes levels appear manually placed rather than calculated

#### `ghost_skip()`
- **Purpose**: Randomly skips trades to break patterns
- **Rate**: ~1 in 6 trades (configurable)
- **Implementation**: Cryptographically secure random selection
- **Benefit**: Creates gaps in trading pattern that look like human hesitation

#### `vol_cap()`
- **Purpose**: Limits concurrent trades per asset and total
- **Limits**: 
  - Max 3 trades per asset
  - Max 10 total concurrent trades
- **Implementation**: Real-time tracking of active positions
- **Benefit**: Prevents suspicious volume spikes

#### `execution_shuffle()`
- **Purpose**: Randomizes order execution sequence
- **Implementation**: Secure random shuffle with delays between trades
- **Benefit**: Breaks predictable execution patterns

### 2. Stealth Levels

```python
class StealthLevel(Enum):
    OFF = "off"           # No stealth
    LOW = "low"           # Minimal obfuscation
    MEDIUM = "medium"     # Standard stealth
    HIGH = "high"         # Maximum randomization
    GHOST = "ghost"       # Ultra-stealth mode (COMMANDER only)
```

### 3. Tier Integration

| Tier | Stealth Access | Max Level | Available Modes |
|------|----------------|-----------|-----------------|
| NIBBLER | ❌ No | - | None |
| FANG | ✅ Yes | LOW | CHAINGUN only |
| COMMANDER | ✅ Yes | GHOST | All modes + exclusive STEALTH mode |

## Implementation Details

### File Structure

```
/root/HydraX-v2/
├── src/bitten_core/
│   ├── stealth_protocol.py          # Core stealth implementation
│   ├── stealth_integration.py       # Fire mode integration
│   └── stealth_config_loader.py     # Configuration management
├── config/
│   └── stealth_settings.yml         # Stealth configuration
├── logs/
│   └── stealth_log.txt             # Stealth action logs
└── examples/
    └── stealth_protocol_example.py  # Usage examples
```

### Key Classes

#### `StealthProtocol`
Main implementation class that provides all stealth functions.

```python
stealth = get_stealth_protocol()
stealth_params = stealth.apply_full_stealth(trade_params)
```

#### `StealthFireModeIntegration`
Integrates stealth with BITTEN fire modes.

```python
integration = StealthFireModeIntegration()
result = await integration.execute_stealth_trade(
    user_id, tier, fire_mode, trade_params
)
```

#### `StealthConfigLoader`
Loads configuration from YAML file.

```python
loader = get_stealth_config_loader()
config = loader.get_stealth_config(StealthLevel.MEDIUM)
```

## Usage Examples

### Basic Stealth Application

```python
# Initialize stealth
stealth = get_stealth_protocol()
stealth.set_level(StealthLevel.MEDIUM)

# Apply to trade
trade_params = {
    'symbol': 'EURUSD',
    'volume': 0.1,
    'tp': 1.1000,
    'sl': 1.0900
}

stealth_params = stealth.apply_full_stealth(trade_params)
```

### Tier-Based Stealth

```python
# user with STEALTH mode
result = await apply_stealth_to_fire_command(
    user_id=12345,
    tier=TierLevel.fire_mode=FireMode.STEALTH,
    trade_params=trade_params
)
```

### Batch Execution with Shuffle

```python
trades = [trade1, trade2, trade3, trade4]
shuffled = stealth.execution_shuffle(trades)
# Trades now execute in random order with delays
```

## Logging and Monitoring

All stealth actions are logged to `/logs/stealth_log.txt` with the following information:
- Timestamp
- Action type
- Original value
- Modified value
- Stealth level
- Additional details

Example log entry:
```json
{
    "timestamp": "2024-01-10T15:30:45",
    "action_type": "lot_size_jitter",
    "original": 0.1,
    "modified": 0.093,
    "level": "medium",
    "details": {
        "pair": "EURUSD",
        "jitter_percent": -7.0,
        "direction": "decrease"
    }
}
```

## Configuration

Stealth behavior is configured via `/config/stealth_settings.yml`:

```yaml
stealth:
  enabled: true
  default_level: medium
  
  entry_delay:
    medium:
      min: 1.0
      max: 6.0
      
  lot_jitter:
    medium:
      min: 0.03  # 3%
      max: 0.07  # 7%
```

## Security Considerations

1. **Cryptographically Secure Randomness**: All random operations use `secrets` module
2. **No Predictable Patterns**: Avoids using timestamps or sequential IDs
3. **Configurable Behavior**: Can be adjusted without code changes
4. **Audit Trail**: All actions logged for compliance

## Testing

Run the test suite:
```bash
python test_stealth_protocol.py
```

Run usage examples:
```bash
python examples/stealth_protocol_example.py
```

## Best Practices

1. **Start Conservative**: Begin with LOW or MEDIUM stealth levels
2. **Monitor Logs**: Regularly check stealth logs for patterns
3. **Adjust Parameters**: Fine-tune based on trading results
4. **Tier Appropriate**: Use stealth levels appropriate to subscription tier
5. **Pattern Breaking**: Enable pattern breaking for long-term stealth

## Troubleshooting

### Stealth Not Applied
- Check if stealth is enabled in configuration
- Verify tier has stealth access
- Ensure fire mode supports stealth

### Too Many Skipped Trades
- Lower ghost_skip rate
- Reduce stealth level
- Check volume caps

### Logs Not Generated
- Verify log directory exists
- Check file permissions
- Ensure logging is enabled in config

## Future Enhancements

1. **Machine Learning Integration**: Adaptive stealth based on market conditions
2. **Regional Variations**: Different stealth profiles for different regions
3. **Advanced Pattern Breaking**: More sophisticated behavior changes
4. **Real-time Adjustment**: Dynamic stealth level based on detection risk