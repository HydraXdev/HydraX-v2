"""
Telegram Bot Integration for Daily Drill Reports
Handles automated delivery and user interaction with drill reports
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from .daily_drill_report import DailyDrillReportSystem, DailyTradingStats
from .tactical_strategies import tactical_strategy_manager
from .xp_economy import XPEconomy

logger = logging.getLogger(__name__)


class DrillReportBotIntegration:
    """Telegram bot integration for drill reports"""
    
    def __init__(self, bot_token: str, drill_system: DailyDrillReportSystem, xp_economy: XPEconomy = None):
        self.bot_token = bot_token
        self.drill_system = drill_system
        self.xp_economy = xp_economy
        self.app = Application.builder().token(bot_token).build()
        self._setup_handlers()
        
        # Schedule daily reports
        schedule.every().day.at("18:00").do(self._send_scheduled_reports)
    
    def _setup_handlers(self):
        """Setup command and callback handlers"""
        self.app.add_handler(CommandHandler("drill", self.cmd_drill_report))
        self.app.add_handler(CommandHandler("weekly", self.cmd_weekly_summary))
        self.app.add_handler(CommandHandler("drill_settings", self.cmd_drill_settings))
        self.app.add_handler(CallbackQueryHandler(self.handle_drill_callback))
    
    async def cmd_drill_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /drill command - show today's drill report with XP integration"""
        user_id = str(update.effective_user.id)
        
        try:
            # Generate drill report
            drill_message = self.drill_system.generate_drill_report(user_id)
            telegram_report = self.drill_system.format_telegram_report(drill_message, user_id)
            
            # Enhance with XP economy data if available
            if self.xp_economy:
                xp_summary = self.xp_economy.get_drill_report_xp_summary(user_id)
                tactical_status = self.xp_economy.get_tactical_unlock_status(user_id)
                
                # Add XP section to drill report
                xp_section = f"\n\n🔓 **XP ECONOMY STATUS**\n"
                xp_section += f"Current Balance: {xp_summary['current_balance']} XP\n"
                xp_section += f"Today's Earnings: +{xp_summary['today_earned']} XP\n"
                xp_section += f"Week's Earnings: +{xp_summary['week_earned']} XP\n"
                
                # Add tactical progression
                if tactical_status.get('next_unlock'):
                    next_unlock = tactical_status['next_unlock']
                    progress_bar = self._create_progress_bar(tactical_status['progress_percentage'])
                    xp_section += f"\n🎯 **TACTICAL PROGRESSION**\n"
                    xp_section += f"Next Unlock: {next_unlock['display_name']}\n"
                    xp_section += f"Progress: {progress_bar} {tactical_status['progress_percentage']:.1f}%\n"
                    xp_section += f"Need: {next_unlock['xp_needed']} more XP\n"
                
                # Add recent unlocks
                if xp_summary['recent_unlocks']:
                    xp_section += f"\n⚡ **RECENT UNLOCKS**\n"
                    for unlock in xp_summary['recent_unlocks'][:3]:  # Show last 3
                        xp_section += f"• {unlock['display_name']} ({unlock['days_ago']}d ago)\n"
                
                telegram_report += xp_section
            
            # Add interactive buttons with XP info
            keyboard = [
                [
                    InlineKeyboardButton("📊 Weekly Summary", callback_data=f"weekly_{user_id}"),
                    InlineKeyboardButton("🔓 XP Status", callback_data=f"xp_{user_id}")
                ],
                [
                    InlineKeyboardButton("🎯 Tactical Progress", callback_data=f"tactical_{user_id}"),
                    InlineKeyboardButton("🏆 Achievements", callback_data=f"achievements_{user_id}")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data=f"settings_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                telegram_report, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in drill report command: {e}")
            await update.message.reply_text(
                "⚠️ Unable to generate drill report. Try again later, soldier."
            )
    
    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 100 * length)
        empty = length - filled
        return "█" * filled + "░" * empty
    
    async def cmd_weekly_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weekly command - show weekly performance summary"""
        user_id = str(update.effective_user.id)
        
        try:
            weekly_stats = self.drill_system.get_weekly_summary(user_id)
            
            if "error" in weekly_stats:
                await update.message.reply_text(
                    "📊 **WEEKLY SUMMARY**\n\n"
                    "No trading activity this week, soldier.\n"
                    "Get back in there and engage the enemy! 🎯"
                )
                return
            
            summary = f"""📊 **WEEKLY PERFORMANCE SUMMARY**

