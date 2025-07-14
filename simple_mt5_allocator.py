#\!/usr/bin/env python3
"""
Simple MT5 Instance Allocator - Next available by broker type only
No tier logic - that's handled by BITTEN before sending to EA
"""

import sqlite3
import json
from datetime import datetime, timedelta
import uuid

class SimpleMT5Allocator:
    def __init__(self):
        self.db_path = '/root/HydraX-v2/data/mt5_instances.db'
        self.broker_types = {
            "generic_demo": {
                "name": "Generic_Demo",
                "magic_range": (50001, 50200),
                "port_range": (9401, 9600),
                "max_instances": 200,
                "recycle_days": 7,
                "description": "Press Pass instant demo"
            },
            "forex_demo": {
                "name": "Forex_Demo", 
                "magic_range": (30001, 30020),
                "port_range": (9201, 9220),
                "max_instances": 20,
                "recycle_days": None,
                "description": "Regulated broker demo"
            },
            "coinexx_demo": {
                "name": "Coinexx_Demo",
                "magic_range": (40001, 40010),
                "port_range": (9301, 9310),
                "max_instances": 10,
                "recycle_days": None,
                "description": "Offshore broker demo"
            },
            "forex_live": {
                "name": "Forex_Live",
                "magic_range": (20001, 20005),
                "port_range": (9101, 9105),
                "max_instances": 5,
                "recycle_days": None,
                "description": "Regulated broker live"
            },
            "coinexx_live": {
                "name": "Coinexx_Live",
                "magic_range": (10001, 10010),
                "port_range": (9001, 9010),
                "max_instances": 10,
                "recycle_days": None,
                "description": "Offshore broker live"
            }
        }
        self.ensure_tables()
    
    def ensure_tables(self):
        """Create simple allocation tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simple_allocations (
                allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                broker_type TEXT NOT NULL,
                instance_number INTEGER NOT NULL,
                magic_number INTEGER NOT NULL,
                port INTEGER NOT NULL,
                allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                UNIQUE(broker_type, instance_number)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_next_available(self, broker_type):
        """Get next available instance for specific broker type"""
        if broker_type not in self.broker_types:
            return None, f"Invalid broker type: {broker_type}"
        
        broker_config = self.broker_types[broker_type]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find all active allocations for this broker type
        cursor.execute("""
            SELECT instance_number 
            FROM simple_allocations 
            WHERE broker_type = ? AND status = 'active'
            ORDER BY instance_number
        """, (broker_type,))
        
        used_numbers = [row[0] for row in cursor.fetchall()]
        
        # Find first available instance number
        next_instance = 1
        for used in used_numbers:
            if used == next_instance:
                next_instance += 1
            else:
                break
        
        # Check if we've exceeded max instances
        if next_instance > broker_config["max_instances"]:
            conn.close()
            return None, f"All {broker_config['max_instances']} {broker_type} instances are in use"
        
        # Calculate magic number and port
        magic_start, _ = broker_config["magic_range"]
        port_start, _ = broker_config["port_range"]
        
        magic_number = magic_start + (next_instance - 1)
        port = port_start + (next_instance - 1)
        
        conn.close()
        
        return {
            "broker_type": broker_type,
            "instance_number": next_instance,
            "magic_number": magic_number,
            "port": port,
            "directory": f"C:\\MT5_Farm\\Clones\\{broker_config['name']}_{next_instance}"
        }, "Success"
    
    def allocate_instance(self, user_id, broker_type):
        """Allocate next available instance of specified broker type to user"""
        
        # Check if user already has an active instance
        existing = self.get_user_instance(user_id)
        if existing:
            return None, f"User already has active instance: {existing['broker_type']}_{existing['instance_number']}"
        
        # Get next available
        instance, message = self.get_next_available(broker_type)
        if not instance:
            return None, message
        
        # Allocate it
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        broker_config = self.broker_types[broker_type]
        expires_at = None
        if broker_config["recycle_days"]:
            expires_at = datetime.now() + timedelta(days=broker_config["recycle_days"])
        
        try:
            cursor.execute("""
                INSERT INTO simple_allocations 
                (user_id, broker_type, instance_number, magic_number, port, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, broker_type, instance["instance_number"], 
                  instance["magic_number"], instance["port"], expires_at))
            
            conn.commit()
            conn.close()
            
            return instance, "Successfully allocated"
            
        except sqlite3.IntegrityError:
            conn.close()
            return None, "Instance already allocated, trying next..."
    
    def deallocate_instance(self, user_id):
        """Release user's instance back to pool"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE simple_allocations 
            SET status = 'released' 
            WHERE user_id = ? AND status = 'active'
        """, (user_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_user_instance(self, user_id):
        """Get user's active instance if any"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT broker_type, instance_number, magic_number, port, 
                   allocated_at, expires_at
            FROM simple_allocations
            WHERE user_id = ? AND status = 'active'
            ORDER BY allocated_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            broker_config = self.broker_types[row[0]]
            return {
                "broker_type": row[0],
                "instance_number": row[1],
                "magic_number": row[2],
                "port": row[3],
                "allocated_at": row[4],
                "expires_at": row[5],
                "directory": f"C:\\MT5_Farm\\Clones\\{broker_config['name']}_{row[1]}"
            }
        return None
    
    def get_broker_availability(self):
        """Show how many instances available per broker type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        availability = {}
        
        for broker_type, config in self.broker_types.items():
            cursor.execute("""
                SELECT COUNT(*) FROM simple_allocations 
                WHERE broker_type = ? AND status = 'active'
            """, (broker_type,))
            
            used = cursor.fetchone()[0]
            total = config["max_instances"]
            available = total - used
            
            availability[broker_type] = {
                "total": total,
                "used": used,
                "available": available,
                "description": config["description"]
            }
        
        conn.close()
        return availability
    
    def recycle_expired(self):
        """Recycle expired instances (mainly Press Pass)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE simple_allocations 
            SET status = 'expired' 
            WHERE expires_at < datetime('now') AND status = 'active'
        """)
        
        recycled = cursor.rowcount
        conn.commit()
        conn.close()
        
        return recycled

