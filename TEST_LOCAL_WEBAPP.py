#!/usr/bin/env python3
"""
Test signal with local webapp URL
"""

import asyncio
import json
import time
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = '-1002581996861'
WEBAPP_URL = 'http://134.199.204.67:8888'  # Using public IP for Telegram access

async def send_webapp_signal():
    """Send test signal with local webapp"""
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Create a SNIPER signal
    signal = {
        'id': f"LOCAL-{int(time.time()*1000)}",
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 92,
        'signal_type': 'SNIPER',
        'entry': 1.09125,
        'sl': 1.08925,
        'tp': 1.09525,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.2,
        'session': 'LONDON',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600  # 10 minutes
    }
    
    # Format message
    line1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥"
    line2 = f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | R:R {signal['rr_ratio']}"
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
    
    # Create button
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎯 OPEN MISSION BRIEF",
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
    
    print(f"✅ Signal sent with local webapp!")
    print(f"Signal ID: {signal['id']}")
    print(f"\n🌐 WebApp URL (click to test locally):")
    print(f"{webapp_url}")
    
    # Send another signal after 5 seconds - PRECISION
    await asyncio.sleep(5)
    
    signal2 = {
        'id': f"LOCAL-{int(time.time()*1000)}",
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 85,
        'signal_type': 'PRECISION',
        'entry': 1.26485,
        'sl': 1.26685,
        'tp': 1.26085,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.5,
        'session': 'NEW_YORK',
        'timestamp': datetime.now().isoformat(),
        'expiry': 480  # 8 minutes
    }
    
    line1 = f"⭐ **Precision Strike** ⭐"
    line2 = f"{signal2['symbol']} {signal2['direction']} | {signal2['tcs_score']}% | 🇺🇸 {signal2['session']}"
    message2 = f"{line1}\n{line2}"
    
    webapp_data2 = {
        'mission_id': signal2['id'],
        'signal': signal2,
        'timestamp': int(time.time())
    }
    
    encoded_data2 = urllib.parse.quote(json.dumps(webapp_data2))
    webapp_url2 = f"{WEBAPP_URL}/hud?data={encoded_data2}"
    
    keyboard2 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="⭐ VIEW INTEL",
            url=webapp_url2
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message2,
        parse_mode='Markdown',
        reply_markup=keyboard2
    )
    
    print(f"\n✅ Second signal sent!")
    print(f"Signal ID: {signal2['id']}")

if __name__ == '__main__':
    print("🚀 Sending signals with local webapp...\n")
    asyncio.run(send_webapp_signal())
    print("\n📱 Check your Telegram and click the buttons!")
    print("🌐 WebApp server running at http://134.199.204.67:8888")
