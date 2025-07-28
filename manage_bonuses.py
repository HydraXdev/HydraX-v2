#!/usr/bin/env python3
"""
CLI tool to manage BITTEN bonuses and special events
"""

import sys
import argparse
from datetime import datetime, timedelta

sys.path.append('src')
from bitten_core.bonus_manager import BonusManager

def list_events(args):
    """List all special events"""
    manager = BonusManager()
    events = manager.config.get('special_events', {})
    
    print("\n📅 SPECIAL EVENTS:")
    print("-" * 80)
    
    for event_name, event_data in events.items():
        status = "✅ ACTIVE" if event_data.get('active', False) else "⏸️  INACTIVE"
        print(f"\n{event_name}: {status}")
        print(f"  Period: {event_data['start_datetime']} to {event_data['end_datetime']}")
        print(f"  Tiers: {', '.join(event_data['eligible_tiers'])}")
        print(f"  Bonuses:")
        for bonus_type, value in event_data['bonuses'].items():
            if value > 0:
                print(f"    - {bonus_type}: +{value}")
        print(f"  Message: {event_data['message']}")

def activate_event(args):
    """Activate a special event"""
    manager = BonusManager()
    if manager.activate_special_event(args.event_name):
        print(f"✅ Event '{args.event_name}' activated!")
    else:
        print(f"❌ Event '{args.event_name}' not found!")

def deactivate_event(args):
    """Deactivate a special event"""
    manager = BonusManager()
    if manager.deactivate_special_event(args.event_name):
        print(f"⏸️  Event '{args.event_name}' deactivated!")
    else:
        print(f"❌ Event '{args.event_name}' not found!")

def grant_bonus(args):
    """Grant a bonus to a user"""
    manager = BonusManager()
    
    # Parse bonuses
    bonuses = {
        'risk_percent': args.risk or 0,
        'daily_shots': args.shots or 0,
        'positions': args.positions or 0,
        'tcs_reduction': args.tcs or 0
    }
    
    bonus_id = manager.grant_user_bonus(
        user_id=args.user_id,
        bonus_type=args.type,
        duration_hours=args.hours,
        bonuses=bonuses,
        reason=args.reason
    )
    
    print(f"✅ Bonus granted!")
    print(f"   ID: {bonus_id}")
    print(f"   User: {args.user_id}")
    print(f"   Duration: {args.hours} hours")
    print(f"   Reason: {args.reason}")

def grant_achievement(args):
    """Grant an achievement bonus"""
    manager = BonusManager()
    
    bonus_id = manager.grant_achievement_bonus(args.user_id, args.achievement)
    
    if bonus_id:
        print(f"🏆 Achievement '{args.achievement}' granted to user {args.user_id}!")
        print(f"   Bonus ID: {bonus_id}")
    else:
        print(f"❌ Achievement '{args.achievement}' not found!")
        print("\nAvailable achievements:")
        for ach_name in manager.config.get('achievement_bonuses', {}).keys():
            print(f"  - {ach_name}")

def list_user_bonuses(args):
    """List bonuses for a user"""
    manager = BonusManager()
    bonuses = manager.get_user_bonuses(args.user_id)
    
    print(f"\n🎁 BONUSES FOR USER {args.user_id}:")
    print("-" * 80)
    
    if not bonuses:
        print("No active bonuses")
    else:
        for bonus in bonuses:
            print(f"\nID: {bonus['id']}")
            print(f"  Type: {bonus['type']}")
            print(f"  Expires: {bonus['expires']}")
            print(f"  Reason: {bonus['reason']}")
            print(f"  Bonuses:")
            for bonus_type, value in bonus['bonuses'].items():
                if value > 0:
                    print(f"    - {bonus_type}: +{value}")

def cleanup_expired(args):
    """Clean up expired bonuses"""
    manager = BonusManager()
    cleaned = manager.cleanup_expired_bonuses()
    print(f"🧹 Cleaned up {cleaned} expired bonuses")

def create_event(args):
    """Create a new special event"""
    manager = BonusManager()
    
    # Calculate datetime strings
    start = datetime.now() + timedelta(days=args.start_days)
    end = start + timedelta(days=args.duration_days)
    
    event_data = {
        'start_datetime': start.strftime('%Y-%m-%d %H:%M:%S'),
        'end_datetime': end.strftime('%Y-%m-%d %H:%M:%S'),
        'eligible_tiers': args.tiers.split(','),
        'bonuses': {
            'risk_percent': args.risk or 0,
            'daily_shots': args.shots or 0,
            'positions': args.positions or 0,
            'tcs_reduction': args.tcs or 0
        },
        'message': args.message,
        'active': args.activate
    }
    
    if manager.create_special_event(args.name, event_data):
        print(f"✅ Event '{args.name}' created!")
        if args.activate:
            print("   Status: ACTIVE")
    else:
        print(f"❌ Failed to create event")

def main():
    parser = argparse.ArgumentParser(description='BITTEN Bonus Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List events
    list_parser = subparsers.add_parser('list-events', help='List all special events')
    
    # Activate/deactivate event
    activate_parser = subparsers.add_parser('activate', help='Activate a special event')
    activate_parser.add_argument('event_name', help='Name of the event')
    
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a special event')
    deactivate_parser.add_argument('event_name', help='Name of the event')
    
    # Create event
    create_parser = subparsers.add_parser('create-event', help='Create a new special event')
    create_parser.add_argument('name', help='Event name')
    create_parser.add_argument('--start-days', type=int, default=0, help='Days from now to start')
    create_parser.add_argument('--duration-days', type=int, default=1, help='Duration in days')
    create_parser.add_argument('--tiers', default='NIBBLER,FANG,COMMANDER', help='Eligible tiers (comma-separated)')
    create_parser.add_argument('--risk', type=float, help='Bonus risk percent')
    create_parser.add_argument('--shots', type=int, help='Bonus daily shots')
    create_parser.add_argument('--positions', type=int, help='Bonus positions')
    create_parser.add_argument('--tcs', type=int, help='TCS reduction')
    create_parser.add_argument('--message', required=True, help='Event message')
    create_parser.add_argument('--activate', action='store_true', help='Activate immediately')
    
    # Grant bonus
    grant_parser = subparsers.add_parser('grant', help='Grant a bonus to a user')
    grant_parser.add_argument('user_id', type=int, help='User ID')
    grant_parser.add_argument('--type', default='manual', help='Bonus type')
    grant_parser.add_argument('--hours', type=int, default=24, help='Duration in hours')
    grant_parser.add_argument('--risk', type=float, help='Bonus risk percent')
    grant_parser.add_argument('--shots', type=int, help='Bonus daily shots')
    grant_parser.add_argument('--positions', type=int, help='Bonus positions')
    grant_parser.add_argument('--tcs', type=int, help='TCS reduction')
    grant_parser.add_argument('--reason', required=True, help='Reason for bonus')
    
    # Grant achievement
    ach_parser = subparsers.add_parser('achievement', help='Grant an achievement bonus')
    ach_parser.add_argument('user_id', type=int, help='User ID')
    ach_parser.add_argument('achievement', help='Achievement name')
    
    # List user bonuses
    user_parser = subparsers.add_parser('user', help='List bonuses for a user')
    user_parser.add_argument('user_id', type=int, help='User ID')
    
    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up expired bonuses')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        'list-events': list_events,
        'activate': activate_event,
        'deactivate': deactivate_event,
        'create-event': create_event,
        'grant': grant_bonus,
        'achievement': grant_achievement,
        'user': list_user_bonuses,
        'cleanup': cleanup_expired
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()