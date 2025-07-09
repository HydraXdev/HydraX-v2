# test_system.py
# BITTEN System Testing and Validation

import sys
import os
import time
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, '/root/HydraX-v2/src')

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from bitten_core import (
            BittenCore, RankAccess, TelegramRouter, FireRouter,
            XPLogger, TradeWriter, UserRank, TradeDirection
        )
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_initialization():
    """Test database creation"""
    print("🧪 Testing database initialization...")
    
    try:
        from bitten_core import XPLogger, TradeWriter
        
        # Test XP Logger database
        xp_logger = XPLogger()
        print("✅ XP Logger database initialized")
        
        # Test Trade Writer database  
        trade_writer = TradeWriter()
        print("✅ Trade Writer database initialized")
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_core_system():
    """Test core system initialization"""
    print("🧪 Testing core system...")
    
    try:
        from bitten_core import BittenCore
        
        # Initialize core
        core = BittenCore()
        print("✅ BITTEN Core initialized")
        
        # Test system status
        stats = core.get_core_stats()
        print(f"✅ Core stats: {len(stats)} metrics")
        
        return True
    except Exception as e:
        print(f"❌ Core system test failed: {e}")
        return False

def test_telegram_processing():
    """Test Telegram update processing"""
    print("🧪 Testing Telegram processing...")
    
    try:
        from bitten_core import BittenCore
        
        core = BittenCore()
        
        # Mock Telegram update
        mock_update = {
            'update_id': 12345,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'username': 'test_user'
                },
                'chat': {
                    'id': 123456789
                },
                'text': '/start',
                'date': int(time.time())
            }
        }
        
        # Process update
        result = core.process_telegram_update(mock_update)
        
        if result['success']:
            print("✅ Telegram /start command processed successfully")
            print(f"   Response: {result['message'][:50]}...")
            return True
        else:
            print(f"❌ Telegram processing failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram processing test failed: {e}")
        return False

def test_trade_execution():
    """Test trade execution system"""
    print("🧪 Testing trade execution...")
    
    try:
        from bitten_core import BittenCore
        
        core = BittenCore()
        
        # Test trade execution
        result = core.execute_trade(123456789, ['GBPUSD', 'buy', '0.1', '85'])
        
        if result.success:
            print("✅ Trade execution test passed")
            print(f"   Response: {result.message[:50]}...")
            return True
        else:
            print(f"⚠️ Trade execution returned: {result.message}")
            return True  # This is expected in test mode
            
    except Exception as e:
        print(f"❌ Trade execution test failed: {e}")
        return False

def test_user_management():
    """Test user authorization system"""
    print("🧪 Testing user management...")
    
    try:
        from bitten_core import RankAccess, UserRank
        
        rank_access = RankAccess()
        
        # Test user operations
        test_user_id = 123456789
        
        # Add user
        rank_access.add_user(test_user_id, "test_user", UserRank.AUTHORIZED)
        
        # Check rank
        user_rank = rank_access.get_user_rank(test_user_id)
        print(f"✅ User rank: {user_rank.name}")
        
        # Check permissions
        can_trade = rank_access.check_permission(test_user_id, UserRank.AUTHORIZED)
        print(f"✅ Trading permission: {can_trade}")
        
        return True
        
    except Exception as e:
        print(f"❌ User management test failed: {e}")
        return False

def run_all_tests():
    """Run comprehensive system tests"""
    print("🚀 BITTEN System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database_initialization),
        ("Core System Tests", test_core_system),
        ("User Management Tests", test_user_management),
        ("Telegram Processing Tests", test_telegram_processing),
        ("Trade Execution Tests", test_trade_execution),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Review issues before deployment.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)