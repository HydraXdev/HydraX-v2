#!/usr/bin/env python3
"""
🔧 ENGINE ENGINEER v2 - INTEGRATION TEST
Test the deployed Engine Engineer v2 systems
"""

import json
import os
import sys
from datetime import datetime

def test_original_engine_engineer():
    """Test the original Engine Engineer v2"""
    print("🔧 Testing Original Engine Engineer v2...")
    
    try:
        # Import and test the original engine
        sys.path.insert(0, '/root/HydraX-v2/core')
        from engine_engineer_v2 import EngineEngineer
        
        engineer = EngineEngineer()
        status = engineer.status()
        
        print(f"✅ Original Engine Engineer Status: {status}")
        print(f"   📊 Config Loaded: {status['config_loaded']}")
        print(f"   📄 Logs Loaded: {status['logs_loaded']}")
        print(f"   🎯 Missions Tracked: {status['missions_tracked']}")
        
        return True, engineer
        
    except Exception as e:
        print(f"❌ Original Engine Engineer Error: {e}")
        return False, None

def test_enhanced_engine_engineer():
    """Test the enhanced Engine Engineer"""
    print("\n🔧 Testing Enhanced Engine Engineer...")
    
    try:
        # Test enhanced version
        sys.path.insert(0, '/root/HydraX-v2')
        from engine_engineer_enhanced import EnhancedEngineEngineer, engineer_status, engineer_health_check
        
        engineer = EnhancedEngineEngineer()
        status = engineer.get_comprehensive_status()
        health = engineer.system_health_check()
        
        print(f"✅ Enhanced Engine Engineer Status: {status['status']}")
        print(f"   🎯 Engine Type: {status['engine_type']}")
        print(f"   📈 Missions Tracked: {status['missions_tracked']}")
        print(f"   🔗 Bridge Troll: {status.get('integrations', {}).get('bridge_troll', 'N/A')}")
        print(f"   🎯 InitSync: {status.get('integrations', {}).get('initsync', 'N/A')}")
        print(f"   🏥 System Health: {health['overall_status']}")
        
        return True, engineer
        
    except Exception as e:
        print(f"❌ Enhanced Engine Engineer Error: {e}")
        return False, None

def test_integration_modules():
    """Test integration modules"""
    print("\n🔧 Testing Integration Modules...")
    
    # Test Bridge Troll integration
    try:
        from troll_integration import troll_health
        print("✅ Bridge Troll integration available")
    except ImportError:
        print("⚠️ Bridge Troll integration not available (expected)")
        
    # Test InitSync integration
    try:
        from initsync_integration import initsync_get_user, initsync_create_user
        print("✅ InitSync integration available")
        
        # Test basic InitSync functionality
        success, session_id, data = initsync_create_user(
            telegram_id=999999999,
            user_id="test_engineer",
            tier="fang",
            platforms=["telegram"]
        )
        
        if success:
            print(f"✅ InitSync test session created: {session_id}")
        else:
            print(f"⚠️ InitSync test failed: {session_id}")
            
    except ImportError as e:
        print(f"❌ InitSync integration error: {e}")

def main():
    """Run all Engine Engineer tests"""
    print("🔧 ENGINE ENGINEER v2 - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Test original engine
    orig_success, orig_engineer = test_original_engine_engineer()
    
    # Test enhanced engine
    enhanced_success, enhanced_engineer = test_enhanced_engine_engineer()
    
    # Test integrations
    test_integration_modules()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Original Engine Engineer: {'✅ PASS' if orig_success else '❌ FAIL'}")
    print(f"Enhanced Engine Engineer: {'✅ PASS' if enhanced_success else '❌ FAIL'}")
    
    if enhanced_success:
        print("\n🌐 Enhanced Engine Engineer API Endpoints:")
        print("  GET  /engineer/status")
        print("  GET  /engineer/missions/<user_id>")
        print("  GET  /engineer/missions/expired")
        print("  GET  /engineer/missions/active")
        print("  GET  /engineer/bridge/<bridge_id>")
        print("  GET  /engineer/user/<telegram_id>")
        print("  GET  /engineer/health")
        print("  POST /engineer/restart")
        
    print("\n✅ ENGINE ENGINEER v2 DEPLOYMENT TEST COMPLETE")
    
    return orig_success and enhanced_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)