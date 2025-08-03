#!/usr/bin/env python3
"""
DIRECT MT5 BRIDGE - No Windows dependency, real data from MetaTrader 5
Uses python MT5 library to connect directly to broker
"""

import MetaTrader5 as mt5
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import sys
import os

class MT5DirectBridge:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # 10-pair configuration (BITTEN official)
        self.pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY",
            "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"
        ]
        
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/mt5_direct.log'),
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
        CREATE TABLE IF NOT EXISTS mt5_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            connected BOOLEAN,
            account_info TEXT,
            symbols_available INTEGER,
            last_error TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Database ready")
        
    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5 connection
            if not mt5.initialize():
                error = mt5.last_error()
                self.logger.error(f"MT5 initialization failed: {error}")
                return False
                
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Failed to get account info")
                return False
                
            self.logger.info(f"MT5 connected: Account {account_info.login}")
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 connection error: {e}")
            return False
            
    def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time symbol data from MT5"""
        try:
            # Get symbol tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.logger.warning(f"No tick data for {symbol}")
                return None
                
            return {
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "volume": tick.volume,
                "spread": round((tick.ask - tick.bid) * 100000, 1),
                "timestamp": datetime.fromtimestamp(tick.time).strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting {symbol} data: {e}")
            return None
            
    def store_tick_data(self, data: Dict):
        """Store tick data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO live_ticks (symbol, timestamp, bid, ask, spread, volume)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'],
                data['timestamp'],
                data['bid'],
                data['ask'],
                data['spread'],
                data['volume']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            
    def update_status(self, connected: bool, error: str = None):
        """Update connection status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            account_info = ""
            symbols_count = 0
            
            if connected:
                try:
                    acc = mt5.account_info()
                    if acc:
                        account_info = f"Login: {acc.login}, Balance: {acc.balance}"
                        
                    symbols = mt5.symbols_get()
                    if symbols:
                        symbols_count = len(symbols)
                except:
                    pass
            
            cursor.execute('''
            INSERT INTO mt5_status (timestamp, connected, account_info, symbols_available, last_error)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                connected,
                account_info,
                symbols_count,
                error or ""
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
            
    def run_data_collection(self):
        """Collect data for all pairs"""
        if not self.connect_mt5():
            self.update_status(False, "Connection failed")
            return False
            
        self.update_status(True)
        
        pairs_updated = 0
        for symbol in self.pairs:
            data = self.get_symbol_data(symbol)
            if data:
                self.store_tick_data(data)
                pairs_updated += 1
                self.logger.debug(f"Updated {symbol}: {data['bid']}/{data['ask']}")
            else:
                self.logger.warning(f"Failed to get {symbol}")
                
        self.logger.info(f"Updated {pairs_updated}/{len(self.pairs)} pairs")
        
        # Shutdown MT5
        mt5.shutdown()
        
        return pairs_updated > 0
        
    def run_continuous(self, interval: int = 30):
        """Run continuous data collection"""
        self.logger.info(f"Starting continuous MT5 bridge (interval: {interval}s)")
        
        while True:
            try:
                success = self.run_data_collection()
                if not success:
                    self.logger.warning("Collection failed - retrying")
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Bridge error: {e}")
                time.sleep(60)
                
        # Final cleanup
        try:
            mt5.shutdown()
        except:
            pass
            
    def test_connection(self):
        """Test MT5 connection"""
        print("🔗 TESTING DIRECT MT5 CONNECTION...")
        print("=" * 50)
        
        # Test MT5 library
        try:
            import MetaTrader5
            print("✅ MT5 library: AVAILABLE")
        except ImportError:
            print("❌ MT5 library: NOT INSTALLED")
            print("Install with: pip install MetaTrader5")
            return False
            
        # Test connection
        if self.connect_mt5():
            print("✅ MT5 connection: SUCCESS")
            
            # Get account info
            account = mt5.account_info()
            if account:
                print(f"📊 Account: {account.login} (Balance: ${account.balance})")
                
            # Test symbol data
            print("\n📈 Testing symbol data:")
            for symbol in self.pairs[:3]:  # Test first 3 pairs
                data = self.get_symbol_data(symbol)
                if data:
                    print(f"  ✅ {symbol}: {data['bid']}/{data['ask']}")
                else:
                    print(f"  ❌ {symbol}: NO DATA")
                    
            mt5.shutdown()
            return True
        else:
            print("❌ MT5 connection: FAILED")
            print("Make sure MT5 terminal is running and logged in")
            return False

def install_mt5():
    """Install MT5 library"""
    print("Installing MetaTrader5 library...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "MetaTrader5"], check=True)
        print("✅ MT5 library installed")
        return True
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

if __name__ == "__main__":
    # Check if MT5 library is available
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("MetaTrader5 library not found. Installing...")
        if install_mt5():
            import MetaTrader5 as mt5
        else:
            print("Failed to install MT5 library")
            sys.exit(1)
    
    bridge = MT5DirectBridge()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            bridge.test_connection()
        elif sys.argv[1] == "run":
            bridge.run_continuous()
    else:
        print("Usage:")
        print("  python3 mt5_direct_bridge.py test  - Test connection")
        print("  python3 mt5_direct_bridge.py run   - Run continuous bridge")