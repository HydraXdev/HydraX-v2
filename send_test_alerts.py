#!/usr/bin/env python3
"""
Send test alerts to see format in Telegram
"""

import requests
import time

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"  # Main BITTEN channel

def send_telegram_message(text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test different alert formats
test_alerts = [
    # ARCADE variants with different words
    "🔫 RAID 78%",
    "🔫 ATTACK 72%", 
    "🔫 FIREFIGHT 91%",
    
    # SNIPER with different visuals
    "⚡ OVERWATCH 87%",
    "🔥 OVERWATCH 92%",
    "🎯 OVERWATCH 89%",
    
    # Mixed realistic feed
    "🔫 RAID 83%",
    "⚡ OVERWATCH 96%",
    "🔫 ATTACK 75%",
    "🔫 FIREFIGHT 88%",
    "⚡ OVERWATCH 85%",
    "🔫 RAID 94%"
]

print("Sending test alerts to Telegram...")

for alert in test_alerts:
    print(f"Sending: {alert}")
    result = send_telegram_message(alert)
    if result and result.get('ok'):
        print("✓ Sent")
    else:
        print("✗ Failed")
    time.sleep(1)  # Don't spam

print("\nTest alerts sent! Check Telegram to see how they look.")