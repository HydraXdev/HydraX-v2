#!/usr/bin/env python3
"""
LIVE SIGNAL ENGINE - Real forex data → TCS analysis → Live signals
Connects Forex API Bridge to Self-Optimizing TCS Engine
"""

import sqlite3
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import sys
import os

# Add project path
sys.path.append('/root/HydraX-v2/src')
from bitten_core.self_optimizing_tcs import SelfOptimizingTCS, TCSOptimizationConfig

class LiveSignalEngine:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # Initialize TCS optimizer
        self.tcs_config = TCSOptimizationConfig(
            target_signals_per_day=65,
            min_tcs_threshold=70.0,
            max_tcs_threshold=78.0,
            target_win_rate=0.85,
            adjustment_interval_hours=4
        )
        
        self.tcs_optimizer = SelfOptimizingTCS(self.tcs_config)
        
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
                logging.FileHandler('/root/HydraX-v2/logs/live_signals.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_signal_database(self):
        """Setup live signals database"""
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
            source TEXT DEFAULT 'live_engine'
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            timestamp DATETIME NOT NULL,
            result TEXT, -- 'win', 'loss', 'pending'
            pips_result REAL,
            duration_minutes INTEGER,
            tcs_accuracy REAL,
            FOREIGN KEY (signal_id) REFERENCES live_signals(id)
        )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Signal database ready")
        
    def get_latest_market_data(self) -> Dict[str, Dict]:
        """Get latest tick data for all pairs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            market_data = {}
            
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
                    market_data[symbol] = {
                        "bid": result[0],
                        "ask": result[1],
                        "spread": result[2],
                        "timestamp": result[3],
                        "mid": (result[0] + result[1]) / 2
                    }
                    
            conn.close()
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return {}
            
    def analyze_market_structure(self, symbol: str) -> Dict:
        """Analyze market structure for TCS calculation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent price history (last 100 ticks)
            cursor.execute('''
            SELECT bid, ask, timestamp
            FROM live_ticks 
            WHERE symbol = ?
            ORDER BY timestamp DESC 
            LIMIT 100
            ''', (symbol,))
            
            history = cursor.fetchall()
            conn.close()
            
            if len(history) < 10:
                return {"tcs_score": 0, "reason": "Insufficient data"}
                
            # Calculate basic technical indicators
            prices = [(row[0] + row[1]) / 2 for row in history]
            current_price = prices[0]
            
            # Trend detection (last 20 vs last 10)
            recent_avg = sum(prices[:10]) / 10
            older_avg = sum(prices[10:20]) / 10 if len(prices) >= 20 else recent_avg
            
            trend_strength = abs(recent_avg - older_avg) / older_avg if older_avg > 0 else 0
            trend_direction = "UP" if recent_avg > older_avg else "DOWN"
            
            # Volatility assessment
            price_changes = [abs(prices[i] - prices[i+1]) for i in range(len(prices)-1)]
            volatility = sum(price_changes[:20]) / 20 if len(price_changes) >= 20 else 0
            
            # Support/Resistance levels
            max_price = max(prices[:20])
            min_price = min(prices[:20])
            price_range = max_price - min_price
            
            # Basic TCS calculation
            base_score = 70
            
            # Trend component (0-10 points)
            trend_score = min(10, trend_strength * 1000)
            
            # Volatility component (0-8 points) 
            vol_score = min(8, volatility * 50000) if volatility > 0 else 0
            
            # Position in range (0-7 points)
            if price_range > 0:
                range_position = (current_price - min_price) / price_range
                range_score = 7 if 0.2 <= range_position <= 0.8 else 3
            else:
                range_score = 5
                
            # Time-based bonus (market session activity)
            current_hour = datetime.now().hour
            session_bonus = 5 if 8 <= current_hour <= 17 else 2  # NY/London hours
            
            final_tcs = int(base_score + trend_score + vol_score + range_score + session_bonus)
            final_tcs = min(95, max(60, final_tcs))  # Clamp between 60-95
            
            return {
                "tcs_score": final_tcs,
                "trend_direction": trend_direction,
                "trend_strength": trend_strength,
                "volatility": volatility,
                "range_position": range_position if price_range > 0 else 0.5,
                "session_bonus": session_bonus,
                "components": {
                    "base": base_score,
                    "trend": trend_score,
                    "volatility": vol_score,
                    "range": range_score,
                    "session": session_bonus
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {"tcs_score": 0, "reason": str(e)}
            
    def generate_signal(self, symbol: str, market_data: Dict, analysis: Dict) -> Optional[Dict]:
        """Generate trading signal if conditions are met"""
        try:
            current_tcs = self.tcs_optimizer.get_current_threshold()
            tcs_score = analysis["tcs_score"]
            
            # Check if TCS meets current threshold
            if tcs_score < current_tcs:
                return None
                
            # Get current market prices
            bid = market_data["bid"]
            ask = market_data["ask"]
            spread = market_data["spread"]
            
            # Determine direction based on trend
            direction = analysis["trend_direction"]
            
            # Calculate entry, SL, TP based on direction
            if direction == "UP":
                entry_price = ask
                # SL: 20 pips below entry
                if symbol.endswith("JPY"):
                    stop_loss = entry_price - 0.20
                    take_profit = entry_price + 0.40  # 40 pips TP
                else:
                    stop_loss = entry_price - 0.0020
                    take_profit = entry_price + 0.0040  # 40 pips TP
            else:  # DOWN
                entry_price = bid
                if symbol.endswith("JPY"):
                    stop_loss = entry_price + 0.20
                    take_profit = entry_price - 0.40
                else:
                    stop_loss = entry_price + 0.0020
                    take_profit = entry_price - 0.0040
                    
            # Calculate risk:reward
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Signal expires in 15 minutes
            expires_at = datetime.now() + timedelta(minutes=15)
            
            signal = {
                "symbol": symbol,
                "direction": direction,
                "tcs_score": tcs_score,
                "entry_price": round(entry_price, 5),
                "stop_loss": round(stop_loss, 5),
                "take_profit": round(take_profit, 5),
                "risk_reward": round(risk_reward, 2),
                "expires_at": expires_at,
                "spread": spread,
                "timestamp": datetime.now(),
                "analysis": analysis
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None
            
    def store_signal(self, signal: Dict) -> int:
        """Store signal in database"""
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
                "live_engine"
            ))
            
            signal_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return signal_id
            
        except Exception as e:
            self.logger.error(f"Error storing signal: {e}")
            return 0
            
    def run_signal_generation_cycle(self):
        """Run one complete signal generation cycle"""
        self.logger.info("🔍 Running signal generation cycle...")
        
        # Get latest market data
        market_data = self.get_latest_market_data()
        
        if not market_data:
            self.logger.warning("No market data available")
            return 0
            
        signals_generated = 0
        current_threshold = self.tcs_optimizer.get_current_threshold()
        
        self.logger.info(f"📊 Current TCS threshold: {current_threshold}%")
        
        # Analyze each pair for signals
        for symbol in self.pairs:
            if symbol not in market_data:
                self.logger.warning(f"No data for {symbol}")
                continue
                
            # Analyze market structure
            analysis = self.analyze_market_structure(symbol)
            
            if analysis["tcs_score"] == 0:
                continue
                
            # Generate signal if conditions met
            signal = self.generate_signal(symbol, market_data[symbol], analysis)
            
            if signal:
                signal_id = self.store_signal(signal)
                if signal_id > 0:
                    signals_generated += 1
                    self.logger.info(f"🎯 SIGNAL: {signal['symbol']} {signal['direction']} @ {signal['entry_price']} (TCS: {signal['tcs_score']}%)")
                    
        self.logger.info(f"✅ Generated {signals_generated} signals")
        
        # Update TCS optimizer with signal volume
        if signals_generated > 0:
            self.tcs_optimizer.update_signal_volume(signals_generated)
            
        return signals_generated
        
    def run_continuous_engine(self, interval: int = 120):
        """Run continuous signal generation"""
        self.logger.info(f"🚀 Starting Live Signal Engine (interval: {interval}s)")
        
        while True:
            try:
                signals = self.run_signal_generation_cycle()
                
                if signals == 0:
                    self.logger.info("No signals generated this cycle")
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Engine stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Engine error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
                
    def test_signal_generation(self):
        """Test signal generation"""
        print("🎯 TESTING LIVE SIGNAL ENGINE...")
        print("=" * 50)
        
        # Test market data
        market_data = self.get_latest_market_data()
        print(f"📊 Market data: {len(market_data)} pairs available")
        
        if not market_data:
            print("❌ No market data - start forex_api_bridge.py first")
            return False
            
        # Test TCS optimizer
        current_threshold = self.tcs_optimizer.get_current_threshold()
        print(f"🔧 TCS threshold: {current_threshold}%")
        
        # Test signal generation
        signals = self.run_signal_generation_cycle()
        print(f"🎯 Signals generated: {signals}")
        
        # Show recent signals
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT symbol, direction, tcs_score, entry_price, timestamp
        FROM live_signals 
        ORDER BY timestamp DESC 
        LIMIT 5
        ''')
        
        recent_signals = cursor.fetchall()
        conn.close()
        
        if recent_signals:
            print(f"\n📈 Recent signals:")
            for signal in recent_signals:
                print(f"  {signal[0]} {signal[1]} @ {signal[3]} (TCS: {signal[2]}%) - {signal[4]}")
        else:
            print("\n⚠️  No recent signals")
            
        return len(recent_signals) > 0

if __name__ == "__main__":
    engine = LiveSignalEngine()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            engine.test_signal_generation()
        elif sys.argv[1] == "run":
            engine.run_continuous_engine()
    else:
        print("Usage:")
        print("  python3 live_signal_engine.py test  - Test signal generation")
        print("  python3 live_signal_engine.py run   - Run continuous engine")