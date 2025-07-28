"""
Weekend Safety Briefing Telegram Commands
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def weekend_brief_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /weekend_brief - Get your weekend safety briefing on demand
    """
    user_id = update.effective_user.id
    
    try:
        # Get user profile
        profile_manager = context.bot_data.get('profile_manager')
        user_profile = await profile_manager.get_user_profile(user_id)
        
        if not user_profile:
            await update.message.reply_text(
                "⚠️ No profile found. Use /start to begin."
            )
            return
        
        # Get MT5 bridge
        mt5_bridge = context.bot_data.get('mt5_bridge')
        positions = await mt5_bridge.get_open_positions(user_id)
        
        # Get briefing system
        from .weekend_warning_system import WeekendSafetyBriefing
        briefing_system = WeekendSafetyBriefing()
        
        # Generate briefing
        briefing = briefing_system.get_weekend_warning_message(
            user_profile.tier_level,
            len(positions)
        )
        
        # Add stats if available
        if hasattr(user_profile, 'weekend_stats'):
            briefing += briefing_system.get_weekend_stats_summary(
                user_profile.weekend_stats
            )
        
        # Add on-demand footer
        briefing += (
            "\n\n"
            "────────────────────\n"
            "**ON-DEMAND BRIEFING**\n"
            "_Requested by operator_\n"
        )
        
        await update.message.reply_text(briefing, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in weekend_brief_command: {e}")
        await update.message.reply_text(
            "❌ Error generating briefing. Try again later."
        )

async def force_weekend_briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /force_weekend_briefing - Admin command to trigger briefing for all users
    """
    user_id = update.effective_user.id
    
    # Check admin
    if user_id not in context.bot_data.get('admin_ids', []):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    try:
        await update.message.reply_text(
            "🎖️ Initiating weekend safety briefing for all operators..."
        )
        
        # Get scheduler and trigger
        from .weekend_briefing_scheduler import trigger_test_briefing
        telegram_router = context.bot_data.get('telegram_router')
        profile_manager = context.bot_data.get('profile_manager')
        
        await trigger_test_briefing(telegram_router, profile_manager)
        
        await update.message.reply_text(
            "✅ Weekend safety briefing complete. Check logs for details."
        )
        
    except Exception as e:
        logger.error(f"Error in force_weekend_briefing: {e}")
        await update.message.reply_text(
            f"❌ Briefing failed: {str(e)}"
        )

async def weekend_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /weekend_stats - Show user's weekend trading performance
    """
    user_id = update.effective_user.id
    
    try:
        # Get user profile
        profile_manager = context.bot_data.get('profile_manager')
        user_profile = await profile_manager.get_user_profile(user_id)
        
        if not user_profile:
            await update.message.reply_text(
                "⚠️ No profile found. Use /start to begin."
            )
            return
        
        # Get weekend stats
        stats = user_profile.get_weekend_trading_stats()
        
        if not stats or stats['total_trades'] == 0:
            message = (
                "📊 **NO WEEKEND TRADING HISTORY**\n"
                "────────────────────\n"
                "You haven't traded on weekends yet.\n"
                "\n"
                "_Smart move, operator._"
            )
        else:
            win_rate = (stats['wins'] / stats['total_trades']) * 100
            
            # Determine rating
            if win_rate >= 70:
                rating = "🟢 EXCELLENT"
                comment = "Weekend warrior status confirmed."
            elif win_rate >= 50:
                rating = "🟡 ACCEPTABLE"
                comment = "Room for improvement."
            else:
                rating = "🔴 POOR"
                comment = "Consider avoiding weekends."
            
            message = (
                f"📊 **WEEKEND COMBAT RECORD**\n"
                f"────────────────────\n"
                f"**Total Missions:** {stats['total_trades']}\n"
                f"**Successful:** {stats['wins']}\n"
                f"**Failed:** {stats['losses']}\n"
                f"**Win Rate:** {win_rate:.1f}%\n"
                f"**Total P&L:** ${stats['total_pnl']:+.2f}\n"
                f"\n"
                f"**Rating:** {rating}\n"
                f"\n"
                f"_{comment}_"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in weekend_stats_command: {e}")
        await update.message.reply_text(
            "❌ Error retrieving stats. Try again later."
        )

# Register commands with the bot
def register_weekend_commands(application):
    """Register all weekend briefing commands"""
    from telegram.ext import CommandHandler
    
    application.add_handler(CommandHandler("weekend_brief", weekend_brief_command))
    application.add_handler(CommandHandler("weekend_stats", weekend_stats_command))
    application.add_handler(CommandHandler("force_weekend_briefing", force_weekend_briefing_command))
    
    logger.info("✅ Weekend briefing commands registered")