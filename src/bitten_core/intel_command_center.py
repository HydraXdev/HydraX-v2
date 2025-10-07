"""
BITTEN Intel Command Center
Comprehensive dropdown menu system for all user needs
White-glove concierge service with military precision
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from .rank_access import UserRank
from .telegram_router import CommandResult


class MenuCategory(Enum):
    """Main menu categories"""

    MAIN = "main"
    COMBAT_OPS = "combat_ops"
    FIELD_MANUAL = "field_manual"
    TIER_INTEL = "tier_intel"
    XP_ECONOMY = "xp_economy"
    TECH_SUPPORT = "tech_support"
    EMERGENCY = "emergency"
    SPEAK_TO_BOT = "speak_to_bot"
    EDUCATION = "education"
    TOOLS = "tools"
    ACCOUNT = "account"
    COMMUNITY = "community"
    ANALYTICS = "analytics"


@dataclass
class MenuItem:
    """Menu item configuration"""

    id: str
    label: str
    icon: str
    category: MenuCategory
    parent: Optional[str] = None
    action: Optional[str] = None
    data: Optional[Dict] = None
    tier_required: Optional[UserRank] = None
    description: Optional[str] = None


class IntelCommandCenter:
    """
    Comprehensive dropdown menu system
    White-glove concierge service for BITTEN operatives
    """

    def __init__(self, webapp_url: str = "https://your-domain.com/bitten"):
        self.webapp_url = webapp_url
        self.menu_structure = self._build_menu_structure()
        self.active_sessions = {}  # Track user menu states
        self.easter_eggs = self._init_easter_eggs()
        self.secret_sequences = {}  # Track user input sequences

    def _init_easter_eggs(self):
        """Initialize easter egg system"""
        return {
            "secret_combos": {
                "show me the money": "profit_vault",
                "norman lives": "cat_companion_mode",
                "diamond hands": "hodl_therapy",
                "wen lambo": "lambo_calculator",
                "number go up": "hopium_injection",
                "trust the process": "zen_mode",
                "the cake is a lie": "portal_mode",
                "bitten by the bug": "dev_secrets",
            },
            "konami_code": ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"],
            "bit_quotes": [
                "🐱 *Bit chirps and knocks your phone off the table*",
                "🐱 Bit: 'Chirp chirp chirp' (Translation: 'Stop revenge trading, human')",
                "🐱 *Bit stares at you judgmentally* You know what you did wrong.",
                "🐱 Bit found this shiny thing: 📈 (He recommends you don't touch it)",
            ],
            "norman_quotes": [
                "👦 Norman: 'Hey, maybe we should review that trade plan again...'",
                "👦 Norman: 'Bit thinks your risk management needs work'",
                "👦 Norman: 'The Mississippi way is slow and steady, not YOLO'",
                "👦 Norman: 'Remember, we're learning together here'",
            ],
        }

    def _build_menu_structure(self) -> Dict[str, MenuItem]:
        """Build the complete menu structure"""
        menu = {}

        # MAIN MENU
        menu["main"] = MenuItem(
            id="main",
            label="INTEL COMMAND CENTER",
            icon="🎯",
            category=MenuCategory.MAIN,
            description='"Everything you need, Operative. No stone unturned."',
        )

        # Level 1: Main Categories
        main_categories = [
            ("combat_ops", "🔫 COMBAT OPS", "Trading operations & execution"),
            ("field_manual", "📚 FIELD MANUAL", "Complete guides & tutorials"),
            ("tier_intel", "💰 TIER INTEL", "Subscription tiers & benefits"),
            ("xp_economy", "🎖️ XP ECONOMY", "Rewards, shop & prestige"),
            ("education", "🎓 WAR COLLEGE", "Trading education & theory"),
            ("tools", "🛠️ TACTICAL TOOLS", "Calculators & utilities"),
            ("analytics", "📊 BATTLE STATS", "Performance & analytics"),
            ("account", "👤 ACCOUNT OPS", "Settings & preferences"),
            ("community", "👥 SQUAD HQ", "Community & social"),
            ("tech_support", "🔧 TECH SUPPORT", "Issues & troubleshooting"),
            ("emergency", "🚨 EMERGENCY", "Urgent assistance"),
            ("speak_to_bot", "🤖 BOT CONCIERGE", "AI assistants"),
        ]

        for cat_id, label, desc in main_categories:
            menu[cat_id] = MenuItem(
                id=cat_id,
                label=label,
                icon=label.split()[0],
                category=MenuCategory.MAIN,
                parent="main",
                description=desc,
            )

        # COMBAT OPS Submenu
        combat_items = [
            ("fire_modes", "🎯 FIRE MODES", "BIT vs COMMANDER explained"),
            ("signal_types", "📡 SIGNAL TYPES", "Arcade, Sniper, Special ops"),
            ("risk_management", "⚖️ RISK MANAGEMENT", "Risk modes & cooldowns"),
            ("trade_execution", "🔫 TRADE EXECUTION", "How to fire positions"),
            ("position_management", "📋 POSITION MGMT", "Manage open trades"),
            ("trading_hours", "⏰ TRADING HOURS", "Best times to trade"),
            ("currency_pairs", "💱 CURRENCY INTEL", "Pair characteristics"),
            ("entry_types", "🎪 ENTRY TYPES", "Market vs pending orders"),
            ("exit_strategies", "🚪 EXIT STRATEGIES", "TP, SL, partials"),
            ("news_trading", "📰 NEWS WARFARE", "Trading around events"),
        ]

        for item_id, label, desc in combat_items:
            menu[f"combat_{item_id}"] = MenuItem(
                id=f"combat_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.COMBAT_OPS,
                parent="combat_ops",
                description=desc,
            )

        # FIELD MANUAL Submenu
        manual_items = [
            ("getting_started", "🚀 BOOT CAMP", "Complete beginner guide"),
            ("webapp_setup", "🌐 WEBAPP ACCESS", "Access your trading dashboard"),
            ("first_trade", "🎯 FIRST MISSION", "Your first trade walkthrough"),
            ("reading_signals", "📖 SIGNAL DECODE", "Understanding briefings"),
            ("risk_sizing", "📏 POSITION SIZING", "Calculate lot sizes"),
            ("psychology", "🧠 MENTAL WARFARE", "Trading psychology"),
            ("mistakes", "❌ COMMON ERRORS", "Avoid these mistakes"),
            ("glossary", "📖 COMBAT GLOSSARY", "Trading terms explained"),
            ("faqs", "❓ FIELD FAQS", "Frequently asked questions"),
            ("video_guides", "🎥 VIDEO BRIEFS", "Visual tutorials"),
        ]

        for item_id, label, desc in manual_items:
            menu[f"manual_{item_id}"] = MenuItem(
                id=f"manual_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.FIELD_MANUAL,
                parent="field_manual",
                description=desc,
            )

        # TIER INTEL Submenu
        tier_items = [
            ("nibbler_tier", "🐭 NIBBLER ($39)", "Entry tier features"),
            ("fang_tier", "🦷 FANG ($89)", "Advanced features"),
            ("commander_tier", "⭐ COMMANDER ($189)", "Elite access"),
            ("apex_tier", "👑 ()", "Maximum power"),
            ("compare_tiers", "📊 COMPARE TIERS", "Side-by-side comparison"),
            ("upgrade_now", "⬆️ UPGRADE NOW", "Instant tier upgrade"),
            ("downgrade_info", "⬇️ DOWNGRADE INFO", "How downgrades work"),
            ("trial_info", "🎁 TRIAL OPTIONS", "Test drive higher tiers"),
            ("payment_methods", "💳 PAYMENT OPS", "Accepted payments"),
            ("refund_policy", "↩️ REFUND INTEL", "Money-back terms"),
        ]

        for item_id, label, desc in tier_items:
            menu[f"tier_{item_id}"] = MenuItem(
                id=f"tier_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TIER_INTEL,
                parent="tier_intel",
                description=desc,
            )

        # XP ECONOMY Submenu
        xp_items = [
            ("earning_xp", "💰 EARNING XP", "All ways to gain XP"),
            ("xp_shop", "🛍️ XP SHOP", "Spend your XP points"),
            ("prestige_system", "⭐ PRESTIGE OPS", "50k XP reset benefits"),
            ("daily_challenges", "📅 DAILY MISSIONS", "Today's challenges"),
            ("weekly_events", "🎪 WEEKLY EVENTS", "Special XP events"),
            ("xp_multipliers", "🔥 XP BOOSTERS", "Multiply your gains"),
            ("leaderboards", "🏆 LEADERBOARDS", "Top operatives"),
            ("xp_history", "📜 XP LEDGER", "Your XP transactions"),
            ("medals_showcase", "🎖️ MEDAL RACK", "Your achievements"),
            ("referral_program", "👥 RECRUIT REWARDS", "Earn by recruiting"),
        ]

        for item_id, label, desc in xp_items:
            menu[f"xp_{item_id}"] = MenuItem(
                id=f"xp_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.XP_ECONOMY,
                parent="xp_economy",
                description=desc,
            )

        # EDUCATION (War College) Submenu
        education_items = [
            ("forex_basics", "📚 FOREX 101", "Currency market basics"),
            ("technical_analysis", "📈 TECH ANALYSIS", "Charts & indicators"),
            ("fundamental_analysis", "🌍 FUNDAMENTALS", "Economic factors"),
            ("risk_management_edu", "🛡️ RISK DOCTRINE", "Protect your capital"),
            ("trading_strategies", "🎯 BATTLE TACTICS", "Proven strategies"),
            ("market_psychology", "🧠 MARKET PSYCH", "Crowd behavior"),
            ("economic_calendar", "📅 ECON CALENDAR", "Important events"),
            ("recommended_books", "📚 READING LIST", "Essential books"),
            ("webinar_schedule", "🎓 LIVE TRAINING", "Upcoming webinars"),
            ("quiz_challenges", "🎮 KNOWLEDGE TEST", "Test your skills"),
        ]

        for item_id, label, desc in education_items:
            menu[f"edu_{item_id}"] = MenuItem(
                id=f"edu_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.EDUCATION,
                parent="education",
                description=desc,
            )

        # TOOLS Submenu
        tools_items = [
            ("compound_calc", "📊 COMPOUND CALC", "Growth projections"),
            ("position_calc", "🧮 LOT SIZE CALC", "Perfect position sizing"),
            ("risk_calc", "⚖️ RISK CALCULATOR", "Risk/reward ratios"),
            ("pip_calc", "💰 PIP CALCULATOR", "Pip values by pair"),
            ("profit_calc", "💵 PROFIT CALC", "Potential profits"),
            ("drawdown_calc", "📉 DRAWDOWN CALC", "Max loss scenarios"),
            ("margin_calc", "🏦 MARGIN CALC", "Required margin"),
            ("correlation_tool", "🔗 CORRELATION", "Pair correlations"),
            ("timezone_convert", "🌍 TIME ZONES", "Market sessions"),
            ("trade_journal", "📔 TRADE JOURNAL", "Track your trades"),
            ("wen_lambo_calc", "🏎️ WEN LAMBO", "Calculate your path to riches"),
            ("whale_tracker", "🐋 WHALE ACTIVITY", "Big money movements detected"),
            ("fomo_meter", "📈 FOMO METER", "Retail sentiment indicator"),
        ]

        for item_id, label, desc in tools_items:
            menu[f"tool_{item_id}"] = MenuItem(
                id=f"tool_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TOOLS,
                parent="tools",
                description=desc,
                action="webapp",  # Most tools open webapp
            )

        # ANALYTICS Submenu
        analytics_items = [
            ("performance_stats", "📊 PERFORMANCE", "Your trading stats"),
            ("win_rate", "🎯 WIN RATE", "Success metrics"),
            ("profit_curve", "📈 PROFIT CURVE", "Equity growth"),
            ("best_pairs", "💱 BEST PAIRS", "Your profitable pairs"),
            ("worst_pairs", "❌ WORST PAIRS", "Pairs to avoid"),
            ("time_analysis", "⏰ TIME ANALYSIS", "Best trading times"),
            ("streak_analysis", "🔥 STREAK DATA", "Win/loss streaks"),
            ("monthly_report", "📅 MONTHLY REPORT", "Detailed breakdown"),
            ("compare_period", "📊 COMPARE PERIODS", "Progress over time"),
            ("export_data", "💾 EXPORT DATA", "Download your stats"),
        ]

        for item_id, label, desc in analytics_items:
            menu[f"analytics_{item_id}"] = MenuItem(
                id=f"analytics_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.ANALYTICS,
                parent="analytics",
                description=desc,
            )

        # ACCOUNT OPS Submenu
        account_items = [
            ("profile_settings", "👤 PROFILE", "Your operative profile"),
            ("notification_prefs", "🔔 NOTIFICATIONS", "Alert preferences"),
            ("sound_settings", "🔊 SOUND CONFIG", "Audio preferences"),
            ("display_settings", "🖥️ DISPLAY", "UI preferences"),
            ("security_settings", "🔐 SECURITY", "2FA & passwords"),
            ("api_keys", "🔑 API KEYS", "MT5 connections"),
            ("billing_info", "💳 BILLING", "Payment methods"),
            ("subscription_mgmt", "📋 SUBSCRIPTION", "Manage your tier"),
            ("data_privacy", "🔒 PRIVACY", "Data settings"),
            ("delete_account", "❌ DEACTIVATE", "Account removal"),
        ]

        for item_id, label, desc in account_items:
            menu[f"account_{item_id}"] = MenuItem(
                id=f"account_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.ACCOUNT,
                parent="account",
                description=desc,
            )

        # COMMUNITY Submenu
        community_items = [
            ("squad_chat", "💬 SQUAD CHAT", "Team communication"),
            ("find_squad", "🔍 FIND SQUAD", "Join a team"),
            ("create_squad", "➕ CREATE SQUAD", "Start your team"),
            ("squad_leaderboard", "🏆 SQUAD RANKS", "Top teams"),
            ("mentorship", "🎓 MENTORSHIP", "Learn from elites"),
            ("share_trades", "📤 SHARE WINS", "Brag about profits"),
            ("follow_elites", "👁️ FOLLOW ELITES", "Watch top traders"),
            ("forums", "💭 WAR ROOM", "Discussion forums"),
            ("events_calendar", "📅 EVENTS", "Community events"),
            ("referral_center", "🎁 REFERRAL HQ", "Invite & earn"),
        ]

        for item_id, label, desc in community_items:
            menu[f"community_{item_id}"] = MenuItem(
                id=f"community_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.COMMUNITY,
                parent="community",
                description=desc,
            )

        # TECH SUPPORT Submenu
        support_items = [
            ("connection_issues", "🔌 CONNECTION", "MT5 connection help"),
            ("trade_failures", "❌ TRADE FAILS", "Why trades fail"),
            ("login_problems", "🔐 LOGIN ISSUES", "Access problems"),
            ("subscription_issues", "💳 BILLING HELP", "Payment problems"),
            ("signal_issues", "📡 SIGNAL ISSUES", "Not receiving signals"),
            ("webapp_problems", "🌐 WEBAPP BUGS", "Interface issues"),
            ("mobile_issues", "📱 MOBILE HELP", "Phone app issues"),
            ("api_errors", "⚠️ API ERRORS", "Technical errors"),
            ("report_bug", "🐛 REPORT BUG", "Submit bug report"),
            ("feature_request", "💡 SUGGESTIONS", "Request features"),
        ]

        for item_id, label, desc in support_items:
            menu[f"support_{item_id}"] = MenuItem(
                id=f"support_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TECH_SUPPORT,
                parent="tech_support",
                description=desc,
            )

        # EMERGENCY Submenu
        emergency_items = [
            ("stop_pause", "⏸️ PAUSE NEW TRADES", "Stop new signal executions only"),
            ("stop_close_all", "🛑 CLOSE ALL POSITIONS", "Close all trades immediately"),
            ("account_lock", "🔒 ACCOUNT LOCKOUT", "Complete trading lockout"),
            ("trade_stuck", "🚨 TRADE STUCK", "Position won't close"),
            ("massive_loss", "💔 BIG LOSS", "Recovery protocol"),
            ("account_blown", "💥 ACCOUNT BLOWN", "What to do now"),
            ("cant_login", "🔒 LOCKED OUT", "Emergency access"),
            ("wrong_size", "⚠️ WRONG SIZE", "Traded too big"),
            ("margin_call", "📞 MARGIN CALL", "Urgent help"),
            ("hacked_account", "🔓 HACKED", "Security breach"),
            ("payment_failed", "❌ PAYMENT FAIL", "Subscription lapsed"),
            ("mental_crisis", "🧠 NEED HELP", "Trading psychology"),
            ("hodl_therapy", "💎 HODL THERAPY", "Diamond hands support group"),
            ("paper_hands_rehab", "📄 PAPER HANDS REHAB", "Weak hands recovery"),
            ("contact_human", "👤 HUMAN HELP", "Speak to support"),
        ]

        for item_id, label, desc in emergency_items:
            menu[f"emergency_{item_id}"] = MenuItem(
                id=f"emergency_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.EMERGENCY,
                parent="emergency",
                description=desc,
                action="urgent",
            )

        # BOT CONCIERGE Submenu
        bot_items = [
            ("overwatch_bot", "🎖️ OVERWATCH", "Strategic guidance"),
            ("medic_bot", "💊 MEDIC", "Recovery & support"),
            ("drill_bot", "📢 DRILL SGT", "Motivation & discipline"),
            ("tech_bot", "🔧 TECH SPEC", "Technical assistance"),
            ("analyst_bot", "📊 ANALYST", "Market analysis"),
            ("mentor_bot", "🎓 MENTOR", "Educational guidance"),
            ("psych_bot", "🧠 PSYCHOLOGIST", "Mental game coach"),
            ("risk_bot", "⚖️ RISK OFFICER", "Risk management"),
            ("news_bot", "📰 NEWS DESK", "Market updates"),
            ("bit_companion", "🐱 BIT", "Chat with the legendary black cat"),
            ("norman_companion", "👦 NORMAN", "Chat with the 17-year-old founder"),
        ]

        for item_id, label, desc in bot_items:
            menu[f"bot_{item_id}"] = MenuItem(
                id=f"bot_{item_id}",
                label=label,
                icon=label.split()[0],
                category=MenuCategory.SPEAK_TO_BOT,
                parent="speak_to_bot",
                description=desc,
                action="bot_chat",
            )

        return menu

    def handle_intel_command(self, user_id: int, user_rank: UserRank) -> CommandResult:
        """Handle /intel command - show main menu"""
        keyboard = self._build_keyboard("main", user_rank)

        message = """🎯 **INTEL COMMAND CENTER**
