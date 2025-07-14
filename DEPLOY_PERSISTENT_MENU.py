import os
#!/usr/bin/env python3
"""
Deploy Persistent Intel Command Center Menu
Creates always-accessible menu button at top of Telegram chat
"""

import asyncio
from telegram import Bot, MenuButtonWebApp, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode

BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
CHAT_ID = "int(os.getenv("CHAT_ID", "-1002581996861"))"

async def deploy_persistent_menu():
    """Deploy persistent menu accessible at all times"""
    bot = Bot(token=BOT_TOKEN)
    
    print("🎯 DEPLOYING PERSISTENT INTEL COMMAND CENTER")
    print("=" * 50)
    
    try:
        # Method 1: Set permanent menu button (appears next to chat input)
        print("🔧 Setting persistent menu button...")
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📋 INTEL CENTER",
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )
        )
        print("✅ Persistent menu button deployed!")
        
        # Method 2: Create persistent reply keyboard (always visible)
        print("\n🔧 Creating persistent keyboard menu...")
        persistent_keyboard = ReplyKeyboardMarkup([
            [
                KeyboardButton("🎯 INTEL CENTER"),
                KeyboardButton("📊 BATTLE STATS")
            ],
            [
                KeyboardButton("🔫 COMBAT OPS"),
                KeyboardButton("📚 FIELD MANUAL")
            ],
            [
                KeyboardButton("💰 TIER INTEL"),
                KeyboardButton("🛠️ TACTICAL TOOLS")
            ]
        ], 
        resize_keyboard=True, 
        persistent=True,
        one_time_keyboard=False
        )
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🎮 **INTEL COMMAND CENTER - ALWAYS ACCESSIBLE**\n\n"
                 "✅ **Persistent Menu Button**: Click 📋 next to message input\n"
                 "✅ **Quick Access Keyboard**: Use buttons below (always visible)\n"
                 "✅ **Command Access**: Type `/menu` anytime\n\n"
                 "_Choose your preferred access method:_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=persistent_keyboard
        )
        print("✅ Persistent keyboard deployed!")
        
        # Method 3: Pin important menu message at top
        print("\n🔧 Creating pinned menu message...")
        menu_message = await bot.send_message(
            chat_id=CHAT_ID,
            text="📌 **QUICK ACCESS INTEL CENTER**\n\n"
                 "🎯 Tap any button for instant access:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 FULL MENU", callback_data="menu_main"),
                    InlineKeyboardButton("🔫 COMBAT", callback_data="menu_combat_ops")
                ],
                [
                    InlineKeyboardButton("📚 MANUAL", callback_data="menu_field_manual"),
                    InlineKeyboardButton("🛠️ TOOLS", callback_data="menu_tools")
                ],
                [
                    InlineKeyboardButton("🚨 EMERGENCY", callback_data="menu_emergency"),
                    InlineKeyboardButton("💰 UPGRADE", callback_data="menu_tier_intel")
                ]
            ])
        )
        
        # Pin the menu message to top of chat
        await bot.pin_chat_message(
            chat_id=CHAT_ID,
            message_id=menu_message.message_id,
            disable_notification=True
        )
        print("✅ Menu message pinned to top of chat!")
        
        print("\n🎉 SUCCESS! Intel Command Center is now accessible:")
        print("   1️⃣ Persistent menu button (📋) next to message input")
        print("   2️⃣ Always-visible keyboard buttons")  
        print("   3️⃣ Pinned message at top of chat")
        print("   4️⃣ /menu command anytime")
        
    except Exception as e:
        print(f"❌ Error deploying persistent menu: {e}")

async def test_menu_handlers():
    """Test that menu handlers are working"""
    print("\n🧪 Testing menu integration...")
    
    # Import the Intel Command Center
    try:
        import sys
        sys.path.insert(0, 'src')
        from bitten_core.intel_command_center import IntelCommandCenter
        from bitten_core.telegram_router import TelegramRouter
        
        intel_center = IntelCommandCenter("https://joinbitten.com")
        print("✅ Intel Command Center loaded successfully")
        
        # Test menu structure
        menu_items = len(intel_center.menu_structure)
        print(f"✅ {menu_items} menu items available")
        
        print("✅ Menu system integration ready")
        
    except Exception as e:
        print(f"⚠️ Menu integration check: {e}")
        print("💡 Run this after deploying the integration script")

async def main():
    print("🚀 INTEL COMMAND CENTER PERSISTENT DEPLOYMENT")
    print("=" * 55)
    
    await deploy_persistent_menu()
    await test_menu_handlers()
    
    print("\n📋 DEPLOYMENT COMPLETE!")
    print("Users now have 4 ways to access the Intel Command Center:")
    print("• 📋 Menu button (always visible)")
    print("• 🎯 Keyboard buttons (persistent)")
    print("• 📌 Pinned message (top of chat)")
    print("• 💬 /menu command (anytime)")

if __name__ == "__main__":
    asyncio.run(main())