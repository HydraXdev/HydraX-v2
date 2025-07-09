#!/usr/bin/env python3
"""Send test signal with pattern names and all new features"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def send_pattern_signal():
    """Send signal with pattern name"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"pat_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "EUR/USD"
    direction = "BUY"
    tcs_score = 82
    entry = 1.0848
    sl = 1.0818
    tp = 1.0908
    
    # Create webapp data
    webapp_data = {
        'user_id': '7176191872',
        'signal': {
            'id': signal_id,
            'signal_type': 'WALL_BREACH',  # Pattern will be selected randomly in webapp
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
    webapp_url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    # Create the signal message - now with pattern hint
    message = (
        f"⭐ **WALL BREACH DETECTED**\n"
        f"{symbol} | {direction} | {tcs_score}% confidence\n"
        f"⏰ Expires in 10 minutes"
    )
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🎯 VIEW MISSION INTEL",
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
    
    print(f"✅ Pattern signal sent: {symbol} {direction} @ {entry}")
    print(f"📊 New features:")
    print("  • Pattern name shown (WALL BREACH)")
    print("  • Setup Intel button for education")
    print("  • Combined Stats & History page")
    print("  • Price masking (last 2 digits XX)")
    print("  • Dollar values under pips")
    print("  • Squad engagement percentage")
    print("  • Ammo display for shots left")

async def main():
    await send_pattern_signal()
    
    print("\n✨ Check Telegram for the signal!")
    print("\nClick 'VIEW MISSION INTEL' to see:")
    print("1. Pattern name at top (e.g., WALL BREACH)")
    print("2. Click 'Setup Intel' button for pattern explanation")
    print("3. Click 'Stats & History' for combined page")
    print("4. Notice prices end in XX for security")
    print("5. See dollar amounts under pip values")
    print("6. Check squad engagement % above mission card")
    print("7. See ammo/shots display instead of trades left")

if __name__ == "__main__":
    asyncio.run(main())