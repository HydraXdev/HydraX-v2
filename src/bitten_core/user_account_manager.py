#!/usr/bin/env python3
"""
BITTEN User Account Manager
Handles MT5 account information storage and user management
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class UserAccountManager:
    """Manages user account information and MT5 account data"""
    
    def __init__(self, base_dir: str = "/root/HydraX-v2"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.engagement_db_path = self.data_dir / "engagement.db"
        self.user_accounts_json = self.data_dir / "user_accounts.json"
        
        # Initialize database
        self.init_database()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for account manager"""
        log_formatter = logging.Formatter(
            '%(asctime)s - [ACCOUNT_MGR] %(levelname)s - %(message)s'
        )
        
        # File handler
        log_file = self.base_dir / "account_manager.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(log_formatter)
        
        # Configure logger
        self.logger = logging.getLogger('account_manager')
        self.logger.setLevel(logging.INFO)
        
        # Only add handler if not already present
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
    
    def init_database(self):
        """Initialize database tables for user accounts"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                # Create user_accounts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_user_id TEXT NOT NULL,
                        mt5_account_number TEXT,
                        balance REAL,
                        equity REAL,
                        leverage INTEGER,
                        broker TEXT,
                        server TEXT,
                        currency TEXT,
                        margin_free REAL,
                        margin_level REAL,
                        account_name TEXT,
                        company TEXT,
                        trade_mode INTEGER,
                        last_updated TEXT NOT NULL,
                        created_at TEXT,
                        UNIQUE(telegram_user_id, mt5_account_number)
                    )
                ''')
                
                # Create index for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_telegram_user_id 
                    ON user_accounts(telegram_user_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_mt5_account_number 
                    ON user_accounts(mt5_account_number)
                ''')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def store_account_info(self, telegram_user_id: str, mt5_account_info: Dict[str, Any]) -> bool:
        """Store or update MT5 account information for a user"""
        try:
            if not mt5_account_info:
                self.logger.warning(f"No MT5 account info provided for user {telegram_user_id}")
                return False
            
            # Extract account data
            account_number = str(mt5_account_info.get('account_number', ''))
            balance = mt5_account_info.get('balance', 0.0)
            equity = mt5_account_info.get('equity', 0.0)
            leverage = mt5_account_info.get('leverage', 0)
            broker = mt5_account_info.get('broker', '')
            server = mt5_account_info.get('server', '')
            currency = mt5_account_info.get('currency', 'USD')
            margin_free = mt5_account_info.get('margin_free', 0.0)
            margin_level = mt5_account_info.get('margin_level', 0.0)
            account_name = mt5_account_info.get('name', '')
            company = mt5_account_info.get('company', '')
            trade_mode = mt5_account_info.get('trade_mode', 0)
            
            if not account_number:
                self.logger.warning(f"No account number provided for user {telegram_user_id}")
                return False
            
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                # Check if record exists
                cursor.execute('''
                    SELECT id FROM user_accounts 
                    WHERE telegram_user_id = ? AND mt5_account_number = ?
                ''', (telegram_user_id, account_number))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_accounts SET
                            balance = ?, equity = ?, leverage = ?, broker = ?, server = ?,
                            currency = ?, margin_free = ?, margin_level = ?, account_name = ?,
                            company = ?, trade_mode = ?, last_updated = ?
                        WHERE telegram_user_id = ? AND mt5_account_number = ?
                    ''', (
                        balance, equity, leverage, broker, server, currency,
                        margin_free, margin_level, account_name, company, trade_mode,
                        datetime.now().isoformat(), telegram_user_id, account_number
                    ))
                    
                    self.logger.info(f"✅ Updated account info for user {telegram_user_id}, account {account_number}")
                    
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_accounts (
                            telegram_user_id, mt5_account_number, balance, equity, leverage,
                            broker, server, currency, margin_free, margin_level, account_name,
                            company, trade_mode, last_updated, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        telegram_user_id, account_number, balance, equity, leverage,
                        broker, server, currency, margin_free, margin_level, account_name,
                        company, trade_mode, datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                    
                    self.logger.info(f"✅ Created new account record for user {telegram_user_id}, account {account_number}")
                
                conn.commit()
                
                # Also store in JSON for backup
                self.store_account_json(telegram_user_id, mt5_account_info)
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store account info for user {telegram_user_id}: {e}")
            return False
    
    def store_account_json(self, telegram_user_id: str, mt5_account_info: Dict[str, Any]):
        """Store account info in JSON file as backup"""
        try:
            # Load existing data
            user_accounts = {}
            if self.user_accounts_json.exists():
                with open(self.user_accounts_json, 'r') as f:
                    user_accounts = json.load(f)
            
            # Update user data
            if telegram_user_id not in user_accounts:
                user_accounts[telegram_user_id] = {
                    "accounts": [],
                    "created_at": datetime.now().isoformat()
                }
            
            account_number = str(mt5_account_info.get('account_number', ''))
            
            # Find existing account or create new one
            existing_account = None
            for account in user_accounts[telegram_user_id]["accounts"]:
                if account.get("account_number") == account_number:
                    existing_account = account
                    break
            
            if existing_account:
                # Update existing account
                existing_account.update(mt5_account_info)
                existing_account["last_updated"] = datetime.now().isoformat()
            else:
                # Add new account
                mt5_account_info["last_updated"] = datetime.now().isoformat()
                user_accounts[telegram_user_id]["accounts"].append(mt5_account_info)
            
            user_accounts[telegram_user_id]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.user_accounts_json, 'w') as f:
                json.dump(user_accounts, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store account JSON for user {telegram_user_id}: {e}")
    
    def get_user_account_info(self, telegram_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's MT5 account information"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM user_accounts 
                    WHERE telegram_user_id = ? 
                    ORDER BY last_updated DESC 
                    LIMIT 1
                ''', (telegram_user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    account_data = dict(zip(columns, result))
                    
                    self.logger.info(f"Retrieved account info for user {telegram_user_id}")
                    return account_data
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get account info for user {telegram_user_id}: {e}")
            return None
    
    def get_all_user_accounts(self, telegram_user_id: str) -> List[Dict[str, Any]]:
        """Get all MT5 accounts for a user"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM user_accounts 
                    WHERE telegram_user_id = ? 
                    ORDER BY last_updated DESC
                ''', (telegram_user_id,))
                
                results = cursor.fetchall()
                
                if results:
                    columns = [desc[0] for desc in cursor.description]
                    accounts = [dict(zip(columns, row)) for row in results]
                    
                    self.logger.info(f"Retrieved {len(accounts)} accounts for user {telegram_user_id}")
                    return accounts
                
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get all accounts for user {telegram_user_id}: {e}")
            return []
    
    def update_account_balance(self, telegram_user_id: str, account_number: str, 
                             new_balance: float, new_equity: float) -> bool:
        """Update account balance and equity"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_accounts 
                    SET balance = ?, equity = ?, last_updated = ?
                    WHERE telegram_user_id = ? AND mt5_account_number = ?
                ''', (new_balance, new_equity, datetime.now().isoformat(), 
                      telegram_user_id, str(account_number)))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"✅ Updated balance for user {telegram_user_id}, account {account_number}")
                    return True
                else:
                    self.logger.warning(f"No account found to update for user {telegram_user_id}, account {account_number}")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update balance for user {telegram_user_id}: {e}")
            return False
    
    def process_bridge_response(self, telegram_user_id: str, bridge_response: Dict[str, Any]) -> bool:
        """Process bridge response and store account info"""
        try:
            # Extract account info from bridge response
            account_info = bridge_response.get('account_info')
            
            if not account_info:
                self.logger.warning(f"No account_info in bridge response for user {telegram_user_id}")
                return False
            
            # Store the account information
            success = self.store_account_info(telegram_user_id, account_info)
            
            if success:
                self.logger.info(f"✅ Processed bridge response for user {telegram_user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process bridge response for user {telegram_user_id}: {e}")
            return False
    
    def get_account_stats(self) -> Dict[str, Any]:
        """Get account statistics"""
        try:
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                
                # Get total number of users
                cursor.execute('SELECT COUNT(DISTINCT telegram_user_id) FROM user_accounts')
                total_users = cursor.fetchone()[0]
                
                # Get total number of accounts
                cursor.execute('SELECT COUNT(*) FROM user_accounts')
                total_accounts = cursor.fetchone()[0]
                
                # Get brokers breakdown
                cursor.execute('''
                    SELECT broker, COUNT(*) as count 
                    FROM user_accounts 
                    GROUP BY broker 
                    ORDER BY count DESC
                ''')
                brokers = dict(cursor.fetchall())
                
                # Get recent activity
                cursor.execute('''
                    SELECT COUNT(*) FROM user_accounts 
                    WHERE last_updated > datetime('now', '-24 hours')
                ''')
                recent_activity = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'total_accounts': total_accounts,
                    'brokers': brokers,
                    'recent_activity_24h': recent_activity,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get account stats: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of account manager"""
        try:
            # Check database connection
            with sqlite3.connect(self.engagement_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM user_accounts')
                account_count = cursor.fetchone()[0]
            
            # Check JSON file
            json_exists = self.user_accounts_json.exists()
            
            return {
                'status': 'healthy',
                'database_connection': 'connected',
                'account_count': account_count,
                'json_backup_exists': json_exists,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
_account_manager = None

def get_account_manager() -> UserAccountManager:
    """Get global account manager instance"""
    global _account_manager
    if _account_manager is None:
        _account_manager = UserAccountManager()
    return _account_manager

def store_user_account_info(telegram_user_id: str, mt5_account_info: Dict[str, Any]) -> bool:
    """Convenience function for storing account info"""
    manager = get_account_manager()
    return manager.store_account_info(telegram_user_id, mt5_account_info)

def process_bridge_account_info(telegram_user_id: str, bridge_response: Dict[str, Any]) -> bool:
    """Convenience function for processing bridge responses"""
    manager = get_account_manager()
    return manager.process_bridge_response(telegram_user_id, bridge_response)