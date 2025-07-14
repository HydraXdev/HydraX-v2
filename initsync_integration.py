#!/usr/bin/env python3
"""
🎯 BITTEN INITSYNC INTEGRATION UTILITIES
Simplified integration layer for BITTEN InitSync Module

USAGE EXAMPLES:
- Initialize user: initsync_create_user(telegram_id, tier, platforms)
- Get session: initsync_get_session(session_id)
- Validate auth: initsync_validate_auth(session_id, token)
- Check status: initsync_get_status(telegram_id)
"""

import json
import sqlite3
import hashlib
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any

class SimpleInitSync:
    """Simplified InitSync for immediate deployment"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/simple_initsync.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize simple database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                telegram_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                bridge_id TEXT,
                account_id TEXT,
                auth_token TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                session_data TEXT
            )
        ''')
        self.conn.commit()
        
    def create_user_session(self, telegram_id: int, user_id: str, tier: str, 
                           platforms: List[str]) -> Tuple[bool, str, Optional[Dict]]:
        """Create new user session"""
        try:
            # Generate session ID and token
            session_id = f"init_{telegram_id}_{int(time.time())}"
            auth_token = hashlib.sha256(f"{telegram_id}:{session_id}:{uuid.uuid4()}".encode()).hexdigest()
            
            # Assign bridge based on tier
            bridge_id = self.assign_bridge_for_tier(tier)
            account_id = f"BITTEN_{telegram_id}_{bridge_id.replace('bridge_', '')}"
            
            # Create session data
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=24)  # 24 hour session
            
            session_data = {
                "platforms": platforms,
                "tier": tier,
                "bridge_id": bridge_id,
                "account_id": account_id,
                "risk_profile": self.get_tier_config(tier),
                "initialized_at": now.isoformat()
            }
            
            # Save to database
            self.conn.execute('''
                INSERT INTO user_sessions 
                (session_id, telegram_id, user_id, tier, bridge_id, account_id, 
                 auth_token, created_at, expires_at, session_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, telegram_id, user_id, tier, bridge_id, account_id,
                auth_token, now.isoformat(), expires_at.isoformat(), 
                json.dumps(session_data)
            ))
            self.conn.commit()
            
            return True, session_id, {
                "session_id": session_id,
                "auth_token": auth_token,
                "bridge_id": bridge_id,
                "account_id": account_id,
                "tier": tier,
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            return False, str(e), None
            
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM user_sessions WHERE session_id = ? AND status = 'active'
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Check if expired
            expires_at = datetime.fromisoformat(row[9])
            if expires_at <= datetime.now(timezone.utc):
                return None
                
            return {
                "session_id": row[0],
                "telegram_id": row[1],
                "user_id": row[2],
                "tier": row[3],
                "bridge_id": row[4],
                "account_id": row[5],
                "auth_token": row[6],
                "status": row[7],
                "created_at": row[8],
                "expires_at": row[9],
                "session_data": json.loads(row[10]) if row[10] else {}
            }
            
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
            
    def validate_auth(self, session_id: str, auth_token: str) -> bool:
        """Validate session authentication"""
        session = self.get_session(session_id)
        return session and session["auth_token"] == auth_token
        
    def get_user_by_telegram(self, telegram_id: int) -> Optional[Dict]:
        """Get active session for telegram user"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM user_sessions 
                WHERE telegram_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            ''', (telegram_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return self.get_session(row[0])  # Use session_id to get full data
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
            
    def assign_bridge_for_tier(self, tier: str) -> str:
        """Assign bridge based on user tier"""
        tier_bridge_map = {
            "press_pass": "bridge_001",
            "nibbler": "bridge_006", 
            "fang": "bridge_011",
            "commander": "bridge_016",
            "apex": "bridge_021"
        }
        return tier_bridge_map.get(tier, "bridge_001")
        
    def get_tier_config(self, tier: str) -> Dict:
        """Get configuration for user tier"""
        configs = {
            "press_pass": {
                "max_lot_size": 0.01,
                "max_daily_loss": 50.0,
                "fire_modes": ["manual"]
            },
            "nibbler": {
                "max_lot_size": 0.1,
                "max_daily_loss": 200.0,
                "fire_modes": ["manual"]
            },
            "fang": {
                "max_lot_size": 0.5,
                "max_daily_loss": 500.0,
                "fire_modes": ["manual"]
            },
            "commander": {
                "max_lot_size": 1.0,
                "max_daily_loss": 1000.0,
                "fire_modes": ["manual", "semi_auto", "full_auto"]
            },
            "apex": {
                "max_lot_size": 2.0,
                "max_daily_loss": 2000.0,
                "fire_modes": ["manual", "semi_auto", "full_auto"]
            }
        }
        return configs.get(tier, configs["press_pass"])

# Global instance
SIMPLE_INITSYNC = SimpleInitSync()

# Convenience functions
def initsync_create_user(telegram_id: int, user_id: str, tier: str, platforms: List[str]) -> Tuple[bool, str, Optional[Dict]]:
    """Create new user session"""
    return SIMPLE_INITSYNC.create_user_session(telegram_id, user_id, tier, platforms)

def initsync_get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID"""
    return SIMPLE_INITSYNC.get_session(session_id)

def initsync_validate_auth(session_id: str, auth_token: str) -> bool:
    """Validate session authentication"""
    return SIMPLE_INITSYNC.validate_auth(session_id, auth_token)

def initsync_get_user(telegram_id: int) -> Optional[Dict]:
    """Get user session by telegram ID"""
    return SIMPLE_INITSYNC.get_user_by_telegram(telegram_id)

def initsync_get_bridge(telegram_id: int) -> Optional[str]:
    """Get bridge ID for user"""
    user = initsync_get_user(telegram_id)
    return user["bridge_id"] if user else None

def initsync_get_tier(telegram_id: int) -> Optional[str]:
    """Get tier for user"""
    user = initsync_get_user(telegram_id)
    return user["tier"] if user else None

if __name__ == "__main__":
    print("🎯 INITSYNC INTEGRATION - TESTING MODE")
    print("=" * 40)
    
    # Test user creation
    success, result, session_data = initsync_create_user(
        telegram_id=123456789,
        user_id="test_user_001", 
        tier="fang",
        platforms=["telegram", "webapp"]
    )
    
    if success:
        print(f"✅ User created: {result}")
        print(f"🎯 Session data: {session_data}")
        
        # Test session retrieval
        session = initsync_get_session(result)
        print(f"📊 Retrieved session: {session['tier'] if session else 'None'}")
        
        # Test auth validation
        if session_data:
            auth_valid = initsync_validate_auth(result, session_data["auth_token"])
            print(f"🔒 Auth validation: {auth_valid}")
            
        # Test user lookup
        user = initsync_get_user(123456789)
        print(f"👤 User lookup: {user['bridge_id'] if user else 'None'}")
        
    else:
        print(f"❌ User creation failed: {result}")
    
    print("\n🔗 Available Functions:")
    print("  initsync_create_user(telegram_id, user_id, tier, platforms)")
    print("  initsync_get_session(session_id)")
    print("  initsync_validate_auth(session_id, auth_token)")
    print("  initsync_get_user(telegram_id)")
    print("  initsync_get_bridge(telegram_id)")
    print("  initsync_get_tier(telegram_id)")