*"Everything you need, Operative. No stone unturned."*

Welcome to your comprehensive command interface. Every question answered, every tool at your fingertips.

Select your intel category:"""

        return CommandResult(True, message, data={"reply_markup": keyboard})

    def handle_menu_callback(self, callback_data: str, user_id: int, user_rank: UserRank) -> Dict[str, Any]:
        """Handle menu navigation callbacks"""
        # Parse callback data: menu_{action}_{menu_id}
        parts = callback_data.split("_", 2)
        if len(parts) < 3 or parts[0] != "menu":
            return {"error": "Invalid callback data"}

        action = parts[1]
        menu_id = parts[2]

        if action == "nav":
            # Navigation to submenu
            return self._handle_navigation(menu_id, user_rank)
        elif action == "action":
            # Execute menu action
            return self._handle_action(menu_id, user_rank)
        elif action == "close":
            # Close menu
            return {"action": "delete_message"}

        return {"error": "Unknown action"}

    def _handle_navigation(self, menu_id: str, user_rank: UserRank) -> Dict[str, Any]:
        """Handle navigation to a submenu"""
        if menu_id not in self.menu_structure:
            return {"error": "Menu not found"}

        menu_item = self.menu_structure[menu_id]

        # Check tier requirements
        if menu_item.tier_required and user_rank.value < menu_item.tier_required.value:
            return {
                "action": "answer_callback",
                "text": f"🔒 {menu_item.tier_required.name} tier required",
                "show_alert": True,
            }

        # Build submenu message
        message = self._build_menu_message(menu_id, user_rank)
        keyboard = self._build_keyboard(menu_id, user_rank)

        return {"action": "edit_message", "text": message, "reply_markup": keyboard}

    def _handle_action(self, menu_id: str, user_rank: UserRank) -> Dict[str, Any]:
        """Handle menu item actions"""
        if menu_id not in self.menu_structure:
            return {"error": "Menu not found"}

        menu_item = self.menu_structure[menu_id]

        if menu_item.action == "webapp":
            # Open webapp with specific tool
            webapp_url = f"{self.webapp_url}/tools/{menu_id.replace('tool_', '')}"
            return {"action": "answer_callback", "text": "Opening tool in webapp...", "url": webapp_url}
        elif menu_item.action == "bot_chat":
            # Start chat with specific bot
            bot_name = menu_id.replace("bot_", "")
            return {
                "action": "send_message",
                "text": f"Connecting you to {menu_item.label}...\n\nType your question:",
                "data": {"bot": bot_name},
            }
        elif menu_item.action == "urgent":
            # Handle emergency actions
            return self._handle_emergency(menu_id)
        else:
            # Show detailed information
            return self._show_detailed_info(menu_id)

    def _build_keyboard(self, menu_id: str, user_rank: UserRank) -> InlineKeyboardMarkup:
        """Build inline keyboard for menu"""
        buttons = []

        # Get submenu items
        submenu_items = [item for item in self.menu_structure.values() if item.parent == menu_id]

        # Group items in rows of 2
        row = []
        for item in submenu_items:
            # Check tier requirements
            if item.tier_required and user_rank.value < item.tier_required.value:
                label = f"🔒 {item.label}"
            else:
                label = item.label

            callback_data = f"menu_nav_{item.id}"
            if item.action:
                callback_data = f"menu_action_{item.id}"

            row.append(InlineKeyboardButton(label, callback_data=callback_data))

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:  # Add remaining button
            buttons.append(row)

        # Add navigation buttons
        nav_row = []
        if menu_id != "main":
            parent = self.menu_structure[menu_id].parent
            nav_row.append(InlineKeyboardButton("◀️ BACK", callback_data=f"menu_nav_{parent}"))
        nav_row.append(InlineKeyboardButton("❌ CLOSE", callback_data="menu_close"))
        buttons.append(nav_row)

        return InlineKeyboardMarkup(buttons)

    def _build_menu_message(self, menu_id: str, user_rank: UserRank) -> str:
        """Build menu message with descriptions"""
        menu_item = self.menu_structure[menu_id]

        message = f"{menu_item.icon} **{menu_item.label}**\n"
        if menu_item.description:
            message += f"_{menu_item.description}_\n"

        message += "\n"

        # Add category-specific content
        if menu_id == "main":
            message += "Your tier: **" + user_rank.name + "**\n"
            message += "Select a category to explore:\n"
        elif menu_id == "tools":
            message += "🛠️ **Interactive Tools**\nCalculators and utilities for precision trading.\n"
        elif menu_id == "education":
            message += "🎓 **BITTEN War College**\nMaster the art of tactical trading.\n"
        elif menu_id == "emergency":
            message += "🚨 **EMERGENCY PROTOCOLS**\nImmediate assistance for critical situations.\n"

        return message

    def _get_quick_fire_info(self, menu_id: str) -> str:
        """Get quick fire specific information"""
        return f"""🎯 **QUICK FIRE: {menu_id.replace('quick_fire_', '').title()}**

