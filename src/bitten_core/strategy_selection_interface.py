"""
BITTEN Behavioral Strategy Selection Interface
Telegram bot commands and UI for NIBBLER strategy selection system
"""

from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from .behavioral_strategies import BehavioralStrategy, behavioral_strategy_manager
from .xp_economy import XPEconomy


class StrategySelectionInterface:
    """Interface for behavioral strategy selection and management"""

    def __init__(self, xp_economy: XPEconomy):
        self.xp_economy = xp_economy
        self.strategy_manager = behavioral_strategy_manager

    def get_strategy_menu(self, user_id: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Generate strategy selection menu for user"""

        # Get user's XP balance
        user_balance = self.xp_economy.get_user_balance(user_id)
        user_xp = user_balance.current_balance

        # Get current strategy
        current_strategy = self.strategy_manager.get_user_strategy(user_id)
        current_config = self.strategy_manager.STRATEGY_CONFIGS[current_strategy]

        # Get unlocked strategies
        unlocked_strategies = self.strategy_manager.get_unlocked_strategies(user_xp)

        # Get next unlock info
        next_unlock = self.strategy_manager.get_next_unlock(user_xp)

        # Build message
        message = f"""🎮 **BEHAVIORAL STRATEGY CENTER**

🏆 **Current XP**: {user_xp:}
🎯 **Active Strategy**: {current_config.display_name}
📝 *{current_config.description}*

**UNLOCKED STRATEGIES** ({len(unlocked_strategies)}/6):"""

        # Add unlocked strategies
        for strategy in unlocked_strategies:
            config = self.strategy_manager.STRATEGY_CONFIGS[strategy]
            is_current = "✅ " if strategy == current_strategy else "⚪ "
            message += f"\n{is_current}{config.display_name} - {config.description}"

        # Add next unlock info
        if next_unlock:
            message += f"\n\n🔓 **NEXT UNLOCK**: {next_unlock['display_name']}"
            message += f"\n📊 **Progress**: {user_xp:} / {next_unlock['required_xp']:} XP"
            message += f"\n⚡ **Need**: {next_unlock['xp_needed']:} more XP"
        else:
            message += f"\n\n🏆 **ALL STRATEGIES UNLOCKED!**"

        # Create keyboard
        keyboard = []

        # Strategy selection buttons (2 per row)
        strategy_buttons = []
        for strategy in unlocked_strategies:
            config = self.strategy_manager.STRATEGY_CONFIGS[strategy]
            emoji = "✅" if strategy == current_strategy else "⚪"
            button_text = f"{emoji} {config.display_name.split(' ', 1)[0]}"  # Just emoji + first word
            strategy_buttons.append(
                InlineKeyboardButton(button_text, callback_data=f"strategy_select_{strategy.value}")
            )

        # Add strategy buttons in pairs
        for i in range(0, len(strategy_buttons), 2):
            row = strategy_buttons[i : i + 2]
            keyboard.append(row)

        # Action buttons
        keyboard.append(
            [
                InlineKeyboardButton("📊 Strategy Stats", callback_data="strategy_stats"),
                InlineKeyboardButton("❓ Strategy Guide", callback_data="strategy_guide"),
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="strategy_menu"),
                InlineKeyboardButton("❌ Close", callback_data="close_menu"),
            ]
        )

        return message, InlineKeyboardMarkup(keyboard)

    def get_strategy_details(self, strategy: BehavioralStrategy) -> str:
        """Get detailed information about a strategy"""
        config = self.strategy_manager.STRATEGY_CONFIGS[strategy]

        message = f"""🎯 **{config.display_name}**

📋 **Description**: {config.description}

🔓 **Unlock Requirement**: {config.unlock_xp:} XP

⚙️ **Strategy Mechanics**:
• **TCS Filter**: {config.tcs_modifier:.1%} modifier
• **Risk Profile**: {config.risk_modifier:.1%} multiplier
• **Signal Focus**: {config.signal_filter.replace('_', ' ').title()}

🎮 **Gameplay Features**:"""

        mechanics = config.gameplay_mechanics
        if mechanics.get("special_abilities"):
            message += f"\n• **Special Abilities**: {', '.join(mechanics['special_abilities'])}"

        message += f"\n• **Signal Preference**: {mechanics.get('signal_preference', 'All types')}"
        message += f"\n• **Risk Profile**: {mechanics.get('risk_profile', 'Balanced')}"

        if strategy == BehavioralStrategy.LONE_WOLF:
            message += f"\n\n🐺 **DEFAULT STRATEGY** - Always available for all users"

        return message

    def handle_strategy_selection(self, user_id: str, strategy_value: str) -> Tuple[bool, str]:
        """Handle user strategy selection"""

        try:
            strategy = BehavioralStrategy(strategy_value)
        except ValueError:
            return False, "❌ Invalid strategy selection"

        # Get user XP
        user_balance = self.xp_economy.get_user_balance(user_id)
        user_xp = user_balance.current_balance

        # Check if user can use this strategy
        if not self.strategy_manager.can_unlock_strategy(user_xp, strategy):
            config = self.strategy_manager.STRATEGY_CONFIGS[strategy]
            needed_xp = config.unlock_xp - user_xp
            return (
                False,
                f"❌ Insufficient XP for {config.display_name}\nNeed {needed_xp:} more XP (have {user_xp:}, need {config.unlock_xp:})",
            )

        # Set the strategy
        success = self.strategy_manager.set_user_strategy(user_id, strategy, user_xp)

        if success:
            config = self.strategy_manager.STRATEGY_CONFIGS[strategy]
            return (
                True,
                f"✅ **Strategy Activated**: {config.display_name}\n\n{config.description}\n\nYour signals will now be filtered and modified according to this behavioral strategy!",
            )
        else:
            return False, "❌ Failed to activate strategy. Please try again."

    def get_strategy_guide(self) -> str:
        """Get comprehensive strategy guide"""

        message = """📚 **BEHAVIORAL STRATEGY GUIDE**

🎮 **What are Behavioral Strategies?**
Behavioral strategies modify how signals are filtered and executed based on different trading personalities. Each strategy has unique mechanics and unlock requirements.

🔓 **Progression System**:
• Unlock new strategies with XP
• Each strategy requires 120 XP more than the previous
• Strategies modify TCS thresholds, risk levels, and signal filtering

📊 **Strategy Overview**:

🐺 **LONE WOLF** (Default)
• Available to everyone
• Standard 60+ TCS filtering
• Balanced risk and signal selection

🩸 **FIRST BLOOD** (120 XP)
• Session opening specialist
• Bonus TCS for London/NY/Overlap sessions
• Slightly more aggressive risk

⚡ **CONVICTION PLAY** (240 XP)
• Premium signals only (75+ TCS)
• Higher risk on high-confidence trades
• Quality over quantity approach

💎 **DIAMOND HANDS** (360 XP)
• Extended take profit targets
• Tighter stop losses
• Hold positions longer

🔄 **RESET MASTER** (480 XP)
• Mean reversion specialist
• Bonus for support/resistance signals
• Counter-trend expert

🏗️ **STEADY BUILDER** (600 XP)
• Consistency and volume focus
• Smaller targets, more frequency
• Conservative compounding approach

💡 **Tips**:
• Start with LONE WOLF to learn the basics
• Each strategy suits different market conditions
• You can change strategies anytime (if unlocked)
• Strategy choice affects all your signals"""

        return message

    def get_strategy_stats(self, user_id: str) -> str:
        """Get user's strategy statistics"""

        stats = self.strategy_manager.get_strategy_stats(user_id)
        user_balance = self.xp_economy.get_user_balance(user_id)

        message = f"""📊 **YOUR STRATEGY STATS**

🎯 **Current Strategy**: {stats['display_name']}
📝 **Description**: {stats['description']}
🔓 **Unlock XP**: {stats['unlock_xp']:}
📅 **Active Since**: {stats['active_since'][:10]}

💰 **XP Progress**:
• **Current Balance**: {user_balance.current_balance:} XP
• **Lifetime Earned**: {user_balance.lifetime_earned:} XP
• **Lifetime Spent**: {user_balance.lifetime_spent:} XP

🎮 **Strategy Mechanics**:"""

        mechanics = stats["gameplay_mechanics"]
        message += f"\n• **Signal Preference**: {mechanics.get('signal_preference', 'All types')}"
        message += f"\n• **Risk Profile**: {mechanics.get('risk_profile', 'Balanced')}"

        if mechanics.get("special_abilities"):
            message += f"\n• **Special Abilities**: {', '.join(mechanics['special_abilities'])}"

        # Show unlocked strategies count
        unlocked_count = len(self.strategy_manager.get_unlocked_strategies(user_balance.current_balance))
        message += f"\n\n🏆 **Progress**: {unlocked_count}/6 strategies unlocked"

        return message


# Telegram bot command handlers
def register_strategy_commands(bot_instance):
    """Register strategy-related commands with the bot"""

    def cmd_strategies(update, context):
        """Show strategy selection menu"""
        user_id = str(update.effective_user.id)

        interface = StrategySelectionInterface(bot_instance.xp_economy)
        message, keyboard = interface.get_strategy_menu(user_id)

        try:
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        except Exception as e:
            update.message.reply_text(f"❌ Error loading strategy menu: {e}")

    def handle_strategy_callback(update, context):
        """Handle strategy selection callbacks"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        data = query.data

        interface = StrategySelectionInterface(bot_instance.xp_economy)

        try:
            if data == "strategy_menu":
                message, keyboard = interface.get_strategy_menu(user_id)
                query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

            elif data.startswith("strategy_select_"):
                strategy_value = data.replace("strategy_select_", "")
                success, response = interface.handle_strategy_selection(user_id, strategy_value)

                if success:
                    query.answer(f"✅ Strategy activated!")
                    # Refresh menu to show new selection
                    message, keyboard = interface.get_strategy_menu(user_id)
                    query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                else:
                    query.answer(f"❌ {response}")

            elif data == "strategy_stats":
                stats_message = interface.get_strategy_stats(user_id)
                query.answer("📊 Strategy stats")
                query.edit_message_text(
                    stats_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="strategy_menu")]]
                    ),
                )

            elif data == "strategy_guide":
                guide_message = interface.get_strategy_guide()
                query.answer("📚 Strategy guide")
                query.edit_message_text(
                    guide_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="strategy_menu")]]
                    ),
                )

            elif data == "close_menu":
                query.edit_message_text("🎮 Strategy menu closed. Use /strategies to reopen.")
                query.answer("Menu closed")

        except Exception as e:
            query.answer(f"❌ Error: {e}")

    # Register command and callback handlers
    bot_instance.add_command_handler("strategies", cmd_strategies)
    bot_instance.add_callback_handler(handle_strategy_callback)
