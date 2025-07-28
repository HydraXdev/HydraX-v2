#!/usr/bin/env python3
"""
BITTEN Bot with Integrated Intel Command Center
Complete bot with signals, menu system, and Easter eggs
"""

import os
import sys
import asyncio
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional, List

# Add the src path
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# BITTEN imports
try:
    from bitten_core.intel_command_center import IntelCommandCenter, handle_intel_command, handle_intel_callback
    from bitten_core.rank_access import UserRank
    INTEL_CENTER_AVAILABLE = True
except ImportError:
    print("⚠️ Intel Command Center not available - running in basic mode")
    INTEL_CENTER_AVAILABLE = False

import signal_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'
CHAT_ID = -1002581996861
USER_ID = 7176191872
WEBAPP_URL = 'https://joinbitten.com'

# Signal configuration  
SIGNAL_CONFIG = {
    'check_interval': 30,      # Check every 30 seconds
    'signal_chance': 0.15,     # 15% chance per check
    'cooldown_minutes': 5,     # 5 min cooldown per symbol
    'min_confidence': 70,      # Minimum TCS score
}

# Global state
bot_state = {
    'signals_active': True,    # ENABLED - Telegram alerts active
    'mode': 'AUTO',
    'signals_sent': 0,
    'start_time': datetime.now(),
    'last_signals': {},
    'data_source': 'SIMULATED'
}

# Initialize Intel Command Center
if INTEL_CENTER_AVAILABLE:
    intel_center = IntelCommandCenter(WEBAPP_URL)