⚡ **INSTANT EXECUTION**
• Pre-validated signal
• Optimized entry timing
• Auto risk management
• Fast deployment ready

Use: `/fire quick` for instant trades"""

    def _get_analysis_info(self, menu_id: str) -> str:
        """Get analysis specific information"""
        return f"""📊 **ANALYSIS: {menu_id.replace('analyze_', '').title()}**

🔍 **DETAILED BREAKDOWN**
• Market sentiment analysis
• Technical indicator signals
• Risk/reward calculations
• Entry/exit strategies

Use: `/analyze` for full report"""

    def _get_tier_info(self, menu_id: str) -> str:
        """Get tier specific information"""
        tier_name = menu_id.replace("tier_", "").upper()
        tier_info = {
            "NIBBLER": "🔰 Entry tier - $39/month\n• Manual fire mode\n• Basic signals\n• 6 trades/day",
            "FANG": "🦷 Advanced tier - $89/month\n• Manual + Chaingun\n• All signals\n• 10 trades/day",
            "COMMANDER": "⭐ Elite tier - $189/month\n• Auto + Semi modes\n• Advanced features\n• Unlimited trades\n• STEALTH mode",
            "": "🏔️ Ultimate tier - /month\n• All features unlocked\n• Unlimited trades\n• Exclusive signals",
        }
        return f"""💰 **{tier_name} TIER**

