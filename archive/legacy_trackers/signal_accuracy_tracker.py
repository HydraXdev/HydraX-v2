#!/usr/bin/env python3
"""
📊 SIGNAL ACCURACY TRACKER
Tracks theoretical win rate of ALL signals regardless of whether they were fired
This shows what win rate would be if every signal was executed perfectly
"""

import sqlite3
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import requests
import time

logger = logging.getLogger(__name__)

@dataclass
class SignalAccuracy:
    """Theoretical signal performance tracking"""
    signal_id: str
    symbol: str
    direction: str
    signal_type: str  # RAPID_ASSAULT, SNIPER_OPS
    tcs_score: float
    
    # Signal data
    generated_at: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    # Theoretical outcome (tracked via market data)
    outcome: str = "PENDING"  # WIN, LOSS, PENDING, EXPIRED
    outcome_time: Optional[datetime] = None
    outcome_price: Optional[float] = None
    actual_pips: float = 0.0
    max_favorable_pips: float = 0.0
    max_adverse_pips: float = 0.0
    
    # Market conditions at signal time
    spread: float = 0.0
    session: str = "UNKNOWN"
    volatility_level: str = "NORMAL"

class SignalAccuracyDatabase:
    """Database for tracking all signal accuracy"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/signal_accuracy.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize signal accuracy database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # All signals accuracy tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                tcs_score REAL NOT NULL,
                
                generated_at TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                risk_reward_ratio REAL NOT NULL,
                
                outcome TEXT DEFAULT 'PENDING',
                outcome_time TIMESTAMP,
                outcome_price REAL,
                actual_pips REAL DEFAULT 0,
                max_favorable_pips REAL DEFAULT 0,
                max_adverse_pips REAL DEFAULT 0,
                
                spread REAL DEFAULT 0,
                session TEXT DEFAULT 'UNKNOWN',
                volatility_level TEXT DEFAULT 'NORMAL',
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # TCS correlation analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tcs_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                tcs_range TEXT NOT NULL,  -- "70-75", "76-80", etc.
                signal_type TEXT NOT NULL,
                
                total_signals INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pending INTEGER DEFAULT 0,
                
                win_rate REAL DEFAULT 0,
                avg_pips REAL DEFAULT 0,
                avg_rr_achieved REAL DEFAULT 0,
                
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(date, tcs_range, signal_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_signal(self, signal_accuracy: SignalAccuracy):
        """Store a new signal for accuracy tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO signal_accuracy (
                signal_id, symbol, direction, signal_type, tcs_score,
                generated_at, entry_price, stop_loss, take_profit, risk_reward_ratio,
                outcome, outcome_time, outcome_price, actual_pips, 
                max_favorable_pips, max_adverse_pips,
                spread, session, volatility_level, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            signal_accuracy.signal_id, signal_accuracy.symbol, signal_accuracy.direction,
            signal_accuracy.signal_type, signal_accuracy.tcs_score,
            signal_accuracy.generated_at, signal_accuracy.entry_price,
            signal_accuracy.stop_loss, signal_accuracy.take_profit, signal_accuracy.risk_reward_ratio,
            signal_accuracy.outcome, signal_accuracy.outcome_time, signal_accuracy.outcome_price,
            signal_accuracy.actual_pips, signal_accuracy.max_favorable_pips, signal_accuracy.max_adverse_pips,
            signal_accuracy.spread, signal_accuracy.session, signal_accuracy.volatility_level
        ))
        
        conn.commit()
        conn.close()
    
    def update_signal_outcome(self, signal_id: str, outcome: str, outcome_time: datetime, 
                            outcome_price: float, actual_pips: float):
        """Update signal outcome when TP/SL is hit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE signal_accuracy 
            SET outcome = ?, outcome_time = ?, outcome_price = ?, actual_pips = ?, updated_at = CURRENT_TIMESTAMP
            WHERE signal_id = ?
        ''', (outcome, outcome_time, outcome_price, actual_pips, signal_id))
        
        conn.commit()
        conn.close()
    
    def get_theoretical_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Get theoretical win rate for all signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                COUNT(CASE WHEN outcome = 'PENDING' THEN 1 END) as pending,
                AVG(tcs_score) as avg_tcs,
                AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN actual_pips END) as avg_pips,
                AVG(CASE WHEN outcome = 'WIN' THEN actual_pips END) as avg_win_pips,
                AVG(CASE WHEN outcome = 'LOSS' THEN actual_pips END) as avg_loss_pips
            FROM signal_accuracy 
            WHERE generated_at > datetime('now', '-{} hours')
        '''.format(hours))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            total = result[0]
            wins = result[1] or 0
            losses = result[2] or 0
            pending = result[3] or 0
            completed = wins + losses
            
            return {
                'total_signals': total,
                'wins': wins,
                'losses': losses,
                'pending': pending,
                'completed': completed,
                'theoretical_win_rate': wins / completed if completed > 0 else 0,
                'avg_tcs': result[4] or 0,
                'avg_pips': result[5] or 0,
                'avg_win_pips': result[6] or 0,
                'avg_loss_pips': result[7] or 0,
                'completion_rate': completed / total if total > 0 else 0
            }
        
        return {
            'total_signals': 0, 'wins': 0, 'losses': 0, 'pending': 0, 'completed': 0,
            'theoretical_win_rate': 0, 'avg_tcs': 0, 'avg_pips': 0,
            'avg_win_pips': 0, 'avg_loss_pips': 0, 'completion_rate': 0
        }
    
    def get_tcs_correlation(self, hours: int = 168) -> List[Dict]:
        """Get TCS score correlation with win rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN tcs_score >= 90 THEN '90+'
                    WHEN tcs_score >= 85 THEN '85-89'
                    WHEN tcs_score >= 80 THEN '80-84'
                    WHEN tcs_score >= 75 THEN '75-79'
                    WHEN tcs_score >= 70 THEN '70-74'
                    ELSE 'Below 70'
                END as tcs_range,
                signal_type,
                COUNT(*) as total,
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                AVG(tcs_score) as avg_tcs,
                AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN actual_pips END) as avg_pips
            FROM signal_accuracy 
            WHERE generated_at > datetime('now', '-{} hours')
            AND outcome IN ('WIN', 'LOSS')
            GROUP BY tcs_range, signal_type
            ORDER BY avg_tcs DESC, signal_type
        '''.format(hours))
        
        results = cursor.fetchall()
        conn.close()
        
        correlation_data = []
        for row in results:
            total_completed = row[3] + row[4]  # wins + losses
            if total_completed > 0:
                correlation_data.append({
                    'tcs_range': row[0],
                    'signal_type': row[1],
                    'total_signals': row[2],
                    'completed_signals': total_completed,
                    'wins': row[3],
                    'losses': row[4],
                    'win_rate': row[3] / total_completed,
                    'avg_tcs': row[5] or 0,
                    'avg_pips': row[6] or 0
                })
        
        return correlation_data

class SignalAccuracyTracker:
    """Real-time signal accuracy tracking system"""
    
    def __init__(self):
        self.db = SignalAccuracyDatabase()
        self.monitored_signals: Dict[str, SignalAccuracy] = {}
        self.monitoring_task = None
        
        # Bridge configuration for price checking
        self.bridge_ip = "localhost"
        self.bridge_port = 5555
    
    def track_signal(self, signal_data: Dict):
        """Start tracking a new signal for accuracy"""
        try:
            # Extract signal data
            signal_id = signal_data.get('mission_id', f"SIGNAL_{int(time.time())}")
            
            # Create signal accuracy object
            signal_accuracy = SignalAccuracy(
                signal_id=signal_id,
                symbol=signal_data.get('symbol', 'UNKNOWN'),
                direction=signal_data.get('direction', 'BUY'),
                signal_type=signal_data.get('signal_type', 'RAPID_ASSAULT'),
                tcs_score=signal_data.get('tcs', 0),
                generated_at=datetime.now(),
                entry_price=signal_data.get('entry_price', 0),
                stop_loss=signal_data.get('stop_loss', 0),
                take_profit=signal_data.get('take_profit', 0),
                risk_reward_ratio=signal_data.get('risk_reward_ratio', 2.0),
                spread=signal_data.get('spread', 0),
                session=self._get_current_session(),
                volatility_level="NORMAL"
            )
            
            # Store in database
            self.db.store_signal(signal_accuracy)
            
            # Add to monitoring
            self.monitored_signals[signal_id] = signal_accuracy
            
            logger.info(f"📊 Started tracking signal {signal_id}: {signal_accuracy.symbol} {signal_accuracy.direction} TCS:{signal_accuracy.tcs_score}%")
            
        except Exception as e:
            logger.error(f"Error tracking signal: {e}")
    
    def _get_current_session(self) -> str:
        """Determine current trading session"""
        hour = datetime.utcnow().hour
        if 7 <= hour < 16:
            return "LONDON"
        elif 13 <= hour < 22:
            return "NY"
        elif 7 <= hour < 9 or 13 <= hour < 16:
            return "OVERLAP"
        elif 23 <= hour or hour < 7:
            return "ASIAN"
        else:
            return "OTHER"
    
    async def start_monitoring(self):
        """Start monitoring signals for outcomes"""
        logger.info("🔍 Starting signal accuracy monitoring...")
        self.monitoring_task = asyncio.create_task(self._monitor_signals())
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
    
    async def _monitor_signals(self):
        """Monitor pending signals for TP/SL hits"""
        while True:
            try:
                pending_signals = [s for s in self.monitored_signals.values() if s.outcome == "PENDING"]
                
                for signal in pending_signals:
                    await self._check_signal_outcome(signal)
                
                # Check for expired signals (older than 4 hours)
                await self._check_expired_signals()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Signal monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_signal_outcome(self, signal: SignalAccuracy):
        """Check if signal hit TP or SL"""
        try:
            # Get current price from bridge
            current_price = await self._get_current_price(signal.symbol)
            if not current_price:
                return
            
            # Check for TP/SL hit
            outcome = None
            outcome_price = current_price
            
            if signal.direction == "BUY":
                if current_price >= signal.take_profit:
                    outcome = "WIN"
                    outcome_price = signal.take_profit
                elif current_price <= signal.stop_loss:
                    outcome = "LOSS"
                    outcome_price = signal.stop_loss
            else:  # SELL
                if current_price <= signal.take_profit:
                    outcome = "WIN"
                    outcome_price = signal.take_profit
                elif current_price >= signal.stop_loss:
                    outcome = "LOSS"
                    outcome_price = signal.stop_loss
            
            if outcome:
                # Calculate pips
                if signal.direction == "BUY":
                    pips = (outcome_price - signal.entry_price) * 10000
                else:
                    pips = (signal.entry_price - outcome_price) * 10000
                
                # Update signal
                signal.outcome = outcome
                signal.outcome_time = datetime.now()
                signal.outcome_price = outcome_price
                signal.actual_pips = pips
                
                # Update database
                self.db.update_signal_outcome(
                    signal.signal_id, outcome, signal.outcome_time, outcome_price, pips
                )
                
                logger.info(f"🎯 Signal {signal.signal_id} completed: {outcome} ({pips:.1f} pips)")
                
        except Exception as e:
            logger.error(f"Error checking signal {signal.signal_id}: {e}")
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from bridge"""
        try:
            # This would connect to your bridge to get real price
            # For now, return None to indicate price unavailable
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    async def _check_expired_signals(self):
        """Mark old signals as expired"""
        cutoff_time = datetime.now() - timedelta(hours=4)
        
        for signal in self.monitored_signals.values():
            if signal.outcome == "PENDING" and signal.generated_at < cutoff_time:
                signal.outcome = "EXPIRED"
                signal.outcome_time = datetime.now()
                
                self.db.update_signal_outcome(
                    signal.signal_id, "EXPIRED", signal.outcome_time, 0, 0
                )
                
                logger.info(f"⏰ Signal {signal.signal_id} marked as expired")
    
    def get_theoretical_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Get theoretical performance stats"""
        performance = self.db.get_theoretical_performance(hours)
        
        # Add TCS correlation
        correlation = self.db.get_tcs_correlation(hours)
        performance['tcs_correlation'] = correlation
        
        return performance
    
    def get_accuracy_summary(self) -> str:
        """Get formatted accuracy summary"""
        stats = self.get_theoretical_performance(24)
        
        summary = f"""
📊 SIGNAL ACCURACY TRACKER (24H)
================================
🎯 Total Signals: {stats['total_signals']}
✅ Completed: {stats['completed']} ({stats['completion_rate']:.1%})
🏆 Theoretical Win Rate: {stats['theoretical_win_rate']:.1%}
📈 Average TCS: {stats['avg_tcs']:.1f}%
💰 Average Pips: {stats['avg_pips']:.1f}

📋 TCS CORRELATION:"""
        
        for corr in stats['tcs_correlation']:
            summary += f"\n  {corr['tcs_range']} TCS ({corr['signal_type']}): {corr['win_rate']:.1%} win rate"
        
        return summary

# Global tracker instance
signal_accuracy_tracker = SignalAccuracyTracker()

# Integration function for 
def track_apex_signal(signal_data: Dict):
    """Track signal for accuracy analysis"""
    signal_accuracy_tracker.track_signal(signal_data)

# Example usage
if __name__ == "__main__":
    async def test():
        tracker = SignalAccuracyTracker()
        await tracker.start_monitoring()
        
        # Test signal
        test_signal = {
            'mission_id': 'TEST_001',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'signal_type': 'RAPID_ASSAULT',
            'tcs': 85,
            'entry_price': 1.0900,
            'stop_loss': 1.0880,
            'take_profit': 1.0940,
            'risk_reward_ratio': 2.0
        }
        
        tracker.track_signal(test_signal)
        print("Signal tracking started...")
        
        await asyncio.sleep(10)
        print(tracker.get_accuracy_summary())
    
    asyncio.run(test())