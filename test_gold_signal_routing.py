#!/usr/bin/env python3
"""Test XAUUSD signal routing to offshore users only"""

import sys
import json
from datetime import datetime
sys.path.append('/root/HydraX-v2')

from src.bitten_core.bitten_core import BittenCore
from src.bitten_core.user_registry_manager import get_user_registry_manager

def test_gold_signal_routing():
    """Test XAUUSD signal delivery to offshore users"""
    
    print("🧪 Testing GOLD Signal Routing")
    print("=" * 60)
    
    # Initialize BittenCore
    core = BittenCore()
    
    # Create a mock production bot for testing
    class MockProductionBot:
        def __init__(self):
            self.dm_signals_sent = []
            self.group_signals_sent = []
            
        def send_dm_signal(self, telegram_id, signal_text, parse_mode="MarkdownV2"):
            print(f"\n📨 DM Signal sent to {telegram_id}:")
            print("-" * 40)
            print(signal_text)
            print("-" * 40)
            self.dm_signals_sent.append({
                'telegram_id': telegram_id,
                'signal_text': signal_text
            })
            return True
            
        def send_adaptive_response(self, chat_id, message_text, user_tier, user_action):
            print(f"\n📡 Group Signal to {chat_id}:")
            print(message_text)
            self.group_signals_sent.append({
                'chat_id': chat_id,
                'message_text': message_text
            })
    
    # Set mock bot
    mock_bot = MockProductionBot()
    core.production_bot = mock_bot
    
    # Update test users to be ready for fire
    registry = get_user_registry_manager()
    registry.update_user_status("111111111", "ready_for_fire")
    registry.update_user_status("222222222", "ready_for_fire")
    registry.update_user_status("7176191872", "ready_for_fire")
    
    # Set the registry on core
    core.user_registry = registry
    
    # Debug: check ready users
    ready_users = registry.get_all_ready_users()
    print(f"\nReady users: {list(ready_users.keys())}")
    
    # Test signal 1: XAUUSD (should go private)
    print("\n🏆 Test 1: XAUUSD Signal")
    print("-" * 60)
    
    gold_signal = {
        'signal_id': 'ELITE_XAUUSD_001',
        'symbol': 'XAUUSD',
        'direction': 'BUY',
        'entry_price': 2411.50,
        'stop_loss': 2405.00,
        'take_profit': 2424.50,
        'risk_reward': 2.0,
        'signal_type': 'PRECISION_STRIKE',
        'confidence': 85,
        'pattern': 'LIQUIDITY_SWEEP_REVERSAL',
        'citadel_score': 8.5,
        'expires_at': '2025-08-01T23:00:00Z'
    }
    
    result1 = core._deliver_signal_to_users(gold_signal)
    print(f"\nDelivery Result:")
    print(json.dumps(result1, indent=2))
    
    # Test signal 2: EURUSD (should go to group)
    print("\n\n💶 Test 2: EURUSD Signal")
    print("-" * 60)
    
    eur_signal = {
        'signal_id': 'ELITE_EURUSD_002',
        'symbol': 'EURUSD',
        'direction': 'SELL',
        'entry_price': 1.1540,
        'stop_loss': 1.1560,
        'take_profit': 1.1500,
        'risk_reward': 2.0,
        'signal_type': 'RAPID_ASSAULT',
        'confidence': 78,
        'pattern': 'ORDER_BLOCK_BOUNCE',
        'citadel_score': 7.2,
        'expires_at': '2025-08-01T23:00:00Z'
    }
    
    # Clear sent signals
    mock_bot.dm_signals_sent = []
    mock_bot.group_signals_sent = []
    
    result2 = core._deliver_signal_to_users(eur_signal)
    
    # Summary
    print("\n\n📊 Test Summary")
    print("=" * 60)
    print(f"XAUUSD Signal:")
    print(f"  - Delivered to: {result1.get('total_delivered', 0)} offshore users")
    print(f"  - Public broadcast: {result1.get('public_broadcast', True)}")
    print(f"  - Total XP awarded: {result1.get('total_xp_awarded', 0)}")
    print(f"  - DM signals sent: {len(mock_bot.dm_signals_sent)}")
    
    print(f"\nEURUSD Signal:")
    print(f"  - Group signals sent: {len(mock_bot.group_signals_sent)}")
    print(f"  - DM signals sent: {len(mock_bot.dm_signals_sent)} (should be 0)")
    
    # Check user eligibility
    print("\n\n👥 User Eligibility Check")
    print("=" * 60)
    registry = get_user_registry_manager()
    
    test_users = ['111111111', '222222222', '7176191872']
    for user_id in test_users:
        info = registry.get_user_info(user_id)
        if info:
            region = info.get('user_region', 'US')
            opt_in = info.get('offshore_opt_in', False)
            eligible = region != 'US' and opt_in
            print(f"User {user_id}: Region={region}, OptIn={opt_in}, Eligible={'✅' if eligible else '❌'}")

if __name__ == "__main__":
    test_gold_signal_routing()