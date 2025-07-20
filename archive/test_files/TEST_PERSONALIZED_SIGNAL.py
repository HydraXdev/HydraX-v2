import os
#!/usr/bin/env python3
"""Test personalized webapp mission brief"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from datetime import datetime
import json
import urllib.parse

BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = int(os.getenv("CHAT_ID", "-1002581996861"))
WEBAPP_URL = "http://134.199.204.67:8888"

async def send_test_signal():
    bot = Bot(token=BOT_TOKEN)
    
    # Create test signal data with user stats
    signal_data = {
        'user_id': 'test_user',
        'signal': {
            'id': 'test_001',
            'signal_type': 'SNIPER',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'tcs_score': 92,
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0890,
            'sl_pips': 20,
            'tp_pips': 40,
            'rr_ratio': 2.0,
            'expiry': 600  # 10 minutes
        }
    }
    
    # URL encode the data
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    webapp_url = f"{WEBAPP_URL}/hud?data={encoded_data}"
    
    # Create inline keyboard with WebApp button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL →",
            url=webapp_url  # Regular URL button
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format the Telegram message
    message = (
        "🔥 **SNIPER SHOT DETECTED**\n"
        "EUR/USD | BUY | 92%\n"
        "⏰ Expires in 10 minutes"
    )
    
    # Send the signal
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    print(f"✅ Test signal sent!")
    print(f"📱 WebApp URL: {webapp_url}")

# Run the test
if __name__ == "__main__":
    asyncio.run(send_test_signal())