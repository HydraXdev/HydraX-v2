#!/usr/bin/env python3
"""
Simple bot to handle menu interactions and Easter eggs
Focuses on the menu system without complex signal generation
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("📋 INTEL CENTER"), KeyboardButton("📊 BATTLE STATS")],
        [KeyboardButton("🔫 COMBAT OPS"), KeyboardButton("📚 FIELD MANUAL")],
        [KeyboardButton("💰 TIER INTEL"), KeyboardButton("🛠️ TACTICAL TOOLS")],
        [KeyboardButton("🚨 EMERGENCY"), KeyboardButton("🐱 NORMAN")]
    ], resize_keyboard=True)
    
    welcome_text = """🎯 **BITTEN INTEL COMMAND CENTER**

*Welcome to your comprehensive battlefield menu system!*

✅ **12+ Menu Categories** - Every tool you need
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

📋 **Access the full menu system via the buttons below!**"""
    
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
        '🚨 emergency': "🚨 **EMERGENCY PROTOCOLS**\n\nUrgent assistance, HODL therapy, paper hands rehab, and crisis support.\n\n*Use /menu for full access*"
    }
    
    if message_text in responses:
        response = responses[message_text]
        if response:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

def main():
    """Main function"""
    print("🎯 STARTING SIMPLE INTEL COMMAND CENTER BOT")
    print("=" * 50)
    print("🎮 Features: Menu system + Easter eggs")
    print("🐱 Norman integration ready")
    print("📋 12+ menu categories available")
    print("")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["menu", "intel"], menu_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")