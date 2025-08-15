# Corrected Hard Lock Logic

## What You Asked For:
"Add a hard lock that prevents a trade from executing if the trade size (lot size × stop loss) exceeds the safe percentage of the current account balance."

## Your Bitmode Settings:
```yaml
bitmode:
  risk_default: 2.0      # Default 2% risk
  risk_boost: 2.5        # Boost mode 2.5% risk
  drawdown_cap: 6        # 6% daily cap for bitmode
```

## Simple Hard Lock Logic:

### For Each Trade:
1. Calculate actual risk: `risk = (lot_size × stop_loss_pips × pip_value) / account_balance × 100`
2. Check if risk > allowed risk (2.0% or 2.5% in boost mode)
3. If yes → **BLOCK THE TRADE** (don't modify it)

### Daily Cap Check:
1. Calculate daily loss so far
2. If daily_loss + new_trade_risk > drawdown_cap (6%) → **BLOCK THE TRADE**

## What Should NOT Happen:
- ❌ Auto-adjusting trade sizes (users set their own sizes)
- ❌ Account preservation minimums (not requested)
- ❌ Different limits per tier (use bitmode settings)

## Correct Implementation:
```python
def hard_lock_check(lot_size, stop_loss_pips, account_balance, daily_loss_so_far):
    # Calculate risk
    risk_amount = lot_size * stop_loss_pips * 10  # $10 per pip per lot
    risk_percent = (risk_amount / account_balance) * 100
    
    # Check 1: Single trade risk
    max_risk = 2.5 if boost_mode else 2.0  # From bitmode settings
    if risk_percent > max_risk:
        return False, f"Trade risks {risk_percent:.1f}%, exceeds {max_risk}% limit"
    
    # Check 2: Daily cap
    daily_loss_percent = abs(daily_loss_so_far / account_balance * 100)
    if daily_loss_percent + risk_percent > 6.0:  # bitmode drawdown_cap
        return False, f"Would exceed 6% daily cap"
    
    return True, "Trade approved"
```

This is ALL that should happen - simple blocking based on your bitmode risk settings.