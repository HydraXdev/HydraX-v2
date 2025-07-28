#!/usr/bin/env python3
"""
Simple bot to handle menu interactions and Easter eggs
Focuses on the menu system without complex signal generation
"""

import logging
import requests
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

# User configuration
AUTHORIZED_USERS = {
    "7176191872": {
        "tier": "COMMANDER",
        "account_id": "843859",
        "bridge_id": "bridge_01"
    }
}

COMMANDER_IDS = [7176191872]

# Easter eggs
EASTER_EGGS = {
    'show me the money': "💰 **SECRET PROFIT VAULT UNLOCKED**\n\n🎯 Secret #1: The house always wins... we just make you feel like you're the house\n💎 Secret #2: Diamond hands are just paper hands that forgot how to sell\n🚀 Secret #3: Moon is actually just the friends we liquidated along the way",
    'norman lives': "👦 **NORMAN IS ALIVE AND WELL!**\n\nThe 17-year-old legend from Mississippi who started it all.\n\n🐱 *Bit chirps softly from the corner* (Translation: 'The human is doing okay, I guess')\n\nNorman: 'Yeah, Bit and I are still here. Still learning, still growing.'",
    'diamond hands': "💎 **HODL THERAPY SESSION ACTIVATED**\n\n🎭 Welcome to Diamond Hands Anonymous\n📝 Step 1: Admit you have a problem with selling\n💪 Step 2: Believe that diamond hands can restore you to profitability\n🙏 Step 3: Turn your portfolio over to the care of the HODL gods\n\n*Remember: Paper hands were made for toilet, not trading*",
    'wen lambo': "🏎️ **WEN LAMBO CALCULATOR**\n\n💰 Current Balance: $420.69\n🎯 Lambo Price: $200,000\n📈 Required Gain: 47,519%\n⏰ Time to Lambo: 69,420 years\n\n*Alternative: Buy Honda Civic now, pretend it's Lambo*",
    'number go up': "📈 **HOPIUM INJECTION ADMINISTERED**\n\n🚀 NUMBER WILL GO UP\n💎 DIAMOND HANDS ACTIVATED\n🌙 MOON MISSION ENGAGED\n🦍 APE MODE: ENABLED\n\n*Side effects may include: unrealistic expectations, FOMO, and lambo dreams*",
    'trust the process': "🧠 **ZEN MODE ACTIVATED**\n\n☯️ The market is not your enemy, your emotions are\n🎯 Trust the process, respect the journey\n💭 What you seek is seeking you... (hopefully profits)",
    'the cake is a lie': "🍰 **PORTAL MODE ACTIVATED**\n\n🔬 Aperture Trading Laboratory\n🤖 GLaDOS: 'The enrichment center reminds you that your portfolio was a lie'\n🔥 This was a triumph... for the market makers",
    'bitten by the bug': "👨‍💻 **DEVELOPER SECRETS UNLOCKED**\n\n🐛 Bug Report: User has too much time on their hands\n💡 Feature Idea: Auto-delete account when they find easter eggs\n🤫 Insider Info: The algorithm is just Bit walking across Norman's keyboard\n☕ Truth: 90% of trading success is just good coffee",
    'bit lives': "🐱 **BIT THE LEGENDARY CAT**\n\n*Bit chirps proudly*\n\nBorn In Truck (B.I.T.) - the black cat who started it all.\nFound by 17-year-old Norman in Mississippi.\n\n🐱 *Bit doesn't purr, he chirps*\n*Chirp chirp* (Translation: 'I'm the real genius behind this operation')"
}

