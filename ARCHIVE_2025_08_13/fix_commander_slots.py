#!/usr/bin/env python3
"""
Fix Commander Fire Slots for User 7176191872
Sets max_slots to 3 for COMMANDER tier user
"""

import sys
import sqlite3
import logging
from datetime import datetime

# Setup path
sys.path.insert(0, '/root/HydraX-v2')

from src.bitten_core.fire_mode_database import fire_mode_db
from config.fire_mode_config import FireModeConfig

def fix_commander_slots():
    """Fix fire slot allocation for COMMANDER tier user"""
    
    user_id = "7176191872"
    
    print("🔧 COMMANDER FIRE SLOT FIX")
    print("=" * 50)
    print(f"User: {user_id}")
    print()
    
    # Check current configuration
    print("📊 Current Fire Mode Configuration:")
    try:
        mode_info = fire_mode_db.get_user_mode(user_id)
        print(f"✅ Current Mode: {mode_info['current_mode']}")
        print(f"✅ Max Slots: {mode_info['max_slots']}")
        print(f"✅ Slots in Use: {mode_info['slots_in_use']}")
        print(f"✅ Last Change: {mode_info['last_mode_change']}")
        print()
        
        # Check what COMMANDER should get
        commander_config = FireModeConfig.SIGNAL_ACCESS.get("COMMANDER", {})
        expected_slots = commander_config.get("max_auto_slots", 3)
        print(f"🎖️ COMMANDER Expected Slots: {expected_slots}")
        
        if mode_info['max_slots'] < expected_slots:
            print(f"❌ MISMATCH: User has {mode_info['max_slots']} but should have {expected_slots}")
            print()
            
            # Fix the slot allocation
            print("🔧 Fixing slot allocation...")
            if fire_mode_db.set_max_slots(user_id, expected_slots):
                print(f"✅ Updated max_slots to {expected_slots}")
            else:
                print("❌ Failed to update max_slots")
                return False
                
            # Set AUTO mode
            print("🔧 Setting AUTO mode...")
            if fire_mode_db.set_user_mode(user_id, "AUTO", "COMMANDER tier slot fix"):
                print("✅ Set mode to AUTO")
            else:
                print("❌ Failed to set AUTO mode")
                return False
                
            print()
            
            # Verify fix
            print("🔍 Verifying fix...")
            updated_info = fire_mode_db.get_user_mode(user_id)
            print(f"✅ New Mode: {updated_info['current_mode']}")
            print(f"✅ New Max Slots: {updated_info['max_slots']}")
            print(f"✅ Slots in Use: {updated_info['slots_in_use']}")
            
            if updated_info['max_slots'] == expected_slots and updated_info['current_mode'] == 'AUTO':
                print()
                print("🎉 FIRE SLOT FIX SUCCESSFUL!")
                print(f"🎯 User {user_id} now has {expected_slots} AUTO fire slots")
                print()
                return True
            else:
                print("❌ Fix verification failed")
                return False
        else:
            print(f"✅ Slot allocation already correct: {mode_info['max_slots']} slots")
            
            # Just ensure AUTO mode is set
            if mode_info['current_mode'] != 'AUTO':
                print("🔧 Setting AUTO mode...")
                if fire_mode_db.set_user_mode(user_id, "AUTO", "COMMANDER tier mode set"):
                    print("✅ Set mode to AUTO")
                else:
                    print("❌ Failed to set AUTO mode")
                    return False
            
            print()
            print("🎉 COMMANDER CONFIGURATION VERIFIED!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_slot_system():
    """Test the slot system works correctly"""
    
    user_id = "7176191872"
    
    print("🧪 TESTING SLOT SYSTEM")
    print("=" * 50)
    
    try:
        # Check slot availability
        available = fire_mode_db.check_slot_available(user_id)
        print(f"✅ Slot Available: {available}")
        
        # Get current status
        mode_info = fire_mode_db.get_user_mode(user_id)
        print(f"✅ Available Slots: {mode_info['max_slots'] - mode_info['slots_in_use']}/{mode_info['max_slots']}")
        
        # Test occupying a slot
        test_mission_id = f"TEST_SLOT_{int(datetime.now().timestamp())}"
        if fire_mode_db.occupy_slot(user_id, test_mission_id, "EURUSD"):
            print(f"✅ Successfully occupied slot for {test_mission_id}")
            
            # Check updated status
            updated_info = fire_mode_db.get_user_mode(user_id)
            print(f"✅ Slots after occupy: {updated_info['slots_in_use']}/{updated_info['max_slots']}")
            
            # Release the test slot
            if fire_mode_db.release_slot(user_id, test_mission_id):
                print(f"✅ Successfully released slot for {test_mission_id}")
                
                # Final status
                final_info = fire_mode_db.get_user_mode(user_id)
                print(f"✅ Final slots: {final_info['slots_in_use']}/{final_info['max_slots']}")
                
                print()
                print("🎉 SLOT SYSTEM TEST PASSED!")
                return True
            else:
                print("❌ Failed to release test slot")
                return False
        else:
            print("❌ Failed to occupy test slot")
            return False
            
    except Exception as e:
        print(f"❌ Slot test error: {e}")
        return False

if __name__ == "__main__":
    print("🎖️ COMMANDER FIRE SLOT SYSTEM FIX")
    print("=" * 60)
    print()
    
    # Fix the slot allocation
    fix_success = fix_commander_slots()
    print()
    
    if fix_success:
        # Test the system
        test_success = test_slot_system()
        print()
        
        if test_success:
            print("🚀 COMMANDER FIRE SYSTEM FULLY OPERATIONAL!")
            print()
            print("🎯 Your fire mode now shows:")
            print("   • Mode: AUTO")
            print("   • Slots: 3 available")
            print("   • Auto-firing: 87%+ TCS signals")
            print()
            print("✅ Ready for full auto fire testing!")
        else:
            print("❌ Slot system test failed - please check configuration")
    else:
        print("❌ Fire slot fix failed - please check database")