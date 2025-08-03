#!/usr/bin/env python3
"""
Demo: WebApp Button vs Text Link
Shows the difference between the two approaches
"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import json
import urllib.parse

BOT_TOKEN = "8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k"
CHAT_ID = "-1002581996861"

async def demo_both_methods():
    """Send both types for comparison"""
    bot = Bot(token=BOT_TOKEN)
    
    # Sample signal data
    signal_data = {
        'mission_id': 'DEMO_123456',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 87,
        'entry': 1.09235,
        'sl': 1.09035,
        'tp': 1.09635
    }
    
    print("🚀 Sending comparison demo...")
    
    # METHOD 1: TEXT LINK (Current)
    text_message = (
        f"⚡ SNIPER OPS - {signal_data['symbol']} {signal_data['direction']} - TCS {signal_data['tcs_score']}\n"
        f"[🎯 VIEW INTEL](https://joinbitten.com/hud?mission_id={signal_data['mission_id']})"
    )
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"📱 **METHOD 1: TEXT LINK**\n{text_message}",
        parse_mode='Markdown',
        disable_web_page_preview=False
    )
    
    await asyncio.sleep(2)
    
    # METHOD 2: WEBAPP BUTTON (Recommended)
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    webapp_url = f"https://joinbitten.com/hud?data={encoded_data}"
    
    button_message = (
        f"🔥🔥 **SNIPER SHOT** 🔥🔥\n"
        f"**{signal_data['symbol']} {signal_data['direction']}** | {signal_data['tcs_score']}% | R:R 2.0\n"
        f"Entry: {signal_data['entry']} | TP: {signal_data['tp']}"
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎯 MISSION BRIEFING",
            web_app=WebAppInfo(url=webapp_url)
        )
    ]])
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"📱 **METHOD 2: WEBAPP BUTTON**\n{button_message}",
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    print("✅ Both methods sent!")
    print("\n📊 **COMPARISON:**")
    print("TEXT LINK:")
    print("  ✅ Simple to implement")
    print("  ❌ Requires browser confirmation")
    print("  ❌ Opens in external browser")
    print("  ❌ No seamless experience")
    
    print("\nWEBAPP BUTTON:")
    print("  ✅ Opens instantly in Telegram")
    print("  ✅ No browser confirmation")
    print("  ✅ Seamless mobile experience")
    print("  ✅ Better user experience")
    print("  ❌ Slightly more complex to implement")

if __name__ == "__main__":
    asyncio.run(demo_both_methods())