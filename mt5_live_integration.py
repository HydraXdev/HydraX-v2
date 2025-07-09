#!/usr/bin/env python3
"""
MT5 Live Data Integration for BITTEN
Connects real market data to signal filtering system
"""

import json
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MT5_LIVE')

# BITTEN Configuration
TRADING_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD", "EURGBP"
]

# Signal filtering thresholds
FILTER_CONFIG = {
    "min_spread": 0.00001,  # Minimum spread to consider
    "max_spread": 0.0005,   # Maximum acceptable spread
    "min_volume": 1000000,  # Minimum tick volume
    "rsi_oversold": 30,     # RSI oversold level
    "rsi_overbought": 70,   # RSI overbought level
    "momentum_threshold": 0.0002,  # Minimum price momentum
    "confidence_threshold": 0.85  # Minimum signal confidence
}

class MT5LiveDataProcessor:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        self.init_database()
        self.price_history = {pair: [] for pair in TRADING_PAIRS}
        self.signal_count = 0
        
    def init_database(self):
        """Initialize database for live market data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Live tick data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                bid REAL NOT NULL,
                ask REAL NOT NULL,
                spread REAL NOT NULL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Filtered signals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                confidence REAL NOT NULL,
                filters_passed TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def process_mt5_tick(self, data: Dict) -> Dict:
        """Process incoming MT5 tick data"""
        symbol = data.get('symbol')
        bid = float(data.get('bid', 0))
        ask = float(data.get('ask', 0))
        volume = int(data.get('volume', 0))
        timestamp = data.get('time', datetime.now().isoformat())
        
        # Calculate spread
        spread = ask - bid
        
        # Store tick data
        self.store_tick(symbol, bid, ask, spread, volume)
        
        # Update price history
        if symbol in self.price_history:
            self.price_history[symbol].append({
                'bid': bid,
                'ask': ask,
                'time': timestamp,
                'volume': volume
            })
            # Keep last 100 ticks
            self.price_history[symbol] = self.price_history[symbol][-100:]
        
        # Apply filters and check for signals
        signal = self.apply_filters(symbol, bid, ask, spread, volume)
        
        return signal
        
    def store_tick(self, symbol: str, bid: float, ask: float, spread: float, volume: int):
        """Store tick data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO live_ticks (symbol, bid, ask, spread, volume)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, bid, ask, spread, volume))
        conn.commit()
        conn.close()
        
    def apply_filters(self, symbol: str, bid: float, ask: float, spread: float, volume: int) -> Dict:
        """Apply BITTEN signal filters"""
        filters_passed = []
        confidence = 0.0
        
        # Filter 1: Spread check
        if FILTER_CONFIG['min_spread'] <= spread <= FILTER_CONFIG['max_spread']:
            filters_passed.append('spread')
            confidence += 0.2
        else:
            return None
            
        # Filter 2: Volume check
        if volume >= FILTER_CONFIG['min_volume']:
            filters_passed.append('volume')
            confidence += 0.15
            
        # Filter 3: Price momentum
        momentum = self.calculate_momentum(symbol)
        if abs(momentum) >= FILTER_CONFIG['momentum_threshold']:
            filters_passed.append('momentum')
            confidence += 0.25
            direction = 'BUY' if momentum > 0 else 'SELL'
        else:
            return None
            
        # Filter 4: RSI check
        rsi = self.calculate_rsi(symbol)
        if rsi is not None:
            if (direction == 'BUY' and rsi < FILTER_CONFIG['rsi_oversold']) or \
               (direction == 'SELL' and rsi > FILTER_CONFIG['rsi_overbought']):
                filters_passed.append('rsi')
                confidence += 0.2
                
        # Filter 5: Market session check
        if self.is_optimal_session(symbol):
            filters_passed.append('session')
            confidence += 0.2
            
        # Generate signal if confidence threshold met
        if confidence >= FILTER_CONFIG['confidence_threshold']:
            self.signal_count += 1
            signal = {
                'id': f'LIVE_{self.signal_count:06d}',
                'symbol': symbol,
                'direction': direction,
                'entry_price': ask if direction == 'BUY' else bid,
                'confidence': confidence,
                'filters_passed': ','.join(filters_passed),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store signal
            self.store_signal(signal)
            logger.info(f"LIVE SIGNAL: {symbol} {direction} @ {signal['entry_price']} (Confidence: {confidence:.2f})")
            
            return signal
            
        return None
        
    def calculate_momentum(self, symbol: str) -> float:
        """Calculate price momentum"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return 0.0
            
        prices = [tick['bid'] for tick in self.price_history[symbol][-20:]]
        if len(prices) < 2:
            return 0.0
            
        # Simple momentum: current price vs 20 ticks ago
        momentum = (prices[-1] - prices[0]) / prices[0]
        return momentum
        
    def calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < period + 1:
            return None
            
        prices = [tick['bid'] for tick in self.price_history[symbol][-(period+1):]]
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
                
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def is_optimal_session(self, symbol: str) -> bool:
        """Check if current time is optimal for trading this pair"""
        current_hour = datetime.now().hour
        
        # Define optimal trading hours for each pair
        optimal_hours = {
            "EURUSD": range(7, 17),    # European session
            "GBPUSD": range(7, 17),    # European session
            "USDJPY": range(0, 10),    # Asian session
            "AUDUSD": range(22, 32),   # Asian/Sydney session (wraps around)
            "USDCAD": range(13, 22),   # US session
            "USDCHF": range(7, 17),    # European session
            "NZDUSD": range(21, 31),   # Sydney session (wraps around)
            "EURGBP": range(7, 17)     # European session
        }
        
        if symbol in optimal_hours:
            hours = optimal_hours[symbol]
            if hasattr(hours, '__contains__'):
                return current_hour in hours or (current_hour + 24) in hours
                
        return True  # Default to true if not specified
        
    def store_signal(self, signal: Dict):
        """Store filtered signal in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO live_signals (symbol, direction, entry_price, confidence, filters_passed)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            signal['symbol'],
            signal['direction'],
            signal['entry_price'],
            signal['confidence'],
            signal['filters_passed']
        ))
        conn.commit()
        conn.close()
        
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Get recent live signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM live_signals
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'direction': row[2],
                'entry_price': row[3],
                'confidence': row[4],
                'filters_passed': row[5],
                'timestamp': row[6]
            })
            
        conn.close()
        return signals

# Global processor instance
processor = MT5LiveDataProcessor()

def process_live_mt5_data(data: Dict) -> Dict:
    """Process incoming MT5 data"""
    return processor.process_mt5_tick(data)

def get_live_signals(limit: int = 10) -> List[Dict]:
    """Get recent live signals"""
    return processor.get_recent_signals(limit)

if __name__ == "__main__":
    logger.info("MT5 Live Data Processor initialized")
    logger.info(f"Monitoring pairs: {', '.join(TRADING_PAIRS)}")
    logger.info("Waiting for live market data...")