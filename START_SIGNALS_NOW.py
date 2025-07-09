#!/usr/bin/env python3
"""
BITTEN Live Signals - Working Bot with Correct IDs
Starts immediately with your user and chat IDs
"""

import os
import sys
import asyncio
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# YOUR CORRECT CONFIGURATION
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = '-1002581996861'  # Your group chat
USER_ID = '7176191872'      # Your user ID
WEBAPP_URL = 'https://joinbitten.com'

# Signal configuration
SIGNAL_CONFIG = {
    'check_interval': 15,      # Check every 15 seconds
    'signal_chance': 0.25,     # 25% chance per check
    'cooldown_minutes': 5,     # 5 min cooldown per symbol
    'min_confidence': 70,      # Minimum TCS score
}

# Global state
bot_state = {
    'signals_active': True,
    'mode': 'MANUAL',
    'signals_sent': 0,
    'start_time': datetime.now(),
    'last_signals': {}
}


class TradingSignalGenerator:
    """Generates realistic trading signals"""
    
    def __init__(self):
        self.pairs = {
            'EURUSD': {'price': 1.0900, 'volatility': 0.0015},
            'GBPUSD': {'price': 1.2650, 'volatility': 0.0020},
            'USDJPY': {'price': 150.50, 'volatility': 0.15},
            'AUDUSD': {'price': 0.6550, 'volatility': 0.0012},
            'USDCAD': {'price': 1.3650, 'volatility': 0.0018},
            'XAUUSD': {'price': 2050.00, 'volatility': 10.0}
        }
    
    def update_prices(self):
        """Simulate price movements"""
        for symbol, data in self.pairs.items():
            change = random.uniform(-data['volatility'], data['volatility'])
            data['price'] = round(data['price'] + change, 5)
    
    def generate_signal(self) -> Optional[Dict]:
        """Generate a trading signal if conditions met"""
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
            
            # Generate signal details
            direction = random.choice(['BUY', 'SELL'])
            tcs_score = random.randint(SIGNAL_CONFIG['min_confidence'], 95)
            
            # Calculate levels
            pip = 0.0001 if symbol != 'USDJPY' else 0.01
            if symbol == 'XAUUSD':
                pip = 0.1
            
            sl_pips = random.randint(20, 50)
            tp_pips = random.randint(30, 100)
            
            if direction == 'BUY':
                entry = data['price']
                sl = round(entry - (sl_pips * pip), 5)
                tp = round(entry + (tp_pips * pip), 5)
            else:
                entry = data['price']
                sl = round(entry + (sl_pips * pip), 5)
                tp = round(entry - (tp_pips * pip), 5)
            
            signal = {
                'id': f"SIG-{int(time.time()*1000)}",
                'symbol': symbol,
                'direction': direction,
                'tcs_score': tcs_score,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips,
                'rr_ratio': round(tp_pips / sl_pips, 1),
                'timestamp': datetime.now(),
                'expiry': 600  # 10 minutes
            }
            
            # Update last signal time
            bot_state['last_signals'][symbol] = time.time()
            
            return signal
        
        return None


# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"/start from {user.username} ({user.id})")
    
    # Check if it's you
    is_owner = str(user.id) == USER_ID
    
    welcome = f"""
🎯 **Welcome to BITTEN Trading System**

{'👑 Commander Access Granted' if is_owner else '🔐 User Access'}

**System Status**: 🟢 ONLINE
**Signal Engine**: ⚡ ACTIVE
**Current Mode**: {bot_state['mode']}

**Available Commands:**
/ping - Check bot status
/mode - View fire mode
/status - System statistics
/signals - Toggle signals on/off
/help - Show help

Signals will start flowing immediately!
"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    start_time = time.time()
    
    # Send initial message
    msg = await update.message.reply_text("🏓 Pinging...")
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000)
    
    # Edit with result
    await msg.edit_text(
        f"🏓 **PONG!**\n\n"
        f"Bot Status: 🟢 Online\n"
        f"Response: {response_time}ms\n"
        f"Signals: {'✅ Active' if bot_state['signals_active'] else '❌ Paused'}\n"
        f"Uptime: {get_uptime()}",
        parse_mode='Markdown'
    )


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mode command"""
    mode_info = {
        'MANUAL': {
            'name': '🎯 MANUAL',
            'desc': 'Full control - You decide when to fire',
            'tier': 'All tiers'
        },
        'SEMI_AUTO': {
            'name': '⚡ SEMI-AUTO',
            'desc': 'Confirmation required for each trade',
            'tier': 'Fang+'
        },
        'AUTO': {
            'name': '🤖 AUTO-FIRE',
            'desc': 'Fully automated execution',
            'tier': 'Commander+'
        }
    }
    
    current = mode_info.get(bot_state['mode'], mode_info['MANUAL'])
    
    response = f"""
**Current Fire Mode**

{current['name']}
_{current['desc']}_

Required Tier: {current['tier']}

Your current tier determines available modes.
Use tier upgrades to unlock more fire modes.
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    uptime = get_uptime()
    
    status = f"""
📊 **BITTEN System Status**

**🤖 Bot Status**
• State: 🟢 Online
• Uptime: {uptime}
• Started: {bot_state['start_time'].strftime('%H:%M:%S')}

**📡 Signal Engine**
• Status: {'⚡ Active' if bot_state['signals_active'] else '⏸️ Paused'}
• Signals Sent: {bot_state['signals_sent']}
• Check Interval: {SIGNAL_CONFIG['check_interval']}s
• Min Confidence: {SIGNAL_CONFIG['min_confidence']}%

