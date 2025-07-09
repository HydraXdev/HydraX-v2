#!/usr/bin/env python3
"""
AAA-Quality Telegram Menu System for BITTEN
Frictionless user experience with smart navigation
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from typing import List, Dict, Any

class BITTENMenu:
    """Intelligent menu system with context-aware navigation"""
    
    def __init__(self):
        self.webapp_url = "http://134.199.204.67:8888"
        
    def main_menu(self, user_tier: str = "nibbler") -> InlineKeyboardMarkup:
        """Generate main menu based on user tier"""
        
        # Core buttons available to all
        buttons = [
            [
                InlineKeyboardButton("🎯 Mission Control", callback_data="menu_mission"),
                InlineKeyboardButton("📊 My Stats", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton("🎓 Training", callback_data="menu_training"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ]
        ]
        
        # Tier-specific buttons
        if user_tier in ["fang", "commander", "apex"]:
            buttons.insert(1, [
                InlineKeyboardButton("🔥 Fire Modes", callback_data="menu_firemodes"),
                InlineKeyboardButton("👥 Squad", callback_data="menu_squad")
            ])
        
        if user_tier in ["commander", "apex"]:
            buttons.append([
                InlineKeyboardButton("🤖 Auto-Trade", callback_data="menu_auto"),
                InlineKeyboardButton("📈 Advanced", callback_data="menu_advanced")
            ])
        
        # Help always at bottom
        buttons.append([
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
            InlineKeyboardButton("🌐 WebApp", url=self.webapp_url)
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    def mission_menu(self) -> InlineKeyboardMarkup:
        """Mission control submenu"""
        buttons = [
            [
                InlineKeyboardButton("🎯 Active Signals", callback_data="mission_active"),
                InlineKeyboardButton("📜 History", callback_data="mission_history")
            ],
            [
                InlineKeyboardButton("🏆 Daily Mission", callback_data="mission_daily"),
                InlineKeyboardButton("💰 P&L Today", callback_data="mission_pnl")
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def training_menu(self) -> InlineKeyboardMarkup:
        """Education/Training submenu"""
        buttons = [
            [
                InlineKeyboardButton("📚 Quick Lessons", callback_data="train_lessons"),
                InlineKeyboardButton("🎮 Missions", callback_data="train_missions")
            ],
            [
                InlineKeyboardButton("📝 Journal", callback_data="train_journal"),
                InlineKeyboardButton("🏅 Achievements", callback_data="train_achievements")
            ],
            [
                InlineKeyboardButton("🎥 Video Library", url=f"{self.webapp_url}/learn"),
                InlineKeyboardButton("💡 Tips", callback_data="train_tips")
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def settings_menu(self, user_settings: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Settings submenu with current status"""
        
        # Toggle states
        alerts_icon = "🔔" if user_settings.get('alerts', True) else "🔕"
        stealth_icon = "🛡️" if user_settings.get('stealth', True) else "⚠️"
        
        buttons = [
            [
                InlineKeyboardButton(f"{alerts_icon} Alerts", callback_data="set_alerts"),
                InlineKeyboardButton(f"{stealth_icon} Stealth", callback_data="set_stealth")
            ],
            [
                InlineKeyboardButton("🎯 Risk Level", callback_data="set_risk"),
                InlineKeyboardButton("🌍 Timezone", callback_data="set_timezone")
            ],
            [
                InlineKeyboardButton("🔗 MT5 Setup", callback_data="set_mt5"),
                InlineKeyboardButton("👤 Profile", callback_data="set_profile")
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def quick_actions(self, context: str = "default") -> InlineKeyboardMarkup:
        """Context-aware quick action buttons"""
        
        if context == "after_loss":
            buttons = [
                [
                    InlineKeyboardButton("📝 Log Thoughts", callback_data="journal_loss"),
                    InlineKeyboardButton("🎓 Review Lesson", callback_data="learn_loss")
                ],
                [
                    InlineKeyboardButton("☕ Take Break", callback_data="cooldown_start"),
                    InlineKeyboardButton("📊 Analyze", callback_data="analyze_trade")
                ]
            ]
        
        elif context == "after_win":
            buttons = [
                [
                    InlineKeyboardButton("🎯 Next Signal", callback_data="signal_next"),
                    InlineKeyboardButton("📊 View Stats", callback_data="stats_session")
                ],
                [
                    InlineKeyboardButton("🏆 Share Win", callback_data="share_win"),
                    InlineKeyboardButton("💾 Save Setup", callback_data="save_setup")
                ]
            ]
        
        elif context == "cooldown":
            buttons = [
                [
                    InlineKeyboardButton("🎮 Play Mission", callback_data="mission_cooldown"),
                    InlineKeyboardButton("📚 Quick Learn", callback_data="learn_quick")
                ],
                [
                    InlineKeyboardButton("📊 Review Trades", callback_data="review_recent"),
                    InlineKeyboardButton("⏰ Time Left", callback_data="cooldown_status")
                ]
            ]
        
        else:  # default
            buttons = [
                [
                    InlineKeyboardButton("🎯 Signals", callback_data="menu_mission"),
                    InlineKeyboardButton("📊 Stats", callback_data="menu_stats")
                ],
                [
                    InlineKeyboardButton("📚 Learn", callback_data="menu_training"),
                    InlineKeyboardButton("❓ Help", callback_data="menu_help")
                ]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    def signal_actions(self, signal_id: str, user_tier: str) -> InlineKeyboardMarkup:
        """Actions for a specific signal"""
        buttons = []
        
        # Fire button with tier-appropriate text
        if user_tier == "nibbler":
            fire_text = "🎯 FIRE (Manual)"
        elif user_tier == "fang":
            fire_text = "🔥 FIRE SHOT"
        else:
            fire_text = "⚡ EXECUTE"
        
        buttons.append([
            InlineKeyboardButton(fire_text, callback_data=f"fire_{signal_id}"),
            InlineKeyboardButton("📊 Analysis", callback_data=f"analyze_{signal_id}")
        ])
        
        # Additional options
        buttons.append([
            InlineKeyboardButton("⏰ Set Alert", callback_data=f"alert_{signal_id}"),
            InlineKeyboardButton("❌ Pass", callback_data=f"pass_{signal_id}")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    def format_menu_message(self, menu_type: str, user_data: Dict[str, Any]) -> str:
        """Format message to accompany menu"""
        
        messages = {
            "main": f"""🎯 **BITTEN Command Center**
            
Tier: {user_data.get('tier', 'Nibbler').upper()}
XP: {user_data.get('xp', 0):,} | Level {user_data.get('level', 1)}
Today: {user_data.get('trades_today', 0)} trades | {user_data.get('pnl_today', 0):+.2f}%

What's your mission, soldier?""",
            
            "mission": """📡 **Mission Control**

Active signals, trade history, and daily objectives.
Your combat headquarters.""",
            
            "training": f"""🎓 **Training Academy**

Level {user_data.get('level', 1)} | {user_data.get('achievements', 0)} achievements
Knowledge is your edge in the battlefield.""",
            
            "settings": """⚙️ **Configuration**

Customize your trading experience.
Every detail matters."""
        }
        
        return messages.get(menu_type, "Select an option:")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle menu callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        # Main menu navigation
        if data == "menu_main":
            # Get user data (placeholder)
            user_data = {
                'tier': 'nibbler',
                'xp': 1250,
                'level': 5,
                'trades_today': 3,
                'pnl_today': 2.4
            }
            
            await query.edit_message_text(
                text=self.format_menu_message("main", user_data),
                reply_markup=self.main_menu(user_data['tier']),
                parse_mode='Markdown'
            )
        
        elif data == "menu_mission":
            await query.edit_message_text(
                text=self.format_menu_message("mission", {}),
                reply_markup=self.mission_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_training":
            user_data = {'level': 5, 'achievements': 12}
            await query.edit_message_text(
                text=self.format_menu_message("training", user_data),
                reply_markup=self.training_menu(),
                parse_mode='Markdown'
            )
        
        elif data == "menu_settings":
            user_settings = {'alerts': True, 'stealth': True}
            await query.edit_message_text(
                text=self.format_menu_message("settings", {}),
                reply_markup=self.settings_menu(user_settings),
                parse_mode='Markdown'
            )
        
        # Add more callback handlers as needed...

# Commands for bot integration
def get_menu_commands():
    """Get command list for bot"""
    return [
        ("menu", "Open main menu"),
        ("mission", "Mission control"),
        ("stats", "View your statistics"),
        ("training", "Access training academy"),
        ("settings", "Configure settings"),
        ("help", "Get help")
    ]