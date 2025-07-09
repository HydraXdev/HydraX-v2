#!/usr/bin/env python3
"""Send signal to enhanced webapp"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def send_enhanced_signal():
    """Send signal to enhanced webapp"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"enh_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "USD/JPY"
    direction = "BUY"
    tcs_score = 84
    entry = 148.50
    sl = 148.20
    tp = 149.10
    
    # Create webapp data
    webapp_data = {
        'user_id': '7176191872',
        'signal': {
            'id': signal_id,
            'signal_type': 'PRECISION',
            'symbol': symbol,
            'direction': direction,
            'tcs_score': tcs_score,
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 600
        }
    }
    
    # Encode data for enhanced webapp
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    enhanced_url = f"http://134.199.204.67:8889/hud?data={encoded_data}"
    
    # Create the signal message
    message = (
        f"⭐ **ENHANCED HUD TEST**\n"
        f"{symbol} | {direction} | {tcs_score}% confidence\n"
        f"⏰ Expires in 10 minutes"
    )
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🚀 VIEW ENHANCED HUD",
            url=enhanced_url
        )]
    ])
    
    # Send the signal
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    print(f"✅ Enhanced signal sent: {symbol} {direction} @ {entry}")

async def main():
    await send_enhanced_signal()
    print("✅ Check Telegram for enhanced HUD signal!")

if __name__ == "__main__":
    asyncio.run(main())