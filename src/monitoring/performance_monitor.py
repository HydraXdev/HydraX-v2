#!/usr/bin/env python3
"""
BITTEN Performance Monitoring System
Monitors signal generation performance, trade execution, and system health
with focus on 65 signals/day target and 85%+ win rate.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import sqlite3
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

from .logging_config import setup_service_logging

@dataclass
class SignalMetrics:
    """Signal generation performance metrics"""
    timestamp: datetime
    signal_count: int
    pairs_active: int
    generation_time_ms: float
    tcs_threshold: float
    market_conditions: str
    success_rate: float
    avg_confidence: float
    service_name: str = "signal-generator"

@dataclass
class TradeMetrics:
    """Trade execution performance metrics"""
    timestamp: datetime
    trade_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    lot_size: float
    pnl: Optional[float]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    service_name: str = "trade-executor"

@dataclass
class SystemMetrics:
    """System health metrics"""
    timestamp: datetime
    service_name: str
    cpu_usage: float
    memory_usage: float
    active_connections: int
    response_time_ms: float
    error_rate: float
    uptime_seconds: float

@dataclass
class DailyPerformanceReport:
    """Daily performance summary"""
    date: datetime
    signals_generated: int
    signals_target: int = 65
    win_rate: float
    win_rate_target: float = 85.0
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_pnl: float
    avg_signal_generation_time: float
    avg_trade_execution_time: float
    system_uptime: float
    error_count: int
    pairs_traded: List[str]
    performance_score: float

class PerformanceDatabase:
    """SQLite database for performance metrics"""
    
    def __init__(self, db_path: str = "/var/log/bitten/performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS signal_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    signal_count INTEGER,
                    pairs_active INTEGER,
                    generation_time_ms REAL,
                    tcs_threshold REAL,
                    market_conditions TEXT,
                    success_rate REAL,
                    avg_confidence REAL,
                    service_name TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trade_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    trade_id TEXT,
                    symbol TEXT,
                    direction TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    lot_size REAL,
                    pnl REAL,
                    execution_time_ms REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    service_name TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    service_name TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    active_connections INTEGER,
                    response_time_ms REAL,
                    error_rate REAL,
                    uptime_seconds REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    signals_generated INTEGER,
                    signals_target INTEGER,
                    win_rate REAL,
                    win_rate_target REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    avg_pnl REAL,
                    avg_signal_generation_time REAL,
                    avg_trade_execution_time REAL,
                    system_uptime REAL,
                    error_count INTEGER,
                    pairs_traded TEXT,
                    performance_score REAL
                )
            ''')
    
    def store_signal_metrics(self, metrics: SignalMetrics):
        """Store signal generation metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO signal_metrics (
                    timestamp, signal_count, pairs_active, generation_time_ms,
                    tcs_threshold, market_conditions, success_rate, avg_confidence,
                    service_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.signal_count,
                metrics.pairs_active,
                metrics.generation_time_ms,
                metrics.tcs_threshold,
                metrics.market_conditions,
                metrics.success_rate,
                metrics.avg_confidence,
                metrics.service_name
            ))
    
    def store_trade_metrics(self, metrics: TradeMetrics):
        """Store trade execution metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO trade_metrics (
                    timestamp, trade_id, symbol, direction, entry_price,
                    exit_price, lot_size, pnl, execution_time_ms, success,
                    error_message, service_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.trade_id,
                metrics.symbol,
                metrics.direction,
                metrics.entry_price,
                metrics.exit_price,
                metrics.lot_size,
                metrics.pnl,
                metrics.execution_time_ms,
                metrics.success,
                metrics.error_message,
                metrics.service_name
            ))
    
    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system health metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO system_metrics (
                    timestamp, service_name, cpu_usage, memory_usage,
                    active_connections, response_time_ms, error_rate,
                    uptime_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.service_name,
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.active_connections,
                metrics.response_time_ms,
                metrics.error_rate,
                metrics.uptime_seconds
            ))
    
    def store_daily_report(self, report: DailyPerformanceReport):
        """Store daily performance report"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO daily_reports (
                    date, signals_generated, signals_target, win_rate,
                    win_rate_target, total_trades, winning_trades, losing_trades,
                    avg_pnl, avg_signal_generation_time, avg_trade_execution_time,
                    system_uptime, error_count, pairs_traded, performance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.date.isoformat(),
                report.signals_generated,
                report.signals_target,
                report.win_rate,
                report.win_rate_target,
                report.total_trades,
                report.winning_trades,
                report.losing_trades,
                report.avg_pnl,
                report.avg_signal_generation_time,
                report.avg_trade_execution_time,
                report.system_uptime,
                report.error_count,
                json.dumps(report.pairs_traded),
                report.performance_score
            ))
    
    def get_signal_metrics(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get signal metrics for date range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM signal_metrics 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trade_metrics(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get trade metrics for date range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM trade_metrics 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_reports(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get daily reports for date range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM daily_reports 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]

class SignalPerformanceMonitor:
    """Monitors signal generation performance"""
    
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.logger = setup_service_logging("signal-performance-monitor")
        self.signal_count_today = 0
        self.target_signals_per_day = 65
        self.current_tcs_threshold = 70.0
        self.last_reset = datetime.now().date()
        
        # Ring buffer for recent metrics
        self.recent_metrics = deque(maxlen=100)
        
    def record_signal_generation(self, signal_count: int, pairs_active: int, 
                               generation_time_ms: float, tcs_threshold: float,
                               market_conditions: str, success_rate: float,
                               avg_confidence: float):
        """Record signal generation event"""
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.date() != self.last_reset:
            self.signal_count_today = 0
            self.last_reset = now.date()
        
        self.signal_count_today += signal_count
        
        # Create metrics
        metrics = SignalMetrics(
            timestamp=now,
            signal_count=signal_count,
            pairs_active=pairs_active,
            generation_time_ms=generation_time_ms,
            tcs_threshold=tcs_threshold,
            market_conditions=market_conditions,
            success_rate=success_rate,
            avg_confidence=avg_confidence
        )
        
        # Store in database
        self.db.store_signal_metrics(metrics)
        
        # Add to recent metrics
        self.recent_metrics.append(metrics)
        
        # Log performance
        self.logger.info(
            f"Signal generation: {signal_count} signals, "
            f"daily total: {self.signal_count_today}/{self.target_signals_per_day}",
            extra={
                'signal_count': signal_count,
                'daily_total': self.signal_count_today,
                'target': self.target_signals_per_day,
                'generation_time_ms': generation_time_ms,
                'tcs_threshold': tcs_threshold,
                'performance_metrics': asdict(metrics)
            }
        )
        
        # Check if we need TCS adjustment
        self._check_tcs_adjustment()
    
    def _check_tcs_adjustment(self):
        """Check if TCS threshold needs adjustment"""
        if len(self.recent_metrics) < 10:
            return
        
        # Calculate current signal rate
        recent_signals = [m.signal_count for m in self.recent_metrics]
        avg_signals_per_hour = statistics.mean(recent_signals)
        projected_daily = avg_signals_per_hour * 24
        
        # Adjust TCS if needed
        if projected_daily < self.target_signals_per_day * 0.8:
            # Too few signals, lower TCS threshold
            new_threshold = max(65.0, self.current_tcs_threshold - 1.0)
            if new_threshold != self.current_tcs_threshold:
                self.current_tcs_threshold = new_threshold
                self.logger.warning(
                    f"TCS threshold adjusted to {new_threshold} "
                    f"(projected daily: {projected_daily:.1f})"
                )
        elif projected_daily > self.target_signals_per_day * 1.2:
            # Too many signals, raise TCS threshold
            new_threshold = min(85.0, self.current_tcs_threshold + 1.0)
            if new_threshold != self.current_tcs_threshold:
                self.current_tcs_threshold = new_threshold
                self.logger.warning(
                    f"TCS threshold adjusted to {new_threshold} "
                    f"(projected daily: {projected_daily:.1f})"
                )
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Get current signal generation performance"""
        if not self.recent_metrics:
            return {}
        
        recent_generation_times = [m.generation_time_ms for m in self.recent_metrics]
        recent_success_rates = [m.success_rate for m in self.recent_metrics]
        
        return {
            'signals_today': self.signal_count_today,
            'target_signals': self.target_signals_per_day,
            'completion_rate': (self.signal_count_today / self.target_signals_per_day) * 100,
            'current_tcs_threshold': self.current_tcs_threshold,
            'avg_generation_time_ms': statistics.mean(recent_generation_times),
            'avg_success_rate': statistics.mean(recent_success_rates),
            'last_signal_time': self.recent_metrics[-1].timestamp.isoformat()
        }

class TradePerformanceMonitor:
    """Monitors trade execution performance"""
    
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.logger = setup_service_logging("trade-performance-monitor")
        self.target_win_rate = 85.0
        
        # Ring buffer for recent trades
        self.recent_trades = deque(maxlen=100)
        
    def record_trade_execution(self, trade_id: str, symbol: str, direction: str,
                             entry_price: float, lot_size: float, 
                             execution_time_ms: float, success: bool,
                             error_message: Optional[str] = None):
        """Record trade execution event"""
        now = datetime.now()
        
        # Create metrics
        metrics = TradeMetrics(
            timestamp=now,
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=None,  # Will be updated on trade close
            lot_size=lot_size,
            pnl=None,  # Will be updated on trade close
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message
        )
        
        # Store in database
        self.db.store_trade_metrics(metrics)
        
        # Add to recent trades
        self.recent_trades.append(metrics)
        
        # Log performance
        self.logger.info(
            f"Trade execution: {trade_id} {symbol} {direction} "
            f"@ {entry_price} (success: {success})",
            extra={
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'execution_time_ms': execution_time_ms,
                'success': success,
                'performance_metrics': asdict(metrics)
            }
        )
    
    def record_trade_close(self, trade_id: str, exit_price: float, pnl: float):
        """Record trade close event"""
        # Update trade in database
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute('''
                UPDATE trade_metrics 
                SET exit_price = ?, pnl = ?
                WHERE trade_id = ?
            ''', (exit_price, pnl, trade_id))
        
        # Update recent trades
        for trade in self.recent_trades:
            if trade.trade_id == trade_id:
                trade.exit_price = exit_price
                trade.pnl = pnl
                break
        
        self.logger.info(
            f"Trade closed: {trade_id} @ {exit_price} (PnL: {pnl})",
            extra={
                'trade_id': trade_id,
                'exit_price': exit_price,
                'pnl': pnl,
                'action': 'trade_close'
            }
        )
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Get current trade performance"""
        if not self.recent_trades:
            return {}
        
        closed_trades = [t for t in self.recent_trades if t.pnl is not None]
        if not closed_trades:
            return {'message': 'No closed trades yet'}
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]
        
        win_rate = (len(winning_trades) / len(closed_trades)) * 100
        avg_pnl = statistics.mean([t.pnl for t in closed_trades])
        avg_execution_time = statistics.mean([t.execution_time_ms for t in self.recent_trades])
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'target_win_rate': self.target_win_rate,
            'avg_pnl': avg_pnl,
            'avg_execution_time_ms': avg_execution_time,
            'win_rate_status': 'GOOD' if win_rate >= self.target_win_rate else 'NEEDS_IMPROVEMENT'
        }

