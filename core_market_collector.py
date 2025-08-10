#!/usr/bin/env python3
"""
CORE Market Data Collector
Connects to the same ZMQ feed as Elite Guard (port 5560)
Collects and stores tick/candle data for 24/7 crypto markets
"""

import zmq
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import threading
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoreMarketCollector:
    def __init__(self):
        """Initialize CORE market data collector"""
        logger.info("🚀 Initializing CORE Market Data Collector")
        
        # ZMQ setup
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None  # For publishing CORE_SIGNAL messages
        
        # Data storage - focus on crypto that trades 24/7
        self.crypto_symbols = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "BCHUSD"]
        self.forex_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]  # Including GOLD
        self.all_symbols = self.crypto_symbols + self.forex_symbols
        
        # Tick storage (last 1000 ticks per symbol)
        self.tick_data = defaultdict(lambda: deque(maxlen=1000))
        
        # Candle data storage (multiple timeframes)
        self.candles = {
            'M1': defaultdict(list),   # 1 minute
            'M5': defaultdict(list),   # 5 minutes  
            'M15': defaultdict(list),  # 15 minutes
            'H1': defaultdict(list),   # 1 hour
            'H4': defaultdict(list),   # 4 hours
            'D1': defaultdict(list)    # Daily
        }
        
        # Last candle timestamp for each timeframe/symbol
        self.last_candle_time = defaultdict(dict)
        
        # Statistics
        self.total_ticks = 0
        self.ticks_per_symbol = defaultdict(int)
        self.last_tick_time = {}
        
        # Database setup
        self.setup_database()
        
        # Running flag
        self.running = True
        
        # C.O.R.E. Signal Generation Engine - World-Class Crypto Trading
        self.signal_interval = 180  # Check for signals every 3 minutes (aggressive scanning)
        self.last_signal_time = defaultdict(float)  # Track last signal per symbol
        self.signal_threshold = 0.82  # 82% confidence minimum for world-class signals
        self.signals_generated = 0
        self.min_signal_gap = 900  # 15 minutes minimum between signals per symbol
        
        # Advanced crypto analysis parameters
        self.volatility_threshold = 0.015  # 1.5% minimum volatility for signal generation
        self.volume_spike_multiplier = 2.0  # Volume must be 2x average
        self.confluence_requirement = 3  # Minimum 3 confluence factors for high win rate
        self.max_daily_signals = 8  # Maximum 8 crypto signals per day (quality over quantity)
        self.daily_signal_count = defaultdict(int)
        self.last_daily_reset = datetime.now().date()
        
        logger.info(f"📊 Monitoring symbols: {', '.join(self.all_symbols)}")
        logger.info("🎯 Focus on 24/7 crypto: " + ", ".join(self.crypto_symbols))
        logger.info("🚀 C.O.R.E. Signal Engine: World-class crypto signal generation enabled")
    
    def setup_database(self):
        """Setup SQLite database for persistent storage"""
        try:
            self.db_conn = sqlite3.connect('/root/HydraX-v2/data/core_market_data.db', check_same_thread=False)
            self.db_cursor = self.db_conn.cursor()
            
            # Create tick data table
            self.db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    bid REAL NOT NULL,
                    ask REAL NOT NULL,
                    spread REAL,
                    volume REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_symbol_time (symbol, timestamp)
                )
            ''')
            
            # Create candles table
            self.db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL,
                    timestamp DATETIME NOT NULL,
                    UNIQUE(symbol, timeframe, timestamp)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("✅ Database initialized at /root/HydraX-v2/data/core_market_data.db")
            
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
            # Continue without database
            self.db_conn = None
    
    def connect_to_feed(self):
        """Connect to the same ZMQ feed as Elite Guard (port 5560) and setup signal publisher"""
        try:
            # Setup subscriber (data input)
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")  # Same port as Elite Guard
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            # Setup publisher for CORE_SIGNAL (output to production bot)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5558")  # Publish CORE_SIGNAL to port 5558 (crypto signals)
            
            logger.info("✅ Connected to ZMQ feed on port 5560 (same as Elite Guard)")
            logger.info("🚀 C.O.R.E. Signal publisher bound to port 5558 (crypto signals)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to feed: {e}")
            return False
    
    def process_tick(self, tick_data: Dict):
        """Process incoming tick data"""
        try:
            symbol = tick_data.get('symbol', '').upper()
            
            # Skip if not a monitored symbol
            if symbol not in self.all_symbols:
                return
            
            # Extract tick data
            tick = {
                'timestamp': datetime.now(),
                'bid': float(tick_data.get('bid', 0)),
                'ask': float(tick_data.get('ask', 0)),
                'spread': float(tick_data.get('spread', 0)),
                'volume': float(tick_data.get('volume', 0))
            }
            
            # Store tick
            self.tick_data[symbol].append(tick)
            self.total_ticks += 1
            self.ticks_per_symbol[symbol] += 1
            self.last_tick_time[symbol] = tick['timestamp']
            
            # Update candles
            self.update_candles(symbol, tick)
            
            # Store in database
            if self.db_conn:
                try:
                    self.db_cursor.execute('''
                        INSERT INTO ticks (symbol, bid, ask, spread, volume)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (symbol, tick['bid'], tick['ask'], tick['spread'], tick['volume']))
                    self.db_conn.commit()
                except Exception as e:
                    logger.debug(f"DB insert error: {e}")
            
            # Log progress every 100 ticks
            if self.total_ticks % 100 == 0:
                self.log_statistics()
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
    
    def update_candles(self, symbol: str, tick: Dict):
        """Update candle data from tick"""
        current_time = tick['timestamp']
        price = tick['bid']  # Use bid price for candles
        
        # Update each timeframe
        timeframes = {
            'M1': timedelta(minutes=1),
            'M5': timedelta(minutes=5),
            'M15': timedelta(minutes=15),
            'H1': timedelta(hours=1),
            'H4': timedelta(hours=4),
            'D1': timedelta(days=1)
        }
        
        for tf, delta in timeframes.items():
            # Calculate candle start time
            if tf == 'M1':
                candle_time = current_time.replace(second=0, microsecond=0)
            elif tf == 'M5':
                candle_time = current_time.replace(minute=(current_time.minute // 5) * 5, second=0, microsecond=0)
            elif tf == 'M15':
                candle_time = current_time.replace(minute=(current_time.minute // 15) * 15, second=0, microsecond=0)
            elif tf == 'H1':
                candle_time = current_time.replace(minute=0, second=0, microsecond=0)
            elif tf == 'H4':
                candle_time = current_time.replace(hour=(current_time.hour // 4) * 4, minute=0, second=0, microsecond=0)
            elif tf == 'D1':
                candle_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if we need a new candle
            last_time = self.last_candle_time.get(symbol, {}).get(tf)
            
            if last_time != candle_time:
                # Create new candle
                new_candle = {
                    'timestamp': candle_time,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': tick.get('volume', 0)
                }
                self.candles[tf][symbol].append(new_candle)
                self.last_candle_time[symbol][tf] = candle_time
                
                # Keep only last 500 candles
                if len(self.candles[tf][symbol]) > 500:
                    self.candles[tf][symbol] = self.candles[tf][symbol][-500:]
                    
            else:
                # Update existing candle
                if self.candles[tf][symbol]:
                    candle = self.candles[tf][symbol][-1]
                    candle['high'] = max(candle['high'], price)
                    candle['low'] = min(candle['low'], price)
                    candle['close'] = price
                    candle['volume'] += tick.get('volume', 0)
    
    def log_statistics(self):
        """Log collection statistics"""
        logger.info("📊 CORE Market Data Statistics:")
        logger.info(f"   Total ticks collected: {self.total_ticks}")
        
        # Show crypto symbols (24/7)
        logger.info("   🪙 Crypto (24/7):")
        for symbol in self.crypto_symbols:
            count = self.ticks_per_symbol.get(symbol, 0)
            last_time = self.last_tick_time.get(symbol)
            if count > 0:
                time_str = last_time.strftime("%H:%M:%S") if last_time else "Never"
                logger.info(f"      {symbol}: {count} ticks (last: {time_str})")
        
        # Show forex symbols
        logger.info("   💱 Forex/Gold:")
        for symbol in self.forex_symbols:
            count = self.ticks_per_symbol.get(symbol, 0)
            if count > 0:
                last_time = self.last_tick_time.get(symbol)
                time_str = last_time.strftime("%H:%M:%S") if last_time else "Never"
                logger.info(f"      {symbol}: {count} ticks (last: {time_str})")
    
    def data_listener_loop(self):
        """Main loop for listening to market data"""
        logger.info("🎧 Starting CORE data listener loop...")
        
        no_data_count = 0
        
        while self.running:
            try:
                # Try to receive data
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                
                # Parse JSON data
                try:
                    tick_data = json.loads(message)
                    self.process_tick(tick_data)
                    no_data_count = 0  # Reset counter on successful data
                    
                except json.JSONDecodeError:
                    # Try to extract JSON from message
                    if '{' in message and '}' in message:
                        json_str = message[message.index('{'):message.rindex('}')+1]
                        tick_data = json.loads(json_str)
                        self.process_tick(tick_data)
                        no_data_count = 0
                        
            except zmq.Again:
                # No data available
                no_data_count += 1
                
                # Log every 30 seconds of no data
                if no_data_count % 30 == 0:
                    logger.info("⏳ Waiting for market data... (EA may not be sending)")
                    
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in data listener: {e}")
                time.sleep(1)
    
    def get_latest_candles(self, symbol: str, timeframe: str = 'M5', count: int = 20):
        """Get latest candles for analysis"""
        if symbol in self.candles[timeframe]:
            return self.candles[timeframe][symbol][-count:]
        return []
    
    def get_latest_ticks(self, symbol: str, count: int = 100):
        """Get latest ticks for analysis"""
        if symbol in self.tick_data:
            return list(self.tick_data[symbol])[-count:]
        return []
    
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate RSI for momentum analysis"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_atr(self, candles: list, period: int = 14) -> float:
        """Calculate Average True Range for volatility"""
        if len(candles) < period:
            return 0.0
            
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / min(len(true_ranges), period)
    
    def detect_volume_spike(self, symbol: str) -> bool:
        """Detect abnormal volume spikes indicating institutional activity"""
        ticks = self.get_latest_ticks(symbol, 100)
        if len(ticks) < 50:
            return False
            
        recent_volumes = [t.get('volume', 0) for t in ticks[-10:]]
        avg_volume = sum(t.get('volume', 0) for t in ticks[-50:-10]) / 40
        
        current_volume = sum(recent_volumes) / len(recent_volumes)
        return current_volume > (avg_volume * self.volume_spike_multiplier)
    
    def analyze_market_structure(self, symbol: str) -> dict:
        """Analyze market structure for higher highs/lows"""
        candles = self.get_latest_candles(symbol, 'M15', 20)
        if len(candles) < 10:
            return {'trend': 'UNKNOWN', 'strength': 0}
            
        highs = [c['high'] for c in candles[-10:]]
        lows = [c['low'] for c in candles[-10:]]
        
        higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
        
        if higher_highs >= 6 and higher_lows >= 6:
            return {'trend': 'STRONG_BULL', 'strength': 0.9}
        elif higher_highs >= 4 and higher_lows >= 4:
            return {'trend': 'BULL', 'strength': 0.7}
        elif higher_highs <= 2 and higher_lows <= 2:
            return {'trend': 'STRONG_BEAR', 'strength': 0.9}
        elif higher_highs <= 4 and higher_lows <= 4:
            return {'trend': 'BEAR', 'strength': 0.7}
        else:
            return {'trend': 'RANGING', 'strength': 0.3}
    
    def detect_support_resistance_break(self, symbol: str) -> dict:
        """Detect breakouts from key support/resistance levels"""
        candles = self.get_latest_candles(symbol, 'M15', 50)
        if len(candles) < 20:
            return {'breakout': False, 'direction': None, 'strength': 0}
            
        # Find recent highs and lows for S/R levels
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        current_price = candles[-1]['close']
        
        # Resistance level (recent high)
        resistance = max(highs[-20:])
        support = min(lows[-20:])
        
        # Check for breakout
        price_range = resistance - support
        breakout_threshold = price_range * 0.02  # 2% of range
        
        if current_price > resistance + breakout_threshold:
            return {'breakout': True, 'direction': 'BUY', 'strength': 0.8}
        elif current_price < support - breakout_threshold:
            return {'breakout': True, 'direction': 'SELL', 'strength': 0.8}
        else:
            return {'breakout': False, 'direction': None, 'strength': 0}
    
    def calculate_confluence_score(self, symbol: str) -> dict:
        """Calculate confluence score from multiple factors"""
        candles = self.get_latest_candles(symbol, 'M5', 50)
        if len(candles) < 20:
            return {'score': 0, 'direction': None, 'factors': []}
            
        factors = []
        confidence = 0
        direction = None
        
        # 1. RSI Analysis
        closes = [c['close'] for c in candles]
        rsi = self.calculate_rsi(closes)
        if rsi < 30:  # Oversold
            factors.append('RSI_OVERSOLD')
            confidence += 0.15
            direction = 'BUY'
        elif rsi > 70:  # Overbought
            factors.append('RSI_OVERBOUGHT') 
            confidence += 0.15
            direction = 'SELL'
        
        # 2. Volume Analysis
        if self.detect_volume_spike(symbol):
            factors.append('VOLUME_SPIKE')
            confidence += 0.20
        
        # 3. Market Structure
        structure = self.analyze_market_structure(symbol)
        if structure['strength'] > 0.7:
            factors.append(f"STRUCTURE_{structure['trend']}")
            confidence += structure['strength'] * 0.25
            if structure['trend'] in ['BULL', 'STRONG_BULL']:
                direction = 'BUY'
            elif structure['trend'] in ['BEAR', 'STRONG_BEAR']:
                direction = 'SELL'
        
        # 4. Breakout Analysis
        breakout = self.detect_support_resistance_break(symbol)
        if breakout['breakout']:
            factors.append(f"BREAKOUT_{breakout['direction']}")
            confidence += breakout['strength'] * 0.20
            direction = breakout['direction']
        
        # 5. Volatility Check
        atr = self.calculate_atr(candles)
        current_price = candles[-1]['close']
        volatility_pct = (atr / current_price) if current_price > 0 else 0
        
        if volatility_pct > self.volatility_threshold:
            factors.append('VOLATILITY_OPTIMAL')
            confidence += 0.10
        
        return {
            'score': min(confidence, 1.0),  # Cap at 100%
            'direction': direction,
            'factors': factors,
            'confluence_count': len(factors)
        }
    
    def generate_crypto_signal(self, symbol: str) -> dict:
        """Generate high-quality crypto signal with world-class analysis"""
        try:
            # Only generate for crypto symbols
            if symbol not in self.crypto_symbols:
                return None
                
            # Check daily signal limit
            today = datetime.now().date()
            if today != self.last_daily_reset:
                self.daily_signal_count.clear()
                self.last_daily_reset = today
                
            if self.daily_signal_count[symbol] >= self.max_daily_signals:
                return None
                
            # Check minimum time gap
            current_time = time.time()
            if current_time - self.last_signal_time[symbol] < self.min_signal_gap:
                return None
                
            # Calculate confluence
            analysis = self.calculate_confluence_score(symbol)
            
            # High-quality signal requirements
            if (analysis['score'] < self.signal_threshold or
                analysis['confluence_count'] < self.confluence_requirement or
                not analysis['direction']):
                return None
                
            # Get current market data
            candles = self.get_latest_candles(symbol, 'M5', 10)
            if not candles:
                return None
                
            current_candle = candles[-1]
            entry_price = current_candle['close']
            
            # Calculate ATR for dynamic stop/target
            atr = self.calculate_atr(candles, 14)
            atr_multiplier = 3.0  # Conservative for crypto volatility
            
            # Professional risk management
            if analysis['direction'] == 'BUY':
                stop_loss = entry_price - (atr * atr_multiplier)
                take_profit = entry_price + (atr * atr_multiplier * 2.5)  # 1:2.5 RR
            else:  # SELL
                stop_loss = entry_price + (atr * atr_multiplier)
                take_profit = entry_price - (atr * atr_multiplier * 2.5)
            
            # Generate unique signal ID
            signal_id = f"CORE_{symbol}_{int(current_time)}"
            
            # Create professional signal
            signal = {
                'signal_id': signal_id,
                'symbol': symbol,
                'direction': analysis['direction'],
                'signal_type': 'CRYPTO_PRECISION',
                'confidence': analysis['score'] * 100,
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'atr': round(atr, 2),
                'risk_reward_ratio': 2.5,
                'session': self.get_current_session(),
                'timeframe': 'M5_M15_CONFLUENCE',
                'factors': analysis['factors'],
                'confluence_count': analysis['confluence_count'],
                'generated_at': datetime.utcnow().isoformat(),
                'source': 'CORE_v1.0_WORLDCLASS'
            }
            
            # Update tracking
            self.last_signal_time[symbol] = current_time
            self.daily_signal_count[symbol] += 1
            self.signals_generated += 1
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def publish_core_signal(self, signal: dict):
        """Publish CORE_SIGNAL to ZMQ for production bot"""
        try:
            if self.publisher and signal:
                message = f"CORE_SIGNAL {json.dumps(signal)}"
                self.publisher.send_string(message)
                
                logger.info(f"🚀 CORE Signal Generated: {signal['signal_id']}")
                logger.info(f"   {signal['symbol']} {signal['direction']} @ {signal['confidence']:.1f}%")
                logger.info(f"   Confluence: {signal['confluence_count']} factors: {', '.join(signal['factors'])}")
                logger.info(f"   Entry: ${signal['entry_price']} | SL: ${signal['stop_loss']} | TP: ${signal['take_profit']}")
                
        except Exception as e:
            logger.error(f"Error publishing CORE signal: {e}")
    
    def get_current_session(self) -> str:
        """Get current trading session for crypto (24/7 but with optimal times)"""
        hour = datetime.utcnow().hour
        if 13 <= hour <= 17:  # NY Overlap (high volume)
            return "NY_ACTIVE"
        elif 7 <= hour <= 12:  # London Active
            return "LONDON_ACTIVE" 
        elif 0 <= hour <= 6:   # Asian Session
            return "ASIAN_ACTIVE"
        else:
            return "CRYPTO_24_7"
    
    def run(self):
        """Main run method with integrated signal generation"""
        logger.info("🚀 Starting CORE Market Data Collector")
        
        # Connect to feed
        if not self.connect_to_feed():
            logger.error("Failed to connect to data feed")
            return
        
        # Start data listener in separate thread
        listener_thread = threading.Thread(target=self.data_listener_loop, daemon=True)
        listener_thread.start()
        
        logger.info("✅ CORE Market Collector is running")
        logger.info("📡 Listening for 24/7 crypto market data on port 5560")
        logger.info("📊 Data will be stored in: /root/HydraX-v2/data/core_market_data.db")
        logger.info("🚀 C.O.R.E. Signal Engine: Ready for world-class crypto signal generation")
        
        # Signal generation tracking
        last_signal_check = time.time()
        
        try:
            # Keep running with signal generation
            while self.running:
                current_time = time.time()
                
                # Check for signal generation every 3 minutes (180 seconds)
                if current_time - last_signal_check >= self.signal_interval:
                    self.scan_for_crypto_signals()
                    last_signal_check = current_time
                
                # Show current status every 10 seconds
                if self.total_ticks > 0:
                    active_symbols = [s for s in self.all_symbols if self.ticks_per_symbol.get(s, 0) > 0]
                    if active_symbols:
                        signal_stats = f" | Signals: {self.signals_generated}"
                        logger.info(f"📈 Active: {', '.join(active_symbols)} | Total ticks: {self.total_ticks}{signal_stats}")
                
                time.sleep(10)
                        
        except KeyboardInterrupt:
            logger.info("Shutting down CORE collector...")
        finally:
            self.running = False
            if self.subscriber:
                self.subscriber.close()
            if self.publisher:
                self.publisher.close()
            self.context.term()
            if self.db_conn:
                self.db_conn.close()
            logger.info("CORE Market Collector stopped")
    
    def scan_for_crypto_signals(self):
        """Scan crypto symbols for high-quality trading signals"""
        try:
            logger.info("🔍 C.O.R.E. Scanning for crypto signals...")
            
            signals_found = 0
            
            # Scan each crypto symbol for signals
            for symbol in self.crypto_symbols:
                # Skip if not enough data
                if self.ticks_per_symbol.get(symbol, 0) < 100:
                    continue
                    
                # Generate signal for this symbol
                signal = self.generate_crypto_signal(symbol)
                
                if signal:
                    # Publish the signal
                    self.publish_core_signal(signal)
                    signals_found += 1
                    
                    logger.info(f"🎯 C.O.R.E. Signal Generated for {symbol}")
                    logger.info(f"   Direction: {signal['direction']} | Confidence: {signal['confidence']:.1f}%")
                    logger.info(f"   Entry: ${signal['entry_price']} | R:R: 1:{signal['risk_reward_ratio']}")
            
            if signals_found == 0:
                logger.info("🔍 C.O.R.E. Scan complete - No signals met quality threshold")
            else:
                logger.info(f"🚀 C.O.R.E. Scan complete - {signals_found} signals generated")
                
        except Exception as e:
            logger.error(f"Error in crypto signal scan: {e}")

if __name__ == "__main__":
    collector = CoreMarketCollector()
    collector.run()