#!/usr/bin/env python3
"""
BITTEN Result Tracking and Callbacks System
Tracks trade results from MT5 execution back to TCS optimizer
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

class TradeEvent(Enum):
    OPENED = "opened"
    CLOSED = "closed"
    MODIFIED = "modified"
    CANCELLED = "cancelled"

class TradeResult(Enum):
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    PENDING = "pending"

@dataclass
class TradeResultData:
    """Trade result data structure"""
    trade_id: str
    signal_id: str
    user_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    volume: float
    open_time: datetime
    close_time: Optional[datetime]
    profit_pips: Optional[float]
    profit_usd: Optional[float]
    result: TradeResult
    tcs_score: float
    fire_mode: str
    hold_time_minutes: Optional[int]
    sl_hit: bool = False
    tp_hit: bool = False
    manual_close: bool = False
    
class ResultTracker:
    """
    Main result tracking system that manages trade lifecycle
    and feeds results back to TCS optimizer
    """
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/trade_results.db"):
        self.db_path = db_path
        self.callbacks = {
            TradeEvent.OPENED: [],
            TradeEvent.CLOSED: [],
            TradeEvent.MODIFIED: [],
            TradeEvent.CANCELLED: []
        }
        self.active_trades: Dict[str, TradeResultData] = {}
        self._init_database()
        
        # TCS optimizer integration
        self.tcs_optimizer = None
        self.performance_metrics = PerformanceMetrics()
        
    def _init_database(self):
        """Initialize trade results database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                signal_id TEXT,
                user_id TEXT,
                symbol TEXT,
                direction TEXT,
                entry_price REAL,
                exit_price REAL,
                volume REAL,
                open_time DATETIME,
                close_time DATETIME,
                profit_pips REAL,
                profit_usd REAL,
                result TEXT,
                tcs_score REAL,
                fire_mode TEXT,
                hold_time_minutes INTEGER,
                sl_hit BOOLEAN,
                tp_hit BOOLEAN,
                manual_close BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS callback_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT,
                event_type TEXT,
                event_data TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_symbol ON trade_results(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_user ON trade_results(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_time ON trade_results(open_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_result ON trade_results(result)')
        
        conn.commit()
        conn.close()
    
    def register_callback(self, event: TradeEvent, callback: Callable):
        """Register callback for trade events"""
        self.callbacks[event].append(callback)
        logger.info(f"Registered callback for {event.value} events")
    
    def set_tcs_optimizer(self, optimizer):
        """Set TCS optimizer for result feedback"""
        self.tcs_optimizer = optimizer
        logger.info("TCS optimizer connected to result tracker")
    
    async def track_trade_opened(self, trade_data: Dict[str, Any]):
        """Track when a trade is opened"""
        try:
            result_data = TradeResultData(
                trade_id=trade_data['trade_id'],
                signal_id=trade_data['signal_id'],
                user_id=trade_data['user_id'],
                symbol=trade_data['symbol'],
                direction=trade_data['direction'],
                entry_price=trade_data['entry_price'],
                exit_price=None,
                volume=trade_data['volume'],
                open_time=datetime.now(),
                close_time=None,
                profit_pips=None,
                profit_usd=None,
                result=TradeResult.PENDING,
                tcs_score=trade_data.get('tcs_score', 0),
                fire_mode=trade_data.get('fire_mode', 'SINGLE_SHOT'),
                hold_time_minutes=None
            )
            
            # Store in active trades
            self.active_trades[trade_data['trade_id']] = result_data
            
            # Save to database
            await self._save_trade_result(result_data)
            
            # Trigger callbacks
            await self._trigger_callbacks(TradeEvent.OPENED, result_data)
            
            logger.info(f"Trade opened: {trade_data['trade_id']} - {trade_data['symbol']}")
            
        except Exception as e:
            logger.error(f"Error tracking trade opened: {e}")
    
    async def track_trade_closed(self, trade_data: Dict[str, Any]):
        """Track when a trade is closed"""
        try:
            trade_id = trade_data['trade_id']
            
            if trade_id not in self.active_trades:
                logger.warning(f"Trade {trade_id} not found in active trades")
                return
            
            result_data = self.active_trades[trade_id]
            
            # Update trade result
            result_data.exit_price = trade_data['exit_price']
            result_data.close_time = datetime.now()
            result_data.profit_pips = trade_data.get('profit_pips')
            result_data.profit_usd = trade_data.get('profit_usd')
            result_data.sl_hit = trade_data.get('sl_hit', False)
            result_data.tp_hit = trade_data.get('tp_hit', False)
            result_data.manual_close = trade_data.get('manual_close', False)
            
            # Calculate hold time
            if result_data.close_time and result_data.open_time:
                hold_time = result_data.close_time - result_data.open_time
                result_data.hold_time_minutes = int(hold_time.total_seconds() / 60)
            
            # Determine result
            if result_data.profit_pips is not None:
                if result_data.profit_pips > 0:
                    result_data.result = TradeResult.WIN
                elif result_data.profit_pips < 0:
                    result_data.result = TradeResult.LOSS
                else:
                    result_data.result = TradeResult.BREAKEVEN
            
            # Update database
            await self._update_trade_result(result_data)
            
            # Feed back to TCS optimizer
            if self.tcs_optimizer:
                await self._feed_back_to_optimizer(result_data)
            
            # Update performance metrics
            await self.performance_metrics.update_metrics(result_data)
            
            # Trigger callbacks
            await self._trigger_callbacks(TradeEvent.CLOSED, result_data)
            
            # Remove from active trades
            del self.active_trades[trade_id]
            
            logger.info(f"Trade closed: {trade_id} - {result_data.result.value} ({result_data.profit_pips} pips)")
            
        except Exception as e:
            logger.error(f"Error tracking trade closed: {e}")
    
    async def track_trade_modified(self, trade_data: Dict[str, Any]):
        """Track when a trade is modified"""
        try:
            trade_id = trade_data['trade_id']
            
            if trade_id in self.active_trades:
                result_data = self.active_trades[trade_id]
                
                # Log modification event
                await self._log_callback_event(trade_id, TradeEvent.MODIFIED, trade_data)
                
                # Trigger callbacks
                await self._trigger_callbacks(TradeEvent.MODIFIED, result_data)
                
                logger.info(f"Trade modified: {trade_id}")
            
        except Exception as e:
            logger.error(f"Error tracking trade modified: {e}")
    
    async def _save_trade_result(self, result_data: TradeResultData):
        """Save trade result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO trade_results 
            (trade_id, signal_id, user_id, symbol, direction, entry_price, exit_price,
             volume, open_time, close_time, profit_pips, profit_usd, result, tcs_score,
             fire_mode, hold_time_minutes, sl_hit, tp_hit, manual_close)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result_data.trade_id, result_data.signal_id, result_data.user_id,
            result_data.symbol, result_data.direction, result_data.entry_price,
            result_data.exit_price, result_data.volume, result_data.open_time,
            result_data.close_time, result_data.profit_pips, result_data.profit_usd,
            result_data.result.value, result_data.tcs_score, result_data.fire_mode,
            result_data.hold_time_minutes, result_data.sl_hit, result_data.tp_hit,
            result_data.manual_close
        ))
        
        conn.commit()
        conn.close()
    
    async def _update_trade_result(self, result_data: TradeResultData):
        """Update existing trade result in database"""
        await self._save_trade_result(result_data)
    
    async def _log_callback_event(self, trade_id: str, event: TradeEvent, data: Dict):
        """Log callback event for processing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO callback_events (trade_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (trade_id, event.value, json.dumps(data)))
        
        conn.commit()
        conn.close()
    
    async def _trigger_callbacks(self, event: TradeEvent, result_data: TradeResultData):
        """Trigger registered callbacks for event"""
        for callback in self.callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result_data)
                else:
                    callback(result_data)
            except Exception as e:
                logger.error(f"Error in callback for {event.value}: {e}")
    
    async def _feed_back_to_optimizer(self, result_data: TradeResultData):
        """Feed trade result back to TCS optimizer"""
        try:
            if self.tcs_optimizer:
                # Create market condition for optimizer
                market_condition = {
                    'volatility_level': 'MEDIUM',  # You can enhance this
                    'trend_strength': 0.6,
                    'session_activity': self._get_session_activity(),
                    'news_impact': 0.3
                }
                
                # Feed result to optimizer
                await self.tcs_optimizer.log_signal_performance(
                    pair=result_data.symbol,
                    tcs_score=result_data.tcs_score,
                    direction=result_data.direction,
                    result=result_data.result.value.upper(),
                    pips_gained=result_data.profit_pips or 0,
                    hold_time_minutes=result_data.hold_time_minutes or 0,
                    market_condition=market_condition
                )
                
        except Exception as e:
            logger.error(f"Error feeding back to optimizer: {e}")
    
    def _get_session_activity(self) -> str:
        """Get current session activity"""
        hour = datetime.now().hour
        if 0 <= hour < 6:
            return "ASIAN"
        elif 6 <= hour < 14:
            return "LONDON"
        elif 14 <= hour < 22:
            return "NEW_YORK"
        else:
            return "ASIAN"
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary for last N days"""
        return self.performance_metrics.get_summary(days)
    
    def get_active_trades(self) -> Dict[str, TradeResultData]:
        """Get currently active trades"""
        return self.active_trades.copy()

class PerformanceMetrics:
    """Performance metrics and analytics"""
    
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/trade_results.db"
    
    async def update_metrics(self, result_data: TradeResultData):
        """Update performance metrics with new trade result"""
        # This will be called automatically by ResultTracker
        pass
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Win rate
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN result = 'win' THEN 1 END) as wins,
                COUNT(CASE WHEN result = 'loss' THEN 1 END) as losses,
                COUNT(*) as total_trades
            FROM trade_results 
            WHERE close_time > ? AND result != 'pending'
        ''', (start_date,))
        
        win_data = cursor.fetchone()
        wins, losses, total = win_data
        
        win_rate = wins / total if total > 0 else 0
        
        # Profit metrics
        cursor.execute('''
            SELECT 
                SUM(profit_pips) as total_pips,
                AVG(profit_pips) as avg_pips,
                SUM(profit_usd) as total_usd,
                AVG(hold_time_minutes) as avg_hold_time
            FROM trade_results 
            WHERE close_time > ? AND result != 'pending'
        ''', (start_date,))
        
        profit_data = cursor.fetchone()
        total_pips, avg_pips, total_usd, avg_hold_time = profit_data
        
        # TCS performance
        cursor.execute('''
            SELECT 
                AVG(tcs_score) as avg_tcs,
                COUNT(*) as signal_count
            FROM trade_results 
            WHERE open_time > ?
        ''', (start_date,))
        
        tcs_data = cursor.fetchone()
        avg_tcs, signal_count = tcs_data
        
        conn.close()
        
        return {
            'period_days': days,
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pips': total_pips or 0,
            'avg_pips_per_trade': avg_pips or 0,
            'total_usd': total_usd or 0,
            'avg_hold_time_minutes': avg_hold_time or 0,
            'avg_tcs_score': avg_tcs or 0,
            'signal_count': signal_count or 0,
            'signals_per_day': (signal_count or 0) / days if days > 0 else 0
        }

class CallbackManager:
    """Manages callback registration and execution"""
    
    def __init__(self, result_tracker: ResultTracker):
        self.result_tracker = result_tracker
        self._setup_default_callbacks()
    
    def _setup_default_callbacks(self):
        """Set up default system callbacks"""
        
        # TCS optimizer callback
        self.result_tracker.register_callback(
            TradeEvent.CLOSED, 
            self._tcs_optimizer_callback
        )
        
        # Performance logging callback
        self.result_tracker.register_callback(
            TradeEvent.CLOSED,
            self._performance_logging_callback
        )
        
        # Alert callback for significant events
        self.result_tracker.register_callback(
            TradeEvent.CLOSED,
            self._alert_callback
        )
    
    async def _tcs_optimizer_callback(self, result_data: TradeResultData):
        """Callback to feed results to TCS optimizer"""
        # This is handled by the result tracker itself
        pass
    
    async def _performance_logging_callback(self, result_data: TradeResultData):
        """Log performance metrics"""
        logger.info(f"Trade Performance: {result_data.symbol} - {result_data.result.value} "
                   f"({result_data.profit_pips} pips, {result_data.hold_time_minutes}min)")
    
    async def _alert_callback(self, result_data: TradeResultData):
        """Alert callback for significant events"""
        if result_data.result == TradeResult.LOSS and result_data.profit_pips and result_data.profit_pips < -50:
            logger.warning(f"Large loss detected: {result_data.symbol} - {result_data.profit_pips} pips")

# Global result tracker instance
_result_tracker = None

def get_result_tracker() -> ResultTracker:
    """Get global result tracker instance"""
    global _result_tracker
    if _result_tracker is None:
        _result_tracker = ResultTracker()
        CallbackManager(_result_tracker)  # Set up default callbacks
    return _result_tracker

# Example usage functions
async def example_usage():
    """Example of how to use the result tracking system"""
    
    # Get result tracker
    tracker = get_result_tracker()
    
    # Set up TCS optimizer (you would get this from your actual optimizer)
    from .self_optimizing_tcs import get_tcs_optimizer
    optimizer = get_tcs_optimizer()
    tracker.set_tcs_optimizer(optimizer)
    
    # Example trade opened
    trade_data = {
        'trade_id': 'TRADE_001',
        'signal_id': 'SIGNAL_001',
        'user_id': 'USER_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0900,
        'volume': 0.01,
        'tcs_score': 85,
        'fire_mode': 'SINGLE_SHOT'
    }
    
    await tracker.track_trade_opened(trade_data)
    
    # Example trade closed
    close_data = {
        'trade_id': 'TRADE_001',
        'exit_price': 1.0950,
        'profit_pips': 50,
        'profit_usd': 5.0,
        'tp_hit': True
    }
    
    await tracker.track_trade_closed(close_data)
    
    # Get performance summary
    summary = tracker.get_performance_summary(7)
    print(f"Win rate: {summary['win_rate']:.2%}")
    print(f"Signals per day: {summary['signals_per_day']:.1f}")

if __name__ == "__main__":
    asyncio.run(example_usage())