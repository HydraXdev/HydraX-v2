#!/usr/bin/env python3
"""
Send dressed up alerts with live elements
Clock isn't live (just static) but we can make it look urgent
"""

import requests
import time
import random

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

def send_alert(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)
    time.sleep(1.5)

# Generate realistic operator counts and times
def get_random_operators():
    return random.randint(3, 27)

def get_random_time():
    return random.choice(["25 MIN", "30 MIN", "18 MIN", "22 MIN", "35 MIN"])

# ARCADE alerts - RAPID ASSAULT with operators
arcade_alerts = []
for tcs in [71, 78, 82, 91, 85, 73, 88, 94]:
    ops = get_random_operators()
    alert = f"🔫 RAPID ASSAULT [{tcs}%]\n👥 {ops} Operators Engaging"
    arcade_alerts.append(alert)

# SNIPER alerts - FANG+ focus with urgency
sniper_alerts = []
for tcs in [87, 92, 89, 96, 85, 91]:
    time_window = get_random_time()
    alert = f"⚡ PRECISION STRIKE [{tcs}%]\n⏱️ {time_window} • 🎖️ FANG+ ONLY"
    sniper_alerts.append(alert)

# Mix them up for realistic feed
all_alerts = []

# Create mixed feed
for i in range(6):
    if arcade_alerts:
        all_alerts.append(arcade_alerts.pop(0))
    if sniper_alerts and random.random() > 0.3:  # Less sniper alerts
        all_alerts.append(sniper_alerts.pop(0))

# Add remaining
all_alerts.extend(arcade_alerts)
all_alerts.extend(sniper_alerts)

print("=== SENDING DRESSED UP ALERTS ===\n")
print("ARCADE: Rapid Assault + Live Operators")
print("SNIPER: Time Window + FANG+ Only")
print("-" * 40)

for alert in all_alerts[:12]:  # Send 12 alerts
    print(f"\n{alert}")
    send_alert(alert)

# Bonus: Send some variations
print("\n\n=== BONUS VARIATIONS ===")

bonus_alerts = [
    # High urgency arcade
    "🔫 🔥 HOT DROP [95%]\n👥 31 Operators • FULL SEND",
    
    # Elite sniper
    "⚡ 💎 DIAMOND TARGET [98%]\n⏱️ 15 MIN • 🎖️ FANG+ ELITE",
    
    # Squad filling fast
    "🔫 BREACH IMMINENT [86%]\n👥 Squad 28/30 • JOINING NOW",
    
    # Last chance sniper
    "⚡ ⚠️ FINAL WINDOW [91%]\n⏱️ 8 MIN LEFT • 🎖️ FANG+ REQ",
    
    # Popular arcade
    "🔫 🚨 FIREFIGHT [79%]\n👥 45 Operators • TRENDING 🔥"
]

for alert in bonus_alerts:
    print(f"\n{alert}")
    send_alert(alert)

print("\n✓ All alerts sent! Check Telegram.")