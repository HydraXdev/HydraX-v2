"""
Data ingestion script for Elite Guard tracking data
Parses comprehensive_tracking.jsonl and loads into elite_guard_reports.db
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = "/root/HydraX-v2/data/elite_guard_reports.db"
TRACKING_PATHS = [
    "/root/HydraX-v2/comprehensive_tracking.jsonl",
    "/root/HydraX-v2/comprehensive_tracking.jsonl",
    "/root/HydraX-v2/comprehensive_tracking.jsonl"
]

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def parse_signal_data(signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse signal data from tracking file"""
    try:
        # Extract signal information
        signal_id = signal_data.get('signal_id', '')
        if not signal_id:
            return None
        
        # Parse timestamp
        timestamp = signal_data.get('timestamp', '')
        if not timestamp:
            # Try alternate timestamp fields
            timestamp = signal_data.get('created_at', signal_data.get('time', ''))
        
        # Determine session from timestamp or explicit field
        session = signal_data.get('session', 'UNKNOWN')
        if session == 'UNKNOWN' and timestamp:
            # Infer session from timestamp (basic logic)
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                if 7 <= hour < 16:
                    session = 'LONDON'
                elif 13 <= hour < 22:
                    session = 'NY'
                elif 22 <= hour or hour < 7:
                    session = 'TOKYO'
            except:
                session = 'UNKNOWN'
        
        return {
            'timestamp': timestamp,
            'signal_id': signal_id,
            'session': session,
            'pattern_name': signal_data.get('pattern_type', signal_data.get('pattern_name', 'UNKNOWN')),
            'pair': signal_data.get('symbol', signal_data.get('pair', '')),
            'confidence_score': signal_data.get('confidence', signal_data.get('confidence_score', 0.0)),
            'quality_score': signal_data.get('quality_score', signal_data.get('citadel_score', 0.0)),
            'thresholds_applied': signal_data.get('thresholds_applied', 'unknown'),
            'volatility_atr': signal_data.get('volatility_atr', 0.0),
            'volume_zscore': signal_data.get('volume_zscore', 0.0),
            'market_regime': signal_data.get('market_regime', 'UNKNOWN')
        }
    
    except Exception as e:
        logger.warning(f"Error parsing signal data: {e}")
        return None

