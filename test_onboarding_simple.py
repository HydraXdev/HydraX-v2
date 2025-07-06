#!/usr/bin/env python3
"""
Simple test for BITTEN Onboarding System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json

# Import directly to avoid circular imports
from src.bitten_core.onboarding.orchestrator import OnboardingOrchestrator

async def test_onboarding():
    """Test the onboarding flow"""
    
    print("🎮 BITTEN Onboarding Test")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = OnboardingOrchestrator(hud_webapp_url="https://bitten.trading")
    
    # Check if dialogue loaded
    print(f"Dialogue loaded: {len(orchestrator.dialogue) if orchestrator.dialogue else 0} sections")
    
    # Test user
    user_id = "test_123"
    telegram_id = 123456
    
    # Clear any existing session
    if hasattr(orchestrator.session_manager, '_sessions'):
        orchestrator.session_manager._sessions.pop(user_id, None)
    
    # Start onboarding
    print("\n1️⃣ Starting onboarding...")
    try:
        message, keyboard = await orchestrator.start_onboarding(
            user_id=user_id,
            telegram_id=telegram_id,
            variant="standard"
        )
        print(f"✅ Started successfully!")
        if message:
            print(f"Message preview: {message[:100]}...")
        else:
            print("⚠️ No message returned")
        if keyboard:
            print(f"Keyboard buttons: {len(keyboard.get('inline_keyboard', []))} rows")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_onboarding())