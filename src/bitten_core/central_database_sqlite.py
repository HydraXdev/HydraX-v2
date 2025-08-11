#!/usr/bin/env python3
"""
BITTEN Central User Database - SQLite Implementation
Single source of truth for all user data
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any

class CentralDatabase:
    """Central database for all user data using SQLite"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/bitten_central.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all tables in the central database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Core Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                user_uuid TEXT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                tier TEXT NOT NULL DEFAULT 'NIBBLER',
                subscription_status TEXT DEFAULT 'INACTIVE',
                subscription_expires_at TIMESTAMP,
                stripe_customer_id TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_banned BOOLEAN DEFAULT 0,
                ban_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User Profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                telegram_id INTEGER PRIMARY KEY,
                callsign TEXT,
                bio TEXT,
                timezone TEXT DEFAULT 'UTC',
                risk_percentage REAL DEFAULT 2.0,
                daily_tactic TEXT DEFAULT 'LONE_WOLF',
                account_currency TEXT DEFAULT 'USD',
                notification_settings TEXT DEFAULT '{}',
                trading_preferences TEXT DEFAULT '{}',
                ui_theme TEXT DEFAULT 'dark',
                language_code TEXT DEFAULT 'en',
                profile_image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # MT5 Trading Accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_mt5_accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                account_number INTEGER NOT NULL,
                broker TEXT NOT NULL,
                server TEXT NOT NULL,
                balance REAL DEFAULT 0.00,
                equity REAL DEFAULT 0.00,
                margin REAL DEFAULT 0.00,
                free_margin REAL DEFAULT 0.00,
                leverage INTEGER DEFAULT 100,
                currency TEXT DEFAULT 'USD',
                account_type TEXT DEFAULT 'DEMO',
                is_primary BOOLEAN DEFAULT 0,
                last_sync_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                UNIQUE(telegram_id, account_number)
            )
        ''')
        
        # Fire Mode Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_fire_modes (
                telegram_id INTEGER PRIMARY KEY,
                current_mode TEXT DEFAULT 'manual',
                max_slots INTEGER DEFAULT 1,
                slots_in_use INTEGER DEFAULT 0,
                auto_fire_tcs_threshold INTEGER DEFAULT 75,
                chaingun_count INTEGER DEFAULT 0,
                last_mode_change TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # XP and Level System
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_xp (
                telegram_id INTEGER PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                daily_xp INTEGER DEFAULT 0,
                weekly_xp INTEGER DEFAULT 0,
                monthly_xp INTEGER DEFAULT 0,
                last_daily_reset DATE,
                last_weekly_reset DATE,
                last_monthly_reset DATE,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                prestige_level INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # Achievements System
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                achievement_code TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress TEXT DEFAULT '{}',
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                UNIQUE(telegram_id, achievement_code)
            )
        ''')
        
        # Referral System
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_referrals (
                telegram_id INTEGER PRIMARY KEY,
                personal_referral_code TEXT UNIQUE NOT NULL,
                referred_by_code TEXT,
                referred_by_user INTEGER,
                referral_count INTEGER DEFAULT 0,
                active_referral_count INTEGER DEFAULT 0,
                total_credits_earned REAL DEFAULT 0.00,
                pending_credits REAL DEFAULT 0.00,
                applied_credits REAL DEFAULT 0.00,
                lifetime_commission REAL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (referred_by_user) REFERENCES users(telegram_id)
            )
        ''')
        
        # Trading Statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_trading_stats (
                telegram_id INTEGER PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.00,
                total_pnl REAL DEFAULT 0.00,
                best_trade REAL DEFAULT 0.00,
                worst_trade REAL DEFAULT 0.00,
                average_win REAL DEFAULT 0.00,
                average_loss REAL DEFAULT 0.00,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                worst_streak INTEGER DEFAULT 0,
                last_trade_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # Trading Guardrails
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_trading_guardrails (
                telegram_id INTEGER PRIMARY KEY,
                max_daily_loss REAL DEFAULT 0.06,
                max_daily_trades INTEGER DEFAULT 6,
                daily_trades_used INTEGER DEFAULT 0,
                daily_loss_amount REAL DEFAULT 0.00,
                daily_starting_balance REAL,
                last_daily_reset DATE DEFAULT CURRENT_DATE,
                max_concurrent_trades INTEGER DEFAULT 3,
                current_open_trades INTEGER DEFAULT 0,
                risk_per_trade REAL DEFAULT 0.02,
                consecutive_losses INTEGER DEFAULT 0,
                cooldown_until TIMESTAMP,
                emergency_stop_active BOOLEAN DEFAULT 0,
                emergency_stop_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # Active Trading Slots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_trading_slots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                mission_id TEXT NOT NULL,
                signal_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                lot_size REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                status TEXT DEFAULT 'OPEN',
                pnl REAL,
                close_reason TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mt5_telegram ON user_mt5_accounts(telegram_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_telegram ON active_trading_slots(telegram_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_status ON active_trading_slots(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_telegram ON user_audit_log(telegram_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON user_audit_log(action)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Central database initialized at {self.db_path}")
    
    def create_user(self, telegram_id: int, user_data: Dict) -> bool:
        """Create a new user with all related records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Insert into users table
            cursor.execute('''
                INSERT INTO users (telegram_id, user_uuid, username, tier, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                user_data.get('user_uuid', f'USER_{telegram_id}'),
                user_data.get('username', ''),
                user_data.get('tier', 'NIBBLER'),
                datetime.now().isoformat()
            ))
            
            # Insert into user_profiles
            cursor.execute('''
                INSERT INTO user_profiles (telegram_id, created_at)
                VALUES (?, ?)
            ''', (telegram_id, datetime.now().isoformat()))
            
            # Insert into user_fire_modes
            cursor.execute('''
                INSERT INTO user_fire_modes (telegram_id, created_at)
                VALUES (?, ?)
            ''', (telegram_id, datetime.now().isoformat()))
            
            # Insert into user_xp
            cursor.execute('''
                INSERT INTO user_xp (telegram_id, created_at)
                VALUES (?, ?)
            ''', (telegram_id, datetime.now().isoformat()))
            
            # Insert into user_trading_stats
            cursor.execute('''
                INSERT INTO user_trading_stats (telegram_id, created_at)
                VALUES (?, ?)
            ''', (telegram_id, datetime.now().isoformat()))
            
            # Insert into user_trading_guardrails with tier-specific limits
            tier = user_data.get('tier', 'NIBBLER')
            limits = self.get_tier_limits(tier)
            cursor.execute('''
                INSERT INTO user_trading_guardrails 
                (telegram_id, max_daily_loss, max_daily_trades, max_concurrent_trades, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                limits['max_daily_loss'],
                limits['max_daily_trades'],
                limits['max_positions'],
                datetime.now().isoformat()
            ))
            
            # Insert into user_referrals
            cursor.execute('''
                INSERT INTO user_referrals 
                (telegram_id, personal_referral_code, created_at)
                VALUES (?, ?, ?)
            ''', (
                telegram_id,
                f"REF_{telegram_id}",  # Generate unique referral code
                datetime.now().isoformat()
            ))
            
            # Add audit log entry
            cursor.execute('''
                INSERT INTO user_audit_log 
                (telegram_id, action, entity_type, new_values, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                'CREATE_USER',
                'USER',
                json.dumps(user_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            print(f"✅ Created user {telegram_id} with all related records")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error creating user {telegram_id}: {e}")
            return False
        finally:
            conn.close()
    
    def get_tier_limits(self, tier: str) -> Dict:
        """Get tier-specific limits"""
        limits = {
            'PRESS_PASS': {
                'max_daily_loss': 0.06,
                'max_daily_trades': 3,
                'max_positions': 1
            },
            'NIBBLER': {
                'max_daily_loss': 0.06,
                'max_daily_trades': 6,
                'max_positions': 3
            },
            'FANG': {
                'max_daily_loss': 0.085,
                'max_daily_trades': 10,
                'max_positions': 6
            },
            'COMMANDER': {
                'max_daily_loss': 0.10,
                'max_daily_trades': 20,
                'max_positions': 10
            }
        }
        return limits.get(tier, limits['NIBBLER'])
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get complete user data from all tables"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get base user data
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return None
            
            result = dict(user)
            
            # Get all related data
            tables = [
                'user_profiles',
                'user_fire_modes',
                'user_xp',
                'user_trading_stats',
                'user_trading_guardrails',
                'user_referrals'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table} WHERE telegram_id = ?", (telegram_id,))
                row = cursor.fetchone()
                if row:
                    result[table.replace('user_', '')] = dict(row)
            
            # Get MT5 accounts
            cursor.execute("SELECT * FROM user_mt5_accounts WHERE telegram_id = ?", (telegram_id,))
            result['mt5_accounts'] = [dict(row) for row in cursor.fetchall()]
            
            # Get active slots
            cursor.execute('''
                SELECT * FROM active_trading_slots 
                WHERE telegram_id = ? AND status = 'OPEN'
            ''', (telegram_id,))
            result['active_slots'] = [dict(row) for row in cursor.fetchall()]
            
            # Get achievements
            cursor.execute("SELECT * FROM user_achievements WHERE telegram_id = ?", (telegram_id,))
            result['achievements'] = [dict(row) for row in cursor.fetchall()]
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting user {telegram_id}: {e}")
            return None
        finally:
            conn.close()
    
    def update_user(self, telegram_id: int, updates: Dict, table: str = 'users') -> bool:
        """Update user data in specified table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build update query
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values())
            values.append(telegram_id)
            
            query = f"UPDATE {table} SET {set_clause}, updated_at = ? WHERE telegram_id = ?"
            values.insert(-1, datetime.now().isoformat())
            
            cursor.execute(query, values)
            
            # Add audit log
            cursor.execute('''
                INSERT INTO user_audit_log 
                (telegram_id, action, entity_type, new_values, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                f'UPDATE_{table.upper()}',
                table.upper(),
                json.dumps(updates),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error updating user {telegram_id}: {e}")
            return False
        finally:
            conn.close()

# Singleton instance
_central_db = None

def get_central_database() -> CentralDatabase:
    """Get singleton instance of central database"""
    global _central_db
    if _central_db is None:
        _central_db = CentralDatabase()
    return _central_db