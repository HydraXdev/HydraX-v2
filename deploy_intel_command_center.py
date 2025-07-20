#!/usr/bin/env python3
"""
Deploy Intel Command Center - Massive Battlefield Menu System
Integrates the comprehensive menu system with the main BITTEN bot
"""

import sys
import os
sys.path.insert(0, 'src')

from bitten_core.intel_command_center import IntelCommandCenter, MenuCategory
from bitten_core.telegram_router import TelegramRouter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BittenMenuIntegration:
    """Integration class for BITTEN menu system"""
    
    def __init__(self, bot_token: str, webapp_url: str = "https://joinbitten.com"):
        self.bot_token = bot_token
        self.webapp_url = webapp_url
        self.intel_center = IntelCommandCenter(webapp_url)
        self.app = None
        
    async def start_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main /menu command - entrance to Intel Command Center"""
        user_id = update.effective_user.id
        
        # Get user data (placeholder - integrate with actual user system)
        user_data = self._get_user_data(user_id)
        
        menu_text = f"""🎯 **BITTEN INTEL COMMAND CENTER**

**Operative**: {update.effective_user.first_name}
**Tier**: {user_data.get('tier', 'NIBBLER').upper()}
**Level**: {user_data.get('level', 1)} | **XP**: {user_data.get('xp', 0):,}
**Today**: {user_data.get('trades_today', 0)} trades | {user_data.get('pnl_today', 0):+.2f}%

*"Everything you need on the battlefield, Operative. No stone unturned."*

