#!/usr/bin/env python3
"""Send test signal to show updated HUD features"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def send_updated_signal():
    """Send signal to updated webapp"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"upd_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "EUR/USD"
    direction = "BUY"
    tcs_score = 88
    entry = 1.0847
    sl = 1.0817
    tp = 1.0907
    
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
    
    # Encode data
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"http://134.199.204.67:8888/hud?data={encoded_data}"
    
    # Create the signal message
    message = (
        f"⭐ **UPDATED HUD DEMO**\n"
        f"{symbol} | {direction} | {tcs_score}% confidence\n"
        f"⏰ Expires in 10 minutes\n\n"
        f"✨ **New Features:**\n"
        f"• Ammo display (shots left)\n"
        f"• Price masking (last 2 digits XX)\n" 
        f"• Dollar values under pips\n"
        f"• Squad engagement %\n"
        f"• Norman's Notebook link\n"
        f"• Trophy room link\n"
        f"• Tactical pulsing fire button"
    )
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🎯 VIEW UPDATED HUD",
            url=webapp_url
        )]
    ])
    
    # Send the signal
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    print(f"✅ Updated signal sent: {symbol} {direction} @ {entry}")
    print(f"📊 Features: Squad %, Ammo display, Price masking, Dollar values")

async def main():
    await send_updated_signal()
    print("\n✅ Check Telegram for the updated HUD with all requested features!")

if __name__ == "__main__":
    asyncio.run(main())