#!/usr/bin/env python3
"""
Simple test script for BITTEN Referral System
Tests core functionality without full system dependencies
"""

import sys
import os
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only what we need
from bitten_core.referral_system import ReferralSystem, ReferralCommandHandler


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def main():
    print("🎖️ BITTEN REFERRAL SYSTEM - SIMPLE TEST 🎖️\n")
    
    # Initialize referral system without XP economy
    print_section("1. SYSTEM INITIALIZATION")
    referral_system = ReferralSystem(db_path="test_referral.db")
    command_handler = ReferralCommandHandler(referral_system)
    print("✅ Referral System initialized")
    
    # Test data
    commander_id = "1001"
    commander_name = "EliteCommander"
    recruit_id = "2001"
    recruit_name = "NewRecruit"
    
    # Generate referral code
    print_section("2. GENERATE REFERRAL CODE")
    success, message, code = referral_system.generate_referral_code(commander_id, "ALPHA")
    print(f"Result: {message}")
    if success:
        print(f"Code: {code.code}")
        print(f"Created at: {code.created_at}")
    
    # Test command handler - show status
    print_section("3. TEST /refer COMMAND")
    response = command_handler.handle_command(commander_id, commander_name, [])
    print("Response preview:")
    print(response[:500] + "..." if len(response) > 500 else response)
    
    # Use referral code
    print_section("4. RECRUIT JOINS WITH CODE")
    success, message, result = referral_system.use_referral_code(
        recruit_id,
        code.code,
        recruit_name,
        "192.168.1.100"
    )
    print(f"Result: {message}")
    if success and result:
        print(f"Referrer: {result.get('referrer_name', 'Unknown')}")
        print(f"Squad Rank: {result.get('squad_rank', 'Unknown')}")
        print(f"XP that would be awarded: {result.get('xp_awarded', 0)}")
    
    # Check stats after recruit
    print_section("5. COMMANDER STATS UPDATE")
    stats = referral_system.get_referral_stats(commander_id)
    print(f"Referral Code: {stats['referral_code']}")
    print(f"Total Recruits: {stats['squad_stats']['total_recruits']}")
    print(f"Squad Rank: {stats['squad_stats']['squad_rank']}")
    print(f"Current Multiplier: {stats['current_multiplier']}x")
    
    # Test promo code
    print_section("6. CREATE PROMO CODE")
    success, message = referral_system.create_promo_code(
        "ELITE2024",
        commander_id,
        max_uses=5,
        expires_in_days=7,
        xp_multiplier=2.0
    )
    print(f"Result: {message}")
    
    # Show leaderboard (even if empty)
    print_section("7. REFERRAL LEADERBOARD")
    leaderboard = referral_system.get_referral_leaderboard(5)
    if leaderboard:
        for entry in leaderboard:
            print(f"{entry['rank']}. User {entry['user_id'][:8]}... - "
                  f"{entry['squad_rank']} - {entry['total_recruits']} recruits")
    else:
        print("No entries yet")
    
    # Test command variations
    print_section("8. COMMAND VARIATIONS")
    test_commands = [
        (["generate"], "Generate default code"),
        (["generate", "CUSTOM123"], "Generate custom code"),
        (["stats"], "View detailed stats"),
        (["tree"], "View squad tree"),
        (["leaderboard"], "View leaderboard")
    ]
    
    for args, desc in test_commands:
        print(f"\n/refer {' '.join(args)} - {desc}")
        response = command_handler.handle_command(commander_id, commander_name, args)
        print(f"Response length: {len(response)} chars")
    
    # Database check
    print_section("9. DATABASE VERIFICATION")
    conn = sqlite3.connect("test_referral.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables created:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check referral codes
    cursor.execute("SELECT COUNT(*) FROM referral_codes")
    code_count = cursor.fetchone()[0]
    print(f"\nReferral codes in database: {code_count}")
    
    # Check recruits
    cursor.execute("SELECT COUNT(*) FROM recruits")
    recruit_count = cursor.fetchone()[0]
    print(f"Recruits in database: {recruit_count}")
    
    conn.close()
    
    print("\n✅ All basic tests completed successfully!")
    
    # Cleanup
    if os.path.exists("test_referral.db"):
        os.remove("test_referral.db")
        print("\n🧹 Test database cleaned up")


if __name__ == "__main__":
    main()