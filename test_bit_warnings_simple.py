#!/usr/bin/env python3
"""
Simple demonstration of Bit's Low TCS Warning System
Shows the warning dialogs and Bit's wisdom without full system dependencies
"""

import sys
sys.path.append('/root/HydraX-v2')

from datetime import datetime
from src.bitten_core.bit_warnings import (
    BitWarningSystem, 
    check_low_tcs_warning,
    format_warning_for_telegram,
    process_warning_response,
    WarningLevel
)

def print_separator():
    print("\n" + "="*80 + "\n")

def demonstrate_warnings():
    """Demonstrate warning generation for different TCS levels"""
    print("🐈 BIT'S LOW TCS WARNING SYSTEM DEMONSTRATION")
    print_separator()
    
    # Mock user profile with some trading history
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
        },
        'account_balance': 10000
    }
    
    # Test cases for different TCS levels
    test_cases = [
        {'tcs': 55, 'description': 'Extreme Risk (< 60%)'},
        {'tcs': 65, 'description': 'High Risk (60-69%)'},
        {'tcs': 72, 'description': 'Moderate Risk (70-75%)'},
        {'tcs': 75.5, 'description': 'Low Risk (just under 76%)'},
        {'tcs': 78, 'description': 'No Warning (above 76%)'}
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"📊 TCS: {test['tcs']}% - {test['description']}")
        print(f"{'='*60}\n")
        
        needs_warning, dialog = check_low_tcs_warning(test['tcs'], user_profile)
        
        if needs_warning:
            # Display the formatted Telegram message
            telegram_message = format_warning_for_telegram(dialog)
            print(telegram_message)
            
            # Show button options
            print("\n🔘 Available Actions:")
            for button in dialog['buttons']:
                print(f"  • {button['text']} (action: {button['action']})")
            
            # Show if double confirmation is required
            if dialog['require_double_confirm']:
                print(f"\n⚠️ DOUBLE CONFIRMATION REQUIRED")
                second_conf = dialog.get('second_confirmation', {})
                if second_conf:
                    print(f"Second message: {second_conf['message']}")
        else:
            print("✅ No warning required - TCS is above 76% threshold")

def demonstrate_wisdom_tracking():
    """Demonstrate Bit's wisdom score tracking"""
    print_separator()
    print("📊 WISDOM SCORE TRACKING DEMONSTRATION")
    print_separator()
    
    warning_system = BitWarningSystem()
    
    # Simulate different trader behaviors
    traders = [
        {
            'id': 'wise_trader',
            'name': 'Wise Trader',
            'responses': [
                (65, 'cancel'),
                (58, 'cancel_final'),
                (72, 'review'),
                (68, 'cancel'),
                (70, 'cancel')
            ]
        },
        {
            'id': 'reckless_trader',
            'name': 'Reckless Trader',
            'responses': [
                (65, 'confirm_high'),
                (58, 'override_warning'),
                (55, 'override_warning'),
                (68, 'confirm_high'),
                (60, 'override_warning')
            ]
        },
        {
            'id': 'learning_trader',
            'name': 'Learning Trader',
            'responses': [
                (65, 'cancel'),
                (72, 'confirm_moderate'),
                (68, 'review'),
                (58, 'cancel_final'),
                (74, 'confirm_low')
            ]
        }
    ]
    
    for trader in traders:
        print(f"\n👤 {trader['name']} (ID: {trader['id']})")
        print("-" * 40)
        
        # Process each response
        for tcs, action in trader['responses']:
            level = warning_system.get_warning_level(tcs)
            warning_system.record_confirmation_response(
                trader['id'], tcs, level, action
            )
            heeded = action in ['cancel', 'cancel_final', 'review']
            print(f"  TCS {tcs}% → {action} {'✅' if heeded else '❌'}")
        
        # Get wisdom score
        wisdom_data = warning_system.get_user_wisdom_score(trader['id'])
        print(f"\n  📊 Wisdom Score: {wisdom_data['score']}%")
        print(f"  🏆 Rating: {wisdom_data['rating']}")
        print(f"  📈 Stats: {wisdom_data['warnings_heeded']}/{wisdom_data['total_warnings']} warnings heeded")

