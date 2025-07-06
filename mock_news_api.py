#!/usr/bin/env python3
"""
Mock news API server for testing when real API is not available
"""

from flask import Flask, jsonify
from datetime import datetime, timedelta
import random

app = Flask(__name__)

def generate_mock_events():
    """Generate mock economic events"""
    events = []
    now = datetime.now()
    
    # High impact events
    high_impact_events = [
        {"name": "Non-Farm Payrolls", "currency": "USD", "impact": "High"},
        {"name": "ECB Interest Rate Decision", "currency": "EUR", "impact": "High"},
        {"name": "UK GDP", "currency": "GBP", "impact": "High"},
        {"name": "Bank of Japan Policy Rate", "currency": "JPY", "impact": "High"},
    ]
    
    # Medium impact events
    medium_impact_events = [
        {"name": "US Retail Sales", "currency": "USD", "impact": "Medium"},
        {"name": "German PMI", "currency": "EUR", "impact": "Medium"},
        {"name": "UK Employment", "currency": "GBP", "impact": "Medium"},
        {"name": "AUD Employment Change", "currency": "AUD", "impact": "Medium"},
    ]
    
    # Generate events for next 7 days
    for day in range(7):
        date = now + timedelta(days=day)
        
        # Add 1-2 high impact events per day
        for _ in range(random.randint(1, 2)):
            event_template = random.choice(high_impact_events)
            hour = random.randint(8, 16)  # Between 8 AM and 4 PM
            event_time = date.replace(hour=hour, minute=30 if random.random() > 0.5 else 0)
            
            events.append({
                "date": event_time.strftime("%Y-%m-%d"),
                "time": event_time.strftime("%I:%M%p"),
                "country": event_template["currency"],
                "impact": event_template["impact"],
                "title": event_template["name"],
                "forecast": f"{random.uniform(-0.5, 0.5):.1f}%",
                "previous": f"{random.uniform(-0.5, 0.5):.1f}%"
            })
        
        # Add 2-3 medium impact events per day
        for _ in range(random.randint(2, 3)):
            event_template = random.choice(medium_impact_events)
            hour = random.randint(6, 20)
            event_time = date.replace(hour=hour, minute=0)
            
            events.append({
                "date": event_time.strftime("%Y-%m-%d"),
                "time": event_time.strftime("%I:%M%p"),
                "country": event_template["currency"],
                "impact": event_template["impact"],
                "title": event_template["name"],
                "forecast": f"{random.uniform(-1, 1):.1f}%",
                "previous": f"{random.uniform(-1, 1):.1f}%"
            })
    
    return sorted(events, key=lambda x: x["date"] + " " + x["time"])

@app.route('/ff_calendar_thisweek.json')
def calendar():
    """Mock ForexFactory calendar endpoint"""
    return jsonify(generate_mock_events())

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "mock_news_api"})

if __name__ == '__main__':
    print("🎭 Starting Mock News API Server on http://localhost:5001")
    print("Use NEWS_API_PROVIDER=forexfactory and update base_url to http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)