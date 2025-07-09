#!/usr/bin/env python3
"""
Test the corrected signal format
"""

import requests
import json
from datetime import datetime

def send_test_signal():
    """Send one test signal with corrected format"""
    
    bot_token = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
    chat_id = "-1002581996861"
    
    # CORRECTED FORMAT: Brief 2-3 line signal (like the example)
    message = """⚡ **SIGNAL DETECTED**
EURUSD | BUY | 82% confidence
⏰ Expires in 15 minutes"""

    # Create inline keyboard with WebApp button
    keyboard = {
        "inline_keyboard": [[
            {
                "text": "🎯 VIEW INTEL",
                "url": "https://joinbitten.com/hud?signal=test"
            }
        ]]
    }
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(keyboard)
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Corrected signal format sent successfully!")
            print(f"📝 Message: {message}")
            print("🔗 With WebApp button for full details")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("📱 Testing corrected signal format...")
    print("=" * 50)
    send_test_signal()