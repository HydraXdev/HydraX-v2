#!/usr/bin/env python3
"""
Test the bonus override system
"""

import sys
sys.path.append('src')

from bitten_core.bonus_manager import BonusManager
from datetime import datetime, timedelta

def demonstrate_bonus_system():
    print("🎁 BITTEN BONUS SYSTEM DEMONSTRATION\n")
    
    manager = BonusManager()
    
    # Example 1: Fourth of July Event
    print("1️⃣ Creating Fourth of July Event:")
    event_data = {
        'start_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_datetime': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),
        'eligible_tiers': ['NIBBLER', 'FANG', 'COMMANDER', 'APEX'],
        'bonuses': {
            'risk_percent': 0.5,        # +0.5% risk
            'daily_shots': 2,           # +2 trades
            'positions': 0,
            'tcs_reduction': 0
        },
        'message': '🎆 Fourth of July Special: +0.5% risk & 2 bonus shots!',
        'active': True
    }
    
    manager.create_special_event('fourth_of_july_demo', event_data)
    print("✅ Event created and activated!\n")
    
    # Example 2: User-specific bonus
    print("2️⃣ Granting Win Streak Bonus to User 12345:")
    bonus_id = manager.grant_user_bonus(
        user_id=12345,
        bonus_type='win_streak',
        duration_hours=48,
        bonuses={
            'risk_percent': 0.25,       # +0.25% risk
            'daily_shots': 3,           # +3 trades
            'positions': 0,
            'tcs_reduction': 0
        },
        reason='5-day win streak! Great job!'
    )
    print(f"✅ Bonus granted with ID: {bonus_id}\n")
    
    # Example 3: Achievement bonus
    print("3️⃣ Granting Week Warrior Achievement to User 67890:")
    ach_id = manager.grant_achievement_bonus(67890, 'week_warrior')
    print(f"✅ Achievement bonus granted with ID: {ach_id}\n")
    
    # Show how bonuses stack
    print("4️⃣ BONUS STACKING EXAMPLE:")
    print("\nUser 12345 (NIBBLER tier) with active bonuses:")
    print("- Base limits: 2% risk, 6 trades/day, 1 position")
    print("- Fourth of July event: +0.5% risk, +2 trades")
    print("- Win streak bonus: +0.25% risk, +3 trades")
    print("- Tier multiplier (NIBBLER): 1.0x")
    print("\nFINAL LIMITS WITH BONUSES:")
    print("- Risk: 2% + 0.5% + 0.25% = 2.75% per trade")
    print("- Daily trades: 6 + 2 + 3 = 11 trades")
    print("- Positions: 1 + 0 + 0 = 1 position")
    
    # Show tier scaling
    print("\n5️⃣ TIER SCALING EXAMPLE:")
    print("\nSame bonuses for APEX tier user:")
    print("- Tier multiplier: 2.0x (doubles all bonuses)")
    print("- Risk bonus: (0.5% + 0.25%) × 2.0 = 1.5%")
    print("- Shot bonus: (2 + 3) × 2.0 = 10 extra trades")
    print("\nAPEX FINAL LIMITS:")
    print("- Risk: 2% + 1.5% = 3.5% per trade")
    print("- Daily trades: 999 + 10 = 1009 trades (effectively unlimited)")
    
    # Cleanup demo data
    manager.deactivate_special_event('fourth_of_july_demo')
    print("\n✅ Demo complete! (Demo event deactivated)")

def show_cli_examples():
    print("\n" + "="*80)
    print("📝 CLI USAGE EXAMPLES:")
    print("="*80)
    
    print("\n# List all events:")
    print("python manage_bonuses.py list-events")
    
    print("\n# Create and activate Fourth of July event:")
    print("python manage_bonuses.py create-event july4th_2024 \\")
    print("  --start-days 0 --duration-days 1 \\")
    print("  --risk 0.5 --shots 2 \\")
    print("  --message '🎆 Independence Day: +0.5% risk & 2 bonus shots!' \\")
    print("  --activate")
    
    print("\n# Grant manual bonus to user:")
    print("python manage_bonuses.py grant 12345 \\")
    print("  --type win_streak --hours 48 \\")
    print("  --risk 0.25 --shots 3 \\")
    print("  --reason '5-day win streak bonus!'")
    
    print("\n# Grant achievement:")
    print("python manage_bonuses.py achievement 12345 week_warrior")
    
    print("\n# Check user's bonuses:")
    print("python manage_bonuses.py user 12345")
    
    print("\n# Activate/deactivate events:")
    print("python manage_bonuses.py activate fourth_of_july_2024")
    print("python manage_bonuses.py deactivate fourth_of_july_2024")

if __name__ == "__main__":
    demonstrate_bonus_system()
    show_cli_examples()