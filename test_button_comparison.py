#!/usr/bin/env python3
# Compare FIRE vs EXECUTE buttons

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import sys
sys.path.append('/root/HydraX-v2')
from config.telegram import TelegramConfig

# Import templates
exec(open('/root/HydraX-v2/src/bitten_core/trade_alert_templates.py').read())

BOT_TOKEN = TelegramConfig.BOT_TOKEN
CHAT_ID = str(TelegramConfig.MAIN_CHAT_ID)

async def send_button_comparison():
    """Compare different button options"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test data
    arcade_data = {
        'callsign': '🌅 DAWN RAID',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.08450,
        'take_profit_pips': 15,
        'stop_loss_pips': 10,
        'tcs_score': 82,
        'active_traders': 17,
        'seconds_remaining': 272
    }
    
    sniper_data = {
        'symbol': 'USDJPY',
        'direction': 'SELL',
        'entry_price': 110.250,
        'take_profit_pips': 35,
        'stop_loss_pips': 15,
        'tcs_score': 94,
        'active_traders': 8,
        'seconds_remaining': 495
    }
    
    print("📤 Sending button comparison...")
    
    # Intro message
    intro = """🎯 **BUTTON COMPARISON**
    
Let's compare different button options for arcade vs sniper alerts:"""
    
    await bot.send_message(chat_id=CHAT_ID, text=intro, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(1)
    
    # Option 1: FIRE for arcade
    message1 = TradeAlertTemplates.arcade_alert_final(arcade_data)
    keyboard1 = [[
        InlineKeyboardButton("🔫 FIRE", callback_data="fire_1"),
        InlineKeyboardButton("📊 INTEL", callback_data="intel_1")
    ]]
    await bot.send_message(
        chat_id=CHAT_ID,
        text="**Option 1 - Arcade with FIRE:**\n\n" + message1,
        reply_markup=InlineKeyboardMarkup(keyboard1),
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(1.5)
    
    # Option 2: EXECUTE for arcade
    keyboard2 = [[
        InlineKeyboardButton("⚡ EXECUTE", callback_data="execute_1"),
        InlineKeyboardButton("📊 INTEL", callback_data="intel_2")
    ]]
    await bot.send_message(
        chat_id=CHAT_ID,
        text="**Option 2 - Arcade with EXECUTE:**\n\n" + message1,
        reply_markup=InlineKeyboardMarkup(keyboard2),
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(1.5)
    
    # Sniper with updated format
    message_sniper = TradeAlertTemplates.sniper_compact(sniper_data)
    keyboard_sniper = [[
        InlineKeyboardButton("🎯 EXECUTE", callback_data="execute_sniper"),
        InlineKeyboardButton("🚫 ABORT", callback_data="abort_sniper")
    ]]
    await bot.send_message(
        chat_id=CHAT_ID,
        text="**Sniper with bullseye & stats:**\n\n" + message_sniper,
        reply_markup=InlineKeyboardMarkup(keyboard_sniper),
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(1.5)
    
    # Summary
    summary = """**MY THOUGHTS:**

For accuracy representation:
• 🎯 Bullseye = Perfect for snipers
• 🔫 FIRE = Action-oriented for arcade
• ⚡ EXECUTE = More tactical/precise

EXECUTE feels more professional and works for both arcade and sniper. It implies precision and decisiveness.

What do you think?"""
    
    await bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode=ParseMode.MARKDOWN)
    
    print("✅ Comparison sent!")

if __name__ == "__main__":
    asyncio.run(send_button_comparison())