{tier_info.get(tier_name, 'Premium tier with advanced features')}

Upgrade: `/upgrade {tier_name.lower()}`"""

    def _get_tool_info(self, menu_id: str) -> str:
        """Get tool specific information"""
        tool_name = menu_id.replace("tool_", "").title()
        return f"""🛠️ **TOOL: {tool_name}**

🎯 **PRECISION UTILITY**
• Professional trading calculator
• Real-time market data
• Risk management helper
• Strategy optimization

Available in WebApp interface"""

    def _get_education_info(self, menu_id: str) -> str:
        """Get education specific information"""
        topic = menu_id.replace("education_", "").replace("_", " ").title()
        return f"""🎓 **TRAINING: {topic}**

📚 **TACTICAL EDUCATION**
• Step-by-step tutorials
• Interactive examples
• Practice scenarios
• Expert strategies

Access: `/learn {topic.lower()}`"""

    def _get_field_manual_info(self, menu_id: str) -> str:
        """Get field manual specific information"""
        manual_content = {
            "manual_getting_started": """🚀 **BOOT CAMP - Complete Beginner Guide**

**PHASE 1: ACCOUNT SETUP**
1. Sign up via Telegram (/start)
2. Choose your tier (Press Pass = FREE)
3. Access your trading dashboard
4. Complete profile setup

