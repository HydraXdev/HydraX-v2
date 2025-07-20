#\!/usr/bin/env python3
"""
MT5 Instance Allocator - Assigns instances to users based on tier and preferences
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random

class MT5InstanceAllocator:
    def __init__(self):
        self.db_path = '/root/HydraX-v2/data/mt5_instances.db'
        self.ensure_database()
    
    def ensure_database(self):
        """Ensure allocator tables exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                preferred_broker TEXT,
                leverage_preference TEXT,
                last_instance_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Instance allocations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instance_allocations (
                allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                instance_id TEXT NOT NULL,
                instance_type TEXT NOT NULL,
                magic_number INTEGER,
                port INTEGER,
                allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def allocate_instance(self, user_id, tier, preferences=None):
        """
        Allocate an MT5 instance to a user based on tier and preferences
        
        Allocation Logic:
        - PRESS_PASS: Always gets Generic_Demo (instant, no login)
        - NIBBLER/FANG: Prefers Forex_Demo (regulated) unless user wants offshore
        - COMMANDER: Based on leverage preference (regulated vs offshore)
        """
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine instance type based on tier
        if tier == "PRESS_PASS":
            instance_type = "Generic_Demo"
            expires_days = 7
        else:
            # Check user preferences
            cursor.execute("""
                SELECT preferred_broker, leverage_preference 
                FROM user_preferences 
                WHERE user_id = ?
            """, (user_id,))
            
            pref = cursor.fetchone()
            
            if tier in ["NIBBLER", "FANG"]:
                # Demo accounts for lower tiers
                if pref and pref[0] == "offshore":
                    instance_type = "Coinexx_Demo"
                else:
                    instance_type = "Forex_Demo"  # Default to regulated
                expires_days = None  # No expiry for paid tiers
                
            else:  # COMMANDER
                # Live accounts for higher tiers
                if pref and pref[1] == "high_leverage":
                    instance_type = "Coinexx_Live"
                else:
                    instance_type = "Forex_Live"  # Default to regulated
                expires_days = None
        
        # Find available instance
        instance = self._find_available_instance(instance_type)
        
        if not instance:
            conn.close()
            return None, f"No available {instance_type} instances"
        
        # Allocate the instance
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        cursor.execute("""
            INSERT INTO instance_allocations 
            (user_id, instance_id, instance_type, magic_number, port, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, instance['instance_id'], instance_type, 
              instance['magic_number'], instance['port'], expires_at))
        
        # Update instance status
        cursor.execute("""
            UPDATE mt5_instances 
            SET status = 'allocated', assigned_user_id = ?, last_active = CURRENT_TIMESTAMP
            WHERE instance_id = ?
        """, (user_id, instance['instance_id']))
        
        conn.commit()
        conn.close()
        
        return instance, "Success"
    
    def _find_available_instance(self, instance_type):
        """Find an available instance of the specified type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Magic number and port ranges by type
        ranges = {
            "Generic_Demo": {"magic": (50001, 50200), "port": (9401, 9600)},
            "Forex_Demo": {"magic": (30001, 30020), "port": (9201, 9220)},
            "Coinexx_Demo": {"magic": (40001, 40010), "port": (9301, 9310)},
            "Forex_Live": {"magic": (20001, 20005), "port": (9101, 9105)},
            "Coinexx_Live": {"magic": (10001, 10010), "port": (9001, 9010)}
        }
        
        if instance_type not in ranges:
            return None
        
        # Try to find existing available instance
        cursor.execute("""
            SELECT instance_id, magic_number, port, directory_path
            FROM mt5_instances
            WHERE master_type = ? AND status = 'inactive' AND assigned_user_id IS NULL
            LIMIT 1
        """, (instance_type,))
        
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return {
                "instance_id": result[0],
                "magic_number": result[1],
                "port": result[2],
                "directory": result[3]
            }
        
        # If no instance in DB, calculate next available
        cursor.execute("""
            SELECT MAX(magic_number) FROM mt5_instances WHERE master_type = ?
        """, (instance_type,))
        
        max_magic = cursor.fetchone()[0]
        magic_range = ranges[instance_type]["magic"]
        
        if max_magic:
            next_magic = max_magic + 1
            if next_magic > magic_range[1]:
                conn.close()
                return None  # All instances allocated
        else:
            next_magic = magic_range[0]
        
        # Calculate instance number and port
        instance_num = next_magic - magic_range[0]
        next_port = ranges[instance_type]["port"][0] + instance_num
        
        # Create new instance record
        import uuid
        instance_id = str(uuid.uuid4())
        directory = f"C:\\MT5_Farm\\Clones\\{instance_type}_{instance_num}"
        
        cursor.execute("""
            INSERT INTO mt5_instances 
            (instance_id, master_type, clone_number, magic_number, port, directory_path, status)
            VALUES (?, ?, ?, ?, ?, ?, 'inactive')
        """, (instance_id, instance_type, instance_num, next_magic, next_port, directory))
        
        conn.commit()
        conn.close()
        
        return {
            "instance_id": instance_id,
            "magic_number": next_magic,
            "port": next_port,
            "directory": directory
        }
    
    def deallocate_instance(self, user_id, instance_id):
        """Deallocate an instance from a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mark allocation as inactive
        cursor.execute("""
            UPDATE instance_allocations 
            SET status = 'released' 
            WHERE user_id = ? AND instance_id = ? AND status = 'active'
        """, (user_id, instance_id))
        
        # Mark instance as available
        cursor.execute("""
            UPDATE mt5_instances 
            SET status = 'inactive', assigned_user_id = NULL 
            WHERE instance_id = ?
        """, (instance_id,))
        
        conn.commit()
        conn.close()
    
    def get_user_instance(self, user_id):
        """Get active instance for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.instance_id, a.instance_type, a.magic_number, a.port, 
                   a.allocated_at, a.expires_at, i.directory_path
            FROM instance_allocations a
            JOIN mt5_instances i ON a.instance_id = i.instance_id
            WHERE a.user_id = ? AND a.status = 'active'
            ORDER BY a.allocated_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "instance_id": result[0],
                "type": result[1],
                "magic_number": result[2],
                "port": result[3],
                "allocated_at": result[4],
                "expires_at": result[5],
                "directory": result[6]
            }
        return None
    
    def recycle_expired_instances(self):
        """Recycle expired Press Pass instances"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find expired allocations
        cursor.execute("""
            SELECT instance_id, user_id 
            FROM instance_allocations 
            WHERE expires_at < datetime('now') AND status = 'active'
        """)
        
        expired = cursor.fetchall()
        recycled_count = 0
        
        for instance_id, user_id in expired:
            self.deallocate_instance(user_id, instance_id)
            recycled_count += 1
        
        conn.close()
        return recycled_count

def demonstrate_allocation():
    """Show how the allocator works"""
    allocator = MT5InstanceAllocator()
    
    print("🎯 MT5 Instance Allocator Demo")
    print("=" * 60)
    
    # Test allocations
    test_users = [
        ("user_press_1", "PRESS_PASS", "New user trying Press Pass"),
        ("user_nibbler_1", "NIBBLER", "Paid user preferring regulated"),
        ("user_fang_1", "FANG", "Paid user wanting offshore"),
        ("user_commander_1", "COMMANDER", "High tier regulated"),
        ("user_commander_1", "COMMANDER", "High tier offshore")
    ]
    
    for user_id, tier, description in test_users:
        print(f"\n📤 Allocating for {description}:")
        instance, message = allocator.allocate_instance(user_id, tier)
        
        if instance:
            print(f"   ✅ Allocated: {instance['instance_id'][:8]}...")
            print(f"   📍 Type: {tier} → Magic: {instance['magic_number']}, Port: {instance['port']}")
        else:
            print(f"   ❌ Failed: {message}")
    
    # Check user instance
    print("\n📊 Checking user instances:")
    user_instance = allocator.get_user_instance("user_press_1")
    if user_instance:
        print(f"   User has: {user_instance['type']} (expires: {user_instance['expires_at']})")

if __name__ == "__main__":
    demonstrate_allocation()
    
    print("\n" + "="*60)
    print("📁 EA LOCATION ON MT5:")
    print("="*60)
    print("\nThe EA file needs to be placed in EACH MT5 instance:")
    print("\n1. **Source file**: /root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5")
    print("\n2. **MT5 Destination** (for each instance):")
    print("   C:\\MT5_Farm\\Masters\\[InstanceType]\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5")
    print("\n3. **After copying**:")
    print("   - Open MT5 terminal")
    print("   - Open MetaEditor (F4)")
    print("   - Navigate to Experts folder")
    print("   - Compile the EA (F7)")
    print("   - EA will appear in Navigator under Expert Advisors")
    print("\n4. **To attach**:")
    print("   - Drag from Navigator to each of the 10 charts")
    print("   - Enable 'Allow live trading' in settings")
    print("   - Set unique magic number for each instance")
