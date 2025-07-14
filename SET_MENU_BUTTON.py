import os
#!/usr/bin/env python3
"""Set the bot's menu button to open the Mini App"""

import asyncio
from telegram import Bot, MenuButtonWebApp, WebAppInfo
from telegram.constants import ParseMode

BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

async def set_menu_button():
    """Configure the bot's menu button as a Mini App launcher"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Set menu button for all users
        print("🔧 Setting global menu button...")
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎮 BITTEN HUD",
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )
        )
        print("✅ Global menu button set!")
        
        # Also set for specific chat
        print("\n🔧 Setting chat-specific menu button...")
        await bot.set_chat_menu_button(
            chat_id=CHAT_ID,
            menu_button=MenuButtonWebApp(
                text="🎮 MISSION INTEL",
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )
        )
        print("✅ Chat menu button set!")
        
        # Send instructions
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🎮 *Mini App Configured!*\n\n"
                "The bot menu button (📎 icon) now opens BITTEN HUD directly!\n\n"
                "Try it:\n"
                "1️⃣ Click the 📎 menu icon (bottom left)\n"
                "2️⃣ Select '🎮 BITTEN HUD'\n"
                "3️⃣ HUD opens instantly - no confirmation!\n\n"
                "_This is the official Telegram Mini App method_"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        
        print("\n✨ Success! Check the bot menu button in Telegram")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def send_inline_webapp():
    """Try inline webapp approach"""
    bot = Bot(token=BOT_TOKEN)
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
    
    # Try with reply keyboard
    try:
        print("\n🔧 Trying reply keyboard with WebApp...")
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton(
                text="🎮 Open BITTEN HUD",
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )]
        ], resize_keyboard=True)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📱 *WebApp Keyboard Test*\n\nTap the button below to open HUD directly:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print("✅ Reply keyboard sent!")
        
    except Exception as e:
        print(f"❌ Reply keyboard failed: {e}")

async def main():
    print("🚀 Configuring Telegram Mini App")
    print("================================")
    
    # Set menu button
    await set_menu_button()
    
    # Try inline approach
    await send_inline_webapp()
    
    print("\n📝 Notes:")
    print("- Menu button method is the official way")
    print("- Reply keyboard WebApp requires newer Telegram clients")
    print("- Some methods may require app restart to take effect")

if __name__ == "__main__":
    asyncio.run(main())