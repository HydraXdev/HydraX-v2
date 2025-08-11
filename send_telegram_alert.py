#!/usr/bin/env python3
"""
Send Telegram Alert for Test Signal
Triggers the normal signal alert flow through Telegram
"""

import os
import sys
import requests
import json
from datetime import datetime

# Load Telegram bot token from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Your Telegram user ID (Commander)
CHAT_ID = "7176191872"

def send_signal_alert():
    """Send signal alert via Telegram bot"""
    
    # Signal data for the test signal we created
    signal_data = {
        "signal_id": "ELITE_GUARD_TEST_1754681237",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0950,
        "sl": 1.0940,
        "tp": 1.0970,
        "confidence": 95.0,
        "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
        "signal_type": "PRECISION_STRIKE",
        "session": "OVERLAP",
        "shield_score": 8.5,
        "stop_pips": 10,
        "target_pips": 20,
        "risk_reward": 2.0
    }
    
    # Create formatted message like Elite Guard would send
    message = f"""
🔥 **ELITE GUARD SIGNAL ALERT** 🔥

📡 **{signal_data['symbol']} {signal_data['direction']}**
🎯 **PRECISION_STRIKE** (1:2.0 RR)
💎 **95.0% Confidence**
🛡️ **Shield Score: 8.5/10 (APPROVED)**

📊 **Trade Setup:**
• Entry: {signal_data['entry_price']:.4f}
• Stop Loss: {signal_data['sl']:.4f} (-10 pips)
• Take Profit: {signal_data['tp']:.4f} (+20 pips)
• Pattern: LIQUIDITY SWEEP REVERSAL
• Session: OVERLAP

⚡ **Mission Ready: ELITE_GUARD_TEST_1754681237**

🎯 Execute via webapp: http://134.199.204.67:8888/me
🔫 Or use: `/fire ELITE_GUARD_TEST_1754681237`

**This signal is ready for manual execution testing!**
"""
    
    # Send via Telegram Bot API
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=payload)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Telegram alert sent successfully!")
            print(f"Message ID: {result['result']['message_id']}")
            return True
        else:
            print(f"❌ Telegram API error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

if __name__ == "__main__":
    print("📱 Sending Telegram signal alert...")
    success = send_signal_alert()
    
    if success:
        print("\n🎯 **MANUAL EXECUTION TEST READY**")
        print("1. Check your Telegram for the signal alert")
        print("2. Use /fire ELITE_GUARD_TEST_1754681237 command")
        print("3. OR go to webapp and click execute")
        print("4. Watch complete execution flow with proof!")
    else:
        print("❌ Failed to send alert")