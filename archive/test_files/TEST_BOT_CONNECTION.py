#!/usr/bin/env python3
"""
Minimal bot test to check connection and /ping command
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    await update.message.reply_text("🏓 Pong! Bot is working!")
    print(f"✅ Ping received from {update.effective_user.first_name}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **TEST BOT ACTIVE**\n\n"
        "✅ Connection: Working\n"
        "✅ Commands: Operational\n"
        "✅ /ping: Available\n\n"
        "This is a minimal test bot to verify functionality."
    )
    print(f"✅ Start command from {update.effective_user.first_name}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower().strip()
    
    if text == 'ping':
        await update.message.reply_text("🏓 Pong!")
    elif text == 'test':
        await update.message.reply_text("✅ Test successful!")
    elif text == 'status':
        await update.message.reply_text("🤖 Bot Status: ONLINE and RESPONSIVE")
    else:
        await update.message.reply_text(f"Echo: {update.message.text}")
    
    print(f"✅ Message received: {text}")

def main():
    """Main function"""
    print("🤖 STARTING MINIMAL TEST BOT")
    print("=" * 40)
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    print("🎯 Commands: /ping, /start")
    print("💬 Text: ping, test, status")
    print("")
    
    try:
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("ping", ping_command))
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        print("🚀 Bot starting... (Press Ctrl+C to stop)")
        
        # Run bot
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())