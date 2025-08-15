# 🌍 Offshore Signal Infrastructure

**Implementation Date**: August 1, 2025  
**Status**: ✅ COMPLETE - Infrastructure ready for XAUUSD private routing

## Overview

This infrastructure enables private delivery of XAUUSD (GOLD) signals to offshore users only. US-based users will not receive these signals to comply with regulations.

## User Model Extensions

### UserRegistryManager Updates (`/src/bitten_core/user_registry_manager.py`)

Added two new fields to user profiles:
- `user_region`: string - Either `"US"` or `"INTL"` (default: `"US"`)
- `offshore_opt_in`: boolean - User consent for offshore signals (default: `false`)

### New Methods Added:

```python
# Update user's region
update_user_region(telegram_id: str, region: str) -> bool

# Update offshore opt-in status  
update_offshore_opt_in(telegram_id: str, opt_in: bool) -> bool
```

## Telegram Bot Extensions

### BittenProductionBot Updates (`/bitten_production_bot.py`)

#### 1. **send_dm_signal()** - Private Signal Delivery
```python
def send_dm_signal(telegram_id: str, signal_text: str, parse_mode: str = "MarkdownV2") -> bool
```
- Sends private signals to specific users
- Automatically adds "🔒 Private Signal (Offshore Only)" header for XAUUSD/GOLD signals
- Returns True on success, False on failure

#### 2. **lookup_telegram_id()** - User ID Mapping  
```python
def lookup_telegram_id(user_id: str) -> Optional[str]
```
- Maps internal user_id to telegram_id using registry
- Returns None if user not found

#### 3. **is_offshore_eligible()** - Eligibility Check
```python
def is_offshore_eligible(telegram_id: str) -> bool
```
- Checks if user can receive offshore signals
- Requirements: `user_region == "INTL"` AND `offshore_opt_in == True`

## Usage Examples

### Setting Up a User for Offshore Signals
```python
from src.bitten_core.user_registry_manager import update_user_region, update_offshore_opt_in

# Mark user as international
update_user_region("7176191872", "INTL")

# Enable offshore signals
update_offshore_opt_in("7176191872", True)
```

### Checking Eligibility
```python
# In signal distribution logic
if bot.is_offshore_eligible(telegram_id):
    bot.send_dm_signal(telegram_id, xauusd_signal_text)
```

### Sending Private Signal
```python
# Format signal text
signal_text = """
🎯 **ELITE SIGNAL - XAUUSD** 🎯

📊 **Pattern**: Liquidity Sweep Reversal
💰 **Symbol**: XAUUSD (GOLD)
📈 **Direction**: BUY
💵 **Entry**: 2411.50
🛑 **Stop Loss**: 2405.00
🎯 **Take Profit**: 2424.50
📐 **Risk/Reward**: 1:2

⚡ **Signal Type**: PRECISION_STRIKE
🛡️ **CITADEL Score**: 8.5/10
"""

# Send to eligible user
bot.send_dm_signal("7176191872", signal_text)
```

## Current User Status

As of testing:
- User `7176191872` (Chris): `INTL` region, offshore opt-in ✅ ELIGIBLE
- User `222222222` (Test INTL): `INTL` region, offshore opt-in ✅ ELIGIBLE  
- User `111111111` (Test US): `US` region, offshore opt-in ❌ NOT ELIGIBLE

## Security Considerations

1. **Default Safe**: New users default to `US` region with offshore disabled
2. **Double Opt-in**: Users must be INTL region AND explicitly opt-in
3. **Audit Trail**: All region/opt-in changes are logged
4. **No US Access**: US users cannot receive XAUUSD signals even if opted in

## Integration Points

The infrastructure is ready for integration with:
- Elite Guard signal distribution
- VENOM signal generation 
- CITADEL Shield filtering
- WebApp user settings page

## Next Steps

To route XAUUSD signals privately:
1. Modify Elite Guard to check symbol == "XAUUSD"
2. Get list of offshore-eligible users
3. Use `send_dm_signal()` instead of group broadcast
4. Log delivery for compliance

---

**Status**: Infrastructure complete and tested. Ready for XAUUSD routing implementation.