#!/usr/bin/env python3
"""
TCS Performance Tracker
Advanced performance tracking system for TCS optimization
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

from .self_optimizing_tcs import MarketCondition
from .signal_fusion import FusedSignal
from .mt5_enhanced_adapter import MT5EnhancedAdapter

logger = logging.getLogger(__name__)

@dataclass
class TradePerformance:
    """Complete trade performance data"""
    signal_id: str
    ticket: int
    pair: str
    direction: str
    confidence: float
    tcs_threshold: float
    
    # Entry data
    entry_time: datetime
    entry_price: float
    lot_size: float
    
    # Exit data
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    
    # Performance metrics
    pips_gained: float = 0.0
    profit_usd: float = 0.0
    hold_time_minutes: int = 0
    max_drawdown: float = 0.0
    max_profit: float = 0.0
    
    # Market conditions
    market_condition: Optional[MarketCondition] = None
    volatility_at_entry: float = 0.0
    spread_at_entry: float = 0.0
    
    # Classification
    result: str = "PENDING"  # WIN, LOSS, PENDING, BREAKEVEN
    exit_type: str = "UNKNOWN"  # TP, SL, MANUAL, TRAILING
    
    # User data
    user_id: Optional[int] = None
    user_tier: Optional[str] = None

class TCSPerformanceDatabase:
    """Database for storing TCS performance data"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/tcs_performance.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize performance database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trade performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                ticket INTEGER NOT NULL,
                pair TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                tcs_threshold REAL NOT NULL,
                
                entry_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                lot_size REAL NOT NULL,
                
                exit_time TIMESTAMP,
                exit_price REAL,
                
                pips_gained REAL DEFAULT 0,
                profit_usd REAL DEFAULT 0,
                hold_time_minutes INTEGER DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                max_profit REAL DEFAULT 0,
                
                volatility_at_entry REAL DEFAULT 0,
                spread_at_entry REAL DEFAULT 0,
                
                result TEXT DEFAULT 'PENDING',
                exit_type TEXT DEFAULT 'UNKNOWN',
                
                user_id INTEGER,
                user_tier TEXT,
                
                market_condition TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # TCS threshold history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tcs_threshold_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pair TEXT NOT NULL,
                old_threshold REAL,
                new_threshold REAL,
                reason TEXT,
                market_condition TEXT,
                signals_24h INTEGER,
                win_rate_24h REAL,
                performance_impact REAL
            )
        ''')
        
        # Signal volume tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_volume_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                pair TEXT NOT NULL,
                hour INTEGER NOT NULL,
                signals_generated INTEGER DEFAULT 0,
                signals_executed INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                avg_tcs_threshold REAL DEFAULT 0,
                execution_rate REAL DEFAULT 0,
                
                PRIMARY KEY (date, pair, hour)
            ) WITHOUT ROWID
        ''')
        
        # Market condition analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_condition_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pair TEXT NOT NULL,
                volatility_level TEXT NOT NULL,
                session_activity TEXT NOT NULL,
                trend_strength REAL NOT NULL,
                news_impact REAL NOT NULL,
                
                optimal_threshold REAL NOT NULL,
                signals_count INTEGER DEFAULT 0,
                avg_performance REAL DEFAULT 0,
                win_rate REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_trade_performance(self, performance: TradePerformance):
        """Store trade performance data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert market condition to JSON string
        market_condition_json = json.dumps(asdict(performance.market_condition)) if performance.market_condition else None
        
        cursor.execute('''
            INSERT INTO trade_performance (
                signal_id, ticket, pair, direction, confidence, tcs_threshold,
                entry_time, entry_price, lot_size, exit_time, exit_price,
                pips_gained, profit_usd, hold_time_minutes, max_drawdown, max_profit,
                volatility_at_entry, spread_at_entry, result, exit_type,
                user_id, user_tier, market_condition
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            performance.signal_id, performance.ticket, performance.pair, performance.direction,
            performance.confidence, performance.tcs_threshold,
            performance.entry_time, performance.entry_price, performance.lot_size,
            performance.exit_time, performance.exit_price,
            performance.pips_gained, performance.profit_usd, performance.hold_time_minutes,
            performance.max_drawdown, performance.max_profit,
            performance.volatility_at_entry, performance.spread_at_entry,
            performance.result, performance.exit_type,
            performance.user_id, performance.user_tier, market_condition_json
        ))
        
        conn.commit()
        conn.close()
    
    def update_trade_performance(self, ticket: int, **updates):
        """Update trade performance data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE trade_performance SET {set_clause} WHERE ticket = ?"
        
        cursor.execute(query, list(updates.values()) + [ticket])
        conn.commit()
        conn.close()
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN result = 'LOSS' THEN 1 END) as losses,
                AVG(confidence) as avg_confidence,
                AVG(tcs_threshold) as avg_threshold,
                AVG(pips_gained) as avg_pips,
                AVG(profit_usd) as avg_profit,
                AVG(hold_time_minutes) as avg_hold_time,
                AVG(max_drawdown) as avg_max_drawdown,
                AVG(max_profit) as avg_max_profit
            FROM trade_performance 
            WHERE entry_time > datetime('now', '-{} hours')
            AND result != 'PENDING'
        '''.format(hours))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {
                'total_trades': result[0],
                'wins': result[1] or 0,
                'losses': result[2] or 0,
                'win_rate': (result[1] or 0) / result[0],
                'avg_confidence': result[3] or 0,
                'avg_threshold': result[4] or 0,
                'avg_pips': result[5] or 0,
                'avg_profit': result[6] or 0,
                'avg_hold_time': result[7] or 0,
                'avg_max_drawdown': result[8] or 0,
                'avg_max_profit': result[9] or 0
            }
        
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'avg_confidence': 0,
            'avg_threshold': 0,
            'avg_pips': 0,
            'avg_profit': 0,
            'avg_hold_time': 0,
            'avg_max_drawdown': 0,
            'avg_max_profit': 0
        }
    
    def get_threshold_effectiveness(self, pair: str, hours: int = 168) -> List[Dict]:
        """Get threshold effectiveness analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ROUND(tcs_threshold, 1) as threshold,
                COUNT(*) as trade_count,
                COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                AVG(pips_gained) as avg_pips,
                AVG(profit_usd) as avg_profit,
                AVG(confidence) as avg_confidence
            FROM trade_performance 
            WHERE pair = ? 
            AND entry_time > datetime('now', '-{} hours')
            AND result != 'PENDING'
            GROUP BY ROUND(tcs_threshold, 1)
            ORDER BY threshold
        '''.format(hours), (pair,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'threshold': row[0],
                'trade_count': row[1],
                'wins': row[2],
                'win_rate': row[2] / row[1] if row[1] > 0 else 0,
                'avg_pips': row[3] or 0,
                'avg_profit': row[4] or 0,
                'avg_confidence': row[5] or 0
            }
            for row in results
        ]
    
    def store_threshold_adjustment(self, pair: str, old_threshold: float, 
                                  new_threshold: float, reason: str,
                                  market_condition: MarketCondition,
                                  signals_24h: int, win_rate_24h: float):
        """Store threshold adjustment event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tcs_threshold_history (
                pair, old_threshold, new_threshold, reason, market_condition,
                signals_24h, win_rate_24h
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            pair, old_threshold, new_threshold, reason,
            json.dumps(asdict(market_condition)),
            signals_24h, win_rate_24h
        ))
        
        conn.commit()
        conn.close()

class AdvancedTCSPerformanceTracker:
    """Advanced performance tracking with real-time monitoring"""
    
    def __init__(self, mt5_adapter: MT5EnhancedAdapter):
        self.mt5_adapter = mt5_adapter
        self.db = TCSPerformanceDatabase()
        self.active_trades: Dict[int, TradePerformance] = {}
        self.position_monitoring_task = None
        
    async def start_monitoring(self):
        """Start real-time position monitoring"""
        logger.info("Starting advanced TCS performance monitoring...")
        self.position_monitoring_task = asyncio.create_task(self._monitor_positions())
    
    async def stop_monitoring(self):
        """Stop position monitoring"""
        if self.position_monitoring_task:
            self.position_monitoring_task.cancel()
    
    async def _monitor_positions(self):
        """Monitor active positions for performance tracking"""
        while True:
            try:
                # Get current positions
                positions_data = self.mt5_adapter.get_positions()
                current_positions = positions_data.get('positions', [])
                
                # Update active trades
                for position in current_positions:
                    ticket = position.get('ticket')
                    if ticket in self.active_trades:
                        await self._update_position_metrics(ticket, position)
                
                # Check for closed positions
                await self._check_closed_positions()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Position monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _update_position_metrics(self, ticket: int, position: Dict):
        """Update real-time position metrics"""
        trade = self.active_trades[ticket]
        
        # Calculate current metrics
        current_price = position.get('price_current', trade.entry_price)
        current_profit = position.get('profit', 0)
        
        # Calculate pips
        if trade.direction == 'BUY':
            pips = (current_price - trade.entry_price) * 10000
        else:
            pips = (trade.entry_price - current_price) * 10000
        
        # Update max profit and drawdown
        trade.max_profit = max(trade.max_profit, current_profit)
        if current_profit < 0:
            trade.max_drawdown = max(trade.max_drawdown, abs(current_profit))
        
        # Update current values
        trade.pips_gained = pips
        trade.profit_usd = current_profit
        trade.hold_time_minutes = int((datetime.now() - trade.entry_time).total_seconds() / 60)
    
    async def _check_closed_positions(self):
        """Check for positions that have been closed"""
        # Get list of active tickets
        positions_data = self.mt5_adapter.get_positions()
        active_tickets = {p.get('ticket') for p in positions_data.get('positions', [])}
        
        # Find closed positions
        closed_tickets = set(self.active_trades.keys()) - active_tickets
        
        for ticket in closed_tickets:
            await self._finalize_trade(ticket)
    
    async def _finalize_trade(self, ticket: int):
        """Finalize a closed trade"""
        if ticket not in self.active_trades:
            return
        
        trade = self.active_trades[ticket]
        
        # Mark as closed
        trade.exit_time = datetime.now()
        trade.result = 'WIN' if trade.profit_usd > 0 else 'LOSS'
        if abs(trade.profit_usd) < 0.01:  # Less than 1 cent
            trade.result = 'BREAKEVEN'
        
        # Determine exit type (simplified)
        if trade.profit_usd > 0:
            trade.exit_type = 'TP'
        else:
            trade.exit_type = 'SL'
        
        # Store in database
        self.db.store_trade_performance(trade)
        
        # Remove from active trades
        del self.active_trades[ticket]
        
        logger.info(f"Finalized trade {ticket}: {trade.result} "
                   f"({trade.pips_gained:.1f} pips, ${trade.profit_usd:.2f})")
    
    async def track_signal_execution(self, signal: FusedSignal, ticket: int,
                                   tcs_threshold: float, market_condition: MarketCondition,
                                   user_id: int, user_tier: str, position_data: Dict):
        """Track a new signal execution"""
        
        # Get position details
        entry_price = position_data.get('price', 0)
        lot_size = position_data.get('volume', 0)
        
        # Get market data
        market_data = self.mt5_adapter.get_market_data()
        volatility = market_data.get('atr', 0) if market_data else 0
        spread = market_data.get('spread', 0) if market_data else 0
        
        # Create performance record
        performance = TradePerformance(
            signal_id=signal.signal_id,
            ticket=ticket,
            pair=signal.pair,
            direction=signal.direction,
            confidence=signal.confidence,
            tcs_threshold=tcs_threshold,
            entry_time=datetime.now(),
            entry_price=entry_price,
            lot_size=lot_size,
            market_condition=market_condition,
            volatility_at_entry=volatility,
            spread_at_entry=spread,
            user_id=user_id,
            user_tier=user_tier
        )
        
        # Store in active trades
        self.active_trades[ticket] = performance
        
        logger.info(f"Started tracking trade {ticket} for signal {signal.signal_id}")
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time performance statistics"""
        # Active trades stats
        active_count = len(self.active_trades)
        active_profit = sum(trade.profit_usd for trade in self.active_trades.values())
        active_pips = sum(trade.pips_gained for trade in self.active_trades.values())
        
        # Database stats
        db_stats = self.db.get_performance_metrics(24)
        
        return {
            'active_trades': {
                'count': active_count,
                'total_profit': active_profit,
                'total_pips': active_pips,
                'avg_hold_time': np.mean([trade.hold_time_minutes for trade in self.active_trades.values()]) if self.active_trades else 0
            },
            'last_24h': db_stats,
            'monitoring_active': self.position_monitoring_task is not None and not self.position_monitoring_task.done()
        }
    
    def get_threshold_analysis(self, pair: str) -> Dict[str, Any]:
        """Get threshold effectiveness analysis"""
        effectiveness = self.db.get_threshold_effectiveness(pair)
        
        if not effectiveness:
            return {
                'optimal_threshold': 75.0,
                'confidence_level': 0.5,
                'analysis': 'Insufficient data'
            }
        
        # Find optimal threshold (highest win rate with reasonable sample size)
        best_threshold = 75.0
        best_score = 0
        
        for data in effectiveness:
            if data['trade_count'] >= 5:  # Minimum sample size
                # Score based on win rate and profit
                score = data['win_rate'] * 0.7 + (data['avg_profit'] / 100) * 0.3
                if score > best_score:
                    best_score = score
                    best_threshold = data['threshold']
        
        return {
            'optimal_threshold': best_threshold,
            'confidence_level': min(1.0, best_score),
            'analysis': effectiveness,
            'recommendation': f"Use {best_threshold:.1f}% threshold for {pair}"
        }

# Example usage
async def main():
    """Test advanced performance tracking"""
    from .mt5_enhanced_adapter import MT5EnhancedAdapter
    
    # Initialize
    mt5_adapter = MT5EnhancedAdapter()
    tracker = AdvancedTCSPerformanceTracker(mt5_adapter)
    
    # Start monitoring
    await tracker.start_monitoring()
    
    print("Advanced TCS Performance Tracker started")
    
    # Show stats every minute
    while True:
        stats = tracker.get_real_time_stats()
        print(f"Active trades: {stats['active_trades']['count']}")
        print(f"24h win rate: {stats['last_24h']['win_rate']:.1%}")
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())