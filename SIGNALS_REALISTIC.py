#!/usr/bin/env python3
"""
BITTEN Signals with Realistic Market Simulation
Mimics real market behavior until MT5 bridge is ready
"""

import os
import sys
import asyncio
import logging
import json
import time
import random
import math
from datetime import datetime, timedelta
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

# Signal configuration
SIGNAL_CONFIG = {
    'check_interval': 30,      # Check every 30 seconds
    'signal_chance': 0.12,     # 12% base chance
    'cooldown_minutes': 5,     # 5 min cooldown per symbol
    'min_confidence': 70,      # Minimum TCS score
}

# Forex pairs with realistic base prices
FOREX_PAIRS = {
    'EURUSD': {'base': 1.0900, 'volatility': 0.0008, 'trend': 0},
    'GBPUSD': {'base': 1.2650, 'volatility': 0.0010, 'trend': 0},
    'USDJPY': {'base': 150.50, 'volatility': 0.08, 'trend': 0},
    'AUDUSD': {'base': 0.6550, 'volatility': 0.0006, 'trend': 0},
    'USDCAD': {'base': 1.3650, 'volatility': 0.0007, 'trend': 0}
}

# Market sessions (UTC)
MARKET_SESSIONS = {
    'ASIAN': {'start': 0, 'end': 9, 'pairs': ['USDJPY', 'AUDUSD']},
    'LONDON': {'start': 8, 'end': 17, 'pairs': ['EURUSD', 'GBPUSD']},
    'NEW_YORK': {'start': 13, 'end': 22, 'pairs': ['EURUSD', 'USDCAD']}
}

# Global state
bot_state = {
    'signals_active': True,
    'mode': 'MANUAL',
    'signals_sent': 0,
    'start_time': datetime.now(),
    'last_signals': {},
    'data_source': 'REALISTIC (MT5 Bridge Coming)',
    'price_history': {},
    'market_state': 'NORMAL'  # NORMAL, TRENDING, VOLATILE
}


