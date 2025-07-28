#!/usr/bin/env python3
"""
Working Menu Bot - Simplified version without complex dependencies
All menu buttons fully functional
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'
WEBAPP_URL = 'https://joinbitten.com'

class SimpleMenuSystem:
    """Simplified menu system with all content"""
    
    def __init__(self):
        self.content = {
            # Field Manual Content
            'manual_getting_started': """🚀 **BOOT CAMP - Complete Beginner Guide**

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

📖 **Next Steps**: Access webapp at https://joinbitten.com""",

            'manual_webapp_setup': """🌐 **WEBAPP ACCESS - Your Command Center**

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

**TRADING INTERFACE**
• One-click trade execution
• Real-time P&L tracking
• Risk management tools
• Historical performance

✅ **Ready to Trade**: All via web browser""",

            'manual_first_trade': """🎯 **FIRST MISSION - Your Trading Debut**

**PRE-FLIGHT CHECKLIST**
□ Webapp dashboard accessible
□ Account verified and active
□ Demo balance available ($50k)
□ Risk set to 1% (conservative)

**MISSION EXECUTION**
1. **Wait for Signal**: Bot sends mission brief
2. **Review Intel**: Check TCS, R:R ratio
3. **Fire Command**: Click ⚡ QUICK FIRE or open webapp
4. **Monitor Position**: Track in real-time dashboard
5. **Mission Complete**: Auto-close at TP/SL

**FIRST TRADE REWARDS**
• +100 XP bonus
• "First Blood" achievement
• Unlocks advanced tutorials

🎮 **Pro Tip**: Start small, think big!""",

            'manual_reading_signals': """📖 **SIGNAL DECODE - Understanding Briefings**

**MISSION BRIEF STRUCTURE**
```
🎯 EURUSD BUY ASSAULT
TCS: 87% | R:R 1:2.5
Entry: 1.0850
SL: 1.0820 (30 pips)
TP: 1.0925 (75 pips)
```

**DECODING THE INTEL**
• **TCS (87%)**: Confidence level - higher = better
• **R:R 1:2.5**: Risk 1 to reward 2.5 ratio
• **Entry**: Exact price to enter trade
• **SL**: Stop Loss - max loss point
• **TP**: Take Profit - target exit

**PRIORITY LEVELS**
🔴 **HIGH**: Execute immediately
🟡 **MEDIUM**: Good opportunity
🟢 **LOW**: Optional/educational

**EXECUTION DECISION TREE**
• TCS 80%+: Strong execute
• TCS 60-79%: Careful execute
• TCS <60%: Consider skipping""",

            # Analytics Content
            'analytics_performance_stats': """📊 **PERFORMANCE DASHBOARD**

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

📈 **Trend**: Improving consistency
🎯 **Focus**: Risk management excellence""",

            'analytics_win_rate': """🎯 **WIN RATE ANALYSIS**

**OVERALL STATISTICS**
• All-Time Win Rate: 78.3%
• Last 100 Trades: 82.0%
• Current Streak: 7 wins
• Best Streak: 15 wins
• Recovery Rate: 91% (wins after loss)

**WIN RATE BY TIMEFRAME**
• Daily: 76% (short-term consistency)
• Weekly: 85% (strong weekly performance)
• Monthly: 78% (stable long-term)

**WIN RATE BY PAIR**
🥇 GBPUSD: 89% (23/26 trades)
🥈 EURUSD: 84% (31/37 trades)
🥉 USDJPY: 71% (22/31 trades)

**IMPROVEMENT AREAS**
• News trading: 62% win rate
• Asian session: 68% win rate

🎯 **Target**: Maintain 80%+ consistency""",

            'analytics_best_pairs': """💱 **BEST PERFORMING PAIRS**

**TOP PERFORMERS** (P&L)
🥇 **GBPUSD**: +$2,847 (89% WR)
   • Average: +$124 per win
   • Best Trade: +$312
   • Risk Score: A+

🥈 **EURUSD**: +$1,923 (84% WR)  
   • Average: +$86 per win
   • Best Trade: +$245
   • Risk Score: A

🥉 **USDJPY**: +$1,456 (71% WR)
   • Average: +$98 per win
   • Best Trade: +$289
   • Risk Score: B+

**STRATEGY INSIGHTS**
• Focus more on GBPUSD/EURUSD
• Strong European session performance
• Excellent trend-following results

🎯 **Recommendation**: Increase allocation to top 2 pairs""",

            'analytics_time_analysis': """⏰ **OPTIMAL TRADING TIMES**

**BEST SESSIONS** (Profitability)
🥇 **London Session** (8-12 GMT)
   • Win Rate: 89%
   • Avg Profit: +$127/trade
   • Best Pairs: GBPUSD, EURGBP

🥈 **NY Session** (13-17 GMT)
   • Win Rate: 82%
   • Avg Profit: +$98/trade  
   • Best Pairs: EURUSD, USDJPY

🥉 **Overlap** (12-15 GMT)
   • Win Rate: 94%
   • Avg Profit: +$156/trade
   • High volatility period

**AVOID THESE TIMES**
❌ Asian Session (21-05 GMT): 64% WR
❌ Sunday Open (21-23 GMT): 43% WR
❌ Friday Close (20-22 GMT): 58% WR

⏰ **Optimal Window**: 08:00-17:00 GMT
🎯 **Peak Performance**: 12:00-15:00 GMT""",

            # Tier Information
            'tier_nibbler': """🔰 **NIBBLER TIER - $39/month**

✅ **FEATURES INCLUDED:**
• Manual fire mode
• Basic signals access
• 6 trades per day
• Demo account included
• Risk management tools
• Basic analytics

🎯 **PERFECT FOR:**
• New traders
• Learning the system
• Building confidence
• Small account sizes

🚀 **UPGRADE PATH:**
Ready for more? Consider FANG tier for advanced features!

💳 **Subscribe**: /upgrade nibbler""",

            'tier_fang': """🦷 **FANG TIER - $89/month**

✅ **FEATURES INCLUDED:**
• Manual + Chaingun mode
• All signals access
• 10 trades per day
• Sniper execution
• Advanced analytics
• Priority support

🎯 **PERFECT FOR:**
• Experienced traders
• Aggressive strategies
• Medium accounts
• Active trading

🚀 **MOST POPULAR TIER**

💳 **Subscribe**: /upgrade fang""",

            'tier_commander': """⭐ **COMMANDER TIER - $189/month**

✅ **FEATURES INCLUDED:**
• Auto + Semi-auto modes
• Advanced features
• 20 trades per day
• Risk management suite
• VIP support
• Custom strategies

🎯 **PERFECT FOR:**
• Professional traders
• Large accounts
• Automation seekers
• Serious profits

💳 **Subscribe**: /upgrade commander""",

            'tier_apex': """🏔️ **TIER - /month**

✅ **FEATURES INCLUDED:**
• All features unlocked
• Unlimited trades
• Exclusive signals
• Personal account manager
• Custom development
• White-glove service

🎯 **PERFECT FOR:**
• Elite traders
• Institutional accounts
• Maximum performance
• Ultimate trading power

👑 **THE ULTIMATE EXPERIENCE**

💳 **Subscribe**: /upgrade apex"""
        }
    
    def get_main_menu(self):
        """Get main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("📚 Field Manual", callback_data="menu_nav_field_manual")],
            [InlineKeyboardButton("📊 Battle Stats", callback_data="menu_nav_analytics")],
            [InlineKeyboardButton("💰 Tier Intel", callback_data="menu_nav_tiers")],
            [InlineKeyboardButton("🌐 Open WebApp", url=WEBAPP_URL)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_field_manual_menu(self):
        """Get field manual submenu"""
        keyboard = [
            [InlineKeyboardButton("🚀 Boot Camp", callback_data="menu_action_manual_getting_started")],
            [InlineKeyboardButton("🌐 WebApp Setup", callback_data="menu_action_manual_webapp_setup")],
            [InlineKeyboardButton("🎯 First Mission", callback_data="menu_action_manual_first_trade")],
            [InlineKeyboardButton("📖 Signal Decode", callback_data="menu_action_manual_reading_signals")],
            [InlineKeyboardButton("⬅️ Back to Main", callback_data="menu_nav_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_analytics_menu(self):
        """Get analytics submenu"""
        keyboard = [
            [InlineKeyboardButton("📊 Performance", callback_data="menu_action_analytics_performance_stats")],
            [InlineKeyboardButton("🎯 Win Rate", callback_data="menu_action_analytics_win_rate")],
            [InlineKeyboardButton("💱 Best Pairs", callback_data="menu_action_analytics_best_pairs")],
            [InlineKeyboardButton("⏰ Time Analysis", callback_data="menu_action_analytics_time_analysis")],
            [InlineKeyboardButton("⬅️ Back to Main", callback_data="menu_nav_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_tiers_menu(self):
        """Get tiers submenu"""
        keyboard = [
            [InlineKeyboardButton("🔰 NIBBLER ($39)", callback_data="menu_action_tier_nibbler")],
            [InlineKeyboardButton("🦷 FANG ($89)", callback_data="menu_action_tier_fang")],
            [InlineKeyboardButton("⭐ COMMANDER ($189)", callback_data="menu_action_tier_commander")],
            [InlineKeyboardButton("🏔️ ()", callback_data="menu_action_tier_apex")],
            [InlineKeyboardButton("⬅️ Back to Main", callback_data="menu_nav_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

# Global menu system
menu_system = SimpleMenuSystem()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        """🎯 **BITTEN COMMAND CENTER**
*Your complete trading assistant*

