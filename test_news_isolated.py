#!/usr/bin/env python3
"""
Isolated test for news API functionality
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Direct test without complex imports
class SimpleNewsTest:
    def __init__(self):
        self.base_url = 'https://nfs.faireconomy.media'
        self.endpoint = '/ff_calendar_thisweek.json'
        
    def fetch_events(self):
        """Fetch events directly from API"""
        try:
            url = self.base_url + self.endpoint
            headers = {
                'User-Agent': 'HydraX-BITTEN/2.0 (Trading System)',
                'Accept': 'application/json',
            }
            
            print(f"🌐 Fetching from: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Got {len(data)} raw events")
            return data
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            return self.get_mock_events()
    
    def get_mock_events(self):
        """Generate mock events for testing"""
        events = []
        now = datetime.now()
        
        # Add some mock high impact events
        mock_events = [
            {"hours": 2, "country": "USD", "title": "Non-Farm Payrolls", "impact": "High"},
            {"hours": 6, "country": "EUR", "title": "ECB Rate Decision", "impact": "High"},
            {"hours": 24, "country": "GBP", "title": "UK GDP", "impact": "Medium"},
            {"hours": 48, "country": "JPY", "title": "BoJ Policy Rate", "impact": "High"},
        ]
        
        for mock in mock_events:
            event_time = now + timedelta(hours=mock["hours"])
            events.append({
                "date": event_time.strftime("%Y-%m-%d"),
                "time": event_time.strftime("%I:%M%p"),
                "country": mock["country"],
                "impact": mock["impact"],
                "title": mock["title"],
                "forecast": "0.2%",
                "previous": "0.1%"
            })
        
        return events
    
    def check_news_blackout(self, events: List[Dict[str, Any]]):
        """Check if we're in a news blackout period"""
        now = datetime.now(timezone.utc)
        buffer_minutes = 30
        
        for event in events:
            if event.get('impact', '').lower() != 'high':
                continue
            
            # Parse event time
            try:
                date_str = event.get('date', '')
                time_str = event.get('time', '')
                if date_str and time_str and time_str != 'All Day':
                    datetime_str = f"{date_str} {time_str}"
                    event_time = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M%p")
                    event_time = event_time.replace(tzinfo=timezone.utc)
                    
                    # Check if within blackout window
                    time_diff = abs((event_time - now).total_seconds() / 60)
                    if time_diff <= buffer_minutes:
                        return True, event
            except:
                continue
        
        return False, None

def main():
    print("🧪 Simple News API Test\n")
    
    tester = SimpleNewsTest()
    
    # Fetch events
    events = tester.fetch_events()
    
    # Display first few events
    if events:
        print("\n📰 First 5 events:")
        for i, event in enumerate(events[:5]):
            print(f"\n{i+1}. {event.get('title', 'Unknown')}")
            print(f"   Date: {event.get('date', 'N/A')} {event.get('time', '')}")
            print(f"   Currency: {event.get('country', 'N/A')}")
            print(f"   Impact: {event.get('impact', 'N/A')}")
    
    # Check blackout
    print("\n\n🚫 Checking blackout period...")
    is_blackout, event = tester.check_news_blackout(events)
    
    if is_blackout:
        print(f"❌ Currently in blackout for: {event.get('title')}")
    else:
        print("✅ Not in blackout period")
    
    # Test risk management integration concepts
    print("\n\n🛡️ Risk Management Integration:")
    print("- News events would be added to RiskManager.news_events list")
    print("- RiskManager._is_news_lockout() checks for active blackouts")
    print("- Trading restrictions returned in check_trading_restrictions()")
    print("- State set to TradingState.NEWS_LOCKOUT during blackouts")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()