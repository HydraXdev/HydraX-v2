#!/usr/bin/env python3
"""
Optimized alerts - ARCADE confirmed, SNIPER condensed to 2 lines
"""

import requests
import time
import random

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

def send_alert(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)
    time.sleep(2)

# ARCADE - CONFIRMED FORMAT
arcade_format = "🔫 RAPID ASSAULT [{}%]\n⚡ ENGAGE"

# SNIPER - CONDENSED OPTIONS (2 lines max)
sniper_options = [
    # Option 1: Short and clear
    "🎯⚡ OVERWATCH [{}%]\n🎖️ FANG+ ONLY",
    
    # Option 2: Elite focus
    "⚡🎯 PRECISION [{}%]\n🎖️ ELITE ACCESS",
    
    # Option 3: Sniper + lock
    "🎯⚡ SNIPER OPS [{}%]\n🔒 FANG+ REQ",
    
    # Option 4: Maximum icons
    "⚡🎯⚡ TARGET [{}%]\n🎖️🔒 TIER 2+",
    
    # Option 5: Clean military
    "🎯 OVERWATCH [{}%]\n⚡ FANG+ CERTIFIED",
    
    # Option 6: Action style
    "⚡🎯 PRECISION SHOT [{}%]\n🎖️ RESTRICTED"
]

print("=== TESTING CONDENSED FORMATS ===\n")
print("ARCADE (confirmed):")
print("🔫 RAPID ASSAULT [XX%]")
print("⚡ ENGAGE")
print("\nSNIPER options (pick one):\n")

# Test different TCS scores
test_scores = {
    "arcade": [72, 78, 85, 91, 94],
    "sniper": [87, 89, 92, 95, 98]
}

# Send confirmed arcade format
print("\n--- ARCADE ALERTS ---")
for tcs in test_scores["arcade"]:
    alert = arcade_format.format(tcs)
    print(f"\n{alert}")
    send_alert(alert)

# Send all sniper options for comparison
print("\n\n--- SNIPER OPTIONS ---")
for i, sniper_format in enumerate(sniper_options, 1):
    tcs = random.choice(test_scores["sniper"])
    alert = sniper_format.format(tcs)
    print(f"\nOption {i}:")
    print(alert)
    send_alert(alert)

# Mixed feed test
print("\n\n--- MIXED FEED TEST ---")
mixed_alerts = []

# Create realistic mixed feed
for _ in range(4):
    # Add arcade
    tcs = random.choice(test_scores["arcade"])
    mixed_alerts.append(arcade_format.format(tcs))
    
    # Add sniper (using option 1 for now)
    tcs = random.choice(test_scores["sniper"])
    mixed_alerts.append(sniper_options[0].format(tcs))

print("\nMixed feed example:")
for alert in mixed_alerts:
    print(f"\n{alert}")
    send_alert(alert)

print("\n✓ Check Telegram - all stay on 2 lines!")