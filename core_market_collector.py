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
        
        logger.info(f"📊 Monitoring symbols: {', '.join(self.all_symbols)}")
        logger.info("🎯 Focus on 24/7 crypto: " + ", ".join(self.crypto_symbols))
    
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
        """Connect to the same ZMQ feed as Elite Guard (port 5560)"""
        try:
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")  # Same port as Elite Guard
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            logger.info("✅ Connected to ZMQ feed on port 5560 (same as Elite Guard)")
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
    
    def run(self):
        """Main run method"""
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
        
        try:
            # Keep running
            while self.running:
                time.sleep(10)
                
                # Show current status every 10 seconds
                if self.total_ticks > 0:
                    active_symbols = [s for s in self.all_symbols if self.ticks_per_symbol.get(s, 0) > 0]
                    if active_symbols:
                        logger.info(f"📈 Active: {', '.join(active_symbols)} | Total ticks: {self.total_ticks}")
                        
        except KeyboardInterrupt:
            logger.info("Shutting down CORE collector...")
        finally:
            self.running = False
            if self.subscriber:
                self.subscriber.close()
            self.context.term()
            if self.db_conn:
                self.db_conn.close()
            logger.info("CORE Market Collector stopped")

if __name__ == "__main__":
    collector = CoreMarketCollector()
    collector.run()