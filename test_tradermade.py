#!/usr/bin/env python3
"""
Test TraderMade API connection
"""

import asyncio
import aiohttp

API_KEY = 'iOxhauPWBb-xbxd9QgyR'

async def test_api():
    print("🔍 Testing TraderMade API...")
    print(f"API Key: {API_KEY[:10]}...")
    
    async with aiohttp.ClientSession() as session:
        # Test live endpoint
        pairs = "EURUSD,GBPUSD,USDJPY"
        url = f"https://marketdata.tradermade.com/api/v1/live?currency={pairs}&api_key={API_KEY}"
        
        try:
            async with session.get(url) as response:
                print(f"\n📡 Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ API Connected Successfully!\n")
                    
                    if 'quotes' in data:
                        print("📊 Live Prices:")
                        for quote in data['quotes']:
                            print(f"• {quote['instrument']}: {quote['mid']} (Bid: {quote['bid']}, Ask: {quote['ask']})")
                    
                    print(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
                    print(f"Endpoint: {data.get('endpoint', 'live')}")
                else:
                    text = await response.text()
                    print(f"❌ API Error: {text}")
                    
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == '__main__':
    print("TraderMade API Test\n")
    asyncio.run(test_api())