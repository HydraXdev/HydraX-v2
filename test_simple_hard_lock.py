#!/usr/bin/env python3
"""
Simple test showing the corrected HARD LOCK implementation
Based on bitmode settings only - no unauthorized features
"""

# Bitmode settings from user
BITMODE = {
    'risk_default': 2.0,      # 2% default risk
    'risk_boost': 2.5,        # 2.5% boost risk
    'boost_min_balance': 500, # Boost available at $500+
    'drawdown_cap': 6         # 6% daily cap
}

def hard_lock_check(lot_size, stop_loss_pips, account_balance, daily_loss=0):
    """
    Simple hard lock validation based on bitmode settings
    Returns (allowed, reason)
    """
    # Calculate risk
    pip_value_per_lot = 10  # $10 per pip per lot
    risk_amount = lot_size * stop_loss_pips * pip_value_per_lot
    risk_percent = (risk_amount / account_balance) * 100
    
    # Determine max allowed risk
    if account_balance >= BITMODE['boost_min_balance']:
        max_risk = BITMODE['risk_boost']  # 2.5%
        mode = "boost"
    else:
        max_risk = BITMODE['risk_default']  # 2.0%
        mode = "default"
    
    # Check 1: Single trade risk
    if risk_percent > max_risk:
        return False, f"Trade risks {risk_percent:.1f}%, exceeds {max_risk}% ({mode} mode)"
    
    # Check 2: Daily cap
    daily_loss_percent = abs(daily_loss / account_balance * 100) if daily_loss < 0 else 0
    total_risk = daily_loss_percent + risk_percent
    
    if total_risk > BITMODE['drawdown_cap']:
        if daily_loss_percent >= BITMODE['drawdown_cap']:
            return False, f"Daily {BITMODE['drawdown_cap']}% cap reached. No more trades today."
        else:
            remaining = BITMODE['drawdown_cap'] - daily_loss_percent
            return False, f"Trade would exceed {BITMODE['drawdown_cap']}% daily cap. Only {remaining:.1f}% remaining."
    
    return True, f"Trade approved: {risk_percent:.1f}% risk"

# Test cases
print("🔒 SIMPLE HARD LOCK TEST - Bitmode Settings Only\n")
print(f"Settings: Default {BITMODE['risk_default']}%, Boost {BITMODE['risk_boost']}% (at ${BITMODE['boost_min_balance']}+), Daily cap {BITMODE['drawdown_cap']}%\n")

tests = [
    # (lot_size, stop_loss_pips, balance, daily_loss, description)
    (0.20, 100, 10000, 0, "Normal 2% risk - large account"),
    (0.25, 100, 10000, 0, "2.5% risk - should use boost mode"),
    (0.30, 100, 10000, 0, "3% risk - exceeds boost limit"),
    (0.02, 100, 400, 0, "Small account - no boost available"),
    (0.03, 100, 400, 0, "Small account - exceeds 2% limit"),
    (0.20, 100, 10000, -400, "Already down 4%, new 2% trade"),
    (0.20, 100, 10000, -600, "At 6% cap, new trade blocked"),
    (0.10, 100, 10000, -500, "Down 5%, only 1% allowed"),
]

for lots, sl, balance, loss, desc in tests:
    print(f"📊 {desc}")
    print(f"   Lots: {lots}, SL: {sl} pips, Balance: ${balance}", end="")
    if loss < 0:
        print(f", Daily P&L: ${loss}")
    else:
        print()
    
    allowed, reason = hard_lock_check(lots, sl, balance, loss)
    
    if allowed:
        print(f"   ✅ {reason}")
    else:
        print(f"   ❌ BLOCKED: {reason}")
    print()

print("\nThis is the ONLY validation that should happen:")
print("1. Check if trade risk% > allowed risk (2% or 2.5%)")
print("2. Check if daily loss + new risk > 6%")
print("3. If either fails → BLOCK (don't modify)")
print("\nNo auto-adjustment, no account minimums, no tier-specific limits.")