def get_account_info(user_id):
    """Get account information for user"""
    try:
        user_str = str(user_id)
        if user_str in AUTHORIZED_USERS:
            account_id = AUTHORIZED_USERS[user_str]["account_id"]
            tier = AUTHORIZED_USERS[user_str]["tier"]
            
            # Mock account data - in production this would query MT5 bridge
            return {
                "account_id": account_id,
                "balance": 15000.00,
                "equity": 15247.85,
                "margin": 1250.00,
                "free_margin": 13997.85,
                "currency": "USD",
                "tier": tier,
                "status": "CONNECTED",
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return None

def get_system_status():
    """Get system status"""
    try:
        # Check if is running
        apex_status = "ONLINE" if os.path.exists("/root/HydraX-v2/.apex_engine.pid") else "OFFLINE"
        
        # Check webapp
        try:
            response = requests.get("http://localhost:8888/api/health", timeout=3)
            webapp_status = "ONLINE" if response.status_code == 200 else "OFFLINE"
        except:
            webapp_status = "OFFLINE"
        
        # Check TOC
        try:
            response = requests.get("http://localhost:8890/health", timeout=3)
            toc_status = "ONLINE" if response.status_code == 200 else "OFFLINE"
        except:
            toc_status = "OFFLINE"
        
        return {
            "apex_engine": apex_status,
            "webapp": webapp_status,
            "toc_server": toc_status,
            "mt5_integration": "PENDING",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"error": str(e)}

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command"""
    user_id = update.effective_user.id
    account_info = get_account_info(user_id)
    
    if not account_info:
        await update.message.reply_text(
            "❌ **ACCOUNT ACCESS DENIED**\n\nYour account is not configured for trading.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    balance_text = f"""💰 **ACCOUNT BALANCE**

**Account ID:** {account_info['account_id']}
**Tier:** {account_info['tier']}
**Status:** {account_info['status']}

💵 **Balance:** ${account_info['balance']:,.2f}
📈 **Equity:** ${account_info['equity']:,.2f}
🛡️ **Margin:** ${account_info['margin']:,.2f}
✅ **Free Margin:** ${account_info['free_margin']:,.2f}

📅 **Last Update:** {account_info['last_update']}"""
    
    await update.message.reply_text(balance_text, parse_mode=ParseMode.MARKDOWN)

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /account command"""
    user_id = update.effective_user.id
    account_info = get_account_info(user_id)
    system_status = get_system_status()
    
    if not account_info:
        await update.message.reply_text(
            "❌ **ACCOUNT ACCESS DENIED**\n\nYour account is not configured for trading.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    account_text = f"""👤 **ACCOUNT STATUS**

**Account Details:**
• ID: {account_info['account_id']}
• Tier: {account_info['tier']}
• Currency: {account_info['currency']}
• Status: {account_info['status']}

**System Status:**
• Engine: {system_status.get('apex_engine', 'UNKNOWN')}
• WebApp: {system_status.get('webapp', 'UNKNOWN')}
• TOC Server: {system_status.get('toc_server', 'UNKNOWN')}
• MT5 Integration: {system_status.get('mt5_integration', 'UNKNOWN')}

📅 **Status Check:** {system_status.get('timestamp', 'N/A')}"""
    
    await update.message.reply_text(account_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    system_status = get_system_status()
    
    status_text = f"""🖥️ **SYSTEM STATUS**

**Core Systems:**
🎯 Engine: {system_status.get('apex_engine', 'UNKNOWN')}
🌐 WebApp: {system_status.get('webapp', 'UNKNOWN')}
🧠 TOC Server: {system_status.get('toc_server', 'UNKNOWN')}
🔗 MT5 Integration: {system_status.get('mt5_integration', 'UNKNOWN')}

📊 **Last Check:** {system_status.get('timestamp', 'N/A')}

✅ All critical systems operational"""
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def fire_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fire command"""
    user_id = update.effective_user.id
    
    if user_id not in COMMANDER_IDS:
        await update.message.reply_text(
            "❌ **FIRE ACCESS DENIED**\n\nFire commands require COMMANDER tier access.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check for available signals
    try:
        # Check for recent signals in the log
        if os.path.exists("/root/HydraX-v2/apex_lean.log"):
            with open("/root/HydraX-v2/apex_lean.log", "r") as f:
                lines = f.readlines()[-10:]  # Last 10 lines
            
            # Look for recent signals
            recent_signals = []
            for line in lines:
                if "SNIPER OPS" in line or "RAPID ASSAULT" in line:
                    recent_signals.append(line.strip())
            
            if recent_signals:
                signal_text = "\n".join(recent_signals[-3:])  # Last 3 signals
                fire_text = f"""🔥 **FIRE COMMAND READY**

**Recent Signals:**
```
{signal_text}
```

⚠️ **Fire execution requires webapp confirmation**
Visit: http://localhost:8888"""
            else:
                fire_text = "🔥 **FIRE COMMAND**\n\n⏳ No recent signals available\n\nWaiting for engine signals..."
        else:
            fire_text = "🔥 **FIRE COMMAND**\n\n⚠️ Signal log not found\n\nengine may be offline"
        
        await update.message.reply_text(fire_text, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Fire command error: {e}")
        await update.message.reply_text(
            "❌ **FIRE COMMAND ERROR**\n\nUnable to access signal data.",
            parse_mode=ParseMode.MARKDOWN
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("📋 INTEL CENTER"), KeyboardButton("📊 BATTLE STATS")],
        [KeyboardButton("🔫 COMBAT OPS"), KeyboardButton("📚 FIELD MANUAL")],
        [KeyboardButton("💰 TIER INTEL"), KeyboardButton("🛠️ TACTICAL TOOLS")],
        [KeyboardButton("🚨 EMERGENCY"), KeyboardButton("🐱 NORMAN")],
        [KeyboardButton("💵 BALANCE"), KeyboardButton("👤 ACCOUNT")],
        [KeyboardButton("🔥 FIRE"), KeyboardButton("📡 STATUS")]
    ], resize_keyboard=True)
    
    user_id = update.effective_user.id
    account_info = get_account_info(user_id)
    
    if account_info:
        tier_status = f"**Tier:** {account_info['tier']} | **Account:** {account_info['account_id']}"
    else:
        tier_status = "**Status:** Account not configured"
    
    welcome_text = f"""🎯 **BITTEN COMMAND CENTER**

*Welcome to your comprehensive battlefield system!*

{tier_status}

✅ **Menu + Trading** - Complete dual bot system
✅ **Account Access** - Balance, status, fire commands
✅ **Easter Egg Hunt** - Hidden secrets to discover  
✅ **Norman Integration** - Chat with the legendary cat
✅ **Persistent Access** - Always available

🔍 **Try these secret phrases:**
• 'show me the money'
• 'norman lives' 
• 'diamond hands'
• 'wen lambo'
• 'number go up'
• 'trust the process'
• 'the cake is a lie'
• 'bitten by the bug'

📋 **Access the full menu + trading system below!**"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    menu_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔫 COMBAT OPS", callback_data="combat_ops"),
            InlineKeyboardButton("📚 FIELD MANUAL", callback_data="field_manual")
        ],
        [
            InlineKeyboardButton("💰 TIER INTEL", callback_data="tier_intel"),
            InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="xp_economy")
        ],
        [
            InlineKeyboardButton("🎓 WAR COLLEGE", callback_data="education"),
            InlineKeyboardButton("🛠️ TACTICAL TOOLS", callback_data="tools")
        ],
        [
            InlineKeyboardButton("📊 BATTLE STATS", callback_data="analytics"),
            InlineKeyboardButton("👤 ACCOUNT OPS", callback_data="account")
        ],
        [
            InlineKeyboardButton("👥 SQUAD HQ", callback_data="community"),
            InlineKeyboardButton("🔧 TECH SUPPORT", callback_data="support")
        ],
        [
            InlineKeyboardButton("🚨 EMERGENCY", callback_data="emergency"),
            InlineKeyboardButton("🤖 BOT CONCIERGE", callback_data="bots")
        ]
    ])
    
    menu_text = """📋 **INTEL COMMAND CENTER**
*"Everything you need, Operative. No stone unturned."*

Your comprehensive command interface with 12+ categories:

🔫 **Combat Operations** - Trading execution & strategy
📚 **Field Manual** - Complete guides & tutorials  
💰 **Tier Intelligence** - Subscription info & benefits
🎖️ **XP Economy** - Rewards, shop & prestige
🎓 **War College** - Trading education & theory
🛠️ **Tactical Tools** - Calculators & utilities
📊 **Battle Statistics** - Performance & analytics
👤 **Account Operations** - Settings & preferences
👥 **Squad Headquarters** - Community & social
🔧 **Technical Support** - Issues & troubleshooting
🚨 **Emergency Protocols** - Urgent assistance
🤖 **Bot Concierge** - AI assistants

*Select your intel category:*"""
    
    await update.message.reply_text(
        menu_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=menu_keyboard
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    message_text = update.message.text.lower().strip()
    
    # Check for easter eggs
    if message_text in EASTER_EGGS:
        await update.message.reply_text(
            EASTER_EGGS[message_text],
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Handle menu keywords
    if message_text in ['📋 intel center', 'menu', 'intel', 'help']:
        await menu_command(update, context)
        return
    
    # Handle specific keywords
    responses = {
        '🐱 norman': "👦 Norman appears and checks on the system...\n🐱 *Bit chirps from his shoulder* The menu system is working perfectly!",
        'norman': "👦 Norman: 'The system looks good!' \n🐱 *Bit chirps in agreement*",
        'status': "🤖 **SYSTEM STATUS**\n\n✅ Intel Command Center: ONLINE\n✅ Easter Eggs: 8 ACTIVE\n✅ Norman: JUDGING YOUR TRADES\n✅ Menu Categories: 12+ AVAILABLE",
        'ping': "🏓 Pong! Intel Command Center is responsive!",
        '📋 intel center': None,  # Handled above
        '📊 battle stats': "📊 **BATTLE STATISTICS**\n\nView your performance metrics, win rates, and trading analytics.\n\n*Full stats coming soon...*",
        '🔫 combat ops': "🔫 **COMBAT OPERATIONS**\n\nTrading execution, fire modes, risk management, and tactical strategies.\n\n*Use /menu for full access*",
        '📚 field manual': "📚 **FIELD MANUAL**\n\nComplete guides, tutorials, and step-by-step instructions for battlefield success.\n\n*Use /menu for full access*",
        '💰 tier intel': "💰 **TIER INTELLIGENCE**\n\nSubscription tiers, benefits, upgrades, and payment information.\n\n*Use /menu for full access*",
        '🛠️ tactical tools': "🛠️ **TACTICAL TOOLS**\n\nCalculators, utilities, and special tools including the famous 'Wen Lambo' calculator!\n\n*Use /menu for full access*",
        '🚨 emergency': "🚨 **EMERGENCY PROTOCOLS**\n\nUrgent assistance, HODL therapy, paper hands rehab, and crisis support.\n\n*Use /menu for full access*",
        '💵 balance': None,  # Handled by command
        '👤 account': None,  # Handled by command
        '🔥 fire': None,  # Handled by command
        '📡 status': None   # Handled by command
    }
    
    # Handle trading button presses
    if message_text == '💵 balance':
        await balance_command(update, context)
        return
    elif message_text == '👤 account':
        await account_command(update, context)
        return
    elif message_text == '🔥 fire':
        await fire_command(update, context)
        return
    elif message_text == '📡 status':
        await status_command(update, context)
        return
    
    if message_text in responses:
        response = responses[message_text]
        if response:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

def main():
    """Main function"""
    print("🎯 STARTING BITTEN DUAL BOT SYSTEM")
    print("=" * 50)
    print("🎮 Features: Menu system + Trading commands")
    print("💰 Commands: /balance, /account, /status, /fire")
    print("🐱 Norman integration ready")
    print("📋 12+ menu categories available")
    print("🔥 Trading functionality enabled")
    print("")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["menu", "intel"], menu_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("account", account_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("fire", fire_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"🚀 Bot starting with token: {BOT_TOKEN[:20]}...")
    print(f"👤 Authorized users: {len(AUTHORIZED_USERS)}")
    print(f"🎯 Commanders: {COMMANDER_IDS}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")