**PHASE 2: FIRST DEPLOYMENT**
1. Get familiar with webapp interface
2. Configure risk settings (start 1%)
3. Learn signal interpretation
4. Wait for first signal alert

**PHASE 3: LIVE COMBAT**
1. Execute your first trade via webapp
2. Monitor position in real-time
3. Upgrade to paid tier for more features
4. Scale up as you gain confidence

📖 **Next Steps**: Use /manual for full guide""",
            "manual_webapp_setup": """🌐 **WEBAPP ACCESS - Your Command Center**

**ACCESSING YOUR DASHBOARD**
• URL: https://joinbitten.com
• Login: Use your Telegram credentials
• Mobile: Works on all devices
• Desktop: Full-featured interface

**DASHBOARD OVERVIEW**
• Live Signals: Real-time trade alerts
• Position Manager: Active trades
• Analytics: Performance tracking
• Risk Settings: Personal preferences

**FIRST TIME SETUP**
1. Set risk tolerance (1-3%)
2. Choose notification preferences
3. Review tier features
4. Complete demo walkthrough

**TRADING INTERFACE**
• One-click trade execution
• Real-time P&L tracking
• Risk management tools
• Historical performance

✅ **Ready to Trade**: All via web browser""",
            "manual_first_trade": """🎯 **FIRST MISSION - Your Trading Debut**

**PRE-FLIGHT CHECKLIST**
□ Webapp dashboard accessible
□ Account verified and active
□ Demo balance available ($50k)
□ Risk set to 1% (conservative)

**MISSION EXECUTION**
1. **Wait for Signal**: Bot sends mission brief
2. **Review Intel**: Check TCS, R:R ratio
3. **Fire Command**: Click ⚡ QUICK FIRE or open webapp
4. **Monitor Position**: Track in real-time dashboard
5. **Mission Complete**: Auto-close at TP/SL

**FIRST TRADE REWARDS**
• +100 XP bonus
• "First Blood" achievement
• Unlocks advanced tutorials

🎮 **Pro Tip**: Start small, think big!""",
            "manual_reading_signals": """📖 **SIGNAL DECODE - Understanding Briefings**

