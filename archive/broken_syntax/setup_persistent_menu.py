import os
#!/usr/bin/env python3
"""
Setup Persistent Menu - Simple Integration
Creates always-accessible Intel Command Center menu
"""

import asyncio
from telegram import Bot, MenuButtonWebApp, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode

BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

async def setup_persistent_menu():
    """Setup persistent menu button"""
    bot = Bot(token=BOT_TOKEN)
    
    print("🎯 Setting up persistent Intel Command Center...")
    
    # Create persistent menu button (appears next to message input)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="📋 INTEL CENTER",
            web_app=WebAppInfo(url="https://joinbitten.com/hud")
        )
    )
    
    # Create persistent keyboard
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🎯 INTEL CENTER"), KeyboardButton("📊 STATS")],
        [KeyboardButton("🔫 COMBAT"), KeyboardButton("📚 MANUAL")],
        [KeyboardButton("💰 TIER INFO"), KeyboardButton("🚨 EMERGENCY")]
    ], resize_keyboard=True, persistent=True)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🎮 **INTEL COMMAND CENTER DEPLOYED**\n\n"
             "✅ **Menu Button**: 📋 (next to message input)\n"
             "✅ **Quick Buttons**: Always visible below\n"
             "✅ **Commands**: `/menu` anytime\n\n"
             "*Everything you need on the battlefield!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    print("✅ Persistent Intel Command Center deployed!")
    print("📍 Location: Menu button (📋) + persistent keyboard")

if __name__ == "__main__":
    asyncio.run(setup_persistent_menu())