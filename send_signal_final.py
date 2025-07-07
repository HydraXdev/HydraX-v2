#!/usr/bin/env python3
"""Send BITTEN signal - Final working version"""

import asyncio
import json
import time
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

async def send_bitten_signal():
    """Send BITTEN signal with proper formatting"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief signal alert (proper BITTEN format)
    signal_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""

    # Signal data
    signal_data = {
        'signal_id': f'test_{int(time.time())}',
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry': 1.0850,
        'sl': 1.0830,
        'tp': 1.0880,
        'confidence': 87
    }
    
    # Encode data for URL
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    webapp_url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    # Create inline keyboard with URL button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            url=webapp_url
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        print(f"✅ BITTEN signal sent successfully!")
        print(f"Message ID: {message.message_id}")
        print(f"\n📱 Signal Format:")
        print(f"- Brief 3-line alert in Telegram")
        print(f"- VIEW INTEL button links to joinbitten.com")
        print(f"- Full mission briefing opens in browser")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def send_test_signals():
    """Send multiple test signal types"""
    bot = Bot(token=BOT_TOKEN)
    
    # Different signal types
    signals = [
        {
            'type': 'ARCADE',
            'message': "🎮 **ARCADE SIGNAL**\nGBP/USD | SELL | 75% confidence\n⏰ Expires in 30 minutes",
            'button': "🎮 VIEW ARCADE INTEL"
        },
        {
            'type': 'SNIPER',
            'message': "🎯 **SNIPER SIGNAL**\nUSD/JPY | BUY | 92% confidence\n⏰ Expires in 15 minutes",
            'button': "🎯 VIEW SNIPER INTEL"
        },
        {
            'type': 'HAMMER',
            'message': "🔨 **MIDNIGHT HAMMER**\nEUR/GBP | SELL | 96% confidence\n⏰ Community event - 5 min left",
            'button': "🔨 JOIN THE HAMMER"
        }
    ]
    
    for signal in signals:
        keyboard = [[
            InlineKeyboardButton(
                signal['button'],
                url=f"https://joinbitten.com/hud?type={signal['type']}"
            )
        ]]
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=signal['message'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        print(f"✅ Sent {signal['type']} signal")
        await asyncio.sleep(2)

if __name__ == "__main__":
    print("🚀 BITTEN Signal Test")
    print("=" * 50)
    print(f"Chat ID: {CHAT_ID}")
    print(f"WebApp: https://joinbitten.com/hud")
    print("=" * 50)
    
    # Send single test signal
    asyncio.run(send_bitten_signal())