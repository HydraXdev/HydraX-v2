#!/usr/bin/env python3
"""
BITTEN Alerts - AAA Game Design Version
What would Call of Duty/Fortnite/CS:GO do?
"""


def analyze_top_games():
    """What makes top games addictive"""

    patterns = {
        "Call of Duty": {
            "hooks": [
                "KILLSTREAK notifications",
                "UAV ONLINE callouts",
                "TACTICAL NUKE INCOMING",
                "MISSION STATUS updates",
            ],
            "psychology": "Military authenticity + progression feedback",
        },
        "Fortnite": {
            "hooks": ["STORM CLOSING alerts", "LEGENDARY CHEST nearby", "SUPPLY DROP incoming", "ZONE ROTATION"],
            "psychology": "FOMO + rarity excitement",
        },
        "CS:GO": {
            "hooks": ["BOMB PLANTED", "LAST PLAYER STANDING", "CLUTCH OR KICK", "ECO ROUND"],
            "psychology": "High stakes + team pressure",
        },
    }

    return patterns


# BITTEN AAA Alert Designs (2 lines each)

# Option 1: MISSION STATUS
arcade_mission = """🔫 TACTICAL ALERT
Strike Opportunity 78%"""

sniper_mission = """⚡ PRECISION REQUIRED
Overwatch Position 87%"""

# Option 2: INCOMING/ACTIVE
arcade_incoming = """🔫 INCOMING RAID
Confidence Level: 78%"""

sniper_incoming = """⚡ SNIPER ACTIVE
Target Acquired: 87%"""

# Option 3: URGENCY + REWARD
arcade_urgency = """🔫 RAPID DEPLOYMENT [78%]
⏱️ Window: 30 min"""

sniper_urgency = """⚡ HIGH VALUE TARGET [87%]
🎯 Precision: FANG+ Only"""

# Option 4: CALLSIGN + STATUS
arcade_callsign = """ALPHA-6 • WEAPONS FREE
🔫 Strike Ready [78%]"""

sniper_callsign = """EAGLE-1 • TARGET LOCKED
⚡ Awaiting Authorization [87%]"""

# Option 5: ZONE/SECTOR (like BR games)
arcade_zone = """🔫 SECTOR 7 ACTIVE
Combat Probability: 78%"""

sniper_zone = """⚡ RESTRICTED ZONE
Elite Access Only: 87%"""


def show_game_psychology():
    """What we're missing vs top games"""

    print("=== WHAT TOP GAMES DO ===\n")

    print("1. URGENCY without spam:")
    print("   - Time pressure")
    print("   - Limited windows")
    print("   - 'Last chance' feel\n")

    print("2. STATUS/PROGRESS feel:")
    print("   - 'ALPHA-6 ONLINE'")
    print("   - 'SECTOR 7 HOT'")
    print("   - Makes user feel part of ops\n")

    print("3. RARITY/SPECIAL indicators:")
    print("   - 'LEGENDARY'")
    print("   - 'ELITE ONLY'")
    print("   - 'RESTRICTED ACCESS'\n")

    print("4. COLLECTIVE ACTION:")
    print("   - '3 OPERATORS ENGAGING'")
    print("   - 'SQUAD DEPLOYING'")
    print("   - Social proof\n")


def create_final_recommendations():
    """Best 2-line formats based on psychology"""

    recommendations = [
        {
            "name": "MILITARY OPS",
            "arcade": "🔫 STRIKE TEAM DEPLOYING\nTarget Confidence: 78%",
            "sniper": "⚡ OVERWATCH POSITION\nElite Authorization: 87%",
        },
        {
            "name": "URGENCY PLAY",
            "arcade": "🔫 RAPID ASSAULT [78%]\n⏱️ 30 MIN WINDOW",
            "sniper": "⚡ PRECISION SHOT [87%]\n🎖️ FANG+ CERTIFIED",
        },
        {
            "name": "ZONE CONTROL",
            "arcade": "🔫 HOT ZONE ACTIVE\nEngagement Level: 78%",
            "sniper": "⚡ RESTRICTED SECTOR\nClearance Required: 87%",
        },
        {
            "name": "SQUAD DYNAMICS",
            "arcade": "🔫 FIRETEAM READY\n3 Operators • 78% GO",
            "sniper": "⚡ SNIPER NEST LOCATED\nElite Squad Only • 87%",
        },
    ]

    return recommendations


def test_formats():
    """Generate test messages"""

    print("\n=== AAA GAME DESIGN OPTIONS ===\n")

    recs = create_final_recommendations()

    for i, rec in enumerate(recs, 1):
        print(f"OPTION {i}: {rec['name']}")
        print("-" * 40)
        print("RAPID_ASSAULT:")
        print(rec["arcade"])
        print("\nSNIPER:")
        print(rec["sniper"])
        print("\n")

    print("=== PSYCHOLOGY ELEMENTS ===")
    print("✓ Urgency (time windows)")
    print("✓ Social proof (X operators)")
    print("✓ Status/Rank (Elite, Restricted)")
    print("✓ Mission feel (Deploying, Active)")
    print("✓ Clear differentiation")


if __name__ == "__main__":
    # Show game analysis
    games = analyze_top_games()

    print("=== TOP GAME PATTERNS ===\n")
    for game, data in games.items():
        print(f"{game}:")
        print(f"  Key: {data['psychology']}")
        print(f"  Examples: {', '.join(data['hooks'][:2])}")
        print()

    # Show what we're missing
    show_game_psychology()

    # Show final recommendations
    test_formats()