class RealisticMarketSimulator:
    """Simulates realistic forex market behavior"""
    
    def __init__(self):
        # Initialize price history
        for pair in FOREX_PAIRS:
            bot_state['price_history'][pair] = []
            
        # Market state variables
        self.time_factor = 0
        self.news_events = self._generate_news_schedule()
    
    def _generate_news_schedule(self) -> List[Dict]:
        """Generate random news events for the day"""
        events = []
        current_hour = datetime.now().hour
        
        # 2-3 news events per day
        for _ in range(random.randint(2, 3)):
            hour = random.randint(current_hour + 1, 23)
            impact = random.choice(['LOW', 'MEDIUM', 'HIGH'])
            events.append({
                'hour': hour,
                'impact': impact,
                'processed': False
            })
        
        return sorted(events, key=lambda x: x['hour'])
    
    def get_current_session(self) -> str:
        """Get current market session"""
        current_hour = datetime.utcnow().hour
        
        active_sessions = []
        for session, info in MARKET_SESSIONS.items():
            if info['start'] <= current_hour < info['end']:
                active_sessions.append(session)
        
        return active_sessions[0] if active_sessions else 'OFF_HOURS'
    
    def get_session_volatility(self, pair: str) -> float:
        """Get volatility multiplier based on session"""
        session = self.get_current_session()
        
        # Increase volatility during active sessions
        if session == 'ASIAN' and pair in ['USDJPY', 'AUDUSD']:
            return 1.5
        elif session == 'LONDON' and pair in ['EURUSD', 'GBPUSD']:
            return 1.8
        elif session == 'NEW_YORK' and pair in ['EURUSD', 'USDCAD']:
            return 1.6
        else:
            return 0.7  # Lower volatility off-hours
    
    def update_market_prices(self) -> Dict:
        """Update all market prices with realistic movement"""
        self.time_factor += 1
        prices = {}
        
        # Check for news events
        current_hour = datetime.now().hour
        for event in self.news_events:
            if event['hour'] == current_hour and not event['processed']:
                bot_state['market_state'] = 'VOLATILE'
                event['processed'] = True
                logger.info(f"News event triggered: {event['impact']} impact")
        
        # Update each pair
        for pair, config in FOREX_PAIRS.items():
            # Get session volatility
            session_mult = self.get_session_volatility(pair)
            
            # Calculate price movement
            # Base movement (random walk)
            random_move = random.gauss(0, config['volatility'] * session_mult)
            
            # Add trend component
            if abs(config['trend']) > 0:
                trend_move = config['trend'] * config['volatility'] * 0.3
                random_move += trend_move
            
            # Add sinusoidal component (intraday patterns)
            time_of_day = (self.time_factor % 1440) / 1440  # Minutes in day
            sine_move = math.sin(time_of_day * 2 * math.pi) * config['volatility'] * 0.2
            
            # Calculate new price
            if bot_state['price_history'][pair]:
                last_price = bot_state['price_history'][pair][-1]
            else:
                last_price = config['base']
            
            new_price = last_price + random_move + sine_move
            
            # Add to history
            bot_state['price_history'][pair].append(new_price)
            if len(bot_state['price_history'][pair]) > 50:
                bot_state['price_history'][pair].pop(0)
            
            # Create realistic bid/ask spread
            pip = 0.0001 if pair != 'USDJPY' else 0.01
            base_spread = 1.5 if pair != 'USDJPY' else 0.15  # pips
            
            # Widen spread during volatile times
            if bot_state['market_state'] == 'VOLATILE':
                base_spread *= 2
            
            spread = base_spread * pip
            
            prices[pair] = {
                'bid': round(new_price - spread/2, 5),
                'ask': round(new_price + spread/2, 5),
                'mid': round(new_price, 5),
                'spread_pips': round(base_spread, 1)
            }
            
            # Update trend occasionally
            if random.random() < 0.02:  # 2% chance
                config['trend'] = random.uniform(-1, 1)
        
        # Reset market state
        if bot_state['market_state'] == 'VOLATILE' and random.random() < 0.1:
            bot_state['market_state'] = 'NORMAL'
        
        return prices
    
    def analyze_for_signal(self, pair: str, prices: Dict) -> Optional[Dict]:
        """Analyze price action for signal generation"""
        history = bot_state['price_history'][pair]
        
        if len(history) < 10:
            return None
        
        current_price = prices[pair]['mid']
        
        # Calculate indicators
        sma_5 = sum(history[-5:]) / 5
        sma_10 = sum(history[-10:]) / 10
        sma_20 = sum(history[-20:]) / 20 if len(history) >= 20 else sma_10
        
        # Momentum
        momentum = (current_price - history[-10]) / history[-10] * 100
        
        # Volatility (ATR-like)
        recent_ranges = []
        for i in range(1, min(14, len(history))):
            high = max(history[-i-1], history[-i])
            low = min(history[-i-1], history[-i])
            recent_ranges.append(high - low)
        
        if recent_ranges:
            atr = sum(recent_ranges) / len(recent_ranges)
            pip_value = 0.0001 if pair != 'USDJPY' else 0.01
            atr_pips = atr / pip_value
        else:
            atr_pips = 30
        
        # Signal conditions
        signal_strength = 0
        direction = None
        
        # Trend following
        if sma_5 > sma_10 > sma_20:
            direction = 'BUY'
            signal_strength += 30
        elif sma_5 < sma_10 < sma_20:
            direction = 'SELL'
            signal_strength += 30
        
        # Momentum confirmation
        if direction == 'BUY' and momentum > 0.02:
            signal_strength += 20
        elif direction == 'SELL' and momentum < -0.02:
            signal_strength += 20
        
        # Volatility filter
        if 15 < atr_pips < 50:  # Good volatility range
            signal_strength += 20
        
        # Session bonus
        session = self.get_current_session()
        if session != 'OFF_HOURS':
            signal_strength += 10
        
        # News event bonus
        if bot_state['market_state'] == 'VOLATILE':
            signal_strength += 15
        
        if direction and signal_strength >= 50:
            return {
                'direction': direction,
                'strength': signal_strength,
                'atr_pips': atr_pips,
                'momentum': abs(momentum),
                'spread': prices[pair]['spread_pips']
            }
        
        return None
    
    def generate_signal(self, prices: Dict) -> Optional[Dict]:
        """Generate trading signal from market analysis"""
        # Check each pair
        for pair, price_data in prices.items():
            # Check cooldown
            if pair in bot_state['last_signals']:
                elapsed = time.time() - bot_state['last_signals'][pair]
                if elapsed < SIGNAL_CONFIG['cooldown_minutes'] * 60:
                    continue
            
            # Analyze for signal
            analysis = self.analyze_for_signal(pair, prices)
            
            if not analysis:
                continue
            
            # Adjust chance based on signal strength
            chance_modifier = analysis['strength'] / 500  # Max 20% boost at 100 strength
            if random.random() > (SIGNAL_CONFIG['signal_chance'] + chance_modifier):
                continue
            
            # Calculate TCS score
            base_tcs = 65
            tcs_score = min(95, base_tcs + analysis['strength'] // 2)
            
            # Determine signal type
            if tcs_score >= 90:
                signal_type = 'SNIPER'
            elif tcs_score >= 80:
                signal_type = 'PRECISION'
            else:
                signal_type = 'STANDARD'
            
            # Calculate SL/TP based on ATR
            sl_pips = int(max(20, min(50, analysis['atr_pips'] * 1.5)))
            
            # Better R:R for higher quality signals
            if signal_type == 'SNIPER':
                tp_multiplier = random.uniform(2.5, 3.5)
            elif signal_type == 'PRECISION':
                tp_multiplier = random.uniform(1.8, 2.5)
            else:
                tp_multiplier = random.uniform(1.2, 2.0)
            
            tp_pips = int(sl_pips * tp_multiplier)
            
            # Calculate entry/exit levels
            pip = 0.0001 if pair != 'USDJPY' else 0.01
            
            if analysis['direction'] == 'BUY':
                entry = price_data['ask']
                sl = round(entry - (sl_pips * pip), 5)
                tp = round(entry + (tp_pips * pip), 5)
            else:
                entry = price_data['bid']
                sl = round(entry + (sl_pips * pip), 5)
                tp = round(entry - (tp_pips * pip), 5)
            
            signal = {
                'id': f"SIG-{int(time.time()*1000)}",
                'symbol': pair,
                'direction': analysis['direction'],
                'tcs_score': tcs_score,
                'signal_type': signal_type,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips,
                'rr_ratio': round(tp_pips / sl_pips, 1),
                'spread': analysis['spread'],
                'session': self.get_current_session(),
                'timestamp': datetime.now(),
                'expiry': 600  # 10 minutes
            }
            
            # Update last signal time
            bot_state['last_signals'][pair] = time.time()
            
            return signal
        
        return None


# Command handlers remain the same
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"/start from {user.username} ({user.id})")
    
    welcome = f"""
🎯 **BITTEN Trading System**
Bot-Integrated Tactical Trading Engine

**Status**: 🟢 ONLINE
**Signals**: ⚡ ACTIVE
**Data**: 📊 Realistic Simulation
**Mode**: {bot_state['mode']}

Commands: /ping /mode /status /help

Market-accurate signals with session awareness!
"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    
    response_time = round((time.time() - start_time) * 1000)
    session = RealisticMarketSimulator().get_current_session()
    
    await msg.edit_text(
        f"🏓 **PONG!** {response_time}ms | "
        f"Session: {session} | "
        f"Signals: {'✅' if bot_state['signals_active'] else '❌'}"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command with market info"""
    uptime = get_uptime()
    simulator = RealisticMarketSimulator()
    session = simulator.get_current_session()
    
    # Get latest prices
    if bot_state['price_history']:
        price_str = ""
        for pair in list(FOREX_PAIRS.keys())[:3]:
            if bot_state['price_history'][pair]:
                last_price = bot_state['price_history'][pair][-1]
                price_str += f"• {pair}: {last_price:.5f}\n"
    else:
        price_str = "• Initializing..."
    
    status = f"""
📊 **BITTEN Status**

**System**
• Status: 🟢 Online
• Uptime: {uptime}
• Mode: {bot_state['mode']}

**Market Info**
• Session: {session}
• State: {bot_state['market_state']}
• Signals Sent: {bot_state['signals_sent']}

**Current Prices**
{price_str}

**Coverage**
• Pairs: {', '.join(FOREX_PAIRS.keys())}
• Data: Realistic market simulation
• MT5 Bridge: Coming soon
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


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mode command"""
    modes = {
        'MANUAL': '🎯 MANUAL - You control firing',
        'SEMI_AUTO': '⚡ SEMI-AUTO - Confirm each trade',
        'AUTO': '🤖 AUTO - Fully automated'
    }
    
    response = f"**Fire Mode**: {bot_state['mode']}\n{modes.get(bot_state['mode'], 'Unknown')}"
    await update.message.reply_text(response, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **Commands**
/ping - Check bot & session
/status - Market info & prices
/mode - Fire mode
/signals - Toggle on/off
/help - This help

**Signal Types**
🔥 90%+ = SNIPER (best R:R)
⭐ 80-89% = PRECISION
✅ 70-79% = STANDARD

**Market Sessions** (UTC)
🌏 Asian: 00:00-09:00
🇬🇧 London: 08:00-17:00
🇺🇸 New York: 13:00-22:00

Signals adapt to market conditions!
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Signal alert function
async def send_signal_alert(context: ContextTypes.DEFAULT_TYPE, signal: Dict):
    """Send COMPACT signal alert"""
    try:
        # Add session info for realism
        session_emoji = {
            'ASIAN': '🌏',
            'LONDON': '🇬🇧',
            'NEW_YORK': '🇺🇸',
            'OFF_HOURS': '🌙'
        }.get(signal['session'], '📊')
        
        # Format based on signal type
        if signal['signal_type'] == 'SNIPER':
            line1 = f"🔥🔥 **SNIPER SHOT** 🔥🔥"
            line2 = f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | R:R {signal['rr_ratio']}"
            button_text = "🎯 SNIPER INTEL"
        
        elif signal['signal_type'] == 'PRECISION':
            line1 = f"⭐ **Precision Strike** ⭐"
            line2 = f"{signal['symbol']} {signal['direction']} | {signal['tcs_score']}% | {session_emoji} {signal['session']}"
            button_text = "⭐ VIEW INTEL"
        
        else:  # STANDARD
            line1 = f"✅ Signal: {signal['symbol']} {signal['direction']} | {signal['tcs_score']}%"
            line2 = f"{session_emoji} {signal['session']} | Spread: {signal['spread']}p"
            button_text = "📋 VIEW DETAILS"
        
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
                text=button_text,
                url=webapp_url
            )
        ]])
        
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        bot_state['signals_sent'] += 1
        logger.info(f"Signal sent: {signal['symbol']} {signal['direction']} @ {signal['entry']:.5f} ({signal['session']})")
        
    except Exception as e:
        logger.error(f"Error sending signal: {e}")


