#!/usr/bin/env python3
"""
Test script for news event detection and auto-pause functionality
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.risk_management import RiskManager, NewsEvent
from bitten_core.news_scheduler import NewsScheduler
from bitten_core.news_api_client import NewsAPIClient, EconomicEvent, NewsImpact

def test_news_api_client():
    """Test the news API client"""
    print("=== Testing News API Client ===")
    
    client = NewsAPIClient()
    
    # Test fetching events
    print("\nFetching economic events for next 7 days...")
    events = client.fetch_events(days_ahead=7)
    
    print(f"Found {len(events)} events")
    
    # Display first 5 events
    for i, event in enumerate(events[:5]):
        print(f"\nEvent {i+1}:")
        print(f"  Time: {event.event_time}")
        print(f"  Currency: {event.currency}")
        print(f"  Impact: {event.impact.value}")
        print(f"  Name: {event.event_name}")
        if event.forecast:
            print(f"  Forecast: {event.forecast}")
        if event.previous:
            print(f"  Previous: {event.previous}")
    
    # Test blackout period check
    print("\n\nChecking blackout period...")
    is_blackout, current_event = client.is_news_blackout_period()
    
    if is_blackout:
        print(f"⚠️  Currently in blackout period for: {current_event.event_name}")
    else:
        print("✅ Not in blackout period")
        
        # Get next blackout
        next_window = client.get_next_blackout_window()
        if next_window:
            start, end, event = next_window
            print(f"\nNext blackout: {start} to {end}")
            print(f"For event: {event.event_name} ({event.currency})")

def test_news_scheduler():
    """Test the news scheduler"""
    print("\n\n=== Testing News Scheduler ===")
    
    # Create risk manager and scheduler
    risk_manager = RiskManager()
    scheduler = NewsScheduler(risk_manager)
    
    print("Starting scheduler...")
    scheduler.start()
    
    # Give it time to do initial update
    print("Waiting for initial update...")
    time.sleep(2)
    
    # Check status
    status = scheduler.get_status()
    print(f"\nScheduler Status:")
    print(f"  Running: {status['running']}")
    print(f"  Last Update: {status['last_update']}")
    print(f"  Events Tracked: {status['events_tracked']}")
    print(f"  In Blackout: {status['in_blackout']}")
    
    # Get upcoming events
    upcoming = scheduler.get_upcoming_events(hours=48)
    print(f"\nUpcoming high impact events (48h): {len(upcoming)}")
    
    # Stop scheduler
    scheduler.stop()
    print("\nScheduler stopped")

def test_risk_manager_integration():
    """Test integration with risk manager"""
    print("\n\n=== Testing Risk Manager Integration ===")
    
    risk_manager = RiskManager()
    
    # Add a test news event happening soon
    test_event = NewsEvent(
        event_time=datetime.now(timezone.utc) + timedelta(minutes=20),
        currency="USD",
        impact="high",
        event_name="Test NFP Release"
    )
    
    risk_manager.add_news_event(test_event)
    print(f"Added test event: {test_event.event_name}")
    
    # Check if we're in lockout
    from bitten_core.risk_management import RiskProfile, AccountInfo
    
    profile = RiskProfile(user_id=123, tier_level="NIBBLER")
    account = AccountInfo(balance=10000, equity=10000, margin=0, free_margin=10000)
    
    # Check trading restrictions
    restrictions = risk_manager.check_trading_restrictions(profile, account, "EURUSD")
    
    print(f"\nTrading allowed: {restrictions['can_trade']}")
    if not restrictions['can_trade']:
        print(f"Reason: {restrictions['reason']}")
    print(f"State: {restrictions['state']}")
    print(f"Restrictions: {restrictions.get('restrictions', {})}")

def main():
    """Run all tests"""
    print("🧪 Testing News Event Detection and Auto-Pause\n")
    
    try:
        # Test individual components
        test_news_api_client()
        test_news_scheduler()
        test_risk_manager_integration()
        
        print("\n\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()