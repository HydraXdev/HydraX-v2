#!/usr/bin/env python3
"""
Quick Press Pass Test Runner
Allows testing specific Press Pass functionality without running full suite
"""

import asyncio
import sys
import argparse
from datetime import datetime, timezone
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_press_pass_comprehensive import PressPassComprehensiveTest, MockTelegramMessenger


async def test_activation_only():
    """Test only Press Pass activation"""
    print("\n🎫 Testing Press Pass Activation...")
    tester = PressPassComprehensiveTest()
    await tester.setup()
    await tester.test_press_pass_activation()
    
    result = tester.test_results[0]
    print(f"\nResult: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"Message: {result.message}")
    if result.details:
        print(f"Details: {result.details}")


async def test_xp_reset():
    """Test XP reset functionality"""
    print("\n💀 Testing XP Reset...")
    tester = PressPassComprehensiveTest()
    await tester.setup()
    
    # First activate Press Pass
    await tester.test_press_pass_activation()
    
    # Award some XP
    await tester.test_xp_and_shadow_stats()
    
    # Test reset
    await tester.test_midnight_reset()
    
    reset_result = tester.test_results[-1]
    print(f"\nReset Result: {'✅ PASSED' if reset_result.passed else '❌ FAILED'}")
    print(f"Message: {reset_result.message}")
    if reset_result.details:
        print(f"XP before reset: {reset_result.details.get('pre_reset_xp', 0):,}")
        print(f"XP after reset: {reset_result.details.get('post_reset_xp', 0):,}")
        print(f"Total wiped: {reset_result.details.get('total_wiped', 0):,}")


async def test_warnings():
    """Test warning notifications"""
    print("\n⚠️  Testing Warning Notifications...")
    tester = PressPassComprehensiveTest()
    await tester.setup()
    
    # Activate Press Pass first
    await tester.test_press_pass_activation()
    
    # Test warnings
    await tester.test_warning_notifications()
    
    warning_result = tester.test_results[-1]
    print(f"\nWarning Result: {'✅ PASSED' if warning_result.passed else '❌ FAILED'}")
    print(f"Message: {warning_result.message}")
    if warning_result.details:
        print(f"Messages sent: {warning_result.details.get('messages_sent', 0)}")


async def test_demo_account():
    """Test demo account provisioning"""
    print("\n🏦 Testing Demo Account Provisioning...")
    tester = PressPassComprehensiveTest()
    await tester.setup()
    
    await tester.test_demo_account_provisioning()
    
    result = tester.test_results[0]
    print(f"\nResult: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"Message: {result.message}")
    if result.details:
        print(f"Account Number: {result.details.get('account_number', 'N/A')}")
        print(f"Balance: ${result.details.get('balance', 0):,}")
        print(f"Server: {result.details.get('server', 'N/A')}")


async def test_conversion():
    """Test conversion to paid tier"""
    print("\n💰 Testing Conversion to Paid Tier...")
    tester = PressPassComprehensiveTest()
    await tester.setup()
    
    # Activate Press Pass first
    await tester.test_press_pass_activation()
    
    # Test conversion
    await tester.test_conversion_to_paid()
    
    conversion_result = tester.test_results[-1]
    print(f"\nConversion Result: {'✅ PASSED' if conversion_result.passed else '❌ FAILED'}")
    print(f"Message: {conversion_result.message}")
    if conversion_result.details:
        print(f"Tier: {conversion_result.details.get('tier', 'N/A')}")
        print(f"Discount applied: {conversion_result.details.get('discount_applied', False)}")


async def interactive_test():
    """Interactive test mode"""
    print("\n🎮 Interactive Press Pass Test")
    print("="*40)
    
    tester = PressPassComprehensiveTest()
    await tester.setup()
    
    while True:
        print("\nSelect test to run:")
        print("1. Activate Press Pass")
        print("2. Check Status")
        print("3. Award XP")
        print("4. Send Warning")
        print("5. Execute Reset")
        print("6. Test Demo Account")
        print("7. Test Conversion")
        print("8. Run All Tests")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            await tester.test_press_pass_activation()
            print_last_result(tester)
        elif choice == "2":
            status = tester.xp_manager.get_press_pass_status(tester.test_user_id)
            print(f"\nPress Pass Active: {status['active']}")
            if status['active']:
                print(f"Current XP: {status['current_xp']:,}")
                if status.get('shadow_stats'):
                    print(f"Shadow Stats: {status['shadow_stats']}")
        elif choice == "3":
            amount = int(input("Enter XP amount to award: "))
            xp = tester.xp_manager.award_xp_with_multipliers(
                tester.test_user_id,
                amount,
                "Interactive test award",
                "Manual test"
            )
            print(f"Awarded {xp} XP")
        elif choice == "4":
            hours = float(input("Hours until reset (1 or 0.25): "))
            await tester.xp_manager.press_pass_manager.send_warning_notification(hours)
            print("Warning sent!")
        elif choice == "5":
            await tester.test_midnight_reset()
            print_last_result(tester)
        elif choice == "6":
            await tester.test_demo_account_provisioning()
            print_last_result(tester)
        elif choice == "7":
            await tester.test_conversion_to_paid()
            print_last_result(tester)
        elif choice == "8":
            await tester.run_all_tests()
        else:
            print("Invalid choice")


def print_last_result(tester):
    """Print the last test result"""
    if tester.test_results:
        result = tester.test_results[-1]
        print(f"\n{result.test_name}: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        print(f"Message: {result.message}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Quick Press Pass Test Runner")
    parser.add_argument(
        "test",
        choices=["activation", "xp-reset", "warnings", "demo", "conversion", "interactive", "all"],
        help="Test to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "activation":
        await test_activation_only()
    elif args.test == "xp-reset":
        await test_xp_reset()
    elif args.test == "warnings":
        await test_warnings()
    elif args.test == "demo":
        await test_demo_account()
    elif args.test == "conversion":
        await test_conversion()
    elif args.test == "interactive":
        await interactive_test()
    elif args.test == "all":
        tester = PressPassComprehensiveTest()
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())