#!/usr/bin/env python3
"""
Clean Menu Bot - No dependencies, clean event loop
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Suppress telegram logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

# Content for menu buttons - Main BITTEN System
CONTENT = {
    # Main menu content for BITTEN system buttons
    "combat_ops": """🔫 **COMBAT OPS - Active Mission Center**

**CURRENT OPERATIONS**
• 🎯 Signal #847: EURUSD BUY (TCS: 72%)
• ⚡ Sniper Alert: GBPUSD SELL (TCS: 89%)
• 🔥 Rapid Assault: 3 active positions

**MISSION STATUS**
• Active Trades: 5 positions
• Daily P&L: +$847.23
• Win Streak: 7 consecutive
• Risk Level: MODERATE

**FIRE MODES AVAILABLE**
• 🎯 MANUAL: Click to execute
• ⚡ SEMI-AUTO: Assisted execution  
• 🔥 FULL AUTO: Autonomous trading

🚀 **Ready for Combat**: https://joinbitten.com""",

    "field_manual": """📚 **FIELD MANUAL - Complete Training Guide**

**MISSION BRIEFINGS**
• 🚀 Boot Camp: Getting started guide
• 🎯 Signal Analysis: Understanding TCS scores
• 🔫 Fire Modes: Manual, Semi-Auto, Full Auto
• 💰 Risk Management: Position sizing & limits

**TACTICAL KNOWLEDGE**
• Market Structure & Timing
• Entry/Exit Strategies
• Risk-Reward Optimization
• Emotional Trading Control

**ADVANCED OPERATIONS**
• Multi-timeframe Analysis
• News Event Navigation
• Portfolio Management
• Performance Optimization

📖 **Continue Training**: Access full guides at https://joinbitten.com""",

    "tactical_tools": """🛠️ **TACTICAL TOOLS - Operational Arsenal**

**SIGNAL ANALYSIS TOOLS**
• 📊 TCS Calculator: Confidence scoring
• 📈 Trend Scanner: Multi-timeframe analysis
• ⚡ Volatility Monitor: Market conditions
• 🎯 Entry/Exit Optimizer: Timing precision

**RISK MANAGEMENT**
• 💰 Position Sizer: Lot calculation
• 🛡️ Stop Loss Calculator: Risk limits
• 📉 Drawdown Tracker: Portfolio health
• 🚨 Emergency Stop: Panic button

**PERFORMANCE ANALYTICS**
• 📊 Win Rate Tracker: Success metrics
• 💹 P&L Dashboard: Profit analysis
• 🎖️ Rank Progression: XP tracking
• 📈 Trend Analysis: Performance insights

🔧 **Access Tools**: Available at https://joinbitten.com""",

    "bot_concierge": """🤖 **BOT CONCIERGE - AI Assistant**

**AVAILABLE SERVICES**
• 💬 Live Chat Support: 24/7 assistance
• 📋 Account Management: Settings & preferences
• 🎯 Signal Explanations: TCS breakdown
• 📊 Performance Reviews: Trade analysis

**QUICK HELP**
• ❓ FAQ Database: Common questions
• 🔧 Technical Support: System issues
• 💰 Billing Support: Payment & upgrades
• 📚 Training Resources: Learning materials

**AI CAPABILITIES**
• Signal Analysis Explanations
• Risk Management Advice
• Trading Strategy Guidance
• Performance Optimization Tips

🤖 **Chat Now**: Visit https://joinbitten.com for live support""",

    "tier_intel": """💰 **TIER INTEL - Access Levels**

**YOUR CURRENT TIER**
🦷 **FANG** - $89/month
✅ All signal types
✅ Manual execution
✅ Advanced analytics
⭐ Upgrade to COMMANDER for automation

**TIER COMPARISON**
• 🆓 PRESS PASS: 7-day trial, 6 trades/day
• 🔰 NIBBLER: $39/month, RAPID ASSAULT only
• 🦷 FANG: $89/month, All signals manual
• ⭐ COMMANDER: $139/month, Full automation
• 🏔️ APEX: $188/month, Exclusive features

**UPGRADE BENEFITS**
• 🎯 Autonomous trading slots
• ⚡ Priority signal delivery
• 🔧 Advanced risk controls
• 👑 Elite community access

💎 **Upgrade Now**: https://joinbitten.com""",

    "analytics": """📊 **BATTLE STATS - Performance Analytics**

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

    "education": """🎓 **WAR COLLEGE - Advanced Training**