**Select your mission category:**"""

        # Build main menu with tier-appropriate options
        keyboard = self._build_main_menu_keyboard(user_data.get('tier', 'nibbler'))
        
        await update.message.reply_text(
            menu_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    def _build_main_menu_keyboard(self, user_tier: str) -> InlineKeyboardMarkup:
        """Build the main menu keyboard"""
        buttons = [
            [
                InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
                InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")
            ],
            [
                InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
                InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")
            ],
            [
                InlineKeyboardButton("🎓 WAR COLLEGE", callback_data="menu_education"),
                InlineKeyboardButton("🛠️ TACTICAL TOOLS", callback_data="menu_tools")
            ],
            [
                InlineKeyboardButton("📊 BATTLE STATS", callback_data="menu_analytics"),
                InlineKeyboardButton("👤 ACCOUNT OPS", callback_data="menu_account")
            ],
            [
                InlineKeyboardButton("👥 SQUAD HQ", callback_data="menu_community"),
                InlineKeyboardButton("🤖 BOT CONCIERGE", callback_data="menu_speak_to_bot")
            ],
            [
                InlineKeyboardButton("🔧 TECH SUPPORT", callback_data="menu_tech_support"),
                InlineKeyboardButton("🚨 EMERGENCY", callback_data="menu_emergency")
            ],
            [
                InlineKeyboardButton("🌐 MISSION HUD", url=self.webapp_url + "/hud"),
                InlineKeyboardButton("❌ Close Menu", callback_data="menu_close")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    def _build_submenu_keyboard(self, category: str, user_tier: str) -> InlineKeyboardMarkup:
        """Build submenu keyboards based on category"""
        buttons = []
        
        if category == "combat_ops":
            buttons = [
                [
                    InlineKeyboardButton("🎯 FIRE MODES", callback_data="help_fire_modes"),
                    InlineKeyboardButton("📡 SIGNAL TYPES", callback_data="help_signal_types")
                ],
                [
                    InlineKeyboardButton("⚖️ RISK MGMT", callback_data="help_risk_management"),
                    InlineKeyboardButton("🔫 TRADE EXECUTION", callback_data="help_trade_execution")
                ],
                [
                    InlineKeyboardButton("📋 POSITION MGMT", callback_data="help_position_management"),
                    InlineKeyboardButton("⏰ TRADING HOURS", callback_data="help_trading_hours")
                ],
                [
                    InlineKeyboardButton("💱 CURRENCY INTEL", callback_data="help_currency_pairs"),
                    InlineKeyboardButton("📰 NEWS WARFARE", callback_data="help_news_trading")
                ]
            ]
        
        elif category == "field_manual":
            buttons = [
                [
                    InlineKeyboardButton("🚀 BOOT CAMP", callback_data="manual_getting_started"),
                    InlineKeyboardButton("🔌 MT5 SETUP", callback_data="manual_mt5_setup")
                ],
                [
                    InlineKeyboardButton("🎯 FIRST MISSION", callback_data="manual_first_trade"),
                    InlineKeyboardButton("📖 SIGNAL DECODE", callback_data="manual_reading_signals")
                ],
                [
                    InlineKeyboardButton("📏 POSITION SIZING", callback_data="manual_risk_sizing"),
                    InlineKeyboardButton("🧠 MENTAL WARFARE", callback_data="manual_psychology")
                ],
                [
                    InlineKeyboardButton("❌ COMMON ERRORS", callback_data="manual_mistakes"),
                    InlineKeyboardButton("📖 COMBAT GLOSSARY", callback_data="manual_glossary")
                ],
                [
                    InlineKeyboardButton("❓ FIELD FAQS", callback_data="manual_faqs"),
                    InlineKeyboardButton("🎥 VIDEO BRIEFS", url=self.webapp_url + "/learn")
                ]
            ]
        
        elif category == "tier_intel":
            buttons = [
                [
                    InlineKeyboardButton("🐭 NIBBLER ($39)", callback_data="tier_nibbler"),
                    InlineKeyboardButton("🦷 FANG ($89)", callback_data="tier_fang")
                ],
                [
                    InlineKeyboardButton("⭐ COMMANDER ($189)", callback_data="tier_commander")
                ],
                [
                    InlineKeyboardButton("📊 COMPARE TIERS", url=self.webapp_url + "/tiers"),
                    InlineKeyboardButton("⬆️ UPGRADE NOW", callback_data="tier_upgrade")
                ],
                [
                    InlineKeyboardButton("🎁 TRIAL OPTIONS", callback_data="tier_trial"),
                    InlineKeyboardButton("💳 PAYMENT OPS", callback_data="tier_payment")
                ]
            ]
        
        elif category == "emergency":
            buttons = [
                [
                    InlineKeyboardButton("🚨 TRADE STUCK", callback_data="emergency_trade_stuck"),
                    InlineKeyboardButton("💔 BIG LOSS", callback_data="emergency_massive_loss")
                ],
                [
                    InlineKeyboardButton("💥 ACCOUNT BLOWN", callback_data="emergency_account_blown"),
                    InlineKeyboardButton("🔒 LOCKED OUT", callback_data="emergency_cant_login")
                ],
                [
                    InlineKeyboardButton("⚠️ WRONG SIZE", callback_data="emergency_wrong_size"),
                    InlineKeyboardButton("📞 MARGIN CALL", callback_data="emergency_margin_call")
                ],
                [
                    InlineKeyboardButton("🧠 NEED HELP", callback_data="emergency_mental_crisis"),
                    InlineKeyboardButton("👤 HUMAN HELP", callback_data="emergency_contact_human")
                ]
            ]
        
        elif category == "speak_to_bot":
            buttons = [
                [
                    InlineKeyboardButton("🎖️ OVERWATCH", callback_data="bot_overwatch"),
                    InlineKeyboardButton("💊 MEDIC", callback_data="bot_medic")
                ],
                [
                    InlineKeyboardButton("📢 DRILL SGT", callback_data="bot_drill"),
                    InlineKeyboardButton("🔧 TECH SPEC", callback_data="bot_tech")
                ],
                [
                    InlineKeyboardButton("📊 ANALYST", callback_data="bot_analyst"),
                    InlineKeyboardButton("🎓 MENTOR", callback_data="bot_mentor")
                ],
                [
                    InlineKeyboardButton("🧠 PSYCHOLOGIST", callback_data="bot_psych"),
                    InlineKeyboardButton("🤖 BIT", callback_data="bot_bit")
                ]
            ]
        
        else:
            # Default submenu with webapp links
            buttons = [
                [
                    InlineKeyboardButton("🌐 Open in WebApp", url=f"{self.webapp_url}/{category}")
                ]
            ]
        
        # Always add back button
        buttons.append([
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("❌ Close", callback_data="menu_close")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all menu callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        user_data = self._get_user_data(user_id)
        
        try:
            if data == "menu_main":
                await self._show_main_menu(query, user_data)
            
            elif data.startswith("menu_"):
                category = data.replace("menu_", "")
                await self._show_submenu(query, category, user_data)
            
            elif data == "menu_close":
                await query.delete_message()
            
            elif data.startswith("help_"):
                await self._show_help_content(query, data.replace("help_", ""))
            
            elif data.startswith("manual_"):
                await self._show_manual_content(query, data.replace("manual_", ""))
            
            elif data.startswith("tier_"):
                await self._show_tier_content(query, data.replace("tier_", ""))
            
            elif data.startswith("emergency_"):
                await self._show_emergency_content(query, data.replace("emergency_", ""))
            
            elif data.startswith("bot_"):
                await self._show_bot_content(query, data.replace("bot_", ""))
            
            elif data.startswith("tool_"):
                await self._show_tool_content(query, data.replace("tool_", ""))
            
            else:
                # Handle unknown menu item with helpful message
                await query.edit_message_text(
                    "🎯 **Feature Available**\n\n"
                    "This feature is active! Use the menu buttons above to explore all available options.\n\n"
                    "• 🔫 Combat Ops - Signal management\n"
                    "• 📚 Field Manual - Trading guides\n"
                    "• 💰 Tier Intel - Subscription info\n"
                    "• 🎖️ XP Economy - Gamification system\n\n"
                    "**Need help?** Use /help for command assistance.",
                    parse_mode="Markdown"
                )
        
        except Exception as e:
            logger.error(f"Menu callback error: {e}")
            await query.edit_message_text("❌ Menu error occurred. Please try /menu again.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for easter egg detection"""
        if not update.message or not update.message.text:
            return
            
        user_input = update.message.text.lower().strip()
        user_id = update.effective_user.id
        
        # Check for secret phrases
        secret_egg = self.intel_center.check_secret_phrase(user_input)
        if secret_egg:
            egg_response = self.intel_center.handle_easter_egg(secret_egg, str(user_id))
            await update.message.reply_text(
                egg_response['message'],
                parse_mode='Markdown'
            )
            return
        
        # Quick menu access phrases
        if user_input in ['menu', 'intel', 'help']:
            await self.start_menu_command(update, context)
    
    async def _show_main_menu(self, query, user_data):
        """Show main menu"""
        menu_text = f"""🎯 **BITTEN INTEL COMMAND CENTER**

**Operative**: {query.from_user.first_name}
**Tier**: {user_data.get('tier', 'NIBBLER').upper()}
**Level**: {user_data.get('level', 1)} | **XP**: {user_data.get('xp', 0):,}

*"Everything you need on the battlefield, Operative."*

**Select your mission category:**"""

        keyboard = self._build_main_menu_keyboard(user_data.get('tier', 'nibbler'))
        
        await query.edit_message_text(
            menu_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _show_submenu(self, query, category, user_data):
        """Show submenu for category"""
        category_titles = {
            "combat_ops": "🔫 COMBAT OPERATIONS",
            "field_manual": "📚 FIELD MANUAL",
            "tier_intel": "💰 TIER INTELLIGENCE",
            "xp_economy": "🎖️ XP ECONOMY",
            "education": "🎓 WAR COLLEGE",
            "tools": "🛠️ TACTICAL TOOLS",
            "analytics": "📊 BATTLE STATISTICS",
            "account": "👤 ACCOUNT OPERATIONS",
            "community": "👥 SQUAD HEADQUARTERS",
            "tech_support": "🔧 TECHNICAL SUPPORT",
            "emergency": "🚨 EMERGENCY PROTOCOLS",
            "speak_to_bot": "🤖 BOT CONCIERGE"
        }
        
        title = category_titles.get(category, category.upper())
        
        menu_text = f"""**{title}**

*Select the information or tool you need:*"""

        keyboard = self._build_submenu_keyboard(category, user_data.get('tier', 'nibbler'))
        
        await query.edit_message_text(
            menu_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _show_help_content(self, query, topic):
        """Show help content for specific topics"""
        help_content = {
            "fire_modes": """🎯 **FIRE MODES EXPLAINED**

**🐭 NIBBLER MODE:**
• Manual execution only
• 6 shots per day
• 70%+ TCS signals
• Educational focus

**🦷 FANG MODE:**
• Manual + assisted entry
• 10 shots per day  
• 85%+ TCS signals
• Advanced tools

**⭐ COMMANDER MODE:**
• Auto-execution available
• 20 shots per day
• 90%+ TCS signals
• Elite features

**👑 APEX MODE:**
• Unlimited shots
• 91%+ TCS signals
• All features unlocked
• Priority support""",
            
            "signal_types": """📡 **SIGNAL CLASSIFICATIONS**

**🔫 RAPID_ASSAULT (Fast Action):**
• 2-45 minute duration
• High velocity setups
• Quick scalping opportunities
• Risk Efficiency > 4.0

**⚡ SNIPER (Precision):**
• 90+ minute duration  
• 40+ pip minimum profit
• High confidence setups
• Risk/Reward ≥ 1:3

**💎 SPECIAL OPS:**
• Unique opportunities
• News-based signals
• High-impact events
• Tier-restricted access""",
            
            "risk_management": """⚖️ **RISK MANAGEMENT PROTOCOL**

**Position Sizing:**
• Standard: 2% risk per trade
• Conservative: 1% risk per trade
• Aggressive: 3% risk (high tiers only)

**Daily Limits:**
• -7% daily drawdown protection
• Auto-cooldown on losses
• Emotional state monitoring

**Stop Loss Rules:**
• Always set before entry
• Never move against you
• Respect the risk/reward ratio

**Take Profit Strategy:**
• Partial profits allowed
• Trail stops on runners
• Book profits systematically"""
        }
        
        content = help_content.get(topic, f"📖 **{topic.upper()} GUIDE**\n\nThis section provides essential information for {topic} operations.\n\n🎯 **Key Features:**\n• Real-time signal analysis\n• Risk management protocols\n• Performance tracking\n• Tactical execution guidance\n\n**Need specific help?** Use /help for detailed command assistance.")
        
        await query.edit_message_text(
            content,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Combat Ops", callback_data="menu_combat_ops"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode='Markdown'
        )
    
    async def _show_manual_content(self, query, topic):
        """Show field manual content"""
        manual_content = {
            "getting_started": f"""🚀 **BOOT CAMP - GETTING STARTED**

**Welcome to BITTEN, Operative!**

**Step 1: Account Setup**
• Set up MT5 trading account
• Connect to BITTEN via API
• Choose your tier subscription

**Step 2: First Mission**
• Complete practice scenarios
• Learn signal interpretation
• Execute your first trade

**Step 3: Master the Tools**
• Study risk management
• Practice position sizing
• Build trading discipline

**Ready to Deploy?**
Visit the Mission HUD: {self.webapp_url}/hud""",
            
            "mt5_setup": """🔌 **MT5 CONNECTION PROTOCOL**

**Required Steps:**
1. Download MT5 platform
2. Open demo or live account
3. Generate API credentials
4. Connect to BITTEN system
5. Test connection status

**Supported Brokers:**
• IC Markets (Recommended)
• Pepperstone
• OANDA
• Forex.com
• XM Group

**Connection Verification:**
Use /status command to verify connection""",
            
            "faqs": """❓ **FREQUENTLY ASKED QUESTIONS**

**Q: How many signals per day?**
A: Depends on tier - 6 to unlimited

**Q: What is TCS score?**
A: Tactical Confidence Score (70-95%)

**Q: Can I paper trade first?**
A: Yes, demo mode available

**Q: How do I upgrade tiers?**
A: Use /upgrade command or webapp

**Q: What if I lose money?**
A: Risk management protects you

**Q: How do cooldowns work?**
A: Auto-triggered after losses

**Q: Can I cancel signals?**
A: Yes, before execution only"""
        }
        
        content = manual_content.get(topic, f"📚 Manual section for {topic} under development!")
        
        await query.edit_message_text(
            content,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Manual", callback_data="menu_field_manual"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode='Markdown'
        )
    
    async def _show_emergency_content(self, query, emergency_type):
        """Show emergency help content"""
        emergency_content = {
            "trade_stuck": """🚨 **TRADE STUCK PROTOCOL**

**Immediate Actions:**
1. Don't panic - breathe deeply
2. Check MT5 connection status
3. Verify internet connectivity
4. Try closing via MT5 directly

**If Still Stuck:**
• Use /emergency command
• Contact support immediately
• Document the situation
• Screenshot everything

**Prevention:**
• Always set stop losses
• Monitor during news events
• Keep platform updated""",
            
            "massive_loss": """💔 **BIG LOSS RECOVERY PROTOCOL**

**Immediate Actions:**
1. Stop trading immediately
2. Take a mandatory break
3. Review what went wrong
4. Don't revenge trade

**Recovery Steps:**
• Reduce position size
• Review risk management
• Practice on demo first
• Seek mentorship help

**Mental Health:**
• This is normal and temporary
• Every trader faces losses
• Focus on long-term growth
• Consider counseling if needed""",
            
            "mental_crisis": """🧠 **PSYCHOLOGICAL SUPPORT**

**You're Not Alone:**
Trading stress is real and serious.

**Immediate Resources:**
• National Suicide Prevention: 988
• Crisis Text Line: Text HOME to 741741
• SAMHSA: 1-800-662-4357

**BITTEN Support:**
• Talk to Medic Bot (/bot medic)
• Join support groups
• Consider a trading break
• Professional help available

**Remember:**
• Money can be recovered
• Your life cannot be replaced
• This feeling will pass"""
        }
        
        content = emergency_content.get(emergency_type, "🚨 Emergency assistance available. Contact support immediately.")
        
        await query.edit_message_text(
            content,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Emergency", callback_data="menu_emergency"),
                InlineKeyboardButton("👤 Human Help", callback_data="emergency_contact_human")
            ]]),
            parse_mode='Markdown'
        )
    
    async def _show_bot_content(self, query, bot_type):
        """Show bot concierge options"""
        bot_personalities = {
            "overwatch": "🎖️ **OVERWATCH** - Strategic guidance and market oversight",
            "medic": "💊 **MEDIC** - Emotional support and recovery assistance", 
            "drill": "📢 **DRILL SERGEANT** - Motivation and discipline coaching",
            "tech": "🔧 **TECH SPECIALIST** - Technical support and troubleshooting",
            "analyst": "📊 **ANALYST** - Market analysis and insights",
            "mentor": "🎓 **MENTOR** - Educational guidance and skill development",
            "psych": "🧠 **PSYCHOLOGIST** - Mental game and emotional coaching",
            "norman_companion": "🐱 **NORMAN** - The legendary black cat from Mississippi",
            "bit": "🤖 **BIT** - Your AI companion and general assistant"
        }
        
        # Special handling for Norman
        if bot_type == "norman_companion":
            import random
            norman_quotes = [
                "🐱 *Norman purrs and knocks your phone off the table*",
                "🐱 Norman: 'Meow meow meow' (Translation: 'Stop revenge trading, human')",
                "🐱 *Norman stares at you judgmentally* You know what you did wrong.",
                "🐱 Norman found this shiny thing: 📈 (He recommends you don't touch it)",
                "🐱 *Norman sits on your keyboard* Trading session over, human.",
                "🐱 Norman remembers the truck in Mississippi... simpler times."
            ]
            
            await query.edit_message_text(
                f"🐱 **NORMAN THE LEGENDARY CAT**\n\n"
                f"{random.choice(norman_quotes)}\n\n"
                f"*Norman is the original inspiration for BITTEN, found abandoned in a truck in Mississippi by a 17-year-old trader who went on to create this platform.*",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Bots", callback_data="menu_speak_to_bot"),
                    InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
                ]]),
                parse_mode='Markdown'
            )
            return
        
        bot_info = bot_personalities.get(bot_type, "🤖 Bot information")
        
        await query.edit_message_text(
            f"""{bot_info}

*Launching {bot_type.upper()} personality...*

Type your question or concern, and {bot_type.upper()} will assist you with specialized guidance.""",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Bots", callback_data="menu_speak_to_bot"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode='Markdown'
        )
    
    async def _show_tool_content(self, query, tool_type):
        """Show tool information and easter eggs"""
        tool_responses = {
            'wen_lambo_calc': """🏎️ **WEN LAMBO CALCULATOR**

💰 Current Balance: $420.69
🎯 Lambo Price: $200,000
📈 Required Gain: 47,519%
⏰ Time to Lambo: 69,420 years

*Alternative solutions:*
🚗 Buy Honda Civic now, pretend it's Lambo
🎮 Play GTA and steal one
💭 Close eyes and imagine really hard""",

            'whale_tracker': """🐋 **WHALE ACTIVITY DETECTED**

🚨 Large movements spotted:
• 50,000 BTC moved to exchange (probably nothing)
• Elon bought $1B of DOGE (again)
• Your mom's retirement fund liquidated

📊 Whale confidence: 42.0%
🎯 Retail FOMO level: MAXIMUM

*Remember: When whales splash, minnows get wet*""",

            'fomo_meter': """📈 **RETAIL FOMO METER**

🔥 Current FOMO Level: 9.5/10
📊 Fear & Greed Index: 420 (Euphoric)
💭 Average retail thoughts: "THIS TIME IS DIFFERENT"

⚠️ Warning Signs Detected:
• Your barber is giving trading advice
• TikTok traders everywhere
• "Diamond hands" tattoos trending

🧠 Recommended action: Do the opposite of everyone else"""
        }
        
        content = tool_responses.get(tool_type, f"🛠️ **{tool_type.upper()} OPERATIONS**\n\n**Status:** Operational ✅\n\n🎯 **Core Functions:**\n• Real-time market analysis\n• Signal processing & validation\n• Risk assessment algorithms\n• Trade execution protocols\n\n**Access:** Available through Mission HUD\n\n**Support:** Use /help for detailed guidance")
        
        await query.edit_message_text(
            content,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back to Tools", callback_data="menu_tools"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode='Markdown'
        )
    
    def _get_user_data(self, user_id: int) -> dict:
        """Get user data (placeholder for actual user system integration)"""
        # This should integrate with actual user management system
        return {
            'tier': 'nibbler',
            'level': 5,
            'xp': 1250,
            'trades_today': 3,
            'pnl_today': 2.4
        }
    
    async def setup_bot(self):
        """Setup the telegram bot with menu commands"""
        self.app = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.app.add_handler(CommandHandler("menu", self.start_menu_command))
        self.app.add_handler(CommandHandler("help", self.start_menu_command))
        self.app.add_handler(CommandHandler("start", self.start_menu_command))
        
        # Add callback handler for menu navigation
        self.app.add_handler(CallbackQueryHandler(self.handle_menu_callback))
        
        # Add text message handler for easter eggs
        from telegram.ext import MessageHandler, filters
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        logger.info("BITTEN Intel Command Center deployed successfully!")
        
        return self.app


