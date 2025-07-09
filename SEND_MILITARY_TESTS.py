#!/usr/bin/env python3
"""Send test signals for all three military webapp versions"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import json
import urllib.parse

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861

async def send_military_signals():
    bot = Bot(token=BOT_TOKEN)
    
    # Signal data for testing
    signal_data = {
        'user_id': 'test_user',
        'signal': {
            'id': 'test_military',
            'signal_type': 'SNIPER',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'tcs_score': 92,
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0890,
            'sl_pips': 20,
            'tp_pips': 40,
            'rr_ratio': 2.0,
            'expiry': 600
        }
    }
    
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    
    # Version 1: TACTICAL WARFARE (Port 8889)
    webapp_url_v1 = f"http://134.199.204.67:8889/hud?data={encoded_data}"
    keyboard_v1 = [[
        InlineKeyboardButton(
            "🎯 V1: TACTICAL WARFARE →",
            url=webapp_url_v1
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🔥 **TACTICAL WARFARE VERSION**\nEUR/USD | BUY | 92%\n⏰ Expires in 10 minutes",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard_v1)
    )
    
    # Version 2: HOLOGRAPHIC COMMAND (Port 8890)
    webapp_url_v2 = f"http://134.199.204.67:8890/hud?data={encoded_data}"
    keyboard_v2 = [[
        InlineKeyboardButton(
            "👻 V2: HOLOGRAPHIC OPS →",
            url=webapp_url_v2
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text="👻 **HOLOGRAPHIC COMMAND VERSION**\nEUR/USD | BUY | 92%\n⏰ Expires in 10 minutes",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard_v2)
    )
    
    # Version 3: MECH WARFARE (Port 8891)
    webapp_url_v3 = f"http://134.199.204.67:8891/hud?data={encoded_data}"
    keyboard_v3 = [[
        InlineKeyboardButton(
            "🤖 V3: MECH WARFARE →",
            url=webapp_url_v3
        )
    ]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 **MECH WARFARE VERSION**\nEUR/USD | BUY | 92%\n⏰ Expires in 10 minutes",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard_v3)
    )
    
    print("✅ All three military versions sent!")
    print(f"\n📱 Direct URLs:")
    print(f"V1 Tactical: {webapp_url_v1}")
    print(f"V2 Holographic: {webapp_url_v2}")
    print(f"V3 Mech: {webapp_url_v3}")

if __name__ == "__main__":
    asyncio.run(send_military_signals())