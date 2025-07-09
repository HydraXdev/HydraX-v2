#!/usr/bin/env python3
"""
Revised final alerts - different emoji and starting letters
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
    time.sleep(1.5)

# Test different second line options for ARCADE
arcade_options = [
    # Option 1: Fire emoji + action word
    "🔫 RAPID ASSAULT [78%]\n🔥 FIRE",
    
    # Option 2: Explosion + strike
    "🔫 RAPID ASSAULT [78%]\n💥 STRIKE", 
    
    # Option 3: Target + attack
    "🔫 RAPID ASSAULT [78%]\n🎯 ATTACK",
    
    # Option 4: Alert + go
    "🔫 RAPID ASSAULT [78%]\n🚨 GO GO GO",
    
    # Option 5: Flames + now
    "🔫 RAPID ASSAULT [78%]\n🔥 NOW",
    
    # Option 6: Double fire
    "🔫 RAPID ASSAULT [78%]\n🔥 FIRE 🔥"
]

# SNIPER stays the same
sniper_format = "⚡ SNIPER OPS ⚡ [87%]\n🎖️ ELITE ACCESS"

print("=== TESTING ARCADE OPTIONS ===\n")
print("SNIPER (confirmed):")
print(sniper_format)
print("\nARCADE options (different from 'ENGAGE'):\n")

# Send all arcade options
for i, arcade in enumerate(arcade_options, 1):
    print(f"Option {i}:")
    print(arcade)
    print()
    send_alert(arcade)

# Send sniper for comparison
send_alert(sniper_format)

# Mixed feed with best options
print("\n=== MIXED FEED TEST ===")
print("Using 🔥 FIRE for arcade:\n")

mixed_alerts = [
    "🔫 RAPID ASSAULT [72%]\n🔥 FIRE",
    "⚡ SNIPER OPS ⚡ [92%]\n🎖️ ELITE ACCESS",
    "🔫 RAPID ASSAULT [85%]\n🔥 FIRE",
    "🔫 RAPID ASSAULT [78%]\n🔥 FIRE",
    "⚡ SNIPER OPS ⚡ [89%]\n🎖️ ELITE ACCESS",
    "🔫 RAPID ASSAULT [91%]\n🔥 FIRE",
]

for alert in mixed_alerts:
    print(alert)
    print()
    send_alert(alert)

print("✓ Check Telegram - which second line works best?")