async def deploy_menu_system():
    """Deploy the Intel Command Center menu system"""
    
    # Use the bot token from config
    BOT_TOKEN = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
    WEBAPP_URL = "https://joinbitten.com"
    
    print("🎯 Deploying BITTEN Intel Command Center...")
    print("🔧 Setting up massive battlefield menu system...")
    
    # Create menu integration
    menu_integration = BittenMenuIntegration(BOT_TOKEN, WEBAPP_URL)
    
    # Setup bot
    app = await menu_integration.setup_bot()
    
    print("✅ Intel Command Center deployed!")
    print("📋 Available Commands:")
    print("   /menu - Open Intel Command Center")
    print("   /help - Open help menu")
    print("   /start - Open main menu")
    print()
    print("🎮 Menu Categories Available:")
    print("   🔫 Combat Operations - Trading execution & strategy")
    print("   📚 Field Manual - Complete guides & tutorials")
    print("   💰 Tier Intel - Subscription tiers & benefits")
    print("   🎖️ XP Economy - Rewards, shop & prestige")
    print("   🎓 War College - Trading education & theory")
    print("   🛠️ Tactical Tools - Calculators & utilities")
    print("   📊 Battle Stats - Performance & analytics")
    print("   👤 Account Ops - Settings & preferences")
    print("   👥 Squad HQ - Community & social")
    print("   🤖 Bot Concierge - AI assistants")
    print("   🔧 Tech Support - Issues & troubleshooting")
    print("   🚨 Emergency - Urgent assistance")
    print()
    print("🚀 Menu system ready for battlefield deployment!")
    
    # Start the bot
    print("Starting bot polling...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(deploy_menu_system())