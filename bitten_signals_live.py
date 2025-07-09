#!/usr/bin/env python3
"""
BITTEN Live Signal System
Based on ACTUAL tier_settings.yml configuration
Two signal types: ARCADE (quick) and SNIPER (precision)
"""

# From actual tier_settings.yml
SIGNAL_TYPES = {
    "ARCADE": {
        "tcs_requirements": {
            "NIBBLER": 70,
            "FANG": 75,
            "COMMANDER": 75,  # Can use semi-mode
            "APEX": 75
        },
        "duration": "1-35 min",
        "description": "Quick scalp"
    },
    "SNIPER": {
        "tcs_requirements": {
            "NIBBLER": None,  # No access
            "FANG": 85,
            "COMMANDER": 85,
            "APEX": 85
        },
        "duration": "90-100 min",
        "description": "Precision shot"
    }
}

def get_tcs_visual(tcs_score):
    """Get visual indicator based on TCS (from actual system)"""
    if tcs_score >= 85:
        return "💎"  # SNIPER GRADE
    elif tcs_score >= 77:
        return "⭐"  # PRECISION
    elif tcs_score >= 70:
        return "☠️"  # RISKY
    else:
        return "⚠️"  # STANDARD

def determine_signal_type(tcs_score, market_conditions):
    """
    Determine if signal is ARCADE or SNIPER
    Based on TCS and market conditions
    """
    # SNIPER requires 85%+ TCS AND proper market conditions
    if tcs_score >= 85 and market_conditions.get('strong_trend', False):
        return "SNIPER"
    
    # ARCADE for faster opportunities
    if tcs_score >= 70:
        return "ARCADE"
        
    return None

def format_bitten_signal(signal_data):
    """
    Format signal for Telegram - 2 lines MAX
    Clean, tactical, professional
    """
    tcs = int(signal_data['confidence'] * 100)
    visual = get_tcs_visual(tcs)
    
    # Determine signal type
    signal_type = "SNIPER" if tcs >= 85 else "ARCADE"
    
    # Format: Visual + Pair + Direction + TCS%
    # Second line: Entry @ price • Signal type
    
    message = f"{visual} {signal_data['symbol']} {signal_data['direction']} [{tcs}%]\n"
    message += f"@ {signal_data['entry_price']:.5f} • {signal_type}"
    
    return message, signal_type

def check_user_access(user_tier, signal_type):
    """
    Check if user tier can access signal type
    Based on actual tier_settings.yml
    """
    if user_tier == "NIBBLER" and signal_type == "SNIPER":
        return False, "🔒 SNIPER requires FANG+ • /upgrade"
    
    # Check TCS requirements
    required_tcs = SIGNAL_TYPES[signal_type]["tcs_requirements"].get(user_tier)
    if required_tcs is None:
        return False, f"No {signal_type} access for {user_tier}"
        
    return True, "Access granted"

def get_webapp_button_data(signal_id, user_tier, signal_type):
    """
    Create WebApp button data based on tier
    NIBBLER seeing SNIPER gets upgrade prompt
    """
    if user_tier == "NIBBLER" and signal_type == "SNIPER":
        return {
            "action": "upgrade_prompt",
            "signal_id": signal_id,
            "message": "SNIPER signals require FANG tier or higher"
        }
    
    return {
        "action": "view_mission",
        "signal_id": signal_id,
        "signal_type": signal_type,
        "user_tier": user_tier
    }

# Example alerts showing actual system behavior
EXAMPLE_SIGNALS = [
    # ARCADE - All tiers can see/trade
    {
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.08453,
        "confidence": 0.72,
        "expected_format": "☠️ EURUSD BUY [72%]\n@ 1.08453 • ARCADE",
        "nibbler_access": True
    },
    # ARCADE - Higher quality but still arcade
    {
        "symbol": "GBPUSD",
        "direction": "SELL", 
        "entry_price": 1.26789,
        "confidence": 0.82,
        "expected_format": "⭐ GBPUSD SELL [82%]\n@ 1.26789 • ARCADE",
        "nibbler_access": True
    },
    # SNIPER - NIBBLER cannot access
    {
        "symbol": "USDJPY",
        "direction": "BUY",
        "entry_price": 149.234,
        "confidence": 0.87,
        "expected_format": "💎 USDJPY BUY [87%]\n@ 149.23400 • SNIPER",
        "nibbler_access": False
    },
    # SNIPER - High confidence
    {
        "symbol": "AUDUSD",
        "direction": "SELL",
        "entry_price": 0.65432,
        "confidence": 0.92,
        "expected_format": "💎 AUDUSD SELL [92%]\n@ 0.65432 • SNIPER", 
        "nibbler_access": False
    }
]

if __name__ == "__main__":
    print("=== BITTEN LIVE SIGNAL SYSTEM ===")
    print("(Based on actual tier_settings.yml)\n")
    
    # Test signal formatting
    for signal in EXAMPLE_SIGNALS:
        message, signal_type = format_bitten_signal(signal)
        print(f"{signal_type} Signal:")
        print(message)
        
        # Check NIBBLER access
        if signal['nibbler_access']:
            print("✅ NIBBLER can trade")
        else:
            print("🔒 NIBBLER blocked (upgrade required)")
        print()
    
    print("\nACTUAL SYSTEM RULES:")
    print("• NIBBLER: ARCADE only (70%+ TCS)")
    print("• FANG: ARCADE (75%+) + SNIPER (85%+)")
    print("• COMMANDER/APEX: Same as FANG + auto modes")
    print("\nSIGNAL DURATIONS:")
    print("• ARCADE: 1-35 min scalps")
    print("• SNIPER: 90-100 min precision")