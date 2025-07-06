#!/usr/bin/env python3
"""
Test the BITTEN Onboarding System
Zero-friction experience for everyone from newbies to grandmas
"""

import asyncio
import json
from src.bitten_core.onboarding import OnboardingOrchestrator

async def test_onboarding():
    """Test the complete onboarding flow"""
    
    print("🎮 BITTEN Onboarding Test Suite")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = OnboardingOrchestrator(hud_webapp_url="https://bitten.trading")
    
    # Test user data
    test_user_id = "test_user_123"
    test_telegram_id = 123456789
    
    # Start onboarding
    print("\n1️⃣ Starting onboarding...")
    message, keyboard = await orchestrator.start_onboarding(
        user_id=test_user_id,
        telegram_id=test_telegram_id,
        variant="standard"
    )
    
    print(f"Message: {message[:100]}...")
    print(f"Keyboard: {json.dumps(keyboard, indent=2)}")
    
    # Simulate user answering first question (has experience)
    print("\n2️⃣ User says they have trading experience...")
    message, keyboard = await orchestrator.process_user_input(
        user_id=test_user_id,
        input_type='callback',
        input_data='yes'
    )
    
    print(f"Message: {message[:100]}...")
    print(f"Current state: {orchestrator.session_manager._sessions.get(test_user_id).current_state if test_user_id in orchestrator.session_manager._sessions else 'Unknown'}")
    
    # Continue through a few more states
    print("\n3️⃣ User says they heard from a friend...")
    message, keyboard = await orchestrator.process_user_input(
        user_id=test_user_id,
        input_type='callback',
        input_data='friend'
    )
    
    print(f"Message: {message[:100]}...")
    
    # Test callsign creation
    print("\n4️⃣ Testing callsign validation...")
    
    # Test invalid callsign
    message, keyboard = await orchestrator.process_user_input(
        user_id=test_user_id,
        input_type='text',
        input_data='a'  # Too short
    )
    print(f"Invalid callsign response: {message}")
    
    # Test valid callsign
    message, keyboard = await orchestrator.process_user_input(
        user_id=test_user_id,
        input_type='text',
        input_data='Eagle007'
    )
    print(f"Valid callsign response: {message[:100]}...")
    
    # Check session data
    session = await orchestrator.session_manager.load_session(test_user_id)
    if session:
        print(f"\n📊 Session Data:")
        print(f"- Current State: {session.current_state}")
        print(f"- Callsign: {session.callsign}")
        print(f"- Has Experience: {session.has_experience}")
        print(f"- Progress: {len(session.completed_states)}/{len([s for s in orchestrator.state_transitions])}")
    
    print("\n✅ Onboarding test complete!")

if __name__ == "__main__":
    asyncio.run(test_onboarding())