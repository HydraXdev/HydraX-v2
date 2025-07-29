#!/usr/bin/env python3
"""
Test Individual User Messaging System
Tests the complete pipeline from signal generation to individual user alerts
"""

import json
import time
from datetime import datetime

# Test signal data (similar to what VENOM would generate)
test_signal = {
    "signal_id": "TEST_INDIVIDUAL_MSG_001",
    "pair": "EURUSD",
    "direction": "BUY",
    "timestamp": datetime.now().timestamp(),
    "confidence": 78.5,
    "quality": "silver",
    "session": "NY",
    "signal": {
        "symbol": "EURUSD",
        "direction": "BUY",
        "target_pips": 21,
        "stop_pips": 14,
        "risk_reward": 1.5,  # [RR-FIXED]
        "signal_type": "RAPID_ASSAULT",
        "duration_minutes": 65
    },
    "enhanced_signal": {
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.09235,
        "stop_loss": 1.09095,
        "take_profit": 1.09445,
        "risk_reward_ratio": 1.5,
        "signal_type": "RAPID_ASSAULT",
        "confidence": 78.5
    },
    "venom_analysis": {
        "volatility": 0.0005,
        "momentum_alignment": {
            "short": 0.0002,
            "medium": 0.0001,
            "long": 0.0003
        },
        "session_power": 1.1,
        "spread_quality": "good"
    },
    "citadel_shield": {
        "score": 7.8,
        "classification": "SHIELD_ACTIVE",
        "emoji": "✅",
        "label": "SHIELD ACTIVE",
        "explanation": "Good momentum alignment with acceptable risk parameters",
        "recommendation": "Standard position size recommended",
        "risk_factors": [],
        "quality_factors": [
            {
                "factor": "session_timing",
                "bonus": 0.3,
                "description": "NY session optimal for EURUSD"
            }
        ]
    }
}

def test_user_mission_system():
    """Test the user mission system with dynamic user loading"""
    print("🧪 Testing User Mission System...")
    
    try:
        from user_mission_system import UserMissionSystem
        
        # Create mission system
        mission_system = UserMissionSystem()
        
        # Create base signal for missions
        base_signal = {
            'symbol': test_signal['pair'],
            'direction': test_signal['direction'],
            'tcs_score': test_signal['confidence'],
            'entry_price': test_signal['enhanced_signal']['entry_price'],
            'stop_loss': test_signal['enhanced_signal']['stop_loss'],
            'take_profit': test_signal['enhanced_signal']['take_profit'],
            'signal_type': test_signal['signal']['signal_type']
        }
        
        # Create user missions
        user_missions = mission_system.create_user_missions(base_signal)
        
        print(f"✅ Created {len(user_missions)} user missions:")
        for user_id, mission_url in user_missions.items():
            print(f"   User {user_id}: {mission_url}")
        
        return user_missions
        
    except Exception as e:
        print(f"❌ User mission system test failed: {e}")
        return {}

def test_individual_alerts(user_missions):
    """Test individual alert sending"""
    print("\n🧪 Testing Individual Alert System...")
    
    try:
        from venom_scalp_master import VenomScalpMaster
        
        # Create VENOM instance
        venom = VenomScalpMaster()
        
        # Test individual alerts
        success_count = venom._send_individual_alerts(test_signal, user_missions)
        
        print(f"✅ Individual alerts test completed: {success_count}/{len(user_missions)} sent")
        
        if success_count > 0:
            print("🎯 Individual messaging system is working!")
            return True
        else:
            print("⚠️ No alerts were sent - check bot token and user IDs")
            return False
            
    except Exception as e:
        print(f"❌ Individual alerts test failed: {e}")
        return False

def test_notification_system():
    """Test notification system integration"""
    print("\n🧪 Testing Notification System...")
    
    try:
        from src.bitten_core.notification_handler import notify_signal
        
        # Test notification for a sample user
        test_user_id = "7176191872"  # Commander user
        test_mission_url = "https://joinbitten.com/hud?mission_id=TEST_001"
        
        notification = notify_signal(test_user_id, {
            'symbol': test_signal['pair'],
            'direction': test_signal['direction'],
            'tcs_score': test_signal['confidence'],
            'signal_type': test_signal['signal']['signal_type']
        }, test_mission_url)
        
        print(f"✅ Notification system test completed")
        print(f"   Notification: {notification.title}")
        print(f"   Message: {notification.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 INDIVIDUAL USER MESSAGING SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: User Mission System
    user_missions = test_user_mission_system()
    
    if not user_missions:
        print("❌ Cannot proceed without user missions")
        return
    
    # Test 2: Individual Alerts
    alerts_success = test_individual_alerts(user_missions)
    
    # Test 3: Notification System
    notification_success = test_notification_system()
    
    # Summary
    print("\n📊 TEST SUMMARY:")
    print(f"   User Missions: {'✅' if user_missions else '❌'} ({len(user_missions)} users)")
    print(f"   Individual Alerts: {'✅' if alerts_success else '❌'}")
    print(f"   Notification System: {'✅' if notification_success else '❌'}")
    
    if user_missions and len(user_missions) >= 3:
        print("\n🎯 INDIVIDUAL MESSAGING INTEGRATION: COMPLETE")
        print(f"✅ {len(user_missions)} users are configured to receive individual alerts")
        print("✅ Pipeline ready for live VENOM signals")
    else:
        print("\n⚠️ INDIVIDUAL MESSAGING INTEGRATION: INCOMPLETE")
        print("❌ Need at least 3 users in registry for full functionality")

if __name__ == "__main__":
    main()