def demonstrate_bit_reactions():
    """Demonstrate Bit's different reactions"""
    print_separator()
    print("🐾 BIT'S REACTIONS TO USER DECISIONS")
    print_separator()
    
    # Test different scenarios
    scenarios = [
        {
            'tcs': 55,
            'action': 'cancel',
            'description': 'User wisely cancels extreme risk trade'
        },
        {
            'tcs': 55,
            'action': 'override_warning',
            'description': 'User overrides extreme risk warning'
        },
        {
            'tcs': 68,
            'action': 'confirm_high',
            'description': 'User confirms high risk trade'
        },
        {
            'tcs': 74,
            'action': 'review',
            'description': 'User reviews setup on moderate risk'
        },
        {
            'tcs': 75,
            'action': 'confirm_low',
            'description': 'User proceeds with borderline trade'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📌 {scenario['description']}")
        print(f"   TCS: {scenario['tcs']}% | Action: {scenario['action']}")
        
        # Process the response
        response = process_warning_response('test_user', scenario['tcs'], scenario['action'])
        
        print(f"   Bit's Reaction: {response['bit_reaction']}")
        print(f"   Trade Proceeds: {'Yes' if response['proceed'] else 'No'}")
        if response.get('enforce_cooldown'):
            print(f"   ⏰ 5-minute cooldown enforced!")

def demonstrate_enhanced_warnings():
    """Demonstrate enhanced warnings for serial risk ignorers"""
    print_separator()
    print("🚨 ENHANCED WARNINGS FOR SERIAL RISK IGNORERS")
    print_separator()
    
    warning_system = BitWarningSystem()
    
    # Create a serial risk ignorer
    user_id = 'risk_ignorer'
    
    # Record many ignored warnings
    print("Recording history of ignored warnings...")
    for i in range(10):
        warning_system.record_confirmation_response(
            user_id, 
            65,  # High risk TCS
            WarningLevel.HIGH,
            'override_warning'
        )
    
    # Now show what happens when they get a new warning
    user_profile = {
        'user_id': user_id,
        'tier': 'fang',
        'recent_losses': 5,
        'win_rate_7d': 0.25,
        'account_balance': 8500  # Lost money
    }
    
    needs_warning, dialog = check_low_tcs_warning(65, user_profile)
    
    # Check if enhanced warning should be shown
    if warning_system.should_show_enhanced_warning(user_id):
        enhanced_prefix = warning_system.get_enhanced_warning_prefix(user_id)
        print("\n⚠️ ENHANCED WARNING TRIGGERED!")
        print(enhanced_prefix)
    
    # Show the warning
    print(format_warning_for_telegram(dialog))
    
    # Show wisdom stats
    wisdom_data = warning_system.get_user_wisdom_score(user_id)
    print(f"\n📊 Current Wisdom Score: {wisdom_data['score']}%")
    print(f"🏆 Rating: {wisdom_data['rating']}")

def main():
    """Run all demonstrations"""
    demonstrate_warnings()
    demonstrate_wisdom_tracking()
    demonstrate_bit_reactions()
    demonstrate_enhanced_warnings()
    
    print_separator()
    print("✅ Demonstration Complete!")
    print("\n💡 Key Features Shown:")
    print("• Warning dialogs for trades under 76% TCS")
    print("• Different severity levels (Extreme/High/Moderate/Low)")
    print("• Yoda-style wisdom quotes from Bit")
    print("• Wisdom score tracking based on heeding warnings")
    print("• Different reactions from Bit based on user decisions")
    print("• Enhanced warnings for serial risk ignorers")
    print("• Double confirmation for high-risk trades")
    print("• Cooldown enforcement for reckless trading")
    print("\n🐈 *Bit purrs approvingly* - Remember, patience the path to profits is!")

if __name__ == "__main__":
    main()