# Fire Validator Documentation

**Location**: `/root/HydraX-v2/src/bitten_core/fire_validator.py`
**Created**: October 9, 2025
**Purpose**: Server-side fire validation engine with tier-based enforcement

## Overview

The Fire Validator is the authoritative server-side component that validates all fire requests before they execute trades. It enforces tier-based restrictions, calculates position sizing, and ensures users can only trade within their account limits.

## Key Principle

**Server validation is authoritative** - Client requests are treated as advisory only. The server always enforces tier caps, slot limits, and risk management rules.

## Tier System

### NIBBLER (Entry Tier)
- **Manual Slots**: 1
- **Auto Slots**: 0 (no auto-fire)
- **Daily Trades**: 6
- **Risk Range**: 0.5% fixed
- **Description**: Manual trading only, conservative risk

### FANG (Intermediate Tier)
- **Manual Slots**: 2
- **Auto Slots**: 0 (no auto-fire)
- **Daily Trades**: 6
- **Risk Range**: 0.5% - 1.0%
- **Description**: Manual trading only, moderate risk

### COMMANDER (Advanced Tier)
- **Manual Slots**: 10
- **Auto Slots**: 10
- **Daily Trades**: 6
- **Risk Range**: 0.5% - 4.0%
- **Auto-fire**: Enabled
- **Description**: Full trading capabilities with flexible risk

## Validation Flow

### 10-Step Validation Process

1. **Load User Caps**: Query `user_fire_modes` table for user settings
2. **Trading Enabled Check**: Verify account is not disabled
3. **Fire Mode Validation**: Check if user's tier allows AUTO fire
4. **Slot Availability**: Verify manual/auto slots are available
5. **Daily Trade Limit**: Check trades_used_today vs tier limit
6. **Account Balance**: Load from user_registry.json
7. **Risk Cap Enforcement**: Apply minimum of (requested, preference, tier cap)
8. **Lot Size Calculation**: Calculate position size based on risk
9. **Financial Projections**: Calculate max loss and expected gain
10. **Return Enforced Parameters**: Provide validated trading parameters

## Usage

### Basic Usage

```python
from src.bitten_core.fire_validator import fire_validator

# Validate a fire request
result = fire_validator.validate_fire_request(
    user_id="7176191872",
    signal_id="ELITE_GUARD_EURUSD_1234567890",
    client_request={
        "symbol": "EURUSD",
        "direction": "BUY",
        "sl_pips": 20.0,
        "tp_pips": 30.0,
        "risk_pct": 2.0,  # User's requested risk
        "fire_mode": "MANUAL"  # or "AUTO"
    }
)

if result['allowed']:
    # Use enforced parameters for trade execution
    lot_size = result['enforced']['lot_size']
    risk_pct = result['enforced']['risk_pct']
    max_loss = result['enforced']['max_loss']
    expected_gain = result['enforced']['expected_gain']
else:
    # Handle rejection
    print(f"Fire blocked: {result['reason']}")
```

### Response Structure

#### Success Response

```json
{
  "allowed": true,
  "reason": "Validation passed",
  "enforced": {
    "lot_size": 0.01,
    "risk_pct": 0.5,
    "fire_mode": "MANUAL",
    "max_loss": 2.09,
    "expected_gain": 3.14,
    "symbol": "EURUSD",
    "sl_pips": 20.0,
    "tp_pips": 30.0
  },
  "tier_info": {
    "tier": "COMMANDER",
    "caps": {
      "max_manual_slots": 10,
      "max_auto_slots": 10,
      "max_trades_per_day": 6,
      "min_risk_pct": 0.5,
      "max_risk_pct": 4.0,
      "auto_fire_allowed": true
    },
    "user_caps": {
      "user_id": "7176191872",
      "subscription_tier": "COMMANDER",
      "max_manual_slots": 10,
      "max_auto_slots": 0,
      "manual_slots_in_use": 0,
      "auto_slots_in_use": 0,
      "trades_used_today": 0,
      "tier_max_trades_per_day": 6,
      "risk_per_trade": 0.04
    }
  },
  "validation_details": {
    "balance": 418.27,
    "slots_used": {
      "type": "manual",
      "used": 0,
      "max": 10
    },
    "trades_today": {
      "used": 0,
      "max": 6
    },
    "risk_calculation": {
      "requested": 2.0,
      "user_preference": 0.04,
      "tier_cap": 4.0,
      "enforced": 0.5
    }
  },
  "timestamp": "2025-10-09T22:40:03.313753+00:00"
}
```

#### Rejection Response

```json
{
  "allowed": false,
  "reason": "Auto-fire not available for NIBBLER tier (requires COMMANDER)",
  "enforced": {},
  "tier_info": {
    "caps": {
      "max_manual_slots": 1,
      "max_auto_slots": 0,
      "max_trades_per_day": 6,
      "min_risk_pct": 0.5,
      "max_risk_pct": 0.5,
      "auto_fire_allowed": false
    }
  },
  "timestamp": "2025-10-09T22:35:12.123456+00:00"
}
```

