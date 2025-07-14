#!/usr/bin/env python3
"""
MT5 Live Data Integration with Tiered Signal System
Professional military-grade trading signals
"""

import json
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

from tiered_signal_system import (
    SIGNAL_TIERS, format_tactical_signal, get_signal_tier,
    apply_tiered_filters, check_session_active, SESSION_SCHEDULE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MT5_TIERED')

# BITTEN Configuration
TRADING_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD", "EURGBP"
]

class MT5TieredProcessor:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        self.init_database()
        self.price_history = {pair: [] for pair in TRADING_PAIRS}
        self.signal_counts = {tier: 0 for tier in SIGNAL_TIERS}
        self.daily_counts = {tier: 0 for tier in SIGNAL_TIERS}
        self.last_reset = datetime.now().date()
        
    def init_database(self):
        """Initialize database with tiered signal support"""
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
        
        # Tiered signals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tiered_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                confidence REAL NOT NULL,
                tier TEXT NOT NULL,
                filters_passed TEXT,
                formatted_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def reset_daily_counts(self):
        """Reset daily signal counts at midnight"""
        current_date = datetime.now().date()
        if current_date != self.last_reset:
            self.daily_counts = {tier: 0 for tier in SIGNAL_TIERS}
            self.last_reset = current_date
            logger.info("Daily signal counts reset")
            
    def process_mt5_tick(self, data: Dict) -> Dict:
        """Process incoming MT5 tick data with tiered filtering"""
        self.reset_daily_counts()
        
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
        
        # Calculate indicators
        indicators = self.calculate_indicators(symbol, bid, ask, volume)
        
        # Apply tiered filters
        tier, confidence, filters_passed = apply_tiered_filters(
            symbol, bid, ask, spread, indicators
        )
        
        # Check if we should generate a signal
        if tier and self.should_generate_signal(tier):
            signal = self.create_tiered_signal(
                symbol, bid, ask, indicators['direction'], 
                confidence, tier, filters_passed
            )
            return signal
            
        return None
        
    def should_generate_signal(self, tier: str) -> bool:
        """Check if we haven't exceeded daily limit for tier"""
        max_daily = SIGNAL_TIERS[tier]['max_daily']
        return self.daily_counts[tier] < max_daily
        
    def calculate_indicators(self, symbol: str, bid: float, ask: float, volume: int) -> Dict:
        """Calculate technical indicators"""
        indicators = {
            'volume': volume,
            'optimal_session': check_session_active(symbol)
        }
        
        if len(self.price_history[symbol]) >= 20:
            prices = [tick['bid'] for tick in self.price_history[symbol][-20:]]
            
            # Momentum
            indicators['momentum'] = (prices[-1] - prices[0]) / prices[0]
            indicators['direction'] = 'BUY' if indicators['momentum'] > 0 else 'SELL'
            
            # RSI
            indicators['rsi'] = self.calculate_rsi(symbol)
            
            # Simple MACD confirmation (price above/below short MA)
            sma_5 = np.mean(prices[-5:])
            sma_10 = np.mean(prices[-10:])
            indicators['macd_confirmation'] = (
                (indicators['direction'] == 'BUY' and sma_5 > sma_10) or
                (indicators['direction'] == 'SELL' and sma_5 < sma_10)
            )
            
            # Support/Resistance (simplified)
            recent_high = max(prices[-20:])
            recent_low = min(prices[-20:])
            price_range = recent_high - recent_low
            
            # Check if near support (for buys) or resistance (for sells)
            if indicators['direction'] == 'BUY':
                indicators['support_resistance'] = (bid - recent_low) < (price_range * 0.3)
            else:
                indicators['support_resistance'] = (recent_high - bid) < (price_range * 0.3)
        else:
            indicators['momentum'] = 0
            indicators['direction'] = 'HOLD'
            indicators['rsi'] = 50
            indicators['macd_confirmation'] = False
            indicators['support_resistance'] = False
            
        return indicators
        
    def calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < period + 1:
            return 50.0
            
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
        
    def create_tiered_signal(self, symbol: str, bid: float, ask: float, 
                           direction: str, confidence: float, tier: str, 
                           filters_passed: List[str]) -> Dict:
        """Create a tiered signal"""
        self.signal_counts[tier] += 1
        self.daily_counts[tier] += 1
        
        entry_price = ask if direction == 'BUY' else bid
        
        signal = {
            'signal_id': f'{tier}_{self.signal_counts[tier]:04d}',
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'confidence': confidence,
            'tier': tier,
            'filters_passed': ','.join(filters_passed)
        }
        
        # Format tactical message
        signal['formatted_message'] = format_tactical_signal(signal, tier)
        
        # Store signal
        self.store_signal(signal)
        
        logger.info(f"TIER {tier} SIGNAL: {signal['formatted_message']}")
        
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
        
    def store_signal(self, signal: Dict):
        """Store tiered signal in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tiered_signals 
            (signal_id, symbol, direction, entry_price, confidence, tier, filters_passed, formatted_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal['signal_id'],
            signal['symbol'],
            signal['direction'],
            signal['entry_price'],
            signal['confidence'],
            signal['tier'],
            signal['filters_passed'],
            signal['formatted_message']
        ))
        conn.commit()
        conn.close()
        
    def get_recent_signals_by_tier(self, tier: str = None, limit: int = 10) -> List[Dict]:
        """Get recent signals filtered by tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tier:
            cursor.execute('''
                SELECT * FROM tiered_signals
                WHERE tier = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (tier, limit))
        else:
            cursor.execute('''
                SELECT * FROM tiered_signals
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'signal_id': row[1],
                'symbol': row[2],
                'direction': row[3],
                'entry_price': row[4],
                'confidence': row[5],
                'tier': row[6],
                'filters_passed': row[7],
                'formatted_message': row[8],
                'timestamp': row[9]
            })
            
        conn.close()
        return signals
        
    def get_daily_stats(self) -> Dict:
        """Get daily statistics by tier"""
        return {
            'daily_counts': self.daily_counts.copy(),
            'daily_limits': {tier: config['max_daily'] for tier, config in SIGNAL_TIERS.items()},
            'remaining': {
                tier: SIGNAL_TIERS[tier]['max_daily'] - self.daily_counts[tier] 
                for tier in SIGNAL_TIERS
            }
        }

# Global processor instance
processor = MT5TieredProcessor()

def process_live_mt5_data(data: Dict) -> Dict:
    """Process incoming MT5 data with tiered system"""
    return processor.process_mt5_tick(data)

def get_signals_by_tier(tier: str, limit: int = 10) -> List[Dict]:
    """Get recent signals for specific tier"""
    return processor.get_recent_signals_by_tier(tier, limit)

def get_daily_signal_stats() -> Dict:
    """Get daily signal statistics"""
    return processor.get_daily_stats()

if __name__ == "__main__":
    logger.info("MT5 Tiered Signal Processor initialized")
    logger.info(f"Monitoring pairs: {', '.join(TRADING_PAIRS)}")
    logger.info("Signal tiers: NIBBLER (75-80%), FANG (80-92%), COMMANDER (92-96%), APEX (96%+)")
    logger.info("Waiting for live market data...")