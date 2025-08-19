#!/usr/bin/env python3
"""
BITTEN News Filter Control Panel
Quick controls and monitoring for the deployed news filter
"""

import sys
import json
from datetime import datetime

def get_news_filter_status():
    """Get current news filter status from running Elite Guard"""
    try:
        # Import the modules
        sys.path.append('/root/HydraX-v2')
        from news_intelligence_gate import NewsIntelligenceGate
        import logging
        
        # Create a temporary instance to check status
        logger = logging.getLogger()
        news_gate = NewsIntelligenceGate(logger)
        
        status = {
            'enabled': news_gate.enabled,
            'statistics': news_gate.get_statistics(),
            'upcoming_events': news_gate.get_upcoming_events(24),
            'calendar_events_total': len(news_gate.economic_calendar),
            'last_update': news_gate.last_update
        }
        
        return status
        
    except Exception as e:
        return {'error': str(e)}

def print_status():
    """Print formatted news filter status"""
    print("🗞️ BITTEN News Filter Status Check")
    print("=" * 50)
    
    status = get_news_filter_status()
    
    if 'error' in status:
        print(f"❌ Error: {status['error']}")
        return
    
    # Basic status
    enabled_icon = "✅" if status['enabled'] else "❌"
    print(f"{enabled_icon} News Filter: {'ENABLED' if status['enabled'] else 'DISABLED'}")
    
    # Statistics
    stats = status['statistics']
    print(f"📊 Evaluations: {stats['total_evaluations']}")
    print(f"🚫 Blocked: {stats['blocked_cycles']} ({stats.get('block_rate', 0):.1f}%)")
    print(f"📉 Reduced: {stats['reduced_confidence']} ({stats.get('reduce_rate', 0):.1f}%)")
    print(f"🟢 Normal: {stats['normal_trading']} ({stats.get('normal_rate', 0):.1f}%)")
    
    # Calendar status
    print(f"📅 Calendar Events: {status['calendar_events_total']}")
    
    if status['last_update'] > 0:
        last_update = datetime.fromtimestamp(status['last_update'])
        print(f"🕐 Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("🕐 Last Update: Never")
    
    # Upcoming events
    upcoming = status['upcoming_events']
    if upcoming:
        print(f"\n📋 Next {min(3, len(upcoming))} Events:")
        for event in upcoming[:3]:
            event_time = datetime.fromtimestamp(event.event_timestamp)
            print(f"   {event.country} {event.impact}: {event.title}")
            print(f"      📅 {event_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("\n📋 No upcoming high/medium impact events")
    
    print("\n🎛️ Controls:")
    print("   python3 news_filter_control.py enable   # Enable filter")
    print("   python3 news_filter_control.py disable  # Disable filter") 
    print("   python3 news_filter_control.py update   # Force calendar update")

def enable_filter():
    """Enable news filter (simulation - actual control would need Elite Guard instance)"""
    print("🗞️ Enable News Filter")
    print("To enable the news filter in the live system:")
    print("1. Connect to Python shell:")
    print("   python3 -c \"")
    print("   from elite_guard_with_citadel import EliteGuardWithCitadel")
    print("   # Note: This would require connecting to the running instance")
    print("   # The filter is enabled by default in the current deployment")
    print("   \"")
    print("✅ News filter is already ENABLED by default in the current deployment")

def disable_filter():
    """Disable news filter (simulation)"""
    print("🗞️ Disable News Filter (For A/B Testing)")
    print("To disable the news filter in the live system:")
    print("1. You would need to access the running Elite Guard instance")
    print("2. Call guard.disable_news_filter()")
    print("⚠️ This would disable news filtering for A/B testing comparison")

def force_update():
    """Force calendar update"""
    print("📡 Force Calendar Update")
    try:
        sys.path.append('/root/HydraX-v2')
        from news_intelligence_gate import NewsIntelligenceGate
        import logging
        
        logger = logging.getLogger()
        news_gate = NewsIntelligenceGate(logger)
        
        print("📡 Attempting to fetch economic calendar...")
        success = news_gate.force_calendar_update()
        
        if success:
            print(f"✅ Calendar updated: {len(news_gate.economic_calendar)} events loaded")
        else:
            print("❌ Calendar update failed - check network connectivity")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main control function"""
    if len(sys.argv) < 2:
        print_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        print_status()
    elif command == 'enable':
        enable_filter()
    elif command == 'disable':
        disable_filter()
    elif command == 'update':
        force_update()
    else:
        print("❌ Unknown command. Use: status, enable, disable, or update")

if __name__ == "__main__":
    main()