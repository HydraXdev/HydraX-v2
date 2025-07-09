#!/usr/bin/env python3
"""Send signal with direct webapp integration - no preview"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def send_direct_signal():
    """Send signal with WebApp button"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"dir_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "EUR/USD"
    direction = "BUY"
    tcs_score = 85
    entry = 1.0850
    sl = 1.0820
    tp = 1.0910
    pattern = "LONDON_RAID"
    
    # Create webapp data
    webapp_data = {
        'user_id': '7176191872',
        'signal': {
            'id': signal_id,
            'pattern': pattern,
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
    
    # Encode data for URL
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    # Create the signal message - short and sweet
    message = (
        f"🔥 *{pattern}*\n"
        f"{symbol} | {direction} | {tcs_score}%"
    )
    
    # Try WebApp button first
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎯 OPEN INTEL",
                web_app=WebAppInfo(url=webapp_url)
            )]
        ])
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Sent with WebApp button (direct open)")
        
    except Exception as e:
        # Fallback to URL button
        print(f"⚠️ WebApp button failed: {e}")
        print("📱 Using URL button fallback...")
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎯 VIEW INTEL",
                url=webapp_url
            )]
        ])
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Sent with URL button (requires confirmation)")
    
    print(f"\n📊 Signal: {symbol} {direction} @ {entry}")
    print(f"🎯 Pattern: {pattern}")
    print(f"📈 TCS: {tcs_score}%")
    print("\n💡 To remove confirmation dialog:")
    print("1. Open @BotFather")
    print("2. Send /mybots")
    print("3. Select your bot")
    print("4. Bot Settings → Configure Mini App")
    print("5. Set URL: https://joinbitten.com/hud")

async def main():
    await send_direct_signal()

if __name__ == "__main__":
    asyncio.run(main())