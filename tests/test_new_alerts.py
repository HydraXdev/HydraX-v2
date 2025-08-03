#!/usr/bin/env python3
"""
Test the new alert format with both alert types
"""

import asyncio
import json
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

async def test_both_alert_types():
    """Send both SNIPER SHOT and RAPID ASSAULT alerts"""
    
    # Use the correct trading bot
    bot = Bot("7854827710:AAE6m_sNuMk2X6Z3yf2mYO6-6-Clqan-F2c")
    chat_id = "-1002581996861"
    
    print("🚀 Testing both alert types with correct bot...")
    
    # TEST 1: SNIPER SHOT (80%+ TCS)
    sniper_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 87,
        'entry': 1.09235,
        'sl': 1.09035,
        'tp': 1.09635
    }
    
    # Create mission data
    sniper_mission_data = {
        'mission_id': f"SNIPER_{int(datetime.now().timestamp())}",
        'signal': sniper_signal,
        'timestamp': int(datetime.now().timestamp()),
        'user_tier': 'COMMANDER'
    }
    
    encoded_data1 = urllib.parse.quote(json.dumps(sniper_mission_data))
    webapp_url1 = f"https://joinbitten.com/hud?data={encoded_data1}"
    
    sniper_message = (
        f"⚡⚡⚡ **SNIPER OPS** ⚡⚡⚡\n"
        f"**{sniper_signal['symbol']} {sniper_signal['direction']}** | TCS {sniper_signal['tcs_score']}%\n"
        f"🎯 HIGH PRECISION TARGET"
    )
    
    sniper_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="🎯 VIEW INTEL", url=webapp_url1)
    ]])
    
    await bot.send_message(
        chat_id=chat_id,
        text=sniper_message,
        parse_mode='Markdown',
        reply_markup=sniper_keyboard,
        disable_web_page_preview=True
    )
    
    print("✅ SNIPER SHOT alert sent!")
    await asyncio.sleep(3)
    
    # TEST 2: RAPID ASSAULT (65-79% TCS)
    rapid_signal = {
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 72,
        'entry': 1.26545,
        'sl': 1.26745,
        'tp': 1.26145
    }
    
    # Create mission data
    rapid_mission_data = {
        'mission_id': f"RAPID_{int(datetime.now().timestamp())}",
        'signal': rapid_signal,
        'timestamp': int(datetime.now().timestamp()),
        'user_tier': 'FANG'
    }
    
    encoded_data2 = urllib.parse.quote(json.dumps(rapid_mission_data))
    webapp_url2 = f"https://joinbitten.com/hud?data={encoded_data2}"
    
    rapid_message = (
        f"🔫🔫🔫 **RAPID ASSAULT** 🔫🔫🔫\n"
        f"**{rapid_signal['symbol']} {rapid_signal['direction']}** | TCS {rapid_signal['tcs_score']}%\n"
        f"⚡ FAST STRIKE OPPORTUNITY"
    )
    
    rapid_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="🎯 VIEW INTEL", url=webapp_url2)
    ]])
    
    await bot.send_message(
        chat_id=chat_id,
        text=rapid_message,
        parse_mode='Markdown',
        reply_markup=rapid_keyboard,
        disable_web_page_preview=True
    )
    
    print("✅ RAPID ASSAULT alert sent!")
    
    print("\n🎯 **COMPARISON COMPLETE**")
    print("- SNIPER SHOT: 80%+ TCS with 🎯 SNIPER MISSION button")
    print("- RAPID ASSAULT: 65-79% TCS with 📊 VIEW INTEL button")
    print("- Both use URL buttons (better than text links)")
    print("- Both include encoded mission data for HUD")

if __name__ == "__main__":
    asyncio.run(test_both_alert_types())