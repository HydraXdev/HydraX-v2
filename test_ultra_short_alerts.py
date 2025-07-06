#!/usr/bin/env python3
"""Ultra-short Telegram alerts with tier distinction"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = -1002581996861

async def send_tier_alerts():
    """Send ultra-short alerts with visual distinction"""
    bot = Bot(token=BOT_TOKEN)
    
    # NIBBLER Alert - Flashing lights style
    nibbler_message = """🚨 **NIBBLER OPS** 🚨 EURUSD +30p | TCS: 72%"""
    
    nibbler_keyboard = [[InlineKeyboardButton("👁️ VIEW MISSION", url="http://134.199.204.67:5000/?tier=nibbler&symbol=EURUSD&tcs=72")]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=nibbler_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(nibbler_keyboard)
    )
    await asyncio.sleep(1)
    
    # FANG Alert - Mid tier
    fang_message = """⚡ **FANG STRIKE** ⚡ GBPUSD +40p | TCS: 85% 🎯"""
    
    fang_keyboard = [[InlineKeyboardButton("🎯 ENTER BRIEFING", url="http://134.199.204.67:5000/?tier=fang&symbol=GBPUSD&tcs=85")]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=fang_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(fang_keyboard)
    )
    await asyncio.sleep(1)
    
    # SNIPER Alert - Bullseye style
    sniper_message = """🎯 **SNIPER LOCKED** 🎯 [CLASSIFIED] +45p | TCS: 91% 🔥"""
    
    sniper_keyboard = [[InlineKeyboardButton("🔫 ENTER BRIEFING", url="http://134.199.204.67:5000/?tier=commander&symbol=XAUUSD&tcs=91")]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=sniper_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(sniper_keyboard)
    )
    await asyncio.sleep(1)
    
    # APEX Alert - Reality distortion
    apex_message = """🌌 **APEX PROTOCOL** 🌌 QUANTUM SHIFT | TCS: 94% ⚛️"""
    
    apex_keyboard = [[InlineKeyboardButton("🔮 ENTER VOID", url="http://134.199.204.67:5000/?tier=apex&symbol=BTCUSD&tcs=94")]]
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=apex_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(apex_keyboard)
    )

async def main():
    print("🚀 Sending ultra-short tier alerts...")
    await send_tier_alerts()
    print("✅ Done! Check Telegram for clean, distinguishable alerts")

if __name__ == "__main__":
    asyncio.run(main())