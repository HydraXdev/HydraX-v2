#!/usr/bin/env python3
"""
Admin Slot Manager - Flexible slot allocation with per-user overrides
Allows administrators to customize slot limits beyond tier defaults
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import sys

# Add path for imports
sys.path.append('/root/HydraX-v2/src')
from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdminSlotManager:
    """Advanced slot management with per-user overrides and admin controls"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/fire_modes.db"):
        self.db_path = db_path
        self.fire_mode_db = FireModeDatabase(db_path)
        self.init_admin_tables()
        
    def init_admin_tables(self):
        """Initialize admin-specific tables for slot management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User-specific slot overrides
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_slot_overrides (
                user_id TEXT PRIMARY KEY,
                manual_slot_override INTEGER,    -- Custom manual slot limit (NULL = use tier default)
                auto_slot_override INTEGER,      -- Custom auto slot limit (NULL = use tier default)
                total_slot_override INTEGER,     -- Custom total slot limit (NULL = calculated)
                override_reason TEXT,            -- Admin note for why override was applied
                set_by_admin TEXT,               -- Admin who set the override
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP             -- NULL = permanent, otherwise temporary override
            )
        ''')
        
        # Tier-based default limits (can be updated by admin)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tier_slot_defaults (
                tier TEXT PRIMARY KEY,
                manual_slots INTEGER NOT NULL,
                auto_slots INTEGER NOT NULL,
                total_slots INTEGER,             -- If NULL, calculated as manual + auto
                notes TEXT,
                updated_by_admin TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Slot allocation history for auditing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slot_allocation_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,           -- 'INCREASE', 'DECREASE', 'SET_OVERRIDE', 'REMOVE_OVERRIDE'
                slot_type TEXT NOT NULL,        -- 'MANUAL', 'AUTO', 'TOTAL'
                old_value INTEGER,
                new_value INTEGER,
                admin_user TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default tier limits from ARCHITECTURE.md
        default_tiers = [
            ('PRESS', 0, 0, 'Read-only access'),
            ('GLADIATOR', 1, 0, 'Basic manual trading'),
            ('REAPER', 2, 0, 'Standard manual trading'),
            ('COMMANDER', 3, 3, 'Advanced manual + auto trading'),
            ('FANG', 3, 3, 'Premium manual + auto trading'),
            ('FANG+', 5, 5, 'Elite tier with expanded limits')
        ]
        
        for tier, manual, auto, notes in default_tiers:
            cursor.execute('''
                INSERT OR IGNORE INTO tier_slot_defaults (tier, manual_slots, auto_slots, notes)
                VALUES (?, ?, ?, ?)
            ''', (tier, manual, auto, notes))
        
        conn.commit()
        conn.close()
        logger.info("Admin slot management tables initialized")
    
    def get_effective_slot_limits(self, user_id: str, user_tier: str) -> Dict[str, int]:
        """Get effective slot limits considering overrides and tier defaults"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for user-specific overrides first
        cursor.execute('''
            SELECT manual_slot_override, auto_slot_override, total_slot_override,
                   expires_at, override_reason
            FROM user_slot_overrides 
            WHERE user_id = ? 
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        ''', (user_id,))
        override_data = cursor.fetchone()
        
        # Get tier defaults
        cursor.execute('''
            SELECT manual_slots, auto_slots, total_slots
            FROM tier_slot_defaults 
            WHERE tier = ?
        ''', (user_tier.upper(),))
        tier_data = cursor.fetchone()
        
        conn.close()
        
        # Use tier defaults if available, otherwise fallback
        if tier_data:
            tier_manual, tier_auto, tier_total = tier_data
        else:
            # Fallback to hardcoded defaults if tier not in database
            fallback_limits = {
                'PRESS': (0, 0), 'GLADIATOR': (1, 0), 'REAPER': (2, 0),
                'COMMANDER': (3, 3), 'FANG': (3, 3), 'FANG+': (5, 5)
            }
            tier_manual, tier_auto = fallback_limits.get(user_tier.upper(), (1, 0))
            tier_total = None
        
        # Apply overrides if they exist
        if override_data:
            manual_override, auto_override, total_override, expires_at, reason = override_data
            
            effective_manual = manual_override if manual_override is not None else tier_manual
            effective_auto = auto_override if auto_override is not None else tier_auto
            effective_total = total_override if total_override is not None else (tier_total or (effective_manual + effective_auto))
            
            logger.info(f"🎯 User {user_id} has slot overrides: Manual={effective_manual}, Auto={effective_auto}, Total={effective_total}, Reason: {reason}")
        else:
            effective_manual = tier_manual
            effective_auto = tier_auto
            effective_total = tier_total or (tier_manual + tier_auto)
        
        return {
            'manual': effective_manual,
            'auto': effective_auto,
            'total': effective_total,
            'has_override': override_data is not None,
            'tier_defaults': {'manual': tier_manual, 'auto': tier_auto, 'total': tier_total or (tier_manual + tier_auto)}
        }
    
    def set_user_slot_override(self, user_id: str, admin_user: str, manual_slots: Optional[int] = None, 
                               auto_slots: Optional[int] = None, total_slots: Optional[int] = None,
                               reason: str = "Admin adjustment", expires_at: Optional[str] = None) -> bool:
        """Set custom slot limits for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current limits for history
            current_limits = self.get_effective_slot_limits(user_id, "COMMANDER")  # Use tier for reference
            
            # Insert or update override
            cursor.execute('''
                INSERT OR REPLACE INTO user_slot_overrides 
                (user_id, manual_slot_override, auto_slot_override, total_slot_override,
                 override_reason, set_by_admin, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, manual_slots, auto_slots, total_slots, reason, admin_user, expires_at))
            
            # Log history
            changes = []
            if manual_slots is not None:
                cursor.execute('''
                    INSERT INTO slot_allocation_history 
                    (user_id, action, slot_type, old_value, new_value, admin_user, reason)
                    VALUES (?, 'SET_OVERRIDE', 'MANUAL', ?, ?, ?, ?)
                ''', (user_id, current_limits['manual'], manual_slots, admin_user, reason))
                changes.append(f"Manual: {current_limits['manual']} → {manual_slots}")
            
            if auto_slots is not None:
                cursor.execute('''
                    INSERT INTO slot_allocation_history 
                    (user_id, action, slot_type, old_value, new_value, admin_user, reason)
                    VALUES (?, 'SET_OVERRIDE', 'AUTO', ?, ?, ?, ?)
                ''', (user_id, current_limits['auto'], auto_slots, admin_user, reason))
                changes.append(f"Auto: {current_limits['auto']} → {auto_slots}")
            
            if total_slots is not None:
                cursor.execute('''
                    INSERT INTO slot_allocation_history 
                    (user_id, action, slot_type, old_value, new_value, admin_user, reason)
                    VALUES (?, 'SET_OVERRIDE', 'TOTAL', ?, ?, ?, ?)
                ''', (user_id, current_limits['total'], total_slots, admin_user, reason))
                changes.append(f"Total: {current_limits['total']} → {total_slots}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Slot override set for user {user_id} by {admin_user}: {', '.join(changes)}")
            logger.info(f"   Reason: {reason}")
            if expires_at:
                logger.info(f"   Expires: {expires_at}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set slot override for user {user_id}: {e}")
            return False
    
    def remove_user_slot_override(self, user_id: str, admin_user: str, reason: str = "Override removed") -> bool:
        """Remove custom slot limits for a user (revert to tier defaults)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current override before removing
            cursor.execute('SELECT manual_slot_override, auto_slot_override, total_slot_override FROM user_slot_overrides WHERE user_id = ?', (user_id,))
            override_data = cursor.fetchone()
            
            if not override_data:
                logger.warning(f"No slot override found for user {user_id}")
                return False
            
            # Remove override
            cursor.execute('DELETE FROM user_slot_overrides WHERE user_id = ?', (user_id,))
            
            # Log history
            cursor.execute('''
                INSERT INTO slot_allocation_history 
                (user_id, action, slot_type, old_value, new_value, admin_user, reason)
                VALUES (?, 'REMOVE_OVERRIDE', 'ALL', ?, NULL, ?, ?)
            ''', (user_id, f"{override_data[0]},{override_data[1]},{override_data[2]}", admin_user, reason))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Slot override removed for user {user_id} by {admin_user}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove slot override for user {user_id}: {e}")
            return False
    
    def update_tier_defaults(self, tier: str, admin_user: str, manual_slots: Optional[int] = None,
                           auto_slots: Optional[int] = None, total_slots: Optional[int] = None,
                           notes: Optional[str] = None) -> bool:
        """Update default slot limits for an entire tier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current defaults
            cursor.execute('SELECT manual_slots, auto_slots, total_slots FROM tier_slot_defaults WHERE tier = ?', (tier.upper(),))
            current_data = cursor.fetchone()
            
            if not current_data:
                logger.error(f"Tier {tier} not found in defaults")
                return False
            
            current_manual, current_auto, current_total = current_data
            
            # Build update query dynamically
            updates = []
            params = []
            
            if manual_slots is not None:
                updates.append("manual_slots = ?")
                params.append(manual_slots)
            
            if auto_slots is not None:
                updates.append("auto_slots = ?")
                params.append(auto_slots)
            
            if total_slots is not None:
                updates.append("total_slots = ?")
                params.append(total_slots)
            
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            
            updates.append("updated_by_admin = ?")
            params.append(admin_user)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(tier.upper())
            
            query = f"UPDATE tier_slot_defaults SET {', '.join(updates)} WHERE tier = ?"
            cursor.execute(query, params)
            
            # Log the change
            changes = []
            if manual_slots is not None and manual_slots != current_manual:
                changes.append(f"Manual: {current_manual} → {manual_slots}")
            if auto_slots is not None and auto_slots != current_auto:
                changes.append(f"Auto: {current_auto} → {auto_slots}")
            if total_slots is not None and total_slots != current_total:
                changes.append(f"Total: {current_total} → {total_slots}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Tier {tier} defaults updated by {admin_user}: {', '.join(changes)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update tier {tier} defaults: {e}")
            return False
    
    def get_slot_allocation_history(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get slot allocation history for auditing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT * FROM slot_allocation_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM slot_allocation_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        history = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return history
    
    def get_users_with_overrides(self) -> List[Dict]:
        """Get all users with active slot overrides"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, manual_slot_override, auto_slot_override, total_slot_override,
                   override_reason, set_by_admin, created_at, expires_at
            FROM user_slot_overrides 
            WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        overrides = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return overrides