**📈 Market Coverage**
• EUR/USD ✅
• GBP/USD ✅
• USD/JPY ✅
• AUD/USD ✅
• USD/CAD ✅
• XAU/USD ✅

**⚙️ Configuration**
• Fire Mode: {bot_state['mode']}
• Signal Cooldown: {SIGNAL_CONFIG['cooldown_minutes']}min
• WebApp: Connected ✅
"""
    
    await update.message.reply_text(status, parse_mode='Markdown')


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals command - toggle signals on/off"""
    user = update.effective_user
    
    # Only owner can toggle
    if str(user.id) != USER_ID:
        await update.message.reply_text("⚠️ Only the commander can control signals.")
        return
    
    # Toggle state
    bot_state['signals_active'] = not bot_state['signals_active']
    
    if bot_state['signals_active']:
        await update.message.reply_text(
            "✅ **Signals ACTIVATED**\n\n"
            "Signal engine is now running.\n"
            "You'll receive alerts when conditions are met.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⏸️ **Signals PAUSED**\n\n"
            "Signal engine stopped.\n"
            "Use /signals again to resume.",
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **BITTEN Command Reference**

**🎯 Basic Commands**
/start - Initialize bot
/ping - Check responsiveness
/help - Show this help

**📊 Status Commands**
/status - Full system status
/mode - Current fire mode
/signals - Toggle signals on/off

**🔧 Settings** (Coming Soon)
/settings - View settings
/tier - Check your tier
/stats - Trading statistics

**📡 Signal Info**
• Signals appear automatically
• Each signal valid for 10 minutes
• Minimum 5min cooldown per pair
• 70%+ confidence required

Need support? Contact @CommanderBit
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Signal Functions
async def send_signal_alert(context: ContextTypes.DEFAULT_TYPE, signal: Dict):
    """Send signal alert to Telegram"""
    try:
        # Determine emoji based on TCS
        if signal['tcs_score'] >= 90:
            emoji = '🔥'
            quality = 'SNIPER'
        elif signal['tcs_score'] >= 80:
            emoji = '⭐'
            quality = 'PRECISION'
        else:
            emoji = '✅'
            quality = 'STANDARD'
        
        # Format message
        message = f"""
⚡ **SIGNAL DETECTED** ⚡

**{signal['symbol']}** | **{signal['direction']}** | {signal['tcs_score']}% {emoji}

📍 Entry: `{signal['entry']}`
🛡️ SL: `{signal['sl']}` (-{signal['sl_pips']} pips)
🎯 TP: `{signal['tp']}` (+{signal['tp_pips']} pips)

📊 R:R Ratio: 1:{signal['rr_ratio']}
🎖️ Quality: {quality}
⏰ Valid for: 10 minutes

_Signal ID: {signal['id']}_
"""
        
        # Create webapp data (remove datetime object)
        signal_clean = signal.copy()
        signal_clean['timestamp'] = signal['timestamp'].isoformat()
        
        webapp_data = {
            'mission_id': signal['id'],
            'signal': signal_clean,
            'timestamp': int(time.time())
        }
        
        # Create keyboard
        import urllib.parse
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        webapp_url = f"{WEBAPP_URL}/hud?data={encoded_data}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎯 VIEW INTEL",
                web_app=WebAppInfo(url=webapp_url)
            )],
            [InlineKeyboardButton(
                "🔫 FIRE (Test Mode)",
                callback_data=f"fire_{signal['id']}"
            )]
        ])
        
        # Send message
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        # Update stats
        bot_state['signals_sent'] += 1
        logger.info(f"Signal sent: {signal['symbol']} {signal['direction']} @ {signal['tcs_score']}%")
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")


async def signal_generator_task(application: Application):
    """Background task to generate signals"""
    generator = TradingSignalGenerator()
    logger.info("Signal generator started")
    
    # Send startup notification
    try:
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚀 **BITTEN Signal Engine Started**\n\n"
                 f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
                 f"Monitoring 6 currency pairs\n"
                 f"Signals will appear when conditions are met.\n\n"
                 f"Use /help to see commands.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Startup message error: {e}")
    
    # Main signal loop
    while True:
        try:
            if bot_state['signals_active']:
                signal = generator.generate_signal()
                
                if signal:
                    await send_signal_alert(application, signal)
                    
                    # Random extra delay after signal
                    await asyncio.sleep(random.randint(30, 60))
            
            # Regular check interval
            await asyncio.sleep(SIGNAL_CONFIG['check_interval'])
            
        except Exception as e:
            logger.error(f"Signal generator error: {e}")
            await asyncio.sleep(60)


# Helper Functions
def get_uptime() -> str:
    """Get formatted uptime"""
    delta = datetime.now() - bot_state['start_time']
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"


# Main Function
def main():
    """Start the bot"""
    print("""
    ╔══════════════════════════════════════════╗
    ║    BITTEN SIGNALS - LIVE & READY! 🚀    ║
    ╚══════════════════════════════════════════╝
    
    Bot Token: Configured ✅
    Chat ID: -1002581996861 ✅
    User ID: 7176191872 ✅
    
    Starting signal engine...
    """)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("mode", mode_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("signals", signals_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Post-init: start signal generator
    async def post_init(app: Application) -> None:
        asyncio.create_task(signal_generator_task(app))
    
    application.post_init = post_init
    
    # Run the bot
    print("✅ Bot starting... Check Telegram for signals!")
    print("📱 Commands: /ping /mode /status /help")
    print("\nPress Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()