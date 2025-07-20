import os
#!/usr/bin/env python3
"""
Force a signal immediately for testing webapp buttons
"""

import asyncio
import json
import time
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import telegram

# Configuration
BOT_TOKEN = 'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")'
CHAT_ID = 'int(os.getenv("CHAT_ID", "-1002581996861"))'
WEBAPP_URL = 'https://joinbitten.com'

async def send_test_signal():
    """Send a test signal immediately"""
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Create a test signal
    signal = {
        'id': f"TEST-{int(time.time()*1000)}",
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 88,
        'signal_type': 'PRECISION',
        'entry': 1.09052,
        'sl': 1.08852,
        'tp': 1.09452,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.2,
        'session': 'LONDON',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Format message
    line1 = f"⭐ **Precision Strike** ⭐"
    line2 = f"EURUSD BUY | 88% | 🇬🇧 LONDON"
    message = f"{line1}\n{line2}"
    
    # Create webapp data
    webapp_data = {
        'mission_id': signal['id'],
        'signal': signal,
        'timestamp': int(time.time())
    }
    
    import urllib.parse
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"{WEBAPP_URL}/hud?data={encoded_data}"
    
    # Create webapp button
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="⭐ VIEW INTEL",
            url=webapp_url
        )
    ]])
    
    # Send message
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    print(f"✅ Test signal sent!")
    print(f"Signal ID: {signal['id']}")
    print(f"WebApp URL: {webapp_url}")

if __name__ == '__main__':
    print("🚀 Sending test signal...")
    asyncio.run(send_test_signal())
