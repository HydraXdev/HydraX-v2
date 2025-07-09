"""
BITTEN Intel Command Center
Comprehensive dropdown menu system for all user needs
White-glove concierge service with military precision
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

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
        
    def _build_menu_structure(self) -> Dict[str, MenuItem]:
        """Build the complete menu structure"""
        menu = {}
        
        # MAIN MENU
        menu['main'] = MenuItem(
            id='main',
            label='INTEL COMMAND CENTER',
            icon='🎯',
            category=MenuCategory.MAIN,
            description='"Everything you need, Operative. No stone unturned."'
        )
        
        # Level 1: Main Categories
        main_categories = [
            ('combat_ops', '🔫 COMBAT OPS', 'Trading operations & execution'),
            ('field_manual', '📚 FIELD MANUAL', 'Complete guides & tutorials'),
            ('tier_intel', '💰 TIER INTEL', 'Subscription tiers & benefits'),
            ('xp_economy', '🎖️ XP ECONOMY', 'Rewards, shop & prestige'),
            ('education', '🎓 WAR COLLEGE', 'Trading education & theory'),
            ('tools', '🛠️ TACTICAL TOOLS', 'Calculators & utilities'),
            ('analytics', '📊 BATTLE STATS', 'Performance & analytics'),
            ('account', '👤 ACCOUNT OPS', 'Settings & preferences'),
            ('community', '👥 SQUAD HQ', 'Community & social'),
            ('tech_support', '🔧 TECH SUPPORT', 'Issues & troubleshooting'),
            ('emergency', '🚨 EMERGENCY', 'Urgent assistance'),
            ('speak_to_bot', '🤖 BOT CONCIERGE', 'AI assistants')
        ]
        
        for cat_id, label, desc in main_categories:
            menu[cat_id] = MenuItem(
                id=cat_id,
                label=label,
                icon=label.split()[0],
                category=MenuCategory.MAIN,
                parent='main',
                description=desc
            )
        
        # COMBAT OPS Submenu
        combat_items = [
            ('fire_modes', '🎯 FIRE MODES', 'BIT vs COMMANDER explained'),
            ('signal_types', '📡 SIGNAL TYPES', 'Arcade, Sniper, Special ops'),
            ('risk_management', '⚖️ RISK MANAGEMENT', 'Risk modes & cooldowns'),
            ('trade_execution', '🔫 TRADE EXECUTION', 'How to fire positions'),
            ('position_management', '📋 POSITION MGMT', 'Manage open trades'),
            ('trading_hours', '⏰ TRADING HOURS', 'Best times to trade'),
            ('currency_pairs', '💱 CURRENCY INTEL', 'Pair characteristics'),
            ('entry_types', '🎪 ENTRY TYPES', 'Market vs pending orders'),
            ('exit_strategies', '🚪 EXIT STRATEGIES', 'TP, SL, partials'),
            ('news_trading', '📰 NEWS WARFARE', 'Trading around events')
        ]
        
        for item_id, label, desc in combat_items:
            menu[f'combat_{item_id}'] = MenuItem(
                id=f'combat_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.COMBAT_OPS,
                parent='combat_ops',
                description=desc
            )
        
        # FIELD MANUAL Submenu
        manual_items = [
            ('getting_started', '🚀 BOOT CAMP', 'Complete beginner guide'),
            ('mt5_setup', '🔌 MT5 SETUP', 'Step-by-step connection'),
            ('first_trade', '🎯 FIRST MISSION', 'Your first trade walkthrough'),
            ('reading_signals', '📖 SIGNAL DECODE', 'Understanding briefings'),
            ('risk_sizing', '📏 POSITION SIZING', 'Calculate lot sizes'),
            ('psychology', '🧠 MENTAL WARFARE', 'Trading psychology'),
            ('mistakes', '❌ COMMON ERRORS', 'Avoid these mistakes'),
            ('glossary', '📖 COMBAT GLOSSARY', 'Trading terms explained'),
            ('faqs', '❓ FIELD FAQS', 'Frequently asked questions'),
            ('video_guides', '🎥 VIDEO BRIEFS', 'Visual tutorials')
        ]
        
        for item_id, label, desc in manual_items:
            menu[f'manual_{item_id}'] = MenuItem(
                id=f'manual_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.FIELD_MANUAL,
                parent='field_manual',
                description=desc
            )
        
        # TIER INTEL Submenu
        tier_items = [
            ('nibbler_tier', '🐭 NIBBLER ($39)', 'Entry tier features'),
            ('fang_tier', '🦷 FANG ($89)', 'Advanced features'),
            ('commander_tier', '⭐ COMMANDER ($139)', 'Elite access'),
            ('apex_tier', '👑 APEX ($188)', 'Maximum power'),
            ('compare_tiers', '📊 COMPARE TIERS', 'Side-by-side comparison'),
            ('upgrade_now', '⬆️ UPGRADE NOW', 'Instant tier upgrade'),
            ('downgrade_info', '⬇️ DOWNGRADE INFO', 'How downgrades work'),
            ('trial_info', '🎁 TRIAL OPTIONS', 'Test drive higher tiers'),
            ('payment_methods', '💳 PAYMENT OPS', 'Accepted payments'),
            ('refund_policy', '↩️ REFUND INTEL', 'Money-back terms')
        ]
        
        for item_id, label, desc in tier_items:
            menu[f'tier_{item_id}'] = MenuItem(
                id=f'tier_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TIER_INTEL,
                parent='tier_intel',
                description=desc
            )
        
        # XP ECONOMY Submenu
        xp_items = [
            ('earning_xp', '💰 EARNING XP', 'All ways to gain XP'),
            ('xp_shop', '🛍️ XP SHOP', 'Spend your XP points'),
            ('prestige_system', '⭐ PRESTIGE OPS', '50k XP reset benefits'),
            ('daily_challenges', '📅 DAILY MISSIONS', 'Today\'s challenges'),
            ('weekly_events', '🎪 WEEKLY EVENTS', 'Special XP events'),
            ('xp_multipliers', '🔥 XP BOOSTERS', 'Multiply your gains'),
            ('leaderboards', '🏆 LEADERBOARDS', 'Top operatives'),
            ('xp_history', '📜 XP LEDGER', 'Your XP transactions'),
            ('medals_showcase', '🎖️ MEDAL RACK', 'Your achievements'),
            ('referral_program', '👥 RECRUIT REWARDS', 'Earn by recruiting')
        ]
        
        for item_id, label, desc in xp_items:
            menu[f'xp_{item_id}'] = MenuItem(
                id=f'xp_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.XP_ECONOMY,
                parent='xp_economy',
                description=desc
            )
        
        # EDUCATION (War College) Submenu
        education_items = [
            ('forex_basics', '📚 FOREX 101', 'Currency market basics'),
            ('technical_analysis', '📈 TECH ANALYSIS', 'Charts & indicators'),
            ('fundamental_analysis', '🌍 FUNDAMENTALS', 'Economic factors'),
            ('risk_management_edu', '🛡️ RISK DOCTRINE', 'Protect your capital'),
            ('trading_strategies', '🎯 BATTLE TACTICS', 'Proven strategies'),
            ('market_psychology', '🧠 MARKET PSYCH', 'Crowd behavior'),
            ('economic_calendar', '📅 ECON CALENDAR', 'Important events'),
            ('recommended_books', '📚 READING LIST', 'Essential books'),
            ('webinar_schedule', '🎓 LIVE TRAINING', 'Upcoming webinars'),
            ('quiz_challenges', '🎮 KNOWLEDGE TEST', 'Test your skills')
        ]
        
        for item_id, label, desc in education_items:
            menu[f'edu_{item_id}'] = MenuItem(
                id=f'edu_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.EDUCATION,
                parent='education',
                description=desc
            )
        
        # TOOLS Submenu
        tools_items = [
            ('compound_calc', '📊 COMPOUND CALC', 'Growth projections'),
            ('position_calc', '🧮 LOT SIZE CALC', 'Perfect position sizing'),
            ('risk_calc', '⚖️ RISK CALCULATOR', 'Risk/reward ratios'),
            ('pip_calc', '💰 PIP CALCULATOR', 'Pip values by pair'),
            ('profit_calc', '💵 PROFIT CALC', 'Potential profits'),
            ('drawdown_calc', '📉 DRAWDOWN CALC', 'Max loss scenarios'),
            ('margin_calc', '🏦 MARGIN CALC', 'Required margin'),
            ('correlation_tool', '🔗 CORRELATION', 'Pair correlations'),
            ('timezone_convert', '🌍 TIME ZONES', 'Market sessions'),
            ('trade_journal', '📔 TRADE JOURNAL', 'Track your trades')
        ]
        
        for item_id, label, desc in tools_items:
            menu[f'tool_{item_id}'] = MenuItem(
                id=f'tool_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TOOLS,
                parent='tools',
                description=desc,
                action='webapp'  # Most tools open webapp
            )
        
        # ANALYTICS Submenu
        analytics_items = [
            ('performance_stats', '📊 PERFORMANCE', 'Your trading stats'),
            ('win_rate', '🎯 WIN RATE', 'Success metrics'),
            ('profit_curve', '📈 PROFIT CURVE', 'Equity growth'),
            ('best_pairs', '💱 BEST PAIRS', 'Your profitable pairs'),
            ('worst_pairs', '❌ WORST PAIRS', 'Pairs to avoid'),
            ('time_analysis', '⏰ TIME ANALYSIS', 'Best trading times'),
            ('streak_analysis', '🔥 STREAK DATA', 'Win/loss streaks'),
            ('monthly_report', '📅 MONTHLY REPORT', 'Detailed breakdown'),
            ('compare_period', '📊 COMPARE PERIODS', 'Progress over time'),
            ('export_data', '💾 EXPORT DATA', 'Download your stats')
        ]
        
        for item_id, label, desc in analytics_items:
            menu[f'analytics_{item_id}'] = MenuItem(
                id=f'analytics_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.ANALYTICS,
                parent='analytics',
                description=desc
            )
        
        # ACCOUNT OPS Submenu
        account_items = [
            ('profile_settings', '👤 PROFILE', 'Your operative profile'),
            ('notification_prefs', '🔔 NOTIFICATIONS', 'Alert preferences'),
            ('sound_settings', '🔊 SOUND CONFIG', 'Audio preferences'),
            ('display_settings', '🖥️ DISPLAY', 'UI preferences'),
            ('security_settings', '🔐 SECURITY', '2FA & passwords'),
            ('api_keys', '🔑 API KEYS', 'MT5 connections'),
            ('billing_info', '💳 BILLING', 'Payment methods'),
            ('subscription_mgmt', '📋 SUBSCRIPTION', 'Manage your tier'),
            ('data_privacy', '🔒 PRIVACY', 'Data settings'),
            ('delete_account', '❌ DEACTIVATE', 'Account removal')
        ]
        
        for item_id, label, desc in account_items:
            menu[f'account_{item_id}'] = MenuItem(
                id=f'account_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.ACCOUNT,
                parent='account',
                description=desc
            )
        
        # COMMUNITY Submenu
        community_items = [
            ('squad_chat', '💬 SQUAD CHAT', 'Team communication'),
            ('find_squad', '🔍 FIND SQUAD', 'Join a team'),
            ('create_squad', '➕ CREATE SQUAD', 'Start your team'),
            ('squad_leaderboard', '🏆 SQUAD RANKS', 'Top teams'),
            ('mentorship', '🎓 MENTORSHIP', 'Learn from elites'),
            ('share_trades', '📤 SHARE WINS', 'Brag about profits'),
            ('follow_elites', '👁️ FOLLOW ELITES', 'Watch top traders'),
            ('forums', '💭 WAR ROOM', 'Discussion forums'),
            ('events_calendar', '📅 EVENTS', 'Community events'),
            ('referral_center', '🎁 REFERRAL HQ', 'Invite & earn')
        ]
        
        for item_id, label, desc in community_items:
            menu[f'community_{item_id}'] = MenuItem(
                id=f'community_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.COMMUNITY,
                parent='community',
                description=desc
            )
        
        # TECH SUPPORT Submenu
        support_items = [
            ('connection_issues', '🔌 CONNECTION', 'MT5 connection help'),
            ('trade_failures', '❌ TRADE FAILS', 'Why trades fail'),
            ('login_problems', '🔐 LOGIN ISSUES', 'Access problems'),
            ('subscription_issues', '💳 BILLING HELP', 'Payment problems'),
            ('signal_issues', '📡 SIGNAL ISSUES', 'Not receiving signals'),
            ('webapp_problems', '🌐 WEBAPP BUGS', 'Interface issues'),
            ('mobile_issues', '📱 MOBILE HELP', 'Phone app issues'),
            ('api_errors', '⚠️ API ERRORS', 'Technical errors'),
            ('report_bug', '🐛 REPORT BUG', 'Submit bug report'),
            ('feature_request', '💡 SUGGESTIONS', 'Request features')
        ]
        
        for item_id, label, desc in support_items:
            menu[f'support_{item_id}'] = MenuItem(
                id=f'support_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.TECH_SUPPORT,
                parent='tech_support',
                description=desc
            )
        
        # EMERGENCY Submenu
        emergency_items = [
            ('trade_stuck', '🚨 TRADE STUCK', 'Position won\'t close'),
            ('massive_loss', '💔 BIG LOSS', 'Recovery protocol'),
            ('account_blown', '💥 ACCOUNT BLOWN', 'What to do now'),
            ('cant_login', '🔒 LOCKED OUT', 'Emergency access'),
            ('wrong_size', '⚠️ WRONG SIZE', 'Traded too big'),
            ('margin_call', '📞 MARGIN CALL', 'Urgent help'),
            ('hacked_account', '🔓 HACKED', 'Security breach'),
            ('payment_failed', '❌ PAYMENT FAIL', 'Subscription lapsed'),
            ('mental_crisis', '🧠 NEED HELP', 'Trading psychology'),
            ('contact_human', '👤 HUMAN HELP', 'Speak to support')
        ]
        
        for item_id, label, desc in emergency_items:
            menu[f'emergency_{item_id}'] = MenuItem(
                id=f'emergency_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.EMERGENCY,
                parent='emergency',
                description=desc,
                action='urgent'
            )
        
        # BOT CONCIERGE Submenu
        bot_items = [
            ('overwatch_bot', '🎖️ OVERWATCH', 'Strategic guidance'),
            ('medic_bot', '💊 MEDIC', 'Recovery & support'),
            ('drill_bot', '📢 DRILL SGT', 'Motivation & discipline'),
            ('tech_bot', '🔧 TECH SPEC', 'Technical assistance'),
            ('analyst_bot', '📊 ANALYST', 'Market analysis'),
            ('mentor_bot', '🎓 MENTOR', 'Educational guidance'),
            ('psych_bot', '🧠 PSYCHOLOGIST', 'Mental game coach'),
            ('risk_bot', '⚖️ RISK OFFICER', 'Risk management'),
            ('news_bot', '📰 NEWS DESK', 'Market updates'),
            ('bit_companion', '🤖 BIT', 'Your AI companion')
        ]
        
        for item_id, label, desc in bot_items:
            menu[f'bot_{item_id}'] = MenuItem(
                id=f'bot_{item_id}',
                label=label,
                icon=label.split()[0],
                category=MenuCategory.SPEAK_TO_BOT,
                parent='speak_to_bot',
                description=desc,
                action='bot_chat'
            )
        
        return menu
    
    def handle_intel_command(self, user_id: int, user_rank: UserRank) -> CommandResult:
        """Handle /intel command - show main menu"""
        keyboard = self._build_keyboard('main', user_rank)
        
        message = """🎯 **INTEL COMMAND CENTER**
