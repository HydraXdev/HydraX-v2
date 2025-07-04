#!/usr/bin/env python3
"""
Test the Tactical Terms of Engagement Disclaimer
"""

from src.bitten_core import BittenCore

def test_tactical_disclaimer():
    """Test the new tactical disclaimer"""
    
    print("🛡️ TESTING TACTICAL TERMS OF ENGAGEMENT")
    print("=" * 50)
    
    # Initialize core
    core = BittenCore()
    
    # Test user
    test_user_id = 99999
    
    # Test /disclaimer command
    print("\n📄 Fetching Terms of Tactical Engagement...")
    disclaimer_update = {
        'update_id': 1,
        'message': {
            'message_id': 1,
            'from': {'id': test_user_id, 'username': 'tactical_tester'},
            'chat': {'id': test_user_id},
            'text': '/disclaimer',
            'date': 1234567890
        }
    }
    
    result = core.process_telegram_update(disclaimer_update)
    
    # Print the disclaimer sections
    lines = result['message'].split('\n')
    
    print("\n🔒 DISCLAIMER SECTIONS FOUND:")
    for line in lines:
        if line.startswith('##'):
            print(f"  • {line}")
    
    print("\n✅ FINAL WORD:")
    capturing = False
    for line in lines:
        if line.startswith('## ☑️ Final Word'):
            capturing = True
            continue
        if capturing and line.strip():
            print(f"  {line}")
    
    # Test acceptance
    print("\n🎯 Testing acceptance flow...")
    preferences = {
        'bots_enabled': True,
        'immersion_level': 'full'
    }
    
    accept_result = core.bot_control_integration.handle_onboarding_disclaimer(
        test_user_id, True, preferences
    )
    
    print(f"\nAcceptance Result:\n{accept_result['message']}")
    
    print("\n✅ Tactical Terms of Engagement test complete!")
    print("Stay tactical, soldier. 🎯")

if __name__ == "__main__":
    test_tactical_disclaimer()