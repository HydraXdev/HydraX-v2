#!/usr/bin/env python3
"""
Demonstration of Bit's Low TCS Warning System
Shows warning dialogs and wisdom tracking without full system dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import just the bit_warnings module directly
import importlib.util
spec = importlib.util.spec_from_file_location("bit_warnings", "/root/HydraX-v2/src/bitten_core/bit_warnings.py")
bit_warnings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bit_warnings)

from datetime import datetime

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
        
        needs_warning, dialog = bit_warnings.check_low_tcs_warning(test['tcs'], user_profile)
        
        if needs_warning:
            # Display the formatted Telegram message
            telegram_message = bit_warnings.format_warning_for_telegram(dialog)
            print(telegram_message)
            
            # Show button options
            print("\n🔘 Available Actions:")
            for button in dialog['buttons']:
                print(f"  • {button['text']} (action: {button['action']})")
            
            # Show if double confirmation is required
            if dialog['require_double_confirm']:
                print(f"\n⚠️ DOUBLE CONFIRMATION REQUIRED")
                print(f"Cooldown if proceeding: {dialog['cooldown_seconds']} seconds")
        else:
            print("✅ No warning required - TCS is above 76% threshold")

def demonstrate_wisdom_tracking():
    """Demonstrate Bit's wisdom score tracking"""
    print_separator()
    print("📊 WISDOM SCORE TRACKING DEMONSTRATION")
    print_separator()
    
    warning_system = bit_warnings.BitWarningSystem()
    
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
        response = bit_warnings.process_warning_response('test_user', scenario['tcs'], scenario['action'])
        
        print(f"   🐈 Bit's Reaction: {response['bit_reaction']}")
        print(f"   ▶️ Trade Proceeds: {'Yes ⚠️' if response['proceed'] else 'No ✅'}")
        if response.get('enforce_cooldown'):
            print(f"   ⏰ 5-minute cooldown enforced!")

def demonstrate_yoda_wisdom():
    """Show some of Bit's Yoda-style wisdom quotes"""
    print_separator()
    print("✨ BIT'S YODA-STYLE WISDOM QUOTES")
    print_separator()
    
    warning_system = bit_warnings.BitWarningSystem()
    
    # Get sample quotes for each warning level
    print("Sample wisdom for different risk levels:\n")
    
    for level, quotes in warning_system.wisdom_quotes.items():
        print(f"🔸 {level.value.upper()} RISK:")
        # Show first quote from each level
        sample_quote = quotes[0].format(tcs=65)
        print(f"   \"{sample_quote}\"")
        print()
    
    # Show patience wisdom
    print("🧘 PATIENCE WISDOM:")
    patience_quotes = [
        "Patience, for the moment when the setup reveals itself, you must have.",
        "A Jedi trader craves not adventure or excitement. Seek the perfect setup, they do.",
        "Do or do not trade. There is no revenge trade.",
        "The greatest teacher, missed opportunities are. Learn from them, you will."
    ]
    for quote in patience_quotes[:3]:
        print(f"   \"{quote}\"")

def main():
    """Run all demonstrations"""
    demonstrate_warnings()
    demonstrate_wisdom_tracking()
    demonstrate_bit_reactions()
    demonstrate_yoda_wisdom()
    
    print_separator()
    print("✅ Demonstration Complete!")
    print("\n💡 KEY FEATURES OF BIT'S WARNING SYSTEM:")
    print("━" * 50)
    print("📊 TCS Thresholds:")
    print("   • < 60%: Extreme Risk - Double confirmation required")
    print("   • 60-69%: High Risk - Double confirmation required")
    print("   • 70-75%: Moderate Risk - Single confirmation")  
    print("   • 76%+: No warning - Safe to trade")
    print("\n🎮 User Actions:")
    print("   • Cancel/Review: Wise choice, improves wisdom score")
    print("   • Confirm/Override: Risky choice, decreases wisdom score")
    print("\n🏆 Wisdom Ratings:")
    print("   • 80%+: Jedi Master Trader")
    print("   • 60-79%: Jedi Knight")
    print("   • 40-59%: Padawan Learner")
    print("   • 20-39%: Youngling")
    print("   • < 20%: Sith Lord (Ignores all wisdom)")
    print("\n🐈 Bit's Special Features:")
    print("   • Yoda-style wisdom quotes")
    print("   • Personalized discipline reminders")
    print("   • Risk multiplier calculations")
    print("   • Enhanced warnings for serial risk takers")
    print("   • 5-minute cooldown after high-risk trades")
    print("\n*Bit purrs approvingly* - Remember, patience the path to profits is!")

if __name__ == "__main__":
    main()