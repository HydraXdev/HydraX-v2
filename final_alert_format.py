#!/usr/bin/env python3
"""
Final BITTEN alert format
ARCADE: 🔫 RAPID ASSAULT [XX%] / ⚡ ENGAGE
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

# FINAL FORMATS
def arcade_alert(tcs):
    return f"🔫 RAPID ASSAULT [{tcs}%]\n⚡ ENGAGE"

def sniper_alert(tcs):
    return f"⚡ SNIPER OPS ⚡ [{tcs}%]\n🎖️ ELITE ACCESS"

print("=== FINAL BITTEN ALERT FORMAT ===\n")
print("ARCADE:")
print("🔫 RAPID ASSAULT [XX%]")
print("⚡ ENGAGE")
print("\nSNIPER:")
print("⚡ SNIPER OPS ⚡ [XX%]")
print("🎖️ ELITE ACCESS")
print("\n" + "-"*40 + "\n")

# Create realistic mixed feed
arcade_scores = [71, 74, 78, 82, 85, 88, 91, 94]
sniper_scores = [87, 89, 91, 92, 94, 96, 98]

# Build mixed feed
mixed_feed = []

# Add variety - more arcade than sniper (realistic ratio)
for _ in range(6):
    mixed_feed.append(arcade_alert(random.choice(arcade_scores)))
    
for _ in range(3):
    mixed_feed.append(sniper_alert(random.choice(sniper_scores)))

# Shuffle for realistic distribution
random.shuffle(mixed_feed)

print("Sending mixed feed example:\n")

for alert in mixed_feed:
    print(alert)
    print()
    send_alert(alert)

print("✓ Final format sent! This is the production design.")