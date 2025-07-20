#!/usr/bin/env python3
"""
BITTEN Alert Format Options
Testing different military terms and visual styles
"""

# RAPID_ASSAULT Alert Options (Short scalps - pistol emoji)
arcade_formats = [
    # Format 1: Action words
    ["🔫 RAID 78%", "🔫 BREACH 82%", "🔫 ASSAULT 91%"],
    
    # Format 2: Tactical terms  
    ["🔫 STRIKE 78%", "🔫 BLITZ 82%", "🔫 RUSH 91%"],
    
    # Format 3: Military ops
    ["🔫 CONTACT 78%", "🔫 ENGAGE 82%", "🔫 EXECUTE 91%"],
    
    # Format 4: Speed focused
    ["🔫 FLASH 78%", "🔫 RAPID 82%", "🔫 QUICK 91%"],
]

# SNIPER Alert Options (Long precision - lightning/fire)
sniper_formats = [
    # Format 1: Precision terms
    ["⚡ OVERWATCH 87%", "⚡ PRECISION 92%", "⚡ LONGSHOT 96%"],
    
    # Format 2: Elite ops
    ["🔥 EAGLE 87%", "🔥 HAWK 92%", "🔥 FALCON 96%"],
    
    # Format 3: Sniper callouts
    ["⚡ CROSSHAIR 87%", "⚡ SCOPE 92%", "⚡ TARGET 96%"],
    
    # Format 4: Distance themed
    ["🔥 DISTANCE 87%", "🔥 RANGE 92%", "🔥 HORIZON 96%"],
]

# Alternative visual combinations
visual_options = [
    {"arcade": "🔫", "sniper": "⚡"},  # Pistol vs Lightning
    {"arcade": "🔫", "sniper": "🔥"},  # Pistol vs Fire
    {"arcade": "💥", "sniper": "🎯"},  # Explosion vs Target
    {"arcade": "⚔️", "sniper": "🏹"},  # Sword vs Bow
    {"arcade": "🚨", "sniper": "📡"},  # Alert vs Radar
]

def show_alert_comparisons():
    """Show how different formats look side by side"""
    
    print("=== BITTEN ALERT FORMAT OPTIONS ===\n")
    
    # Show each format option
    for i in range(len(arcade_formats)):
        print(f"OPTION {i+1}:")
        print("-" * 40)
        print("RAPID_ASSAULT alerts (all tiers):")
        for alert in arcade_formats[i]:
            print(f"  {alert}")
        
        print("\nSNIPER alerts (FANG+):")
        for alert in sniper_formats[i]:
            print(f"  {alert}")
        print()
    
    # Show mixed stream example
    print("\n=== MIXED ALERT STREAM EXAMPLE ===")
    print("How it looks in Telegram:\n")
    
    # Using Option 1 as example
    mixed_alerts = [
        "🔫 RAID 78%",
        "⚡ OVERWATCH 87%",
        "🔫 BREACH 72%",
        "🔫 ASSAULT 91%",
        "⚡ PRECISION 92%",
        "🔫 RAID 83%",
        "⚡ LONGSHOT 96%"
    ]
    
    for alert in mixed_alerts:
        print(alert)
    
    # Telegram formatting limitations
    print("\n=== TELEGRAM FORMATTING ===")
    print("Telegram bot messages support:")
    print("• Bold: **text**")
    print("• Italic: *text*")
    print("• Code: `text`")
    print("• NO custom colors")
    print("• Emojis are the main visual differentiator")
    
    # Best practices
    print("\n=== RECOMMENDATIONS ===")
    print("1. Keep it SHORT (users scan quickly)")
    print("2. Make emoji contrast strong")
    print("3. Use consistent term per type")
    print("4. TCS% always at end for easy scanning")

def test_readability():
    """Test how easy it is to distinguish"""
    
    print("\n=== READABILITY TEST ===")
    print("Can you quickly identify which are RAPID_ASSAULT vs SNIPER?\n")
    
    test_stream = [
        "🔫 RAID 73%",
        "🔫 RAID 89%",
        "⚡ OVERWATCH 88%",
        "🔫 RAID 94%",
        "⚡ OVERWATCH 91%",
        "🔫 RAID 71%",
        "⚡ OVERWATCH 95%",
        "🔫 RAID 86%"
    ]
    
    for alert in test_stream:
        print(alert)
    
    print("\nKey insight: Same word + different emoji = instant recognition!")

if __name__ == "__main__":
    show_alert_comparisons()
    test_readability()