🗓️ **Active Days**: {weekly_stats['days_active']}/7
💥 **Total Trades**: {weekly_stats['total_trades']}
✅ **Win Rate**: {weekly_stats['win_rate']:.1f}%
📈 **Avg Daily Return**: {weekly_stats['avg_daily_return']:+.1f}%
🔓 **XP Earned**: {weekly_stats['total_xp']}
🎯 **Best Win Streak**: {weekly_stats['best_streak']}

{self._get_weekly_assessment(weekly_stats)}

— DRILL SERGEANT 🎖️"""
            
            await update.message.reply_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in weekly summary: {e}")
            await update.message.reply_text(
                "⚠️ Unable to generate weekly summary. Systems temporarily down."
            )
    
    async def cmd_drill_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /drill_settings command"""
        user_id = str(update.effective_user.id)
        
        keyboard = [
            [
                InlineKeyboardButton("⏰ Report Time", callback_data=f"time_{user_id}"),
                InlineKeyboardButton("🗣️ Tone Style", callback_data=f"tone_{user_id}")
            ],
            [
                InlineKeyboardButton("📊 Include Stats", callback_data=f"stats_{user_id}"),
                InlineKeyboardButton("🎯 Tomorrow Tips", callback_data=f"tips_{user_id}")
            ],
            [
                InlineKeyboardButton("✅ Enable Reports", callback_data=f"enable_{user_id}"),
                InlineKeyboardButton("❌ Disable Reports", callback_data=f"disable_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = """⚙️ **DRILL REPORT SETTINGS**

Configure your daily drill reports:

⏰ **Report Time**: When to receive daily reports
🗣️ **Tone Style**: Drill sergeant personality 
📊 **Include Stats**: Show detailed statistics
🎯 **Tomorrow Tips**: Include next-day guidance
✅/❌ **Enable/Disable**: Turn reports on/off

Choose an option to modify:"""
        
        await update.message.reply_text(
            settings_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_drill_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle drill report callback queries"""
        callback_data = query.data
        user_id = str(query.from_user.id)
        
        try:
            if callback_data.startswith("weekly_"):
                await self._handle_weekly_callback(query, user_id)
            elif callback_data.startswith("settings_"):
                await self._handle_settings_callback(query, user_id)
            elif callback_data.startswith("strategy_"):
                await self._handle_strategy_callback(query, user_id)
            elif callback_data.startswith("achievements_"):
                await self._handle_achievements_callback(query, user_id)
            elif callback_data.startswith("xp_"):
                await self._handle_xp_callback(query, user_id)
            elif callback_data.startswith("tactical_"):
                await self._handle_tactical_callback(query, user_id)
            else:
                await query.answer("Unknown command, soldier.")
                
        except Exception as e:
            logger.error(f"Error handling drill callback: {e}")
            await query.answer("Command failed. Try again.")
    
    async def _handle_weekly_callback(self, query, user_id: str):
        """Handle weekly summary callback"""
        weekly_stats = self.drill_system.get_weekly_summary(user_id)
        
        if "error" in weekly_stats:
            await query.answer("No weekly data available yet.")
            return
        
        summary = f"""📊 **WEEKLY STATS**
Days Active: {weekly_stats['days_active']}/7
Win Rate: {weekly_stats['win_rate']:.1f}%
Total XP: {weekly_stats['total_xp']}
Best Streak: {weekly_stats['best_streak']}"""
        
        await query.answer(summary, show_alert=True)
    
    async def _handle_settings_callback(self, query, user_id: str):
        """Handle settings callback"""
        await query.answer("Settings panel opened.")
        # This would open detailed settings interface
    
    async def _handle_strategy_callback(self, query, user_id: str):
        """Handle tomorrow's strategy callback"""
        # Get current tactical state
        daily_state = tactical_strategy_manager.get_daily_state(user_id)
        
        if daily_state.selected_strategy:
            strategy_name = daily_state.selected_strategy.value.replace('_', ' ').title()
            await query.answer(f"Current strategy: {strategy_name}")
        else:
            await query.answer("No strategy selected yet. Use /tactics to choose.")
    
    async def _handle_achievements_callback(self, query, user_id: str):
        """Handle achievements callback"""
        if self.xp_economy and self.xp_economy.achievement_system:
            stats = self.xp_economy.achievement_system.get_achievement_stats(user_id)
            message = f"🏆 **ACHIEVEMENTS**\n"
            message += f"Unlocked: {stats['total_unlocked']}/{stats['total_available']}\n"
            message += f"Progress: {stats['completion_percentage']:.1f}%\n"
            message += f"Achievement XP: {stats['total_xp_earned']}"
            await query.answer(message, show_alert=True)
        else:
            await query.answer("Achievement system integration pending.")
    
    async def _handle_xp_callback(self, query, user_id: str):
        """Handle XP status callback"""
        if self.xp_economy:
            xp_summary = self.xp_economy.get_drill_report_xp_summary(user_id)
            balance = self.xp_economy.get_user_balance(user_id)
            
            message = f"🔓 **XP STATUS**\n"
            message += f"Current Balance: {xp_summary['current_balance']} XP\n"
            message += f"Today's Earnings: +{xp_summary['today_earned']} XP\n"
            message += f"Week's Earnings: +{xp_summary['week_earned']} XP\n"
            message += f"Lifetime Earned: {balance.lifetime_earned} XP\n"
            message += f"Lifetime Spent: {balance.lifetime_spent} XP"
            
            await query.answer(message, show_alert=True)
        else:
            await query.answer("XP system not available.")
    
    async def _handle_tactical_callback(self, query, user_id: str):
        """Handle tactical progress callback"""
        if self.xp_economy:
            tactical_status = self.xp_economy.get_tactical_unlock_status(user_id)
            
            message = f"🎯 **TACTICAL PROGRESS**\n"
            message += f"Current XP: {tactical_status['current_xp']}\n"
            message += f"Unlocked: {tactical_status['unlocked_count']}/{tactical_status['total_strategies']}\n"
            
            if tactical_status.get('next_unlock'):
                next_unlock = tactical_status['next_unlock']
                progress_bar = self._create_progress_bar(next_unlock['progress_percent'], 8)
                message += f"\nNext: {next_unlock['display_name']}\n"
                message += f"{progress_bar} {next_unlock['progress_percent']:.1f}%\n"
                message += f"Need: {next_unlock['xp_needed']} XP"
            else:
                message += f"\n🎉 ALL STRATEGIES UNLOCKED!"
            
            await query.answer(message, show_alert=True)
        else:
            await query.answer("Tactical system not available.")
    
    def _get_weekly_assessment(self, stats: Dict) -> str:
        """Get drill sergeant assessment of weekly performance"""
        win_rate = stats['win_rate']
        days_active = stats['days_active']
        
        if win_rate >= 70 and days_active >= 5:
            return "🏆 **OUTSTANDING WEEK** - You're operating like an elite soldier!"
        elif win_rate >= 60 and days_active >= 4:
            return "💪 **SOLID WEEK** - Good consistency and discipline shown."
        elif win_rate >= 50 and days_active >= 3:
            return "📈 **DECENT WEEK** - Room for improvement, but you're learning."
        elif days_active <= 2:
            return "⚠️ **MIA STATUS** - Where were you, soldier? Market won't wait!"
        else:
            return "🔄 **REGROUP WEEK** - Time to analyze and adjust tactics."
    
    def _send_scheduled_reports(self):
        """Send scheduled daily reports (called by scheduler)"""
        try:
            # This would be called by the scheduler
            reports_sent = self.drill_system.send_daily_reports(self.app.bot)
            logger.info(f"Sent {reports_sent} daily drill reports")
        except Exception as e:
            logger.error(f"Error sending scheduled reports: {e}")
    
    def start_scheduler(self):
        """Start the report scheduler (run in separate thread)"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        import threading
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Drill report scheduler started")


# Integration with main bot
def register_drill_report_handlers(bot_app, drill_system):
    """Register drill report handlers with main bot application"""
    
    drill_integration = DrillReportBotIntegration(None, drill_system)
    
    # Add handlers to existing bot
    bot_app.add_handler(CommandHandler("drill", drill_integration.cmd_drill_report))
    bot_app.add_handler(CommandHandler("weekly", drill_integration.cmd_weekly_summary))
    bot_app.add_handler(CommandHandler("drill_settings", drill_integration.cmd_drill_settings))
    bot_app.add_handler(CallbackQueryHandler(drill_integration.handle_drill_callback, pattern="^(weekly_|settings_|strategy_|achievements_)"))
    
    # Start scheduler
    drill_integration.start_scheduler()
    
    logger.info("Drill report handlers registered with main bot")
    
    return drill_integration


# Enhanced tactical system integration with XP economy
def create_drill_system_integration(tactical_manager, xp_economy: XPEconomy = None):
    """Create integration between drill system, tactical manager, and XP economy"""
    
    drill_system = DailyDrillReportSystem()
    
    def record_trade_completion(user_id: str, trade_result: Dict):
        """Called when a trade completes - updates daily stats and awards XP"""
        
        daily_state = tactical_manager.get_daily_state(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Award XP through economy system if available
        xp_awarded = 0
        if xp_economy:
            # Build context for XP calculation
            context = {
                "pair": trade_result.get('pair', 'Unknown'),
                "strategy": daily_state.selected_strategy.value if daily_state.selected_strategy else "NONE",
                "win_streak": daily_state.wins_today + (1 if trade_result.get('result') == 'WIN' else 0),
                "perfect_day": daily_state.losses_today == 0 and trade_result.get('result') == 'WIN'
            }
            
            # Award XP based on trade result
            xp_result = xp_economy.award_trade_xp(
                user_id=user_id,
                trade_result=trade_result.get('result', 'LOSS'),
                context=context
            )
            xp_awarded = xp_result['xp_added']
            
            # Check for strategy unlocks and add to trade result
            if xp_result.get('strategy_unlocks'):
                trade_result['strategy_unlocks'] = xp_result['strategy_unlocks']
            
            # Check for achievement unlocks
            if xp_result.get('achievement_unlocks'):
                trade_result['achievement_unlocks'] = xp_result['achievement_unlocks']
        
        # Get current stats or create new
        current_stats = drill_system._get_daily_stats(user_id, today)
        
        if not current_stats:
            # Create new daily stats
            stats = DailyTradingStats(
                user_id=user_id,
                date=today,
                trades_taken=daily_state.shots_fired,
                wins=daily_state.wins_today,
                losses=daily_state.losses_today,
                net_pnl_percent=daily_state.daily_pnl,
                strategy_used=daily_state.selected_strategy.value if daily_state.selected_strategy else "NONE",
                xp_gained=xp_awarded,
                shots_remaining=tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy].max_shots - daily_state.shots_fired if daily_state.selected_strategy else 0,
                max_shots=tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy].max_shots if daily_state.selected_strategy else 0,
                consecutive_wins=daily_state.wins_today,
                consecutive_losses=daily_state.losses_today,
                best_trade_pnl=trade_result.get('pnl_percent', 0),
                worst_trade_pnl=trade_result.get('pnl_percent', 0),
                total_pips=trade_result.get('pips', 0)
            )
        else:
            # Update existing stats
            stats = current_stats
            stats.trades_taken = daily_state.shots_fired
            stats.wins = daily_state.wins_today
            stats.losses = daily_state.losses_today
            stats.net_pnl_percent = daily_state.daily_pnl
            stats.xp_gained += xp_awarded
            stats.consecutive_wins = daily_state.wins_today
            stats.consecutive_losses = daily_state.losses_today
            
            # Update best/worst trades
            trade_pnl = trade_result.get('pnl_percent', 0)
            if trade_pnl > stats.best_trade_pnl:
                stats.best_trade_pnl = trade_pnl
            if trade_pnl < stats.worst_trade_pnl:
                stats.worst_trade_pnl = trade_pnl
        
        # Record updated stats
        drill_system.record_daily_stats(user_id, stats)
        
        logger.info(f"Updated daily drill stats for user {user_id}, awarded {xp_awarded} XP")
        
        # Return enhanced trade result with XP and unlock information
        enhanced_result = {
            **trade_result,
            'xp_awarded': xp_awarded,
            'daily_stats': stats
        }
        
        return enhanced_result
    
    return drill_system, record_trade_completion


# Example usage
if __name__ == "__main__":
    # Test drill report generation
    drill_system = DailyDrillReportSystem()
    
    # Simulate excellent performance
    excellent_stats = DailyTradingStats(
        user_id="test_user",
        date="2025-07-22",
        trades_taken=4,
        wins=3,
        losses=1,
        net_pnl_percent=6.1,
        strategy_used="FIRST_BLOOD",
        xp_gained=10,
        shots_remaining=0,
        max_shots=4,
        consecutive_wins=3,
        consecutive_losses=0,
        best_trade_pnl=3.2,
        worst_trade_pnl=-1.1,
        total_pips=45
    )
    
    drill_system.record_daily_stats("test_user", excellent_stats)
    drill_message = drill_system.generate_drill_report("test_user")
    report = drill_system.format_telegram_report(drill_message, "test_user")
    
    print("=== EXCELLENT PERFORMANCE DRILL REPORT ===")
    print(report)
    print()
    
    # Simulate poor performance
    poor_stats = DailyTradingStats(
        user_id="test_user2",
        date="2025-07-22",
        trades_taken=3,
        wins=0,
        losses=3,
        net_pnl_percent=-4.8,
        strategy_used="LONE_WOLF",
        xp_gained=0,
        shots_remaining=1,
        max_shots=4,
        consecutive_wins=0,
        consecutive_losses=3,
        best_trade_pnl=-1.2,
        worst_trade_pnl=-2.1,
        total_pips=-28
    )
    
    drill_system.record_daily_stats("test_user2", poor_stats)
    drill_message2 = drill_system.generate_drill_report("test_user2")
    report2 = drill_system.format_telegram_report(drill_message2, "test_user2")
    
    print("=== ROUGH DAY DRILL REPORT ===")
    print(report2)