Welcome to the elite tactical trading system. Choose your mission below:""",
        reply_markup=menu_system.get_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu command"""
    await update.message.reply_text(
        """🎯 **INTEL COMMAND CENTER**

Select your intel category:""",
        reply_markup=menu_system.get_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    
    print(f"🔍 CALLBACK: {query.data} from user {query.from_user.id}")
    
    try:
        if query.data == "menu_nav_main":
            await query.edit_message_text(
                """🎯 **BITTEN COMMAND CENTER**

Select your mission:""",
                reply_markup=menu_system.get_main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data == "menu_nav_field_manual":
            await query.edit_message_text(
                """📚 **FIELD MANUAL**
*Complete guides and tutorials*

Select your training guide:""",
                reply_markup=menu_system.get_field_manual_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data == "menu_nav_analytics":
            await query.edit_message_text(
                """📊 **BATTLE STATS**
*Performance analytics and insights*

Select your analytics:""",
                reply_markup=menu_system.get_analytics_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data == "menu_nav_tiers":
            await query.edit_message_text(
                """💰 **TIER INTEL**
*Subscription tiers and features*

Select a tier to learn more:""",
                reply_markup=menu_system.get_tiers_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data.startswith("menu_action_"):
            # Handle action buttons
            action_id = query.data.replace("menu_action_", "")
            
            content = menu_system.content.get(action_id, f"📋 **{action_id.replace('_', ' ').title()}**\n\nContent for {action_id}")
            
            await query.answer()  # Acknowledge the callback
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=content,
                parse_mode=ParseMode.MARKDOWN
            )
            
        else:
            await query.answer("✅ Button received!")
            
    except Exception as e:
        print(f"❌ Error handling callback: {e}")
        await query.answer("❌ Menu error - please try again")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower()
    
    if text in ['menu', 'intel', 'help']:
        await menu_command(update, context)
    elif text == 'status':
        await update.message.reply_text("🤖 BITTEN Bot: ONLINE\n📋 Menu System: ACTIVE")
    else:
        await update.message.reply_text("Use /start or /menu to access the command center!")

async def main():
    """Main function"""
    print("🚀 Starting BITTEN Menu Bot...")
    print(f"🎯 WebApp URL: {WEBAPP_URL}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["menu", "intel"], menu_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot ready! All menu buttons should work now!")
    print("📋 Test with /start or /menu")
    
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())