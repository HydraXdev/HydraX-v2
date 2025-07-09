#!/usr/bin/env python3
"""
FOREX API BRIDGE - Real market data from Forex APIs
No Windows dependency, professional-grade data feed
"""

import requests
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class ForexAPIBridge:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # 10-pair configuration (BITTEN official)
        self.pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY",
            "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"
        ]
        
        # Multiple API sources for redundancy
        self.apis = {
            "fixer": {
                "url": "http://data.fixer.io/api/latest",
                "key": os.getenv("FIXER_API_KEY", ""),
                "enabled": bool(os.getenv("FIXER_API_KEY"))
            },
            "exchangerate": {
                "url": "https://api.exchangerate-api.com/v4/latest/USD",
                "key": "",
                "enabled": True  # Free API
            },
            "currencylayer": {
                "url": "http://api.currencylayer.com/live",
                "key": os.getenv("CURRENCYLAYER_API_KEY", ""),
                "enabled": bool(os.getenv("CURRENCYLAYER_API_KEY"))
            }
        }
        
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/forex_api.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            bid REAL NOT NULL,
            ask REAL NOT NULL,
            volume INTEGER DEFAULT 0,
            spread REAL NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            api_source TEXT,
            success BOOLEAN,
            pairs_updated INTEGER,
            error_message TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Database ready")
        
    def get_exchange_rates_free(self) -> Optional[Dict]:
        """Get rates from free exchangerate-api"""
        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "exchangerate-api",
                    "base": "USD",
                    "rates": data.get("rates", {}),
                    "timestamp": datetime.now()
                }
            else:
                self.logger.error(f"Exchange API HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Exchange API error: {e}")
            return None
            
    def get_fxapi_rates(self) -> Optional[Dict]:
        """Get rates from fxapi.com (free tier)"""
        try:
            response = requests.get(
                "https://fxapi.com/api/latest?base=USD&symbols=EUR,GBP,JPY,CAD,AUD,NZD,CHF",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "source": "fxapi",
                        "base": "USD", 
                        "rates": data.get("rates", {}),
                        "timestamp": datetime.now()
                    }
                else:
                    self.logger.error(f"FXAPI error: {data.get('error', 'Unknown')}")
                    return None
            else:
                self.logger.error(f"FXAPI HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"FXAPI error: {e}")
            return None
            
    def convert_rates_to_pairs(self, rates_data: Dict) -> Dict[str, Dict]:
        """Convert API rates to forex pairs with bid/ask"""
        if not rates_data or "rates" not in rates_data:
            return {}
            
        rates = rates_data["rates"]
        pairs_data = {}
        
        # Standard spread assumption (professional broker spreads)
        spreads = {
            "EURUSD": 0.8, "GBPUSD": 1.2, "USDJPY": 0.9, "USDCAD": 1.1,
            "GBPJPY": 2.1, "AUDUSD": 1.0, "NZDUSD": 1.5, "EURGBP": 1.3,
            "USDCHF": 1.2, "EURJPY": 1.8
        }
        
        # Convert rates to pairs
        for pair in self.pairs:
            try:
                base = pair[:3]
                quote = pair[3:]
                
                if base == "USD":
                    # USD base pairs (USDXXX)
                    if quote in rates:
                        mid_rate = rates[quote]
                        spread_pips = spreads.get(pair, 1.0)
                        
                        # Calculate bid/ask
                        if quote == "JPY":
                            spread_price = spread_pips * 0.01
                        else:
                            spread_price = spread_pips * 0.00001
                            
                        ask = mid_rate + (spread_price / 2)
                        bid = mid_rate - (spread_price / 2)
                        
                        pairs_data[pair] = {
                            "bid": round(bid, 5),
                            "ask": round(ask, 5),
                            "spread": spread_pips,
                            "timestamp": rates_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                elif quote == "USD":
                    # XXX/USD pairs
                    if base in rates:
                        usd_rate = 1.0 / rates[base]  # Invert rate
                        spread_pips = spreads.get(pair, 1.0)
                        spread_price = spread_pips * 0.00001
                        
                        ask = usd_rate + (spread_price / 2)
                        bid = usd_rate - (spread_price / 2)
                        
                        pairs_data[pair] = {
                            "bid": round(bid, 5),
                            "ask": round(ask, 5), 
                            "spread": spread_pips,
                            "timestamp": rates_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                else:
                    # Cross pairs (XXXYYY)
                    if base in rates and quote in rates:
                        cross_rate = rates[base] / rates[quote]
                        spread_pips = spreads.get(pair, 2.0)
                        
                        if quote == "JPY":
                            spread_price = spread_pips * 0.01
                        else:
                            spread_price = spread_pips * 0.00001
                            
                        ask = cross_rate + (spread_price / 2)
                        bid = cross_rate - (spread_price / 2)
                        
                        pairs_data[pair] = {
                            "bid": round(bid, 5),
                            "ask": round(ask, 5),
                            "spread": spread_pips,
                            "timestamp": rates_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
            except Exception as e:
                self.logger.error(f"Error converting {pair}: {e}")
                continue
                
        return pairs_data
        
    def store_tick_data(self, symbol: str, data: Dict):
        """Store tick data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO live_ticks (symbol, timestamp, bid, ask, spread, volume)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                data['timestamp'],
                data['bid'],
                data['ask'],
                data['spread'],
                0  # Volume not available from API
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database error storing {symbol}: {e}")
            
    def update_api_status(self, source: str, success: bool, pairs_count: int, error: str = None):
        """Update API status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO api_status (timestamp, api_source, success, pairs_updated, error_message)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                source,
                success,
                pairs_count,
                error or ""
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
            
    def run_data_collection(self):
        """Collect data from APIs"""
        # Try multiple APIs for redundancy
        apis_to_try = [
            ("exchangerate-api", self.get_exchange_rates_free),
            ("fxapi", self.get_fxapi_rates)
        ]
        
        for api_name, api_func in apis_to_try:
            try:
                self.logger.info(f"Trying {api_name}...")
                rates_data = api_func()
                
                if rates_data:
                    pairs_data = self.convert_rates_to_pairs(rates_data)
                    
                    if pairs_data:
                        pairs_updated = 0
                        for symbol, data in pairs_data.items():
                            self.store_tick_data(symbol, data)
                            pairs_updated += 1
                            self.logger.debug(f"Updated {symbol}: {data['bid']}/{data['ask']}")
                            
                        self.update_api_status(api_name, True, pairs_updated)
                        self.logger.info(f"✅ {api_name}: Updated {pairs_updated}/{len(self.pairs)} pairs")
                        return True
                    else:
                        self.logger.warning(f"{api_name}: No pair data generated")
                        self.update_api_status(api_name, False, 0, "No pair data")
                else:
                    self.logger.warning(f"{api_name}: No rates data")
                    self.update_api_status(api_name, False, 0, "No rates data")
                    
            except Exception as e:
                self.logger.error(f"{api_name} error: {e}")
                self.update_api_status(api_name, False, 0, str(e))
                continue
                
        self.logger.error("All APIs failed")
        return False
        
    def run_continuous(self, interval: int = 60):
        """Run continuous data collection"""
        self.logger.info(f"Starting Forex API bridge (interval: {interval}s)")
        
        while True:
            try:
                success = self.run_data_collection()
                if not success:
                    self.logger.warning("All APIs failed - retrying in 2 minutes")
                    time.sleep(120)
                else:
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                self.logger.info("Stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Bridge error: {e}")
                time.sleep(120)
                
    def test_connection(self):
        """Test API connections"""
        print("🌐 TESTING FOREX API BRIDGE...")
        print("=" * 50)
        
        # Test APIs
        success = self.run_data_collection()
        
        if success:
            print("✅ Forex APIs: WORKING")
            
            # Show recent data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            SELECT symbol, timestamp, bid, ask, spread 
            FROM live_ticks 
            ORDER BY timestamp DESC 
            LIMIT 10
            ''')
            
            recent_data = cursor.fetchall()
            conn.close()
            
            print(f"\n📈 Recent data ({len(recent_data)} pairs):")
            for row in recent_data:
                print(f"  {row[0]}: {row[2]}/{row[3]} (spread: {row[4]} pips)")
                
            return True
        else:
            print("❌ Forex APIs: ALL FAILED")
            print("Check internet connection and API limits")
            return False

if __name__ == "__main__":
    import sys
    
    bridge = ForexAPIBridge()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            bridge.test_connection()
        elif sys.argv[1] == "run":
            bridge.run_continuous()
    else:
        print("Usage:")
        print("  python3 forex_api_bridge.py test  - Test APIs")
        print("  python3 forex_api_bridge.py run   - Run continuous bridge")