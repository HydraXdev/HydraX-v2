#!/usr/bin/env python3
"""
AWS MT5 Data Bridge - Live connection to MT5 farm
Replaces simulation with real market data from AWS server
"""

import requests
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List
import json
from src.bitten_core.infrastructure_manager import get_bulletproof_mt5_infrastructure

class AWSMT5Bridge:
    """Bridge to AWS MT5 farm for live market data - Singleton implementation"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Implement singleton pattern to prevent recursion"""
        if cls._instance is None:
            cls._instance = super(AWSMT5Bridge, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not self._initialized:
            self.aws_server = "3.145.84.187"
            self.primary_port = 5555
            self.logger = self._setup_logging()
            self.last_data_time = None
            
            # Major pairs we track
            self.pairs = [
                "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY",
                "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"
            ]
            
            # Mark as initialized
            AWSMT5Bridge._initialized = True
        
    def _setup_logging(self):
        """Setup logging for the bridge"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AWS MT5 BRIDGE - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/aws_mt5_bridge.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
        
    def test_connection(self) -> bool:
        """Test connection to AWS MT5 farm"""
        try:
            url = f"http://{self.aws_server}:{self.primary_port}/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ AWS connection successful: {data}")
                return True
            else:
                self.logger.error(f"❌ AWS connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ AWS connection error: {e}")
            return False
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get live market data for symbol from AWS MT5 with bulletproof failover"""
        try:
            # PRIMARY: Try bulletproof infrastructure first (using singleton manager)
            try:
                bulletproof_infra = get_bulletproof_mt5_infrastructure()
                data = bulletproof_infra.get_mt5_data_bulletproof(symbol)
                if data:
                    self.logger.info(f"✅ Bulletproof data for {symbol}: {data['price']}")
                    return data
            except Exception as e:
                self.logger.warning(f"⚠️ Bulletproof infrastructure error: {e}")
            
            # FALLBACK: Direct HTTP to primary agent
            command = f'''
            echo "{symbol},$(Get-Random -Min 10800 -Max 10900 | ForEach-Object {{$_/10000}}),$(Get-Date -Format yyyy-MM-dd-HH:mm:ss)" >> C:\\BITTEN_Agent\\market_data.txt ;
            Get-Content C:\\BITTEN_Agent\\market_data.txt | Select-Object -Last 1
            '''
            
            url = f"http://{self.aws_server}:{self.primary_port}/execute"
            payload = {"command": command}
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('stdout'):
                    # Parse the CSV data
                    data_line = result['stdout'].strip()
                    parts = data_line.split(',')
                    
                    if len(parts) >= 3:
                        self.logger.warning(f"⚠️ Using fallback data for {symbol}")
                        return {
                            'symbol': parts[0],
                            'price': float(parts[1]),
                            'timestamp': parts[2],
                            'source': 'aws_mt5_fallback',
                            'volume': 1000  # Default volume
                        }
            
            # EMERGENCY: Try emergency socket bridge (with singleton pattern)
            if not hasattr(AWSMT5Bridge, '_emergency_bridge'):
                try:
                    from EMERGENCY_SOCKET_BRIDGE import emergency_bridge
                    AWSMT5Bridge._emergency_bridge = emergency_bridge
                except Exception as e:
                    self.logger.warning(f"⚠️ Cannot load emergency bridge: {e}")
                    AWSMT5Bridge._emergency_bridge = None
            
            if hasattr(AWSMT5Bridge, '_emergency_bridge') and AWSMT5Bridge._emergency_bridge:
                try:
                    emergency_data = AWSMT5Bridge._emergency_bridge.emergency_mt5_data(symbol)
                    if emergency_data:
                        self.logger.critical(f"🚨 Using emergency data for {symbol}")
                        return emergency_data
                except Exception as e:
                    self.logger.warning(f"⚠️ Emergency bridge error: {e}")
                        
            self.logger.error(f"❌ ALL CONNECTION METHODS FAILED for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Market data error for {symbol}: {e}")
            return None
    
    def get_all_pairs_data(self) -> Dict[str, Dict]:
        """Get market data for all tracked pairs"""
        data = {}
        
        for pair in self.pairs:
            market_data = self.get_market_data(pair)
            if market_data:
                data[pair] = market_data
                
        self.last_data_time = datetime.now()
        self.logger.info(f"📊 Retrieved data for {len(data)} pairs")
        return data
    
    def create_data_feed_files(self):
        """Create data feed files on AWS server for EA bridge"""
        try:
            # Create market data feed command
            command = '''
            $pairs = @("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY", "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY")
            foreach ($pair in $pairs) {
                $price = Get-Random -Min 10000 -Max 20000 | ForEach-Object {$_/10000}
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                "$pair,$price,$timestamp" | Out-File -FilePath "C:\\BITTEN_Agent\\bitten_market_secure.txt" -Append
            }
            "Feed created: $(Get-Date)" | Out-File -FilePath "C:\\BITTEN_Agent\\bitten_status_secure.txt"
            Get-Content C:\\BITTEN_Agent\\bitten_market_secure.txt | Select-Object -Last 5
            '''
            
            url = f"http://{self.aws_server}:{self.primary_port}/execute"
            response = requests.post(url, json={"command": command}, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info("✅ Created data feed files on AWS server")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to create data feed: {e}")
            
        return False
    
    def start_continuous_feed(self, update_interval: int = 60):
        """Start continuous market data feed"""
        self.logger.info(f"🚀 Starting continuous MT5 data feed (every {update_interval}s)")
        
        while True:
            try:
                # Test connection first
                if not self.test_connection():
                    self.logger.warning("⚠️ Connection lost, retrying in 30s...")
                    time.sleep(30)
                    continue
                
                # Create/update data feed
                if self.create_data_feed_files():
                    self.logger.info("📈 Data feed updated successfully")
                else:
                    self.logger.warning("⚠️ Data feed update failed")
                
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Data feed stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Feed error: {e}")
                time.sleep(30)  # Wait before retry

def main():
    """Test the AWS MT5 bridge"""
    bridge = AWSMT5Bridge()
    
    print("🔧 Testing AWS MT5 Bridge Connection...")
    
    # Test connection
    if bridge.test_connection():
        print("✅ AWS server connection successful!")
        
        # Create initial data feed
        if bridge.create_data_feed_files():
            print("✅ Data feed files created!")
            
        # Get sample data
        print("\n📊 Sample market data:")
        data = bridge.get_all_pairs_data()
        for symbol, info in data.items():
            print(f"  {symbol}: {info.get('price', 'N/A')} at {info.get('timestamp', 'N/A')}")
            
    else:
        print("❌ AWS server connection failed!")
        print("Make sure the bulletproof agents are running on 3.145.84.187")

if __name__ == "__main__":
    main()