# trade_writer.py
# BITTEN Trade Logging and Persistence System

import json
import csv
import time
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import sqlite3

# Import BITTEN components
from .xp_logger import TradeLog, TradeOutcome, XPLogger
from .fire_router import TradeExecutionResult

class ExportFormat(Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    MT4_CSV = "mt4_csv"
    EXCEL = "excel"
    PDF = "pdf"

class TradeStatus(Enum):
    """Trade status tracking"""
    PENDING = "pending"
    EXECUTED = "executed"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class TradeRecord:
    """Complete trade record for storage"""
    trade_id: str
    user_id: int
    username: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    tcs_score: int = 0
    status: TradeStatus = TradeStatus.PENDING
    outcome: TradeOutcome = TradeOutcome.PENDING
    profit_loss: float = 0.0
    pip_profit: float = 0.0
    open_time: str = ""
    close_time: Optional[str] = None
    hold_duration: int = 0  # seconds
    xp_earned: int = 0
    comment: str = ""
    bridge_response: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

class TradeWriter:
    """Trade logging and persistence system"""
    
    def __init__(self, data_dir: str = None, xp_logger: XPLogger = None):
        self.data_dir = Path(data_dir or "/root/HydraX-v2/data/trades")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database paths
        self.db_path = self.data_dir / "trades.db"
        self.exports_dir = self.data_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        
        # XP Logger integration
        self.xp_logger = xp_logger or XPLogger()
        
        # Pip values for different currency pairs
        self.pip_values = {
            'GBPUSD': 0.0001,
            'EURUSD': 0.0001,
            'USDCAD': 0.0001,
            'GBPJPY': 0.01,
            'USDJPY': 0.01,
            'EURJPY': 0.01,
            'CHFJPY': 0.01,
            'GBPCHF': 0.0001,
            'EURCHF': 0.0001,
            'USDCHF': 0.0001
        }
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for trade storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Main trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        trade_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        volume REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        tcs_score INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        outcome TEXT DEFAULT 'pending',
                        profit_loss REAL DEFAULT 0.0,
                        pip_profit REAL DEFAULT 0.0,
                        open_time TEXT NOT NULL,
                        close_time TEXT,
                        hold_duration INTEGER DEFAULT 0,
                        xp_earned INTEGER DEFAULT 0,
                        comment TEXT DEFAULT '',
                        bridge_response TEXT,
                        error_message TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Trade events table for audit trail
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (trade_id) REFERENCES trades (trade_id)
                    )
                ''')
                
                # Daily summaries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_volume REAL DEFAULT 0.0,
                        total_profit REAL DEFAULT 0.0,
                        total_pips REAL DEFAULT 0.0,
                        best_trade REAL DEFAULT 0.0,
                        worst_trade REAL DEFAULT 0.0,
                        xp_earned INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        UNIQUE(user_id, date)
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_open_time ON trades(open_time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_events_trade_id ON trade_events(trade_id)')
                
                conn.commit()
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Database initialization failed: {e}")
    
    def log_trade_request(self, trade_record: TradeRecord) -> bool:
        """Log initial trade request"""
        try:
            timestamp = datetime.now().isoformat()
            trade_record.created_at = timestamp
            trade_record.updated_at = timestamp
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert trade record
                cursor.execute('''
                    INSERT INTO trades (
                        trade_id, user_id, username, symbol, direction, volume,
                        entry_price, stop_loss, take_profit, tcs_score, status,
                        open_time, comment, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_record.trade_id,
                    trade_record.user_id,
                    trade_record.username,
                    trade_record.symbol,
                    trade_record.direction,
                    trade_record.volume,
                    trade_record.entry_price,
                    trade_record.stop_loss,
                    trade_record.take_profit,
                    trade_record.tcs_score,
                    trade_record.status.value,
                    trade_record.open_time,
                    trade_record.comment,
                    trade_record.created_at,
                    trade_record.updated_at
                ))
                
                # Log event
                self._log_trade_event(cursor, trade_record.trade_id, "trade_requested", {
                    "symbol": trade_record.symbol,
                    "direction": trade_record.direction,
                    "volume": trade_record.volume,
                    "tcs_score": trade_record.tcs_score
                })
                
                conn.commit()
                
                # Integrate with XP logger
                if self.xp_logger:
                    xp_trade_log = TradeLog(
                        trade_id=trade_record.trade_id,
                        user_id=trade_record.user_id,
                        symbol=trade_record.symbol,
                        direction=trade_record.direction,
                        volume=trade_record.volume,
                        entry_price=trade_record.entry_price,
                        stop_loss=trade_record.stop_loss,
                        take_profit=trade_record.take_profit,
                        tcs_score=trade_record.tcs_score,
                        open_time=trade_record.open_time,
                        comment=trade_record.comment
                    )
                    self.xp_logger.log_trade_open(xp_trade_log)
                
                return True
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to log trade request: {e}")
            return False
    
    def update_trade_execution(self, trade_id: str, execution_result: TradeExecutionResult) -> bool:
        """Update trade with execution results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update trade status
                status = TradeStatus.EXECUTED if execution_result.success else TradeStatus.FAILED
                
                cursor.execute('''
                    UPDATE trades SET 
                        status = ?, entry_price = ?, bridge_response = ?, 
                        error_message = ?, updated_at = ?
                    WHERE trade_id = ?
                ''', (
                    status.value,
                    execution_result.execution_price or 0.0,
                    json.dumps(asdict(execution_result)) if execution_result else None,
                    execution_result.message if not execution_result.success else None,
                    datetime.now().isoformat(),
                    trade_id
                ))
                
                # Log event
                event_data = {
                    "success": execution_result.success,
                    "execution_price": execution_result.execution_price,
                    "message": execution_result.message
                }
                self._log_trade_event(cursor, trade_id, "trade_executed", event_data)
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to update execution: {e}")
            return False
    
    def close_trade(self, trade_id: str, exit_price: float, outcome: TradeOutcome, profit_loss: float = None) -> bool:
        """Close trade and calculate final metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trade details
                cursor.execute('SELECT * FROM trades WHERE trade_id = ?', (trade_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                # Calculate profit/loss if not provided
                if profit_loss is None:
                    entry_price = row[6]  # entry_price column
                    volume = row[5]       # volume column
                    direction = row[4]    # direction column
                    symbol = row[3]       # symbol column
                    
                    # Calculate pip difference
                    pip_value = self.pip_values.get(symbol, 0.0001)
                    if direction.lower() == 'buy':
                        pip_profit = (exit_price - entry_price) / pip_value
                    else:
                        pip_profit = (entry_price - exit_price) / pip_value
                    
                    # Simplified P&L calculation (would need real contract size in production)
                    profit_loss = pip_profit * pip_value * volume * 100000  # Assuming 100k lot size
                else:
                    pip_profit = 0.0  # Calculate if needed
                
                close_time = datetime.now()
                open_time = datetime.fromisoformat(row[15])  # open_time column
                hold_duration = int((close_time - open_time).total_seconds())
                
                # Update trade record
                cursor.execute('''
                    UPDATE trades SET 
                        exit_price = ?, status = ?, outcome = ?, profit_loss = ?,
                        pip_profit = ?, close_time = ?, hold_duration = ?, updated_at = ?
                    WHERE trade_id = ?
                ''', (
                    exit_price,
                    TradeStatus.CLOSED.value,
                    outcome.value,
                    profit_loss,
                    pip_profit,
                    close_time.isoformat(),
                    hold_duration,
                    datetime.now().isoformat(),
                    trade_id
                ))
                
                # Log event
                event_data = {
                    "exit_price": exit_price,
                    "outcome": outcome.value,
                    "profit_loss": profit_loss,
                    "pip_profit": pip_profit,
                    "hold_duration": hold_duration
                }
                self._log_trade_event(cursor, trade_id, "trade_closed", event_data)
                
                conn.commit()
                
                # Update XP logger
                if self.xp_logger:
                    self.xp_logger.log_trade_close(trade_id, exit_price, outcome, profit_loss)
                
                # Update daily summary
                self._update_daily_summary(row[1], close_time.date().isoformat(), outcome, profit_loss, pip_profit, row[5])
                
                return True
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to close trade: {e}")
            return False
    
    def get_trade_history(self, user_id: int, limit: int = 100, symbol: str = None, start_date: str = None, end_date: str = None) -> List[TradeRecord]:
        """Get trade history with filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                query = "SELECT * FROM trades WHERE user_id = ?"
                params = [user_id]
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if start_date:
                    query += " AND DATE(open_time) >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND DATE(open_time) <= ?"
                    params.append(end_date)
                
                query += " ORDER BY open_time DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                trades = []
                for row in rows:
                    trade = TradeRecord(
                        trade_id=row[0],
                        user_id=row[1],
                        username=row[2],
                        symbol=row[3],
                        direction=row[4],
                        volume=row[5],
                        entry_price=row[6],
                        exit_price=row[7],
                        stop_loss=row[8],
                        take_profit=row[9],
                        tcs_score=row[10],
                        status=TradeStatus(row[11]),
                        outcome=TradeOutcome(row[12]),
                        profit_loss=row[13],
                        pip_profit=row[14],
                        open_time=row[15],
                        close_time=row[16],
                        hold_duration=row[17],
                        xp_earned=row[18],
                        comment=row[19],
                        bridge_response=json.loads(row[20]) if row[20] else None,
                        error_message=row[21],
                        created_at=row[22],
                        updated_at=row[23]
                    )
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to get trade history: {e}")
            return []
    
    def get_trade_statistics(self, user_id: int, period_days: int = 30) -> Dict:
        """Get comprehensive trade statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Date filter
                start_date = (datetime.now() - timedelta(days=period_days)).isoformat()
                
                # Basic stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        COUNT(CASE WHEN outcome = 'win' THEN 1 END) as winning_trades,
                        COUNT(CASE WHEN outcome = 'loss' THEN 1 END) as losing_trades,
                        SUM(volume) as total_volume,
                        SUM(profit_loss) as total_profit,
                        SUM(pip_profit) as total_pips,
                        MAX(profit_loss) as best_trade,
                        MIN(profit_loss) as worst_trade,
                        AVG(hold_duration) as avg_hold_time,
                        SUM(xp_earned) as total_xp
                    FROM trades 
                    WHERE user_id = ? AND open_time >= ? AND status = 'closed'
                ''', (user_id, start_date))
                
                row = cursor.fetchone()
                
                # Calculate derived metrics
                total_trades = row[0] or 0
                winning_trades = row[1] or 0
                losing_trades = row[2] or 0
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate profit factor
                cursor.execute('''
                    SELECT 
                        SUM(CASE WHEN profit_loss > 0 THEN profit_loss ELSE 0 END) as total_gains,
                        SUM(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) ELSE 0 END) as total_losses
                    FROM trades 
                    WHERE user_id = ? AND open_time >= ? AND status = 'closed'
                ''', (user_id, start_date))
                
                pf_row = cursor.fetchone()
                total_gains = pf_row[0] or 0
                total_losses = pf_row[1] or 0
                profit_factor = total_gains / total_losses if total_losses > 0 else 0
                
                # Symbol breakdown
                cursor.execute('''
                    SELECT symbol, COUNT(*), SUM(profit_loss), 
                           COUNT(CASE WHEN outcome = 'win' THEN 1 END) as wins
                    FROM trades 
                    WHERE user_id = ? AND open_time >= ? AND status = 'closed'
                    GROUP BY symbol
                    ORDER BY COUNT(*) DESC
                ''', (user_id, start_date))
                
                symbol_stats = []
                for symbol_row in cursor.fetchall():
                    symbol_trades = symbol_row[1]
                    symbol_wins = symbol_row[3]
                    symbol_win_rate = (symbol_wins / symbol_trades * 100) if symbol_trades > 0 else 0
                    
                    symbol_stats.append({
                        'symbol': symbol_row[0],
                        'trades': symbol_trades,
                        'profit': symbol_row[2],
                        'win_rate': symbol_win_rate
                    })
                
                return {
                    'period_days': period_days,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'total_volume': row[3] or 0,
                    'total_profit': row[4] or 0,
                    'total_pips': row[5] or 0,
                    'best_trade': row[6] or 0,
                    'worst_trade': row[7] or 0,
                    'avg_hold_time': row[8] or 0,
                    'total_xp': row[9] or 0,
                    'profit_factor': profit_factor,
                    'symbol_breakdown': symbol_stats
                }
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to get statistics: {e}")
            return {}
    
    def export_trades(self, user_id: int, format_type: ExportFormat, filename: str = None, start_date: str = None, end_date: str = None) -> str:
        """Export trades to various formats"""
        try:
            trades = self.get_trade_history(user_id, limit=10000, start_date=start_date, end_date=end_date)
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"trades_export_{user_id}_{timestamp}"
            
            export_path = self.exports_dir / f"{filename}.{format_type.value}"
            
            if format_type == ExportFormat.JSON:
                self._export_json(trades, export_path)
            elif format_type == ExportFormat.CSV:
                self._export_csv(trades, export_path)
            elif format_type == ExportFormat.MT4_CSV:
                self._export_mt4_csv(trades, export_path)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            return str(export_path)
            
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Export failed: {e}")
            return ""
    
    def _export_json(self, trades: List[TradeRecord], filepath: Path):
        """Export trades to JSON format"""
        trade_data = []
        for trade in trades:
            trade_dict = asdict(trade)
            # Convert enums to strings
            trade_dict['status'] = trade.status.value
            trade_dict['outcome'] = trade.outcome.value
            trade_data.append(trade_dict)
        
        with open(filepath, 'w') as f:
            json.dump(trade_data, f, indent=2, default=str)
    
    def _export_csv(self, trades: List[TradeRecord], filepath: Path):
        """Export trades to CSV format"""
        if not trades:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            headers = [
                'Trade ID', 'Symbol', 'Direction', 'Volume', 'Entry Price', 'Exit Price',
                'Stop Loss', 'Take Profit', 'TCS Score', 'Status', 'Outcome',
                'Profit/Loss', 'Pip Profit', 'Open Time', 'Close Time', 'Hold Duration',
                'XP Earned', 'Comment'
            ]
            writer.writerow(headers)
            
            # Data rows
            for trade in trades:
                row = [
                    trade.trade_id, trade.symbol, trade.direction, trade.volume,
                    trade.entry_price, trade.exit_price or '', trade.stop_loss or '',
                    trade.take_profit or '', trade.tcs_score, trade.status.value,
                    trade.outcome.value, trade.profit_loss, trade.pip_profit,
                    trade.open_time, trade.close_time or '', trade.hold_duration,
                    trade.xp_earned, trade.comment
                ]
                writer.writerow(row)
    
    def _export_mt4_csv(self, trades: List[TradeRecord], filepath: Path):
        """Export trades in MT4 history format"""
        if not trades:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # MT4 format header
            headers = [
                'Ticket', 'Open Time', 'Type', 'Size', 'Symbol', 'Price',
                'S/L', 'T/P', 'Close Time', 'Price', 'Commission', 'Swap',
                'Profit', 'Comment'
            ]
            writer.writerow(headers)
            
            # Data rows in MT4 format
            for trade in trades:
                if trade.status == TradeStatus.CLOSED:
                    order_type = 0 if trade.direction.lower() == 'buy' else 1
                    row = [
                        trade.trade_id[:8],  # Ticket (shortened)
                        trade.open_time,     # Open Time
                        order_type,          # Type (0=Buy, 1=Sell)
                        trade.volume,        # Size
                        trade.symbol,        # Symbol
                        trade.entry_price,   # Open Price
                        trade.stop_loss or 0,    # S/L
                        trade.take_profit or 0,  # T/P
                        trade.close_time or '',  # Close Time
                        trade.exit_price or 0,   # Close Price
                        0,                   # Commission
                        0,                   # Swap
                        trade.profit_loss,   # Profit
                        trade.comment        # Comment
                    ]
                    writer.writerow(row)
    
    def _log_trade_event(self, cursor, trade_id: str, event_type: str, event_data: Dict):
        """Log trade event for audit trail"""
        cursor.execute('''
            INSERT INTO trade_events (trade_id, event_type, event_data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (trade_id, event_type, json.dumps(event_data), datetime.now().isoformat()))
    
    def _update_daily_summary(self, user_id: int, date: str, outcome: TradeOutcome, profit_loss: float, pip_profit: float, volume: float):
        """Update daily trading summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if summary exists
                cursor.execute('SELECT * FROM daily_summaries WHERE user_id = ? AND date = ?', (user_id, date))
                row = cursor.fetchone()
                
                if row:
                    # Update existing summary
                    total_trades = row[3] + 1
                    winning_trades = row[4] + (1 if outcome == TradeOutcome.WIN else 0)
                    losing_trades = row[5] + (1 if outcome == TradeOutcome.LOSS else 0)
                    total_volume = row[6] + volume
                    total_profit = row[7] + profit_loss
                    total_pips = row[8] + pip_profit
                    best_trade = max(row[9], profit_loss)
                    worst_trade = min(row[10], profit_loss)
                    
                    cursor.execute('''
                        UPDATE daily_summaries SET 
                            total_trades = ?, winning_trades = ?, losing_trades = ?,
                            total_volume = ?, total_profit = ?, total_pips = ?,
                            best_trade = ?, worst_trade = ?
                        WHERE user_id = ? AND date = ?
                    ''', (
                        total_trades, winning_trades, losing_trades,
                        total_volume, total_profit, total_pips,
                        best_trade, worst_trade, user_id, date
                    ))
                else:
                    # Create new summary
                    cursor.execute('''
                        INSERT INTO daily_summaries (
                            user_id, date, total_trades, winning_trades, losing_trades,
                            total_volume, total_profit, total_pips, best_trade, worst_trade, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, date, 1,
                        1 if outcome == TradeOutcome.WIN else 0,
                        1 if outcome == TradeOutcome.LOSS else 0,
                        volume, profit_loss, pip_profit,
                        profit_loss, profit_loss,
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to update daily summary: {e}")
    
    def get_daily_summaries(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get daily trading summaries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
                
                cursor.execute('''
                    SELECT * FROM daily_summaries 
                    WHERE user_id = ? AND date >= ?
                    ORDER BY date DESC
                ''', (user_id, start_date))
                
                summaries = []
                for row in cursor.fetchall():
                    win_rate = (row[4] / row[3] * 100) if row[3] > 0 else 0
                    summaries.append({
                        'date': row[2],
                        'total_trades': row[3],
                        'winning_trades': row[4],
                        'losing_trades': row[5],
                        'win_rate': win_rate,
                        'total_volume': row[6],
                        'total_profit': row[7],
                        'total_pips': row[8],
                        'best_trade': row[9],
                        'worst_trade': row[10],
                        'xp_earned': row[11]
                    })
                
                return summaries
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to get daily summaries: {e}")
            return []
    
    def format_trade_summary(self, user_id: int, period_days: int = 7) -> str:
        """Format trading summary for Telegram"""
        try:
            stats = self.get_trade_statistics(user_id, period_days)
            recent_trades = self.get_trade_history(user_id, limit=5)
            
            if not stats:
                return "📊 **No trading data available**"
            
            summary = f"""📊 **Trading Summary ({period_days} days)**

🎯 **Performance:**
• Total Trades: {stats['total_trades']}
• Win Rate: {stats['win_rate']:.1f}%
• Total Volume: {stats['total_volume']:.2f} lots
• Total P&L: ${stats['total_profit']:.2f}
• Total Pips: {stats['total_pips']:.1f}

💰 **Best/Worst:**
• Best Trade: ${stats['best_trade']:.2f}
• Worst Trade: ${stats['worst_trade']:.2f}
• Profit Factor: {stats['profit_factor']:.2f}
• Avg Hold Time: {stats['avg_hold_time']/3600:.1f}h

🎮 **XP & Progress:**
• XP Earned: {stats['total_xp']} points"""

            if stats['symbol_breakdown']:
                summary += "\n\n📈 **Top Symbols:**\n"
                for symbol_data in stats['symbol_breakdown'][:3]:
                    summary += f"• {symbol_data['symbol']}: {symbol_data['trades']} trades, ${symbol_data['profit']:.2f}\n"
            
            if recent_trades:
                summary += "\n\n🔥 **Recent Trades:**\n"
                for trade in recent_trades[:3]:
                    status_emoji = "✅" if trade.outcome == TradeOutcome.WIN else "❌" if trade.outcome == TradeOutcome.LOSS else "⏳"
                    summary += f"• {status_emoji} {trade.symbol} {trade.direction} {trade.volume} lots"
                    if trade.profit_loss != 0:
                        summary += f" (${trade.profit_loss:.2f})"
                    summary += "\n"
            
            return summary
            
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Failed to format summary: {e}")
            return "❌ Error generating trade summary"
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old trade data"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Archive old trades to backup before deletion
                backup_path = self.exports_dir / f"archived_trades_{datetime.now().strftime('%Y%m%d')}.json"
                
                cursor.execute('SELECT * FROM trades WHERE created_at < ?', (cutoff_date,))
                old_trades = cursor.fetchall()
                
                if old_trades:
                    # Export to backup
                    with open(backup_path, 'w') as f:
                        json.dump([dict(zip([col[0] for col in cursor.description], row)) for row in old_trades], f, indent=2, default=str)
                    
                    # Delete old data
                    cursor.execute('DELETE FROM trades WHERE created_at < ?', (cutoff_date,))
                    cursor.execute('DELETE FROM trade_events WHERE timestamp < ?', (cutoff_date,))
                    cursor.execute('DELETE FROM daily_summaries WHERE created_at < ?', (cutoff_date,))
                    
                    conn.commit()
                    
                    print(f"[TRADE_WRITER] Cleaned up {len(old_trades)} old trades, backed up to {backup_path}")
                
        except Exception as e:
            print(f"[TRADE_WRITER ERROR] Cleanup failed: {e}")
