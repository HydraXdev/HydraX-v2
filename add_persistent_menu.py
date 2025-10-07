#!/usr/bin/env python3
"""
Add persistent menu system to BITTEN bot
Creates a permanent keyboard that stays at the bottom
"""


def create_persistent_menu_code():
    """Generate the code for persistent menu system"""

    persistent_menu_code = '''
# Add this import at the top of bitten_production_bot.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Add this method to the BittenProductionBot class
def create_persistent_keyboard(self, user_tier="NIBBLER"):
    """Create persistent keyboard that stays at bottom"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton("🔫 FIRE"),
                KeyboardButton("📊 STATUS"),
                KeyboardButton("💰 CREDITS")
            ],
            [
                KeyboardButton("🎯 TACTICAL"),
                KeyboardButton("📚 HELP"),
                KeyboardButton("⚙️ SETTINGS")
            ],
            [
                KeyboardButton("🏆 RECRUIT"),
                KeyboardButton("📱 MENU"),
                KeyboardButton("❌ HIDE")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,  # This makes it persistent
        is_persistent=True        # This keeps it visible
    )
    return keyboard

# Add this command handler (replace the existing /menu handler)
elif message.text == "/menu":
    # Show persistent menu
    try:
        keyboard = self.create_persistent_keyboard(user_tier)

        menu_text = f"""🎯 **BITTEN TACTICAL INTERFACE**

Welcome {user_name}! Your persistent menu is now active.

**Available Commands:**
🔫 **FIRE** - Execute trades
📊 **STATUS** - System status
💰 **CREDITS** - Referral credits
🎯 **TACTICAL** - Strategy selection
📚 **HELP** - Command help
⚙️ **SETTINGS** - Configuration
🏆 **RECRUIT** - Referral system
📱 **MENU** - Advanced menu
❌ **HIDE** - Hide keyboard

This menu will stay at the bottom for quick access!"""

        self.bot.send_message(
            message.chat.id,
            menu_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Persistent menu error: {e}")
        self.send_adaptive_response(message.chat.id, "❌ Menu system error", user_tier, "error")

# Add handlers for the persistent keyboard buttons
elif message.text == "🔫 FIRE":
    # Redirect to fire command
    message.text = "/fire"
    # Process as fire command (existing logic)

elif message.text == "📊 STATUS":
    # Redirect to status command
    message.text = "/status"
    # Process as status command (existing logic)

elif message.text == "💰 CREDITS":
    # Redirect to credits command
    message.text = "/credits"
    # Process as credits command (existing logic)

elif message.text == "🎯 TACTICAL":
    # Redirect to tactical command
    message.text = "/tactical"
    # Process as tactical command (existing logic)

elif message.text == "📚 HELP":
    # Redirect to help command
    message.text = "/help"
    # Process as help command (existing logic)

elif message.text == "⚙️ SETTINGS":
    # Show settings menu
    settings_text = f"""⚙️ **SETTINGS MENU**

**Fire Mode:** AUTO
**Notifications:** ✅ Enabled
**Risk Level:** 2%
**Session:** London/NY

Use /mode to change fire settings
Use /slots to adjust position sizing"""
    self.send_adaptive_response(message.chat.id, settings_text, user_tier, "settings")

elif message.text == "🏆 RECRUIT":
    # Redirect to recruit command
    message.text = "/recruit"
    # Process as recruit command (existing logic)

elif message.text == "📱 MENU":
    # Show advanced inline menu (existing menu system)
    # Keep the existing /menu logic here

elif message.text == "❌ HIDE":
    # Hide the persistent keyboard
    from telebot.types import ReplyKeyboardRemove
    self.bot.send_message(
        message.chat.id,
        "🫥 Persistent menu hidden. Type /menu to show it again.",
        reply_markup=ReplyKeyboardRemove()
    )
'''

    return persistent_menu_code


