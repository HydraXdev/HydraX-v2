#!/usr/bin/env python3
"""
Simple Bot Runner - Fixes event loop issues
"""

import subprocess
import sys
import time

def run_bot():
    """Run the bot in a clean process"""
    print("🚀 Starting BITTEN Menu Bot...")
    
    try:
        # Run the bot in a subprocess to avoid event loop conflicts
        result = subprocess.run([
            sys.executable, '-c', '''
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w"

content_map = {
    "manual_getting_started": """🚀 **BOOT CAMP - Complete Beginner Guide**

**PHASE 1: ACCOUNT SETUP**
1. Sign up via Telegram (/start)
2. Choose your tier (Press Pass = FREE)
3. Access your trading dashboard
4. Complete profile setup

**PHASE 2: FIRST DEPLOYMENT**
1. Get familiar with webapp interface
2. Configure risk settings (start 1%)
3. Learn signal interpretation
4. Wait for first signal alert

**PHASE 3: LIVE COMBAT**
1. Execute your first trade via webapp
2. Monitor position in real-time
3. Upgrade to paid tier for more features
4. Scale up as you gain confidence

📖 **Next Steps**: Access https://joinbitten.com""",

    "analytics_performance_stats": """📊 **PERFORMANCE DASHBOARD**

**CURRENT STATS** (Last 30 days)
• Total Trades: 47
• Win Rate: 74.5%
• Net Profit: +$1,247.50
• Max Drawdown: -3.2%
• Average R:R: 1:2.1

**RANK PROGRESSION**
Current: 🦷 FANG Operative
Next: ⭐ COMMANDER (Need 15 more wins)
XP: 12,450 / 15,000

**RECENT PERFORMANCE**
This Week: +$284 (6W-2L)
Last Week: +$419 (8W-1L)
Best Day: +$156 (3W-0L)

📈 **Trend**: Improving consistency""",

    "manual_webapp_setup": """🌐 **WEBAPP ACCESS - Your Command Center**

**ACCESSING YOUR DASHBOARD**
• URL: https://joinbitten.com
• Login: Use your Telegram credentials
• Mobile: Works on all devices
• Desktop: Full-featured interface

**FIRST TIME SETUP**
1. Set risk tolerance (1-3%)
2. Choose notification preferences
3. Review tier features
4. Complete demo walkthrough

✅ **Ready to Trade**: All via web browser"""
}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Field Manual", callback_data="field_manual")],
        [InlineKeyboardButton("📊 Battle Stats", callback_data="analytics")],
        [InlineKeyboardButton("🚀 Boot Camp", callback_data="manual_getting_started")],
        [InlineKeyboardButton("🌐 WebApp", url="https://joinbitten.com")]
    ]
    await update.message.reply_text(
        "🎯 **BITTEN COMMAND CENTER**\\n\\nSelect your mission:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"🔍 CALLBACK: {query.data}")
    
    if query.data == "field_manual":
        keyboard = [
            [InlineKeyboardButton("🚀 Boot Camp", callback_data="manual_getting_started")],
            [InlineKeyboardButton("🌐 WebApp Setup", callback_data="manual_webapp_setup")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main")]
        ]
        await query.edit_message_text(
            "📚 **FIELD MANUAL**\\n\\nSelect guide:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data == "analytics":
        keyboard = [
            [InlineKeyboardButton("📊 Performance", callback_data="analytics_performance_stats")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main")]
        ]
        await query.edit_message_text(
            "📊 **BATTLE STATS**\\n\\nSelect analytics:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data in content_map:
        content = content_map[query.data]
        await query.answer()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=content,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.answer("✅ Menu working!")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(handle_cb))
    print("✅ Bot started! Use /start to test menus")
    await app.run_polling()

asyncio.run(main())
'''], capture_output=False)
        
    except KeyboardInterrupt:
        print("\\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_bot()