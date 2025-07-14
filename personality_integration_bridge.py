#!/usr/bin/env python3
"""
PERSONALITY INTEGRATION BRIDGE
Connects existing BITTEN systems to new personality bot
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class PersonalityIntegrationBridge:
    """
    Bridge between existing BITTEN systems and new personality bot
    """
    
    def __init__(self, data_path: str = "/root/HydraX-v2/bitten/data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Database for personality bot data
        self.bot_db_path = self.data_path / "personality_bot.db"
        self.setup_database()
        
        # Load existing systems
        self.load_existing_systems()
        
        logging.info("Personality Integration Bridge initialized")
    
    def setup_database(self):
        """Setup database for personality bot data"""
        with sqlite3.connect(self.bot_db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    persona_type TEXT DEFAULT 'DEFAULT',
                    xp_total INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS xp_awards (
                    award_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT,
                    xp_amount INTEGER,
                    persona_type TEXT,
                    multiplier REAL DEFAULT 1.0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS behavior_tracking (
                    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    interaction_type TEXT,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS persona_evolutions (
                    evolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    old_persona TEXT,
                    new_persona TEXT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    chat_id INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def load_existing_systems(self):
        """Load connections to existing BITTEN systems"""
        try:
            # Try to connect to existing XP system
            self.existing_xp_db = "/root/HydraX-v2/bitten/data/xp_system.db"
            
            # Try to connect to existing persona data
            self.existing_persona_file = "/root/HydraX-v2/bitten/data/user_persona.json"
            
            # Load existing user data if available
            self.sync_existing_data()
            
        except Exception as e:
            logging.warning(f"Could not load existing systems: {e}")
    
    def sync_existing_data(self):
        """Sync data from existing BITTEN systems"""
        try:
            # Sync persona data if available
            if Path(self.existing_persona_file).exists():
                with open(self.existing_persona_file, 'r') as f:
                    persona_data = json.load(f)
                    
                with sqlite3.connect(self.bot_db_path) as conn:
                    for user_id, persona in persona_data.get('user_personas', {}).items():
                        conn.execute("""
                            INSERT OR REPLACE INTO user_profiles (user_id, persona_type)
                            VALUES (?, ?)
                        """, (user_id, persona))
                
                logging.info(f"Synced {len(persona_data.get('user_personas', {}))} personas")
            
            # Sync XP data if available
            if Path(self.existing_xp_db).exists():
                with sqlite3.connect(self.existing_xp_db) as existing_conn:
                    cursor = existing_conn.execute("SELECT user_id, total_xp, level FROM user_xp")
                    xp_data = cursor.fetchall()
                
                with sqlite3.connect(self.bot_db_path) as conn:
                    for user_id, total_xp, level in xp_data:
                        conn.execute("""
                            UPDATE user_profiles 
                            SET xp_total = ?, level = ?
                            WHERE user_id = ?
                        """, (total_xp, level, user_id))
                
                logging.info(f"Synced XP data for {len(xp_data)} users")
                
        except Exception as e:
            logging.error(f"Error syncing existing data: {e}")
    
    def create_user_profile(self, user_id: str, username: str, persona: str):
        """Create new user profile"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_profiles 
                    (user_id, username, persona_type, xp_total, level)
                    VALUES (?, ?, ?, 0, 1)
                """, (user_id, username, persona))
            
            logging.info(f"Created profile for user {user_id} with persona {persona}")
            return True
            
        except Exception as e:
            logging.error(f"Error creating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, username, persona_type, xp_total, level, created_at, last_active
                    FROM user_profiles WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'user_id': result[0],
                        'username': result[1],
                        'persona_type': result[2],
                        'xp_total': result[3],
                        'level': result[4],
                        'created_at': result[5],
                        'last_active': result[6]
                    }
                return None
                
        except Exception as e:
            logging.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_persona(self, user_id: str, new_persona: str):
        """Update user's persona"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                # Update persona
                conn.execute("""
                    UPDATE user_profiles 
                    SET persona_type = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_persona, user_id))
            
            # Update existing persona file if it exists
            if Path(self.existing_persona_file).exists():
                try:
                    with open(self.existing_persona_file, 'r') as f:
                        persona_data = json.load(f)
                    
                    persona_data.setdefault('user_personas', {})[user_id] = new_persona
                    
                    with open(self.existing_persona_file, 'w') as f:
                        json.dump(persona_data, f, indent=2)
                        
                except Exception as e:
                    logging.warning(f"Could not update existing persona file: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating user persona: {e}")
            return False
    
    def award_xp(self, user_id: str, action: str, xp_amount: int, persona: str, multiplier: float = 1.0):
        """Award XP to user"""
        try:
            final_xp = int(xp_amount * multiplier)
            
            with sqlite3.connect(self.bot_db_path) as conn:
                # Record XP award
                conn.execute("""
                    INSERT INTO xp_awards (user_id, action, xp_amount, persona_type, multiplier)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, action, final_xp, persona, multiplier))
                
                # Update total XP
                conn.execute("""
                    UPDATE user_profiles 
                    SET xp_total = xp_total + ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (final_xp, user_id))
                
                # Check for level up
                cursor = conn.execute("SELECT xp_total FROM user_profiles WHERE user_id = ?", (user_id,))
                current_xp = cursor.fetchone()[0]
                
                new_level = self.calculate_level(current_xp)
                
                # Update level if changed
                conn.execute("""
                    UPDATE user_profiles SET level = ? WHERE user_id = ?
                """, (new_level, user_id))
            
            # Sync with existing XP system if available
            self.sync_xp_to_existing_system(user_id, final_xp)
            
            return new_level
            
        except Exception as e:
            logging.error(f"Error awarding XP: {e}")
            return None
    
    def calculate_level(self, total_xp: int) -> int:
        """Calculate level based on total XP"""
        # Simple level calculation (100 XP per level)
        return max(1, total_xp // 100 + 1)
    
    def sync_xp_to_existing_system(self, user_id: str, xp_amount: int):
        """Sync XP award to existing BITTEN XP system"""
        try:
            if Path(self.existing_xp_db).exists():
                with sqlite3.connect(self.existing_xp_db) as conn:
                    # Update existing XP system
                    conn.execute("""
                        INSERT OR IGNORE INTO user_xp (user_id, total_xp, level)
                        VALUES (?, 0, 1)
                    """, (user_id,))
                    
                    conn.execute("""
                        UPDATE user_xp 
                        SET total_xp = total_xp + ?, last_updated = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (xp_amount, user_id))
                    
        except Exception as e:
            logging.warning(f"Could not sync to existing XP system: {e}")
    
    def track_behavior(self, user_id: str, interaction_type: str, data: Dict):
        """Track user behavior for persona evolution"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                conn.execute("""
                    INSERT INTO behavior_tracking (user_id, interaction_type, data)
                    VALUES (?, ?, ?)
                """, (user_id, interaction_type, json.dumps(data)))
            
        except Exception as e:
            logging.error(f"Error tracking behavior: {e}")
    
    def get_recent_behavior(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get recent behavior data for user"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                cursor = conn.execute("""
                    SELECT interaction_type, data, timestamp
                    FROM behavior_tracking 
                    WHERE user_id = ? AND timestamp > datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(days), (user_id,))
                
                results = cursor.fetchall()
                
                return [
                    {
                        'interaction_type': row[0],
                        'data': json.loads(row[1]),
                        'timestamp': row[2]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logging.error(f"Error getting recent behavior: {e}")
            return []
    
    def log_persona_evolution(self, user_id: str, old_persona: str, new_persona: str, reason: str):
        """Log persona evolution event"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                conn.execute("""
                    INSERT INTO persona_evolutions (user_id, old_persona, new_persona, reason)
                    VALUES (?, ?, ?, ?)
                """, (user_id, old_persona, new_persona, reason))
            
        except Exception as e:
            logging.error(f"Error logging persona evolution: {e}")
    
    def register_chat_session(self, user_id: str, chat_id: int):
        """Register chat session for user"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO chat_sessions (user_id, chat_id)
                    VALUES (?, ?)
                """, (user_id, chat_id))
            
        except Exception as e:
            logging.error(f"Error registering chat session: {e}")
    
    def get_user_stats(self) -> Dict:
        """Get overall user statistics"""
        try:
            with sqlite3.connect(self.bot_db_path) as conn:
                # Total users
                cursor = conn.execute("SELECT COUNT(*) FROM user_profiles")
                total_users = cursor.fetchone()[0]
                
                # Users by persona
                cursor = conn.execute("""
                    SELECT persona_type, COUNT(*) 
                    FROM user_profiles 
                    GROUP BY persona_type
                """)
                persona_distribution = dict(cursor.fetchall())
                
                # Recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM user_profiles 
                    WHERE last_active > datetime('now', '-7 days')
                """)
                active_users = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'active_users_7d': active_users,
                    'persona_distribution': persona_distribution
                }
                
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return {}

# Integration helper functions
def create_personality_bridge():
    """Create and return personality integration bridge"""
    return PersonalityIntegrationBridge()

def migrate_existing_data():
    """Migrate existing BITTEN data to personality system"""
    bridge = PersonalityIntegrationBridge()
    bridge.sync_existing_data()
    return bridge

if __name__ == "__main__":
    # Test the integration bridge
    logging.basicConfig(level=logging.INFO)
    
    bridge = create_personality_bridge()
    stats = bridge.get_user_stats()
    
    print("🔗 Personality Integration Bridge Stats:")
    print(f"Total Users: {stats.get('total_users', 0)}")
    print(f"Active Users (7d): {stats.get('active_users_7d', 0)}")
    print(f"Persona Distribution: {stats.get('persona_distribution', {})}")