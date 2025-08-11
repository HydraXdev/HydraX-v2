#!/usr/bin/env python3
"""
BITTEN Data Migration Script
Migrates all scattered user data to central database
"""

import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DataMigrator:
    """Migrates all user data to central database"""
    
    def __init__(self):
        self.base_path = Path("/root/HydraX-v2")
        self.data_path = self.base_path / "data"
        
        # Import central database
        from central_database_sqlite import get_central_database
        self.central_db = get_central_database()
        
        self.conflicts = []
        self.migrated_users = set()
        self.stats = {
            'total_users': 0,
            'migrated': 0,
            'conflicts': 0,
            'errors': 0
        }
    
    def load_json_file(self, filename: str) -> Dict:
        """Load JSON file safely"""
        filepath = self.base_path / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        return {}
    
    def load_sqlite_table(self, db_file: str, table: str) -> List[Dict]:
        """Load data from SQLite table"""
        db_path = self.data_path / db_file
        if not db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table}")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error loading {db_file}/{table}: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def migrate_user_registry(self):
        """Migrate user_registry.json"""
        logger.info("Migrating user_registry.json...")
        
        # Load both original and fixed versions
        registry = self.load_json_file("user_registry.json")
        fixed_registry = self.load_json_file("user_registry_fixed.json")
        
        # Prefer fixed registry if it exists
        if fixed_registry:
            registry = fixed_registry
        
        # Process users
        users_data = registry.get('users', {})
        
        for telegram_id_str, user_data in users_data.items():
            telegram_id = int(telegram_id_str)
            
            # Create user in central database
            user_info = {
                'user_uuid': user_data.get('user_uuid', f'USER_{telegram_id}'),
                'username': user_data.get('username', ''),
                'tier': user_data.get('tier', 'NIBBLER'),
                'account_balance': user_data.get('account_balance', 0),
                'account_currency': user_data.get('account_currency', 'USD'),
                'broker': user_data.get('broker', ''),
                'mt5_account': user_data.get('mt5_account', ''),
            }
            
            if self.central_db.create_user(telegram_id, user_info):
                self.migrated_users.add(telegram_id)
                self.stats['migrated'] += 1
                logger.info(f"✅ Migrated user {telegram_id} from registry")
            else:
                self.stats['errors'] += 1
    
    def migrate_user_profiles(self):
        """Migrate user_profiles.db"""
        logger.info("Migrating user_profiles.db...")
        
        profiles = self.load_sqlite_table("user_profiles.db", "user_profiles")
        
        for profile in profiles:
            telegram_id = profile.get('telegram_id')
            if not telegram_id:
                continue
            
            # If user doesn't exist, create them first
            if telegram_id not in self.migrated_users:
                user_data = {
                    'user_uuid': f'USER_{telegram_id}',
                    'tier': profile.get('tier', 'NIBBLER')
                }
                if self.central_db.create_user(telegram_id, user_data):
                    self.migrated_users.add(telegram_id)
            
            # Update profile data
            profile_updates = {
                'callsign': profile.get('callsign', ''),
                'bio': profile.get('bio', ''),
                'timezone': profile.get('timezone', 'UTC'),
                'risk_percentage': profile.get('risk_percentage', 2.0),
                'daily_tactic': profile.get('daily_tactic', 'LONE_WOLF')
            }
            
            if self.central_db.update_user(telegram_id, profile_updates, 'user_profiles'):
                logger.info(f"✅ Updated profile for user {telegram_id}")
            else:
                self.stats['errors'] += 1
    
    def migrate_fire_modes(self):
        """Migrate fire_modes.db"""
        logger.info("Migrating fire_modes.db...")
        
        fire_modes = self.load_sqlite_table("fire_modes.db", "user_fire_modes")
        
        for mode_data in fire_modes:
            telegram_id = mode_data.get('user_id')
            if not telegram_id:
                continue
            
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid telegram_id: {telegram_id}")
                continue
            
            # Ensure user exists
            if telegram_id not in self.migrated_users:
                if not self.central_db.create_user(telegram_id, {'tier': 'NIBBLER'}):
                    continue
                self.migrated_users.add(telegram_id)
            
            # Update fire mode settings
            mode_updates = {
                'current_mode': mode_data.get('current_mode', 'manual'),
                'max_slots': mode_data.get('max_slots', 1),
                'slots_in_use': mode_data.get('slots_in_use', 0)
            }
            
            if self.central_db.update_user(telegram_id, mode_updates, 'user_fire_modes'):
                logger.info(f"✅ Updated fire mode for user {telegram_id}")
    
    def migrate_xp_data(self):
        """Migrate bitten_xp.db"""
        logger.info("Migrating bitten_xp.db...")
        
        xp_data = self.load_sqlite_table("bitten_xp.db", "xp_balances")
        
        for xp_record in xp_data:
            telegram_id = xp_record.get('user_id')
            if not telegram_id:
                continue
            
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid telegram_id: {telegram_id}")
                continue
            
            # Ensure user exists
            if telegram_id not in self.migrated_users:
                if not self.central_db.create_user(telegram_id, {'tier': 'NIBBLER'}):
                    continue
                self.migrated_users.add(telegram_id)
            
            # Update XP data
            xp_updates = {
                'total_xp': xp_record.get('total_xp', 0),
                'current_level': xp_record.get('level', 1),
                'current_streak': xp_record.get('current_streak', 0),
                'max_streak': xp_record.get('max_streak', 0)
            }
            
            if self.central_db.update_user(telegram_id, xp_updates, 'user_xp'):
                logger.info(f"✅ Updated XP for user {telegram_id}")
    
    def migrate_referrals(self):
        """Migrate referral data"""
        logger.info("Migrating referral data...")
        
        # Try both referral databases
        referrals1 = self.load_sqlite_table("standalone_referral.db", "referral_codes")
        referrals2 = self.load_sqlite_table("credit_referrals.db", "referral_codes")
        
        all_referrals = referrals1 + referrals2
        
        for referral in all_referrals:
            telegram_id = referral.get('user_id') or referral.get('telegram_id')
            if not telegram_id:
                continue
            
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid telegram_id: {telegram_id}")
                continue
            
            # Ensure user exists
            if telegram_id not in self.migrated_users:
                if not self.central_db.create_user(telegram_id, {'tier': 'NIBBLER'}):
                    continue
                self.migrated_users.add(telegram_id)
            
            # Update referral data
            referral_updates = {
                'personal_referral_code': referral.get('code', f'REF_{telegram_id}'),
                'referral_count': referral.get('uses', 0),
                'total_credits_earned': referral.get('credits_earned', 0)
            }
            
            if self.central_db.update_user(telegram_id, referral_updates, 'user_referrals'):
                logger.info(f"✅ Updated referrals for user {telegram_id}")
    
    def migrate_trading_stats(self):
        """Migrate trading statistics"""
        logger.info("Migrating trading statistics...")
        
        # Check various possible sources
        stats_sources = [
            ("trades/trades.db", "trades"),
            ("live_performance.db", "performance"),
            ("drill_reports.db", "drill_reports")
        ]
        
        for db_file, table in stats_sources:
            try:
                stats = self.load_sqlite_table(db_file, table)
                for stat in stats:
                    telegram_id = stat.get('user_id') or stat.get('telegram_id')
                    if not telegram_id:
                        continue
                    
                    try:
                        telegram_id = int(telegram_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Skipping invalid telegram_id: {telegram_id}")
                        continue
                    
                    # Ensure user exists
                    if telegram_id not in self.migrated_users:
                        if not self.central_db.create_user(telegram_id, {'tier': 'NIBBLER'}):
                            continue
                        self.migrated_users.add(telegram_id)
                    
                    # Update trading stats
                    stats_updates = {
                        'total_trades': stat.get('total_trades', 0),
                        'winning_trades': stat.get('winning_trades', 0),
                        'losing_trades': stat.get('losing_trades', 0),
                        'total_pnl': stat.get('total_pnl', 0)
                    }
                    
                    if self.central_db.update_user(telegram_id, stats_updates, 'user_trading_stats'):
                        logger.info(f"✅ Updated trading stats for user {telegram_id}")
            except Exception as e:
                logger.error(f"Error migrating {db_file}: {e}")
    
    def verify_migration(self):
        """Verify all users were migrated successfully"""
        logger.info("\nVerifying migration...")
        
        # Check each migrated user
        for telegram_id in self.migrated_users:
            user = self.central_db.get_user(telegram_id)
            if user:
                logger.info(f"✅ User {telegram_id} verified in central database")
            else:
                logger.error(f"❌ User {telegram_id} missing from central database")
                self.stats['errors'] += 1
        
        self.stats['total_users'] = len(self.migrated_users)
    
    def run_migration(self):
        """Run complete migration"""
        logger.info("="*60)
        logger.info("STARTING DATA MIGRATION TO CENTRAL DATABASE")
        logger.info("="*60)
        
        # Run migrations in order
        self.migrate_user_registry()
        self.migrate_user_profiles()
        self.migrate_fire_modes()
        self.migrate_xp_data()
        self.migrate_referrals()
        self.migrate_trading_stats()
        
        # Verify migration
        self.verify_migration()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total users found: {self.stats['total_users']}")
        logger.info(f"Successfully migrated: {self.stats['migrated']}")
        logger.info(f"Conflicts resolved: {self.stats['conflicts']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        
        if self.stats['errors'] == 0:
            logger.info("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
        else:
            logger.warning(f"\n⚠️ Migration completed with {self.stats['errors']} errors")
        
        return self.stats

if __name__ == "__main__":
    migrator = DataMigrator()
    stats = migrator.run_migration()
    
    # Save migration report
    report_path = Path("/root/HydraX-v2/data/migration_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'migrated_users': list(migrator.migrated_users)
        }, f, indent=2)
    
    logger.info(f"\n📊 Migration report saved to {report_path}")