## Risk Calculation

### Lot Size Formula

```
lot_size = (balance * risk_pct / 100) / (stop_pips * pip_value)
```

### Example

- **Balance**: $418.27
- **Risk**: 0.5% = $2.09
- **Stop Loss**: 20 pips
- **Pip Value**: $10 (EURUSD standard lot)
- **Calculation**: $2.09 / (20 * $10) = $2.09 / $200 = 0.0105 lots
- **Rounded**: 0.01 lots (MT5 minimum)

### Pip Values

| Symbol | Pip Value (per standard lot) |
|--------|------------------------------|
| EURUSD | $10.00 |
| GBPUSD | $10.00 |
| USDJPY | $9.09 |
| EURJPY | $9.09 |
| GBPJPY | $9.09 |
| XAUUSD | $10.00 |
| XAGUSD | $50.00 |

## Risk Enforcement

The validator enforces risk as the **MINIMUM** of three values:

1. **User's Request**: What they're asking for in this specific trade
2. **User Preference**: Their saved risk_per_trade setting
3. **Tier Cap**: Maximum allowed by their subscription tier

It also enforces the **tier minimum** to prevent zero-risk trades.

### Example: COMMANDER User

```python
# User settings in database:
risk_per_trade = 0.04  # 0.04% saved preference

# User requests:
requested_risk = 2.0  # 2% for this trade

# Tier caps:
min_risk = 0.5  # 0.5% minimum
max_risk = 4.0  # 4% maximum

# Enforcement:
enforced = min(2.0, 0.04, 4.0)  # = 0.04
enforced = max(0.04, 0.5)       # = 0.5 (apply minimum)

# Result: 0.5% enforced
```

## Database Schema

### Required Tables

#### user_fire_modes

```sql
CREATE TABLE user_fire_modes (
    user_id TEXT PRIMARY KEY,
    subscription_tier TEXT DEFAULT 'NIBBLER',
    max_manual_slots INTEGER DEFAULT 1,
    max_auto_slots_separate INTEGER DEFAULT 0,
    manual_slots_in_use INTEGER DEFAULT 0,
    auto_slots_in_use INTEGER DEFAULT 0,
    trades_used_today INTEGER DEFAULT 0,
    tier_max_trades_per_day INTEGER DEFAULT 6,
    risk_per_trade REAL DEFAULT 0.02,
    trading_enabled BOOLEAN DEFAULT TRUE,
    auto_fire_enabled BOOLEAN DEFAULT TRUE
);
```

## Integration Points

### Where to Use the Validator

1. **WebApp Fire Endpoint** (`/api/fire`):
   ```python
   from src.bitten_core.fire_validator import fire_validator

   validation = fire_validator.validate_fire_request(
       user_id=user_id,
       signal_id=signal_id,
       client_request=request_data
   )

   if not validation['allowed']:
       return jsonify({"error": validation['reason']}), 403

   # Use validation['enforced'] parameters for trade
   ```

2. **Auto-Fire System**:
   ```python
   # Before auto-firing signal
   validation = fire_validator.validate_fire_request(
       user_id=user_id,
       signal_id=signal['signal_id'],
       client_request={
           "symbol": signal['symbol'],
           "direction": signal['direction'],
           "sl_pips": signal['stop_pips'],
           "tp_pips": signal['target_pips'],
           "risk_pct": user_settings['auto_fire_risk'],
           "fire_mode": "AUTO"
       }
   )
   ```

3. **Manual Fire Commands** (Telegram/Discord):
   ```python
   validation = fire_validator.validate_fire_request(
       user_id=str(message.from_user.id),
       signal_id=signal_id,
       client_request={
           "symbol": signal['symbol'],
           "direction": signal['direction'],
           "sl_pips": signal['stop_pips'],
           "tp_pips": signal['target_pips'],
           "risk_pct": 2.0,  # Default or from user command
           "fire_mode": "MANUAL"
       }
   )
   ```

## Common Validation Failures

### 1. Tier Restriction

```
"Auto-fire not available for NIBBLER tier (requires COMMANDER)"
```
**Solution**: User needs to upgrade to COMMANDER tier

### 2. Slots Full

```
"No manual slots available (1/1 in use)"
```
**Solution**: User needs to close existing position or upgrade tier

### 3. Daily Limit

```
"Daily trade limit reached (6/6 trades used today)"
```
**Solution**: Wait for daily reset or upgrade to tier with higher limits

### 4. Trading Disabled

```
"Trading disabled for this account"
```
**Solution**: Administrator needs to re-enable trading for user

### 5. No Balance

```
"Account balance unavailable or zero"
```
**Solution**: User needs to connect MT5 account or fund account

## Testing

### Run Built-in Tests

```bash
# Test with sample data
cd /root/HydraX-v2
python3 src/bitten_core/fire_validator.py

# Test with real database
python3 test_fire_validator.py
```

### Manual Testing

