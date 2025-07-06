#!/usr/bin/env python3
"""
Simple test to demonstrate the HARD LOCK trade size validation logic
"""

def calculate_risk_percent(lot_size, stop_loss_pips, account_balance, pip_value_per_lot=10):
    """Calculate the risk percentage for a trade"""
    potential_loss = lot_size * stop_loss_pips * pip_value_per_lot
    risk_percent = (potential_loss / account_balance) * 100
    return risk_percent, potential_loss

def validate_hard_lock(tier, lot_size, stop_loss_pips, account_balance, daily_loss_so_far=0):
    """Validate trade against hard lock limits"""
    
    # Tier-specific risk limits (from config)
    tier_limits = {
        'NIBBLER': 2.0,      # 2% max risk per trade
        'FANG': 2.5,         # 2.5% max risk per trade
        'COMMANDER': 3.0,    # 3% max risk per trade
        'APEX': 3.0          # 3% max risk per trade
    }
    
    # Daily risk caps
    daily_caps = {
        'NIBBLER': 6.0,      # 6% daily loss limit
        'FANG': 6.0,         # 6% daily loss limit (was 8.5%)
        'COMMANDER': 10.0,   # 10% daily loss limit
        'APEX': 10.0         # 10% daily loss limit
    }
    
    # Get limits for tier
    max_risk_per_trade = tier_limits.get(tier, 2.0)
    daily_cap = daily_caps.get(tier, 6.0)
    
    # Calculate risk for this trade
    risk_percent, potential_loss = calculate_risk_percent(lot_size, stop_loss_pips, account_balance)
    
    # Calculate daily loss percentage so far
    daily_loss_percent = abs((daily_loss_so_far / account_balance) * 100) if daily_loss_so_far < 0 else 0
    
    # Check 1: Single trade risk limit
    if risk_percent > max_risk_per_trade:
        safe_lot_size = (account_balance * (max_risk_per_trade / 100)) / (stop_loss_pips * 10)
        safe_lot_size = round(safe_lot_size, 2)
        return False, f"Trade exceeds {tier} limit of {max_risk_per_trade}%. Risk: {risk_percent:.1f}%", safe_lot_size
    
    # Check 2: Daily risk cap
    total_daily_risk = daily_loss_percent + risk_percent
    if total_daily_risk > daily_cap:
        remaining_risk = max(0, daily_cap - daily_loss_percent)
        if remaining_risk <= 0:
            return False, f"Daily cap of {daily_cap}% reached. No more trades allowed.", 0
        
        safe_lot_size = (account_balance * (remaining_risk / 100)) / (stop_loss_pips * 10)
        safe_lot_size = round(safe_lot_size, 2)
        return False, f"Trade would exceed daily cap. Total: {total_daily_risk:.1f}% > {daily_cap}%", safe_lot_size
    
    # Check 3: Account preservation (never risk below $100)
    if account_balance - potential_loss < 100:
        max_allowed_loss = account_balance - 100
        safe_lot_size = max_allowed_loss / (stop_loss_pips * 10)
        safe_lot_size = round(max(0.01, safe_lot_size), 2)
        return False, f"Trade would risk account falling below $100 minimum", safe_lot_size
    
    return True, f"Trade approved. Risk: {risk_percent:.1f}% of ${account_balance}", lot_size

# Test scenarios
print("🔒 HARD LOCK TRADE SIZE VALIDATION TESTS 🔒\n")

test_cases = [
    # (tier, lot_size, stop_loss_pips, account_balance, daily_loss_so_far, description)
    ("NIBBLER", 0.20, 100, 10000, 0, "Normal 2% risk trade"),
    ("NIBBLER", 0.50, 100, 10000, 0, "5% risk - exceeds tier limit"),
    ("NIBBLER", 0.10, 100, 500, 0, "Small account - 20% risk"),
    ("APEX", 0.30, 100, 10000, 0, "APEX 3% risk - within limit"),
    ("FANG", 0.20, 100, 10000, -500, "Already down 5%, new 2% trade"),
    ("NIBBLER", 0.05, 100, 500, -25, "Small account, already down 5%"),
    ("COMMANDER", 0.50, 100, 10000, -800, "Would exceed 10% daily cap"),
]

for tier, lots, sl_pips, balance, daily_loss, desc in test_cases:
    print(f"\n📊 {desc}")
    print(f"   Tier: {tier}, Account: ${balance}, Lots: {lots}, SL: {sl_pips} pips")
    if daily_loss < 0:
        print(f"   Daily P&L: ${daily_loss} ({abs(daily_loss/balance*100):.1f}% loss)")
    
    is_valid, message, safe_lots = validate_hard_lock(tier, lots, sl_pips, balance, daily_loss)
    
    if is_valid:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        if safe_lots > 0:
            print(f"   💡 Suggested safe lot size: {safe_lots}")

print("\n\n📝 SUMMARY:")
print("The hard lock system prevents:")
print("1. Any single trade from exceeding tier-specific risk limits")
print("2. Daily losses from exceeding the cap (6% for Nibbler/Fang, 10% for Commander/Apex)")
print("3. Account balance from falling below $100")
print("\nTrade sizes are automatically adjusted to safe levels when possible.")