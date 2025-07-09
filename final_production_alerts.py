#!/usr/bin/env python3
"""
FINAL PRODUCTION ALERTS
ARCADE: 🔫 RAPID ASSAULT [XX%] / 🔥 STRIKE 💥
SNIPER: ⚡ SNIPER OPS ⚡ [XX%] / 🎖️ ELITE ACCESS
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

# FINAL PRODUCTION FORMATS
def arcade_alert(tcs):
    return f"🔫 RAPID ASSAULT [{tcs}%]\n🔥 STRIKE 💥"

def sniper_alert(tcs):
    return f"⚡ SNIPER OPS ⚡ [{tcs}%]\n🎖️ ELITE ACCESS"

print("=== FINAL PRODUCTION ALERTS ===\n")
print("ARCADE:")
print("🔫 RAPID ASSAULT [XX%]")
print("🔥 STRIKE 💥")
print("\nSNIPER:")
print("⚡ SNIPER OPS ⚡ [XX%]")
print("🎖️ ELITE ACCESS")
print("\n" + "="*40 + "\n")

# Create realistic feed
arcade_scores = [71, 74, 78, 82, 85, 88, 91, 94]
sniper_scores = [87, 89, 91, 92, 94, 96, 98]

# Build production feed
production_feed = []

# Realistic ratio - more arcade than sniper
for _ in range(7):
    production_feed.append(arcade_alert(random.choice(arcade_scores)))
    
for _ in range(3):
    production_feed.append(sniper_alert(random.choice(sniper_scores)))

# Shuffle
random.shuffle(production_feed)

print("Sending production alerts:\n")

for alert in production_feed:
    print(alert)
    print()
    send_alert(alert)

print("✅ PRODUCTION FORMAT CONFIRMED!")
print("\nARCADE: 🔫 RAPID ASSAULT [XX%] / 🔥 STRIKE 💥")
print("SNIPER: ⚡ SNIPER OPS ⚡ [XX%] / 🎖️ ELITE ACCESS")