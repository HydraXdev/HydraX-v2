#!/usr/bin/env python3
"""
Direct test of referral system functionality
"""

import sys
import os

# Direct import without going through __init__.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'bitten_core'))

from referral_system import ReferralSystem, ReferralCommandHandler

print("🎖️ BITTEN REFERRAL SYSTEM - DIRECT TEST 🎖️\n")

# Initialize
print("1. Initializing referral system...")
referral_system = ReferralSystem(db_path="test_referral.db")
command_handler = ReferralCommandHandler(referral_system)
print("✅ System initialized\n")

# Generate code
print("2. Generating referral code...")
success, message, code = referral_system.generate_referral_code("commander123", "ELITE")
print(f"Result: {message}")
if code:
    print(f"Code: {code.code}\n")

# Use code
print("3. New recruit using code...")
success, message, result = referral_system.use_referral_code(
    "recruit456",
    code.code if code else "ELITE",
    "NewRecruit",
    "192.168.1.1"
)
print(f"Result: {message}")
if result:
    print(f"Details: {result}\n")

# Get stats
print("4. Commander stats...")
stats = referral_system.get_referral_stats("commander123")
print(f"Total recruits: {stats['squad_stats']['total_recruits']}")
print(f"Squad rank: {stats['squad_stats']['squad_rank']}\n")

# Test command
print("5. Testing /refer command...")
response = command_handler.handle_command("commander123", "Commander", [])
print("Response preview:")
print(response[:300] + "..." if len(response) > 300 else response)

print("\n✅ Test completed!")

# Cleanup
if os.path.exists("test_referral.db"):
    os.remove("test_referral.db")
    print("🧹 Cleaned up test database")