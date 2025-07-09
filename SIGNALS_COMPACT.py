#!/usr/bin/env python3
"""
BITTEN Signals - Compact Alerts Edition
2-line alerts with clear visual differentiation
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

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = '-1002581996861'
USER_ID = '7176191872'
WEBAPP_URL = 'https://joinbitten.com'

# Signal configuration
SIGNAL_CONFIG = {
    'check_interval': 20,      # Check every 20 seconds
    'signal_chance': 0.20,     # 20% chance per check
    'cooldown_minutes': 5,     # 5 min cooldown per symbol
    'min_confidence': 70,      # Minimum TCS score
}

# Forex pairs only (no gold)
FOREX_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

# Global state
bot_state = {
    'signals_active': True,
    'mode': 'MANUAL',
    'signals_sent': 0,
    'start_time': datetime.now(),
    'last_signals': {},
    'data_source': 'SIMULATED'  # Will be 'LIVE' when using real data
}


class CompactSignalGenerator:
    """Generates trading signals with simulated forex data"""
    
    def __init__(self):
        # Forex pairs only
        self.pairs = {
            'EURUSD': {'price': 1.0900, 'volatility': 0.0015},
            'GBPUSD': {'price': 1.2650, 'volatility': 0.0020},
            'USDJPY': {'price': 150.50, 'volatility': 0.15},
            'AUDUSD': {'price': 0.6550, 'volatility': 0.0012},
            'USDCAD': {'price': 1.3650, 'volatility': 0.0018}
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
            
            # Generate signal with weighted TCS distribution
            # 10% chance for SNIPER (90-95)
            # 30% chance for PRECISION (80-89)
            # 60% chance for STANDARD (70-79)
            rand = random.random()
            if rand < 0.10:
                tcs_score = random.randint(90, 95)
                signal_type = 'SNIPER'
            elif rand < 0.40:
                tcs_score = random.randint(80, 89)
                signal_type = 'PRECISION'
            else:
                tcs_score = random.randint(70, 79)
                signal_type = 'STANDARD'
            
            direction = random.choice(['BUY', 'SELL'])
            
            # Calculate levels
            pip = 0.0001 if symbol != 'USDJPY' else 0.01
            
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
                'signal_type': signal_type,
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
    
    is_owner = str(user.id) == USER_ID
    
    welcome = f"""
🎯 **BITTEN Trading System**
Bot-Integrated Tactical Trading Engine

**Status**: 🟢 ONLINE
**Signals**: ⚡ ACTIVE
**Mode**: {bot_state['mode']}

Commands: /ping /mode /status /help

Compact signal alerts activated!
"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    
    response_time = round((time.time() - start_time) * 1000)
    
    await msg.edit_text(
        f"🏓 **PONG!** {response_time}ms | "
        f"Signals: {'✅' if bot_state['signals_active'] else '❌'} | "
        f"Uptime: {get_uptime()}"
    )


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mode command"""
    modes = {
        'MANUAL': '🎯 MANUAL - You control firing',
        'SEMI_AUTO': '⚡ SEMI-AUTO - Confirm each trade',
        'AUTO': '🤖 AUTO - Fully automated'
    }
    
    response = f"**Fire Mode**: {bot_state['mode']}\n{modes.get(bot_state['mode'], 'Unknown')}"
    await update.message.reply_text(response, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    uptime = get_uptime()
    
    # Get active pairs string
    active_pairs = ", ".join(FOREX_PAIRS)
    
    status = f"""
📊 **BITTEN Status**

**System**
• Status: 🟢 Online
• Uptime: {uptime}
• Mode: {bot_state['mode']}

**Signals**
• Engine: {'⚡ Active' if bot_state['signals_active'] else '⏸️ Paused'}
• Sent Today: {bot_state['signals_sent']}
• Data: {bot_state['data_source']} (Live MT5 feed coming soon)

