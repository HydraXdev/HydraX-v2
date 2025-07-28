#!/usr/bin/env python3
"""
BITTEN Alert System - Based on ACTUAL implementation
Using existing RAPID_ASSAULT/SNIPER signal types and tier access
"""

# From actual BITTEN system
TCS_GRADES = {
    "SNIPER": {"min": 85, "emoji": "💎", "name": "SNIPER"},
    "PRECISION": {"min": 77, "emoji": "⭐", "name": "PRECISION"},
    "RISKY": {"min": 70, "emoji": "☠️", "name": "RISKY"},
    "STANDARD": {"min": 0, "emoji": "⚠️", "name": "STANDARD"}
}

# Actual tier configs from system
TIER_ACCESS = {
    "NIBBLER": {
        "has_sniper_access": False,
        "min_tcs": 70,
        "arcade_tcs": 70
    },
    "FANG": {
        "has_sniper_access": True,
        "min_tcs": 75,  # for arcade
        "sniper_tcs": 85
    },
    "COMMANDER": {
        "has_sniper_access": True,
        "min_tcs": 90,
        "has_autofire": True
    }: {
        "has_sniper_access": True,
        "min_tcs": 91,
        "has_autofire": True
    }
}

def get_tcs_grade(tcs_score):
    """Get TCS grade emoji based on score"""
    if tcs_score >= 85:
        return "💎"
    elif tcs_score >= 77:
        return "⭐"
    elif tcs_score >= 70:
        return "☠️"
    else:
        return "⚠️"

def format_bitten_alert(signal_data):
    """
    Format alert based on actual BITTEN system
    2 lines MAX, shows signal type (RAPID_ASSAULT/SNIPER)
    """
    
    tcs = int(signal_data['confidence'] * 100)
    grade_emoji = get_tcs_grade(tcs)
    
    # Determine if RAPID_ASSAULT or SNIPER based on TCS
    signal_type = "SNIPER" if tcs >= 85 else "RAPID_ASSAULT"
    
    # Line 1: Grade emoji + Pair + Direction + TCS
    # Line 2: Entry price + Signal type
    
    message = f"{grade_emoji} {signal_data['symbol']} {signal_data['direction']} [{tcs}%]\n"
    message += f"@ {signal_data['entry_price']:.5f} • {signal_type}"
    
    return message, signal_type

def check_tier_access(user_tier, signal_type, tcs_score):
    """
    Check if user can trade this signal based on actual tier rules
    """
    tier_config = TIER_ACCESS.get(user_tier)
    
    # NIBBLER can't access SNIPER at all
    if user_tier == "NIBBLER" and signal_type == "SNIPER":
        return False, "SNIPER signals require FANG+ tier"
    
    # Check TCS requirements
    if user_tier == "FANG":
        if signal_type == "SNIPER" and tcs_score < 85:
            return False, "SNIPER requires 85% TCS"
        elif signal_type == "RAPID_ASSAULT" and tcs_score < 75:
            return False, "RAPID_ASSAULT requires 75% TCS for FANG"
    else:
        if tcs_score < tier_config['min_tcs']:
            return False, f"TCS below {user_tier} minimum ({tier_config['min_tcs']}%)"
    
    return True, "Access granted"

# Example alerts matching actual system
EXAMPLE_ALERTS = [
    # NIBBLER can see/trade these RAPID_ASSAULT signals
    {"symbol": "EURUSD", "direction": "BUY", "entry_price": 1.08453, "confidence": 0.72, "tier_access": "ALL"},
    {"symbol": "GBPUSD", "direction": "SELL", "entry_price": 1.26789, "confidence": 0.78, "tier_access": "ALL"},
    
    # FANG+ only SNIPER signals  
    {"symbol": "USDJPY", "direction": "BUY", "entry_price": 149.234, "confidence": 0.87, "tier_access": "FANG+"},
    {"symbol": "AUDUSD", "direction": "SELL", "entry_price": 0.65432, "confidence": 0.92, "tier_access": "FANG+"}]

if __name__ == "__main__":
    print("=== BITTEN ALERTS (ACTUAL SYSTEM) ===\n")
    
    for signal in EXAMPLE_ALERTS:
        message, signal_type = format_bitten_alert(signal)
        print(f"{signal_type} Signal:")
        print(message)
        print(f"Access: {signal['tier_access']}")
        print()
    
    print("\nACTUAL TIER RULES:")
    print("• NIBBLER: RAPID_ASSAULT only (no SNIPER access)")
    print("• FANG: Both RAPID_ASSAULT (75%+) and SNIPER (85%+)")
    print("• COMMANDER/: All signals with higher TCS minimums")
    
    print("\nVISUAL TCS GRADES:")
    print("💎 85%+ SNIPER GRADE")
    print("⭐ 77-84% PRECISION")
    print("☠️ 70-76% RISKY")
    print("⚠️ <70% STANDARD")