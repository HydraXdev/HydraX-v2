#!/usr/bin/env python3
"""
BITTEN Alert System - FINAL VERSION
Users decide what TCS they want to see
Shows what they're missing to create upgrade desire
"""


def format_telegram_alert(tcs_score, signal_filter, user_tier):
    """
    Super minimal Telegram alert
    Just TCS% and lock if it's a SNIPER they can't access
    """

    # Visual indicator for quick scanning
    if tcs_score >= 90:
        visual = "💎"
    elif tcs_score >= 85:
        visual = "⭐"
    elif tcs_score >= 77:
        visual = "🎯"
    else:
        visual = "⚡"  # Lower but still valid

    # Base alert
    alert = f"{visual} {tcs_score}%"

    # Only add lock if it's SNIPER and they're NIBBLER
    if signal_filter == "SNIPER" and user_tier == "NIBBLER":
        alert += " 🔒 FANG+"

    return alert


def get_user_preference_system():
    """
    How users can set their own TCS preferences
    """
    return {
        "commands": {
            "/alerts": "Set your minimum TCS filter",
            "/alerts 80": "Only see 80%+ signals",
            "/alerts 85": "Only see 85%+ signals",
            "/alerts all": "See all signals (default)",
        },
        "examples": {
            "Power user wants 85%+": {
                "setting": "/alerts 85",
                "sees": ["💎 92%", "⭐ 87%"],
                "misses": ["🎯 78%", "⚡ 72%"],
            },
            "Active trader wants 80%+": {
                "setting": "/alerts 80",
                "sees": ["💎 92%", "⭐ 87%", "🎯 82%"],
                "misses": ["⚡ 72%", "⚡ 75%"],
            },
            "Beginner wants all": {"setting": "/alerts all", "sees": "Everything", "misses": "Nothing"},
        },
    }


def create_alert_batch_example():
    """
    Show how alerts look in Telegram
    Clean, scannable, no spam
    """

    # Example signal batch
    signals = [
        {"tcs": 92, "filter": "SNIPER", "duration": "90 min"},
        {"tcs": 87, "filter": "SHORT", "duration": "20 min"},
        {"tcs": 78, "filter": "SHORT", "duration": "15 min"},
        {"tcs": 95, "filter": "SNIPER", "duration": "95 min"},
        {"tcs": 72, "filter": "SHORT", "duration": "10 min"},
    ]

    print("=== TELEGRAM ALERT STREAM ===\n")

    # Show for different users
    for user_type in ["NIBBLER", "FANG", "COMMANDER"]:
        print(f"{user_type} sees:")
        print("-" * 30)

        for sig in signals:
            alert = format_telegram_alert(sig["tcs"], sig["filter"], user_type)

            # Add context for this example
            if "🔒" in alert:
                context = f" (SNIPER: {sig['duration']})"
            else:
                context = f" ({sig['filter']}: {sig['duration']})"

            print(f"{alert}{context}")

        print()


def explain_upgrade_psychology():
    """
    How the system creates upgrade desire
    """

    print("\n=== UPGRADE PSYCHOLOGY ===\n")

    print("NIBBLER sees these alerts:")
    print("💎 92%          <- Can shoot! (short)")
    print("⭐ 87% 🔒 FANG+  <- Can't shoot (sniper)")
    print("🎯 78%          <- Can shoot! (short)")
    print("💎 95% 🔒 FANG+  <- Can't shoot (sniper)")

    print("\nCreates natural curiosity:")
    print("• 'Why are these locked?'")
    print("• 'What's special about FANG+?'")
    print("• 'These high TCS must be good...'")

    print("\nNo spam needed - the lock speaks for itself!")


def show_webapp_flow():
    """
    What happens when they click
    """

    print("\n=== WEBAPP FLOW ===\n")

    print("1. User sees: 💎 92% 🔒 FANG+")
    print("2. Clicks 'VIEW INTEL' (curious)")
    print("3. WebApp shows full mission brief")
    print("4. Tries to fire → 'This is a SNIPER mission. Upgrade to FANG+ for access.'")
    print("5. Shows upgrade benefits clearly")

    print("\nKey: Let them SEE what they're missing!")


if __name__ == "__main__":
    print("=== BITTEN FINAL ALERT SYSTEM ===\n")

    print("CORE CONCEPT:")
    print("• Minimal alerts (just TCS%)")
    print("• Users filter by preference")
    print("• Locks create upgrade desire")
    print("• No spam, just information\n")

    # Show example stream
    create_alert_batch_example()

    # Show preference system
    prefs = get_user_preference_system()
    print("\n=== USER PREFERENCES ===")
    for cmd, desc in prefs["commands"].items():
        print(f"{cmd} - {desc}")

    # Explain psychology
    explain_upgrade_psychology()

    # Show webapp flow
    show_webapp_flow()

    print("\n=== IMPLEMENTATION SUMMARY ===")
    print("✅ NIBBLER can shoot ANY TCS short scalp")
    print("✅ SNIPER shots always 85%+ (FANG+ only)")
    print("✅ Users set their own TCS filter")
    print("✅ Minimal alerts reduce noise")
    print("✅ Locks create natural upgrade path")
