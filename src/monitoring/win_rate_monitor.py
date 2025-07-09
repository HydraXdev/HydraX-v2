#!/usr/bin/env python3
"""
BITTEN Win Rate Monitoring System
Specialized monitoring for trading win rates with 85%+ target tracking,
trend analysis, and automated alerts.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3
from pathlib import Path
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor

from .logging_config import setup_service_logging
from .alert_system import AlertManager, AlertSeverity

@dataclass
class WinRateMetrics:
    """Win rate metrics for analysis"""
    timestamp: datetime
    symbol: str
    direction: str
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_pnl: float
    avg_winning_pnl: float
    avg_losing_pnl: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    win_rate_trend: str  # 'improving', 'declining', 'stable'
    sample_size: int  # Number of trades in calculation

@dataclass
class TradingSession:
    """Trading session analysis"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    symbols_traded: List[str]
    session_type: str  # 'london', 'new_york', 'asian', 'overlap'

@dataclass
class WinRateAlert:
    """Win rate alert definition"""
    alert_id: str
    symbol: str
    current_win_rate: float
    target_win_rate: float
    trade_count: int
    severity: AlertSeverity
    trend: str
    message: str
    timestamp: datetime

class WinRateDatabase:
    """SQLite database for win rate tracking"""
    
    def __init__(self, db_path: str = "/var/log/bitten/win_rate.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trade_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE,
                    symbol TEXT,
                    direction TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    entry_time TEXT,
                    exit_time TEXT,
                    lot_size REAL,
                    pnl REAL,
                    is_winner BOOLEAN,
                    duration_minutes INTEGER,
                    session_type TEXT,
                    strategy TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS win_rate_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    win_rate REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    avg_pnl REAL,
                    avg_winning_pnl REAL,
                    avg_losing_pnl REAL,
                    max_consecutive_wins INTEGER,
                    max_consecutive_losses INTEGER,
                    win_rate_trend TEXT,
                    sample_size INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    start_time TEXT,
                    end_time TEXT,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    symbols_traded TEXT,
                    session_type TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS win_rate_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    symbol TEXT,
                    current_win_rate REAL,
                    target_win_rate REAL,
                    trade_count INTEGER,
                    severity TEXT,
                    trend TEXT,
                    message TEXT,
                    timestamp TEXT,
                    acknowledged BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_symbol ON trade_results(symbol)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_results_timestamp ON trade_results(exit_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_win_rate_snapshots_timestamp ON win_rate_snapshots(timestamp)')
    
    def store_trade_result(self, trade_id: str, symbol: str, direction: str,
                          entry_price: float, exit_price: float,
                          entry_time: datetime, exit_time: datetime,
                          lot_size: float, pnl: float, strategy: str = None):
        """Store trade result"""
        with sqlite3.connect(self.db_path) as conn:
            is_winner = pnl > 0
            duration_minutes = (exit_time - entry_time).total_seconds() / 60
            
            # Determine session type
            session_type = self._get_session_type(exit_time)
            
            conn.execute('''
                INSERT OR REPLACE INTO trade_results (
                    trade_id, symbol, direction, entry_price, exit_price,
                    entry_time, exit_time, lot_size, pnl, is_winner,
                    duration_minutes, session_type, strategy, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_id, symbol, direction, entry_price, exit_price,
                entry_time.isoformat(), exit_time.isoformat(),
                lot_size, pnl, is_winner, duration_minutes,
                session_type, strategy, datetime.now().isoformat()
            ))
    
    def store_win_rate_snapshot(self, metrics: WinRateMetrics):
        """Store win rate snapshot"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO win_rate_snapshots (
                    timestamp, symbol, win_rate, total_trades, winning_trades,
                    losing_trades, avg_pnl, avg_winning_pnl, avg_losing_pnl,
                    max_consecutive_wins, max_consecutive_losses,
                    win_rate_trend, sample_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.symbol,
                metrics.win_rate,
                metrics.total_trades,
                metrics.winning_trades,
                metrics.losing_trades,
                metrics.avg_pnl,
                metrics.avg_winning_pnl,
                metrics.avg_losing_pnl,
                metrics.max_consecutive_wins,
                metrics.max_consecutive_losses,
                metrics.win_rate_trend,
                metrics.sample_size
            ))
    
    def store_trading_session(self, session: TradingSession):
        """Store trading session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO trading_sessions (
                    session_id, start_time, end_time, total_trades,
                    winning_trades, losing_trades, win_rate, total_pnl,
                    symbols_traded, session_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.total_trades,
                session.winning_trades,
                session.losing_trades,
                session.win_rate,
                session.total_pnl,
                json.dumps(session.symbols_traded),
                session.session_type
            ))
    
    def get_trades_by_symbol(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get trades for a specific symbol"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM trade_results 
                WHERE symbol = ? AND exit_time BETWEEN ? AND ?
                ORDER BY exit_time DESC
            ''', (symbol, start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_win_rate_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get win rate history for a symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM win_rate_snapshots 
                WHERE symbol = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            ''', (symbol, start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_performance(self, session_type: str = None, days: int = 7) -> List[Dict]:
        """Get trading session performance"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if session_type:
                cursor = conn.execute('''
                    SELECT * FROM trading_sessions 
                    WHERE session_type = ? AND start_time BETWEEN ? AND ?
                    ORDER BY start_time DESC
                ''', (session_type, start_date.isoformat(), end_date.isoformat()))
            else:
                cursor = conn.execute('''
                    SELECT * FROM trading_sessions 
                    WHERE start_time BETWEEN ? AND ?
                    ORDER BY start_time DESC
                ''', (start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_session_type(self, timestamp: datetime) -> str:
        """Determine trading session type based on timestamp"""
        hour = timestamp.hour
        
        if 8 <= hour < 12:
            return 'london'
        elif 12 <= hour < 16:
            return 'overlap'
        elif 16 <= hour < 20:
            return 'new_york'
        else:
            return 'asian'

class WinRateAnalyzer:
    """Analyzes win rates and trends"""
    
    def __init__(self, db: WinRateDatabase):
        self.db = db
        self.logger = setup_service_logging("win-rate-analyzer")
        self.target_win_rate = 85.0
        self.minimum_trades = 10  # Minimum trades for reliable analysis
    
    def calculate_win_rate_metrics(self, symbol: str, days: int = 7) -> WinRateMetrics:
        """Calculate comprehensive win rate metrics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get trades for the period
        trades = self.db.get_trades_by_symbol(symbol, start_date, end_date)
        
        if len(trades) < self.minimum_trades:
            # Not enough trades for reliable analysis
            return WinRateMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='mixed',
                win_rate=0.0,
                total_trades=len(trades),
                winning_trades=0,
                losing_trades=0,
                avg_pnl=0.0,
                avg_winning_pnl=0.0,
                avg_losing_pnl=0.0,
                max_consecutive_wins=0,
                max_consecutive_losses=0,
                win_rate_trend='unknown',
                sample_size=len(trades)
            )
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['is_winner'])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100
        
        # Calculate PnL metrics
        all_pnl = [t['pnl'] for t in trades]
        winning_pnl = [t['pnl'] for t in trades if t['is_winner']]
        losing_pnl = [t['pnl'] for t in trades if not t['is_winner']]
        
        avg_pnl = statistics.mean(all_pnl)
        avg_winning_pnl = statistics.mean(winning_pnl) if winning_pnl else 0.0
        avg_losing_pnl = statistics.mean(losing_pnl) if losing_pnl else 0.0
        
        # Calculate consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive(trades, True)
        max_consecutive_losses = self._calculate_max_consecutive(trades, False)
        
        # Calculate trend
        trend = self._calculate_trend(symbol, win_rate, days)
        
        return WinRateMetrics(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=self._get_dominant_direction(trades),
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_pnl=avg_pnl,
            avg_winning_pnl=avg_winning_pnl,
            avg_losing_pnl=avg_losing_pnl,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            win_rate_trend=trend,
            sample_size=total_trades
        )
    
    def _calculate_max_consecutive(self, trades: List[Dict], is_winner: bool) -> int:
        """Calculate maximum consecutive wins or losses"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in reversed(trades):  # Oldest to newest
            if trade['is_winner'] == is_winner:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _get_dominant_direction(self, trades: List[Dict]) -> str:
        """Get dominant trading direction"""
        buy_count = sum(1 for t in trades if t['direction'] == 'BUY')
        sell_count = sum(1 for t in trades if t['direction'] == 'SELL')
        
        if buy_count > sell_count:
            return 'BUY'
        elif sell_count > buy_count:
            return 'SELL'
        else:
            return 'mixed'
    
    def _calculate_trend(self, symbol: str, current_win_rate: float, days: int) -> str:
        """Calculate win rate trend"""
        try:
            # Get historical win rates
            history = self.db.get_win_rate_history(symbol, days * 2)
            
            if len(history) < 5:
                return 'stable'
            
            # Calculate trend over recent history
            recent_rates = [h['win_rate'] for h in history[:5]]
            older_rates = [h['win_rate'] for h in history[5:10]] if len(history) > 5 else recent_rates
            
            recent_avg = statistics.mean(recent_rates)
            older_avg = statistics.mean(older_rates)
            
            if recent_avg > older_avg + 5:
                return 'improving'
            elif recent_avg < older_avg - 5:
                return 'declining'
            else:
                return 'stable'
        
        except Exception as e:
            self.logger.error(f"Error calculating trend: {e}")
            return 'unknown'
    
    def analyze_session_performance(self, days: int = 7) -> Dict[str, Any]:
        """Analyze performance by trading session"""
        session_performance = {}
        
        for session_type in ['london', 'new_york', 'asian', 'overlap']:
            sessions = self.db.get_session_performance(session_type, days)
            
            if not sessions:
                continue
            
            total_trades = sum(s['total_trades'] for s in sessions)
            total_winning = sum(s['winning_trades'] for s in sessions)
            total_pnl = sum(s['total_pnl'] for s in sessions)
            
            avg_win_rate = (total_winning / total_trades) * 100 if total_trades > 0 else 0
            
            session_performance[session_type] = {
                'session_count': len(sessions),
                'total_trades': total_trades,
                'avg_win_rate': avg_win_rate,
                'total_pnl': total_pnl,
                'avg_pnl_per_session': total_pnl / len(sessions) if sessions else 0
            }
        
        return session_performance
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        symbols = ['GBPUSD', 'EURUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 
                  'NZDUSD', 'USDCAD', 'EURJPY', 'GBPJPY', 'EURGBP']
        
        summary = {
            'overall_win_rate': 0.0,
            'total_trades': 0,
            'symbols': {},
            'session_performance': self.analyze_session_performance(),
            'timestamp': datetime.now().isoformat()
        }
        
        total_trades = 0
        total_winning = 0
        
        for symbol in symbols:
            metrics = self.calculate_win_rate_metrics(symbol)
            
            summary['symbols'][symbol] = {
                'win_rate': metrics.win_rate,
                'total_trades': metrics.total_trades,
                'trend': metrics.win_rate_trend,
                'avg_pnl': metrics.avg_pnl
            }
            
            total_trades += metrics.total_trades
            total_winning += metrics.winning_trades
        
        summary['overall_win_rate'] = (total_winning / total_trades) * 100 if total_trades > 0 else 0
        summary['total_trades'] = total_trades
        
        return summary

class WinRateMonitor:
    """Main win rate monitoring system"""
    
    def __init__(self, alert_manager: AlertManager = None):
        self.db = WinRateDatabase()
        self.analyzer = WinRateAnalyzer(self.db)
        self.alert_manager = alert_manager
        self.logger = setup_service_logging("win-rate-monitor")
        
        # Monitoring configuration
        self.target_win_rate = 85.0
        self.warning_threshold = 80.0
        self.critical_threshold = 75.0
        self.minimum_trades = 10
        
        # Background tasks
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Recent trades tracking
        self.recent_trades = deque(maxlen=1000)
        self.symbol_metrics = {}
        
        # Monitoring symbols
        self.monitored_symbols = [
            'GBPUSD', 'EURUSD', 'USDJPY', 'USDCHF', 'AUDUSD',
            'NZDUSD', 'USDCAD', 'EURJPY', 'GBPJPY', 'EURGBP'
        ]
    
    def start(self):
        """Start win rate monitoring"""
        self.running = True
        
        # Start monitoring task
        self.executor.submit(self._monitoring_loop)
        
        # Start analysis task
        self.executor.submit(self._analysis_loop)
        
        self.logger.info("Win rate monitoring started")
    
    def stop(self):
        """Stop win rate monitoring"""
        self.running = False
        self.executor.shutdown(wait=True)
        self.logger.info("Win rate monitoring stopped")
    
    def record_trade(self, trade_id: str, symbol: str, direction: str,
                    entry_price: float, exit_price: float,
                    entry_time: datetime, exit_time: datetime,
                    lot_size: float, pnl: float, strategy: str = None):
        """Record a completed trade"""
        # Store in database
        self.db.store_trade_result(
            trade_id, symbol, direction, entry_price, exit_price,
            entry_time, exit_time, lot_size, pnl, strategy
        )
        
        # Add to recent trades
        self.recent_trades.append({
            'trade_id': trade_id,
            'symbol': symbol,
            'direction': direction,
            'pnl': pnl,
            'is_winner': pnl > 0,
            'timestamp': exit_time
        })
        
        # Log trade
        self.logger.info(
            f"Trade recorded: {trade_id} {symbol} {direction} "
            f"PnL: {pnl:.2f} ({'WIN' if pnl > 0 else 'LOSS'})",
            extra={
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'pnl': pnl,
                'is_winner': pnl > 0,
                'action': 'trade_recorded'
            }
        )
        
        # Check for immediate alerts
        self._check_immediate_alerts(symbol)
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Update metrics for all symbols
                for symbol in self.monitored_symbols:
                    metrics = self.analyzer.calculate_win_rate_metrics(symbol)
                    self.symbol_metrics[symbol] = metrics
                    
                    # Store snapshot
                    self.db.store_win_rate_snapshot(metrics)
                    
                    # Check for alerts
                    self._check_win_rate_alerts(symbol, metrics)
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def _analysis_loop(self):
        """Background analysis loop"""
        while self.running:
            try:
                # Generate hourly analysis
                self._generate_hourly_analysis()
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def _check_immediate_alerts(self, symbol: str):
        """Check for immediate win rate alerts after trade"""
        if symbol not in self.symbol_metrics:
            return
        
        metrics = self.symbol_metrics[symbol]
        
        # Only alert if we have enough trades
        if metrics.total_trades < self.minimum_trades:
            return
        
        # Check win rate thresholds
        if metrics.win_rate < self.critical_threshold:
            self._trigger_win_rate_alert(symbol, metrics, AlertSeverity.CRITICAL)
        elif metrics.win_rate < self.warning_threshold:
            self._trigger_win_rate_alert(symbol, metrics, AlertSeverity.HIGH)
    
    def _check_win_rate_alerts(self, symbol: str, metrics: WinRateMetrics):
        """Check win rate alerts for a symbol"""
        if metrics.total_trades < self.minimum_trades:
            return
        
        # Check for declining trend
        if metrics.win_rate_trend == 'declining' and metrics.win_rate < self.target_win_rate:
            self._trigger_win_rate_alert(symbol, metrics, AlertSeverity.MEDIUM)
        
        # Check for critical win rate
        if metrics.win_rate < self.critical_threshold:
            self._trigger_win_rate_alert(symbol, metrics, AlertSeverity.CRITICAL)
        elif metrics.win_rate < self.warning_threshold:
            self._trigger_win_rate_alert(symbol, metrics, AlertSeverity.HIGH)
    
    def _trigger_win_rate_alert(self, symbol: str, metrics: WinRateMetrics, severity: AlertSeverity):
        """Trigger win rate alert"""
        if not self.alert_manager:
            return
        
        alert_id = f"win_rate_{symbol}_{severity.value}"
        
        # Create alert message
        if severity == AlertSeverity.CRITICAL:
            message = f"Critical win rate for {symbol}: {metrics.win_rate:.1f}% (target: {self.target_win_rate}%)"
        elif severity == AlertSeverity.HIGH:
            message = f"Low win rate for {symbol}: {metrics.win_rate:.1f}% (target: {self.target_win_rate}%)"
        else:
            message = f"Declining win rate for {symbol}: {metrics.win_rate:.1f}% (trend: {metrics.win_rate_trend})"
        
        # Send alert to alert manager
        self.alert_manager.check_metric(
            service="win-rate-monitor",
            metric=f"win_rate_{symbol}",
            value=metrics.win_rate,
            tags={
                'symbol': symbol,
                'trend': metrics.win_rate_trend,
                'total_trades': str(metrics.total_trades),
                'severity': severity.value
            }
        )
        
        # Log alert
        self.logger.warning(
            f"Win rate alert: {message}",
            extra={
                'symbol': symbol,
                'win_rate': metrics.win_rate,
                'target': self.target_win_rate,
                'trend': metrics.win_rate_trend,
                'total_trades': metrics.total_trades,
                'severity': severity.value
            }
        )
    
    def _generate_hourly_analysis(self):
        """Generate hourly win rate analysis"""
        try:
            # Get performance summary
            summary = self.analyzer.get_performance_summary()
            
            # Log summary
            self.logger.info(
                f"Hourly win rate analysis: Overall {summary['overall_win_rate']:.1f}%, "
                f"Total trades: {summary['total_trades']}",
                extra={
                    'overall_win_rate': summary['overall_win_rate'],
                    'total_trades': summary['total_trades'],
                    'symbols': summary['symbols'],
                    'session_performance': summary['session_performance'],
                    'action': 'hourly_analysis'
                }
            )
            
            # Check overall win rate
            if summary['overall_win_rate'] < self.critical_threshold:
                self._trigger_overall_alert(summary, AlertSeverity.CRITICAL)
            elif summary['overall_win_rate'] < self.warning_threshold:
                self._trigger_overall_alert(summary, AlertSeverity.HIGH)
            
        except Exception as e:
            self.logger.error(f"Error generating hourly analysis: {e}")
    
    def _trigger_overall_alert(self, summary: Dict[str, Any], severity: AlertSeverity):
        """Trigger overall system win rate alert"""
        if not self.alert_manager:
            return
        
        message = f"Overall system win rate: {summary['overall_win_rate']:.1f}% (target: {self.target_win_rate}%)"
        
        self.alert_manager.check_metric(
            service="win-rate-monitor",
            metric="overall_win_rate",
            value=summary['overall_win_rate'],
            tags={
                'total_trades': str(summary['total_trades']),
                'severity': severity.value
            }
        )
        
        self.logger.warning(f"Overall win rate alert: {message}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current win rate status"""
        summary = self.analyzer.get_performance_summary()
        
        return {
            'overall_win_rate': summary['overall_win_rate'],
            'target_win_rate': self.target_win_rate,
            'total_trades': summary['total_trades'],
            'symbols': summary['symbols'],
            'session_performance': summary['session_performance'],
            'recent_trades_count': len(self.recent_trades),
            'monitoring_status': 'running' if self.running else 'stopped',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_symbol_performance(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """Get detailed performance for a specific symbol"""
        metrics = self.analyzer.calculate_win_rate_metrics(symbol, days)
        
        return {
            'symbol': symbol,
            'win_rate': metrics.win_rate,
            'total_trades': metrics.total_trades,
            'winning_trades': metrics.winning_trades,
            'losing_trades': metrics.losing_trades,
            'avg_pnl': metrics.avg_pnl,
            'trend': metrics.win_rate_trend,
            'max_consecutive_wins': metrics.max_consecutive_wins,
            'max_consecutive_losses': metrics.max_consecutive_losses,
            'target_win_rate': self.target_win_rate,
            'status': self._get_status_level(metrics.win_rate),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_status_level(self, win_rate: float) -> str:
        """Get status level based on win rate"""
        if win_rate >= self.target_win_rate:
            return 'excellent'
        elif win_rate >= self.warning_threshold:
            return 'good'
        elif win_rate >= self.critical_threshold:
            return 'warning'
        else:
            return 'critical'

# Global win rate monitor instance
_win_rate_monitor = None

def get_win_rate_monitor(alert_manager: AlertManager = None) -> WinRateMonitor:
    """Get global win rate monitor instance"""
    global _win_rate_monitor
    if _win_rate_monitor is None:
        _win_rate_monitor = WinRateMonitor(alert_manager)
    return _win_rate_monitor

# Example usage
if __name__ == "__main__":
    # Create win rate monitor
    monitor = get_win_rate_monitor()
    
    # Start monitoring
    monitor.start()
    
    # Simulate some trades
    base_time = datetime.now()
    
    # Simulate winning trades
    for i in range(8):
        monitor.record_trade(
            trade_id=f"WIN_{i}",
            symbol="GBPUSD",
            direction="BUY",
            entry_price=1.2650,
            exit_price=1.2680,
            entry_time=base_time - timedelta(hours=i*2),
            exit_time=base_time - timedelta(hours=i*2-1),
            lot_size=0.1,
            pnl=30.0,
            strategy="london_breakout"
        )
    
    # Simulate losing trades
    for i in range(3):
        monitor.record_trade(
            trade_id=f"LOSS_{i}",
            symbol="GBPUSD",
            direction="SELL",
            entry_price=1.2650,
            exit_price=1.2630,
            entry_time=base_time - timedelta(hours=i*3),
            exit_time=base_time - timedelta(hours=i*3-1),
            lot_size=0.1,
            pnl=-20.0,
            strategy="mean_reversion"
        )
    
    # Get current status
    status = monitor.get_current_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Get symbol performance
    perf = monitor.get_symbol_performance("GBPUSD")
    print(json.dumps(perf, indent=2, default=str))
    
    # Stop monitoring
    monitor.stop()