def demonstrate():
    """Show how the simple allocator works"""
    allocator = SimpleMT5Allocator()
    
    print("🎯 Simple MT5 Allocator Demo")
    print("=" * 60)
    
    # Show availability
    print("\n📊 Current Availability:")
    availability = allocator.get_broker_availability()
    
    for broker_type, stats in availability.items():
        print(f"\n{broker_type}:")
        print(f"  {stats['description']}")
        print(f"  Available: {stats['available']}/{stats['total']}")
    
    # Test allocations
    print("\n\n🧪 Testing Allocations:")
    
    test_cases = [
        ("user_1", "generic_demo", "User wants Press Pass trial"),
        ("user_2", "forex_demo", "User wants regulated demo"),
        ("user_3", "coinexx_live", "User wants offshore live"),
        ("user_4", "generic_demo", "Another Press Pass user"),
        ("user_5", "forex_live", "Conservative live trader")
    ]
    
    for user_id, broker_type, description in test_cases:
        print(f"\n📤 {description}:")
        instance, message = allocator.allocate_instance(user_id, broker_type)
        
        if instance:
            print(f"   ✅ Allocated: {broker_type}_{instance['instance_number']}")
            print(f"   📍 Magic: {instance['magic_number']}, Port: {instance['port']}")
        else:
            print(f"   ❌ Failed: {message}")
    
    # Show updated availability
    print("\n\n📊 Updated Availability:")
    availability = allocator.get_broker_availability()
    
    for broker_type, stats in availability.items():
        if stats['used'] > 0:
            print(f"{broker_type}: {stats['used']} used, {stats['available']} available")

if __name__ == "__main__":
    demonstrate()
    
    print("\n" + "="*60)
    print("✅ SIMPLE ALLOCATOR BENEFITS:")
    print("="*60)
    print("\n1. User chooses broker type (not tier-based)")
    print("2. Next available instance from that broker pool")
    print("3. No complex tier logic - BITTEN handles that")
    print("4. Clear tracking of what's available")
    print("5. Automatic Press Pass recycling after 7 days")
    
    print("\n📋 USAGE:")
    print("```python")
    print("allocator = SimpleMT5Allocator()")
    print("")
    print("# User wants offshore demo")
    print('instance, msg = allocator.allocate_instance("user123", "coinexx_demo")')
    print("")
    print("# Check what user has")
    print('instance = allocator.get_user_instance("user123")')
    print("")
    print("# See availability")
    print("stats = allocator.get_broker_availability()")
    print("```")