class BITTENBot:
    """Main BITTEN bot with Intel Command Center integration"""
    
    def __init__(self):
        self.pairs = {
            'EURUSD': {'price': 1.0900, 'volatility': 0.0015},
            'GBPUSD': {'price': 1.2650, 'volatility': 0.0020},
            'USDJPY': {'price': 150.50, 'volatility': 0.15},
            'AUDUSD': {'price': 0.6550, 'volatility': 0.0012},
            'USDCAD': {'price': 1.3650, 'volatility': 0.0018}
        }
        
        # Easter egg responses
        self.easter_eggs = {
            'show me the money': "💰 **SECRET PROFIT VAULT UNLOCKED**\n\n🎯 Secret #1: The house always wins... we just make you feel like you're the house\n💎 Secret #2: Diamond hands are just paper hands that forgot how to sell\n🚀 Secret #3: Moon is actually just the friends we liquidated along the way",
            'norman lives': "🐱 *Norman purrs and knocks your phone off the table*\n\nNorman: 'Meow meow meow' (Translation: 'Stop revenge trading, human')",
            'diamond hands': "💎 **HODL THERAPY SESSION ACTIVATED**\n\n🎭 Welcome to Diamond Hands Anonymous\n📝 Step 1: Admit you have a problem with selling\n💪 Step 2: Believe that diamond hands can restore you to profitability\n🙏 Step 3: Turn your portfolio over to the care of the HODL gods",
            'wen lambo': "🏎️ **WEN LAMBO CALCULATOR**\n\n💰 Current Balance: $420.69\n🎯 Lambo Price: $200,000\n📈 Required Gain: 47,519%\n⏰ Time to Lambo: 69,420 years\n\n*Alternative: Buy Honda Civic now, pretend it's Lambo*",
            'number go up': "📈 **HOPIUM INJECTION ADMINISTERED**\n\n🚀 NUMBER WILL GO UP\n💎 DIAMOND HANDS ACTIVATED\n🌙 MOON MISSION ENGAGED\n🦍 APE MODE: ENABLED\n\n*Side effects may include: unrealistic expectations, FOMO, and lambo dreams*",
            'trust the process': "🧠 **ZEN MODE ACTIVATED**\n\n☯️ The market is not your enemy, your emotions are\n🎯 Trust the process, respect the journey\n💭 What you seek is seeking you... (hopefully profits)",
            'the cake is a lie': "🍰 **PORTAL MODE ACTIVATED**\n\n🔬 Aperture Trading Laboratory\n🤖 GLaDOS: 'The enrichment center reminds you that your portfolio was a lie'\n🔥 This was a triumph... for the market makers",
            'bitten by the bug': "👨‍💻 **DEVELOPER SECRETS UNLOCKED**\n\n🐛 Bug Report: User has too much time on their hands\n💡 Feature Idea: Auto-delete account when they find easter eggs\n🤫 Insider Info: The algorithm is just Norman walking across the keyboard\n☕ Truth: 90% of trading success is just good coffee"
        }
    
    def update_prices(self):
        """Simulate price movements"""
        for symbol, data in self.pairs.items():
            change = random.uniform(-data['volatility'], data['volatility'])
            data['price'] = round(data['price'] + change, 5)
    
    def generate_signal(self) -> Optional[Dict]:
        """Generate a trading signal using ORIGINAL BITTEN SYSTEM"""
        self.update_prices()
        
        # Check each pair
        for symbol, data in self.pairs.items():
            # Check cooldown
            if symbol in bot_state['last_signals']:
                elapsed = time.time() - bot_state['last_signals'][symbol]
                if elapsed < SIGNAL_CONFIG['cooldown_minutes'] * 60:
                    continue
            
            # Random chance for signal
            if random.random() > SIGNAL_CONFIG['signal_chance']:
                continue
            
            # Generate signal with ORIGINAL SYSTEM - RAPID ASSAULT & SNIPER OPS
            rand = random.random()
            if rand < 0.15:  # 15% chance for SNIPER OPS
                signal_type = "SNIPER OPS"
                emoji = "⚡"
                tcs = random.randint(90, 96)
            else:  # 85% chance for RAPID ASSAULT
                signal_type = "RAPID ASSAULT"
                emoji = "🔫"
                tcs = random.randint(87, 94)
            
            # Direction and pricing
            direction = random.choice(['BUY', 'SELL'])
            entry_price = data['price']
            
            # Calculate SL and TP (risk/reward 1:1.8 to 1:2.5)
            pip_value = 0.0001 if 'JPY' not in symbol else 0.01
            sl_pips = random.randint(10, 25)
            tp_pips = random.randint(int(sl_pips * 1.8), int(sl_pips * 2.5))
            
            if direction == 'BUY':
                sl_price = entry_price - (sl_pips * pip_value)
                tp_price = entry_price + (tp_pips * pip_value)
            else:
                sl_price = entry_price + (sl_pips * pip_value)
                tp_price = entry_price - (tp_pips * pip_value)
            
            # Create signal
            signal = {
                'signal_id': f"SIG-{int(time.time())}",
                'symbol': symbol,
                'direction': direction,
                'entry_price': round(entry_price, 5),
                'sl_price': round(sl_price, 5),
                'tp_price': round(tp_price, 5),
                'sl_pips': sl_pips,
                'tp_pips': tp_pips,
                'tcs': tcs,
                'signal_type': signal_type,
                'emoji': emoji,
                'timestamp': datetime.now().isoformat(),
                'expires_in': 10  # 10 minutes
            }
            
            # Update cooldown
            bot_state['last_signals'][symbol] = time.time()
            
            return signal
        
        return None
    
    def format_signal_message(self, signal: Dict) -> str:
        """Format signal for Telegram using ORIGINAL BITTEN FORMAT"""
        # ORIGINAL SIGNAL TYPES FROM CLAUDE.MD - RESTORED
        if signal['signal_type'] == 'SNIPER OPS':
            message = f"{signal['emoji']} **SNIPER OPS [{signal['tcs']}%]**\n"
        else:
            message = f"{signal['emoji']} **RAPID ASSAULT [{signal['tcs']}%]**\n"
        
        message += f"{signal['symbol']} {signal['direction']} @ {signal['entry_price']}\n"
        message += f"SL: {signal['sl_pips']}p | TP: {signal['tp_pips']}p"
        
        return message

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """🎯 **BITTEN TACTICAL TRADING SYSTEM**

*Welcome to the battlefield, Operative.*

Your Intel Command Center is now online with:

✅ **12+ Menu Categories** - Everything you need
✅ **Easter Egg System** - Hidden secrets to discover  
✅ **Norman Integration** - Chat with the legendary cat
✅ **Signal System** - Live trading alerts
✅ **Multiple Access Methods** - Always available

🔍 **Try secret phrases:**
• 'show me the money'
• 'norman lives' 
• 'diamond hands'
• 'wen lambo'

📋 **Access Intel Center:**
• Menu button (📋) next to message input
• /menu or /intel commands
• Type 'menu' or 'help'
• Keyboard shortcuts below"""
    
    # Create persistent keyboard
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("📋 INTEL CENTER"), KeyboardButton("📊 STATS")],
        [KeyboardButton("🔫 SIGNALS"), KeyboardButton("🛠️ TOOLS")],
        [KeyboardButton("🚨 EMERGENCY"), KeyboardButton("🐱 NORMAN")]
    ], resize_keyboard=True)
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu, /intel commands"""
    if not INTEL_CENTER_AVAILABLE:
        await update.message.reply_text("⚠️ Intel Command Center temporarily unavailable")
        return
    
    # Get user rank (simplified for demo)
    user_rank = UserRank.NIBBLER  # Would be fetched from database
    
    # Use Intel Command Center
    result = handle_intel_command(update.effective_user.id, user_rank)
    
    await update.message.reply_text(
        result.message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=result.data.get('reply_markup')
    )

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Intel Command Center menu callbacks"""
    if not INTEL_CENTER_AVAILABLE:
        await update.callback_query.answer("Intel Command Center unavailable")
        return
    
    query = update.callback_query
    user_rank = UserRank.NIBBLER  # Would be fetched from database
    
    # Debug: Log the callback data
    print(f"🔍 DEBUG: Menu callback received: {query.data}")
    
    try:
        result = handle_intel_callback(query.data, query.from_user.id, user_rank)
        print(f"🔍 DEBUG: Result: {result}")
    except Exception as e:
        print(f"❌ DEBUG: Error handling callback: {e}")
        await query.answer("❌ Menu error - please try again")
        return
    
    if result.get('action') == 'edit_message':
        await query.edit_message_text(
            text=result['text'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=result.get('reply_markup')
        )
    elif result.get('action') == 'answer_callback':
        await query.answer(result['text'], show_alert=result.get('show_alert', False))
    elif result.get('action') == 'send_message':
        await query.answer()  # Acknowledge the callback
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=result['text'],
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle action button callbacks (qf_, an_, sh_, sn_, in_, unlock_, etc.)"""
    query = update.callback_query
    
    # Debug: Log the callback data
    print(f"🔍 DEBUG: Action callback received: {query.data}")
    
    try:
        # Import telegram router for handling actions
        from bitten_core.telegram_router import TelegramRouter
        
        # Create router instance
        router = TelegramRouter()
        
        # Simulate callback query structure expected by router
        callback_data = {
            'data': query.data,
            'from': {
                'id': query.from_user.id,
                'username': query.from_user.username or 'Unknown'
            }
        }
        
        # Handle the callback
        result = router.handle_callback_query(callback_data)
        
        if result.success:
            # Handle different response types
            if result.data and result.data.get('callback_answer'):
                # Simple callback answer
                await query.answer(
                    result.message,
                    show_alert=result.data.get('show_alert', False)
                )
            elif result.data and result.data.get('reply_markup'):
                # Edit message with new markup
                await query.edit_message_text(
                    text=result.message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=result.data['reply_markup']
                )
            elif result.data and result.data.get('edit_message'):
                # Edit message without markup
                await query.edit_message_text(
                    text=result.message,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif result.data and result.data.get('delete_message'):
                # Delete the message
                await query.delete_message()
            else:
                # Send new message
                await query.answer()
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=result.message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=result.data.get('reply_markup') if result.data else None
                )
        else:
            await query.answer(f"❌ {result.message}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling action callback: {e}")
        await query.answer("❌ Action failed - please try again", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    message_text = update.message.text.lower().strip()
    
    # Check for easter eggs
    bitten_bot = BITTENBot()
    if message_text in bitten_bot.easter_eggs:
        response = bitten_bot.easter_eggs[message_text]
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Handle menu keywords
    if message_text in ['menu', 'intel', 'help', '📋 intel center']:
        await menu_command(update, context)
        return
    
    # Handle other keywords
    keyword_responses = {
        'norman': "🐱 Norman appears and stares at you judgmentally...",
        'signals': f"📡 Signals: {'ACTIVE' if bot_state['signals_active'] else 'DISABLED'}\n📊 Sent today: {bot_state['signals_sent']}",
        'status': f"🤖 BITTEN Bot Status: ONLINE\n📡 Signals: {'ACTIVE' if bot_state['signals_active'] else 'DISABLED'}\n🎯 Intel Center: {'ONLINE' if INTEL_CENTER_AVAILABLE else 'OFFLINE'}",
        'ping': "🏓 Pong! Bot is responsive."}
    
    if message_text in keyword_responses:
        await update.message.reply_text(keyword_responses[message_text])

async def signal_loop(app):
    """Background task to generate and send signals"""
    bitten_bot = BITTENBot()
    
    while True:
        try:
            if bot_state['signals_active']:
                signal = bitten_bot.generate_signal()
                
                if signal:
                    # Store signal
                    signal_storage.save_signal('global', signal)
                    
                    # Format message
                    message = bitten_bot.format_signal_message(signal)
                    
                    # Create WebApp button for mission briefing
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "🎯 MISSION BRIEF",
                            web_app=WebAppInfo(url=f"{WEBAPP_URL}/hud?signal={signal['signal_id']}")
                        )
                    ]])
                    
                    # Send signal
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                    
                    bot_state['signals_sent'] += 1
                    logger.info(f"Signal sent: {signal['symbol']} {signal['direction']}")
            
            await asyncio.sleep(SIGNAL_CONFIG['check_interval'])
            
        except Exception as e:
            logger.error(f"Signal loop error: {e}")
            await asyncio.sleep(30)

async def main():
    """Main bot function"""
    print("🎯 STARTING BITTEN BOT WITH INTEL COMMAND CENTER")
    print("=" * 60)
    print(f"🤖 Bot Status: ACTIVE")
    print(f"📡 Signals: {'ENABLED' if bot_state['signals_active'] else 'DISABLED'}")
    print(f"🎮 Intel Center: {'ENABLED' if INTEL_CENTER_AVAILABLE else 'DISABLED'}")
    print(f"🎯 Chat ID: {CHAT_ID}")
    print("")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["menu", "intel"], menu_command))
    app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^menu_"))
    app.add_handler(CallbackQueryHandler(handle_action_callback, pattern=r"^(qf_|an_|sh_|sn_|in_|unlock_|copy_|upgrade_|tier_info_|emergency_|recover_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start background tasks
    asyncio.create_task(signal_loop(app))
    
    # Start bot
    print("🚀 Bot starting...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")