**MISSION BRIEF STRUCTURE**
```
🎯 EURUSD BUY ASSAULT
TCS: 87% | R:R 1:2.5
Entry: 1.0850
SL: 1.0820 (30 pips)
TP: 1.0925 (75 pips)
```

**DECODING THE INTEL**
• **TCS (87%)**: Confidence level - higher = better
• **R:R 1:2.5**: Risk 1 to reward 2.5 ratio
• **Entry**: Exact price to enter trade
• **SL**: Stop Loss - max loss point
• **TP**: Take Profit - target exit

**PRIORITY LEVELS**
🔴 **HIGH**: Execute immediately
🟡 **MEDIUM**: Good opportunity
🟢 **LOW**: Optional/educational

**EXECUTION DECISION TREE**
• TCS 80%+: Strong execute
• TCS 60-79%: Careful execute
• TCS <60%: Consider skipping

📊 **Advanced**: Use /analyze for deeper intel""",
        }

        return manual_content.get(
            menu_id,
            f"""📚 **FIELD MANUAL: {menu_id.replace('manual_', '').replace('_', ' ').title()}**

📖 **TACTICAL GUIDE**
Comprehensive documentation for this topic.
Access full manual via webapp.

🔗 **Quick Access**: Use /manual {menu_id.replace('manual_', '')}""",
        )

    def _get_analytics_info(self, menu_id: str) -> str:
        """Get analytics/battle stats information"""
        analytics_content = {
            "analytics_performance_stats": """📊 **PERFORMANCE DASHBOARD**

**CURRENT STATS** (Last 30 days)
• Total Trades: 47
• Win Rate: 74.5%
• Net Profit: +$1,247.50
• Max Drawdown: -3.2%
• Average R:R: 1:2.1

**RANK PROGRESSION**
Current: 🦷 FANG Operative
Next: ⭐ COMMANDER (Need 15 more wins)
XP: 12,450 / 15,000

**RECENT PERFORMANCE**
This Week: +$284 (6W-2L)
Last Week: +$419 (8W-1L)
Best Day: +$156 (3W-0L)

📈 **Trend**: Improving consistency
🎯 **Focus**: Risk management excellence""",
            "analytics_win_rate": """🎯 **WIN RATE ANALYSIS**

**OVERALL STATISTICS**
• All-Time Win Rate: 78.3%
• Last 100 Trades: 82.0%
• Current Streak: 7 wins
• Best Streak: 15 wins
• Recovery Rate: 91% (wins after loss)

**WIN RATE BY TIMEFRAME**
• Daily: 76% (short-term consistency)
• Weekly: 85% (strong weekly performance)
• Monthly: 78% (stable long-term)

**WIN RATE BY PAIR**
🥇 GBPUSD: 89% (23/26 trades)
🥈 EURUSD: 84% (31/37 trades)
🥉 USDJPY: 71% (22/31 trades)

**IMPROVEMENT AREAS**
• News trading: 62% win rate
• Asian session: 68% win rate

🎯 **Target**: Maintain 80%+ consistency""",
            "analytics_best_pairs": """💱 **BEST PERFORMING PAIRS**

**TOP PERFORMERS** (P&L)
🥇 **GBPUSD**: +$2,847 (89% WR)
   • Average: +$124 per win
   • Best Trade: +$312
   • Risk Score: A+

🥈 **EURUSD**: +$1,923 (84% WR)
   • Average: +$86 per win
   • Best Trade: +$245
   • Risk Score: A

🥉 **USDJPY**: +$1,456 (71% WR)
   • Average: +$98 per win
   • Best Trade: +$289
   • Risk Score: B+

**STRATEGY INSIGHTS**
• Focus more on GBPUSD/EURUSD
• Strong European session performance
• Excellent trend-following results

🎯 **Recommendation**: Increase allocation to top 2 pairs""",
            "analytics_time_analysis": """⏰ **OPTIMAL TRADING TIMES**

**BEST SESSIONS** (Profitability)
🥇 **London Session** (8-12 GMT)
   • Win Rate: 89%
   • Avg Profit: +$127/trade
   • Best Pairs: GBPUSD, EURGBP

🥈 **NY Session** (13-17 GMT)
   • Win Rate: 82%
   • Avg Profit: +$98/trade
   • Best Pairs: EURUSD, USDJPY

🥉 **Overlap** (12-15 GMT)
   • Win Rate: 94%
   • Avg Profit: +$156/trade
   • High volatility period

**AVOID THESE TIMES**
❌ Asian Session (21-05 GMT): 64% WR
❌ Sunday Open (21-23 GMT): 43% WR
❌ Friday Close (20-22 GMT): 58% WR

⏰ **Optimal Window**: 08:00-17:00 GMT
🎯 **Peak Performance**: 12:00-15:00 GMT""",
            "analytics_monthly_report": """📅 **MONTHLY PERFORMANCE REPORT**

**CURRENT MONTH SUMMARY**
📊 **Trades**: 28 executed
🎯 **Win Rate**: 82.1% (23W-5L)
💰 **Net P&L**: +$1,847.50
📈 **ROI**: +18.5%
📉 **Max DD**: -2.1%

**WEEKLY BREAKDOWN**
Week 1: +$524 (7W-1L)
Week 2: +$389 (6W-2L)
Week 3: +$672 (8W-0L) ⭐
Week 4: +$262 (2W-2L)

**TOP ACHIEVEMENTS**
🏆 Best Week: +$672 (Week 3)
🎯 Perfect Week: 8W-0L streak
💎 Biggest Win: +$184 (GBPUSD)
🛡️ Risk Control: Max 2.1% DD

**GOALS vs ACTUAL**
Target Win Rate: 75% ✅ (82.1%)
Target ROI: 15% ✅ (18.5%)
Target Max DD: <5% ✅ (-2.1%)

