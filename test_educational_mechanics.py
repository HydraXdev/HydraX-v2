#!/usr/bin/env python3
"""Test script to demonstrate educational game mechanics in fire_router.py"""

import sys
sys.path.append('/root/HydraX-v2/src')

from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode
from datetime import datetime

def test_educational_mechanics():
    """Test the new educational mechanics"""
    
    # Initialize router
    router = FireRouter()
    
    # Test user ID
    user_id = 12345
    
    print("🎮 TESTING EDUCATIONAL GAME MECHANICS\n")
    print("=" * 50)
    
    # Test 1: Tactical Recovery Period (Cooldown as game mechanic)
    print("\n1️⃣ TEST: Tactical Recovery Period")
    print("-" * 30)
    
    # Simulate a recent trade
    router.last_shot_time[user_id] = datetime.now()
    
    # Try to trade immediately (should trigger recovery)
    trade_request = TradeRequest(
        user_id=user_id,
        symbol="GBPUSD",
        direction=TradeDirection.BUY,
        volume=0.1,
        tcs_score=80,
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    result = router.execute_trade(trade_request)
    print(f"Result: {result.message}")
    
    # Test 2: Recovery Mini-Game
    print("\n\n2️⃣ TEST: Recovery Mini-Game")
    print("-" * 30)
    
    # Try to complete the mini-game with wrong answer
    game_result = router.complete_recovery_game(user_id, "wrong_answer")
    print(f"Wrong answer result:\n{game_result['message']}")
    
    # Try with correct answer (would need to know the actual answer)
    # This is just for demonstration
    
    # Test 3: Low Performance Support (Educational intervention as squad support)
    print("\n\n3️⃣ TEST: Squad Support for Low Performance")
    print("-" * 30)
    
    # Simulate poor performance
    router.user_performance[user_id] = {
        'total_trades': 10,
        'wins': 2,
        'losses': 8,
        'win_rate': 0.2,
        'recent_trades': [],
        'recent_losses': 4,
        'avg_tcs': 65,
        'education_level': 1,
        'achievements': []
    }
    
    # Clear cooldown for this test
    router.last_shot_time.pop(user_id, None)
    
    # Try low TCS trade with poor performance
    low_tcs_trade = TradeRequest(
        user_id=user_id,
        symbol="EURUSD",
        direction=TradeDirection.SELL,
        volume=0.1,
        tcs_score=70,
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    result = router.execute_trade(low_tcs_trade)
    print(f"Low TCS with poor performance:\n{result.message}")
    
    # Test 4: Dynamic Difficulty Adjustment (Stealth Education)
    print("\n\n4️⃣ TEST: Dynamic Difficulty (Stealth Education)")
    print("-" * 30)
    
    # The system silently adjusts TCS requirements based on performance
    # This happens behind the scenes - users don't know about it
    
    difficulty = router.education_system.calculate_difficulty_adjustment(
        user_id, router.user_performance[user_id]
    )
    print(f"Difficulty adjustment: {difficulty['modifier']}x")
    print(f"Applied silently: {difficulty['applied_silently']}")
    print("(User doesn't see this - requirements are secretly adjusted)")
    
    # Test 5: Successful Trade with Tactical Debrief
    print("\n\n5️⃣ TEST: Successful Trade with Educational Debrief")
    print("-" * 30)
    
    # Simulate better performance
    router.user_performance[user_id] = {
        'total_trades': 20,
        'wins': 14,
        'losses': 6,
        'win_rate': 0.7,
        'recent_trades': [],
        'recent_losses': 0,
        'avg_tcs': 82,
        'education_level': 3,
        'achievements': ['first_blood', 'discipline']
    }
    
    # High confidence trade
    good_trade = TradeRequest(
        user_id=user_id,
        symbol="GBPJPY",
        direction=TradeDirection.BUY,
        volume=0.1,
        tcs_score=88,
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    # Mock successful execution
    router.execution_stats['total_trades'] = 100
    router.execution_stats['successful_trades'] = 75
    
    # This would normally execute, but in test mode we'll simulate
    print("Simulated successful trade with educational debrief:")
    print("📍 **Tactical Analysis:** High-confidence entry executed perfectly")
    print("🎯 Current win rate maintaining tactical advantage")
    print("💡 **Squad Tip:** Your stop loss is your friend, not your enemy")
    print("\n🏆 **ACHIEVEMENTS UNLOCKED:**")
    print("🏅 High Roller: Average TCS > 85")
    
    # Test 6: Mission Briefing with Tactical Intel
    print("\n\n6️⃣ TEST: Pre-Trade Mission Briefing")
    print("-" * 30)
    
    # Generate mission briefing
    user_profile = router._build_user_profile(user_id)
    performance = router._get_user_performance(user_id)
    
    briefing = router.education_system.generate_mission_briefing(
        good_trade, user_profile, performance
    )
    
    if briefing['intel']:
        print("📋 **MISSION BRIEFING**")
        for intel in briefing['intel']:
            print(f"  • {intel}")
    
    print("\n" + "=" * 50)
    print("\n✅ Educational game mechanics demonstration complete!")
    print("\nKey Features Demonstrated:")
    print("• Cooldowns feel like tactical recovery periods")
    print("• Mini-games during downtime teach concepts")
    print("• Squad support instead of warnings")
    print("• Dynamic difficulty adjusts silently")
    print("• Educational content disguised as game feedback")

if __name__ == "__main__":
    test_educational_mechanics()