```python
from src.bitten_core.fire_validator import fire_validator

# Test NIBBLER manual fire (should pass if slots available)
result = fire_validator.validate_fire_request(
    user_id="999888777",  # Example NIBBLER user
    signal_id="TEST_001",
    client_request={
        "symbol": "EURUSD",
        "direction": "BUY",
        "sl_pips": 20.0,
        "tp_pips": 30.0,
        "risk_pct": 2.0,
        "fire_mode": "MANUAL"
    }
)

print(result)
```

## Security Considerations

### 1. Server Authority

- **Never trust client-provided risk calculations**
- Always use server-calculated lot sizes
- Enforce tier caps regardless of client requests

### 2. Balance Verification

- Load balance from authoritative source (user_registry.json)
- Cross-reference with EA heartbeat data when available
- Reject trades if balance unavailable

### 3. Slot Management

- Track slots in database, not client state
- Increment slots_in_use BEFORE firing
- Decrement slots_in_use AFTER position closes

### 4. Daily Limits

- Reset trades_used_today at daily reset time
- Use server time, not client time
- Atomic increment to prevent race conditions

## Performance

### Optimization

- Database queries are simple index lookups (fast)
- Balance loaded from JSON file (in-memory cache recommended)
- No external API calls required
- Average validation time: <10ms

### Caching Strategy

```python
# Optional: Cache tier caps to avoid repeated object access
tier_caps_cache = {
    tier: fire_validator.TIER_CAPS[tier]
    for tier in ['NIBBLER', 'FANG', 'COMMANDER']
}
```

## Monitoring & Logging

### Log Levels

- **INFO**: Successful validations with enforced parameters
- **WARNING**: Rejected requests (expected behavior)
- **ERROR**: Validation errors (database issues, missing data)

### Key Metrics to Track

1. Validation success rate by tier
2. Average lot size by tier
3. Risk cap enforcement frequency
4. Slot utilization by tier
5. Daily limit hit frequency

### Example Log Output

```
INFO:[FIRE_VALIDATOR] Validating request for user 7176191872, signal TEST_EURUSD_BUY_001
INFO:[FIRE_VALIDATOR] User 7176191872 tier: COMMANDER
INFO:[FIRE_VALIDATOR] Slots check: MANUAL 0/10 used, available=True
INFO:[FIRE_VALIDATOR] Daily ammo check: 0/6 trades used, available=True
INFO:[FIRE_VALIDATOR] Loaded balance for 7176191872: $418.27
INFO:[FIRE_VALIDATOR] Account balance: $418.27
INFO:[FIRE_VALIDATOR] Risk: requested=2.0%, enforced=0.5%
INFO:[FIRE_VALIDATOR] Lot calculation: balance=$418.27, risk=0.5% ($2.09), SL=20.0 pips, pip_value=$10.0, lot=0.0105
INFO:[FIRE_VALIDATOR] Calculated lot size: 0.01
```

## Future Enhancements

### Planned Features

1. **Dynamic Pip Values**: Real-time pip value calculation based on current exchange rates
2. **Broker-Specific Limits**: Different lot size limits per broker
3. **Position Correlation**: Check for hedging/correlation across positions
4. **Drawdown Protection**: Block trades if daily/weekly drawdown exceeds limit
5. **Time-Based Restrictions**: Prevent trading during high-impact news events
6. **Multi-Account Support**: Validate across multiple connected accounts

### API Versioning

Current version: v1.0 (October 9, 2025)

Future versions will maintain backward compatibility with v1 response structure.

## Troubleshooting

### Issue: Wrong risk being enforced

**Check**:
1. User's `risk_per_trade` in database
2. Tier caps in `fire_validator.TIER_CAPS`
3. Client request `risk_pct` value

**Debug**:
```python
result = fire_validator.validate_fire_request(...)
print(result['validation_details']['risk_calculation'])
```

### Issue: Lot size too small/large

**Check**:
1. Account balance in user_registry.json
2. Stop loss pips from signal
3. Pip value for symbol

**Debug**:
```python
# Check logs for lot calculation details
# Example: "Lot calculation: balance=$418.27, risk=0.5% ($2.09),
#           SL=20.0 pips, pip_value=$10.0, lot=0.0105"
```

### Issue: Always getting "User not found"

**Check**:
1. User exists in `/root/HydraX-v2/data/fire_modes.db`
2. Query using correct user_id format
3. Database file permissions

**Solution**:
```bash
# Check if user exists
sqlite3 /root/HydraX-v2/data/fire_modes.db \
  "SELECT user_id, subscription_tier FROM user_fire_modes WHERE user_id='7176191872';"
```

## Support

For issues or questions:
1. Check logs in `/root/HydraX-v2/logs/`
2. Run test suite: `python3 test_fire_validator.py`
3. Verify database schema matches documentation
4. Review integration code for correct usage

---

**Last Updated**: October 9, 2025
**Maintainer**: BITTEN Development Team
**File**: `/root/HydraX-v2/src/bitten_core/fire_validator.py`
