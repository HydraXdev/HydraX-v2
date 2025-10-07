"""
NIBBLER Tactical Strategy Selection Interface
Telegram bot commands and UI for daily tactical strategy selection
"""

from typing import Dict, List, Optional, Tuple

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
except ImportError:
    # Fallback for newer telegram versions
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.constants import ParseMode
from .tactical_strategies import TacticalStrategy, tactical_strategy_manager
from .xp_economy import XPEconomy


class TacticalInterface:
    """Interface for tactical strategy selection and management"""

    def __init__(self, xp_economy: XPEconomy):
        self.xp_economy = xp_economy
        self.tactical_manager = tactical_strategy_manager

    def get_daily_strategy_menu(self, user_id: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Generate daily strategy selection menu"""

        # Get user XP and unlocked strategies
        user_balance = self.xp_economy.get_user_balance(user_id)
        user_xp = user_balance.current_balance
        unlocked_strategies = self.tactical_manager.get_unlocked_strategies(user_xp)

        # Get current daily state
        daily_state = self.tactical_manager.get_daily_state(user_id)

        # Build message
        message = f"""🎯 **DAILY TACTICAL SELECTION**

💰 **Current XP**: {user_xp:}
📊 **Today's Status**: """

        if daily_state.selected_strategy:
            config = self.tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy]
            if daily_state.locked_until:
                from datetime import datetime

                hours_left = (daily_state.locked_until - datetime.now()).total_seconds() / 3600
                message += f"""🔒 **{config.display_name}** (Locked {hours_left:.1f}h)
🎯 **Shots**: {daily_state.shots_fired}/{config.max_shots}
📈 **Wins**: {daily_state.wins_today} | **Losses**: {daily_state.losses_today}
💰 **Daily P&L**: {daily_state.daily_pnl:+.1f}%"""
            else:
                message += f"Ready to select"
        else:
            message += "No strategy selected"

        message += f"\n\n**AVAILABLE TACTICS** ({len(unlocked_strategies)}/4):"

        # Add strategy descriptions with personal stats
        for strategy in unlocked_strategies:
            config = self.tactical_manager.TACTICAL_CONFIGS[strategy]
            stats = self.tactical_manager.get_strategy_stats(user_id, strategy)

            is_selected = "✅" if daily_state.selected_strategy == strategy else "⚪"

            message += f"""
{is_selected} **{config.display_name}**
    📋 {config.description}
    🎯 Max shots: {config.max_shots} | Potential: {config.daily_potential}
    📊 Your stats: {stats['win_rate']:.1f}% WR, avg {stats['avg_daily_pnl']:+.1f}%/day"""

        # Show next unlock if applicable
        next_unlock_xp = 999999
        for strategy, config in self.tactical_manager.TACTICAL_CONFIGS.items():
            if config.unlock_xp > user_xp:
                next_unlock_xp = min(next_unlock_xp, config.unlock_xp)

        if next_unlock_xp < 999999:
            message += f"\n\n🔓 **Next unlock at {next_unlock_xp} XP** ({next_unlock_xp - user_xp} needed)"

        # Create keyboard
        keyboard = []

        # Strategy selection buttons
        if not daily_state.locked_until:
            strategy_buttons = []
            for strategy in unlocked_strategies:
                config = self.tactical_manager.TACTICAL_CONFIGS[strategy]
                emoji = config.display_name.split()[0]  # Get emoji
                strategy_buttons.append(
                    InlineKeyboardButton(
                        f"{emoji} {strategy.value.replace('_', ' ').title()}",
                        callback_data=f"select_tactic_{strategy.value}",
                    )
                )

            # Add strategy buttons in pairs
            for i in range(0, len(strategy_buttons), 2):
                row = strategy_buttons[i : i + 2]
                keyboard.append(row)
        else:
            keyboard.append([InlineKeyboardButton("🔒 Strategy Locked Until Midnight", callback_data="noop")])

        # Additional buttons
        keyboard.append(
            [
                InlineKeyboardButton("📊 Detailed Stats", callback_data="tactical_stats"),
                InlineKeyboardButton("❓ Strategy Guide", callback_data="tactical_guide"),
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="tactical_menu"),
                InlineKeyboardButton("❌ Close", callback_data="close_menu"),
            ]
        )

        return message, InlineKeyboardMarkup(keyboard)

    def handle_strategy_selection(self, user_id: str, strategy_value: str) -> Tuple[bool, str]:
        """Handle user strategy selection for the day"""

        try:
            strategy = TacticalStrategy(strategy_value)
        except ValueError:
            return False, "❌ Invalid strategy selection"

        # Get user XP
        user_balance = self.xp_economy.get_user_balance(user_id)
        user_xp = user_balance.current_balance

        # Attempt to select strategy
        success, message = self.tactical_manager.select_daily_strategy(user_id, strategy, user_xp)

        if success:
            config = self.tactical_manager.TACTICAL_CONFIGS[strategy]
            detailed_message = f"""🎯 **TACTICAL SELECTION CONFIRMED**

**{config.display_name}** activated for today!

📋 **Mission Brief**:
{config.description}

🎯 **Rules of Engagement**:
• Max shots: {config.max_shots}
• Daily potential: {config.daily_potential}
• Teaching focus: {config.teaching_focus}

🧠 **Psychology**: {config.psychology}

⚠️ **LOCKED UNTIL MIDNIGHT** - No switching allowed!

Ready to hunt! 🎯"""
            return True, detailed_message
        else:
            return False, f"❌ {message}"

    def get_tactical_stats(self, user_id: str) -> str:
        """Get detailed tactical performance stats"""

        user_balance = self.xp_economy.get_user_balance(user_id)
        daily_state = self.tactical_manager.get_daily_state(user_id)

        message = f"""📊 **TACTICAL PERFORMANCE REPORT**

💰 **Current XP**: {user_balance.current_balance:}
🏆 **Lifetime Earned**: {user_balance.lifetime_earned:}

📅 **Today's Mission**:"""

        if daily_state.selected_strategy:
            config = self.tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy]
            message += f"""
🎯 **Strategy**: {config.display_name}
📊 **Shots**: {daily_state.shots_fired}/{config.max_shots}
📈 **Performance**: {daily_state.wins_today}W-{daily_state.losses_today}L
💰 **Daily P&L**: {daily_state.daily_pnl:+.2f}%"""
        else:
            message += "\n❌ No strategy selected today"

        message += "\n\n**STRATEGY PERFORMANCE HISTORY**:"

        # Show stats for each unlocked strategy
        unlocked = self.tactical_manager.get_unlocked_strategies(user_balance.current_balance)
        for strategy in unlocked:
            stats = self.tactical_manager.get_strategy_stats(user_id, strategy)
            config = self.tactical_manager.TACTICAL_CONFIGS[strategy]

            message += f"""
{config.display_name}:
    📊 {stats['total_shots']} shots over {stats['total_days']} days
    📈 {stats['win_rate']:.1f}% win rate ({stats['wins']}W-{stats['losses']}L)
    💰 Avg: {stats['avg_daily_pnl']:+.1f}%/day
    🏆 Best: {stats['best_day']:+.1f}% | Worst: {stats['worst_day']:+.1f}%"""

        return message

    def get_tactical_guide(self) -> str:
        """Get comprehensive tactical strategy guide"""

        message = """📚 **NIBBLER TACTICAL WARFARE GUIDE**

🎯 **MISSION OBJECTIVE**: Master signal execution through tactical progression

⚠️ **ENGAGEMENT RULES**:
• 2% risk per shot (NEVER exceed)
• Max 6% daily drawdown (hard limit)
• 1 trade open at a time
• Strategy locked until midnight
• All signals are RAPID RAID (under 1 hour)

🎮 **TACTICAL PROGRESSION**:

🐺 **LONE WOLF** (Training Wheels)
• 4 shots, any 74+ TCS, 1:1.3 R:R
• Learn basics without getting hurt
• ~10-12 opportunities/day

🎯 **FIRST BLOOD** (Escalation Mastery)
• 4 shots with escalating requirements
• Shot 1: 75+ TCS, 1:1.25 R:R (confidence)
• Shot 2: 78+ TCS, 1:1.5 R:R (momentum)
• Shot 3: 80+ TCS, 1:1.75 R:R (house money)
• Shot 4: 85+ TCS, 1:1.9 R:R (elite)
• STOP after 2 wins (profit protection)

💥 **DOUBLE TAP** (Precision Selection)
• 2 shots only, both 85+ TCS, same direction
• 1:1.8 R:R for quality over quantity
• Teaches patience and directional conviction

⚡ **TACTICAL COMMAND** (Earned Mastery)
• Choice between sniper or volume mode
• Ultimate precision OR proven capability
• Complete tactical flexibility

🧠 **PSYCHOLOGY OF PROGRESSION**:
Each tactic teaches specific trading skills:
• LONE WOLF: Basic execution
• FIRST BLOOD: Momentum & escalation
• DOUBLE TAP: Quality assessment & patience
• TACTICAL COMMAND: Complete mastery

💡 **PRO TIPS**:
• Higher TCS = higher win rates
• Better traders need fewer shots
• Quality > quantity always wins
• Discipline beats aggression"""

        return message

    def get_shot_confirmation(self, user_id: str, signal_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Get shot confirmation with tactical context"""

        can_fire, reason, shot_info = self.tactical_manager.can_fire_shot(
            user_id, signal_data.get("tcs", 0), signal_data.get("direction", "")
        )

        if not can_fire:
            return False, f"❌ {reason}", None

        daily_state = self.tactical_manager.get_daily_state(user_id)
        config = self.tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy]

        confirmation_message = f"""🎯 **SHOT CONFIRMATION**

**{config.display_name}** - Shot {shot_info['shot_number']}/{config.max_shots}

📊 **Signal**: {signal_data.get('pair', '')} {signal_data.get('direction', '')}
🎯 **TCS**: {signal_data.get('tcs', 0)} ({shot_info['description']})
💰 **R:R**: 1:{shot_info['risk_reward']}
📈 **Risk**: 2% of account

⚠️ **Confirm this shot?**"""

        return True, confirmation_message, shot_info


# Telegram bot command handlers
def register_tactical_commands(bot_instance):
    """Register tactical strategy commands with the bot"""

    def cmd_tactics(update, context):
        """Show daily tactical strategy menu"""
        user_id = str(update.effective_user.id)

        interface = TacticalInterface(bot_instance.xp_economy)
        message, keyboard = interface.get_daily_strategy_menu(user_id)

        try:
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        except Exception as e:
            update.message.reply_text(f"❌ Error loading tactical menu: {e}")

    def handle_tactical_callback(update, context):
        """Handle tactical strategy callbacks"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        data = query.data

        interface = TacticalInterface(bot_instance.xp_economy)

        try:
            if data == "tactical_menu":
                message, keyboard = interface.get_daily_strategy_menu(user_id)
                query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

            elif data.startswith("select_tactic_"):
                strategy_value = data.replace("select_tactic_", "")
                success, response = interface.handle_strategy_selection(user_id, strategy_value)

                if success:
                    query.answer(f"✅ Strategy selected!")
                    query.edit_message_text(response, parse_mode=ParseMode.MARKDOWN)
                else:
                    query.answer(f"❌ Selection failed")
                    query.edit_message_text(
                        response,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🔙 Back to Menu", callback_data="tactical_menu")]]
                        ),
                    )

            elif data == "tactical_stats":
                stats_message = interface.get_tactical_stats(user_id)
                query.answer("📊 Tactical stats")
                query.edit_message_text(
                    stats_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="tactical_menu")]]
                    ),
                )

            elif data == "tactical_guide":
                guide_message = interface.get_tactical_guide()
                query.answer("📚 Tactical guide")
                query.edit_message_text(
                    guide_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="tactical_menu")]]
                    ),
                )

            elif data == "close_menu":
                query.edit_message_text("🎯 Tactical menu closed. Use /tactics to reopen.")
                query.answer("Menu closed")

            elif data == "noop":
                query.answer("Strategy locked until midnight")

        except Exception as e:
            query.answer(f"❌ Error: {e}")

    # Register command and callback handlers
    bot_instance.add_command_handler("tactics", cmd_tactics)
    bot_instance.add_callback_handler(handle_tactical_callback)
