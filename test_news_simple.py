#!/usr/bin/env python3
"""
Simple test for news API functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from bitten_core.news_api_client import NewsAPIClient, NewsImpact
    from datetime import datetime, timezone
    
    print("🧪 Testing News API Client\n")
    
    # Create client
    client = NewsAPIClient()
    print(f"✅ Created NewsAPIClient with provider: {client.provider}")
    
    # Test fetching events
    print("\n📅 Fetching events for next 7 days...")
    events = client.fetch_events(days_ahead=7)
    
    if events:
        print(f"✅ Found {len(events)} events")
        
        # Show first few events
        print("\n📰 First 3 events:")
        for i, event in enumerate(events[:3]):
            print(f"\n{i+1}. {event.event_name}")
            print(f"   Time: {event.event_time}")
            print(f"   Currency: {event.currency}")
            print(f"   Impact: {event.impact.value}")
    else:
        print("⚠️  No events found (API might be down or using mock data)")
    
    # Test blackout period
    print("\n\n🚫 Checking blackout period...")
    is_blackout, current_event = client.is_news_blackout_period()
    
    if is_blackout and current_event:
        print(f"❌ Currently in blackout for: {current_event.event_name}")
    else:
        print("✅ Not in blackout period")
        
        # Get next blackout
        next_window = client.get_next_blackout_window()
        if next_window:
            start, end, event = next_window
            print(f"\n⏰ Next blackout: {start} to {end}")
            print(f"   Event: {event.event_name} ({event.currency})")
    
    print("\n✅ News API test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()