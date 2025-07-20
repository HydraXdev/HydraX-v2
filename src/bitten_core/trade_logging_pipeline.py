#!/usr/bin/env python3
"""
BITTEN Trade Logging Pipeline
Comprehensive trade logging system for complete round trip recording
"""

import json
import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class TradeLoggingPipeline:
    """Comprehensive trade logging system for BITTEN"""
    
    def __init__(self, base_dir: str = "/root/HydraX-v2"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.fired_trades_file = self.base_dir / "fired_trades.json"
        self.engagement_db_path = self.data_dir / "engagement.db"
        self.trades_db_path = self.data_dir / "trades" / "trades.db"
        self.bridge_log_path = self.base_dir / "bridge_core.log"
        
        # Ensure trades directory exists
        (self.data_dir / "trades").mkdir(exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize databases
        self.init_databases()
        
    def setup_logging(self):
        """Setup bridge core logging"""
        log_formatter = logging.Formatter(
            '%(asctime)s - [TRADE_PIPELINE] %(levelname)s - %(message)s'
        )
        
        # File handler for bridge_core.log
        if not os.path.exists(self.bridge_log_path):
            self.bridge_log_path.touch()
            
        file_handler = logging.FileHandler(self.bridge_log_path)
        file_handler.setFormatter(log_formatter)
        
        # Configure logger
        pipeline_logger = logging.getLogger('trade_pipeline')
        pipeline_logger.setLevel(logging.INFO)
        pipeline_logger.addHandler(file_handler)
        
        self.pipeline_logger = pipeline_logger
        
    def init_databases(self):
        """Initialize database tables if they don't exist"""
        try:
            # Initialize engagement.db
            self.init_engagement_db()
            
            # Initialize trades.db
            self.init_trades_db()
            
            self.pipeline_logger.info("Database tables initialized successfully")
            
        except Exception as e:
            self.pipeline_logger.error(f"Database initialization failed: {e}")
    
    def init_engagement_db(self):
        """Initialize engagement database tables - use existing schema"""
        with sqlite3.connect(self.engagement_db_path) as conn:
            cursor = conn.cursor()
            
            # Don't create tables - they already exist with correct schema
            # Just ensure they exist, but don't override existing structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fire_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT DEFAULT 'fire'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_engagement (
                    user_id TEXT PRIMARY KEY,
                    total_fires INTEGER DEFAULT 0,
                    total_signals_engaged INTEGER DEFAULT 0,
                    last_fire_time TEXT,
                    streak_days INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
    
    def init_trades_db(self):
        """Initialize trades database tables"""
        with sqlite3.connect(self.trades_db_path) as conn:
            cursor = conn.cursor()
            
            # Create trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket TEXT,
                    mission_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    volume REAL NOT NULL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    execution_price REAL,
                    tcs_score REAL,
                    result TEXT,
                    status TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    duration INTEGER,
                    pips_result REAL,
                    profit_loss REAL,
                    comment TEXT,
                    bridge_response TEXT
                )
            ''')
            
            conn.commit()
    
    def log_complete_trade(self, mission_data: Dict[str, Any], execution_result: Dict[str, Any], 
                          user_id: str, mission_id: str) -> bool:
        """Log complete trade to all systems"""
        try:
            self.pipeline_logger.info(f"Starting complete trade logging for mission: {mission_id}")
            
            # Extract trade data
            trade_data = self.extract_trade_data(mission_data, execution_result, user_id, mission_id)
            
            # Log to all systems
            results = []
            
            # 1. Log to fired_trades.json
            results.append(self.log_to_fired_trades(trade_data))
            
            # 2. Log to engagement.db (fire_actions table)
            results.append(self.log_to_fire_actions(trade_data))
            
            # 3. Log to trades.db
            results.append(self.log_to_trades_db(trade_data))
            
            # 4. Update user engagement stats
            results.append(self.update_user_engagement(trade_data))
            
            # 5. Log to bridge core log
            self.log_to_bridge_core(trade_data)
            
            success = all(results)
            
            if success:
                self.pipeline_logger.info(f"✅ Complete trade logging successful for mission: {mission_id}")
            else:
                self.pipeline_logger.error(f"❌ Some logging operations failed for mission: {mission_id}")
                
            return success
            
        except Exception as e:
            self.pipeline_logger.error(f"❌ Complete trade logging failed: {e}")
            return False
    
    def extract_trade_data(self, mission_data: Dict[str, Any], execution_result: Dict[str, Any], 
                          user_id: str, mission_id: str) -> Dict[str, Any]:
        """Extract standardized trade data from mission and execution result"""
        
        # Get signal data
        signal = mission_data.get('signal', {})
        enhanced_signal = mission_data.get('enhanced_signal', signal)
        
        # Extract timing data
        timing = mission_data.get('timing', {})
        created_at = timing.get('created_at', datetime.now().isoformat())
        fired_at = mission_data.get('fired_at', datetime.now().isoformat())
        
        # Calculate duration
        try:
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            fired_time = datetime.fromisoformat(fired_at.replace('Z', '+00:00'))
            duration = int((fired_time - created_time).total_seconds())
        except:
            duration = 0
        
        return {
            'mission_id': mission_id,
            'user_id': user_id,
            'symbol': enhanced_signal.get('symbol', 'UNKNOWN'),
            'direction': enhanced_signal.get('direction', 'BUY'),
            'volume': enhanced_signal.get('volume', 0.1),
            'entry_price': enhanced_signal.get('entry_price', 0.0),
            'stop_loss': enhanced_signal.get('stop_loss', 0.0),
            'take_profit': enhanced_signal.get('take_profit', 0.0),
            'tcs_score': enhanced_signal.get('tcs_score', 0.0),
            'signal_type': enhanced_signal.get('signal_type', 'UNKNOWN'),
            'risk_reward_ratio': enhanced_signal.get('risk_reward_ratio', 0.0),
            'status': mission_data.get('status', 'unknown'),
            'created_at': created_at,
            'fired_at': fired_at,
            'duration': duration,
            'execution_result': execution_result,
            'success': execution_result.get('success', False),
            'ticket': execution_result.get('ticket', None),
            'execution_price': execution_result.get('execution_price', None),
            'message': execution_result.get('message', ''),
            'user_tier': mission_data.get('user_tier', 'UNKNOWN'),
            'account_balance': mission_data.get('account_balance', 0.0)
        }
    
    def log_to_fired_trades(self, trade_data: Dict[str, Any]) -> bool:
        """Log trade to fired_trades.json"""
        try:
            # Load existing trades
            fired_trades = []
            if self.fired_trades_file.exists():
                with open(self.fired_trades_file, 'r') as f:
                    fired_trades = json.load(f)
            
            # Create new trade record
            new_trade = {
                'mission_id': trade_data['mission_id'],
                'status': trade_data['status'],
                'fired_at': trade_data['fired_at'],
                'fired_by': trade_data['user_id'],
                'symbol': trade_data['symbol'],
                'direction': trade_data['direction'],
                'entry_price': trade_data['entry_price'],
                'stop_loss': trade_data['stop_loss'],
                'take_profit': trade_data['take_profit'],
                'tcs_score': trade_data['tcs_score'],
                'signal_type': trade_data['signal_type'],
                'risk_reward_ratio': trade_data['risk_reward_ratio'],
                'volume': trade_data['volume'],
                'execution_result': trade_data['execution_result'],
                'user_tier': trade_data['user_tier'],
                'account_balance': trade_data['account_balance']
            }
            
            # Add to list
            fired_trades.append(new_trade)
            
            # Keep only last 1000 trades
            if len(fired_trades) > 1000:
                fired_trades = fired_trades[-1000:]
            
            # Save back to file
            with open(self.fired_trades_file, 'w') as f:
                json.dump(fired_trades, f, indent=2)
            
            self.pipeline_logger.info(f"✅ Trade logged to fired_trades.json: {trade_data['mission_id']}")
            return True
            
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to log to fired_trades.json: {e}")
            return False
    
    def log_to_fire_actions(self, trade_data: Dict[str, Any]) -> bool:
        """Log trade to engagement.db fire_actions table"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                # Use existing fire_actions table schema
                cursor.execute('''
                    INSERT INTO fire_actions (
                        user_id, signal_id, fired_at, action_type
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    trade_data['user_id'],
                    trade_data['mission_id'],  # Use mission_id as signal_id
                    trade_data['fired_at'],
                    'fire'
                ))
                
                conn.commit()
            
            self.pipeline_logger.info(f"✅ Trade logged to fire_actions: {trade_data['mission_id']}")
            return True
            
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to log to fire_actions: {e}")
            return False
    
    def log_to_trades_db(self, trade_data: Dict[str, Any]) -> bool:
        """Log trade to trades.db"""
        try:
            with sqlite3.connect(self.trades_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trades (
                        ticket, mission_id, user_id, symbol, direction, volume,
                        entry_price, stop_loss, take_profit, execution_price,
                        tcs_score, result, status, opened_at, closed_at, duration,
                        comment, bridge_response
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(trade_data['ticket']) if trade_data['ticket'] else None,
                    trade_data['mission_id'],
                    trade_data['user_id'],
                    trade_data['symbol'],
                    trade_data['direction'],
                    trade_data['volume'],
                    trade_data['entry_price'],
                    trade_data['stop_loss'],
                    trade_data['take_profit'],
                    trade_data['execution_price'],
                    trade_data['tcs_score'],
                    'success' if trade_data['success'] else 'failed',
                    trade_data['status'],
                    trade_data['created_at'],
                    trade_data['fired_at'],
                    trade_data['duration'],
                    f"BITTEN_{trade_data['mission_id']}",
                    json.dumps(trade_data['execution_result'])
                ))
                
                conn.commit()
            
            self.pipeline_logger.info(f"✅ Trade logged to trades.db: {trade_data['mission_id']}")
            return True
            
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to log to trades.db: {e}")
            return False
    
    def update_user_engagement(self, trade_data: Dict[str, Any]) -> bool:
        """Update user engagement statistics"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                user_id = trade_data['user_id']
                success = trade_data['success']
                
                # Get current user stats using existing schema
                cursor.execute('''
                    SELECT total_fires, total_signals_engaged, last_fire_time, streak_days
                    FROM user_engagement WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    # Update existing record
                    total_fires, total_signals_engaged, last_fire_time, streak_days = result
                    
                    total_fires += 1
                    total_signals_engaged += 1  # Track signal engagement
                    
                    cursor.execute('''
                        UPDATE user_engagement 
                        SET total_fires = ?, total_signals_engaged = ?,
                            last_fire_time = ?, updated_at = ?
                        WHERE user_id = ?
                    ''', (
                        total_fires, total_signals_engaged,
                        trade_data['fired_at'], datetime.now().isoformat(),
                        user_id
                    ))
                    
                else:
                    # Create new record using existing schema
                    cursor.execute('''
                        INSERT INTO user_engagement (
                            user_id, total_fires, total_signals_engaged,
                            last_fire_time, streak_days, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, 1, 1, trade_data['fired_at'], 0,
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                
                conn.commit()
            
            self.pipeline_logger.info(f"✅ User engagement updated for user: {user_id}")
            return True
            
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to update user engagement: {e}")
            return False
    
    def log_to_bridge_core(self, trade_data: Dict[str, Any]):
        """Log trade to bridge_core.log"""
        try:
            status = "SUCCESS" if trade_data['success'] else "FAILED"
            ticket = trade_data['ticket'] or "NO_TICKET"
            
            self.pipeline_logger.info(
                f"TRADE_EXECUTION: {status} | "
                f"Mission: {trade_data['mission_id']} | "
                f"User: {trade_data['user_id']} | "
                f"Symbol: {trade_data['symbol']} | "
                f"Direction: {trade_data['direction']} | "
                f"Volume: {trade_data['volume']} | "
                f"TCS: {trade_data['tcs_score']}% | "
                f"Ticket: {ticket} | "
                f"Duration: {trade_data['duration']}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to log to bridge_core.log: {e}")
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user engagement statistics"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM user_engagement WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
                
                return None
                
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to get user stats: {e}")
            return None
    
    def get_recent_trades(self, user_id: str = None, limit: int = 10) -> list:
        """Get recent trades from trades.db"""
        try:
            with sqlite3.connect(self.trades_db_path) as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute('''
                        SELECT * FROM trades WHERE user_id = ?
                        ORDER BY id DESC LIMIT ?
                    ''', (user_id, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM trades ORDER BY id DESC LIMIT ?
                    ''', (limit,))
                
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            self.pipeline_logger.error(f"❌ Failed to get recent trades: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of logging pipeline"""
        try:
            # Check file system
            files_exist = {
                'fired_trades.json': self.fired_trades_file.exists(),
                'engagement.db': self.engagement_db_path.exists(),
                'trades.db': self.trades_db_path.exists(),
                'bridge_core.log': self.bridge_log_path.exists()
            }
            
            # Check database connections
            db_connections = {}
            
            try:
                with sqlite3.connect(self.engagement_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM fire_actions')
                    fire_actions_count = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT COUNT(*) FROM user_engagement')
                    user_engagement_count = cursor.fetchone()[0]
                    
                    db_connections['engagement.db'] = {
                        'status': 'connected',
                        'fire_actions_count': fire_actions_count,
                        'user_engagement_count': user_engagement_count
                    }
                    
            except Exception as e:
                db_connections['engagement.db'] = {'status': 'error', 'error': str(e)}
            
            try:
                with sqlite3.connect(self.trades_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM trades')
                    trades_count = cursor.fetchone()[0]
                    
                    db_connections['trades.db'] = {
                        'status': 'connected',
                        'trades_count': trades_count
                    }
                    
            except Exception as e:
                db_connections['trades.db'] = {'status': 'error', 'error': str(e)}
            
            return {
                'status': 'healthy',
                'files': files_exist,
                'databases': db_connections,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
_trade_logger = None

def get_trade_logger() -> TradeLoggingPipeline:
    """Get global trade logger instance"""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLoggingPipeline()
    return _trade_logger

def log_trade_execution(mission_data: Dict[str, Any], execution_result: Dict[str, Any], 
                       user_id: str, mission_id: str) -> bool:
    """Convenience function for logging trade execution"""
    logger = get_trade_logger()
    return logger.log_complete_trade(mission_data, execution_result, user_id, mission_id)