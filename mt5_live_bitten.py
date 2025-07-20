#!/usr/bin/env python3
"""
MT5 Live Integration with BITTEN Signal System
Uses actual RAPID_ASSAULT/SNIPER signal types from tier_settings.yml
"""

import json
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

from bitten_signals_live import (
    format_bitten_signal, determine_signal_type, 
    check_user_access, get_tcs_visual
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MT5_BITTEN')

# BITTEN's 8 configured pairs (from fire_router.py analysis)
TRADING_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD", "EURGBP"
]

class MT5BITTENProcessor:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/bitten_signals.db"
        self.init_database()
        self.price_history = {pair: [] for pair in TRADING_PAIRS}
        self.signal_counts = {"RAPID_ASSAULT": 0, "SNIPER": 0}
        
    def init_database(self):
        """Initialize database for BITTEN signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Market data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                bid REAL NOT NULL,
                ask REAL NOT NULL,
                spread REAL NOT NULL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # BITTEN signals with type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bitten_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                tcs_score INTEGER NOT NULL,
                signal_type TEXT NOT NULL,
                formatted_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def process_mt5_tick(self, data: Dict) -> Optional[Dict]:
        """Process MT5 tick and generate BITTEN signal if conditions met"""
        symbol = data.get('symbol')
        if symbol not in TRADING_PAIRS:
            return None
            
        bid = float(data.get('bid', 0))
        ask = float(data.get('ask', 0))
        volume = int(data.get('volume', 0))
        
        # Calculate spread
        spread = ask - bid
        
        # Store tick
        self.store_tick(symbol, bid, ask, spread, volume)
        
        # Update price history
        if symbol in self.price_history:
            self.price_history[symbol].append({
                'bid': bid,
                'ask': ask,
                'volume': volume,
                'time': datetime.now()
            })
            self.price_history[symbol] = self.price_history[symbol][-100:]
        
        # Calculate market conditions
        market_conditions = self.analyze_market_conditions(symbol)
        
        # Calculate TCS score
        tcs_score = self.calculate_tcs(symbol, spread, volume, market_conditions)
        
        # Determine signal type
        signal_type = determine_signal_type(tcs_score, market_conditions)
        
        if signal_type:
            # Generate signal
            direction = market_conditions.get('direction', 'BUY')
            entry_price = ask if direction == 'BUY' else bid
            
            signal = self.create_bitten_signal(
                symbol, direction, entry_price, tcs_score/100, signal_type
            )
            
            return signal
            
        return None
        
    def analyze_market_conditions(self, symbol: str) -> Dict:
        """Analyze market conditions for signal generation"""
        conditions = {}
        
        if len(self.price_history[symbol]) < 20:
            return conditions
            
        prices = [tick['bid'] for tick in self.price_history[symbol]]
        
        # Calculate momentum
        momentum = (prices[-1] - prices[-10]) / prices[-10]
        conditions['momentum'] = abs(momentum)
        conditions['direction'] = 'BUY' if momentum > 0 else 'SELL'
        
        # Check for strong trend (for SNIPER signals)
        if len(prices) >= 50:
            sma_20 = np.mean(prices[-20:])
            sma_50 = np.mean(prices[-50:])
            
            # Strong trend if price and MAs are aligned
            if conditions['direction'] == 'BUY':
                conditions['strong_trend'] = prices[-1] > sma_20 > sma_50
            else:
                conditions['strong_trend'] = prices[-1] < sma_20 < sma_50
        else:
            conditions['strong_trend'] = False
            
        # RSI
        if len(prices) >= 15:
            conditions['rsi'] = self.calculate_rsi(prices)
        else:
            conditions['rsi'] = 50
            
        # Session check
        conditions['optimal_session'] = self.is_optimal_session(symbol)
        
        return conditions
        
    def calculate_tcs(self, symbol: str, spread: float, volume: int, conditions: Dict) -> int:
        """
        Calculate Trade Confidence Score (0-100)
        Based on BITTEN's actual filtering logic
        """
        score = 0
        
        # Base score from momentum (up to 30 points)
        if conditions.get('momentum', 0) > 0.0002:
            score += min(30, int(conditions['momentum'] * 100000))
        
        # RSI contribution (up to 20 points)
        rsi = conditions.get('rsi', 50)
        if conditions.get('direction') == 'BUY' and rsi < 30:
            score += 20
        elif conditions.get('direction') == 'SELL' and rsi > 70:
            score += 20
        elif 40 <= rsi <= 60:
            score += 10
            
        # Spread quality (up to 15 points)
        if spread < 0.0002:
            score += 15
        elif spread < 0.0003:
            score += 10
        elif spread < 0.0005:
            score += 5
            
        # Volume (up to 15 points)
        if volume > 5000000:
            score += 15
        elif volume > 2000000:
            score += 10
        elif volume > 1000000:
            score += 5
            
        # Strong trend bonus (up to 10 points)
        if conditions.get('strong_trend', False):
            score += 10
            
        # Session optimization (up to 10 points)
        if conditions.get('optimal_session', False):
            score += 10
            
        # Cap at 100
        return min(100, score)
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices[-period-1:])
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
        
    def is_optimal_session(self, symbol: str) -> bool:
        """Check if current time is optimal for trading this pair"""
        hour = datetime.now().hour
        
        # Session windows from fire_router.py
        sessions = {
            "EURUSD": [(8, 17), (13, 22)],
            "GBPUSD": [(8, 17), (13, 22)],
            "USDJPY": [(0, 9), (13, 22)],
            "USDCHF": [(8, 17), (13, 22)],
            "AUDUSD": [(0, 9)],
            "USDCAD": [(13, 22)],
            "NZDUSD": [(0, 9)],
            "EURGBP": [(8, 17)]
        }
        
        if symbol in sessions:
            for start, end in sessions[symbol]:
                if start <= hour < end:
                    return True
                    
        return False
        
    def create_bitten_signal(self, symbol: str, direction: str, entry_price: float, 
                           confidence: float, signal_type: str) -> Dict:
        """Create BITTEN signal"""
        self.signal_counts[signal_type] += 1
        
        signal = {
            'signal_id': f'{signal_type}_{self.signal_counts[signal_type]:04d}',
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'confidence': confidence,
            'signal_type': signal_type
        }
        
        # Format message
        formatted_message, _ = format_bitten_signal(signal)
        signal['formatted_message'] = formatted_message
        
        # Store signal
        self.store_signal(signal)
        
        logger.info(f"BITTEN {signal_type}: {formatted_message.replace(chr(10), ' | ')}")
        
        return signal
        
    def store_tick(self, symbol: str, bid: float, ask: float, spread: float, volume: int):
        """Store market tick"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO market_ticks (symbol, bid, ask, spread, volume)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, bid, ask, spread, volume))
        conn.commit()
        conn.close()
        
    def store_signal(self, signal: Dict):
        """Store BITTEN signal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bitten_signals 
            (signal_id, symbol, direction, entry_price, tcs_score, signal_type, formatted_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal['signal_id'],
            signal['symbol'],
            signal['direction'],
            signal['entry_price'],
            int(signal['confidence'] * 100),
            signal['signal_type'],
            signal['formatted_message']
        ))
        conn.commit()
        conn.close()

# Global processor
processor = MT5BITTENProcessor()

def process_live_mt5_data(data: Dict) -> Optional[Dict]:
    """Process incoming MT5 data"""
    return processor.process_mt5_tick(data)

if __name__ == "__main__":
    logger.info("BITTEN MT5 Live Processor initialized")
    logger.info(f"Monitoring: {', '.join(TRADING_PAIRS)}")
    logger.info("Signal types: RAPID_ASSAULT (70%+), SNIPER (85%+)")
    logger.info("Waiting for live market data...")