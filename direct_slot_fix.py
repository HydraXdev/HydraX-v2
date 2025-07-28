#!/usr/bin/env python3
"""
Direct Fire Slot Fix for User 7176191872
Direct SQLite operations to ensure COMMANDER gets 3 slots
"""

import sqlite3
import os
from datetime import datetime

def direct_slot_fix():
    """Direct database fix for COMMANDER fire slots"""
    
    user_id = "7176191872"
    db_path = "/root/HydraX-v2/data/fire_modes.db"
    
    print("🔧 DIRECT FIRE SLOT FIX")
    print("=" * 50)
    print(f"User: {user_id}")
    print(f"Database: {db_path}")
    print()
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        print("📝 Ensuring database schema...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_fire_modes (
                user_id TEXT PRIMARY KEY,
                current_mode TEXT DEFAULT 'SELECT',
                max_slots INTEGER DEFAULT 1,
                slots_in_use INTEGER DEFAULT 0,
                last_mode_change TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if user exists
        cursor.execute('SELECT * FROM user_fire_modes WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"✅ Found existing user record")
            print(f"   Current values: mode={existing_user[1]}, max_slots={existing_user[2]}, slots_in_use={existing_user[3]}")
            
            # Update existing record
            cursor.execute('''
                UPDATE user_fire_modes 
                SET current_mode = 'AUTO', 
                    max_slots = 3, 
                    slots_in_use = 0,
                    last_mode_change = ?,
                    updated_at = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
            
            print("✅ Updated existing record")
        else:
            print("ℹ️ No existing record - creating new one")
            
            # Insert new record
            cursor.execute('''
                INSERT INTO user_fire_modes 
                (user_id, current_mode, max_slots, slots_in_use, last_mode_change, created_at, updated_at)
                VALUES (?, 'AUTO', 3, 0, ?, ?, ?)
            ''', (user_id, datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
            
            print("✅ Created new record")
        
        # Commit changes
        conn.commit()
        
        # Verify the fix
        cursor.execute('SELECT * FROM user_fire_modes WHERE user_id = ?', (user_id,))
        updated_user = cursor.fetchone()
        
        if updated_user:
            print()
            print("🔍 Verification Results:")
            print(f"✅ User ID: {updated_user[0]}")
            print(f"✅ Mode: {updated_user[1]}")
            print(f"✅ Max Slots: {updated_user[2]}")
            print(f"✅ Slots in Use: {updated_user[3]}")
            print(f"✅ Last Change: {updated_user[4]}")
            
            if updated_user[1] == 'AUTO' and updated_user[2] == 3:
                print()
                print("🎉 DIRECT FIX SUCCESSFUL!")
                print("🎯 COMMANDER now has 3 AUTO fire slots")
                conn.close()
                return True
            else:
                print("❌ Verification failed")
                conn.close()
                return False
        else:
            print("❌ Could not verify fix")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def test_fire_mode_db():
    """Test the fire_mode_db module after fix"""
    
    print("\n🧪 TESTING FIRE MODE DATABASE MODULE")
    print("=" * 50)
    
    try:
        import sys
        sys.path.insert(0, '/root/HydraX-v2')
        from src.bitten_core.fire_mode_database import fire_mode_db
        
        user_id = "7176191872"
        
        # Test get_user_mode
        mode_info = fire_mode_db.get_user_mode(user_id)
        print(f"✅ Retrieved user mode: {mode_info}")
        
        # Check values
        if mode_info['current_mode'] == 'AUTO' and mode_info['max_slots'] == 3:
            print("✅ Fire mode database module working correctly")
            
            # Test slot availability
            available = fire_mode_db.check_slot_available(user_id)
            print(f"✅ Slots available: {available}")
            
            # Show status
            slots_used = mode_info['slots_in_use']
            max_slots = mode_info['max_slots']
            print(f"✅ Slot status: {slots_used}/{max_slots} used")
            
            return True
        else:
            print(f"❌ Unexpected values - mode: {mode_info['current_mode']}, slots: {mode_info['max_slots']}")
            return False
            
    except Exception as e:
        print(f"❌ Module test error: {e}")
        return False

if __name__ == "__main__":
    print("🎖️ DIRECT COMMANDER FIRE SLOT FIX")
    print("=" * 60)
    print()
    
    # Apply direct fix
    fix_success = direct_slot_fix()
    
    if fix_success:
        # Test the module
        test_success = test_fire_mode_db()
        
        if test_success:
            print()
            print("🚀 COMMANDER FIRE SYSTEM FULLY OPERATIONAL!")
            print()
            print("🎯 Your mode status should now show:")
            print("   • Mode: AUTO")
            print("   • Available slots: 3")
            print("   • Auto-firing signals with 87%+ TCS")
            print()
            print("✅ Ready for full auto fire with 3 slots!")
        else:
            print()
            print("⚠️ Direct fix applied but module test failed")
            print("Database updated but may need system restart")
    else:
        print()
        print("❌ Direct fix failed - please check database permissions")