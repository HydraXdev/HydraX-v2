#!/usr/bin/env python3
"""
Debug Menu Bot - Simple test to verify menu buttons work
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with test menu"""
    keyboard = [
        [InlineKeyboardButton("📚 Field Manual", callback_data="menu_nav_field_manual")],
        [InlineKeyboardButton("📊 Battle Stats", callback_data="menu_nav_analytics")],
        [InlineKeyboardButton("🚀 Boot Camp", callback_data="menu_action_manual_getting_started")],
        [InlineKeyboardButton("🌐 Webapp Setup", callback_data="menu_action_manual_webapp_setup")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧪 **DEBUG MENU TEST**\n\nClick any button to test menu functionality:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    
    print(f"🔍 CALLBACK RECEIVED: {query.data}")
    print(f"👤 User: {query.from_user.id} ({query.from_user.username})")
    
    if query.data == "menu_nav_field_manual":
        # Show field manual submenu
        keyboard = [
            [InlineKeyboardButton("🚀 Boot Camp", callback_data="menu_action_manual_getting_started")],
            [InlineKeyboardButton("🌐 Webapp Setup", callback_data="menu_action_manual_webapp_setup")],
            [InlineKeyboardButton("🎯 First Mission", callback_data="menu_action_manual_first_trade")],
            [InlineKeyboardButton("⬅️ Back", callback_data="menu_nav_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📚 **FIELD MANUAL**\n\nSelect a guide:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif query.data == "menu_nav_analytics":
        # Show analytics submenu
        keyboard = [
            [InlineKeyboardButton("📊 Performance", callback_data="menu_action_analytics_performance_stats")],
            [InlineKeyboardButton("🎯 Win Rate", callback_data="menu_action_analytics_win_rate")],
            [InlineKeyboardButton("💱 Best Pairs", callback_data="menu_action_analytics_best_pairs")],
            [InlineKeyboardButton("⬅️ Back", callback_data="menu_nav_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 **BATTLE STATS**\n\nSelect analytics:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif query.data.startswith("menu_action_"):
        # Handle action buttons with real content
        action_id = query.data.replace("menu_action_", "")
        
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

📖 **Next Steps**: Use /manual for full guide""",

            "manual_webapp_setup": """🌐 **WEBAPP ACCESS - Your Command Center**

**ACCESSING YOUR DASHBOARD**
• URL: https://joinbitten.com
• Login: Use your Telegram credentials
• Mobile: Works on all devices
• Desktop: Full-featured interface

**DASHBOARD OVERVIEW**
• Live Signals: Real-time trade alerts
• Position Manager: Active trades
• Analytics: Performance tracking
• Risk Settings: Personal preferences

**FIRST TIME SETUP**
1. Set risk tolerance (1-3%)
2. Choose notification preferences
3. Review tier features
4. Complete demo walkthrough

✅ **Ready to Trade**: All via web browser""",

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

📈 **Trend**: Improving consistency"""
        }
        
        content = content_map.get(action_id, f"📋 **{action_id.replace('_', ' ').title()}**\n\nContent for {action_id}")
        
        await query.answer()  # Acknowledge the callback
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=content,
            parse_mode=ParseMode.MARKDOWN
        )
        
    else:
        await query.answer("✅ Button works! Callback received.")

async def main():
    """Main function"""
    print("🚀 Starting DEBUG Menu Bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Debug bot ready! Use /start to test menu buttons")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())