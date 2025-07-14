#!/usr/bin/env python3
"""
Database Initialization Script for HydraX v2 Engagement System
Creates tables, indexes, and sample data for the engagement system
"""

import asyncio
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'engagement.db')
DB_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'database', 'engagement_schema.sql')

class EngagementDatabaseInitializer:
    """Database initializer for engagement system"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"Created data directory: {data_dir}")
    
    def create_database_schema(self):
        """Create database schema for engagement system"""
        logger.info("Creating engagement database schema...")
        
        schema_sql = """
        -- User Login Streaks Table
        CREATE TABLE IF NOT EXISTS user_login_streaks (
            user_id TEXT PRIMARY KEY,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            total_logins INTEGER DEFAULT 0,
            streak_rewards_claimed TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Personal Records Table
        CREATE TABLE IF NOT EXISTS personal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            record_type TEXT NOT NULL,
            value REAL NOT NULL,
            achieved_at TIMESTAMP NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, record_type)
        );

        -- Daily Missions Table
        CREATE TABLE IF NOT EXISTS daily_missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            bot_id TEXT NOT NULL,
            mission_type TEXT NOT NULL,
            description TEXT NOT NULL,
            target_value INTEGER NOT NULL,
            current_progress INTEGER DEFAULT 0,
            rewards TEXT DEFAULT '[]',
            is_completed BOOLEAN DEFAULT FALSE,
            is_claimed BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Mystery Boxes Table
        CREATE TABLE IF NOT EXISTS mystery_boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            rarity TEXT NOT NULL,
            contents TEXT DEFAULT '[]',
            source TEXT NOT NULL,
            opened_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Seasonal Campaigns Table
        CREATE TABLE IF NOT EXISTS seasonal_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            milestones TEXT DEFAULT '[]',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- User Campaign Progress Table
        CREATE TABLE IF NOT EXISTS user_campaign_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            current_progress INTEGER DEFAULT 0,
            completed_milestones TEXT DEFAULT '[]',
            total_rewards_claimed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, campaign_id)
        );

        -- Engagement Events Log Table
        CREATE TABLE IF NOT EXISTS engagement_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Reward Claims Table
        CREATE TABLE IF NOT EXISTS reward_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            reward_type TEXT NOT NULL,
            reward_amount TEXT NOT NULL,
            reward_metadata TEXT DEFAULT '{}',
            source TEXT NOT NULL,
            claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_user_login_streaks_user_id ON user_login_streaks(user_id);
        CREATE INDEX IF NOT EXISTS idx_personal_records_user_id ON personal_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_personal_records_type ON personal_records(record_type);
        CREATE INDEX IF NOT EXISTS idx_daily_missions_user_id ON daily_missions(user_id);
        CREATE INDEX IF NOT EXISTS idx_daily_missions_expires ON daily_missions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_mystery_boxes_user_id ON mystery_boxes(user_id);
        CREATE INDEX IF NOT EXISTS idx_mystery_boxes_opened ON mystery_boxes(opened_at);
        CREATE INDEX IF NOT EXISTS idx_campaign_progress_user_id ON user_campaign_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_engagement_events_user_id ON engagement_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_engagement_events_type ON engagement_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_reward_claims_user_id ON reward_claims(user_id);
        CREATE INDEX IF NOT EXISTS idx_reward_claims_type ON reward_claims(reward_type);

        -- Triggers for updated_at timestamps
        CREATE TRIGGER IF NOT EXISTS update_user_login_streaks_timestamp 
            AFTER UPDATE ON user_login_streaks
            BEGIN
                UPDATE user_login_streaks SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
            END;

        CREATE TRIGGER IF NOT EXISTS update_daily_missions_timestamp 
            AFTER UPDATE ON daily_missions
            BEGIN
                UPDATE daily_missions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;

        CREATE TRIGGER IF NOT EXISTS update_campaign_progress_timestamp 
            AFTER UPDATE ON user_campaign_progress
            BEGIN
                UPDATE user_campaign_progress SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Error creating database schema: {e}")
            raise
    
    def create_sample_data(self):
        """Create sample data for testing"""
        logger.info("Creating sample data...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Sample seasonal campaign
                campaign_data = {
                    'campaign_id': 'winter_2024',
                    'name': 'Winter Warriors',
                    'description': 'Battle through the frozen lands and earn exclusive winter rewards!',
                    'start_date': (datetime.now() - timedelta(days=10)).isoformat(),
                    'end_date': (datetime.now() + timedelta(days=20)).isoformat(),
                    'milestones': json.dumps([
                        {'level': 1, 'xp_required': 100, 'rewards': [{'type': 'bits', 'amount': 100}]},
                        {'level': 2, 'xp_required': 250, 'rewards': [{'type': 'xp', 'amount': 50}]},
                        {'level': 3, 'xp_required': 500, 'rewards': [{'type': 'mystery_box', 'amount': 1}]},
                        {'level': 4, 'xp_required': 1000, 'rewards': [{'type': 'rare_item', 'amount': 1}]},
                        {'level': 5, 'xp_required': 2000, 'rewards': [{'type': 'exclusive_bot', 'amount': 1}]}
                    ]),
                    'is_active': True
                }
                
                cursor.execute("""
                    INSERT OR REPLACE INTO seasonal_campaigns 
                    (campaign_id, name, description, start_date, end_date, milestones, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign_data['campaign_id'],
                    campaign_data['name'],
                    campaign_data['description'],
                    campaign_data['start_date'],
                    campaign_data['end_date'],
                    campaign_data['milestones'],
                    campaign_data['is_active']
                ))
                
                # Sample test user data
                test_users = [
                    'test_user_1',
                    'test_user_2',
                    'test_user_3'
                ]
                
                for user_id in test_users:
                    # Login streak
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_login_streaks 
                        (user_id, current_streak, longest_streak, last_login, total_logins, streak_rewards_claimed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, 1, 1, datetime.now().isoformat(), 1, '[]'))
                    
                    # Personal record
                    cursor.execute("""
                        INSERT OR REPLACE INTO personal_records 
                        (user_id, record_type, value, achieved_at, details)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, 'highest_damage_dealt', 1000.0, datetime.now().isoformat(), '{}'))
                    
                    # Campaign progress
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_campaign_progress 
                        (user_id, campaign_id, current_progress, completed_milestones, total_rewards_claimed)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, 'winter_2024', 0, '[]', 0))
                
                conn.commit()
                logger.info(f"Sample data created for {len(test_users)} test users")
                
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            raise
    
    def verify_database(self):
        """Verify database was created properly"""
        logger.info("Verifying database structure...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = [
                    'user_login_streaks',
                    'personal_records',
                    'daily_missions',
                    'mystery_boxes',
                    'seasonal_campaigns',
                    'user_campaign_progress',
                    'engagement_events',
                    'reward_claims'
                ]
                
                for table in expected_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        logger.info(f"✓ Table {table}: {count} rows")
                    else:
                        logger.error(f"✗ Table {table}: NOT FOUND")
                
                # Check indexes
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                indexes = [row[0] for row in cursor.fetchall()]
                logger.info(f"✓ Created {len(indexes)} indexes")
                
                # Check triggers
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='trigger'
                """)
                triggers = [row[0] for row in cursor.fetchall()]
                logger.info(f"✓ Created {len(triggers)} triggers")
                
                logger.info("Database verification completed successfully")
                
        except Exception as e:
            logger.error(f"Error verifying database: {e}")
            raise
    
    def run_maintenance_tasks(self):
        """Run database maintenance tasks"""
        logger.info("Running database maintenance tasks...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up expired missions
                cursor.execute("""
                    DELETE FROM daily_missions 
                    WHERE expires_at < datetime('now') AND is_completed = FALSE
                """)
                expired_missions = cursor.rowcount
                
                # Clean up old engagement events (keep last 30 days)
                cursor.execute("""
                    DELETE FROM engagement_events 
                    WHERE timestamp < datetime('now', '-30 days')
                """)
                old_events = cursor.rowcount
                
                conn.commit()
                
                # Vacuum database (must be done outside transaction)
                conn.execute("VACUUM")
                logger.info(f"Maintenance completed: removed {expired_missions} expired missions, {old_events} old events")
                
        except Exception as e:
            logger.error(f"Error running maintenance tasks: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Table row counts
                tables = [
                    'user_login_streaks',
                    'personal_records', 
                    'daily_missions',
                    'mystery_boxes',
                    'seasonal_campaigns',
                    'user_campaign_progress',
                    'engagement_events',
                    'reward_claims'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database size
                cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                # Active campaigns
                cursor.execute("SELECT COUNT(*) FROM seasonal_campaigns WHERE is_active = TRUE")
                stats['active_campaigns'] = cursor.fetchone()[0]
                
                # Total users with engagement data
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_login_streaks")
                stats['total_users'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


async def main():
    """Main initialization function"""
    logger.info("Starting HydraX v2 Engagement Database Initialization")
    
    try:
        # Initialize database
        db_init = EngagementDatabaseInitializer()
        
        # Create schema
        db_init.create_database_schema()
        
        # Create sample data
        db_init.create_sample_data()
        
        # Verify database
        db_init.verify_database()
        
        # Run maintenance
        db_init.run_maintenance_tasks()
        
        # Get stats
        stats = db_init.get_database_stats()
        logger.info("Database Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("✅ Engagement database initialization completed successfully!")
        
        # Test basic operations
        logger.info("Testing basic database operations...")
        
        with sqlite3.connect(db_init.db_path) as conn:
            cursor = conn.cursor()
            
            # Test login streak query
            cursor.execute("SELECT user_id, current_streak FROM user_login_streaks LIMIT 3")
            streaks = cursor.fetchall()
            logger.info(f"Sample login streaks: {streaks}")
            
            # Test campaign query
            cursor.execute("SELECT campaign_id, name FROM seasonal_campaigns WHERE is_active = TRUE")
            campaigns = cursor.fetchall()
            logger.info(f"Active campaigns: {campaigns}")
        
        logger.info("✅ Database operations test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    # Run the initialization
    asyncio.run(main())