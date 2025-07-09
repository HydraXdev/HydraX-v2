#!/usr/bin/env python3
"""Clean signal bot with simplified alerts and improved UX"""

import asyncio
import json
import random
import time
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = '-1002581996861'
WEBAPP_URL = 'http://134.199.204.67:8888'

class CleanSignalBot:
    """Simplified signal bot with clean alerts"""
    
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
        # Market pairs
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 
                      'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP']
    
    def setup_handlers(self):
        """Set up command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("menu", self.cmd_menu))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command with main menu"""
        user = update.effective_user
        
        welcome_message = f"""🎯 **Welcome to BITTEN, {user.first_name}!**

Ready for combat? Your mission awaits.

Use /menu to access command center."""
        
        keyboard = [
            [
                InlineKeyboardButton("📡 Signals", callback_data="menu_signals"),
                InlineKeyboardButton("📊 Stats", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton("🎓 Training", callback_data="menu_training"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        keyboard = [
            [
                InlineKeyboardButton("📡 Signals", callback_data="menu_signals"),
                InlineKeyboardButton("📊 Stats", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton("🎓 Training", callback_data="menu_training"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = """🎯 **BITTEN Command Center**

What's your mission, soldier?"""
        
        if update.message:
            await update.message.reply_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """📖 **BITTEN Help**

**Commands:**
/menu - Open main menu
/stats - View your statistics
/help - Show this help

**Signal Types:**
🔥 SNIPER (90%+) - Highest confidence
⭐ PRECISION (80-89%) - High confidence
✅ STANDARD (70-79%) - Good opportunity

**Remember:** Quality over quantity!"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stats command"""
        # Placeholder stats
        stats_text = """📊 **Your Stats**

Tier: NIBBLER
Level: 5
XP: 1,250

Today: 3/6 trades
Win Rate: 75%
P&L: +2.4%"""
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "menu_signals":
            text = "📡 **Signal Status**\n\nMonitoring markets...\nNext check in 30s"
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif query.data == "menu_stats":
            await self.cmd_stats(query, context)
        
        elif query.data == "menu_training":
            keyboard = [[InlineKeyboardButton("📚 Open Training", url=f"{WEBAPP_URL}/education/nibbler")]]
            await query.edit_message_text(
                "🎓 **Training Academy**\n\nLevel up your skills!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif query.data == "menu_settings":
            text = "⚙️ **Settings**\n\nComing soon..."
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif query.data == "menu_help":
            await self.cmd_help(query, context)
    
    def generate_signal(self):
        """Generate a clean signal"""
        symbol = random.choice(self.pairs)
        direction = random.choice(['BUY', 'SELL'])
        
        # TCS distribution
        tcs_ranges = [
            (90, 95, 'SNIPER'),      # 10% chance
            (80, 89, 'PRECISION'),   # 30% chance
            (70, 79, 'STANDARD')     # 60% chance
        ]
        
        # Select range based on probability
        rand = random.random()
        if rand < 0.1:
            tcs_range = tcs_ranges[0]
        elif rand < 0.4:
            tcs_range = tcs_ranges[1]
        else:
            tcs_range = tcs_ranges[2]
        
        tcs_score = random.randint(tcs_range[0], tcs_range[1])
        signal_type = tcs_range[2]
        
        # Generate price data
        if 'JPY' in symbol:
            base_price = random.uniform(100, 150)
            pip_value = 0.01
        else:
            base_price = random.uniform(0.8, 1.5)
            pip_value = 0.0001
        
        entry = round(base_price + random.uniform(-0.01, 0.01), 5)
        sl_pips = random.randint(15, 25)
        tp_pips = sl_pips * random.uniform(1.5, 3.0)
        
        if direction == 'BUY':
            sl = entry - (sl_pips * pip_value)
            tp = entry + (tp_pips * pip_value)
        else:
            sl = entry + (sl_pips * pip_value)
            tp = entry - (tp_pips * pip_value)
        
        return {
            'id': f"SIG-{int(time.time()*1000)}",
            'symbol': symbol,
            'direction': direction,
            'tcs_score': tcs_score,
            'signal_type': signal_type,
            'entry': entry,
            'sl': round(sl, 5),
            'tp': round(tp, 5),
            'sl_pips': sl_pips,
            'tp_pips': int(tp_pips),
            'rr_ratio': round(tp_pips / sl_pips, 1),
            'timestamp': datetime.now().isoformat(),
            'expiry': 600  # 10 minutes
        }
    
    async def send_signal(self, signal):
        """Send clean signal to Telegram"""
        # Clean, minimal format
        if signal['tcs_score'] >= 90:
            message = f"🔥 **{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}%"
        elif signal['tcs_score'] >= 80:
            message = f"⭐ **{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}%"
        else:
            message = f"✅ {signal['symbol']} {signal['direction']} | {signal['tcs_score']}%"
        
        # Prepare webapp data
        webapp_data = {
            'mission_id': signal['id'],
            'signal': signal,
            'timestamp': int(time.time())
        }
        
        import urllib.parse
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        webapp_url = f"{WEBAPP_URL}/hud?data={encoded_data}"
        
        # Single button
        keyboard = [[InlineKeyboardButton("View Intel →", url=webapp_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message
        await self.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"Signal sent: {signal['symbol']} {signal['direction']} @ {signal['tcs_score']}%")
    
    async def signal_generator(self):
        """Background task to generate signals"""
        await asyncio.sleep(5)  # Initial delay
        
        # Send startup message
        await self.bot.send_message(
            chat_id=CHAT_ID,
            text="🟢 **Signal Engine Online**\n\nMonitoring markets...",
            parse_mode='Markdown'
        )
        
        while True:
            # Check every 30 seconds
            await asyncio.sleep(30)
            
            # 15% chance of signal
            if random.random() < 0.15:
                signal = self.generate_signal()
                await self.send_signal(signal)
    
    async def start(self):
        """Start the bot"""
        # Initialize
        await self.app.initialize()
        await self.app.start()
        
        # Start signal generator
        asyncio.create_task(self.signal_generator())
        
        # Start polling
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("Clean signal bot started")
        
        # Keep running
        while True:
            await asyncio.sleep(1)

async def main():
    """Main entry point"""
    bot = CleanSignalBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

if __name__ == '__main__':
    asyncio.run(main())