#!/usr/bin/env python3
"""
Entitlement system for mapping users to tiers
Controls which exit strategies and features each user can access
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
import logging
import argparse

logger = logging.getLogger(__name__)

class EntitlementManager:
    """
    Manages user tier assignments and entitlements
    """
    
    # Tier definitions
    TIERS = {
        "TIER_BEGINNER": {
            "name": "Beginner",
            "price": 39,
            "features": ["fixed_scalp", "time_boxed"],
            "max_concurrent": 1,
            "autofire": False
        },
        "TIER_PLUS": {
            "name": "Plus",
            "price": 89,
            "features": ["scalp_runner", "partials", "trailing", "be_protection"],
            "max_concurrent": 3,
            "autofire": False
        },
        "TIER_PRO": {
            "name": "Pro",
            "price": 199,
            "features": ["scalp_runner", "partials", "trailing", "be_protection", "autofire", "session_filter"],
            "max_concurrent": 5,
            "autofire": True
        }
    }
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/entitlements.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize entitlements database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create entitlements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_entitlements (
                user_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL DEFAULT 'TIER_BEGINNER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                notes TEXT
            )
        """)
        
        # Create tier history table for tracking changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tier_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                old_tier TEXT,
                new_tier TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by TEXT,
                reason TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Entitlements database initialized")
    
    def get_user_tier(self, user_id: str) -> str:
        """
        Get user's current tier
        Returns TIER_BEGINNER if user not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tier FROM user_entitlements 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Default to beginner for new users
            self.set_user_tier(user_id, "TIER_BEGINNER", reason="New user default")
            return "TIER_BEGINNER"
    
    def set_user_tier(self, user_id: str, tier: str, 
                     changed_by: str = "system", reason: str = "") -> bool:
        """Set user's tier with history tracking"""
        if tier not in self.TIERS:
            logger.error(f"Invalid tier: {tier}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current tier for history
            cursor.execute("SELECT tier FROM user_entitlements WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            old_tier = result[0] if result else None
            
            # Update or insert tier
            cursor.execute("""
                INSERT OR REPLACE INTO user_entitlements (user_id, tier, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, tier))
            
            # Record history
            cursor.execute("""
                INSERT INTO tier_history (user_id, old_tier, new_tier, changed_by, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, old_tier, tier, changed_by, reason))
            
            conn.commit()
            logger.info(f"User {user_id} tier changed from {old_tier} to {tier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set tier: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_tier_features(self, tier: str) -> Dict:
        """Get features available for a tier"""
        return self.TIERS.get(tier, self.TIERS["TIER_BEGINNER"])
    
    def can_use_feature(self, user_id: str, feature: str) -> bool:
        """Check if user can use a specific feature"""
        tier = self.get_user_tier(user_id)
        tier_info = self.get_tier_features(tier)
        return feature in tier_info.get("features", [])
    
    def can_autofire(self, user_id: str) -> bool:
        """Check if user has autofire permission"""
        tier = self.get_user_tier(user_id)
        tier_info = self.get_tier_features(tier)
        return tier_info.get("autofire", False)
    
    def get_max_concurrent(self, user_id: str) -> int:
        """Get maximum concurrent positions for user"""
        tier = self.get_user_tier(user_id)
        tier_info = self.get_tier_features(tier)
        return tier_info.get("max_concurrent", 1)
    
    def get_all_users_by_tier(self, tier: str) -> List[str]:
        """Get all users with a specific tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id FROM user_entitlements 
            WHERE tier = ?
        """, (tier,))
        
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def get_tier_statistics(self) -> Dict[str, int]:
        """Get count of users per tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tier, COUNT(*) as count
            FROM user_entitlements
            GROUP BY tier
        """)
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Include zeros for missing tiers
        for tier in self.TIERS:
            if tier not in stats:
                stats[tier] = 0
        
        return stats
    
    def get_user_history(self, user_id: str) -> List[Dict]:
        """Get tier change history for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT old_tier, new_tier, changed_at, changed_by, reason
            FROM tier_history
            WHERE user_id = ?
            ORDER BY changed_at DESC
            LIMIT 10
        """, (user_id,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "old_tier": row[0],
                "new_tier": row[1],
                "changed_at": row[2],
                "changed_by": row[3],
                "reason": row[4]
            })
        
        conn.close()
        return history

# Singleton instance
entitlement_manager = EntitlementManager()

def main():
    """CLI for managing user tiers"""
    parser = argparse.ArgumentParser(description="Manage user tier entitlements")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Set tier command
    set_parser = subparsers.add_parser("set", help="Set user tier")
    set_parser.add_argument("--user", required=True, help="User ID")
    set_parser.add_argument("--tier", required=True, 
                          choices=["TIER_BEGINNER", "TIER_PLUS", "TIER_PRO"],
                          help="Tier to assign")
    set_parser.add_argument("--reason", default="Manual CLI update", help="Reason for change")
    
    # Get tier command
    get_parser = subparsers.add_parser("get", help="Get user tier")
    get_parser.add_argument("--user", required=True, help="User ID")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show tier statistics")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show user tier history")
    history_parser.add_argument("--user", required=True, help="User ID")
    
    args = parser.parse_args()
    
    if args.command == "set":
        success = entitlement_manager.set_user_tier(
            args.user, args.tier, "CLI", args.reason
        )
        if success:
            print(f"✅ User {args.user} set to {args.tier}")
        else:
            print(f"❌ Failed to set tier")
    
    elif args.command == "get":
        tier = entitlement_manager.get_user_tier(args.user)
        features = entitlement_manager.get_tier_features(tier)
        print(f"User: {args.user}")
        print(f"Tier: {tier} ({features['name']})")
        print(f"Features: {', '.join(features['features'])}")
        print(f"Autofire: {'Yes' if features['autofire'] else 'No'}")
        print(f"Max Concurrent: {features['max_concurrent']}")
    
    elif args.command == "stats":
        stats = entitlement_manager.get_tier_statistics()
        print("Tier Statistics:")
        for tier, count in stats.items():
            tier_info = entitlement_manager.TIERS[tier]
            print(f"  {tier_info['name']} ({tier}): {count} users")
    
    elif args.command == "history":
        history = entitlement_manager.get_user_history(args.user)
        print(f"Tier History for {args.user}:")
        for entry in history:
            print(f"  {entry['changed_at']}: {entry['old_tier'] or 'NEW'} → {entry['new_tier']}")
            print(f"    By: {entry['changed_by']} | Reason: {entry['reason']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()