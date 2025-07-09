#!/usr/bin/env python3
"""
Test alert formats for BITTEN
Send sample alerts to see how they look
"""

import random

# The 12 actual pairs from the system
PAIRS = [
    # Core pairs
    "GBPUSD", "EURUSD", "USDJPY", "GBPJPY", "USDCAD",
    # Extra pairs  
    "AUDUSD", "NZDUSD", "AUDJPY", "EURJPY", "EURGBP", "GBPCHF", "USDCHF"
]

def generate_test_alerts():
    """Generate realistic test alerts"""
    
    alerts = []
    
    # ARCADE alerts (quick action words)
    arcade_words = ["RAID", "ATTACK", "FIREFIGHT"]
    
    # Generate some arcade alerts (various TCS)
    arcade_tcs = [72, 78, 83, 91, 95, 74, 88]
    for tcs in arcade_tcs:
        word = random.choice(arcade_words)
        alerts.append(f"🔫 {word} {tcs}%")
    
    # Generate some sniper alerts (85%+ only)
    sniper_tcs = [87, 92, 89, 96, 85, 91]
    for tcs in sniper_tcs:
        alerts.append(f"⚡ OVERWATCH {tcs}%")
    
    # Mix them up like real feed
    random.shuffle(alerts)
    
    return alerts

def show_format_options():
    """Show different word options for arcade"""
    
    print("=== ARCADE WORD OPTIONS ===\n")
    
    # Test different action words
    options = {
        "RAID": ["🔫 RAID 78%", "🔫 RAID 92%", "🔫 RAID 71%"],
        "ATTACK": ["🔫 ATTACK 78%", "🔫 ATTACK 92%", "🔫 ATTACK 71%"],
        "FIREFIGHT": ["🔫 FIREFIGHT 78%", "🔫 FIREFIGHT 92%", "🔫 FIREFIGHT 71%"],
        "STRIKE": ["🔫 STRIKE 78%", "🔫 STRIKE 92%", "🔫 STRIKE 71%"],
        "BREACH": ["🔫 BREACH 78%", "🔫 BREACH 92%", "🔫 BREACH 71%"]
    }
    
    for word, examples in options.items():
        print(f"{word}:")
        for ex in examples:
            print(f"  {ex}")
        print()
    
    print("=== SNIPER OPTIONS ===\n")
    print("⚡ OVERWATCH 87%")
    print("⚡ OVERWATCH 92%")
    print("⚡ OVERWATCH 96%")
    
    print("\n=== MIXED FEED EXAMPLE ===")
    print("How it looks in your Telegram:\n")
    
    # Generate realistic mixed feed
    test_alerts = generate_test_alerts()
    for alert in test_alerts[:10]:  # Show 10 alerts
        print(alert)
    
    print("\n=== VISUAL ALTERNATIVES ===")
    print("\nOption A (Current):")
    print("🔫 RAID 82%")
    print("⚡ OVERWATCH 89%")
    
    print("\nOption B (Fire variant):")
    print("🔫 RAID 82%")
    print("🔥 OVERWATCH 89%")
    
    print("\nOption C (Target variant):")
    print("🔫 RAID 82%")
    print("🎯 OVERWATCH 89%")

def create_telegram_test():
    """Create test messages to send to Telegram"""
    
    print("\n=== COPY THESE TO TEST IN TELEGRAM ===\n")
    
    # Create a batch of test alerts
    test_batch = [
        "🔫 RAID 78%",
        "⚡ OVERWATCH 87%",
        "🔫 ATTACK 72%",
        "🔫 FIREFIGHT 91%",
        "⚡ OVERWATCH 92%",
        "🔫 RAID 83%",
        "⚡ OVERWATCH 96%",
        "🔫 ATTACK 75%",
        "🔫 FIREFIGHT 88%",
        "⚡ OVERWATCH 89%"
    ]
    
    print("Test batch to copy/paste:")
    print("-" * 30)
    for alert in test_batch:
        print(alert)

if __name__ == "__main__":
    show_format_options()
    create_telegram_test()
    
    print("\n\nTRADING PAIRS CONFIRMED:")
    print(f"Total: {len(PAIRS)} pairs")
    print("Core:", ", ".join(PAIRS[:5]))
    print("Extra:", ", ".join(PAIRS[5:]))