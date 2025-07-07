#!/usr/bin/env python3
"""Send BITTEN signal with URL button (works without WebApp support)"""

import asyncio
import json
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
WEBAPP_URL = 'https://joinbitten.com/hud'

async def send_signal_with_url_button():
    """Send signal with regular URL button instead of WebApp"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Signal data
    signal_data = {
        'signal_id': f'test_{int(time.time())}',
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'confidence': 87
    }
    
    # Create regular URL button (not WebApp)
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            url=f"{WEBAPP_URL}?data={json.dumps(signal_data)}"
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        print(f"✅ Signal sent with URL button!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📱 This uses a regular URL button")
        print(f"Opens in browser: {WEBAPP_URL}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Sending BITTEN signal with URL button...")
    asyncio.run(send_signal_with_url_button())