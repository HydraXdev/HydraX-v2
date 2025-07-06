#!/usr/bin/env python3
"""Test WebApp integration with actual briefing links"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
import urllib.parse

# Bot configuration
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861
WEBAPP_URL = "http://134.199.204.67:5000"

async def send_webapp_alerts():
    """Send alerts with actual WebApp buttons"""
    bot = Bot(token=BOT_TOKEN)
    
    # NIBBLER WebApp Alert
    nibbler_params = {
        'tier': 'nibbler',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry': '1.0823',
        'tcs': '72',
        'signal_id': 'SIG-N001'
    }
    nibbler_url = f"{WEBAPP_URL}/?{urllib.parse.urlencode(nibbler_params)}"
    
    nibbler_message = """🟢 **NIBBLER OPS** | EURUSD BUY
Entry: 1.0823 | Risk: -20p | Target: +30p
TCS: 72% | R/R: 1:1.5

_Click below to see your personalized mission brief_"""
    
    # Standard URL button for WebApp
    nibbler_keyboard = [
        [InlineKeyboardButton("📊 OPEN MISSION BRIEF", url=nibbler_url)],
        [InlineKeyboardButton("🔓 Upgrade to FANG", callback_data="upgrade")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=nibbler_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(nibbler_keyboard)
    )
    await asyncio.sleep(2)
    
    # FANG WebApp Alert
    fang_params = {
        'tier': 'fang',
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'entry': '1.2750',
        'tcs': '85',
        'signal_id': 'SIG-F002'
    }
    fang_url = f"{WEBAPP_URL}/?{urllib.parse.urlencode(fang_params)}"
    
    fang_message = """🔵 **FANG TACTICAL** | GBPUSD SELL
Entry: 1.2750 | SL: -25p | TP: +40p
TCS: 85% 🎯 | R/R: 1:1.6
🤖 AI Confidence: HIGH

_Your personalized brief with AI analysis awaits_"""
    
    fang_keyboard = [
        [InlineKeyboardButton("🎯 VIEW TACTICAL BRIEF", url=fang_url)],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=fang_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(fang_keyboard)
    )
    await asyncio.sleep(2)
    
    # COMMANDER WebApp Alert
    commander_params = {
        'tier': 'commander',
        'symbol': 'XAUUSD',
        'direction': 'BUY',
        'entry': '1825.50',
        'tcs': '91',
        'signal_id': 'SIG-C003'
    }
    commander_url = f"{WEBAPP_URL}/?{urllib.parse.urlencode(commander_params)}"
    
    commander_message = """🟡 **COMMANDER ELITE** | XAUUSD BUY
Entry: $1825.50 | SL: -250p | TP: +450p
TCS: 91% 🔥 | R/R: 1:1.8
🎯 SPOTTER CONFIRMED | 👥 Squad: 87% in

_Full intel package with squad data ready_"""
    
    commander_keyboard = [
        [InlineKeyboardButton("💎 ACCESS FULL INTEL", url=commander_url)],
        [InlineKeyboardButton("👥 Squad View", callback_data="squad")]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=commander_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(commander_keyboard)
    )
    await asyncio.sleep(2)
    
    # APEX WebApp Alert
    apex_params = {
        'tier': 'apex',
        'symbol': 'BTCUSD',
        'direction': 'BUY',
        'entry': '45250',
        'tcs': '94',
        'signal_id': 'SIG-A004'
    }
    apex_url = f"{WEBAPP_URL}/?{urllib.parse.urlencode(apex_params)}"
    
    apex_message = """🔴 **APEX PROTOCOL** | BTCUSD BUY
Entry: $45,250 | SL: -$500 | TP: +$1,200
TCS: 94% 🌌 | R/R: 1:2.4
🔮 Quantum: 94.7% | Reality: Level 3

_Enter the quantum realm_"""
    
    apex_keyboard = [
        [InlineKeyboardButton("🌌 ENTER QUANTUM BRIEF", url=apex_url)]
    ]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=apex_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(apex_keyboard)
    )
    
    # Instructions
    await asyncio.sleep(2)
    instructions = """📱 **WEBAPP BRIEFINGS LIVE!**

Click any button above to see your personalized mission brief.

Each tier sees:
• Personal stats (last trade, streak, etc.)
• Full risk/reward info
• Tier-specific analysis tools

The WebApp shows how your personal performance affects each trade decision!

🔗 Direct test link: http://134.199.204.67:5000/test"""
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=instructions,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("✅ WebApp integrated alerts sent!")

async def main():
    """Run the WebApp integration test"""
    print("🚀 Sending WebApp integrated alerts...")
    print("=" * 50)
    
    await send_webapp_alerts()
    
    print("\n✅ Check Telegram - click the buttons to see actual WebApp briefings!")
    print("🔗 WebApp server running at: http://134.199.204.67:5000")

if __name__ == "__main__":
    asyncio.run(main())