def parse_trade_data(trade_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse trade data from tracking file"""
    try:
        # Extract trade information
        signal_id = trade_data.get('signal_id', '')
        if not signal_id:
            return None
        
        # Parse user_id (default to 0 if missing)
        user_id = trade_data.get('user_id', 0)
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                user_id = 0
        
        # Parse timestamp
        timestamp = trade_data.get('timestamp', '')
        if not timestamp:
            timestamp = trade_data.get('created_at', trade_data.get('time', ''))
        
        # Parse P&L values
        pl_dollars = trade_data.get('pl_dollars', trade_data.get('profit_loss_dollars', 0.0))
        pl_pips = trade_data.get('pl_pips', trade_data.get('profit_loss_pips', 0.0))
        
        # Parse win/loss status
        win_loss_status = trade_data.get('win_loss_status')
        if win_loss_status is None:
            # Infer from P&L if not explicit
            win_loss_status = pl_dollars > 0 if pl_dollars != 0 else None
        
        return {
            'signal_id': signal_id,
            'user_id': user_id,
            'timestamp': timestamp,
            'win_loss_status': win_loss_status,
            'pl_dollars': pl_dollars,
            'pl_pips': pl_pips,
            'time_to_outcome_minutes': trade_data.get('time_to_outcome_minutes', 0),
            'outcome_source': trade_data.get('outcome_source', 'tracking'),
            'sl_distance_pips': trade_data.get('sl_distance_pips', trade_data.get('stop_pips', 0.0)),
            'tp_distance_pips': trade_data.get('tp_distance_pips', trade_data.get('target_pips', 0.0)),
            'rr_ratio_realized': trade_data.get('rr_ratio_realized', 0.0),
            'rr_ratio_intended': trade_data.get('rr_ratio_intended', trade_data.get('risk_reward_ratio', 1.5)),
            'risk_percentage': trade_data.get('risk_percentage', 2.0),
            'execution_status': trade_data.get('execution_status', trade_data.get('status', 'FILLED')),
            'timeout_loss': trade_data.get('timeout_loss', False),
            'false_negative': trade_data.get('false_negative', False)
        }
    
    except Exception as e:
        logger.warning(f"Error parsing trade data: {e}")
        return None

def insert_signal(cursor: sqlite3.Cursor, signal_data: Dict[str, Any]) -> bool:
    """Insert signal into database"""
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO signals 
        (timestamp, signal_id, session, pattern_name, pair, confidence_score, quality_score, 
         thresholds_applied, volatility_atr, volume_zscore, market_regime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_data['timestamp'],
            signal_data['signal_id'],
            signal_data['session'],
            signal_data['pattern_name'],
            signal_data['pair'],
            signal_data['confidence_score'],
            signal_data['quality_score'],
            signal_data['thresholds_applied'],
            signal_data['volatility_atr'],
            signal_data['volume_zscore'],
            signal_data['market_regime']
        ))
        return True
    except Exception as e:
        logger.warning(f"Error inserting signal {signal_data.get('signal_id', 'unknown')}: {e}")
        return False

def insert_trade(cursor: sqlite3.Cursor, trade_data: Dict[str, Any]) -> bool:
    """Insert trade into database"""
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO trades 
        (signal_id, user_id, timestamp, win_loss_status, pl_dollars, pl_pips, 
         time_to_outcome_minutes, outcome_source, sl_distance_pips, tp_distance_pips,
         rr_ratio_realized, rr_ratio_intended, risk_percentage, execution_status,
         timeout_loss, false_negative)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data['signal_id'],
            trade_data['user_id'],
            trade_data['timestamp'],
            trade_data['win_loss_status'],
            trade_data['pl_dollars'],
            trade_data['pl_pips'],
            trade_data['time_to_outcome_minutes'],
            trade_data['outcome_source'],
            trade_data['sl_distance_pips'],
            trade_data['tp_distance_pips'],
            trade_data['rr_ratio_realized'],
            trade_data['rr_ratio_intended'],
            trade_data['risk_percentage'],
            trade_data['execution_status'],
            trade_data['timeout_loss'],
            trade_data['false_negative']
        ))
        return True
    except Exception as e:
        logger.warning(f"Error inserting trade for signal {trade_data.get('signal_id', 'unknown')}: {e}")
        return False

def ingest_tracking_file(file_path: str) -> Dict[str, int]:
    """Ingest data from a tracking file"""
    stats = {'signals': 0, 'trades': 0, 'errors': 0}
    
    if not Path(file_path).exists():
        logger.warning(f"Tracking file not found: {file_path}")
        return stats
    
    logger.info(f"Processing tracking file: {file_path}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Determine if this is signal or trade data
                    if 'signal_id' in data and ('pattern_type' in data or 'pattern_name' in data):
                        # This looks like signal data
                        signal_data = parse_signal_data(data)
                        if signal_data and insert_signal(cursor, signal_data):
                            stats['signals'] += 1
                    
                    # Check if this also contains trade data
                    if 'signal_id' in data and ('pl_dollars' in data or 'win_loss_status' in data):
                        # This looks like trade data
                        trade_data = parse_trade_data(data)
                        if trade_data and insert_trade(cursor, trade_data):
                            stats['trades'] += 1
                
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on line {line_num}: {e}")
                    stats['errors'] += 1
                except Exception as e:
                    logger.warning(f"Error processing line {line_num}: {e}")
                    stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        stats['errors'] += 1
    
    return stats

def create_sample_users(cursor: sqlite3.Cursor):
    """Create sample users if users table is empty"""
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.info("Creating sample users...")
            sample_users = [
                ("trader1", "2025-08-01"),
                ("trader2", "2025-08-05"),
                ("elite_user", "2025-07-15"),
                ("scalper_pro", "2025-08-10"),
                ("swing_master", "2025-07-20"),
                ("algo_bot", "2025-08-15"),
                ("risk_manager", "2025-07-25"),
                ("pattern_hunter", "2025-08-20"),
                ("momentum_trader", "2025-08-03"),
                ("gold_specialist", "2025-07-30"),
            ]
            
            for username, join_date in sample_users:
                cursor.execute("""
                INSERT OR IGNORE INTO users (username, join_date, total_trades)
                VALUES (?, ?, 0)
                """, (username, join_date))
            
            logger.info(f"Created {len(sample_users)} sample users")
    
    except Exception as e:
        logger.error(f"Error creating sample users: {e}")

def update_user_trade_counts(cursor: sqlite3.Cursor):
    """Update user trade counts based on actual trades"""
    try:
        cursor.execute("""
        UPDATE users 
        SET total_trades = (
            SELECT COUNT(*) 
            FROM trades 
            WHERE trades.user_id = users.id
        )
        WHERE id > 0
        """)
        logger.info("Updated user trade counts")
    except Exception as e:
        logger.error(f"Error updating user trade counts: {e}")

def log_system_action(cursor: sqlite3.Cursor, action_type: str, status: str = "SUCCESS", details: str = None):
    """Log system actions to the actions table"""
    try:
        cursor.execute("""
        INSERT INTO actions (timestamp, user_id, action_type, status, details)
        VALUES (datetime('now'), NULL, ?, ?, ?)
        """, (action_type, status, details))
    except Exception as e:
        logger.warning(f"Error logging system action: {e}")

def main():
    """Main ingestion function"""
    logger.info("Starting Elite Guard data ingestion...")
    
    total_stats = {'signals': 0, 'trades': 0, 'errors': 0}
    start_time = datetime.now()
    
    # Initialize database
    try:
        from database import ensure_database_exists
        if not ensure_database_exists():
            logger.error("Failed to initialize database")
            return
    except ImportError:
        logger.error("Could not import database module")
        return
    
    # Log ingestion start
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        log_system_action(cursor, "DATA_INGESTION_START", "SUCCESS", "Starting Elite Guard data ingestion process")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Error logging ingestion start: {e}")
    
    # Process each tracking file
    for file_path in TRACKING_PATHS:
        try:
            stats = ingest_tracking_file(file_path)
            total_stats['signals'] += stats['signals']
            total_stats['trades'] += stats['trades']
            total_stats['errors'] += stats['errors']
            
            logger.info(f"File {Path(file_path).name}: {stats['signals']} signals, {stats['trades']} trades, {stats['errors']} errors")
            
            # Log file processing
            if stats['signals'] > 0 or stats['trades'] > 0:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    details = f"Processed {Path(file_path).name}: {stats['signals']} signals, {stats['trades']} trades"
                    log_system_action(cursor, "DATA_FILE_PROCESSED", "SUCCESS", details)
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error logging file processing: {e}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            # Log processing error
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                details = f"Failed to process {Path(file_path).name}: {str(e)}"
                log_system_action(cursor, "DATA_FILE_PROCESSED", "ERROR", details)
                conn.commit()
                conn.close()
            except Exception as log_e:
                logger.warning(f"Error logging file processing error: {log_e}")
    
    # Create sample users if needed
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        create_sample_users(cursor)
        update_user_trade_counts(cursor)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error with user management: {e}")
    
    # Log ingestion completion
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        details = f"Completed in {duration:.1f}s: {total_stats['signals']} signals, {total_stats['trades']} trades, {total_stats['errors']} errors"
        status = "SUCCESS" if total_stats['errors'] == 0 else "WARNING"
        log_system_action(cursor, "DATA_INGESTION_COMPLETE", status, details)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Error logging ingestion completion: {e}")
    
    logger.info(f"Ingestion complete! Total: {total_stats['signals']} signals, {total_stats['trades']} trades, {total_stats['errors']} errors")

if __name__ == "__main__":
    main()