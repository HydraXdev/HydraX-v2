#!/usr/bin/env python3
"""
Test with the CORRECT ORIGINAL alert templates from the system
"""

import asyncio
import json
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

async def test_correct_alerts():
    """Send alerts with the ORIGINAL CORRECT templates"""
    
    bot = Bot("7854827710:AAE9kCptkoSl8lmQwmX940UMqFWOb3TmTI0")
    chat_id = "-1002581996861"
    
    print("🚀 Testing ORIGINAL CORRECT alert templates...")
    
    # TEST 1: SNIPER OPS (80%+ TCS) - ORIGINAL FORMAT
    sniper_tcs = 87
    sniper_symbol = "EURUSD"
    
    sniper_mission_data = {
        'mission_id': f"SNIPER_{int(datetime.now().timestamp())}",
        'signal': {'symbol': sniper_symbol, 'tcs_score': sniper_tcs},
        'timestamp': int(datetime.now().timestamp()),
        'user_tier': 'COMMANDER'
    }
    
    encoded_data1 = urllib.parse.quote(json.dumps(sniper_mission_data))
    webapp_url1 = f"https://joinbitten.com/hud?data={encoded_data1}"
    
    # ORIGINAL SNIPER OPS FORMAT
    sniper_message = f"⚡ **SNIPER OPS** ⚡ [{sniper_tcs}%]\n🎖️ {sniper_symbol} ELITE ACCESS"
    
    sniper_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="VIEW INTEL", url=webapp_url1)
    ]])
    
    await bot.send_message(
        chat_id=chat_id,
        text=sniper_message,
        parse_mode='Markdown',
        reply_markup=sniper_keyboard,
        disable_web_page_preview=True
    )
    
    print("✅ SNIPER OPS alert sent!")
    await asyncio.sleep(3)
    
    # TEST 2: RAPID ASSAULT (65-79% TCS) - ORIGINAL FORMAT
    rapid_tcs = 72
    rapid_symbol = "GBPUSD"
    
    rapid_mission_data = {
        'mission_id': f"RAPID_{int(datetime.now().timestamp())}",
        'signal': {'symbol': rapid_symbol, 'tcs_score': rapid_tcs},
        'timestamp': int(datetime.now().timestamp()),
        'user_tier': 'FANG'
    }
    
    encoded_data2 = urllib.parse.quote(json.dumps(rapid_mission_data))
    webapp_url2 = f"https://joinbitten.com/hud?data={encoded_data2}"
    
    # ORIGINAL RAPID ASSAULT FORMAT
    rapid_message = f"🔫 **RAPID ASSAULT** [{rapid_tcs}%]\n🔥 {rapid_symbol} STRIKE 💥"
    
    rapid_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="MISSION BRIEF", url=webapp_url2)
    ]])
    
    await bot.send_message(
        chat_id=chat_id,
        text=rapid_message,
        parse_mode='Markdown',
        reply_markup=rapid_keyboard,
        disable_web_page_preview=True
    )
    
    print("✅ RAPID ASSAULT alert sent!")
    
    print("\n🎯 **ORIGINAL CORRECT TEMPLATES RESTORED**")
    print("- SNIPER OPS: ⚡ SNIPER OPS ⚡ [87%] + 🎖️ ELITE ACCESS")
    print("- RAPID ASSAULT: 🔫 RAPID ASSAULT [72%] + 🔥 STRIKE 💥")
    print("- Buttons: VIEW INTEL / MISSION BRIEF")

if __name__ == "__main__":
    asyncio.run(test_correct_alerts())