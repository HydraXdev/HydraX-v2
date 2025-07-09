#!/usr/bin/env python3
"""
BITTEN Signals with LIVE TraderMade Data
Compact alerts with real market prices
"""

import os
import sys
import asyncio
import logging
import json
import time
import random
import aiohttp
from datetime import datetime
from typing import Dict, Optional, List

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
TRADERMADE_API_KEY = 'iOxhauPWBb-xbxd9QgyR'  # Limited after 30 days on free plan

# Signal configuration
SIGNAL_CONFIG = {
    'check_interval': 30,      # Check every 30 seconds (be nice to API)
    'signal_chance': 0.15,     # 15% chance per check
    'cooldown_minutes': 5,     # 5 min cooldown per symbol
    'min_confidence': 70,      # Minimum TCS score
}

# Forex pairs to monitor
FOREX_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

# Global state
bot_state = {
    'signals_active': True,
    'mode': 'MANUAL',
    'signals_sent': 0,
    'start_time': datetime.now(),
    'last_signals': {},
    'data_source': 'LIVE (TraderMade)',
    'last_prices': {},
    'price_history': {}
}


class LiveMarketSignalGenerator:
    """Generates trading signals using live TraderMade data"""
    
    def __init__(self):
        self.api_key = TRADERMADE_API_KEY
        self.base_url = "https://marketdata.tradermade.com/api/v1"
        self.session = None
        
        # Initialize price history for each pair
        for pair in FOREX_PAIRS:
            bot_state['price_history'][pair] = []
    
    async def get_live_prices(self) -> Dict:
        """Fetch live prices from TraderMade"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Build currency pairs string
            pairs_str = ",".join(FOREX_PAIRS)
            url = f"{self.base_url}/live?currency={pairs_str}&api_key={self.api_key}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'quotes' in data:
                        prices = {}
                        for quote in data['quotes']:
                            symbol = quote['instrument']
                            prices[symbol] = {
                                'bid': float(quote['bid']),
                                'ask': float(quote['ask']),
                                'mid': float(quote['mid']),
                                'timestamp': quote.get('timestamp', int(time.time()))
                            }
                        
                        # Update last prices
                        bot_state['last_prices'] = prices
                        logger.info(f"Live prices updated: {list(prices.keys())}")
                        return prices
                    else:
                        logger.warning("No quotes in TraderMade response")
                        return None
                else:
                    logger.error(f"TraderMade API error: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("TraderMade API timeout")
            return None
        except Exception as e:
            logger.error(f"Error fetching live prices: {e}")
            return None
    
    def analyze_price_action(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Analyze price action for potential signals"""
        # Add to price history
        history = bot_state['price_history'][symbol]
        history.append(current_price)
        
        # Keep last 20 prices
        if len(history) > 20:
            history.pop(0)
        
        # Need at least 5 prices for analysis
        if len(history) < 5:
            return None
        
        # Calculate simple indicators
        sma_5 = sum(history[-5:]) / 5
        sma_10 = sum(history[-10:]) / 10 if len(history) >= 10 else sma_5
        
        # Price momentum
        momentum = (current_price - history[0]) / history[0] * 100
        
        # Volatility (simple)
        if len(history) >= 10:
            recent_range = max(history[-10:]) - min(history[-10:])
            pip_value = 0.0001 if symbol != 'USDJPY' else 0.01
            volatility_pips = recent_range / pip_value
        else:
            volatility_pips = 30  # Default
        
        # Generate signal based on conditions
        signal_data = None
        
        # Bullish signal
        if sma_5 > sma_10 * 1.0001 and momentum > 0.01:
            signal_data = {
                'direction': 'BUY',
                'strength': abs(momentum),
                'volatility': volatility_pips
            }
        # Bearish signal  
        elif sma_5 < sma_10 * 0.9999 and momentum < -0.01:
            signal_data = {
                'direction': 'SELL',
                'strength': abs(momentum),
                'volatility': volatility_pips
            }
        
        return signal_data
    
    async def generate_signal(self) -> Optional[Dict]:
        """Generate a trading signal using live data"""
        # Get live prices
        prices = await self.get_live_prices()
        
        if not prices:
            logger.warning("No live prices available, skipping signal generation")
            return None
        
        # Check each pair for signals
        for symbol, price_data in prices.items():
            if symbol not in FOREX_PAIRS:
                continue
            
            # Check cooldown
            if symbol in bot_state['last_signals']:
                elapsed = time.time() - bot_state['last_signals'][symbol]
                if elapsed < SIGNAL_CONFIG['cooldown_minutes'] * 60:
                    continue
            
            # Analyze price action
            current_price = price_data['mid']
            analysis = self.analyze_price_action(symbol, current_price)
            
            if not analysis:
                continue
            
            # Random chance for signal (adjusted by strength)
            chance_modifier = min(analysis['strength'] * 0.1, 0.1)  # Max 10% boost
            if random.random() > (SIGNAL_CONFIG['signal_chance'] + chance_modifier):
                continue
            
            # Generate TCS score based on signal strength and volatility
            base_tcs = 70
            strength_bonus = min(int(analysis['strength'] * 10), 15)
            volatility_penalty = max(0, int(analysis['volatility'] / 10) - 3)
            
            tcs_score = base_tcs + strength_bonus - volatility_penalty
            tcs_score = max(70, min(95, tcs_score))  # Clamp between 70-95
            
            # Determine signal type
            if tcs_score >= 90:
                signal_type = 'SNIPER'
            elif tcs_score >= 80:
                signal_type = 'PRECISION'
            else:
                signal_type = 'STANDARD'
            
            # Calculate levels using spread
            spread = price_data['ask'] - price_data['bid']
            pip = 0.0001 if symbol != 'USDJPY' else 0.01
            
            # Dynamic SL/TP based on volatility
            sl_pips = int(20 + analysis['volatility'] * 0.5)
            tp_pips = int(sl_pips * random.uniform(1.2, 2.5))
            
            if analysis['direction'] == 'BUY':
                entry = price_data['ask']  # Buy at ask
                sl = round(entry - (sl_pips * pip), 5)
                tp = round(entry + (tp_pips * pip), 5)
            else:
                entry = price_data['bid']  # Sell at bid
                sl = round(entry + (sl_pips * pip), 5)
                tp = round(entry - (tp_pips * pip), 5)
            
            signal = {
                'id': f"SIG-{int(time.time()*1000)}",
                'symbol': symbol,
                'direction': analysis['direction'],
                'tcs_score': tcs_score,
                'signal_type': signal_type,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips,
                'rr_ratio': round(tp_pips / sl_pips, 1),
                'spread': round(spread / pip, 1),
                'timestamp': datetime.now(),
                'expiry': 600,  # 10 minutes
                'live_data': True
            }
            
            # Update last signal time
            bot_state['last_signals'][symbol] = time.time()
            
            return signal
        
        return None