*"Everything you need, Operative. No stone unturned."*

Welcome to your comprehensive command interface. Every question answered, every tool at your fingertips. 

Select your intel category:"""
        
        return CommandResult(
            True,
            message,
            data={'reply_markup': keyboard}
        )
    
    def handle_menu_callback(self, callback_data: str, user_id: int, user_rank: UserRank) -> Dict[str, Any]:
        """Handle menu navigation callbacks"""
        # Parse callback data: menu_{action}_{menu_id}
        parts = callback_data.split('_', 2)
        if len(parts) < 3 or parts[0] != 'menu':
            return {'error': 'Invalid callback data'}
        
        action = parts[1]
        menu_id = parts[2]
        
        if action == 'nav':
            # Navigation to submenu
            return self._handle_navigation(menu_id, user_rank)
        elif action == 'action':
            # Execute menu action
            return self._handle_action(menu_id, user_rank)
        elif action == 'close':
            # Close menu
            return {'action': 'delete_message'}
        
        return {'error': 'Unknown action'}
    
    def _handle_navigation(self, menu_id: str, user_rank: UserRank) -> Dict[str, Any]:
        """Handle navigation to a submenu"""
        if menu_id not in self.menu_structure:
            return {'error': 'Menu not found'}
        
        menu_item = self.menu_structure[menu_id]
        
        # Check tier requirements
        if menu_item.tier_required and user_rank.value < menu_item.tier_required.value:
            return {
                'action': 'answer_callback',
                'text': f"🔒 {menu_item.tier_required.name} tier required",
                'show_alert': True
            }
        
        # Build submenu message
        message = self._build_menu_message(menu_id, user_rank)
        keyboard = self._build_keyboard(menu_id, user_rank)
        
        return {
            'action': 'edit_message',
            'text': message,
            'reply_markup': keyboard
        }
    
    def _handle_action(self, menu_id: str, user_rank: UserRank) -> Dict[str, Any]:
        """Handle menu item actions"""
        if menu_id not in self.menu_structure:
            return {'error': 'Menu not found'}
        
        menu_item = self.menu_structure[menu_id]
        
        if menu_item.action == 'webapp':
            # Open webapp with specific tool
            webapp_url = f"{self.webapp_url}/tools/{menu_id.replace('tool_', '')}"
            return {
                'action': 'answer_callback',
                'text': 'Opening tool in webapp...',
                'url': webapp_url
            }
        elif menu_item.action == 'bot_chat':
            # Start chat with specific bot
            bot_name = menu_id.replace('bot_', '')
            return {
                'action': 'send_message',
                'text': f"Connecting you to {menu_item.label}...\n\nType your question:",
                'data': {'bot': bot_name}
            }
        elif menu_item.action == 'urgent':
            # Handle emergency actions
            return self._handle_emergency(menu_id)
        else:
            # Show detailed information
            return self._show_detailed_info(menu_id)
    
    def _build_keyboard(self, menu_id: str, user_rank: UserRank) -> InlineKeyboardMarkup:
        """Build inline keyboard for menu"""
        buttons = []
        
        # Get submenu items
        submenu_items = [
            item for item in self.menu_structure.values()
            if item.parent == menu_id
        ]
        
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
        if menu_id != 'main':
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
        if menu_id == 'main':
            message += "Your tier: **" + user_rank.name + "**\n"
            message += "Select a category to explore:\n"
        elif menu_id == 'tools':
            message += "🛠️ **Interactive Tools**\nCalculators and utilities for precision trading.\n"
        elif menu_id == 'education':
            message += "🎓 **BITTEN War College**\nMaster the art of tactical trading.\n"
        elif menu_id == 'emergency':
            message += "🚨 **EMERGENCY PROTOCOLS**\nImmediate assistance for critical situations.\n"
        
        return message
    
    def _show_detailed_info(self, menu_id: str) -> Dict[str, Any]:
        """Show detailed information for a menu item"""
        # This would fetch detailed content based on menu_id
        # For now, return a placeholder
        info_map = {
            'combat_fire_modes': """🎯 **FIRE MODES EXPLAINED**

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
            
            'manual_getting_started': """🚀 **BOOT CAMP - Getting Started**

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
            
            'tool_compound_calc': """📊 **COMPOUND CALCULATOR**

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
        
        content = info_map.get(menu_id, f"Detailed information for {menu_id}")
        
        return {
            'action': 'answer_callback',
            'text': content[:200],  # Telegram callback answer limit
            'show_alert': True
        }
    
    def _handle_emergency(self, menu_id: str) -> Dict[str, Any]:
        """Handle emergency menu items with immediate actions"""
        emergency_responses = {
            'emergency_trade_stuck': {
                'message': """🚨 **TRADE STUCK - EMERGENCY PROTOCOL**

1. **Stay Calm** - Don't panic close
2. **Check MT5** - Is platform connected?
3. **Try Manual Close** - Use MT5 directly
4. **Force Close** - Right-click > Close position
5. **Contact Broker** - If still stuck

**Prevention:**
• Always set stop loss
• Monitor connection status
• Keep broker support handy""",
                'action': 'send_support_ticket'
            },
            'emergency_massive_loss': {
                'message': """💔 **RECOVERY PROTOCOL ACTIVATED**

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
                'action': 'activate_recovery_mode'
            },
        }
        
        response = emergency_responses.get(menu_id, {
            'message': 'Emergency assistance requested',
            'action': 'contact_support'
        })
        
        return {
            'action': 'send_message',
            'text': response['message'],
            'data': {'emergency': response['action']}
        }
    
    def get_contextual_help(self, context: str, user_rank: UserRank) -> str:
        """Get context-sensitive help suggestions"""
        # Provide smart suggestions based on user's current context
        suggestions = {
            'new_user': [
                ('manual_getting_started', '🚀 Start Here'),
                ('manual_mt5_setup', '🔌 Connect MT5'),
                ('tier_nibbler_tier', '🐭 Your Tier Benefits')
            ],
            'after_loss': [
                ('emergency_massive_loss', '💔 Recovery Protocol'),
                ('bot_medic_bot', '💊 Talk to Medic'),
                ('edu_risk_management_edu', '🛡️ Risk Management')
            ],
            'high_performer': [
                ('tier_upgrade_now', '⬆️ Upgrade Tier'),
                ('xp_prestige_system', '⭐ Prestige Info'),
                ('analytics_performance_stats', '📊 Your Stats')
            ]
        }
        
        return suggestions.get(context, [])


# Global instance
intel_center = IntelCommandCenter()


# Helper functions for integration
def handle_intel_command(user_id: int, user_rank: UserRank) -> CommandResult:
    """Handle /intel command"""
    return intel_center.handle_intel_command(user_id, user_rank)


def handle_intel_callback(callback_data: str, user_id: int, user_rank: UserRank) -> Dict[str, Any]:
    """Handle intel menu callbacks"""
    return intel_center.handle_menu_callback(callback_data, user_id, user_rank)