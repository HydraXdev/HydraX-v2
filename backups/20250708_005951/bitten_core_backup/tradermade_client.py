#!/usr/bin/env python3
"""
TraderMade API Client for Live Forex Data
Provides real-time market data for BITTEN signal detection
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class TraderMadeClient:
    """Client for TraderMade live forex data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('TRADERMADE_API_KEY')
        self.base_url = "https://marketdata.tradermade.com/api/v1"
        self.websocket_url = "wss://marketdata.tradermade.com/feedadv"
        self.session = None
        self.websocket = None
        
        # Supported pairs
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF']
        
        # Cache for latest prices
        self.price_cache: Dict[str, Dict] = {}
        
    async def connect(self):
        """Initialize connection to TraderMade"""
        if not self.api_key:
            print("⚠️ No TraderMade API key found! Using simulated data...")
            return await self.start_simulated_feed()
        
        self.session = aiohttp.ClientSession()
        print("🌐 Connecting to TraderMade API...")
        
        # Test connection with live endpoint
        try:
            url = f"{self.base_url}/live"
            params = {
                'currency': 'EURUSD',
                'api_key': self.api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ TraderMade connection successful!")
                    print(f"EUR/USD: {data['quotes'][0]['bid']}/{data['quotes'][0]['ask']}")
                else:
                    print(f"❌ TraderMade API error: {response.status}")
                    return await self.start_simulated_feed()
                    
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return await self.start_simulated_feed()
    
    async def start_simulated_feed(self):
        """Start simulated market data for testing"""
        print("🎮 Starting simulated market data feed...")
        
        # Base prices for simulation
        self.base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2750,
            'USDJPY': 150.50,
            'AUDUSD': 0.6550,
            'NZDUSD': 0.6050,
            'USDCAD': 1.3550,
            'USDCHF': 0.8850
        }
        
        # Start simulated price updates
        asyncio.create_task(self._simulate_price_updates())
    
    async def _simulate_price_updates(self):
        """Generate realistic price movements"""
        import random
        
        while True:
            for pair in self.pairs:
                base_price = self.base_prices[pair]
                
                # Simulate realistic price movement
                movement = random.gauss(0, 0.0002)  # ~2 pip standard deviation
                new_price = base_price * (1 + movement)
                
                # JPY pairs have different pip value
                if 'JPY' in pair:
                    spread = 0.02
                else:
                    spread = 0.0002
                
                # Update cache
                self.price_cache[pair] = {
                    'symbol': pair,
                    'bid': round(new_price - spread/2, 5),
                    'ask': round(new_price + spread/2, 5),
                    'mid': round(new_price, 5),
                    'timestamp': int(time.time()),
                    'datetime': datetime.now().isoformat()
                }
                
                # Update base price with momentum
                self.base_prices[pair] = new_price
            
            await asyncio.sleep(1)  # Update every second
    
    async def get_live_rates(self, pairs: Optional[List[str]] = None) -> Dict[str, Dict]:
        """Get current rates for specified pairs"""
        pairs = pairs or self.pairs
        
        if self.api_key and self.session:
            # Real API call
            try:
                url = f"{self.base_url}/live"
                params = {
                    'currency': ','.join(pairs),
                    'api_key': self.api_key
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Update cache
                        for quote in data.get('quotes', []):
                            symbol = quote['instrument'].replace('/', '')
                            self.price_cache[symbol] = {
                                'symbol': symbol,
                                'bid': quote['bid'],
                                'ask': quote['ask'],
                                'mid': quote['mid'],
                                'timestamp': data['timestamp'],
                                'datetime': data['datetime']
                            }
                        
                        return self.price_cache
                    else:
                        print(f"API error: {response.status}")
                        return self.price_cache
                        
            except Exception as e:
                print(f"Error fetching live rates: {e}")
                return self.price_cache
        else:
            # Return simulated data
            return {pair: self.price_cache.get(pair) for pair in pairs if pair in self.price_cache}
    
    async def get_ohlc(self, pair: str, timeframe: str = '5m', count: int = 100) -> List[Dict]:
        """Get OHLC candle data"""
        # For simulation, generate synthetic OHLC data
        if not self.api_key:
            return self._generate_synthetic_ohlc(pair, timeframe, count)
        
        # Real API implementation would go here
        # TraderMade requires different endpoint for historical data
        pass
    
    def _generate_synthetic_ohlc(self, pair: str, timeframe: str, count: int) -> List[Dict]:
        """Generate synthetic OHLC data for testing"""
        import random
        
        candles = []
        current_price = self.base_prices.get(pair, 1.0)
        
        # Time intervals
        intervals = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        interval = intervals.get(timeframe, 300)
        current_time = int(time.time())
        
        for i in range(count):
            # Generate OHLC
            open_price = current_price
            movement = random.gauss(0, 0.0005)
            high = open_price * (1 + abs(movement) + random.uniform(0, 0.0002))
            low = open_price * (1 - abs(movement) - random.uniform(0, 0.0002))
            close = open_price * (1 + movement)
            
            candles.append({
                'time': current_time - (interval * i),
                'open': round(open_price, 5),
                'high': round(high, 5),
                'low': round(low, 5),
                'close': round(close, 5),
                'volume': random.randint(100, 1000)
            })
            
            current_price = close
        
        return list(reversed(candles))
    
    async def stream_prices(self, callback):
        """Stream live prices via callback"""
        while True:
            rates = await self.get_live_rates()
            if rates:
                await callback(rates)
            await asyncio.sleep(1)
    
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.websocket:
            await self.websocket.close()
        print("🔌 TraderMade client disconnected")

# Test the client
async def test_tradermade():
    """Test TraderMade client"""
    client = TraderMadeClient()
    await client.connect()
    
    # Get live rates
    print("\n📊 Current Rates:")
    rates = await client.get_live_rates()
    for pair, data in rates.items():
        if data:
            print(f"{pair}: {data['bid']}/{data['ask']} (spread: {round((data['ask']-data['bid'])*10000, 1)} pips)")
    
    # Stream prices for 10 seconds
    print("\n📈 Streaming prices for 10 seconds...")
    
    async def price_callback(rates):
        # Just print EUR/USD
        if 'EURUSD' in rates:
            data = rates['EURUSD']
            print(f"EUR/USD: {data['bid']}/{data['ask']}", end='\r')
    
    # Run stream for 10 seconds
    stream_task = asyncio.create_task(client.stream_prices(price_callback))
    await asyncio.sleep(10)
    stream_task.cancel()
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_tradermade())