#!/usr/bin/env python3
"""
🎯 TEST MISSED WIN ANALYSIS SYSTEM
Test the enhanced ghost tracking system with missed win analysis
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Add src to path for imports
sys.path.insert(0, '/root/HydraX-v2/src')
sys.path.insert(0, '/root/HydraX-v2')

def create_test_mission_files():
    """Create test mission files for missed win analysis"""
    print("📁 Creating test mission files...")
    
    missions_dir = "/root/HydraX-v2/missions"
    os.makedirs(missions_dir, exist_ok=True)
    
    # Current time for testing
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    # Create expired missions with different scenarios
    test_missions = [
        {
            "mission_id": "test_mission_001",
            "user_id": "test_user_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": 1.0900,
            "take_profit": 1.0920,  # 20 pips TP
            "stop_loss": 1.0880,    # 20 pips SL
            "tcs_score": 85,
            "status": "pending",
            "created_timestamp": now_ts - 7200,  # 2 hours ago
            "expires_timestamp": now_ts - 3600   # Expired 1 hour ago
        },
        {
            "mission_id": "test_mission_002", 
            "user_id": "test_user_002",
            "symbol": "GBPUSD",
            "direction": "SELL",
            "entry_price": 1.2700,
            "take_profit": 1.2680,  # 20 pips TP
            "stop_loss": 1.2720,    # 20 pips SL
            "tcs_score": 78,
            "status": "pending",
            "created_timestamp": now_ts - 5400,  # 1.5 hours ago
            "expires_timestamp": now_ts - 1800   # Expired 30 mins ago
        },
        {
            "mission_id": "test_mission_003",
            "user_id": "test_user_003", 
            "symbol": "USDJPY",
            "direction": "BUY",
            "entry_price": 150.00,
            "take_profit": 150.20,  # 20 pips TP
            "stop_loss": 149.80,    # 20 pips SL
            "tcs_score": 72,
            "status": "pending",
            "created_timestamp": now_ts - 10800, # 3 hours ago
            "expires_timestamp": now_ts - 900    # Expired 15 mins ago
        }
    ]
    
    # Save test missions
    for mission in test_missions:
        filename = f"{mission['mission_id']}.json"
        filepath = os.path.join(missions_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(mission, f, indent=2)
        
        print(f"   ✅ Created {filename}")
    
    print(f"📁 Created {len(test_missions)} test mission files")
    return test_missions

def test_enhanced_ghost_tracker():
    """Test the enhanced ghost tracker missed win analysis"""
    print("\n👻 Testing Enhanced Ghost Tracker...")
    
    try:
        from bitten_core.enhanced_ghost_tracker import enhanced_ghost_tracker
        
        # Test missed win analysis
        print("🔍 Running missed win analysis...")
        missed_results = enhanced_ghost_tracker.analyze_missed_winners(24)
        
        print(f"✅ Analyzed {len(missed_results)} expired missions")
        
        for result in missed_results:
            print(f"   📊 {result.symbol} {result.direction} TCS:{result.tcs_score}% → {result.result}")
            if result.tp_hit:
                print(f"      💰 TP would have been hit at {result.price_reached}")
        
        # Test summary
        print("\n📈 Getting missed win summary...")
        summary = enhanced_ghost_tracker.get_missed_win_summary(24)
        
        print(f"   📊 Total expired: {summary['total_expired']}")
        print(f"   💰 Unfired wins: {summary['unfired_wins']}")
        print(f"   📉 Unfired losses: {summary['unfired_losses']}")
        print(f"   📊 Missed win rate: {summary['missed_win_rate']:.1f}%")
        
        if summary.get('top_missed_tcs'):
            top = summary['top_missed_tcs']
            print(f"   🎯 Top missed: {top['symbol']} {top['direction']} (TCS {top['tcs_score']}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Ghost Tracker test failed: {e}")
        return False

def test_live_performance_tracker():
    """Test the live performance tracker true win rate"""
    print("\n📊 Testing Live Performance Tracker...")
    
    try:
        from bitten_core.live_performance_tracker import live_tracker
        
        # Test true win rate calculation
        print("🎯 Calculating true win rate...")
        true_stats = live_tracker.get_true_win_rate(24, include_unfired=True)
        
        if 'error' in true_stats:
            print(f"❌ True win rate calculation failed: {true_stats['error']}")
            return False
        
        print(f"   📊 Period: {true_stats['period_hours']} hours")
        print(f"   🔥 Fired signals: {true_stats['fired_signals']['total']} ({true_stats['fired_signals']['win_rate']:.1f}% win rate)")
        print(f"   👻 Unfired signals: {true_stats['unfired_signals']['total']} ({true_stats['unfired_signals']['win_rate']:.1f}% win rate)")
        print(f"   🎯 TRUE WIN RATE: {true_stats['true_performance']['true_win_rate']:.1f}%")
        
        # Test TCS breakdown
        if true_stats.get('tcs_band_breakdown'):
            print("\n🎚️ TCS Band Breakdown:")
            for tcs_range, data in true_stats['tcs_band_breakdown'].items():
                if data['combined_total'] > 0:
                    print(f"   TCS {tcs_range}%: {data['combined_win_rate']:.1f}% ({data['fired_wins']}F + {data['unfired_wins']}U)")
        
        return True
        
    except Exception as e:
        print(f"❌ Live Performance Tracker test failed: {e}")
        return False

def test_performance_commands():
    """Test the performance commands with missed wins"""
    print("\n💬 Testing Performance Commands...")
    
    try:
        from bitten_core.performance_commands import handle_missed_wins_command
        
        # Test missed wins command
        print("📊 Testing /MISSEDWINS command...")
        result = handle_missed_wins_command("/MISSEDWINS")
        
        if result.startswith("❌"):
            print(f"❌ MISSEDWINS command failed: {result}")
            return False
        
        print("✅ /MISSEDWINS command response:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        # Test with time parameter
        print("\n📊 Testing /MISSEDWINS 12 command...")
        result_12h = handle_missed_wins_command("/MISSEDWINS 12")
        print(f"✅ /MISSEDWINS 12 response length: {len(result_12h)} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance Commands test failed: {e}")
        return False

def test_database_integration():
    """Test database integration for missed wins"""
    print("\n💾 Testing Database Integration...")
    
    try:
        # Check if missed win log was created
        log_path = "/root/HydraX-v2/data/missed_win_log.json"
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            print(f"✅ Missed win log exists with {log_data['total_results']} results")
            print(f"   📅 Last updated: {log_data['last_updated']}")
            
            # Show sample results
            if log_data.get('results'):
                print("   📊 Sample results:")
                for result in log_data['results'][:3]:
                    print(f"      {result['symbol']} {result['direction']} TCS:{result['tcs_score']}% → {result['result']}")
            
            return True
        else:
            print("⚠️ Missed win log not yet created")
            return False
            
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    missions_dir = "/root/HydraX-v2/missions"
    test_missions = ["test_mission_001.json", "test_mission_002.json", "test_mission_003.json"]
    
    for mission_file in test_missions:
        filepath = os.path.join(missions_dir, mission_file)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"   🗑️ Removed {mission_file}")

def main():
    """Run comprehensive missed win analysis tests"""
    print("🎯 MISSED WIN ANALYSIS - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Test setup
    test_missions = create_test_mission_files()
    
    # Run tests
    tests = [
        ("Enhanced Ghost Tracker", test_enhanced_ghost_tracker),
        ("Live Performance Tracker", test_live_performance_tracker), 
        ("Performance Commands", test_performance_commands),
        ("Database Integration", test_database_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Missed Win Analysis System Ready!")
    else:
        print("⚠️ Some tests failed - Check logs for details")
    
    # Cleanup
    cleanup_test_files()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)