# Command Handlers (same as before)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"/start from {user.username} ({user.id})")
    
    welcome = f"""
🎯 **BITTEN Trading System**
Bot-Integrated Tactical Trading Engine

**Status**: 🟢 ONLINE
**Signals**: ⚡ ACTIVE
**Data**: 📊 LIVE (TraderMade)
**Mode**: {bot_state['mode']}

Commands: /ping /mode /status /help

Live market signals activated!
"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    
    response_time = round((time.time() - start_time) * 1000)
    
    # Check if we have live prices
    price_status = "📊 Live" if bot_state['last_prices'] else "⚠️ Waiting"
    
    await msg.edit_text(
        f"🏓 **PONG!** {response_time}ms | "
        f"Data: {price_status} | "
        f"Signals: {'✅' if bot_state['signals_active'] else '❌'}"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    uptime = get_uptime()
    
    # Get last price update time
    if bot_state['last_prices']:
        last_update = "✅ Connected"
        # Show current prices
        price_str = "\n".join([
            f"• {pair}: {data['mid']:.5f}"
            for pair, data in list(bot_state['last_prices'].items())[:3]
        ])
    else:
        last_update = "⏳ Connecting..."
        price_str = "• Waiting for data..."
    
    status = f"""
📊 **BITTEN Status**

