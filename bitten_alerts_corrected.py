#!/usr/bin/env python3
"""
BITTEN Alerts - CORRECTED VERSION
NIBBLER can shoot ANY TCS - the filter is WHICH signals they receive
"""

def format_bitten_alert(tcs_score, filter_type, user_tier):
    """
    Minimal alert - just TCS and lock if needed
    
    Filter types:
    1. SHORT (1-35 min) - Any TCS, all tiers get these
    2. SNIPER (90-100 min) - 80%+ only, FANG+ only
    """
    
    # Visual based on TCS only
    if tcs_score >= 90:
        visual = "💎"  # Diamond 
    elif tcs_score >= 85:
        visual = "⭐"  # Star
    else:
        visual = "🎯"  # Target
    
    # Access check - ONLY lock SNIPER shots from NIBBLER
    if filter_type == "SNIPER" and user_tier == "NIBBLER":
        # NIBBLER can't access sniper filter
        return f"{visual} {tcs_score}% 🔒 FANG+"
    else:
        # Everyone else just sees TCS
        return f"{visual} {tcs_score}%"

# Examples showing the CORRECT system
CORRECT_EXAMPLES = [
    # SHORT SCALPS - NIBBLER CAN SHOOT ALL OF THESE
    {"tcs": 72, "filter": "SHORT", "tier": "NIBBLER", "alert": "🎯 72%", "note": "NIBBLER CAN shoot low TCS shorts"},
    {"tcs": 89, "filter": "SHORT", "tier": "NIBBLER", "alert": "⭐ 89%", "note": "NIBBLER CAN shoot high TCS shorts"},
    {"tcs": 98, "filter": "SHORT", "tier": "NIBBLER", "alert": "💎 98%", "note": "NIBBLER CAN shoot ANY TCS short!"},
    
    # SNIPER SHOTS - NIBBLER LOCKED OUT
    {"tcs": 87, "filter": "SNIPER", "tier": "NIBBLER", "alert": "⭐ 87% 🔒 FANG+", "note": "SNIPER filter locked"},
    {"tcs": 92, "filter": "SNIPER", "tier": "NIBBLER", "alert": "💎 92% 🔒 FANG+", "note": "SNIPER filter locked"},
    
    # FANG+ ACCESS
    {"tcs": 87, "filter": "SNIPER", "tier": "FANG", "alert": "⭐ 87%", "note": "FANG can access sniper"},
    {"tcs": 92, "filter": "SNIPER", "tier": "COMMANDER", "alert": "💎 92%", "note": "COMMANDER AUTO would fire"},
]

def explain_system():
    """Explain the actual system"""
    
    print("=== BITTEN SIGNAL SYSTEM (CORRECTED) ===\n")
    
    print("TWO FILTERS (not quality tiers!):")
    print("1. SHORT SCALPS (1-35 min) - ANY TCS level")
    print("2. SNIPER SHOTS (90-100 min) - Always 80%+ TCS\n")
    
    print("TIER ACCESS:")
    print("• NIBBLER: SHORT scalps only (can be 70% or 98%!)")
    print("• FANG+: BOTH filters (shorts + snipers)\n")
    
    print("KEY POINT: NIBBLER can shoot ANY TCS!")
    print("They're limited by WHICH signals, not TCS level\n")
    
    print("AUTO/SEMI (COMMANDER/APEX only):")
    print("• AUTO mode: Fires at 90%+ automatically")
    print("• SEMI mode: Manual, can fire at 85%+ snipers\n")

if __name__ == "__main__":
    explain_system()
    
    print("EXAMPLE ALERTS:")
    print("-" * 40)
    
    for ex in CORRECT_EXAMPLES:
        print(f"\n{ex['filter']} signal, {ex['tier']} user:")
        print(f"Alert: {ex['alert']}")
        print(f"Note: {ex['note']}")
    
    print("\n\nSUMMARY:")
    print("• SHORT scalps: Any TCS, all tiers")
    print("• SNIPER shots: 85%+ only, FANG+ only")
    print("• NIBBLER gets high-quality shorts too!")
    print("• Lock ONLY shows on sniper shots they can't access")