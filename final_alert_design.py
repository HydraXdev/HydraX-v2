#!/usr/bin/env python3
"""
Final alert design - different lengths + more emojis
One short, one longer for instant visual difference
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

# DESIGN 1: Short vs Long text
alerts_v1 = [
    # ARCADE - SHORT
    "🚨🔫 RAID [78%]\nSTRIKE NOW",
    
    # SNIPER - LONGER TEXT
    "⚡🎯 PRECISION OVERWATCH [87%]\n🎖️ FANG+ AUTHORIZATION REQUIRED",
    
    # More examples
    "🚨🔫 RAID [82%]\nSTRIKE NOW",
    "⚡🎯 PRECISION OVERWATCH [92%]\n🎖️ FANG+ AUTHORIZATION REQUIRED",
    "🚨🔫 RAID [71%]\nSTRIKE NOW",
    "⚡🎯 PRECISION OVERWATCH [89%]\n🎖️ FANG+ AUTHORIZATION REQUIRED",
]

# DESIGN 2: Different emoji density
alerts_v2 = [
    # ARCADE - Less emojis, shorter
    "🔫 RAPID ASSAULT [78%]\n⚡ ENGAGE",
    
    # SNIPER - More emojis, longer
    "🎯⚡🔥 SNIPER POSITION [87%]\n🎖️🔒 FANG+ ELITE ACCESS ONLY",
    
    "🔫 RAPID ASSAULT [91%]\n⚡ ENGAGE",
    "🎯⚡🔥 SNIPER POSITION [94%]\n🎖️🔒 FANG+ ELITE ACCESS ONLY",
]

# DESIGN 3: Alert style difference
alerts_v3 = [
    # ARCADE - Action focused
    "🚨🔫 COMBAT [78%]\n💥 FIRE",
    
    # SNIPER - Status focused  
    "⚡🎯⚡ OVERWATCH ACTIVE [87%]\n🎖️ RESTRICTED: FANG+ OPERATORS",
    
    "🚨🔫 COMBAT [85%]\n💥 FIRE",
    "⚡🎯⚡ OVERWATCH ACTIVE [93%]\n🎖️ RESTRICTED: FANG+ OPERATORS",
]

# DESIGN 4: Maximum differentiation
alerts_v4 = [
    # ARCADE - Very short
    "🔥🔫 RAID 78%\n⚡GO⚡",
    
    # SNIPER - Much longer
    "🎯⚡🎯 PRECISION SNIPER OPS [87%]\n🎖️🔒 TIER 2+ AUTHORIZATION REQUIRED",
    
    "🔥🔫 RAID 92%\n⚡GO⚡",
    "🎯⚡🎯 PRECISION SNIPER OPS [95%]\n🎖️🔒 TIER 2+ AUTHORIZATION REQUIRED",
]

print("=== SENDING FINAL ALERT DESIGNS ===\n")

# Send all designs
all_designs = [
    ("DESIGN 1: Short vs Long", alerts_v1),
    ("DESIGN 2: Emoji Density", alerts_v2),
    ("DESIGN 3: Action vs Status", alerts_v3),
    ("DESIGN 4: Maximum Difference", alerts_v4)
]

for design_name, alerts in all_designs:
    print(f"\n{design_name}:")
    print("-" * 40)
    
    # Mix arcade and sniper
    for i in range(0, len(alerts), 2):
        if i < len(alerts):
            # Arcade
            print(f"ARCADE:\n{alerts[i]}\n")
            send_alert(alerts[i])
            
        if i + 1 < len(alerts):
            # Sniper
            print(f"SNIPER:\n{alerts[i+1]}\n")
            send_alert(alerts[i+1])

print("\n✓ All designs sent! Check which has best visual differentiation.")