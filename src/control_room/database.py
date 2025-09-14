"""
Database module for Throne Control Panel
Handles SQLite database operations and schema management
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = "/root/HydraX-v2/data/elite_guard_reports.db"

def ensure_database_exists() -> bool:
    """Ensure database and tables exist with proper schema"""
    try:
        # Create data directory if it doesn't exist
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create signals table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            signal_id TEXT UNIQUE NOT NULL,
            session TEXT,
            pattern_name TEXT,
            pair TEXT,
            confidence_score REAL,
            quality_score REAL,
            thresholds_applied TEXT,
            volatility_atr REAL,
            volume_zscore REAL,
            market_regime TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            join_date TEXT NOT NULL,
            total_trades INTEGER DEFAULT 0,
            allow_signal_notifications BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

        # Create trades table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT NOT NULL,
            user_id INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            win_loss_status BOOLEAN,
            pl_dollars REAL,
            pl_pips REAL,
            time_to_outcome_minutes INTEGER,
            outcome_source TEXT,
            sl_distance_pips REAL,
            tp_distance_pips REAL,
            rr_ratio_realized REAL,
            rr_ratio_intended REAL,
            risk_percentage REAL,
            execution_status TEXT,
            timeout_loss BOOLEAN DEFAULT 0,
            false_negative BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (signal_id) REFERENCES signals(signal_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create session_metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT NOT NULL,
            win_rate REAL,
            expectancy_r REAL,
            signal_count INTEGER,
            updated_at TEXT DEFAULT (datetime('now'))
        )
        """)
        
        # Create actions table for system monitoring and audit logging
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            user_id INTEGER,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'SUCCESS',
            details TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_pair ON signals(pair)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_session ON signals(session)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_pattern ON signals(pattern_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_user_id ON actions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_type ON actions(action_type)")
        
        # Insert sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM signals")
        signal_count = cursor.fetchone()[0]
        
        if signal_count == 0:
            insert_sample_data(cursor)
            
        # Insert sample actions if actions table is empty
        cursor.execute("SELECT COUNT(*) FROM actions")
        action_count = cursor.fetchone()[0]
        
        if action_count == 0:
            insert_sample_actions(cursor)
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def insert_sample_data(cursor: sqlite3.Cursor):
    """Insert comprehensive sample data for testing purposes"""
    
    # Insert sample users first with notification preferences
    sample_users = [
        ("trader1", "2025-08-01", 150, 1),
        ("trader2", "2025-08-05", 89, 0),
        ("elite_user", "2025-07-15", 245, 1),
        ("scalper_pro", "2025-08-10", 78, 1),
        ("swing_master", "2025-07-20", 132, 0),
        ("algo_bot", "2025-08-15", 67, 1),
        ("risk_manager", "2025-07-25", 198, 1),
        ("pattern_hunter", "2025-08-20", 56, 0),
        ("momentum_trader", "2025-08-03", 123, 1),
        ("gold_specialist", "2025-07-30", 87, 0),
    ]
    
    for user in sample_users:
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, join_date, total_trades, allow_signal_notifications)
        VALUES (?, ?, ?, ?)
        """, user)
    
    # Enhanced sample signals with more patterns and pairs
    sample_signals = [
        ("2025-09-01 08:15:00", "ELITE_SNIPER_EURUSD_1725177300", "LONDON", "ORDER_BLOCK_BOUNCE", "EURUSD", 37.1, 42.5, "confidence_70", 0.0012, 1.5, "TRENDING"),
        ("2025-09-01 14:30:00", "ELITE_SNIPER_GBPUSD_1725199800", "NY", "LIQUIDITY_SWEEP_REVERSAL", "GBPUSD", 71.4, 78.3, "confidence_80", 0.0018, 2.1, "VOLATILE"),
        ("2025-09-01 16:45:00", "ELITE_SNIPER_XAUUSD_1725207900", "NY", "VCB_BREAKOUT", "XAUUSD", 68.2, 75.7, "confidence_75", 0.45, 1.8, "TRENDING"),
        ("2025-09-02 03:20:00", "ELITE_SNIPER_USDJPY_1725246000", "TOKYO", "FAIR_VALUE_GAP_FILL", "USDJPY", 42.8, 48.8, "confidence_70", 0.15, 1.2, "CONSOLIDATING"),
        ("2025-09-02 09:45:00", "ELITE_SNIPER_USDCHF_1725269100", "LONDON", "MOMENTUM_BREAKOUT", "USDCHF", 71.4, 82.1, "confidence_85", 0.0014, 2.4, "VOLATILE"),
        ("2025-09-02 11:20:00", "ELITE_SNIPER_GBPJPY_1725276000", "LONDON", "SWEEP_AND_RETURN", "GBPJPY", 65.8, 72.3, "confidence_75", 0.22, 1.9, "TRENDING"),
        ("2025-09-02 15:35:00", "ELITE_SNIPER_EURJPY_1725291300", "NY", "EMA_RSI_SCALP", "EURJPY", 59.7, 64.2, "confidence_70", 0.18, 1.6, "CONSOLIDATING"),
        ("2025-09-03 07:10:00", "ELITE_SNIPER_AUDUSD_1725346200", "LONDON", "BB_SCALP", "AUDUSD", 61.2, 67.8, "confidence_75", 0.0016, 1.3, "VOLATILE"),
        ("2025-09-03 12:25:00", "ELITE_SNIPER_NZDUSD_1725365100", "NY", "KALMAN_QUICKFIRE", "NZDUSD", 75.6, 83.9, "confidence_85", 0.0013, 2.2, "TRENDING"),
        ("2025-09-03 18:40:00", "ELITE_SNIPER_EURGBP_1725387600", "LONDON", "ORDER_BLOCK_BOUNCE", "EURGBP", 45.3, 52.1, "confidence_70", 0.0009, 1.1, "CONSOLIDATING"),
    ]
    
    for signal in sample_signals:
        cursor.execute("""
        INSERT OR IGNORE INTO signals (timestamp, signal_id, session, pattern_name, pair, confidence_score, quality_score, thresholds_applied, volatility_atr, volume_zscore, market_regime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, signal)
    
    # Enhanced sample trades with user_id assignments
    sample_trades = [
        ("ELITE_SNIPER_EURUSD_1725177300", 1, "2025-09-01 09:42:00", False, -18.45, -8.3, 87, "broker", 18.5, 24.8, -0.45, 1.34, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_GBPUSD_1725199800", 2, "2025-09-01 15:15:00", True, 42.67, 18.7, 45, "broker", 20.1, 28.9, 1.44, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_XAUUSD_1725207900", 3, "2025-09-01 17:23:00", True, 127.89, 8.9, 38, "broker", 15.2, 22.8, 1.28, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_USDJPY_1725246000", 4, "2025-09-02 04:55:00", False, -22.15, -11.4, 95, "broker", 16.7, 21.3, -0.67, 1.27, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_USDCHF_1725269100", 5, "2025-09-02 10:12:00", True, 35.67, 16.2, 27, "broker", 19.8, 29.7, 1.89, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_GBPJPY_1725276000", 6, "2025-09-02 11:35:00", True, 31.22, 14.7, 52, "broker", 18.3, 26.4, 1.43, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_EURJPY_1725291300", 7, "2025-09-02 16:20:00", False, -25.34, -12.1, 73, "broker", 17.9, 23.7, -0.71, 1.32, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_AUDUSD_1725346200", 8, "2025-09-03 08:45:00", True, 29.45, 13.1, 64, "broker", 19.2, 28.8, 1.52, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_NZDUSD_1725365100", 9, "2025-09-03 13:10:00", True, 41.32, 18.9, 31, "broker", 20.4, 30.6, 2.12, 1.50, 2.0, "FILLED", False, False),
        ("ELITE_SNIPER_EURGBP_1725387600", 10, "2025-09-03 19:25:00", False, -15.23, -7.8, 89, "broker", 16.8, 25.2, -0.45, 1.50, 2.0, "FILLED", False, False),
    ]
    
    for trade in sample_trades:
        cursor.execute("""
        INSERT OR IGNORE INTO trades (signal_id, user_id, timestamp, win_loss_status, pl_dollars, pl_pips, time_to_outcome_minutes, outcome_source, sl_distance_pips, tp_distance_pips, rr_ratio_realized, rr_ratio_intended, risk_percentage, execution_status, timeout_loss, false_negative)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, trade)
    
    logger.info("Enhanced sample data inserted successfully")

def insert_sample_actions(cursor: sqlite3.Cursor):
    """Insert sample system actions for testing purposes"""
    
    # Sample actions with different types for monitoring
    sample_actions = [
        ("2025-09-07 08:15:00", 1, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_EURUSD_1725177300", "pair": "EURUSD", "pattern": "ORDER_BLOCK_BOUNCE"}'),
        ("2025-09-07 08:16:00", None, "SYSTEM_STATUS", "SUCCESS", '{"signals_per_hour": 12, "active_users": 7, "kill_switch": false}'),
        ("2025-09-07 09:30:00", 3, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_GBPUSD_1725199800", "pair": "GBPUSD", "pattern": "LIQUIDITY_SWEEP_REVERSAL"}'),
        ("2025-09-07 09:45:00", 1, "KILL_SWITCH", "SUCCESS", '{"enabled": false, "reason": "Manual toggle", "duration_minutes": 15}'),
        ("2025-09-07 10:00:00", 1, "TOGGLE_LEROY", "SUCCESS", '{"enabled": true, "mode": "aggressive", "threshold_adjustment": 5}'),
        ("2025-09-07 10:30:00", 5, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_XAUUSD_1725207900", "pair": "XAUUSD", "pattern": "VCB_BREAKOUT"}'),
        ("2025-09-07 11:15:00", None, "SYSTEM_STATUS", "SUCCESS", '{"signals_per_hour": 8, "active_users": 9, "kill_switch": false}'),
        ("2025-09-07 12:00:00", 2, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_USDJPY_1725246000", "pair": "USDJPY", "pattern": "FAIR_VALUE_GAP_FILL"}'),
        ("2025-09-07 12:30:00", 4, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_USDCHF_1725269100", "pair": "USDCHF", "pattern": "MOMENTUM_BREAKOUT"}'),
        ("2025-09-07 13:00:00", 1, "KILL_SWITCH", "SUCCESS", '{"enabled": true, "reason": "High volatility", "auto_triggered": true}'),
        ("2025-09-07 13:15:00", 6, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_GBPJPY_1725276000", "pair": "GBPJPY", "pattern": "SWEEP_AND_RETURN"}'),
        ("2025-09-07 14:00:00", 1, "TOGGLE_LEROY", "SUCCESS", '{"enabled": false, "mode": "conservative", "threshold_adjustment": -3}'),
        ("2025-09-07 14:30:00", 7, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_EURJPY_1725291300", "pair": "EURJPY", "pattern": "EMA_RSI_SCALP"}'),
        ("2025-09-07 15:00:00", None, "SYSTEM_STATUS", "SUCCESS", '{"signals_per_hour": 15, "active_users": 12, "kill_switch": true}'),
        ("2025-09-07 15:30:00", 8, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_AUDUSD_1725346200", "pair": "AUDUSD", "pattern": "BB_SCALP"}'),
        ("2025-09-07 16:00:00", 1, "KILL_SWITCH", "SUCCESS", '{"enabled": false, "reason": "Manual disable", "duration_minutes": 45}'),
        ("2025-09-07 16:15:00", 9, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_NZDUSD_1725365100", "pair": "NZDUSD", "pattern": "KALMAN_QUICKFIRE"}'),
        ("2025-09-07 17:00:00", 10, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_EURGBP_1725387600", "pair": "EURGBP", "pattern": "ORDER_BLOCK_BOUNCE"}'),
        ("2025-09-07 17:30:00", 1, "TOGGLE_LEROY", "SUCCESS", '{"enabled": true, "mode": "balanced", "threshold_adjustment": 0}'),
        ("2025-09-07 18:00:00", None, "SYSTEM_STATUS", "SUCCESS", '{"signals_per_hour": 10, "active_users": 8, "kill_switch": false}'),
        # Additional recent actions
        ("2025-09-07 18:30:00", 3, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_CADJPY_1725398400", "pair": "CADJPY", "pattern": "LIQUIDITY_SWEEP_REVERSAL"}'),
        ("2025-09-07 19:00:00", 5, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_CHFJPY_1725400200", "pair": "CHFJPY", "pattern": "VCB_BREAKOUT"}'),
        ("2025-09-07 19:30:00", 7, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_NZDJPY_1725402000", "pair": "NZDJPY", "pattern": "MOMENTUM_BREAKOUT"}'),
        ("2025-09-07 20:00:00", None, "SYSTEM_STATUS", "SUCCESS", '{"signals_per_hour": 6, "active_users": 5, "kill_switch": false}'),
        ("2025-09-07 20:30:00", 2, "SIGNAL_LOG", "SUCCESS", '{"signal_id": "ELITE_SNIPER_EURAUD_1725405600", "pair": "EURAUD", "pattern": "FAIR_VALUE_GAP_FILL"}'),
    ]
    
    for action in sample_actions:
        cursor.execute("""
        INSERT OR IGNORE INTO actions (timestamp, user_id, action_type, status, details)
        VALUES (?, ?, ?, ?, ?)
        """, action)
    
    logger.info("Sample actions inserted successfully")

def get_database_info() -> dict:
    """Get database information and statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signals")
        signal_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actions")
        action_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT pair) FROM signals")
        unique_pairs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT pattern_name) FROM signals")
        unique_patterns = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "database_path": DATABASE_PATH,
            "signal_count": signal_count,
            "trade_count": trade_count,
            "user_count": user_count,
            "action_count": action_count,
            "unique_pairs": unique_pairs,
            "unique_patterns": unique_patterns,
            "status": "connected"
        }
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "database_path": DATABASE_PATH,
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Initialize database when run directly
    success = ensure_database_exists()
    if success:
        info = get_database_info()
        print("Database Status:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to initialize database")