def create_hybrid_menu_system():
    """Create a hybrid system with both persistent and inline menus"""

    hybrid_code = '''
# HYBRID MENU SYSTEM - Best of both worlds

def create_quick_keyboard(self):
    """Quick access persistent keyboard (always visible)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton("🔫 FIRE"),
                KeyboardButton("💰 CREDITS"),
                KeyboardButton("📱 MENU")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True
    )
    return keyboard

def create_full_menu_inline(self):
    """Full feature inline menu (appears on demand)"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
            InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")
        ],
        [
            InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
            InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")
        ],
        [
            InlineKeyboardButton("🎯 TACTICAL", callback_data="menu_tactical"),
            InlineKeyboardButton("⚙️ SETTINGS", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("🏆 RECRUIT", callback_data="menu_recruit"),
            InlineKeyboardButton("❌ Close", callback_data="menu_close")
        ]
    ])
    return keyboard

# Auto-enable quick keyboard for new users
def send_welcome_with_keyboard(self, chat_id, user_tier):
    """Send welcome message with persistent quick keyboard"""
    keyboard = self.create_quick_keyboard()

    welcome_text = f"""🎯 **WELCOME TO BITTEN!**

Your quick-access menu is now active at the bottom!

🔫 **FIRE** - Execute trades
💰 **CREDITS** - Check referral balance
📱 **MENU** - Full command center

Type any command or use the buttons below! 🚀"""

    self.bot.send_message(
        chat_id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
'''

    return hybrid_code


def main():
    """Show menu implementation options"""

    print("🎯 PERSISTENT MENU IMPLEMENTATION OPTIONS")
    print("=" * 50)

    print("\n📱 **OPTION 1: FULL PERSISTENT KEYBOARD**")
    print("=" * 40)
    print("✅ Always visible at bottom")
    print("✅ Quick access to all commands")
    print("✅ No need to scroll up")
    print("❌ Takes up screen space")
    print("❌ Limited customization")

    print("\n🔄 **OPTION 2: HYBRID SYSTEM** (RECOMMENDED)")
    print("=" * 45)
    print("✅ Quick buttons always visible: [🔫 FIRE] [💰 CREDITS] [📱 MENU]")
    print("✅ Full inline menu on demand")
    print("✅ Best user experience")
    print("✅ Minimal screen space usage")

    print("\n📋 **CURRENT ISSUE:**")
    print("• InlineKeyboardMarkup = Temporary buttons (disappear when scrolling)")
    print("• ReplyKeyboardMarkup = Persistent buttons (stay at bottom)")
    print("• Your menu uses InlineKeyboardMarkup, so it doesn't stick")

    print("\n🔧 **SOLUTION:**")
    print("Replace the current /menu system with ReplyKeyboardMarkup")
    print("or implement hybrid system for best experience")

    print("\n⚡ **QUICK FIX:**")
    print("1. Add persistent keyboard creation method")
    print("2. Modify /menu command to use ReplyKeyboardMarkup")
    print("3. Add button handlers for persistent menu")
    print("4. Add /hide command to remove keyboard")

    print("\n📝 **IMPLEMENTATION READY:**")
    print("• Persistent menu code generated")
    print("• Hybrid system code generated")
    print("• Ready to integrate into bot")

    return True


if __name__ == "__main__":
    main()

    print("\n🚀 **READY TO IMPLEMENT?**")
    choice = input("Choose implementation (1=Persistent, 2=Hybrid, 3=Show code): ")

    if choice == "1":
        print("\n📝 PERSISTENT MENU CODE:")
        print("=" * 30)
        print(create_persistent_menu_code())
    elif choice == "2":
        print("\n📝 HYBRID MENU CODE:")
        print("=" * 20)
        print(create_hybrid_menu_system())
    elif choice == "3":
        print("\n📝 BOTH CODE OPTIONS:")
        print("=" * 25)
        print("PERSISTENT:")
        print(create_persistent_menu_code())
        print("\nHYBRID:")
        print(create_hybrid_menu_system())
    else:
        print("💡 Run again and choose 1, 2, or 3 to see implementation code")