**COURSE CATALOG**
• 📊 Technical Analysis Mastery
• 💰 Risk Management Protocols
• 🎯 Signal Psychology & Execution
• 📈 Market Structure Fundamentals

**CURRENT CURRICULUM**
• Module 1: Chart Pattern Recognition
• Module 2: Support/Resistance Dynamics
• Module 3: Momentum & Trend Analysis
• Module 4: News Event Navigation

**CERTIFICATION TRACKS**
• 🏆 Tactical Trader Certification
• 🎖️ Risk Management Specialist
• ⭐ Signal Analysis Expert
• 👑 Elite Operative Status

🎓 **Enroll Now**: Advanced training at https://joinbitten.com""",

    "tools": """🛠️ **TACTICAL TOOLS - Operational Arsenal**

**SIGNAL ANALYSIS TOOLS**
• 📊 TCS Calculator: Confidence scoring
• 📈 Trend Scanner: Multi-timeframe analysis
• ⚡ Volatility Monitor: Market conditions
• 🎯 Entry/Exit Optimizer: Timing precision

**RISK MANAGEMENT**
• 💰 Position Sizer: Lot calculation
• 🛡️ Stop Loss Calculator: Risk limits
• 📉 Drawdown Tracker: Portfolio health
• 🚨 Emergency Stop: Panic button

**PERFORMANCE ANALYTICS**
• 📊 Win Rate Tracker: Success metrics
• 💹 P&L Dashboard: Profit analysis
• 🎖️ Rank Progression: XP tracking
• 📈 Trend Analysis: Performance insights

🔧 **Access Tools**: Available at https://joinbitten.com""",

    # Additional content for all main menu buttons
    "xp_economy": """🎖️ **XP ECONOMY - Rewards & Progression**

**YOUR XP STATUS**
Current Level: 47
Total XP: 12,450
Next Level: 15,000 XP (2,550 needed)
Daily XP Earned: +347

**XP SOURCES**
• ✅ Successful Trade: +50 XP
• 🎯 Win Streak Bonus: +25 XP/streak
• 📊 Daily Login: +10 XP
• 🎓 Training Completion: +100 XP

**REWARDS UNLOCKED**
• 🏆 Elite Trader Badge
• 🎯 Custom Callsign Rights
• 📊 Advanced Analytics Access
• 💰 Tier Upgrade Discount

**ACHIEVEMENT PROGRESS**
• Sniper Expert: 87/100 high TCS wins
• Profit Master: 15/20 consecutive wins
• Risk Manager: 45/50 perfect stops

🎖️ **Level Up**: Keep trading to advance ranks!""",

    "account": """👤 **ACCOUNT OPS - Profile Management**

**ACCOUNT OVERVIEW**
• Username: @FANG_Operative_7429
• Tier: 🦷 FANG ($89/month)
• Join Date: March 15, 2025
• Status: ✅ ACTIVE

**SUBSCRIPTION DETAILS**
• Next Billing: August 15, 2025
• Payment Method: •••• 4567
• Auto-Renewal: ✅ ENABLED
• Upgrade Available: ⭐ COMMANDER

**ACCOUNT SETTINGS**
• 🔔 Notifications: ENABLED
• 📱 Mobile Alerts: ON
• 📊 Data Sharing: TACTICAL ONLY
• 🔐 2FA Security: ENABLED

**RECENT ACTIVITY**
• Last Login: Today 14:27
• Last Trade: EURUSD BUY (+$47)
• Session Time: 2h 34m

👤 **Manage Account**: Full settings at https://joinbitten.com""",

    "community": """👥 **SQUAD HQ - Community Hub**

**YOUR SQUAD STATUS**
• Rank: 🦷 FANG Operative
• Squad: ALPHA-7 TACTICAL
• Squad Rank: #3 of 47 members
• Squad XP: 847,230 (Elite Status)

**COMMUNITY FEATURES**
• 💬 Squad Chat: 24/7 discussion
• 🏆 Leaderboards: Daily/weekly/monthly
• 🎯 Squad Challenges: Group missions
• 📊 Performance Sharing: Trade insights

**THIS WEEK'S CHALLENGE**
🎯 **Team Precision Strike**
Objective: 50 squad wins @ 85%+ TCS
Progress: 34/50 (68% complete)
Reward: +500 XP + Premium Badge

**TOP SQUAD MEMBERS**
🥇 APEX_Sniper_001: 94.7% WR
🥈 CMDR_Alpha_Strike: 91.2% WR  
🥉 Your Position: 89.4% WR

👥 **Join Squad**: Community features at https://joinbitten.com""",

    "tech_support": """🔧 **TECH SUPPORT - System Assistance**

**SYSTEM STATUS**
• 🟢 Trading Engine: OPERATIONAL
• 🟢 Signal Feed: LIVE
• 🟢 WebApp: RESPONSIVE
• 🟢 Database: OPTIMAL

**QUICK FIXES**
• 🔄 Refresh Signal Feed
• 🧹 Clear Browser Cache
• 📱 Reset Mobile App
• 🔐 Regenerate API Keys

**COMMON ISSUES**
• ❓ Signal Delays: Check connection
• 📊 Charts Not Loading: Clear cache
• 🔔 Missing Notifications: Check settings
• 💰 Payment Issues: Update card

**CONTACT SUPPORT**
• 📧 Email: support@joinbitten.com
• 💬 Live Chat: Available 24/7
• 📱 Emergency: Use emergency button
• 📋 Ticket System: Track requests

🔧 **Get Help**: Full support at https://joinbitten.com""",

    "emergency": """🚨 **EMERGENCY - Crisis Management**

**EMERGENCY PROTOCOLS**
• 🛑 STOP ALL TRADES: Immediate halt
• 💰 CLOSE POSITIONS: Emergency exit
• 📞 CONTACT SUPPORT: Urgent assistance
• 🔒 ACCOUNT LOCK: Security measure

**MARKET EMERGENCY**
• Flash Crash Protection: AUTO-ENABLED
• News Event Lockout: MONITORING
• Volatility Shields: ACTIVE
• Emergency Stop Loss: SET

**ACCOUNT SECURITY**
• Suspicious Activity: NONE DETECTED
• Login Attempts: NORMAL
• API Access: SECURE
• 2FA Status: ACTIVE

**EMERGENCY CONTACTS**
• 📞 24/7 Hotline: +1-555-BITTEN
• 🚨 Crisis Chat: emergency@joinbitten.com
• 📋 Report Issue: Instant ticket
• 🔒 Security Team: Direct line

**PANIC BUTTON**
[🛑 EMERGENCY STOP ALL]

🚨 **Crisis Response**: Immediate help available""",

    "speak_to_bot": """🤖 **BOT CONCIERGE - AI Assistant**

**AVAILABLE SERVICES**
• 💬 Live Chat Support: 24/7 assistance
• 📋 Account Management: Settings & preferences
• 🎯 Signal Explanations: TCS breakdown
• 📊 Performance Reviews: Trade analysis

**QUICK HELP**
• ❓ FAQ Database: Common questions
• 🔧 Technical Support: System issues
• 💰 Billing Support: Payment & upgrades
• 📚 Training Resources: Learning materials

**AI CAPABILITIES**
• Signal Analysis Explanations
• Risk Management Advice
• Trading Strategy Guidance
• Performance Optimization Tips

🤖 **Chat Now**: Visit https://joinbitten.com for live support"""
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with main BITTEN menu"""
    keyboard = [
        [InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
         InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")],
        [InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
         InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")],
        [InlineKeyboardButton("🎓 WAR COLLEGE", callback_data="menu_education"),
         InlineKeyboardButton("🛠️ TACTICAL TOOLS", callback_data="menu_tools")],
        [InlineKeyboardButton("📊 BATTLE STATS", callback_data="menu_analytics"),
         InlineKeyboardButton("👤 ACCOUNT OPS", callback_data="menu_account")],
        [InlineKeyboardButton("👥 SQUAD HQ", callback_data="menu_community"),
         InlineKeyboardButton("🤖 BOT CONCIERGE", callback_data="menu_bot_concierge")],
        [InlineKeyboardButton("🔧 TECH SUPPORT", callback_data="menu_tech_support"),
         InlineKeyboardButton("🚨 EMERGENCY", callback_data="menu_emergency")],
        [InlineKeyboardButton("🌐 Open WebApp", url="https://joinbitten.com")]
    ]
    
    await update.message.reply_text(
        """🎯 **INTEL COMMAND CENTER**
