#!/usr/bin/env python3
"""
BITTEN Minimal Alert System
Just enough info to know if you can shoot - no spam
Creates curiosity for upgrades without wasting time
"""

# Actual pairs from fire_router.py
CORE_PAIRS = ["GBPUSD", "USDCAD", "GBPJPY", "EURUSD", "USDJPY"]
EXTRA_PAIRS = ["AUDUSD", "NZDUSD", "AUDJPY", "EURJPY", "EURGBP", "GBPCHF", "USDCHF"]


def format_minimal_alert(tcs_score, signal_type, user_tier):
    """
    Ultra-minimal alert format
    Just TCS% and whether they can shoot
    No pairs, no prices - that's in mission brief
    """

    # Visual indicator based on TCS
    if tcs_score >= 85:
        visual = "💎"  # Diamond = SNIPER opportunity
    elif tcs_score >= 77:
        visual = "⭐"  # Star = Solid shot
    else:
        visual = "🎯"  # Target = Standard arcade

    # Can this tier shoot this signal?
    can_shoot = True
    access_msg = ""

    if signal_type == "SNIPER" and user_tier == "NIBBLER":
        can_shoot = False
        access_msg = "🔒 FANG+"  # Locked, needs FANG or higher

    # Format: Just visual + TCS% + access indicator
    if can_shoot:
        # They can shoot - just show TCS
        message = f"{visual} {tcs_score}%"
    else:
        # They can't shoot - show lock
        message = f"{visual} {tcs_score}% {access_msg}"

    return message, can_shoot


def get_alert_variants():
    """Show different alert examples"""

    examples = {
        "NIBBLER seeing RAPID_ASSAULT": {
            "tcs": 75,
            "type": "RAPID_ASSAULT",
            "tier": "NIBBLER",
            "alert": "🎯 75%",
            "can_shoot": True,
            "note": "Can shoot - no lock shown",
        },
        "NIBBLER seeing SNIPER": {
            "tcs": 87,
            "type": "SNIPER",
            "tier": "NIBBLER",
            "alert": "💎 87% 🔒 FANG+",
            "can_shoot": False,
            "note": "Can't shoot - shows upgrade tier needed",
        },
        "FANG seeing SNIPER": {
            "tcs": 88,
            "type": "SNIPER",
            "tier": "FANG",
            "alert": "💎 88%",
            "can_shoot": True,
            "note": "Can shoot - no lock",
        },
        "COMMANDER AUTO mode": {
            "tcs": 92,
            "type": "SNIPER",
            "tier": "COMMANDER",
            "alert": "💎 92%",
            "can_shoot": True,
            "note": "Auto-fires at 90%+ in AUTO mode",
        },
        "COMMANDER SEMI mode": {
            "tcs": 78,
            "type": "RAPID_ASSAULT",
            "tier": "COMMANDER",
            "alert": "🎯 78%",
            "can_shoot": True,
            "note": "Can manually fire at 75%+ in SEMI",
        },
    }

    return examples


# Alternative even MORE minimal format
def format_ultra_minimal(tcs_score, can_shoot):
    """
    ULTRA minimal - just number and lock if needed
    """
    if can_shoot:
        return f"{tcs_score}%"
    else:
        return f"{tcs_score}% 🔒"


# WebApp button logic
def get_button_text(can_shoot, user_tier):
    """
    Button text based on access
    """
    if can_shoot:
        return "VIEW INTEL"  # They can shoot
    else:
        if user_tier == "NIBBLER":
            return "VIEW (FANG+ ONLY)"  # Educational but clear
        else:
            return "VIEW INTEL"  # Shouldn't happen but safe default


if __name__ == "__main__":
    print("=== BITTEN MINIMAL ALERTS ===\n")

    print("CONCEPT: Just enough to know if you can shoot")
    print("No pairs, no prices - just TCS% and access\n")

    examples = get_alert_variants()

    for name, data in examples.items():
        print(f"{name}:")
        print(f"  Alert: {data['alert']}")
        print(f"  Note: {data['note']}")
        print()

    print("\nULTRA MINIMAL VERSION:")
    print("Can shoot: 87%")
    print("Can't shoot: 87% 🔒")

    print("\nKEY POINTS:")
    print("• No pair names (in mission brief)")
    print("• No prices (in mission brief)")
    print("• Just TCS% to show quality")
    print("• Lock icon ONLY if they can't shoot")
    print("• Creates curiosity without spam")

    print("\nACCESS RULES:")
    print("• NIBBLER: 70%+ RAPID_ASSAULT only")
    print("• FANG/COMMANDER/: All signals")
    print("• AUTO mode: 90%+ filter (safety)")
    print("• SEMI mode: 75%+ filter (more shots)")