📈 **Next Month Target**: +20% ROI""",
        }

        return analytics_content.get(
            menu_id,
            f"""📊 **ANALYTICS: {menu_id.replace('analytics_', '').replace('_', ' ').title()}**

📈 **BATTLE STATISTICS**
Detailed performance metrics and analysis.
Full dashboard available in webapp.

📊 **Quick View**: Use /stats {menu_id.replace('analytics_', '')}""",
        )

    def _get_comprehensive_menu_info(self, menu_id: str) -> str:
        """Get comprehensive information for any menu item"""
        if "manual_" in menu_id:
            return self._get_field_manual_info(menu_id)
        elif "analytics_" in menu_id:
            return self._get_analytics_info(menu_id)
        elif "tool_" in menu_id:
            return self._get_tool_info(menu_id)
        elif "education_" in menu_id or "edu_" in menu_id:
            return self._get_education_info(menu_id)
        elif "tier_" in menu_id:
            return self._get_tier_info(menu_id)
        elif "quick_fire" in menu_id:
            return self._get_quick_fire_info(menu_id)
        elif "analyze" in menu_id:
            return self._get_analysis_info(menu_id)
        else:
            return f"📋 **{menu_id.replace('_', ' ').title()}**\n\nFunctionality available via webapp and commands."

    def _show_detailed_info(self, menu_id: str) -> Dict[str, Any]:
        """Show detailed information for a menu item"""
        info_map = {
            "combat_fire_modes": """🎯 **FIRE MODES EXPLAINED**

**BIT MODE** (Default)
• Conservative approach
• Lower risk per trade
• Ideal for building consistency
• Perfect for new operatives

**COMMANDER MODE** (Advanced)
• Aggressive positioning
• Higher risk tolerance
• For experienced traders
• Requires proven track record

Switch modes with: `/mode [bit/commander]`""",
            "manual_getting_started": """🚀 **BOOT CAMP - Getting Started**

**Step 1: Connect MT5**
• Download MetaTrader 5
• Use provided broker link
• Enter your credentials
• Add BITTEN EA to chart

**Step 2: Configure Bot**
• Set your risk preference
• Choose notification settings
• Test with demo account first

**Step 3: First Trade**
• Wait for signal alert
• Review mission briefing
• Execute via /fire command
• Monitor via /positions

*Remember: Start small, grow steady*""",
            "tool_compound_calc": """📊 **COMPOUND CALCULATOR**

Calculate your potential growth:
• Starting capital
• Monthly return %
• Time period
• Compound frequency

**Example:**
$1,000 start
10% monthly
12 months
= $3,138 (213% gain)

[OPEN CALCULATOR] - Tap to use webapp tool""",
        }

        # Add more comprehensive info mappings
        if menu_id not in info_map:
            # Use comprehensive function for all menu items
            content = self._get_comprehensive_menu_info(menu_id)
        else:
            content = info_map[menu_id]

        # For long content, send as a message instead of callback answer
        if len(content) > 200:
            return {"action": "send_message", "text": content, "parse_mode": "Markdown"}
        else:
            return {"action": "answer_callback", "text": content, "show_alert": True}

    def _handle_emergency(self, menu_id: str, user_id: int = None) -> Dict[str, Any]:
        """Handle emergency menu items with immediate actions"""
        from .user_emergency_stop import UserEmergencyLevel, user_emergency_controller

        # User-specific emergency stops
        if menu_id == "emergency_stop_pause":
            if not user_id:
                return {"action": "send_message", "text": "❌ User ID required for emergency stop"}

            result = user_emergency_controller.request_emergency_stop(
                user_id=user_id, level=UserEmergencyLevel.PAUSE_NEW, reason="User requested pause new trades"
            )

            return {
                "action": "send_confirmation",
                "text": result["message"],
                "requires_confirmation": result.get("requires_confirmation", False),
                "buttons": result.get("buttons", []),
            }

        elif menu_id == "emergency_stop_close_all":
            if not user_id:
                return {"action": "send_message", "text": "❌ User ID required for emergency stop"}

            result = user_emergency_controller.request_emergency_stop(
                user_id=user_id, level=UserEmergencyLevel.CLOSE_ALL, reason="User requested close all positions"
            )

            return {
                "action": "send_confirmation",
                "text": result["message"],
                "requires_confirmation": result.get("requires_confirmation", False),
                "buttons": result.get("buttons", []),
            }

        elif menu_id == "emergency_account_lock":
            if not user_id:
                return {"action": "send_message", "text": "❌ User ID required for emergency stop"}

            result = user_emergency_controller.request_emergency_stop(
                user_id=user_id, level=UserEmergencyLevel.ACCOUNT_LOCK, reason="User requested complete account lockout"
            )

            return {
                "action": "send_confirmation",
                "text": result["message"],
                "requires_confirmation": result.get("requires_confirmation", False),
                "buttons": result.get("buttons", []),
            }

        # Other emergency responses
        emergency_responses = {
            "emergency_trade_stuck": {
                "message": """🚨 **TRADE STUCK - EMERGENCY PROTOCOL**

1. **Stay Calm** - Don't panic close
2. **Check MT5** - Is platform connected?
3. **Try Manual Close** - Use MT5 directly
4. **Force Close** - Right-click > Close position
5. **Contact Broker** - If still stuck

**Prevention:**
• Always set stop loss
• Monitor connection status
• Keep broker support handy""",
                "action": "send_support_ticket",
            },
            "emergency_massive_loss": {
                "message": """💔 **RECOVERY PROTOCOL ACTIVATED**

**Immediate Actions:**
1. STOP trading for 24 hours
2. Do NOT revenge trade
3. Review what went wrong
4. Speak to MedicBot for support

