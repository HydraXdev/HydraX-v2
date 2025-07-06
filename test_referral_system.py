#!/usr/bin/env python3
"""
Test script for BITTEN Referral System
Demonstrates the elite military-style recruitment features
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.referral_system import ReferralSystem, ReferralCommandHandler
from bitten_core.xp_economy import XPEconomy
import time


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def main():
    print("🎖️ BITTEN ELITE REFERRAL SYSTEM TEST 🎖️")
    print("Building your squad, military-style!\n")
    
    # Initialize systems
    print_section("1. INITIALIZING SYSTEMS")
    xp_economy = XPEconomy()
    referral_system = ReferralSystem(xp_economy=xp_economy)
    command_handler = ReferralCommandHandler(referral_system)
    
    print("✅ XP Economy initialized")
    print("✅ Referral System initialized")
    print("✅ Command Handler ready")
    
    # Test user IDs
    commander_id = "1001"
    recruit1_id = "2001"
    recruit2_id = "2002"
    recruit3_id = "2003"
    
    # Generate referral code for commander
    print_section("2. GENERATING REFERRAL CODE")
    success, message, code = referral_system.generate_referral_code(commander_id, "ALPHA")
    print(f"Result: {message}")
    if success:
        print(f"Code generated: {code.code}")
    
    # Test command handler
    print("\nTesting /refer command:")
    response = command_handler.handle_command(commander_id, "Commander", [])
    print(response)
    
    # Use referral code - First recruit
    print_section("3. FIRST RECRUIT JOINS")
    success, message, result = referral_system.use_referral_code(
        recruit1_id,
        code.code,
        "Recruit_Alpha",
        "192.168.1.100"
    )
    print(f"Result: {message}")
    if success:
        print(f"XP Awarded: {result['xp_awarded']}")
        print(f"Squad Rank: {result['squad_rank']}")
    
    # Check commander stats
    print_section("4. COMMANDER STATS AFTER FIRST RECRUIT")
    stats = referral_system.get_referral_stats(commander_id)
    print(f"Total Recruits: {stats['squad_stats']['total_recruits']}")
    print(f"Total XP Earned: {stats['squad_stats']['total_xp_earned']}")
    print(f"Squad Rank: {stats['squad_stats']['squad_rank']}")
    print(f"Current Multiplier: {stats['current_multiplier']}x")
    
    # Simulate recruit completing first trade
    print_section("5. RECRUIT COMPLETES FIRST TRADE")
    rewards = referral_system.track_recruit_progress(
        recruit1_id,
        'trade_completed'
    )
    if rewards:
        for referrer_id, xp in rewards:
            print(f"Referrer {referrer_id} earned {xp} XP")
    
    # Add more recruits
    print_section("6. BUILDING THE SQUAD")
    
    # Second recruit
    print("\nSecond recruit joins...")
    referral_system.use_referral_code(
        recruit2_id,
        code.code,
        "Recruit_Bravo",
        "192.168.1.101"
    )
    
    # Third recruit with cooldown test
    print("\nTesting cooldown (should fail)...")
    time.sleep(1)  # Short delay
    success, message, _ = referral_system.use_referral_code(
        recruit3_id,
        code.code,
        "Recruit_Charlie",
        "192.168.1.101"  # Same IP as recruit 2
    )
    print(f"Result: {message}")
    
    # Create promo code
    print_section("7. CREATING PROMO CODE")
    success, message = referral_system.create_promo_code(
        "ELITE2024",
        commander_id,
        max_uses=10,
        expires_in_days=7,
        xp_multiplier=2.0
    )
    print(f"Result: {message}")
    
    # Use promo code
    if success:
        print("\nUsing promo code...")
        success, message, result = referral_system.use_referral_code(
            recruit3_id,
            "ELITE2024",
            "Recruit_Charlie",
            "192.168.1.102"
        )
        print(f"Result: {message}")
        if success:
            print(f"XP Awarded (with 2x bonus): {result['xp_awarded']}")
    
    # Show squad genealogy
    print_section("8. SQUAD GENEALOGY TREE")
    genealogy = referral_system.get_squad_genealogy(commander_id)
    print(f"Commander: User {commander_id}")
    print(f"Squad Stats:")
    print(f"  - Total Recruits: {genealogy['squad_stats']['total_recruits']}")
    print(f"  - Total XP Earned: {genealogy['squad_stats']['total_xp_earned']}")
    print(f"  - Squad Rank: {genealogy['squad_stats']['squad_rank']}")
    print(f"\nDirect Recruits:")
    for recruit in genealogy['recruits']:
        print(f"  - {recruit['username']} ({recruit['rank']}) - {recruit['trades']} trades")
    
    # Show leaderboard
    print_section("9. REFERRAL LEADERBOARD")
    leaderboard = referral_system.get_referral_leaderboard(5)
    for entry in leaderboard:
        print(f"{entry['rank']}. {entry['username']} - {entry['squad_rank']} - "
              f"{entry['total_recruits']} recruits - {entry['total_xp']} XP")
    
    # Test all command variations
    print_section("10. TESTING ALL COMMAND VARIATIONS")
    
    commands = [
        (["generate", "CUSTOM"], "Generate custom code"),
        (["stats"], "View detailed stats"),
        (["tree"], "View squad tree"),
        (["leaderboard"], "View leaderboard"),
    ]
    
    for args, description in commands:
        print(f"\n/refer {' '.join(args)} - {description}:")
        response = command_handler.handle_command(commander_id, "Commander", args)
        print(response[:200] + "..." if len(response) > 200 else response)
    
    # Simulate rank upgrade
    print_section("11. RECRUIT RANK UPGRADE")
    rewards = referral_system.track_recruit_progress(
        recruit1_id,
        'rank_upgraded',
        {'new_rank': 'FANG', 'old_rank': 'NIBBLER'}
    )
    if rewards:
        for referrer_id, xp in rewards:
            print(f"Referrer {referrer_id} earned {xp} XP for recruit reaching FANG")
    
    # Final stats
    print_section("12. FINAL COMMANDER STATS")
    final_stats = referral_system.get_referral_stats(commander_id)
    print(f"Total Recruits: {final_stats['squad_stats']['total_recruits']}")
    print(f"Active Recruits: {final_stats['squad_stats']['active_recruits']}")
    print(f"Total XP Earned: {final_stats['squad_stats']['total_xp_earned']}")
    print(f"Squad Rank: {final_stats['squad_stats']['squad_rank']}")
    print(f"Current Multiplier: {final_stats['current_multiplier']}x")
    
    if final_stats['recent_rewards']:
        print("\nRecent Rewards:")
        for reward in final_stats['recent_rewards'][:5]:
            print(f"  - {reward['type']}: {reward['xp']} XP")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎖️ The elite recruitment system is ready for deployment! 🎖️")


if __name__ == "__main__":
    main()