async def signal_generator_task(application: Application):
    """Background task for realistic signal generation"""
    simulator = RealisticMarketSimulator()
    logger.info("Realistic market simulator started")
    
    # Send startup notification
    try:
        session = simulator.get_current_session()
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚀 **BITTEN Market Engine Active** | Session: {session} | Realistic price simulation engaged",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Startup message error: {e}")
    
    # Main loop
    while True:
        try:
            if bot_state['signals_active']:
                # Update market prices
                prices = simulator.update_market_prices()
                
                # Check for signals
                signal = simulator.generate_signal(prices)
                
                if signal:
                    await send_signal_alert(application, signal)
                    
                    # Variable delay after signal
                    delay = random.randint(60, 180)
                    await asyncio.sleep(delay)
            
            # Regular interval
            await asyncio.sleep(SIGNAL_CONFIG['check_interval'])
            
        except Exception as e:
            logger.error(f"Signal generator error: {e}")
            await asyncio.sleep(60)


def get_uptime() -> str:
    """Get formatted uptime"""
    delta = datetime.now() - bot_state['start_time']
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"


def main():
    """Start the bot"""
    print("""
    ╔══════════════════════════════════════════╗
    ║   BITTEN - REALISTIC MARKET ENGINE 📊    ║
    ╚══════════════════════════════════════════╝
    
    Features:
    • Market session awareness
    • Realistic price movements
    • News event simulation
    • Dynamic volatility
    • Accurate spread modeling
    
    Data: Realistic simulation
    Sessions: Asian, London, New York
    
    Starting market engine...
    """)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("mode", mode_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("signals", signals_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Post-init
    async def post_init(app: Application) -> None:
        asyncio.create_task(signal_generator_task(app))
    
    application.post_init = post_init
    
    # Run
    print("✅ Realistic market simulation active!")
    print("📊 Signals follow market sessions and conditions")
    print("\nPress Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()