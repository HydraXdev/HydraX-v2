#!/usr/bin/env python3
"""
BITTEN Psychological Warfare System Demonstration
Shows how the complete psychological system works in practice
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Mock database for demo
class MockDB:
    def __init__(self):
        self.data = {}
    
    async def fetch_one(self, query: str, params: tuple = ()):
        return None
    
    async def fetch_all(self, query: str, params: tuple = ()):
        return []
    
    async def execute(self, query: str, params: tuple = ()):
        pass

# Mock lockout system
class MockLockoutSystem:
    async def apply_lockout(self, user_id: str, minutes: int, reason: str):
        return {"lockout_applied": True, "duration": minutes, "reason": reason}

async def demonstrate_psychological_warfare():
    """
    Demonstrate the complete BITTEN psychological warfare system
    """
    
    print("🐍 BITTEN PSYCHOLOGICAL WARFARE SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Initialize mock systems
    db = MockDB()
    lockout = MockLockoutSystem()
    
    # Import and initialize the psychological system
    from src.bitten_core.psychology.bitten_psychological_integration import BittenPsychologicalSystem
    
    psych_system = BittenPsychologicalSystem(db, None, lockout)
    
    # Demo user
    user_id = "demo_user_123"
    username = "TraderMike"
    
    print(f"\n🎯 PHASE 1: ONBOARDING - User {username} enters BITTEN")
    print("-" * 40)
    
    # Demonstrate onboarding
    onboarding_result = await psych_system.process_user_onboarding(user_id, username)
    
    print("✅ Norman's Onboarding Sequence:")
    if onboarding_result["success"]:
        sequence = onboarding_result["onboarding_sequence"]
        for i, message in enumerate(sequence["messages"]):
            print(f"   Message {i+1}: {message['text'][:100]}...")
            if message.get("reply_markup"):
                print("   [Interactive buttons included]")
    
    print("\n🎖️ First Mission Assigned:")
    if onboarding_result["success"]:
        mission = onboarding_result["first_mission"]
        print(f"   Title: {mission['title']}")
        print(f"   Tier: {mission['tier']}")
    
    print(f"\n⚔️ PHASE 2: TRADING EVENT PROCESSING")
    print("-" * 40)
    
    # Simulate various trading events
    trading_events = [
        {
            "type": "trade_placed",
            "data": {
                "symbol": "EURUSD",
                "position_size": 0.02,  # 2x normal size - greed trigger
                "stop_loss": 1.1850,
                "take_profit": 1.1950,
                "message": "This is an exciting trade opportunity!"
            }
        },
        {
            "type": "loss_occurred", 
            "data": {
                "symbol": "EURUSD",
                "loss_amount": 100,
                "consecutive_losses": 2,  # Revenge trigger
                "trade_within_minutes_of_loss": 5,
                "message": "I need to win this back immediately"
            }
        },
        {
            "type": "mission_progress",
            "data": {
                "signals_observed": 3,
                "no_trades_placed": True,
                "notes_taken": False,
                "message": "I'm watching signals but getting impatient"
            }
        }
    ]
    
    for i, event in enumerate(trading_events):
        print(f"\n📊 Event {i+1}: {event['type']}")
        
        result = await psych_system.process_trading_event(
            user_id, 
            event["type"], 
            event["data"]
        )
        
        if result["success"]:
            results = result["results"]
            
            # Show emotion analysis
            if results["emotion_analysis"]:
                emotion_result = results["emotion_analysis"]
                print(f"   🧠 Emotion Detected: {emotion_result['emotion']}")
                print(f"   ⚡ Protocol Applied: {emotion_result['protocol']}")
                if emotion_result["lockout_applied"]:
                    print(f"   🔒 Lockout: {emotion_result['lockout_minutes']} minutes")
            
            # Show mission progress
            if results["mission_progress"]:
                mission_result = results["mission_progress"]
                if mission_result.get("mission_completed"):
                    print(f"   🏆 Mission Completed! Reward: {mission_result['reward']} XP")
                else:
                    print(f"   📈 Mission Progress: {mission_result.get('progress', 0)}%")
            
            # Show interventions
            if results["interventions"]:
                for intervention in results["interventions"]:
                    print(f"   🚨 Emergency Mission: {intervention['title']}")
            
            # Show soul filter results
            if results["soul_filter_check"]:
                soul_check = results["soul_filter_check"]
                print(f"   🛡️ Message Alignment: {soul_check['alignment'].value}")
                if "improved_message" in results:
                    print(f"   ✏️ Improved: {results['improved_message'][:50]}...")
        
        # Show any interventions sent
        if user_id in psych_system.active_interventions:
            interventions = psych_system.active_interventions[user_id]
            if interventions:
                latest = interventions[-1]
                print(f"   💬 {latest['personality']}: {latest['message'][:80]}...")
    
    print(f"\n🔍 PHASE 3: PSYCHOLOGICAL STATE ANALYSIS")
    print("-" * 40)
    
    # Show user's psychological state
    psych_state = await psych_system.get_user_psychological_state(user_id)
    
    print("📊 Psychological Profile:")
    print(f"   Health Score: {psych_state.get('psychological_health_score', 'N/A')}/100")
    print(f"   Recent Emotions: {len(psych_state.get('recent_emotions', []))} events")
    print(f"   Education Progress: {len(psych_state.get('education_progress', []))} categories")
    
    if psych_state.get("current_mission"):
        mission = psych_state["current_mission"]
        print(f"   Active Mission: {mission.get('mission_name', 'Unknown')}")
    
    print(f"\n🛡️ PHASE 4: SOUL FILTER VALIDATION")
    print("-" * 40)
    
    # Test various features/messages against the soul filter
    test_features = [
        {
            "description": "Add cute mascot animations to make trading more fun and entertaining",
            "config": {"entertainment_value": "high", "difficulty": "easy"}
        },
        {
            "description": "Create tactical mission briefings that replace trading emotions with military protocols",
            "config": {"psychological_goal": "emotion_replacement", "military_theme": True}
        },
        {
            "description": "Guaranteed profit signals with 100% win rate for easy money",
            "config": {"guarantee": "100_percent", "risk": "none"}
        }
    ]
    
    for i, feature in enumerate(test_features):
        print(f"\n🧪 Feature Test {i+1}:")
        print(f"   Description: {feature['description'][:60]}...")
        
        alignment = psych_system.validate_feature_alignment(
            feature["description"],
            feature["config"]
        )
        
        print(f"   🎯 Alignment: {alignment['alignment'].value}")
        print(f"   📊 Score: {alignment['score']}/100")
        
        if alignment["poison_detected"]:
            print("   ☠️ POISON DETECTED - Feature rejected")
        elif alignment["recommendations"]:
            print(f"   💡 Recommendations: {len(alignment['recommendations'])} suggestions")
    
    print(f"\n🎖️ PHASE 5: MISSION BRIEFING DEMONSTRATION")
    print("-" * 40)
    
    # Show a proper mission briefing
    briefing = await psych_system.mission_system.get_mission_briefing(user_id, "first_blood")
    
    if briefing["success"]:
        print("📋 Mission Briefing Example:")
        print(briefing["briefing"])
        
        personalization = briefing.get("personalization", "")
        if personalization:
            print(f"🎯 Personal Note: {personalization}")
    
    print(f"\n✅ DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("🐍 BITTEN Psychological Warfare System:")
    print("   ✅ Onboarding with Norman's story")
    print("   ✅ Emotion detection and replacement")
    print("   ✅ Tactical mission system")
    print("   ✅ Soul filter protection")
    print("   ✅ Personality-based interventions")
    print("   ✅ Progressive psychological transformation")
    print("\n🎯 Ready for integration with production bot systems!")

def demonstrate_soul_filter():
    """
    Demonstrate the BITTEN Soul Filter in action
    """
    from src.bitten_core.psychology.bitten_soul_filter import soul_filter
    
    print("\n🛡️ BITTEN SOUL FILTER DEMONSTRATION")
    print("=" * 50)
    
    # Test messages
    test_messages = [
        ("This exciting trade opportunity will be fun and profitable!", None),
        ("Execute tactical retreat protocol. Emotion compromises mission success.", "DRILL"),
        ("Get rich quick with our guaranteed trading system!", None),
        ("Discipline separates soldiers from casualties. Follow the protocol.", "DRILL"),
        ("This adorable mascot will make trading cute and enjoyable!", None)
    ]
    
    for message, personality in test_messages:
        print(f"\n📝 Testing: '{message[:40]}...'")
        
        context = {"personality": personality} if personality else {}
        result = soul_filter.evaluate_message(message, context)
        
        print(f"   Alignment: {result['alignment'].value}")
        print(f"   Score: {result.get('score', 'N/A')}")
        
        if result.get("suggested_replacements"):
            print("   Suggested improvements:")
            for old, new in result["suggested_replacements"].items():
                print(f"     '{old}' → '{new}'")
        
        if result["alignment"].value in ["poison", "corrupted"]:
            improved = message
            for old_word, new_word in result["suggested_replacements"].items():
                improved = improved.replace(old_word, new_word)
            print(f"   ✅ Improved: '{improved[:60]}...'")

if __name__ == "__main__":
    print("🚀 Starting BITTEN Psychological Warfare System Demo...")
    
    # Run the soul filter demo first (synchronous)
    demonstrate_soul_filter()
    
    # Run the main async demo
    asyncio.run(demonstrate_psychological_warfare())