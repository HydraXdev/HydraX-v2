#!/usr/bin/env python3
"""
Test for high impact news events
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

class NewsAnalyzer:
    def __init__(self):
        self.base_url = 'https://nfs.faireconomy.media'
        self.endpoint = '/ff_calendar_thisweek.json'
        self.monitored_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
        
    def fetch_and_analyze(self):
        """Fetch and analyze events"""
        try:
            url = self.base_url + self.endpoint
            headers = {
                'User-Agent': 'HydraX-BITTEN/2.0 (Trading System)',
                'Accept': 'application/json',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self.analyze_events(data)
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            return []
    
    def analyze_events(self, events: List[Dict[str, Any]]):
        """Analyze events for impact and relevance"""
        high_impact = []
        medium_impact = []
        
        for event in events:
            # Get impact level
            impact = event.get('impact', '').lower()
            currency = event.get('country', '').upper()
            
            # Skip if not monitored currency
            if currency not in self.monitored_currencies:
                continue
            
            # Categorize by impact
            if impact in ['high', 'red', '3']:
                high_impact.append(event)
            elif impact in ['medium', 'orange', 'yellow', '2']:
                medium_impact.append(event)
        
        return high_impact, medium_impact

def main():
    print("🔍 Analyzing News Events for High Impact\n")
    
    analyzer = NewsAnalyzer()
    high, medium = analyzer.fetch_and_analyze()
    
    print(f"📊 Analysis Results:")
    print(f"- High Impact Events: {len(high)}")
    print(f"- Medium Impact Events: {len(medium)}")
    
    if high:
        print("\n🔴 HIGH IMPACT EVENTS:")
        for event in high[:10]:  # Show first 10
            date_str = event.get('date', 'Unknown')
            time_str = event.get('time', '')
            title = event.get('title', 'Unknown')
            currency = event.get('country', 'N/A')
            
            print(f"\n📌 {title}")
            print(f"   Currency: {currency}")
            print(f"   Time: {date_str} {time_str}")
            print(f"   Impact: {event.get('impact', 'N/A')}")
            
            # Check if it's a key event
            key_events = ['NFP', 'Non-Farm', 'Interest Rate', 'CPI', 'GDP', 'FOMC', 'ECB', 'Bank of']
            is_key = any(key in title for key in key_events)
            if is_key:
                print(f"   ⚠️  KEY EVENT!")
    else:
        print("\nℹ️  No high impact events found in current data")
    
    # Show next few days overview
    print("\n\n📅 Events by Day:")
    events_by_day = {}
    
    for event in high + medium:
        date = event.get('date', 'Unknown')
        if date not in events_by_day:
            events_by_day[date] = {'high': 0, 'medium': 0}
        
        impact = event.get('impact', '').lower()
        if impact in ['high', 'red', '3']:
            events_by_day[date]['high'] += 1
        else:
            events_by_day[date]['medium'] += 1
    
    for date in sorted(events_by_day.keys())[:7]:  # Next 7 days
        counts = events_by_day[date]
        print(f"{date}: 🔴 {counts['high']} high, 🟡 {counts['medium']} medium")
    
    print("\n✅ Analysis completed!")

if __name__ == "__main__":
    main()