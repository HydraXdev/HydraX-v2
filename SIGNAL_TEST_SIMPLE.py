import os
#!/usr/bin/env python3
"""
Simple signal test with basic URL button
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

async def send_test_signal():
    """Send a test signal with simple URL button"""
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Create a test signal
    signal = {
        'id': f"SIG-{int(time.time()*1000)}",
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 92,
        'signal_type': 'SNIPER',
        'entry': 1.26485,
        'sl': 1.26685,
        'tp': 1.26085,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.5,
        'session': 'NEW_YORK',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Format message - SNIPER shot
    line1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥"
    line2 = f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | R:R {signal['rr_ratio']}"
    message = f"{line1}\n{line2}"
    
    # Create simple Google search URL as placeholder
    search_query = f"forex {signal['symbol']} {signal['direction']} analysis"
    google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
    
    # Create simple URL button
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎯 SNIPER INTEL",
            url=google_url
        )
    ]])
    
    # Send message
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    print(f"✅ SNIPER signal sent!")
    print(f"Signal: {signal['symbol']} {signal['direction']} @ {signal['entry']}")
    print(f"URL opens: {google_url}")
    
    # Send another signal after 5 seconds - PRECISION
    await asyncio.sleep(5)
    
    signal2 = {
        'symbol': 'USDJPY',
        'direction': 'BUY',
        'tcs_score': 85,
        'signal_type': 'PRECISION',
        'session': 'ASIAN'
    }
    
    line1 = f"⭐ **Precision Strike** ⭐"
    line2 = f"{signal2['symbol']} {signal2['direction']} | {signal2['tcs_score']}% | 🌏 {signal2['session']}"
    message2 = f"{line1}\n{line2}"
    
    keyboard2 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="⭐ VIEW INTEL",
            url="https://www.tradingview.com/chart/?symbol=FX:USDJPY"
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message2,
        parse_mode='Markdown',
        reply_markup=keyboard2
    )
    
    print(f"✅ PRECISION signal sent!")
    print(f"Signal: {signal2['symbol']} {signal2['direction']}")

if __name__ == '__main__':
    print("🚀 Sending test signals...")
    asyncio.run(send_test_signal())
    print("\n📱 Check your Telegram for 2 test signals!")