**Market Coverage**
• Pairs: {active_pairs}
• Check Rate: Every {SIGNAL_CONFIG['check_interval']}s
• Min TCS: {SIGNAL_CONFIG['min_confidence']}%
"""
    
    await update.message.reply_text(status, parse_mode='Markdown')


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals command - toggle signals on/off"""
    user = update.effective_user
    
    if str(user.id) != USER_ID:
        await update.message.reply_text("⚠️ Only commander can control signals")
        return
    
    bot_state['signals_active'] = not bot_state['signals_active']
    
    status = "✅ ON" if bot_state['signals_active'] else "⏸️ OFF"
    await update.message.reply_text(f"Signals: {status}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **Commands**
/ping - Check bot
/status - System info
/mode - Fire mode
/signals - Toggle on/off
/help - This help

**Signal Types**
🔥 90%+ = SNIPER (rare)
⭐ 80-89% = PRECISION
✅ 70-79% = STANDARD
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Compact Signal Alert
async def send_signal_alert(context: ContextTypes.DEFAULT_TYPE, signal: Dict):
    """Send COMPACT signal alert to Telegram"""
    try:
        # Visual differentiation based on signal type
        if signal['signal_type'] == 'SNIPER':
            # SNIPER: Bold, fire emojis, caps
            line1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥"
            line2 = f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | ⏰ 10min"
            button_text = "🎯 SNIPER INTEL"
        
        elif signal['signal_type'] == 'PRECISION':
            # PRECISION: Star emoji, mixed case
            line1 = f"⭐ **Precision Strike** ⭐"
            line2 = f"{signal['symbol']} {signal['direction']} | {signal['tcs_score']}% confidence | ⏰ 10min"
            button_text = "⭐ VIEW INTEL"
        
        else:  # STANDARD (Nibbler)
            # STANDARD: Simple, no bold
            line1 = f"✅ Signal: {signal['symbol']} {signal['direction']} | {signal['tcs_score']}%"
            line2 = f"⏰ Expires in 10 minutes"
            button_text = "📋 VIEW DETAILS"
        
        # Combine into 2-line message
        message = f"{line1}\n{line2}"
        
        # Create webapp button
        signal_clean = signal.copy()
        signal_clean['timestamp'] = signal['timestamp'].isoformat()
        
        webapp_data = {
            'mission_id': signal['id'],
            'signal': signal_clean,
            'timestamp': int(time.time())
        }
        
        import urllib.parse
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        webapp_url = f"{WEBAPP_URL}/hud?data={encoded_data}"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                button_text,
                web_app=WebAppInfo(url=webapp_url)
            )
        ]])
        
        # Send compact message
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        # Update stats
        bot_state['signals_sent'] += 1
        logger.info(f"Signal sent: {signal['symbol']} {signal['direction']} {signal['signal_type']} @ {signal['tcs_score']}%")
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")


async def signal_generator_task(application: Application):
    """Background task to generate signals"""
    generator = CompactSignalGenerator()
    logger.info("Signal generator started")
    
    # Send startup notification
    try:
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚀 **BITTEN Started** | Monitoring {len(FOREX_PAIRS)} forex pairs | Compact alerts ON",
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
                    
                    # Variable delay after signal
                    delay = random.randint(30, 90)
                    await asyncio.sleep(delay)
            
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
    ║   BITTEN SIGNALS - COMPACT EDITION 🎯    ║
    ╚══════════════════════════════════════════╝
    
    Features:
    • 2-line compact alerts
    • Visual signal differentiation
    • Forex pairs only (no gold)
    • Simulated data (MT5 coming soon)
    
    Signal Types:
    🔥 SNIPER (90%+) - Rare, bold alerts
    ⭐ PRECISION (80-89%) - Quality signals  
    ✅ STANDARD (70-79%) - Regular signals
    
    Starting...
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
    print("✅ Bot starting with compact alerts...")
    print("📱 Watch Telegram for 2-line signals!")
    print("\nPress Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()