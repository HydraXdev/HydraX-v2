#!/usr/bin/env python3
"""
Test Bot Control System
Demonstrates disclaimer management and bot toggle functionality
"""

import asyncio
from src.bitten_core import BittenCore, TelegramUpdate

async def test_bot_controls():
    """Test bot control system functionality"""
    
    print("🤖 BITTEN Bot Control System Test")
    print("=" * 50)
    
    # Initialize core
    core = BittenCore()
    print("✅ BITTEN Core initialized with bot controls")
    
    # Test user ID
    test_user_id = 12345
    test_username = "test_trader"
    
    # Simulate /disclaimer command
    print("\n📄 Testing /disclaimer command...")
    disclaimer_update = {
        'update_id': 1,
        'message': {
            'message_id': 1,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/disclaimer',
            'date': 1234567890
        }
    }
    
    result = core.process_telegram_update(disclaimer_update)
    print(f"Result: {result['message'][:100]}...")
    
    # Simulate /settings command (before accepting disclaimer)
    print("\n⚙️ Testing /settings command (no consent)...")
    settings_update = {
        'update_id': 2,
        'message': {
            'message_id': 2,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/settings',
            'date': 1234567891
        }
    }
    
    result = core.process_telegram_update(settings_update)
    print(f"Result: {result['message']}")
    
    # Accept disclaimer
    print("\n✅ Accepting disclaimer...")
    preferences = {
        'bots_enabled': True,
        'immersion_level': 'moderate'
    }
    disclaimer_result = core.bot_control_integration.handle_onboarding_disclaimer(
        test_user_id, True, preferences
    )
    print(f"Result: {disclaimer_result['message']}")
    
    # Test /bots command
    print("\n🤖 Testing /bots command...")
    bots_update = {
        'update_id': 3,
        'message': {
            'message_id': 3,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/bots',
            'date': 1234567892
        }
    }
    
    result = core.process_telegram_update(bots_update)
    print(f"Result: {result['message'][:200]}...")
    
    # Test /toggle command
    print("\n🔧 Testing /toggle DrillBot...")
    toggle_update = {
        'update_id': 4,
        'message': {
            'message_id': 4,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/toggle DrillBot',
            'date': 1234567893
        }
    }
    
    result = core.process_telegram_update(toggle_update)
    print(f"Result: {result['message']}")
    
    # Test /immersion command
    print("\n🎮 Testing /immersion minimal...")
    immersion_update = {
        'update_id': 5,
        'message': {
            'message_id': 5,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/immersion minimal',
            'date': 1234567894
        }
    }
    
    result = core.process_telegram_update(immersion_update)
    print(f"Result: {result['message']}")
    
    # Test /status with bot status
    print("\n📊 Testing /status with bot status...")
    status_update = {
        'update_id': 6,
        'message': {
            'message_id': 6,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/status',
            'date': 1234567895
        }
    }
    
    result = core.process_telegram_update(status_update)
    bot_status_lines = [line for line in result['message'].split('\n') if '🤖 Bot Status:' in line]
    if bot_status_lines:
        print(f"Bot status line: {bot_status_lines[0]}")
    
    # Test bot message filtering
    print("\n📨 Testing bot message filtering...")
    
    # Enable bots
    core.bot_control_integration.disclaimer_manager.toggle_all_bots(str(test_user_id), True)
    
    # Test bot message when enabled
    bot_msg = core.send_bot_message(test_user_id, 'DrillBot', 'Get ready for trading, soldier!')
    print(f"Bot message (enabled): {bot_msg}")
    
    # Disable bots
    core.bot_control_integration.disclaimer_manager.toggle_all_bots(str(test_user_id), False)
    
    # Test bot message when disabled
    bot_msg = core.send_bot_message(test_user_id, 'DrillBot', 'Get ready for trading, soldier!')
    print(f"Bot message (disabled): {bot_msg}")
    
    # Test /settings with full preferences
    print("\n⚙️ Testing /settings with full preferences...")
    result = core.process_telegram_update({
        'update_id': 7,
        'message': {
            'message_id': 7,
            'from': {'id': test_user_id, 'username': test_username},
            'chat': {'id': test_user_id},
            'text': '/settings',
            'date': 1234567896
        }
    })
    print(f"Settings sections: {result['message'].count('**')//2} sections found")
    
    print("\n✅ Bot control system test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_bot_controls())