#!/usr/bin/env python3
"""
BITTEN Interactive Menu System
Complete inline button navigation for intuitive user experience
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MenuSystem:
    """Complete menu navigation system with inline buttons"""
    
    def __init__(self):
        # Menu state tracking for users
        self.user_menu_state = {}
        
    def get_main_menu(self, user_id: int, user_tier: str = "PRESS_PASS") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Get the main menu with all primary options
        Returns (message_text, keyboard)
        """
        
        # Main menu message
        message = """🎯 **BITTEN COMMAND CENTER**
        
Welcome to your tactical trading headquarters!

Choose an option below to navigate:"""
        
        # Build keyboard based on user tier
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Row 1: Trading & Signals
        keyboard.row(
            InlineKeyboardButton("📡 Live Signals", callback_data="menu_signals"),
            InlineKeyboardButton("🔫 Fire Mode", callback_data="menu_fire_mode")
        )
        
        # Row 2: Stats & Profile
        keyboard.row(
            InlineKeyboardButton("📊 My Stats", callback_data="menu_stats"),
            InlineKeyboardButton("🎮 Profile", callback_data="menu_profile")
        )
        
        # Row 3: Squad & Leaderboard
        keyboard.row(
            InlineKeyboardButton("🪖 My Squad", callback_data="menu_squad"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")
        )
        
        # Row 4: Learn & Settings
        keyboard.row(
            InlineKeyboardButton("📚 How to Play", callback_data="menu_learn"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        )
        
        # Row 5: Premium features (if applicable)
        if user_tier == "PRESS_PASS":
            keyboard.row(
                InlineKeyboardButton("⭐ Upgrade Tier", callback_data="menu_upgrade")
            )
        else:
            keyboard.row(
                InlineKeyboardButton("🎖️ War Room", callback_data="menu_warroom"),
                InlineKeyboardButton("💎 Premium", callback_data="menu_premium")
            )
        
        # Row 6: Help & Support
        keyboard.row(
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
            InlineKeyboardButton("🔄 Refresh", callback_data="menu_refresh")
        )
        
        return message, keyboard
    
    def get_signals_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Get the signals submenu"""
        
        message = """📡 **LIVE SIGNALS**
        
Current market signals and opportunities:

🟢 **Active Signals**: 3
🟡 **Pending**: 2
🔴 **Expired**: 5

Select an option:"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.row(
            InlineKeyboardButton("🎯 View Active", callback_data="signals_active"),
            InlineKeyboardButton("⏰ History", callback_data="signals_history")
        )
        
        keyboard.row(
            InlineKeyboardButton("🔔 Alerts ON/OFF", callback_data="signals_alerts"),
            InlineKeyboardButton("📈 Performance", callback_data="signals_performance")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("🔄 Refresh", callback_data="signals_refresh")
        )
        
        return message, keyboard
    
    def get_fire_mode_menu(self, current_mode: str = "manual") -> Tuple[str, InlineKeyboardMarkup]:
        """Get the fire mode configuration menu"""
        
        mode_emojis = {
            "manual": "🎯",
            "semi_auto": "⚡",
            "full_auto": "🔥"
        }
        
        message = f"""🔫 **FIRE MODE SETTINGS**
        
Current Mode: {mode_emojis.get(current_mode, '🎯')} **{current_mode.upper().replace('_', ' ')}**

**Available Modes:**
🎯 **MANUAL** - Full control, confirm each trade
⚡ **SEMI-AUTO** - Auto-fire high confidence signals
🔥 **FULL AUTO** - Maximum automation

Select your fire mode:"""
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        # Mode selection buttons
        keyboard.row(
            InlineKeyboardButton(
                f"{'✅' if current_mode == 'manual' else '🎯'} MANUAL", 
                callback_data="fire_mode_manual"
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                f"{'✅' if current_mode == 'semi_auto' else '⚡'} SEMI-AUTO", 
                callback_data="fire_mode_semi"
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                f"{'✅' if current_mode == 'full_auto' else '🔥'} FULL AUTO", 
                callback_data="fire_mode_full"
            )
        )
        
        keyboard.row(
            InlineKeyboardButton("📊 Mode Stats", callback_data="fire_mode_stats"),
            InlineKeyboardButton("❓ Mode Help", callback_data="fire_mode_help")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_profile_menu(self, user_data: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """Get the user profile menu"""
        
        callsign = user_data.get('callsign', 'Not Set')
        tier = user_data.get('tier', 'PRESS_PASS')
        total_trades = user_data.get('total_trades', 0)
        win_rate = user_data.get('win_rate', 0)
        
        message = f"""🎮 **YOUR PROFILE**
        
**Callsign**: {callsign}
**Tier**: {tier}
**Total Trades**: {total_trades}
**Win Rate**: {win_rate:.1f}%

Customize your profile:"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if tier != "PRESS_PASS":
            keyboard.row(
                InlineKeyboardButton("✏️ Edit Callsign", callback_data="profile_callsign"),
                InlineKeyboardButton("🎨 Themes", callback_data="profile_themes")
            )
        
        keyboard.row(
            InlineKeyboardButton("📊 Full Stats", callback_data="profile_stats"),
            InlineKeyboardButton("🏆 Achievements", callback_data="profile_achievements")
        )
        
        keyboard.row(
            InlineKeyboardButton("🔗 Connect MT5", callback_data="profile_mt5"),
            InlineKeyboardButton("📱 Notifications", callback_data="profile_notifications")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_callsign_menu(self, current_callsign: str, suggestions: List[str]) -> Tuple[str, InlineKeyboardMarkup]:
        """Get the callsign selection menu"""
        
        message = f"""✏️ **CHOOSE YOUR CALLSIGN**
        
Current: **{current_callsign}**

Select a suggested callsign or type your own:"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Add suggestion buttons (2 per row)
        for i in range(0, len(suggestions), 2):
            if i + 1 < len(suggestions):
                keyboard.row(
                    InlineKeyboardButton(suggestions[i], callback_data=f"callsign_set_{suggestions[i]}"),
                    InlineKeyboardButton(suggestions[i+1], callback_data=f"callsign_set_{suggestions[i+1]}")
                )
            else:
                keyboard.row(
                    InlineKeyboardButton(suggestions[i], callback_data=f"callsign_set_{suggestions[i]}")
                )
        
        keyboard.row(
            InlineKeyboardButton("✍️ Type Custom", callback_data="callsign_custom")
        )
        
        keyboard.row(
            InlineKeyboardButton("⬅️ Back", callback_data="menu_profile"),
            InlineKeyboardButton("❌ Cancel", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_learn_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Get the learning/tutorial menu"""
        
        message = """📚 **HOW TO PLAY BITTEN**

Master the art of tactical trading!

**Quick Start Guide:**
1️⃣ **Watch Signals** - Monitor live trading opportunities
2️⃣ **Set Fire Mode** - Choose your automation level
3️⃣ **Execute Trades** - Fire on high-confidence signals
4️⃣ **Track Performance** - Monitor your success rate
5️⃣ **Level Up** - Earn XP and unlock features

Select a topic to learn more:"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.row(
            InlineKeyboardButton("🎯 Signal Types", callback_data="learn_signals"),
            InlineKeyboardButton("🔫 Fire Modes", callback_data="learn_fire")
        )
        
        keyboard.row(
            InlineKeyboardButton("💰 Risk Management", callback_data="learn_risk"),
            InlineKeyboardButton("📈 Trading Basics", callback_data="learn_basics")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏆 Tier System", callback_data="learn_tiers"),
            InlineKeyboardButton("🎖️ XP & Levels", callback_data="learn_xp")
        )
        
        keyboard.row(
            InlineKeyboardButton("🪖 Squad System", callback_data="learn_squad"),
            InlineKeyboardButton("❓ FAQ", callback_data="learn_faq")
        )
        
        keyboard.row(
            InlineKeyboardButton("📹 Video Tutorial", url="https://youtube.com/bitten_tutorial"),
            InlineKeyboardButton("📖 Full Guide", url="https://bitten.trading/guide")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_stats_menu(self, user_stats: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """Get detailed stats menu"""
        
        message = f"""📊 **YOUR STATISTICS**

**Performance Overview:**
• Total Trades: {user_stats.get('total_trades', 0)}
• Win Rate: {user_stats.get('win_rate', 0):.1f}%
• Total P&L: ${user_stats.get('total_pnl', 0):,.2f}
• Best Streak: {user_stats.get('best_streak', 0)}
• Current Streak: {user_stats.get('current_streak', 0)}

Select time period:"""
        
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        keyboard.row(
            InlineKeyboardButton("📅 Today", callback_data="stats_today"),
            InlineKeyboardButton("📅 Week", callback_data="stats_week"),
            InlineKeyboardButton("📅 Month", callback_data="stats_month")
        )
        
        keyboard.row(
            InlineKeyboardButton("📈 Charts", callback_data="stats_charts"),
            InlineKeyboardButton("🎯 By Signal", callback_data="stats_signals")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏆 Compare", callback_data="stats_compare"),
            InlineKeyboardButton("📤 Export", callback_data="stats_export")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_help_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Get the help menu"""
        
        message = """❓ **HELP & SUPPORT**

How can we help you today?

**Quick Actions:**
• Having issues? Check FAQ first
• Need support? Contact our team
• Found a bug? Report it

Select an option:"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.row(
            InlineKeyboardButton("📖 Commands", callback_data="help_commands"),
            InlineKeyboardButton("❓ FAQ", callback_data="help_faq")
        )
        
        keyboard.row(
            InlineKeyboardButton("🐛 Report Bug", callback_data="help_bug"),
            InlineKeyboardButton("💬 Support", url="https://t.me/bitten_support")
        )
        
        keyboard.row(
            InlineKeyboardButton("📚 Documentation", url="https://docs.bitten.trading"),
            InlineKeyboardButton("🎥 Tutorials", callback_data="help_tutorials")
        )
        
        keyboard.row(
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("⬅️ Back", callback_data="menu_main")
        )
        
        return message, keyboard
    
    def get_back_button(self, callback_data: str = "menu_main") -> InlineKeyboardMarkup:
        """Get a simple back/home button row"""
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("⬅️ Back", callback_data=callback_data),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
        )
        return keyboard
    
    def get_confirmation_menu(self, action: str, data: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """Get a confirmation menu for important actions"""
        
        message = f"""⚠️ **CONFIRM ACTION**

{action}

Are you sure you want to proceed?"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{data.get('action')}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        )
        
        return message, keyboard
    
    def handle_navigation(self, user_id: int, current_menu: str, direction: str) -> str:
        """
        Handle menu navigation tracking
        Returns the appropriate menu to show
        """
        
        # Track user's menu history for back button
        if user_id not in self.user_menu_state:
            self.user_menu_state[user_id] = []
        
        history = self.user_menu_state[user_id]
        
        if direction == "forward":
            history.append(current_menu)
            # Keep only last 10 menu states
            if len(history) > 10:
                history.pop(0)
        
        elif direction == "back" and history:
            return history.pop()
        
        elif direction == "home":
            history.clear()
            return "menu_main"
        
        return current_menu

# Singleton
_menu_instance = None

def get_menu_system() -> MenuSystem:
    """Get singleton instance of menu system"""
    global _menu_instance
    if _menu_instance is None:
        _menu_instance = MenuSystem()
    return _menu_instance