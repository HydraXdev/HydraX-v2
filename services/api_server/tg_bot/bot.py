"""
Telegram Bot Integration
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from ..config import TELEGRAM_BOT_TOKEN
from .commands import (
    start_command,
    fire_command,
    bitmode_command,
    me_command,
    brief_command,
    help_command
)

logger = logging.getLogger(__name__)


class BittenTelegramBot:
    """BITTEN Telegram Bot Handler"""

    def __init__(self):
        self.application = None
        self.bot_token = TELEGRAM_BOT_TOKEN

    async def initialize(self):
        """Initialize the bot application"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set, bot disabled")
            return

        self.application = Application.builder().token(self.bot_token).build()

        # Register command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("fire", fire_command))
        self.application.add_handler(CommandHandler("BITMODE", bitmode_command))
        self.application.add_handler(CommandHandler("me", me_command))
        self.application.add_handler(CommandHandler("brief", brief_command))
        self.application.add_handler(CommandHandler("help", help_command))

        logger.info("Telegram bot initialized successfully")

    async def start(self):
        """Start the bot"""
        if not self.application:
            await self.initialize()

        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot started")

    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")

    async def send_signal_alert(self, signal_data: dict):
        """Send signal alert to Telegram group"""
        if not self.application:
            return

        try:
            message = self._format_signal_message(signal_data)
            # TODO: Send to configured group/channel
            logger.info(f"Signal alert: {message}")
        except Exception as e:
            logger.error(f"Failed to send signal alert: {e}")

    def _format_signal_message(self, signal_data: dict) -> str:
        """Format signal data into Telegram message"""
        return f"""
🎯 NEW SIGNAL

Symbol: {signal_data.get('symbol')}
Direction: {signal_data.get('direction')}
Entry: {signal_data.get('entry')}
TP: {signal_data.get('tp')}
SL: {signal_data.get('sl')}
Confidence: {signal_data.get('confidence')}%

Use /fire {signal_data.get('signal_id')} to execute
"""


# Global instance
telegram_bot = BittenTelegramBot()
