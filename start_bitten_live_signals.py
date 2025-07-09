#!/usr/bin/env python3
"""
BITTEN Live Signal Engine Starter
Starts live signals flowing to Telegram with proper webapp integration and trade tracking
"""

import os
import sys
import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path
import signal as sig
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import BITTEN components
from src.bitten_core.advanced_signal_integration import AdvancedBITTENIntegration
from src.bitten_core.telegram_router import TelegramRouter
from src.bitten_core.tradermade_client import TraderMadeClient
from src.bitten_core.signal_display import SignalDisplay
from src.bitten_core.mission_briefing_generator import MissionBriefing, MissionType
from src.bitten_core.database.manager import DatabaseManager
from src.bitten_core.database.repository import UserRepository
from src.bitten_core.xp_integration import XPIntegration
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()


class LiveSignalEngine:
    """Main engine for live signal generation and distribution"""
    
    def __init__(self):
        self.is_running = False
        
        # Initialize components
        logger.info("Initializing Live Signal Engine...")
        
        # Database
        self.db_manager = DatabaseManager()
        self.user_repo = UserRepository(self.db_manager)
        self.xp_integration = XPIntegration(self.db_manager)
        
        # Signal generation
        self.signal_integration = AdvancedBITTENIntegration()
        self.market_client = TraderMadeClient()
        self.signal_display = SignalDisplay()
        
        # Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.webapp_url = os.getenv('WEBAPP_URL', 'https://joinbitten.com')
        
        # Trade tracking
        self.trade_tracker = TradeTracker()
        
        # Signal statistics
        self.stats = {
            'signals_generated': 0,
            'signals_sent': 0,
            'webapp_clicks': 0,
            'start_time': datetime.now()
        }
        
        logger.info("Live Signal Engine initialized")
    
    async def start(self):
        """Start the signal engine"""
        self.is_running = True
        logger.info("Starting Live Signal Engine...")
        
        # Start Telegram bot
        app = await self._setup_telegram_bot()
        
        # Start signal monitoring in background
        asyncio.create_task(self._monitor_signals())
        
        # Start trade tracking
        asyncio.create_task(self.trade_tracker.start_tracking())
        
        # Keep bot running
        await app.run_polling()
    
    async def _setup_telegram_bot(self):
        """Setup Telegram bot with handlers"""
        app = Application.builder().token(self.bot_token).build()
        
        # Command handlers
        app.add_handler(CommandHandler("start", self._handle_start))
        app.add_handler(CommandHandler("status", self._handle_status))
        app.add_handler(CommandHandler("signals", self._handle_signals_command))
        app.add_handler(CommandHandler("webapp", self._handle_webapp_test))
        
        # Callback handlers
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Start bot
        await app.initialize()
        await app.start()
        
        logger.info("Telegram bot started")
        return app
    
    async def _monitor_signals(self):
        """Monitor for new signals continuously"""
        logger.info("Starting signal monitoring...")
        
        while self.is_running:
            try:
                # Get signals from advanced integration
                signals = await self.signal_integration.get_current_signals()
                
                if signals:
                    for signal in signals:
                        await self._process_signal(signal)
                
                # Wait before next check (adjust based on your needs)
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Signal monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_signal(self, signal):
        """Process and send a signal to Telegram"""
        try:
            self.stats['signals_generated'] += 1
            
            # Create mission briefing
            briefing = self._create_mission_briefing(signal)
            
            # Store briefing
            mission_id = self.trade_tracker.store_mission_briefing(briefing)
            
            # Create Telegram message
            message = self._format_signal_message(signal, mission_id)
            
            # Create webapp button with proper integration
            keyboard = self._create_webapp_keyboard(mission_id, signal)
            
            # Send to Telegram
            bot = Bot(self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            self.stats['signals_sent'] += 1
            logger.info(f"Signal sent: {signal['symbol']} {signal['direction']}")
            
            # Track signal for learning
            self.trade_tracker.track_signal(signal, mission_id)
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def _create_mission_briefing(self, signal):
        """Create detailed mission briefing for webapp"""
        return MissionBriefing(
            mission_id=f"MSN-{int(time.time())}",
            mission_type=MissionType.SNIPER if signal.get('tcs_score', 0) > 85 else MissionType.ARCADE,
            symbol=signal['symbol'],
            direction=signal['direction'],
            entry_price=signal['entry_price'],
            stop_loss=signal['stop_loss'],
            take_profit=signal['take_profit'],
            risk_reward_ratio=signal.get('risk_reward', 2.0),
            tcs_score=signal.get('tcs_score', 75),
            market_conditions={
                'trend': signal.get('trend', 'neutral'),
                'volatility': signal.get('volatility', 'medium'),
                'key_levels': signal.get('key_levels', [])
            },
            strategy_rationale=signal.get('rationale', 'Technical setup detected'),
            risk_factors=signal.get('risk_factors', []),
            execution_notes=signal.get('notes', []),
            timestamp=datetime.now(),
            expires_at=datetime.now().timestamp() + 600  # 10 min expiry
        )
    
    def _format_signal_message(self, signal, mission_id):
        """Format signal for Telegram display"""
        tcs_emoji = self._get_tcs_emoji(signal.get('tcs_score', 75))
        
        return f"""
⚡ **SIGNAL DETECTED** ⚡

**{signal['symbol']}** | **{signal['direction'].upper()}** | {signal.get('tcs_score', 75)}% {tcs_emoji}

Entry: `{signal['entry_price']:.5f}`
SL: `{signal['stop_loss']:.5f}`
TP: `{signal['take_profit']:.5f}`

⏰ Expires in 10 minutes
Mission ID: `{mission_id}`
"""
    
    def _create_webapp_keyboard(self, mission_id, signal):
        """Create keyboard with proper webapp integration"""
        # Prepare webapp data
        webapp_data = {
            'mission_id': mission_id,
            'user_tier': 'NIBBLER',  # Will be dynamic based on user
            'timestamp': int(time.time()),
            'view': 'mission_brief'
        }
        
        # Encode data for URL
        import urllib.parse
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        
        # Create webapp URL
        webapp_url = f"{self.webapp_url}/hud?data={encoded_data}"
        
        # Create buttons
        buttons = []
        
        # Try WebApp button first (for supported clients)
        try:
            webapp_button = InlineKeyboardButton(
                "🎯 VIEW INTEL",
                web_app=WebAppInfo(url=webapp_url)
            )
            buttons.append([webapp_button])
        except:
            # Fallback to regular URL button
            url_button = InlineKeyboardButton(
                "🎯 VIEW INTEL",
                url=webapp_url
            )
            buttons.append([url_button])
        
        # Add fire button (disabled for now)
        fire_button = InlineKeyboardButton(
            "🔫 FIRE (Testing)",
            callback_data=f"fire_test_{mission_id}"
        )
        buttons.append([fire_button])
        
        return InlineKeyboardMarkup(buttons)
    
    def _get_tcs_emoji(self, tcs):
        """Get emoji based on TCS score"""
        if tcs >= 90:
            return "🔥"
        elif tcs >= 80:
            return "⭐"
        elif tcs >= 70:
            return "✅"
        else:
            return "⚠️"
    
    # Telegram handlers
    async def _handle_start(self, update, context):
        """Handle /start command"""
        await update.message.reply_text(
            "🎯 **BITTEN Live Signals Active**\n\n"
            "Signals are now flowing! You'll receive alerts here.\n\n"
            "Commands:\n"
            "/status - Check engine status\n"
            "/signals - Toggle signal alerts\n"
            "/webapp - Test webapp integration"
        )
    
    async def _handle_status(self, update, context):
        """Handle /status command"""
        uptime = datetime.now() - self.stats['start_time']
        
        status_msg = f"""
📊 **Live Signal Engine Status**

**Status**: 🟢 Running
**Uptime**: {uptime}
**Signals Generated**: {self.stats['signals_generated']}
**Signals Sent**: {self.stats['signals_sent']}
**WebApp Clicks**: {self.stats['webapp_clicks']}

**Market Data**: {'🟢 Connected' if self.market_client.is_connected() else '🔴 Disconnected'}
**Signal Integration**: 🟢 Active
**Trade Tracking**: 🟢 Recording
"""
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    
    async def _handle_signals_command(self, update, context):
        """Handle /signals command"""
        # For now, just confirm signals are active
        await update.message.reply_text(
            "✅ Signals are active and flowing!\n\n"
            "You'll receive all signals that meet the quality threshold."
        )
    
    async def _handle_webapp_test(self, update, context):
        """Handle /webapp command to test webapp integration"""
        # Create test signal
        test_signal = {
            'symbol': 'EURUSD',
            'direction': 'buy',
            'entry_price': 1.0900,
            'stop_loss': 1.0850,
            'take_profit': 1.0950,
            'tcs_score': 85
        }
        
        # Process as normal signal
        await self._process_signal(test_signal)
        
        await update.message.reply_text(
            "📤 Test signal sent!\n\n"
            "Check if the WebApp button opens correctly.\n"
            "If it only shows a URL, update your Telegram app."
        )
    
    async def _handle_callback(self, update, context):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("fire_test_"):
            await query.edit_message_text(
                "🔫 Fire button pressed (testing mode)\n\n"
                "In live mode, this would execute the trade."
            )
            
            # Track interaction
            self.stats['webapp_clicks'] += 1


class TradeTracker:
    """Tracks all signals and trades for learning system"""
    
    def __init__(self):
        self.db_path = Path("data/trade_tracking.db")
        self.mission_briefings = {}
        self.signal_history = []
        
        # Create tracking database
        self._init_database()
    
    def _init_database(self):
        """Initialize trade tracking database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Signal tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_tracking (
                signal_id TEXT PRIMARY KEY,
                mission_id TEXT,
                timestamp TIMESTAMP,
                symbol TEXT,
                direction TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                tcs_score INTEGER,
                signal_data TEXT,
                outcome TEXT,
                profit_loss REAL,
                execution_time REAL,
                notes TEXT
            )
        """)
        
        # Mission briefings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mission_briefings (
                mission_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                briefing_data TEXT
            )
        """)
        
        # User interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                mission_id TEXT,
                action TEXT,
                timestamp TIMESTAMP,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Trade tracking database initialized")
    
    def store_mission_briefing(self, briefing):
        """Store mission briefing for later reference"""
        mission_id = briefing.mission_id
        self.mission_briefings[mission_id] = briefing
        
        # Store in database
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO mission_briefings (mission_id, timestamp, briefing_data)
            VALUES (?, ?, ?)
        """, (mission_id, datetime.now(), json.dumps(briefing.__dict__, default=str)))
        
        conn.commit()
        conn.close()
        
        return mission_id
    
    def track_signal(self, signal, mission_id):
        """Track a signal for learning"""
        signal_id = f"SIG-{int(time.time() * 1000)}"
        
        # Store in memory
        self.signal_history.append({
            'signal_id': signal_id,
            'mission_id': mission_id,
            'signal': signal,
            'timestamp': datetime.now()
        })
        
        # Store in database
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO signal_tracking 
            (signal_id, mission_id, timestamp, symbol, direction, entry_price, 
             stop_loss, take_profit, tcs_score, signal_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, mission_id, datetime.now(),
            signal['symbol'], signal['direction'], signal['entry_price'],
            signal['stop_loss'], signal['take_profit'], 
            signal.get('tcs_score', 0),
            json.dumps(signal)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Signal tracked: {signal_id}")
    
    async def start_tracking(self):
        """Start continuous tracking tasks"""
        while True:
            try:
                # Periodic cleanup of old data
                await self._cleanup_old_data()
                
                # Generate tracking report
                await self._generate_tracking_report()
                
                await asyncio.sleep(3600)  # Every hour
                
            except Exception as e:
                logger.error(f"Tracking error: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_data(self):
        """Clean up old tracking data"""
        # Keep last 30 days
        pass
    
    async def _generate_tracking_report(self):
        """Generate tracking statistics"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("""
            SELECT COUNT(*), AVG(tcs_score), COUNT(DISTINCT symbol)
            FROM signal_tracking
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        
        count, avg_tcs, symbols = cursor.fetchone()
        
        logger.info(f"24h Stats: {count} signals, {avg_tcs:.1f} avg TCS, {symbols} pairs")
        
        conn.close()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received...")
    shutdown_flag.set()


async def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════╗
    ║      BITTEN LIVE SIGNAL ENGINE v2.0      ║
    ║         Real-Time Signal Generation      ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Setup signal handlers
    sig.signal(sig.SIGINT, signal_handler)
    sig.signal(sig.SIGTERM, signal_handler)
    
    # Create and start engine
    engine = LiveSignalEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        engine.is_running = False
    
    logger.info("Live Signal Engine stopped")


if __name__ == '__main__':
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Run the engine
    asyncio.run(main())