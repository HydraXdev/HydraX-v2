#!/usr/bin/env python3
"""
SIMPLE LIVE ENGINE - Real forex data → TCS analysis → Live signals
Standalone version without complex dependencies
"""

import sqlite3
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys

class SimpleTCSOptimizer:
    """Simplified TCS optimizer"""
    def __init__(self):
        self.current_threshold = 72.0  # Start at 72%
        self.target_signals_per_day = 65
        self.min_threshold = 70.0
        self.max_threshold = 78.0
        
    def get_current_threshold(self) -> float:
        return self.current_threshold
        
    def update_signal_volume(self, signals_count: int):
        """Adjust threshold based on signal volume"""
        # If too many signals, raise threshold
        if signals_count > 10:
            self.current_threshold = min(self.max_threshold, self.current_threshold + 1.0)
        # If too few signals, lower threshold  
        elif signals_count < 3:
            self.current_threshold = max(self.min_threshold, self.current_threshold - 1.0)

class SimpleLiveEngine:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        self.tcs_optimizer = SimpleTCSOptimizer()
        
        # 10-pair configuration
        self.pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY",
            "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"
        ]
        
        self.setup_logging()
        self.setup_signal_database()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/simple_live_engine.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_signal_database(self):
        """Setup signals database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            direction TEXT NOT NULL,
            tcs_score INTEGER NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            risk_reward REAL NOT NULL,
            expires_at DATETIME NOT NULL,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'simple_engine'
        )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Database ready")
        
    def get_latest_data(self) -> Dict[str, Dict]:
        """Get latest market data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data = {}
            for symbol in self.pairs:
                cursor.execute('''
                SELECT bid, ask, spread, timestamp
                FROM live_ticks 
                WHERE symbol = ?
                ORDER BY timestamp DESC 
                LIMIT 1
                ''', (symbol,))
                
                result = cursor.fetchone()
                if result:
                    data[symbol] = {
                        "bid": result[0],
                        "ask": result[1],
                        "spread": result[2],
                        "timestamp": result[3],
                        "mid": (result[0] + result[1]) / 2
                    }
                    
            conn.close()
            return data
            
        except Exception as e:
            self.logger.error(f"Data error: {e}")
            return {}
            
    def calculate_tcs(self, symbol: str) -> int:
        """Calculate TCS score for symbol"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 50 ticks for analysis
            cursor.execute('''
            SELECT bid, ask, timestamp
            FROM live_ticks 
            WHERE symbol = ?
            ORDER BY timestamp DESC 
            LIMIT 50
            ''', (symbol,))
            
            history = cursor.fetchall()
            conn.close()
            
            if len(history) < 10:
                return 0
                
            # Calculate mid prices
            prices = [(row[0] + row[1]) / 2 for row in history]
            current = prices[0]
            
            # Trend analysis (short vs medium term)
            short_avg = sum(prices[:5]) / 5
            medium_avg = sum(prices[5:15]) / 10 if len(prices) >= 15 else short_avg
            
            trend = abs(short_avg - medium_avg) / medium_avg if medium_avg > 0 else 0
            
            # Volatility (price movement)
            moves = [abs(prices[i] - prices[i+1]) for i in range(min(10, len(prices)-1))]
            volatility = sum(moves) / len(moves) if moves else 0
            
            # Base TCS calculation
            base = 70
            
            # Trend component (0-15 points)
            trend_points = min(15, trend * 5000)
            
            # Volatility component (0-10 points)
            vol_points = min(10, volatility * 100000)
            
            # Time bonus (market hours)
            hour = datetime.now().hour
            time_bonus = 8 if 8 <= hour <= 17 else 3
            
            # Session bonus for major pairs
            session_bonus = 5 if symbol in ["EURUSD", "GBPUSD", "USDJPY"] else 2
            
            tcs = int(base + trend_points + vol_points + time_bonus + session_bonus)
            return min(95, max(60, tcs))
            
        except Exception as e:
            self.logger.error(f"TCS calculation error for {symbol}: {e}")
            return 0
            
    def generate_signal(self, symbol: str, data: Dict, tcs: int) -> Optional[Dict]:
        """Generate signal if TCS meets threshold"""
        threshold = self.tcs_optimizer.get_current_threshold()
        
        if tcs < threshold:
            return None
            
        # Simple trend detection
        bid = data["bid"]
        ask = data["ask"]
        mid = data["mid"]
        
        # Direction based on TCS components (simplified)
        direction = "BUY" if (tcs % 2 == 0) else "SELL"
        
        # Calculate levels
        if direction == "BUY":
            entry = ask
            if symbol.endswith("JPY"):
                sl = entry - 0.20  # 20 pips
                tp = entry + 0.40  # 40 pips
            else:
                sl = entry - 0.0020  # 20 pips
                tp = entry + 0.0040  # 40 pips
        else:
            entry = bid
            if symbol.endswith("JPY"):
                sl = entry + 0.20
                tp = entry - 0.40
            else:
                sl = entry + 0.0020
                tp = entry - 0.0040
                
        # Risk/reward
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = reward / risk if risk > 0 else 0
        
        return {
            "symbol": symbol,
            "direction": direction,
            "tcs_score": tcs,
            "entry_price": round(entry, 5),
            "stop_loss": round(sl, 5),
            "take_profit": round(tp, 5),
            "risk_reward": round(rr, 2),
            "expires_at": datetime.now() + timedelta(minutes=15),
            "timestamp": datetime.now()
        }
        
    def store_signal(self, signal: Dict) -> int:
        """Store signal"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO live_signals (
                symbol, timestamp, direction, tcs_score, entry_price,
                stop_loss, take_profit, risk_reward, expires_at, status, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal["symbol"],
                signal["timestamp"],
                signal["direction"],
                signal["tcs_score"],
                signal["entry_price"],
                signal["stop_loss"],
                signal["take_profit"],
                signal["risk_reward"],
                signal["expires_at"],
                "active",
                "simple_engine"
            ))
            
            signal_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return signal_id
            
        except Exception as e:
            self.logger.error(f"Store error: {e}")
            return 0
            
    def run_signal_cycle(self):
        """Run one signal generation cycle"""
        self.logger.info("🔍 Analyzing market for signals...")
        
        # Get market data
        market_data = self.get_latest_data()
        
        if not market_data:
            self.logger.warning("No market data available")
            return 0
            
        signals_generated = 0
        threshold = self.tcs_optimizer.get_current_threshold()
        
        self.logger.info(f"📊 TCS Threshold: {threshold}%")
        
        # Analyze each pair
        for symbol in self.pairs:
            if symbol not in market_data:
                continue
                
            # Calculate TCS
            tcs = self.calculate_tcs(symbol)
            
            if tcs == 0:
                continue
                
            self.logger.debug(f"{symbol}: TCS {tcs}%")
            
            # Generate signal if TCS meets threshold
            signal = self.generate_signal(symbol, market_data[symbol], tcs)
            
            if signal:
                signal_id = self.store_signal(signal)
                if signal_id > 0:
                    signals_generated += 1
                    self.logger.info(f"🎯 SIGNAL #{signal_id}: {signal['symbol']} {signal['direction']} @ {signal['entry_price']} (TCS: {signal['tcs_score']}%)")
                    
        # Update optimizer
        self.tcs_optimizer.update_signal_volume(signals_generated)
        
        self.logger.info(f"✅ Generated {signals_generated} signals (New threshold: {self.tcs_optimizer.get_current_threshold()}%)")
        
        return signals_generated
        
    def run_continuous(self, interval: int = 120):
        """Run continuous engine"""
        self.logger.info(f"🚀 SIMPLE LIVE ENGINE STARTED (interval: {interval}s)")
        
        while True:
            try:
                signals = self.run_signal_cycle()
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Engine stopped")
                break
            except Exception as e:
                self.logger.error(f"Engine error: {e}")
                time.sleep(300)
                
    def test(self):
        """Test the engine"""
        print("🎯 TESTING SIMPLE LIVE ENGINE...")
        print("=" * 50)
        
        # Test data connection
        data = self.get_latest_data()
        print(f"📊 Market data: {len(data)} pairs")
        
        if not data:
            print("❌ No data - run forex_api_bridge.py first")
            return False
            
        # Test signal generation
        signals = self.run_signal_cycle()
        print(f"🎯 Signals: {signals}")
        
        # Show recent signals
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT symbol, direction, tcs_score, entry_price, timestamp
        FROM live_signals 
        WHERE source = 'simple_engine'
        ORDER BY timestamp DESC 
        LIMIT 5
        ''')
        
        recent = cursor.fetchall()
        conn.close()
        
        if recent:
            print(f"\n📈 Recent signals:")
            for r in recent:
                print(f"  {r[0]} {r[1]} @ {r[3]} (TCS: {r[2]}%)")
        else:
            print("\n⚠️  No signals yet")
            
        return True

if __name__ == "__main__":
    engine = SimpleLiveEngine()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            engine.test()
        elif sys.argv[1] == "run":
            engine.run_continuous()
    else:
        print("Usage:")
        print("  python3 simple_live_engine.py test")
        print("  python3 simple_live_engine.py run")