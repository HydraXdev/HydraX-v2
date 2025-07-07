#!/usr/bin/env python3
"""Send proper BITTEN signal with WebApp button"""

import asyncio
import json
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

# You'll need to replace this with your actual webapp URL
# Options based on what I found in the code:
# WEBAPP_URL = "https://joinbitten.com/hud"  # Production
# WEBAPP_URL = "http://134.199.204.67:5000/hud"  # Test server
WEBAPP_URL = "https://your-domain.com/sniper_hud"  # Default placeholder

async def send_proper_signal():
    """Send a proper BITTEN signal with WebApp button"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert (2-3 lines as per signal_alerts.py)
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Prepare webapp data
    webapp_data = {
        'signal_id': 'sig_12345',
        'user_tier': 'FANG',
        'timestamp': int(time.time()),
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry': 1.0850,
        'tp': 1.0880,
        'sl': 1.0830,
        'confidence': 87
    }
    
    # Create inline keyboard with WebApp button
    keyboard = [
        [InlineKeyboardButton(
            "🎯 VIEW INTEL", 
            web_app=WebAppInfo(
                url=f"{WEBAPP_URL}?data={json.dumps(webapp_data)}"
            )
        )]
    ]
    
    # Alternative: Use regular URL button if WebApp not configured
    keyboard_url = [
        [InlineKeyboardButton(
            "📊 OPEN MISSION BRIEF", 
            url=f"{WEBAPP_URL}?data={json.dumps(webapp_data)}"
        )]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup_url = InlineKeyboardMarkup(keyboard_url)

    try:
        # Send with WebApp button
        msg1 = await bot.send_message(
            chat_id=CHAT_ID,
            text=f"**WebApp Button Test:**\n{signal_message}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Send with URL button
        msg2 = await bot.send_message(
            chat_id=CHAT_ID,
            text=f"**URL Button Test:**\n{signal_message}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup_url
        )
        
        print(f"✅ Signals sent with buttons!")
        print(f"WebApp URL: {WEBAPP_URL}")
        print(f"Message IDs: {msg1.message_id}, {msg2.message_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Sending proper BITTEN signal with buttons...")
    print(f"Note: You need to replace WEBAPP_URL with your actual webapp URL!")
    asyncio.run(send_proper_signal())