# CLI interface for admin operations
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Admin Slot Manager - Configure user slot allocations')
    parser.add_argument('action', choices=['get', 'set', 'remove', 'update-tier', 'history', 'list-overrides'])
    parser.add_argument('--user-id', help='Target user ID')
    parser.add_argument('--tier', help='Target tier')
    parser.add_argument('--manual', type=int, help='Manual slot limit')
    parser.add_argument('--auto', type=int, help='Auto slot limit')
    parser.add_argument('--total', type=int, help='Total slot limit')
    parser.add_argument('--admin', default='system', help='Admin performing action')
    parser.add_argument('--reason', default='Manual adjustment', help='Reason for change')
    parser.add_argument('--expires', help='Expiration date (YYYY-MM-DD HH:MM:SS)')
    
    args = parser.parse_args()
    
    manager = AdminSlotManager()
    
    if args.action == 'get' and args.user_id:
        limits = manager.get_effective_slot_limits(args.user_id, "COMMANDER")
        print(f"Slot limits for user {args.user_id}:")
        print(f"  Manual: {limits['manual']}")
        print(f"  Auto: {limits['auto']}")
        print(f"  Total: {limits['total']}")
        print(f"  Has Override: {limits['has_override']}")
        
    elif args.action == 'set' and args.user_id:
        success = manager.set_user_slot_override(
            args.user_id, args.admin, args.manual, args.auto, args.total, args.reason, args.expires
        )
        print(f"Override {'set' if success else 'failed'} for user {args.user_id}")
        
    elif args.action == 'remove' and args.user_id:
        success = manager.remove_user_slot_override(args.user_id, args.admin, args.reason)
        print(f"Override {'removed' if success else 'failed'} for user {args.user_id}")
        
    elif args.action == 'update-tier' and args.tier:
        success = manager.update_tier_defaults(args.tier, args.admin, args.manual, args.auto, args.total)
        print(f"Tier {args.tier} {'updated' if success else 'update failed'}")
        
    elif args.action == 'history':
        history = manager.get_slot_allocation_history(args.user_id)
        print(f"Slot allocation history:")
        for entry in history:
            print(f"  {entry['timestamp']}: {entry['user_id']} - {entry['action']} {entry['slot_type']} {entry['old_value']}→{entry['new_value']} by {entry['admin_user']}")
            
    elif args.action == 'list-overrides':
        overrides = manager.get_users_with_overrides()
        print(f"Active slot overrides:")
        for override in overrides:
            print(f"  {override['user_id']}: Manual={override['manual_slot_override']}, Auto={override['auto_slot_override']}, Total={override['total_slot_override']}")
            print(f"    Reason: {override['override_reason']}, Set by: {override['set_by_admin']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()