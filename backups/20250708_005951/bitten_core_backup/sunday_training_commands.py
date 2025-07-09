"""
🎯 Sunday Training Operations Telegram Commands
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import logging
from datetime import datetime, timezone

from .sunday_training_ops import SundayTrainingOps, TrainingType

logger = logging.getLogger(__name__)

# Global training ops manager
training_ops = SundayTrainingOps()

async def sunday_ops_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sunday_ops - Show available Sunday training missions
    """
    user_id = update.effective_user.id
    
    try:
        # Check if Sunday
        if datetime.now(timezone.utc).weekday() != 6:
            await update.message.reply_text(
                "🚫 **TRAINING OPS LOCKED**\n\n"
                "Sunday training missions are only available on Sundays.\n"
                "Come back this weekend for 2X XP opportunities.\n\n"
                "_Patience is a warrior's virtue._"
            )
            return
        
        # Get user profile
        profile_manager = context.bot_data.get('profile_manager')
        user_profile = await profile_manager.get_user_profile(user_id)
        
        if not user_profile:
            await update.message.reply_text("⚠️ No profile found. Use /start to begin.")
            return
        
        # Check positions
        mt5_bridge = context.bot_data.get('mt5_bridge')
        positions = await mt5_bridge.get_open_positions(user_id)
        
        # Get training briefing
        briefing = training_ops.get_sunday_briefing(
            user_profile.tier_level,
            len(positions) > 0
        )
        
        await update.message.reply_text(briefing, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in sunday_ops_command: {e}")
        await update.message.reply_text("❌ Error loading training missions.")


async def sunday_gap_hunter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Gap Hunter training mission"""
    await start_mission(update, context, "gap_hunter")


async def sunday_liquidity_recon_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Liquidity Recon mission"""
    await start_mission(update, context, "liquidity_recon")


async def sunday_spread_analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Spread Analysis mission"""
    await start_mission(update, context, "spread_analysis")


async def sunday_chaos_navigation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Chaos Navigation mission"""
    await start_mission(update, context, "chaos_navigation")


async def sunday_paper_assault_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Paper Assault mission"""
    await start_mission(update, context, "paper_assault")


async def start_mission(update: Update, context: ContextTypes.DEFAULT_TYPE, mission_id: str):
    """Generic mission start handler"""
    user_id = update.effective_user.id
    
    try:
        # Check user eligibility
        profile_manager = context.bot_data.get('profile_manager')
        user_profile = await profile_manager.get_user_profile(user_id)
        
        if not user_profile:
            await update.message.reply_text("⚠️ No profile found. Use /start to begin.")
            return
        
        # Check positions for live fire missions
        mission = training_ops.missions.get(mission_id)
        if mission and mission.training_type == TrainingType.LIVE_FIRE:
            mt5_bridge = context.bot_data.get('mt5_bridge')
            positions = await mt5_bridge.get_open_positions(user_id)
            
            if positions:
                await update.message.reply_text(
                    "🚫 **MISSION BLOCKED**\n\n"
                    "You have open positions.\n"
                    "Close all positions before live fire training.\n\n"
                    "_Safety first, soldier._"
                )
                return
        
        # Start mission
        success, message = training_ops.start_mission(user_id, mission_id)
        
        if success and mission.training_type == TrainingType.LIVE_FIRE:
            # Add confirmation for live missions
            keyboard = [[
                InlineKeyboardButton("✅ Confirm Live Fire", callback_data=f"confirm_mission_{mission_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_mission")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"{message}\n\n"
                "⚠️ **LIVE FIRE CONFIRMATION REQUIRED**\n"
                "Real money will be at risk.\n"
                "Are you ready?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error starting mission {mission_id}: {e}")
        await update.message.reply_text("❌ Error starting mission.")


async def mission_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /mission_status - Check current mission progress
    """
    user_id = update.effective_user.id
    
    try:
        progress = training_ops.check_mission_progress(user_id)
        
        if not progress:
            await update.message.reply_text(
                "📋 **NO ACTIVE MISSION**\n\n"
                "Use `/sunday_ops` to see available missions.\n\n"
                "_A warrior without a mission is just waiting._"
            )
            return
        
        mission = progress['mission']
        time_left = progress['time_remaining']
        
        # Format progress
        progress_text = "**Progress:**\n"
        for key, value in progress['progress'].items():
            progress_text += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        if not progress['progress']:
            progress_text = "**Progress:** No objectives completed yet.\n"
        
        message = (
            f"🎯 **MISSION: {mission.name}**\n"
            f"════════════════════\n"
            f"**Type:** {mission.training_type.value}\n"
            f"**Time Remaining:** {time_left.seconds//3600}h {(time_left.seconds//60)%60}m\n"
            f"**XP Multiplier:** {mission.xp_multiplier}x\n\n"
            f"{progress_text}\n"
            f"**XP Earned So Far:** {progress['xp_earned']}\n\n"
            f"_Keep pushing, operator._"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in mission_status: {e}")
        await update.message.reply_text("❌ Error checking mission status.")


async def abort_mission_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /abort_mission - Abort current mission
    """
    user_id = update.effective_user.id
    
    keyboard = [[
        InlineKeyboardButton("✅ Confirm Abort", callback_data="confirm_abort_mission"),
        InlineKeyboardButton("❌ Continue Mission", callback_data="cancel_abort")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ **ABORT MISSION?**\n\n"
        "You will lose all progress and XP.\n"
        "This cannot be undone.\n\n"
        "_Sometimes retreat is wisdom._",
        reply_markup=reply_markup
    )


async def sunday_leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sunday_leaderboard - Show Sunday training leaderboard
    """
    leaderboard = training_ops.get_sunday_leaderboard()
    await update.message.reply_text(leaderboard, parse_mode='Markdown')


async def handle_mission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mission-related callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data.startswith("confirm_mission_"):
        # Extract mission ID and confirm
        mission_id = query.data.replace("confirm_mission_", "")
        await query.edit_message_text(
            "🔥 **LIVE FIRE AUTHORIZED**\n\n"
            "Mission is hot. Trade carefully.\n"
            "High TCS only. Reduced risk mandatory.\n\n"
            "_May your stops be honored._",
            parse_mode='Markdown'
        )
        
    elif query.data == "cancel_mission":
        await query.edit_message_text(
            "❌ **MISSION CANCELLED**\n\n"
            "_Better safe than sorry, operator._"
        )
        
    elif query.data == "confirm_abort_mission":
        success, message = training_ops._complete_mission(user_id, success=False, reason="User aborted")
        await query.edit_message_text(message, parse_mode='Markdown')
        
    elif query.data == "cancel_abort":
        await query.edit_message_text(
            "✅ **MISSION CONTINUES**\n\n"
            "_Never give up, soldier._"
        )


# Mission progress update handlers (called from trade results)
async def update_live_fire_progress(user_id: int, won: bool, tcs: float):
    """Update progress for live fire missions"""
    progress = training_ops.check_mission_progress(user_id)
    
    if not progress:
        return
    
    mission = progress['mission']
    if mission.training_type != TrainingType.LIVE_FIRE:
        return
    
    # Update based on mission type
    current_trades = progress['progress'].get('trades_completed', 0)
    training_ops.update_mission_progress(user_id, 'trades_completed', current_trades + 1)
    
    if won:
        wins = progress['progress'].get('wins', 0)
        training_ops.update_mission_progress(user_id, 'wins', wins + 1)
    
    # Check TCS requirement
    if tcs >= mission.requirements.get('min_tcs', 0):
        valid_trades = progress['progress'].get('valid_tcs_trades', 0)
        training_ops.update_mission_progress(user_id, 'valid_tcs_trades', valid_trades + 1)


def register_sunday_commands(application):
    """Register all Sunday training commands"""
    
    # Main commands
    application.add_handler(CommandHandler("sunday_ops", sunday_ops_command))
    application.add_handler(CommandHandler("mission_status", mission_status_command))
    application.add_handler(CommandHandler("abort_mission", abort_mission_command))
    application.add_handler(CommandHandler("sunday_leaderboard", sunday_leaderboard_command))
    
    # Mission start commands
    application.add_handler(CommandHandler("sunday_gap_hunter", sunday_gap_hunter_command))
    application.add_handler(CommandHandler("sunday_liquidity_recon", sunday_liquidity_recon_command))
    application.add_handler(CommandHandler("sunday_spread_analysis", sunday_spread_analysis_command))
    application.add_handler(CommandHandler("sunday_chaos_navigation", sunday_chaos_navigation_command))
    application.add_handler(CommandHandler("sunday_paper_assault", sunday_paper_assault_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(
        handle_mission_callback,
        pattern="^(confirm_mission_|cancel_mission|confirm_abort_mission|cancel_abort)"
    ))
    
    logger.info("✅ Sunday training commands registered")