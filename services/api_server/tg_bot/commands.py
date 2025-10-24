"""
Telegram Bot Command Handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
import httpx

from ..config import API_PORT

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Welcome to BITTEN v2.0! 🎯\n\n"
        "Commands:\n"
        "/fire <signal_id> - Execute a fire command\n"
        "/BITMODE ON|OFF - Toggle BITMODE\n"
        "/me - View your stats\n"
        "/brief - View mission briefing\n"
        "/help - Show this message"
    )


async def fire_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fire command"""
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /fire <signal_id>\n"
            "Example: /fire ELITE_GUARD_EURUSD_123456"
        )
        return

    signal_id = context.args[0]

    try:
        # Call fire API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{API_PORT}/api/signals/{signal_id}/fire",
                json={"signal_id": signal_id, "user_id": user_id}
            )

            if response.status_code == 200:
                data = response.json()
                await update.message.reply_text(
                    f"✅ Fire command sent!\n"
                    f"Fire ID: {data['fire_id']}\n"
                    f"Status: {data['status']}"
                )
            else:
                error = response.json().get("detail", "Unknown error")
                await update.message.reply_text(f"❌ Fire failed: {error}")

    except Exception as e:
        logger.error(f"Fire command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def bitmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /BITMODE command"""
    user_id = str(update.effective_user.id)

    if not context.args or context.args[0].upper() not in ["ON", "OFF"]:
        await update.message.reply_text(
            "❌ Usage: /BITMODE ON or /BITMODE OFF\n\n"
            "BITMODE: Hybrid position management system\n"
            "- 25% profit at +8 pips\n"
            "- 25% profit at +12 pips\n"
            "- 50% trailing with 10-pip stop\n\n"
            "Available for FANG+ tiers only"
        )
        return

    mode = context.args[0].upper()

    # TODO: Implement BITMODE toggle API call
    await update.message.reply_text(
        f"🎯 BITMODE {mode}\n"
        f"User: {user_id}\n"
        f"Status: BITMODE feature coming soon!"
    )


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /me command"""
    user_id = str(update.effective_user.id)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{API_PORT}/api/users/{user_id}/stats"
            )

            if response.status_code == 200:
                stats = response.json()
                await update.message.reply_text(
                    f"📊 Your Stats\n\n"
                    f"Tier: {stats['tier']}\n"
                    f"XP: {stats['xp']}\n"
                    f"Streak: {stats['streak']}\n"
                    f"Total Fires: {stats['total_fires']}\n"
                    f"Win Rate: {stats['win_rate']}%\n"
                    f"Total P&L: ${stats['total_pnl']}\n\n"
                    f"View full stats at http://134.199.204.67:8888/me"
                )
            else:
                await update.message.reply_text("❌ User not found")

    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def brief_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /brief command"""
    await update.message.reply_text(
        "📋 Mission Briefing\n\n"
        "View your mission briefing at:\n"
        "http://134.199.204.67:8888/brief\n\n"
        "Active signals and tactical objectives available."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await start_command(update, context)
