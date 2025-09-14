#!/usr/bin/env python3
"""
Elite Guard Market Data Manager
Handles all market data operations: OHLC fetching, ATR calculation, candle persistence
"""

import time
import json
import threading
import logging
import statistics
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import zmq

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Manages all market data operations for Elite Guard"""
    
    def __init__(self):
        self.m1_data = defaultdict(lambda: deque(maxlen=100))
        self.m5_data = defaultdict(lambda: deque(maxlen=300))
        self.m15_data = defaultdict(lambda: deque(maxlen=200))
        self.last_tick_times = defaultdict(float)
        
        # Trading pairs to monitor
        self.trading_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD',
            'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP', 'AUDJPY', 'EURAUD',
            'EURCHF', 'AUDCHF', 'GBPCHF', 'GBPAUD', 'XAUUSD', 'XAGUSD'
        ]
        
        # ZMQ setup for data listening
        self.context = None
        self.subscriber = None
        self.running = False
        
    def setup_zmq_subscriber(self) -> bool:
        """Setup ZMQ subscriber for market data"""
        try:
            self.context = zmq.Context()
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")
            self.subscriber.subscribe(b'')
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)
            logger.info("✅ Market data subscriber connected to port 5560")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup market data subscriber: {e}")
            return False
    
    def data_listener(self):
        """Listen for incoming market data"""
        logger.info("🎧 Market data listener started")
        while self.running:
            try:
                message = self.subscriber.recv_string()
                self.process_tick(message)
            except zmq.Again:
                continue
            except Exception as e:
                logger.error(f"Data listener error: {e}")
                time.sleep(1)
    
    def process_tick(self, message: str):
        """Process incoming tick data"""
        try:
            if not message.startswith('TICK '):
                return
                
            parts = message.split()
            if len(parts) < 4:
                return
                
            symbol = parts[1]
            bid = float(parts[2])
            ask = float(parts[3])
            
            if symbol in self.trading_pairs:
                mid_price = (bid + ask) / 2
                self.update_ohlc_data(symbol, mid_price)
                self.last_tick_times[symbol] = time.time()
                
        except Exception as e:
            logger.debug(f"Error processing tick: {e}")
    
    def update_ohlc_data(self, symbol: str, price: float):
        """Update OHLC data structures"""
        current_time = time.time()
        
        # Update M1 candles
        self._update_timeframe_data(self.m1_data[symbol], price, current_time, 60)
        
        # Update M5 candles  
        self._update_timeframe_data(self.m5_data[symbol], price, current_time, 300)
        
        # Update M15 candles
        self._update_timeframe_data(self.m15_data[symbol], price, current_time, 900)
    
    def _update_timeframe_data(self, data_deque: deque, price: float, current_time: float, timeframe_seconds: int):
        """Update specific timeframe data"""
        current_minute = int(current_time // timeframe_seconds) * timeframe_seconds
        
        if data_deque and data_deque[-1]['timestamp'] == current_minute:
            # Update existing candle
            candle = data_deque[-1]
            candle['high'] = max(candle['high'], price)
            candle['low'] = min(candle['low'], price)
            candle['close'] = price
            candle['volume'] += 1
        else:
            # Create new candle
            new_candle = {
                'timestamp': current_minute,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': 1,
                'datetime': datetime.fromtimestamp(current_minute)
            }
            data_deque.append(new_candle)
    
    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(self.m5_data[symbol]) < period + 1:
                return 0.0020  # Default ATR
                
            candles = list(self.m5_data[symbol])[-period-1:]
            true_ranges = []
            
            for i in range(1, len(candles)):
                current = candles[i]
                previous = candles[i-1]
                
                high_low = current['high'] - current['low']
                high_close = abs(current['high'] - previous['close'])
                low_close = abs(current['low'] - previous['close'])
                
                true_range = max(high_low, high_close, low_close)
                true_ranges.append(true_range)
            
            return statistics.mean(true_ranges) if true_ranges else 0.0020
            
        except Exception as e:
            logger.error(f"ATR calculation error for {symbol}: {e}")
            return 0.0020
    
    def get_candle_count(self, symbol: str, timeframe: str) -> int:
        """Get number of candles for a symbol/timeframe"""
        if timeframe == 'M1':
            return len(self.m1_data[symbol])
        elif timeframe == 'M5':
            return len(self.m5_data[symbol])
        elif timeframe == 'M15':
            return len(self.m15_data[symbol])
        return 0
    
    def save_candles(self, filepath: str = '/root/HydraX-v2/candle_cache.json'):
        """Save candle data to file"""
        try:
            cache_data = {
                'm1_data': {symbol: list(candles) for symbol, candles in self.m1_data.items()},
                'm5_data': {symbol: list(candles) for symbol, candles in self.m5_data.items()},
                'm15_data': {symbol: list(candles) for symbol, candles in self.m15_data.items()},
                'last_save': time.time()
            }
            
            with open(filepath, 'w') as f:
                json.dump(cache_data, f, default=str)
                
            logger.debug("💾 Candle data saved to cache")
            
        except Exception as e:
            logger.error(f"Failed to save candles: {e}")
    
    def load_candles(self, filepath: str = '/root/HydraX-v2/candle_cache.json'):
        """Load candle data from file"""
        try:
            with open(filepath, 'r') as f:
                cache_data = json.load(f)
            
            # Restore data structures
            for symbol, candles in cache_data.get('m1_data', {}).items():
                self.m1_data[symbol] = deque(candles, maxlen=100)
            
            for symbol, candles in cache_data.get('m5_data', {}).items():
                self.m5_data[symbol] = deque(candles, maxlen=300)
                
            for symbol, candles in cache_data.get('m15_data', {}).items():
                self.m15_data[symbol] = deque(candles, maxlen=200)
            
            logger.info(f"💾 Candle data loaded from cache ({len(self.m5_data)} symbols)")
            
        except Exception as e:
            logger.info(f"No candle cache found or failed to load: {e}")
    
    def get_data_freshness(self) -> Dict[str, float]:
        """Get data freshness for all symbols"""
        current_time = time.time()
        freshness = {}
        
        for symbol in self.trading_pairs:
            if symbol in self.last_tick_times:
                age = current_time - self.last_tick_times[symbol]
                freshness[symbol] = age
            else:
                freshness[symbol] = float('inf')
                
        return freshness
    
    def start_data_listener(self):
        """Start the data listener thread"""
        if self.setup_zmq_subscriber():
            self.running = True
            listener_thread = threading.Thread(target=self.data_listener, daemon=True)
            listener_thread.start()
            return True
        return False
    
    def stop(self):
        """Stop the data manager"""
        self.running = False
        if self.subscriber:
            self.subscriber.close()
        if self.context:
            self.context.term()
        logger.info("🛑 Market Data Manager stopped")