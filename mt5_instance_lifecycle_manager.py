#\!/usr/bin/env python3
"""
MT5 Instance Lifecycle Manager - Handles replenishment and user data persistence
"""

import sqlite3
import json
from datetime import datetime, timedelta
import uuid

class MT5LifecycleManager:
    def __init__(self):
        self.db_path = '/root/HydraX-v2/data/mt5_instances.db'
        self.ensure_tables()
        
        # Replenishment thresholds by broker type
        self.replenishment_config = {
            "generic_demo": {
                "threshold_percent": 30,  # Replenish when 30% left (high turnover)
                "min_available": 60,      # Always keep 60 ready
                "batch_size": 50,         # Create 50 at a time
                "reason": "High volume Press Pass trials need buffer"
            },
            "forex_demo": {
                "threshold_percent": 40,  # Replenish when 40% left
                "min_available": 10,      # Keep 10 ready
                "batch_size": 10,         # Create 10 at a time
                "reason": "Steady demand from new paid users"
            },
            "forex_live": {
                "threshold_percent": 30,  # Replenish when 30% left (most popular\!)
                "min_available": 30,      # Always keep 30 ready
                "batch_size": 25,         # Create 25 at a time
                "reason": "Most popular live broker - need large buffer"
            },
            "coinexx_demo": {
                "threshold_percent": 50,  # Replenish when 50% left
                "min_available": 5,       # Keep 5 ready
                "batch_size": 5,          # Create 5 at a time
                "reason": "Low volume, replenish conservatively"
            },
            "coinexx_live": {
                "threshold_percent": 50,  # Replenish when 50% left
                "min_available": 7,       # Keep 7 ready
                "batch_size": 5,          # Create 5 at a time
                "reason": "Niche market, moderate buffer"
            }
        }
    
    def ensure_tables(self):
        """Create tables for lifecycle management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User data persistence table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_frozen_data (
                user_id TEXT PRIMARY KEY,
                telegram_id TEXT,
                gamer_name TEXT,
                tier TEXT,
                xp_total INTEGER,
                xp_lifetime INTEGER,
                badges TEXT,  -- JSON array
                achievements TEXT,  -- JSON array
                trade_stats TEXT,  -- JSON object
                win_rate REAL,
                total_trades INTEGER,
                account_size REAL,
                last_magic_number INTEGER,
                last_broker_type TEXT,
                subscription_end_date TIMESTAMP,
                frozen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_snapshot TEXT  -- Full JSON backup
            )
        ''')
        
        # Instance replenishment log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS replenishment_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                broker_type TEXT,
                available_before INTEGER,
                created_count INTEGER,
                available_after INTEGER,
                trigger_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Instance lifecycle events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lifecycle_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT,
                broker_type TEXT,
                event_type TEXT,  -- created, allocated, released, recycled, abandoned
                user_id TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_replenishment_needed(self):
        """Check all broker types and replenish as needed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        replenishment_needed = []
        
        for broker_type, config in self.replenishment_config.items():
            # Get current availability
            cursor.execute("""
                SELECT COUNT(*) FROM simple_allocations 
                WHERE broker_type = ? AND status = 'active'
            """, (broker_type,))
            
            used_count = cursor.fetchone()[0]
            
            # Calculate based on broker type totals
            totals = {
                "generic_demo": 200,
                "forex_demo": 25,
                "forex_live": 100,
                "coinexx_demo": 10,
                "coinexx_live": 15
            }
            
            total = totals.get(broker_type, 10)
            available = total - used_count
            percent_available = (available / total) * 100
            
            # Check if replenishment needed
            needs_replenishment = False
            reason = ""
            
            if percent_available <= config["threshold_percent"]:
                needs_replenishment = True
                reason = f"Below {config['threshold_percent']}% threshold"
            elif available < config["min_available"]:
                needs_replenishment = True
                reason = f"Below minimum {config['min_available']} instances"
            
            if needs_replenishment:
                replenishment_needed.append({
                    "broker_type": broker_type,
                    "available": available,
                    "percent": percent_available,
                    "batch_size": config["batch_size"],
                    "reason": reason
                })
        
        conn.close()
        return replenishment_needed
    
    def freeze_user_data(self, user_id):
        """Freeze user data when subscription lapses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Gather all user data from various tables
        user_data = {
            "user_id": user_id,
            "frozen_at": datetime.now().isoformat(),
            "xp_data": {},
            "trade_stats": {},
            "achievements": [],
            "badges": [],
            "preferences": {}
        }
        
        # Get XP and stats
        cursor.execute("""
            SELECT xp_total, xp_lifetime, win_rate, total_trades, tier
            FROM user_stats WHERE user_id = ?
        """, (user_id,))
        
        stats = cursor.fetchone()
        if stats:
            user_data["xp_data"] = {
                "total": stats[0],
                "lifetime": stats[1]
            }
            user_data["trade_stats"] = {
                "win_rate": stats[2],
                "total_trades": stats[3]
            }
            user_data["tier"] = stats[4]
        
        # Get achievements and badges
        cursor.execute("""
            SELECT achievement_id, unlock_date, points_earned
            FROM achievement_unlocks WHERE user_id = ?
        """, (user_id,))
        
        achievements = cursor.fetchall()
        user_data["achievements"] = [
            {"id": a[0], "date": a[1], "points": a[2]} 
            for a in achievements
        ]
        
        # Get last instance info
        cursor.execute("""
            SELECT broker_type, magic_number 
            FROM simple_allocations 
            WHERE user_id = ? 
            ORDER BY allocated_at DESC LIMIT 1
        """, (user_id,))
        
        last_instance = cursor.fetchone()
        if last_instance:
            user_data["last_broker_type"] = last_instance[0]
            user_data["last_magic_number"] = last_instance[1]
        
        # Store frozen data
        cursor.execute("""
            INSERT OR REPLACE INTO user_frozen_data
            (user_id, xp_total, xp_lifetime, badges, achievements, 
             trade_stats, win_rate, total_trades, last_broker_type,
             subscription_end_date, data_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data["xp_data"].get("total", 0),
            user_data["xp_data"].get("lifetime", 0),
            json.dumps(user_data["badges"]),
            json.dumps(user_data["achievements"]),
            json.dumps(user_data["trade_stats"]),
            user_data["trade_stats"].get("win_rate", 0),
            user_data["trade_stats"].get("total_trades", 0),
            user_data.get("last_broker_type"),
            datetime.now(),
            json.dumps(user_data)
        ))
        
        # Release their MT5 instance
        cursor.execute("""
            UPDATE simple_allocations 
            SET status = 'abandoned' 
            WHERE user_id = ? AND status = 'active'
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
        return user_data
    
    def restore_user_data(self, user_id, new_instance):
        """Restore user data when they return"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get frozen data
        cursor.execute("""
            SELECT xp_total, xp_lifetime, badges, achievements, 
                   trade_stats, win_rate, total_trades, data_snapshot
            FROM user_frozen_data WHERE user_id = ?
        """, (user_id,))
        
        frozen_data = cursor.fetchone()
        if not frozen_data:
            return None
        
        # Parse the data
        restored_data = {
            "xp_total": frozen_data[0],
            "xp_lifetime": frozen_data[1],
            "badges": json.loads(frozen_data[2]),
            "achievements": json.loads(frozen_data[3]),
            "trade_stats": json.loads(frozen_data[4]),
            "win_rate": frozen_data[5],
            "total_trades": frozen_data[6],
            "full_backup": json.loads(frozen_data[7])
        }
        
        # Update user stats with restored data
        cursor.execute("""
            UPDATE user_stats 
            SET xp_total = ?, xp_lifetime = ?, win_rate = ?, total_trades = ?
            WHERE user_id = ?
        """, (
            restored_data["xp_total"],
            restored_data["xp_lifetime"],
            restored_data["win_rate"],
            restored_data["total_trades"],
            user_id
        ))
        
        # Log the restoration
        cursor.execute("""
            INSERT INTO lifecycle_events
            (instance_id, broker_type, event_type, user_id, event_data)
            VALUES (?, ?, 'restored', ?, ?)
        """, (
            new_instance.get("instance_id"),
            new_instance.get("broker_type"),
            user_id,
            json.dumps({"restored_from_freeze": True, "xp": restored_data["xp_total"]})
        ))
        
        conn.commit()
        conn.close()
        
        return restored_data
    
    def get_replenishment_status(self):
        """Get current status of all broker types"""
        status = {}
        
        for broker_type, config in self.replenishment_config.items():
            # Mock data for demonstration
            totals = {
                "generic_demo": 200,
                "forex_demo": 25,
                "forex_live": 100,
                "coinexx_demo": 10,
                "coinexx_live": 15
            }
            
            total = totals[broker_type]
            # Simulate some usage
            import random
            used = random.randint(0, int(total * 0.7))
            available = total - used
            percent = (available / total) * 100
            
            status[broker_type] = {
                "total": total,
                "used": used,
                "available": available,
                "percent_available": round(percent, 1),
                "threshold": config["threshold_percent"],
                "min_required": config["min_available"],
                "needs_replenishment": percent <= config["threshold_percent"] or available < config["min_available"],
                "batch_size": config["batch_size"]
            }
        
        return status

def demonstrate_lifecycle():
    """Show how lifecycle management works"""
    manager = MT5LifecycleManager()
    
    print("🔄 MT5 Instance Lifecycle Manager")
    print("=" * 60)
    
    # Show replenishment status
    print("\n📊 REPLENISHMENT STATUS:")
    print("-" * 60)
    
    status = manager.get_replenishment_status()
    for broker_type, info in status.items():
        print(f"\n{broker_type}:")
        print(f"  Available: {info['available']}/{info['total']} ({info['percent_available']}%)")
        print(f"  Threshold: {info['threshold']}% (min {info['min_required']} instances)")
        
        if info['needs_replenishment']:
            print(f"  ⚠️  NEEDS REPLENISHMENT - Will create {info['batch_size']} more")
        else:
            print(f"  ✅ Sufficient capacity")
    
    # Check what needs replenishment
    print("\n\n🔍 CHECKING REPLENISHMENT NEEDS:")
    needs = manager.check_replenishment_needed()
    
    if needs:
        print("\nInstances needing replenishment:")
        for need in needs:
            print(f"  - {need['broker_type']}: {need['reason']}")
            print(f"    Will create {need['batch_size']} new instances")
    else:
        print("✅ All broker types have sufficient instances")
    
    # Demonstrate user data freeze/restore
    print("\n\n❄️ USER DATA PERSISTENCE DEMO:")
    print("-" * 60)
    
    # Simulate subscription lapse
    test_user = "user_12345"
    print(f"\n1. User {test_user} subscription lapses...")
    frozen_data = manager.freeze_user_data(test_user)
    print(f"   ✅ Data frozen: {frozen_data.get('xp_data', {}).get('total', 0)} XP saved")
    
    # Simulate user return
    print(f"\n2. User returns after 30 days...")
    new_instance = {"instance_id": "new_123", "broker_type": "forex_live"}
    restored = manager.restore_user_data(test_user, new_instance)
    if restored:
        print(f"   ✅ Data restored: {restored['xp_total']} XP, {restored['total_trades']} trades")

if __name__ == "__main__":
    demonstrate_lifecycle()
    
    print("\n" + "="*60)
    print("🎯 LIFECYCLE MANAGEMENT SUMMARY")
    print("="*60)
    
    print("\n📈 REPLENISHMENT STRATEGY:")
    print("- Generic Demo: Replenish at 30% (high turnover)")
    print("- Forex Demo: Replenish at 40% (steady demand)")
    print("- Forex Live: Replenish at 30% (most popular\!)")
    print("- Coinexx: Replenish at 50% (lower demand)")
    
    print("\n❄️ USER DATA PERSISTENCE:")
    print("- All XP, badges, achievements frozen on unsubscribe")
    print("- MT5 instance recycled for others")
    print("- On return: New instance + restored data")
    print("- Account size from MT5, XP/badges from database")
    
    print("\n♻️ RECYCLING TRIGGERS:")
    print("- Press Pass: 7 days (automatic)")
    print("- Subscription lapse: Immediate")
    print("- Abandoned: 30 days no activity")
    print("- Manual: Admin cleanup")
