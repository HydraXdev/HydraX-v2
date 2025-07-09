#!/usr/bin/env python3
"""
Test TraderMade API - Try different endpoints
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta

API_KEY = 'iOxhauPWBb-xbxd9QgyR'

async def test_endpoints():
    print("🔍 Testing TraderMade API Endpoints...")
    print(f"API Key: {API_KEY[:10]}...\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Historical data (usually works on free plan)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        hist_url = f"https://marketdata.tradermade.com/api/v1/historical?currency=EURUSD&date={yesterday}&api_key={API_KEY}"
        
        print("1️⃣ Testing Historical Data...")
        try:
            async with session.get(hist_url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("✅ Historical data accessible!")
                    if 'quotes' in data:
                        for quote in data['quotes']:
                            print(f"• {quote['instrument']} on {quote['date']}: {quote['close']}")
                else:
                    print(f"❌ Error: {await response.text()}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 2: Timeseries (might work)
        print("2️⃣ Testing Timeseries Data...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ts_url = f"https://marketdata.tradermade.com/api/v1/timeseries?currency=EURUSD&start_date={start_date}&end_date={end_date}&api_key={API_KEY}"
        
        try:
            async with session.get(ts_url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("✅ Timeseries data accessible!")
                    if 'quotes' in data:
                        print(f"Got {len(data['quotes'])} days of data")
                else:
                    print(f"❌ Error: {await response.text()}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 3: Convert endpoint (usually free)
        print("3️⃣ Testing Convert Endpoint...")
        convert_url = f"https://marketdata.tradermade.com/api/v1/convert?from=EUR&to=USD&amount=1&api_key={API_KEY}"
        
        try:
            async with session.get(convert_url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("✅ Convert endpoint works!")
                    print(f"• 1 EUR = {data.get('total', 'N/A')} USD")
                else:
                    print(f"❌ Error: {await response.text()}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("TraderMade API Endpoint Test\n")
    asyncio.run(test_endpoints())