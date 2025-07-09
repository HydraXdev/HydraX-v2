#!/usr/bin/env python3
"""Send a real trading signal with webapp button"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import json
import urllib.parse
from datetime import datetime
import random

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

async def send_trading_signal():
    """Send a realistic trading signal"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"sig_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "EUR/USD"
    direction = "BUY"
    tcs_score = 87
    entry = 1.0845
    sl = 1.0815
    tp = 1.0905
    
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
    
    # Encode data for URL
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"http://134.199.204.67:8888/hud?data={encoded_data}"
    
    # Create the signal message (compact format like in CLAUDE.md)
    message = (
        f"⭐ **SIGNAL DETECTED**\n"
        f"{symbol} | {direction} | {tcs_score}% confidence\n"
        f"⏰ Expires in 10 minutes"
    )
    
    # Create inline keyboard with URL button (not WebApp)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🎯 VIEW INTEL",
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
    
    print(f"✅ Signal sent: {symbol} {direction} @ {entry}")
    print(f"📊 TCS: {tcs_score}% | SL: {sl} | TP: {tp}")

async def send_sniper_signal():
    """Send a high confidence sniper signal"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate signal data
    signal_id = f"sniper_{datetime.now().strftime('%H%M%S')}"
    
    # Signal parameters
    symbol = "GBP/USD"
    direction = "SELL"
    tcs_score = 92
    entry = 1.2650
    sl = 1.2680
    tp = 1.2590
    
    # Create webapp data
    webapp_data = {
        'user_id': '7176191872',
        'signal': {
            'id': signal_id,
            'signal_type': 'SNIPER',
            'symbol': symbol,
            'direction': direction,
            'tcs_score': tcs_score,
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 480
        }
    }
    
    # Encode data
    encoded_data = urllib.parse.quote(json.dumps(webapp_data))
    webapp_url = f"http://134.199.204.67:8888/hud?data={encoded_data}"
    
    # Create the signal message
    message = (
        f"🔥🔥 **SNIPER SHOT**\n"
        f"{symbol} | {direction} | {tcs_score}% confidence\n"
        f"⏰ Expires in 8 minutes"
    )
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🎯 VIEW INTEL",
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
    
    print(f"✅ SNIPER signal sent: {symbol} {direction} @ {entry}")
    print(f"📊 TCS: {tcs_score}% | SL: {sl} | TP: {tp}")

async def main():
    """Send signals"""
    print("Sending real trading signals...")
    
    # Send a precision signal
    await send_trading_signal()
    
    # Wait a bit
    await asyncio.sleep(3)
    
    # Send a sniper signal
    await send_sniper_signal()
    
    print("\n✅ Signals sent! Check Telegram.")

if __name__ == "__main__":
    asyncio.run(main())