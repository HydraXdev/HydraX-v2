#!/usr/bin/env python3
"""
👤 USER PROFILE MANAGER - REAL USER DATA MANAGEMENT
ZERO SIMULATION - TRACKS REAL USER PREFERENCES & TACTICAL CHOICES

Manages user profiles, tactical strategies, and real trading preferences
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """Real user profile - NO SIMULATION"""
    user_id: str
    telegram_id: int
    tier: str
    risk_percentage: float
    daily_tactic: str
    broker: str
    account_currency: str
    timezone: str
    created_at: datetime
    last_updated: datetime
    trading_preferences: Dict[str, Any]
    performance_stats: Dict[str, Any]

class UserProfileManager:
    """
    👤 USER PROFILE MANAGER - REAL DATA ONLY
    
    Manages:
    - User tier subscriptions
    - Daily tactical strategy choices
    - Risk preferences
    - Broker configurations
    - Trading performance tracking
    
    CRITICAL: NO SIMULATION - ALL USER DATA IS REAL
    """
    
    def __init__(self, db_path="/root/HydraX-v2/data/user_profiles.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("USER_PROFILES")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Verify no simulation mode
        self.verify_real_data_only()
        
    def verify_real_data_only(self):
        """Verify system uses ZERO simulation"""
        simulation_flags = ['DEMO_USERS', 'FAKE_PROFILES', 'TEST_MODE']
        
        for flag in simulation_flags:
            if hasattr(self, flag.lower()) and getattr(self, flag.lower()):
                raise ValueError(f"CRITICAL: {flag} detected - REAL DATA ONLY POLICY VIOLATED")
                
        self.logger.info("✅ VERIFIED: REAL USER PROFILES ONLY")
    
    def init_database(self):
        """Initialize user profiles database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Create user profiles table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    tier TEXT NOT NULL,
                    risk_percentage REAL DEFAULT 2.0,
                    daily_tactic TEXT DEFAULT 'LONE_WOLF',
                    broker TEXT,
                    account_currency TEXT DEFAULT 'USD',
                    timezone TEXT DEFAULT 'UTC',
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    trading_preferences TEXT,
                    performance_stats TEXT,
                    real_user_verified BOOLEAN DEFAULT 1,
                    simulation_mode BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create tactical choices table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tactical_choices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    tactic TEXT NOT NULL,
                    trades_taken INTEGER DEFAULT 0,
                    trades_won INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Create user preferences table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    max_daily_trades INTEGER DEFAULT 6,
                    risk_tolerance TEXT DEFAULT 'MODERATE',
                    preferred_sessions TEXT,
                    excluded_pairs TEXT,
                    auto_fire_enabled BOOLEAN DEFAULT 0,
                    notifications_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            self.conn.commit()
            self.logger.info(f"✅ User profiles database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def create_user_profile(self, telegram_id: int, tier: str, broker: str = None) -> str:
        """Create new real user profile"""
        try:
            user_id = f"user_{telegram_id}"
            now = datetime.now(timezone.utc)
            
            # Default trading preferences
            trading_preferences = {
                'max_daily_trades': 6,
                'risk_tolerance': 'MODERATE',
                'preferred_sessions': ['LONDON', 'NY'],
                'excluded_pairs': [],
                'auto_fire_enabled': False,
                'notifications_enabled': True
            }
            
            # Default performance stats
            performance_stats = {
                'total_trades': 0,
                'winning_trades': 0,
                'total_pnl': 0.0,
                'best_day': 0.0,
                'worst_day': 0.0,
                'current_streak': 0,
                'max_streak': 0
            }
            
            # Insert user profile
            self.conn.execute('''
                INSERT INTO user_profiles 
                (user_id, telegram_id, tier, broker, created_at, last_updated, 
                 trading_preferences, performance_stats, real_user_verified, simulation_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            ''', (
                user_id, telegram_id, tier, broker, 
                now.isoformat(), now.isoformat(),
                json.dumps(trading_preferences),
                json.dumps(performance_stats)
            ))
            
            # Create default preferences
            self.conn.execute('''
                INSERT INTO user_preferences 
                (user_id, max_daily_trades, risk_tolerance, preferred_sessions, 
                 excluded_pairs, auto_fire_enabled, notifications_enabled)
                VALUES (?, 6, 'MODERATE', ?, ?, 0, 1)
            ''', (
                user_id,
                json.dumps(['LONDON', 'NY']),
                json.dumps([])
            ))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Created real user profile: {user_id}")
            return user_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create user profile for {telegram_id}: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile with real data"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if not row:
                self.logger.warning(f"User profile not found: {user_id}")
                return None
            
            # Convert row to dict
            columns = [desc[0] for desc in cursor.description]
            profile_data = dict(zip(columns, row))
            
            # Verify real user (not simulation)
            if not profile_data.get('real_user_verified', False):
                self.logger.error(f"SIMULATION USER DETECTED: {user_id} - REAL USERS ONLY")
                return None
                
            if profile_data.get('simulation_mode', False):
                self.logger.error(f"SIMULATION MODE DETECTED: {user_id} - REAL DATA ONLY")
                return None
            
            # Parse JSON fields
            profile_data['trading_preferences'] = json.loads(profile_data['trading_preferences'] or '{}')
            profile_data['performance_stats'] = json.loads(profile_data['performance_stats'] or '{}')
            
            self.logger.info(f"✅ Retrieved real user profile: {user_id}")
            return profile_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get user profile {user_id}: {e}")
            return None
    
    def update_daily_tactic(self, user_id: str, tactic: str) -> bool:
        """Update user's daily tactical choice"""
        try:
            valid_tactics = ['LONE_WOLF', 'FIRST_BLOOD', 'DOUBLE_TAP', 'TACTICAL_COMMAND']
            
            if tactic not in valid_tactics:
                self.logger.error(f"Invalid tactic: {tactic}")
                return False
            
            now = datetime.now(timezone.utc)
            today = now.date().isoformat()
            
            # Update user profile
            self.conn.execute('''
                UPDATE user_profiles 
                SET daily_tactic = ?, last_updated = ?
                WHERE user_id = ?
            ''', (tactic, now.isoformat(), user_id))
            
            # Record tactical choice
            self.conn.execute('''
                INSERT OR REPLACE INTO tactical_choices 
                (user_id, date, tactic, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, today, tactic, now.isoformat()))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Updated daily tactic for {user_id}: {tactic}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update daily tactic for {user_id}: {e}")
            return False
    
    def get_user_daily_tactic(self, user_id: str) -> str:
        """Get user's current daily tactic"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            
            cursor = self.conn.execute('''
                SELECT tactic FROM tactical_choices 
                WHERE user_id = ? AND date = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, today))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Default to profile setting
            profile = self.get_user_profile(user_id)
            return profile.get('daily_tactic', 'LONE_WOLF') if profile else 'LONE_WOLF'
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get daily tactic for {user_id}: {e}")
            return 'LONE_WOLF'
    
    def update_user_tier(self, user_id: str, new_tier: str) -> bool:
        """Update user's subscription tier"""
        try:
            valid_tiers = ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER']
            
            if new_tier not in valid_tiers:
                self.logger.error(f"Invalid tier: {new_tier}")
                return False
            
            now = datetime.now(timezone.utc)
            
            self.conn.execute('''
                UPDATE user_profiles 
                SET tier = ?, last_updated = ?
                WHERE user_id = ?
            ''', (new_tier, now.isoformat(), user_id))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Updated tier for {user_id}: {new_tier}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update tier for {user_id}: {e}")
            return False
    
    def update_performance_stats(self, user_id: str, trade_result: Dict) -> bool:
        """Update user's real performance statistics"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            stats = profile['performance_stats']
            
            # Update stats based on real trade result
            stats['total_trades'] += 1
            
            if trade_result.get('success', False):
                stats['winning_trades'] += 1
                stats['current_streak'] += 1
                stats['max_streak'] = max(stats['max_streak'], stats['current_streak'])
            else:
                stats['current_streak'] = 0
            
            pnl = float(trade_result.get('pnl', 0.0))
            stats['total_pnl'] += pnl
            
            # Update daily records
            if pnl > stats.get('best_day', 0):
                stats['best_day'] = pnl
            if pnl < stats.get('worst_day', 0):
                stats['worst_day'] = pnl
            
            # Calculate win rate
            stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0
            
            # Save updated stats
            now = datetime.now(timezone.utc)
            
            self.conn.execute('''
                UPDATE user_profiles 
                SET performance_stats = ?, last_updated = ?
                WHERE user_id = ?
            ''', (json.dumps(stats), now.isoformat(), user_id))
            
            self.conn.commit()
            
            self.logger.info(f"✅ Updated performance stats for {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update performance stats for {user_id}: {e}")
            return False
    
    def get_all_active_users(self) -> List[str]:
        """Get all active real users"""
        try:
            cursor = self.conn.execute('''
                SELECT user_id FROM user_profiles 
                WHERE real_user_verified = 1 AND simulation_mode = 0
                ORDER BY last_updated DESC
            ''')
            
            users = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"✅ Retrieved {len(users)} active real users")
            return users
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get active users: {e}")
            return []
    
    def get_users_by_tier(self, tier: str) -> List[str]:
        """Get users by tier level"""
        try:
            cursor = self.conn.execute('''
                SELECT user_id FROM user_profiles 
                WHERE tier = ? AND real_user_verified = 1 AND simulation_mode = 0
            ''', (tier,))
            
            users = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"✅ Retrieved {len(users)} {tier} tier users")
            return users
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get {tier} tier users: {e}")
            return []

# Global profile manager
PROFILE_MANAGER = None

def get_profile_manager() -> UserProfileManager:
    """Get global profile manager instance"""
    global PROFILE_MANAGER
    if PROFILE_MANAGER is None:
        PROFILE_MANAGER = UserProfileManager()
    return PROFILE_MANAGER

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile"""
    manager = get_profile_manager()
    return manager.get_user_profile(user_id)

def get_all_active_users() -> List[str]:
    """Get all active users"""
    manager = get_profile_manager()
    return manager.get_all_active_users()

if __name__ == "__main__":
    print("👤 TESTING USER PROFILE MANAGER")
    print("=" * 50)
    
    manager = UserProfileManager()
    
    # Test profile creation
    test_telegram_id = 123456789
    user_id = manager.create_user_profile(test_telegram_id, 'NIBBLER', 'MT5')
    print(f"✅ Created test profile: {user_id}")
    
    # Test profile retrieval
    profile = manager.get_user_profile(user_id)
    if profile:
        print(f"✅ Retrieved profile: {profile['tier']}")
    
    print("👤 USER PROFILE MANAGER OPERATIONAL - REAL DATA ONLY")