**Recovery Steps:**
• Reduce position size by 50%
• Focus on high-probability setups only
• Rebuild slowly and steadily
• Consider dropping to lower tier temporarily

*Remember: Every elite trader has been here*""",
                "action": "activate_recovery_mode",
            },
        }

        response = emergency_responses.get(
            menu_id, {"message": "Emergency assistance requested", "action": "contact_support"}
        )

        return {"action": "send_message", "text": response["message"], "data": {"emergency": response["action"]}}

    def get_contextual_help(self, context: str, user_rank: UserRank) -> str:
        """Get context-sensitive help suggestions"""
        # Provide smart suggestions based on user's current context
        suggestions = {
            "new_user": [
                ("manual_getting_started", "🚀 Start Here"),
                ("manual_mt5_setup", "🔌 Connect MT5"),
                ("tier_nibbler_tier", "🐭 Your Tier Benefits"),
            ],
            "after_loss": [
                ("emergency_massive_loss", "💔 Recovery Protocol"),
                ("bot_medic_bot", "💊 Talk to Medic"),
                ("edu_risk_management_edu", "🛡️ Risk Management"),
            ],
            "high_performer": [
                ("tier_upgrade_now", "⬆️ Upgrade Tier"),
                ("xp_prestige_system", "⭐ Prestige Info"),
                ("analytics_performance_stats", "📊 Your Stats"),
            ],
        }

        return suggestions.get(context, [])

    def check_secret_phrase(self, user_input: str) -> Optional[str]:
        """Check if user entered a secret phrase"""
        user_input = user_input.lower().strip()
        return self.easter_eggs["secret_combos"].get(user_input)

    def handle_easter_egg(self, egg_type: str, user_id: str) -> Dict[str, Any]:
        """Handle easter egg activation"""
        import random

        responses = {
            "profit_vault": {
                "message": "💰 **SECRET PROFIT VAULT UNLOCKED**\n\n"
                "🎯 Secret #1: The house always wins... we just make you feel like you're the house\n"
                "💎 Secret #2: Diamond hands are just paper hands that forgot how to sell\n"
                "🚀 Secret #3: Moon is actually just the friends we liquidated along the way\n"
                "🤫 Secret #4: The real profit was inside you all along (kidding, it's in our wallet)",
                "type": "secret_vault",
            },
            "cat_companion_mode": {"message": random.choice(self.easter_eggs["bit_quotes"]), "type": "bit_interaction"},
            "hodl_therapy": {
                "message": "💎 **HODL THERAPY SESSION ACTIVATED**\n\n"
                "🎭 Welcome to Diamond Hands Anonymous\n"
                "📝 Step 1: Admit you have a problem with selling\n"
                "💪 Step 2: Believe that diamond hands can restore you to profitability\n"
                "🙏 Step 3: Turn your portfolio over to the care of the HODL gods\n\n"
                "*Remember: Paper hands were made for toilet, not trading*",
                "type": "therapy_session",
            },
            "lambo_calculator": {
                "message": "🏎️ **WEN LAMBO CALCULATOR**\n\n"
                "💰 Current Balance: $420.69\n"
                "🎯 Lambo Price: $200,000\n"
                "📈 Required Gain: 47,519%\n"
                "⏰ Time to Lambo: 69,420 years\n\n"
                "*Alternative: Buy Honda Civic now, pretend it's Lambo*",
                "type": "calculator",
            },
            "hopium_injection": {
                "message": "📈 **HOPIUM INJECTION ADMINISTERED**\n\n"
                "🚀 NUMBER WILL GO UP\n"
                "💎 DIAMOND HANDS ACTIVATED\n"
                "🌙 MOON MISSION ENGAGED\n"
                "🦍 APE MODE: ENABLED\n\n"
                "*Side effects may include: unrealistic expectations, FOMO, and lambo dreams*",
                "type": "hopium_dose",
            },
            "dev_secrets": {
                "message": "👨‍💻 **DEVELOPER SECRETS UNLOCKED**\n\n"
                "🐛 Bug Report: User has too much time on their hands\n"
                "💡 Feature Idea: Auto-delete account when they find easter eggs\n"
                "🤫 Insider Info: The algorithm is just Norman walking across the keyboard\n"
                "☕ Truth: 90% of trading success is just good coffee",
                "type": "dev_vault",
            },
        }

        return responses.get(
            egg_type, {"message": "🎮 Easter egg found! You're more curious than profitable!", "type": "generic"}
        )

    def add_seasonal_content(self, current_menu: Dict) -> Dict:
        """Add seasonal easter eggs based on current date"""
        from datetime import datetime

        now = datetime.now()

        # Christmas season (December)
        if now.month == 12:
            current_menu["seasonal_christmas"] = MenuItem(
                id="seasonal_christmas",
                label="🎄 SANTA RALLY",
                icon="🎄",
                category=MenuCategory.EMERGENCY,
                parent="emergency",
                description="Ho ho ho-ly gains!",
                action="seasonal",
            )

        # April Fools (April 1st)
        if now.month == 4 and now.day == 1:
            current_menu["seasonal_april_fools"] = MenuItem(
                id="seasonal_april_fools",
                label="😜 TRUST NO ONE",
                icon="😜",
                category=MenuCategory.EMERGENCY,
                parent="emergency",
                description="Especially your indicators today",
                action="chaos",
            )

        return current_menu


# Global instance
intel_center = IntelCommandCenter()


# Helper functions for integration
def handle_intel_command(user_id: int, user_rank: UserRank) -> CommandResult:
    """Handle /intel command"""
    return intel_center.handle_intel_command(user_id, user_rank)


def handle_intel_callback(callback_data: str, user_id: int, user_rank: UserRank) -> Dict[str, Any]:
    """Handle intel menu callbacks"""
    return intel_center.handle_menu_callback(callback_data, user_id, user_rank)
