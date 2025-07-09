#!/usr/bin/env python3
"""
Test STRIKE with fire emoji placement
"""

import requests
import time

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

def send_alert(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)
    time.sleep(2)

# Test both placements
options = [
    # Fire after STRIKE
    "🔫 RAPID ASSAULT [78%]\n💥 STRIKE 🔥",
    
    # Fire before STRIKE  
    "🔫 RAPID ASSAULT [78%]\n💥 🔥 STRIKE",
    
    # Just for comparison - double fire
    "🔫 RAPID ASSAULT [78%]\n🔥 STRIKE 🔥",
    
    # And sniper for visual comparison
    "⚡ SNIPER OPS ⚡ [87%]\n🎖️ ELITE ACCESS"
]

print("=== TESTING STRIKE + FIRE PLACEMENT ===\n")

for i, alert in enumerate(options, 1):
    print(f"Option {i}:")
    print(alert)
    print()
    send_alert(alert)

# Send final mixed example
print("\n=== MIXED FEED EXAMPLE ===\n")

mixed = [
    "🔫 RAPID ASSAULT [72%]\n💥 STRIKE 🔥",
    "⚡ SNIPER OPS ⚡ [92%]\n🎖️ ELITE ACCESS",
    "🔫 RAPID ASSAULT [85%]\n💥 STRIKE 🔥",
    "⚡ SNIPER OPS ⚡ [89%]\n🎖️ ELITE ACCESS",
    "🔫 RAPID ASSAULT [78%]\n💥 STRIKE 🔥",
]

for alert in mixed:
    print(alert)
    print()
    send_alert(alert)

print("✓ Check Telegram to see which looks better!")