class SystemHealthMonitor:
    """Monitors system health metrics"""
    
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.logger = setup_service_logging("system-health-monitor")
        self.start_time = time.time()
        
    def record_system_metrics(self, service_name: str, cpu_usage: float,
                            memory_usage: float, active_connections: int,
                            response_time_ms: float, error_rate: float):
        """Record system health metrics"""
        now = datetime.now()
        uptime = time.time() - self.start_time
        
        metrics = SystemMetrics(
            timestamp=now,
            service_name=service_name,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_connections=active_connections,
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_seconds=uptime
        )
        
        # Store in database
        self.db.store_system_metrics(metrics)
        
        # Log if concerning
        if cpu_usage > 80 or memory_usage > 85 or error_rate > 5:
            self.logger.warning(
                f"System health concern: {service_name} "
                f"CPU: {cpu_usage}%, Memory: {memory_usage}%, "
                f"Error rate: {error_rate}%",
                extra={
                    'service': service_name,
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'error_rate': error_rate,
                    'performance_metrics': asdict(metrics)
                }
            )

class PerformanceReportGenerator:
    """Generates daily performance reports"""
    
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.logger = setup_service_logging("performance-report-generator")
    
    def generate_daily_report(self, date: datetime) -> DailyPerformanceReport:
        """Generate daily performance report"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Get metrics for the day
        signal_metrics = self.db.get_signal_metrics(start_date, end_date)
        trade_metrics = self.db.get_trade_metrics(start_date, end_date)
        
        # Calculate signal performance
        signals_generated = sum(m['signal_count'] for m in signal_metrics)
        avg_signal_time = statistics.mean([m['generation_time_ms'] for m in signal_metrics]) if signal_metrics else 0
        
        # Calculate trade performance
        closed_trades = [t for t in trade_metrics if t['pnl'] is not None]
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(closed_trades)) * 100 if closed_trades else 0
        avg_pnl = statistics.mean([t['pnl'] for t in closed_trades]) if closed_trades else 0
        avg_trade_time = statistics.mean([t['execution_time_ms'] for t in trade_metrics]) if trade_metrics else 0
        
        # Calculate performance score
        signal_score = min(100, (signals_generated / 65) * 100)
        win_rate_score = min(100, (win_rate / 85) * 100)
        performance_score = (signal_score + win_rate_score) / 2
        
        # Get unique pairs
        pairs_traded = list(set(t['symbol'] for t in trade_metrics))
        
        report = DailyPerformanceReport(
            date=date,
            signals_generated=signals_generated,
            win_rate=win_rate,
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_pnl=avg_pnl,
            avg_signal_generation_time=avg_signal_time,
            avg_trade_execution_time=avg_trade_time,
            system_uptime=24.0,  # Assuming full uptime, would be calculated from system metrics
            error_count=len([t for t in trade_metrics if not t['success']]),
            pairs_traded=pairs_traded,
            performance_score=performance_score
        )
        
        # Store report
        self.db.store_daily_report(report)
        
        # Log report
        self.logger.info(
            f"Daily report generated: {signals_generated} signals, "
            f"{win_rate:.1f}% win rate, performance score: {performance_score:.1f}",
            extra={
                'date': date.isoformat(),
                'signals_generated': signals_generated,
                'win_rate': win_rate,
                'performance_score': performance_score,
                'performance_metrics': asdict(report)
            }
        )
        
        return report

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.db = PerformanceDatabase(
            self.config.get('db_path', '/var/log/bitten/performance.db')
        )
        
        # Initialize monitors
        self.signal_monitor = SignalPerformanceMonitor(self.db)
        self.trade_monitor = TradePerformanceMonitor(self.db)
        self.health_monitor = SystemHealthMonitor(self.db)
        self.report_generator = PerformanceReportGenerator(self.db)
        
        self.logger = setup_service_logging("performance-monitor")
        
        # Background tasks
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def start(self):
        """Start performance monitoring"""
        self.running = True
        
        # Start report generation task
        self.executor.submit(self._report_generation_task)
        
        self.logger.info("Performance monitoring started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.running = False
        self.executor.shutdown(wait=True)
        self.logger.info("Performance monitoring stopped")
    
    def _report_generation_task(self):
        """Background task for report generation"""
        while self.running:
            try:
                # Generate yesterday's report
                yesterday = datetime.now() - timedelta(days=1)
                report = self.report_generator.generate_daily_report(yesterday)
                
                # Sleep until next day
                time.sleep(86400)  # 24 hours
                
            except Exception as e:
                self.logger.error(f"Error in report generation: {e}")
                time.sleep(3600)  # Wait 1 hour before retry
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current performance status"""
        return {
            'signal_performance': self.signal_monitor.get_current_performance(),
            'trade_performance': self.trade_monitor.get_current_performance(),
            'timestamp': datetime.now().isoformat(),
            'monitoring_status': 'running' if self.running else 'stopped'
        }

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor(config: Optional[Dict[str, Any]] = None) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)
    return _performance_monitor

# Example usage
if __name__ == "__main__":
    # Create performance monitor
    monitor = get_performance_monitor()
    
    # Start monitoring
    monitor.start()
    
    # Simulate some events
    monitor.signal_monitor.record_signal_generation(
        signal_count=3,
        pairs_active=5,
        generation_time_ms=150.0,
        tcs_threshold=72.0,
        market_conditions="volatile",
        success_rate=0.85,
        avg_confidence=0.78
    )
    
    monitor.trade_monitor.record_trade_execution(
        trade_id="TRADE001",
        symbol="GBPUSD",
        direction="BUY",
        entry_price=1.2650,
        lot_size=0.1,
        execution_time_ms=45.0,
        success=True
    )
    
    # Get current status
    status = monitor.get_current_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Stop monitoring
    monitor.stop()