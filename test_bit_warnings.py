#!/usr/bin/env python3
"""
Test script for Bit's Low TCS Warning System
Demonstrates the warning dialog flow for trades under 76% confidence
"""

import asyncio
from datetime import datetime
from src.bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode
from src.bitten_core.bit_warnings import BitWarningSystem, check_low_tcs_warning

def print_separator():
    print("\n" + "="*80 + "\n")

def test_warning_generation():
    """Test warning dialog generation for different TCS levels"""
    print("🧪 Testing Bit's Warning System for Low TCS Trades")
    print_separator()
    
    # Test different TCS levels
    test_cases = [
        {'tcs': 55, 'description': 'Extreme Risk (< 60%)'},
        {'tcs': 65, 'description': 'High Risk (60-69%)'},
        {'tcs': 72, 'description': 'Moderate Risk (70-75%)'},
        {'tcs': 75.5, 'description': 'Low Risk (just under 76%)'},
        {'tcs': 78, 'description': 'No Warning (above 76%)'}
    ]
    
    # Mock user profile
    user_profile = {
        'user_id': '123456',
        'tier': 'fang',
        'recent_losses': 2,
        'win_rate_7d': 0.45,
        'last_loss_time': datetime.now(),
        'trades_by_tcs': {
            '50s': {'win_rate': 0.35, 'avg_loss': -45.50},
            '60s': {'win_rate': 0.42, 'avg_loss': -38.25},
            '70s': {'win_rate': 0.58, 'avg_loss': -22.10}
        }
    }
    
    for test in test_cases:
        print(f"\n📊 Testing TCS: {test['tcs']}% - {test['description']}")
        print("-" * 60)
        
        needs_warning, dialog = check_low_tcs_warning(test['tcs'], user_profile)
        
        if needs_warning:
            print(f"⚠️ Warning Required: YES")
            print(f"Level: {dialog['level'].upper()}")
            print(f"Title: {dialog['title']}")
            print(f"\nBit says: {dialog['content']['bit_says']}")
            print(f"\nDiscipline reminder: {dialog['content']['discipline_reminder']}")
            print(f"\nRisk stats:")
            stats = dialog['content']['stats']
            for key, value in stats.items():
                print(f"  • {key}: {value}")
            print(f"\nDouble confirmation required: {dialog['require_double_confirm']}")
            print(f"Cooldown: {dialog['cooldown_seconds']}s")
        else:
            print("✅ No warning required - TCS above threshold")

def test_warning_responses():
    """Test processing different user responses to warnings"""
    print_separator()
    print("🧪 Testing User Response Processing")
    print_separator()
    
    warning_system = BitWarningSystem()
    
    # Simulate a warning scenario
    test_scenarios = [
        {
            'user_id': 'wise_trader',
            'tcs': 65,
            'actions': ['cancel', 'cancel', 'confirm_high', 'cancel_final'],
            'description': 'Wise trader who usually heeds warnings'
        },
        {
            'user_id': 'reckless_trader',
            'tcs': 58,
            'actions': ['confirm_extreme', 'override_warning', 'confirm_extreme', 'override_warning'],
            'description': 'Reckless trader who ignores warnings'
        },
        {
            'user_id': 'learning_trader',
            'tcs': 72,
            'actions': ['review', 'cancel', 'confirm_moderate', 'review'],
            'description': 'Learning trader with mixed responses'
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n👤 Testing: {scenario['description']}")
        print(f"User ID: {scenario['user_id']}")
        print("-" * 60)
        
        # Record multiple responses
        for i, action in enumerate(scenario['actions']):
            warning_level = warning_system.get_warning_level(scenario['tcs'])
            warning_system.record_confirmation_response(
                scenario['user_id'],
                scenario['tcs'],
                warning_level,
                action
            )
            print(f"Response {i+1}: {action}")
        
        # Get wisdom score
        wisdom_data = warning_system.get_user_wisdom_score(scenario['user_id'])
        print(f"\n📊 Wisdom Score: {wisdom_data['score']}%")
        print(f"🏆 Rating: {wisdom_data['rating']}")
        print(f"Total warnings: {wisdom_data['total_warnings']}")
        print(f"Warnings heeded: {wisdom_data['warnings_heeded']}")

def test_fire_router_integration():
    """Test integration with FireRouter"""
    print_separator()
    print("🧪 Testing FireRouter Integration")
    print_separator()
    
    # Create fire router instance
    router = FireRouter()
    
    # Create a low TCS trade request
    trade_request = TradeRequest(
        user_id=123456,
        symbol="GBPUSD",
        direction=TradeDirection.BUY,
        volume=0.1,
        tcs_score=68,  # Low TCS - should trigger warning
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    # Mock user profile
    router._build_user_profile = lambda user_id: {
        'user_id': str(user_id),
        'tier': 'fang',
        'account_balance': 10000,
        'total_exposure_percent': 2,
        'shots_today': 3,
        'open_positions': 1,
        'recent_losses': 1,
        'win_rate_7d': 0.55,
        'last_loss_time': None
    }
    
    print(f"📤 Submitting trade: {trade_request.symbol} {trade_request.direction.value.upper()}")
    print(f"TCS Score: {trade_request.tcs_score}%")
    
    # Execute trade (should return warning)
    result = router.execute_trade(trade_request)
    
    print(f"\n📨 Result:")
    print(f"Success: {result.success}")
    print(f"Error Code: {result.error_code}")
    if result.error_code == "LOW_TCS_WARNING":
        print(f"Warning ID: {result.trade_id}")
        print(f"\nWarning Message:")
        print("-" * 60)
        print(result.message)
        print("-" * 60)
        
        # Simulate user response
        print("\n🎮 Simulating user responses...")
        
        # Test 1: User cancels
        print("\n1️⃣ User cancels trade:")
        response = router.process_low_tcs_warning_response(
            123456,
            result.trade_id,
            'cancel'
        )
        print(response['message'])
        
        # Test 2: User confirms (new warning)
        print("\n2️⃣ User confirms trade:")
        # Need to create a new warning first
        result2 = router.execute_trade(trade_request)
        if result2.error_code == "LOW_TCS_WARNING":
            response2 = router.process_low_tcs_warning_response(
                123456,
                result2.trade_id,
                'confirm_high'
            )
            print(response2['message'])

def test_wisdom_stats():
    """Test wisdom statistics display"""
    print_separator()
    print("🧪 Testing Wisdom Statistics Display")
    print_separator()
    
    router = FireRouter()
    
    # Get stats for a user
    stats_result = router.get_user_wisdom_stats(123456)
    print(stats_result['message'])

def main():
    """Run all tests"""
    print("\n" + "🐾"*20)
    print("🐈 BIT'S LOW TCS WARNING SYSTEM TEST SUITE")
    print("🐾"*20)
    
    test_warning_generation()
    test_warning_responses()
    test_fire_router_integration()
    test_wisdom_stats()
    
    print_separator()
    print("✅ All tests completed!")
    print("\n💡 Key Features Demonstrated:")
    print("• Warning dialogs for TCS < 76%")
    print("• Different warning levels based on TCS ranges")
    print("• Yoda-style wisdom from Bit")
    print("• User response tracking and wisdom scores")
    print("• Integration with trade execution flow")
    print("• Double confirmation for high-risk trades")
    print("• Cooldown enforcement after risky trades")

if __name__ == "__main__":
    main()