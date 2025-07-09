#!/usr/bin/env python3
"""
Send a working webapp test signal
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

async def send_webapp_test():
    """Send test signals with different button approaches"""
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Test 1: Direct mission brief URL
    signal1 = {
        'id': f"WEBAPP-{int(time.time()*1000)}",
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 91,
        'signal_type': 'SNIPER'
    }
    
    message1 = "🔥🔥 **SNIPER SHOT** 🔥🔥\n**EURUSD BUY** | 91% | R:R 2.5"
    
    # Create a mission brief page URL
    mission_url = f"https://bitten-signals.vercel.app/mission?symbol=EURUSD&direction=BUY&score=91"
    
    keyboard1 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎯 OPEN MISSION BRIEF",
            url=mission_url
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message1,
        parse_mode='Markdown',
        reply_markup=keyboard1
    )
    
    print("✅ Test 1 sent - Direct URL button")
    
    await asyncio.sleep(3)
    
    # Test 2: Trading View chart
    message2 = "⭐ **Precision Strike** ⭐\nGBPUSD SELL | 85% | 🇬🇧 LONDON"
    
    keyboard2 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="📊 VIEW CHART",
            url="https://www.tradingview.com/chart/?symbol=FX:GBPUSD"
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message2,
        parse_mode='Markdown',
        reply_markup=keyboard2
    )
    
    print("✅ Test 2 sent - TradingView button")
    
    await asyncio.sleep(3)
    
    # Test 3: Callback button (for future implementation)
    message3 = "✅ Signal: USDJPY BUY | 78%\n🌏 ASIAN | Spread: 0.8p"
    
    # For now, use a simple URL until callback handling is implemented
    keyboard3 = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="📖 DETAILS",
            url="https://www.google.com/search?q=USDJPY+analysis"
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message3,
        parse_mode='Markdown',
        reply_markup=keyboard3
    )
    
    print("✅ Test 3 sent - Details button")
    
    print("\n📱 Check your Telegram for 3 test signals with working buttons!")

if __name__ == '__main__':
    print("🚀 Sending webapp test signals...\n")
    asyncio.run(send_webapp_test())