*Elite Tactical Trading System*

**OPERATIONAL STATUS**: ✅ ONLINE
**SIGNAL ENGINE**: ✅ APEX v5.0 ACTIVE
**MARKET CONDITIONS**: 📈 FAVORABLE

Select your mission objective:""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    
    print(f"🔍 CALLBACK RECEIVED: {query.data} from user {query.from_user.username}")
    
    try:
        if query.data == "nav_field_manual":
            keyboard = [
                [InlineKeyboardButton("🚀 Boot Camp", callback_data="show_manual_getting_started")],
                [InlineKeyboardButton("🌐 WebApp Setup", callback_data="show_manual_webapp_setup")],
                [InlineKeyboardButton("⬅️ Back to Main", callback_data="nav_main")]
            ]
            await query.edit_message_text(
                """📚 **FIELD MANUAL**
*Complete guides and tutorials*

Select your training guide:""",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data == "nav_analytics":
            keyboard = [
                [InlineKeyboardButton("📊 Performance Stats", callback_data="show_analytics_performance")],
                [InlineKeyboardButton("🎯 Win Rate Analysis", callback_data="show_analytics_winrate")],
                [InlineKeyboardButton("⬅️ Back to Main", callback_data="nav_main")]
            ]
            await query.edit_message_text(
                """📊 **BATTLE STATS**
*Performance analytics and insights*

Select your analytics:""",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data == "nav_main" or query.data == "main_menu":
            # Return to main BITTEN menu
            keyboard = [
                [InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
                 InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")],
                [InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
                 InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")],
                [InlineKeyboardButton("🎓 WAR COLLEGE", callback_data="menu_education"),
                 InlineKeyboardButton("🛠️ TACTICAL TOOLS", callback_data="menu_tools")],
                [InlineKeyboardButton("📊 BATTLE STATS", callback_data="menu_analytics"),
                 InlineKeyboardButton("👤 ACCOUNT OPS", callback_data="menu_account")],
                [InlineKeyboardButton("👥 SQUAD HQ", callback_data="menu_community"),
                 InlineKeyboardButton("🤖 BOT CONCIERGE", callback_data="menu_bot_concierge")],
                [InlineKeyboardButton("🔧 TECH SUPPORT", callback_data="menu_tech_support"),
                 InlineKeyboardButton("🚨 EMERGENCY", callback_data="menu_emergency")],
                [InlineKeyboardButton("🌐 Open WebApp", url="https://joinbitten.com")]
            ]
            await query.edit_message_text(
                """🎯 **INTEL COMMAND CENTER**
*Elite Tactical Trading System*

**OPERATIONAL STATUS**: ✅ ONLINE
**SIGNAL ENGINE**: ✅ APEX v5.0 ACTIVE
**MARKET CONDITIONS**: 📈 FAVORABLE

Select your mission objective:""",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif query.data.startswith("show_"):
            # Show content
            content_key = query.data.replace("show_", "")
            content = CONTENT.get(content_key, f"Content for {content_key}")
            
            await query.answer()  # Acknowledge callback
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=content,
                parse_mode=ParseMode.MARKDOWN
            )
            print(f"✅ Sent content for: {content_key}")
            
        elif query.data.startswith("menu_"):
            # Handle main BITTEN system menu patterns - DIRECT CONTENT
            content_key = query.data.replace("menu_", "")
            content = CONTENT.get(content_key, f"Content for {content_key} not found")
            
            # Add back to main menu button
            back_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back to Command Center", callback_data="main_menu")
            ]])
            
            await query.answer()  # Acknowledge callback
            await query.edit_message_text(
                text=content,
                reply_markup=back_button,
                parse_mode=ParseMode.MARKDOWN
            )
            print(f"✅ Showed BITTEN content directly for: {content_key}")
            
        else:
            # Handle any unmatched callback patterns
            print(f"🔍 UNMATCHED CALLBACK: {query.data}")
            
            # Try to extract content based on common patterns
            if "_action_" in query.data:
                # Handle menu_action_* patterns
                content_key = query.data.split("_action_")[-1]
                content = CONTENT.get(content_key, f"Content for {content_key} not found")
                
                await query.answer()
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=content,
                    parse_mode=ParseMode.MARKDOWN
                )
                print(f"✅ Handled action pattern: {content_key}")
                
            elif "_nav_" in query.data:
                # Handle navigation patterns
                await query.answer("Navigation handled")
                print(f"✅ Handled nav pattern: {query.data}")
                
            else:
                # Default response with debug info
                await query.answer(f"Button received: {query.data}")
                print(f"❓ Unknown pattern: {query.data}")
            
    except Exception as e:
        print(f"❌ Error handling callback: {e}")
        await query.answer("❌ Error - please try again")

def main():
    """Main function"""
    print("🚀 Starting BITTEN Menu Bot...")
    print("🎯 Bot: @Bitten_Commander_bot")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Bot ready! Use /start to test menu buttons")
    print("📋 Menu buttons should now work properly!")
    
    # Run bot
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()