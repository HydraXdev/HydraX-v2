#!/usr/bin/env python3
"""
Send AAA game-style alerts to Telegram
"""

import requests
import time

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
    time.sleep(2)

# Test different 2-line formats
alerts = [
    # Option 1: Military Ops
    "🔫 STRIKE TEAM DEPLOYING\nTarget Confidence: 78%",
    "⚡ OVERWATCH POSITION\nElite Authorization: 87%",
    
    # Option 2: Urgency 
    "🔫 RAPID ASSAULT [92%]\n⏱️ 30 MIN WINDOW",
    "⚡ PRECISION SHOT [89%]\n🎖️ FANG+ CERTIFIED",
    
    # Option 3: Zone Control
    "🔫 HOT ZONE ACTIVE\nEngagement Level: 71%",
    "⚡ RESTRICTED SECTOR\nClearance Required: 91%",
    
    # Option 4: Squad/Social
    "🔫 FIRETEAM READY\n5 Operators • 85% GO",
    "⚡ SNIPER NEST LOCATED\nElite Squad Only • 94%",
    
    # Bonus: Add live counter
    "🔫 COMBAT ALERT [88%]\n👥 12 Operators Engaging",
    "⚡ HIGH VALUE TARGET\n🎯 3 Snipers in Position • 96%"
]

print("Sending AAA-style alerts...")

for alert in alerts:
    print(f"\nSending:\n{alert}")
    send_alert(alert)

print("\n✓ Sent! Check Telegram for the 2-line format tests.")