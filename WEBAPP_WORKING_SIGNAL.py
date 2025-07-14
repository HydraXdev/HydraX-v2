import os
#!/usr/bin/env python3
"""
Send working webapp signal
"""

import asyncio
import json
import time
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram

# Configuration
BOT_TOKEN = 'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")'
CHAT_ID = 'int(os.getenv("CHAT_ID", "-1002581996861"))'
WEBAPP_URL = 'http://134.199.204.67:8888'

async def send_signals():
    """Send test signals with working webapp"""
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Signal 1: SNIPER SHOT
    signal1 = {
        'id': f"WEBAPP-{int(time.time()*1000)}",
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 93,
        'signal_type': 'SNIPER',
        'entry': 1.09235,
        'sl': 1.09035,
        'tp': 1.09635,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.2,
        'session': 'LONDON',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    message1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥\n**EURUSD BUY** | 93% | R:R 2.0"
    
    webapp_data1 = {
        'mission_id': signal1['id'],
        'signal': signal1,
        'timestamp': int(time.time())
    }
    
    import urllib.parse
    encoded_data1 = urllib.parse.quote(json.dumps(webapp_data1))
    webapp_url1 = f"{WEBAPP_URL}/hud?data={encoded_data1}"
    
    keyboard1 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎯 SNIPER MISSION BRIEF",
            url=webapp_url1
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message1,
        parse_mode='Markdown',
        reply_markup=keyboard1
    )
    
    print("✅ Sniper signal sent!")
    await asyncio.sleep(3)
    
    # Signal 2: PRECISION STRIKE
    signal2 = {
        'id': f"WEBAPP-{int(time.time()*1000)}",
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 86,
        'signal_type': 'PRECISION',
        'entry': 1.26545,
        'sl': 1.26745,
        'tp': 1.26145,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.5,
        'session': 'NEW_YORK',
        'timestamp': datetime.now().isoformat(),
        'expiry': 480
    }
    
    message2 = f"⭐ **Precision Strike** ⭐\nGBPUSD SELL | 86% | NEW YORK"
    
    webapp_data2 = {
        'mission_id': signal2['id'],
        'signal': signal2,
        'timestamp': int(time.time())
    }
    
    encoded_data2 = urllib.parse.quote(json.dumps(webapp_data2))
    webapp_url2 = f"{WEBAPP_URL}/hud?data={encoded_data2}"
    
    keyboard2 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="⭐ PRECISION INTEL",
            url=webapp_url2
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message2,
        parse_mode='Markdown',
        reply_markup=keyboard2
    )
    
    print("✅ Precision signal sent!")
    await asyncio.sleep(3)
    
    # Signal 3: STANDARD
    signal3 = {
        'id': f"WEBAPP-{int(time.time()*1000)}",
        'symbol': 'USDJPY',
        'direction': 'BUY',
        'tcs_score': 78,
        'signal_type': 'STANDARD',
        'entry': 150.125,
        'sl': 149.925,
        'tp': 150.525,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 0.8,
        'session': 'ASIAN',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    message3 = f"✅ Signal: USDJPY BUY | 78%\nASIAN Session | Spread: 0.8p"
    
    webapp_data3 = {
        'mission_id': signal3['id'],
        'signal': signal3,
        'timestamp': int(time.time())
    }
    
    encoded_data3 = urllib.parse.quote(json.dumps(webapp_data3))
    webapp_url3 = f"{WEBAPP_URL}/hud?data={encoded_data3}"
    
    keyboard3 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="📊 VIEW DETAILS",
            url=webapp_url3
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message3,
        parse_mode='Markdown',
        reply_markup=keyboard3
    )
    
    print("✅ Standard signal sent!")

if __name__ == '__main__':
    print("🚀 Sending 3 signals with working webapp...\n")
    asyncio.run(send_signals())
    print("\n🎆 All signals sent! Click the buttons to see mission briefs!")
    print(f"\n🌐 WebApp: {WEBAPP_URL}")