**System**
• Status: 🟢 Online
• Uptime: {uptime}
• Mode: {bot_state['mode']}

**Live Data**
• Source: TraderMade API
• Status: {last_update}
• Signals Sent: {bot_state['signals_sent']}

**Current Prices**
{price_str}

**Coverage**
• Pairs: {', '.join(FOREX_PAIRS)}
• Check Rate: {SIGNAL_CONFIG['check_interval']}s
• Min TCS: {SIGNAL_CONFIG['min_confidence']}%
"""
    
    await update.message.reply_text(status, parse_mode='Markdown')


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals command"""
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
/ping - Check bot & data
/status - Live prices & info
/mode - Fire mode
/signals - Toggle on/off
/help - This help

**Signal Types**
🔥 90%+ = SNIPER (rare)
⭐ 80-89% = PRECISION
✅ 70-79% = STANDARD

**Live Data**
📊 TraderMade real-time feed
🔄 Updates every 30s
📈 Price action analysis
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Signal Alert (same compact format)
async def send_signal_alert(context: ContextTypes.DEFAULT_TYPE, signal: Dict):
    """Send COMPACT signal alert with live data notation"""
    try:
        # Visual differentiation based on signal type
        if signal['signal_type'] == 'SNIPER':
            line1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥"
            line2 = f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | 📊 LIVE"
            button_text = "🎯 SNIPER INTEL"
        
        elif signal['signal_type'] == 'PRECISION':
            line1 = f"⭐ **Precision Strike** ⭐"
            line2 = f"{signal['symbol']} {signal['direction']} | {signal['tcs_score']}% | 📊 Live Data"
            button_text = "⭐ VIEW INTEL"
        
        else:  # STANDARD
            line1 = f"✅ Signal: {signal['symbol']} {signal['direction']} | {signal['tcs_score']}%"
            line2 = f"📊 Live | Spread: {signal['spread']}p | ⏰ 10min"
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
        logger.info(f"Live signal sent: {signal['symbol']} {signal['direction']} @ {signal['entry']:.5f}")
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")


async def signal_generator_task(application: Application):
    """Background task to generate signals from live data"""
    generator = LiveMarketSignalGenerator()
    logger.info("Live signal generator started")
    
    # Send startup notification
    try:
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚀 **BITTEN Live Data Active** | TraderMade API Connected | Monitoring {len(FOREX_PAIRS)} pairs",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Startup message error: {e}")
    
    # Initial price fetch
    await generator.get_live_prices()
    
    # Main signal loop
    while True:
        try:
            if bot_state['signals_active']:
                signal = await generator.generate_signal()
                
                if signal:
                    await send_signal_alert(application, signal)
                    
                    # Variable delay after signal
                    delay = random.randint(45, 120)
                    await asyncio.sleep(delay)
            
            # Regular check interval
            await asyncio.sleep(SIGNAL_CONFIG['check_interval'])
            
        except Exception as e:
            logger.error(f"Signal generator error: {e}")
            await asyncio.sleep(60)
        
    # Cleanup
    if generator.session:
        await generator.session.close()


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
    ║   BITTEN - LIVE MARKET DATA ACTIVE 📊   ║
    ╚══════════════════════════════════════════╝
    
    Features:
    • Real-time TraderMade data feed
    • Live price action analysis
    • Dynamic TCS scoring
    • Compact 2-line alerts
    
    Data Source: TraderMade API ✅
    Pairs: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD
    
    Starting live connection...
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
    print("✅ Connecting to TraderMade...")
    print("📊 Live signals will appear based on real market movement!")
    print("\nPress Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()