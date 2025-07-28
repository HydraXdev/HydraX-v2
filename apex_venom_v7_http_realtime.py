#!/usr/bin/env python3
"""
VENOM v7.0 - HTTP Real-Time Integration
100% REAL DATA from market_data_receiver.py
NO FAKE/SYNTHETIC DATA EVER

This version integrates with the HTTP market data stream
from the PRODUCTION EA sending real tick data
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import sys

# Add src directory to path
sys.path.insert(0, '/root/HydraX-v2/src')

# Import base VENOM and smart timer
from apex_venom_v7_with_smart_timer import ApexVenomV7WithTimer, SmartTimerEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApexVenomV7HTTPRealtime(ApexVenomV7WithTimer):
    """VENOM v7.0 with HTTP real-time market data integration"""
    
    def __init__(self, market_data_url="http://127.0.0.1:8001/market-data"):
        # Initialize without Docker container reference
        super().__init__(core_system=None, mt5_container=None)
        self.market_data_url = market_data_url
        self.last_data_fetch = {}
        self.data_cache_duration = 5  # Cache for 5 seconds
        logger.info("🐍 VENOM v7.0 HTTP Real-Time Initialized")
        logger.info(f"📡 Market data endpoint: {market_data_url}")
        logger.info("🔒 100% REAL DATA - NO SYNTHETIC/FAKE DATA")
        
    def get_real_mt5_data(self, pair: str) -> Dict:
        """Get REAL market data from HTTP endpoint - NO FAKE DATA EVER"""
        try:
            # Check cache first
            cache_key = f"{pair}_last_fetch"
            if cache_key in self.last_data_fetch:
                last_fetch_time, cached_data = self.last_data_fetch[cache_key]
                if (datetime.now() - last_fetch_time).total_seconds() < self.data_cache_duration:
                    return cached_data
            
            # First try the venom-feed endpoint (enhanced receiver)
            try:
                response = requests.get(
                    f"{self.market_data_url}/venom-feed",
                    params={"symbol": pair},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and 'close' in data:
                        # Enhanced receiver format
                        market_data = {
                            'close': float(data.get('close', 0)),
                            'spread': float(data.get('spread', 0)),
                            'volume': int(data.get('volume', 0)),
                            'timestamp': datetime.now(),
                            'is_real': True
                        }
                        self.last_data_fetch[cache_key] = (datetime.now(), market_data)
                        return market_data
            except:
                pass  # Fall back to /all endpoint
            
            # Fall back to /all endpoint
            response = requests.get(f"{self.market_data_url}/all", timeout=10)
            
            if response.status_code == 200:
                all_data = response.json()
                
                # Check if our pair is in the data
                if pair in all_data:
                    tick_data = all_data[pair]
                    
                    market_data = {
                        'close': float(tick_data.get('bid', 0)),
                        'spread': float(tick_data.get('spread', 0)),
                        'volume': int(tick_data.get('volume', 0)),
                        'timestamp': datetime.now(),
                        'is_real': True  # Confirm this is real data
                    }
                    
                    # Cache the data
                    self.last_data_fetch[cache_key] = (datetime.now(), market_data)
                    
                    return market_data
                else:
                    logger.warning(f"⚠️ No data available for {pair}")
                    return {}
            else:
                logger.error(f"❌ HTTP error {response.status_code} fetching market data")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error fetching {pair} data: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {pair} data: {e}")
            return {}
    
    def check_market_data_health(self) -> bool:
        """Check if market data receiver is healthy"""
        try:
            response = requests.get(f"{self.market_data_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Market data receiver is healthy")
                return True
            else:
                logger.error(f"❌ Market data receiver unhealthy: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot reach market data receiver: {e}")
            return False
    
    def scan_all_pairs_realtime(self) -> List[Dict]:
        """Scan all 15 pairs for signals using real-time HTTP data"""
        signals = []
        
        # First check health
        if not self.check_market_data_health():
            logger.error("❌ Market data receiver offline - no signals possible")
            return signals
        
        # Get all available data
        try:
            response = requests.get(f"{self.market_data_url}/all", timeout=5)
            if response.status_code == 200:
                all_data = response.json()
                
                # Handle different response formats
                if 'symbols' in all_data:
                    # Simple receiver format
                    symbol_data = all_data['symbols']
                    logger.info(f"📊 Received data for {len(symbol_data)} pairs")
                else:
                    # Enhanced receiver format (direct symbols)
                    symbol_data = all_data
                    logger.info(f"📊 Received data for {len(symbol_data)} pairs")
                
                # Process each pair
                for pair, tick_data in symbol_data.items():
                    if tick_data and 'bid' in tick_data:
                        # Generate signal for this pair
                        signal = self.generate_venom_signal_with_timer(pair, datetime.now())
                        if signal:
                            signals.append(signal)
                            logger.info(f"🎯 Signal generated: {pair} {signal['signal_type']} @ {signal['confidence']}%")
                
                logger.info(f"📈 Total signals found: {len(signals)}")
                return signals
            else:
                logger.error(f"❌ Failed to get all market data: {response.status_code}")
                return signals
                
        except Exception as e:
            logger.error(f"❌ Error scanning pairs: {e}")
            return signals
    
    def run_continuous_scan(self, interval=30):
        """Run continuous signal scanning with real-time data"""
        logger.info("🚀 Starting continuous VENOM scan with HTTP real-time data")
        logger.info(f"⏰ Scan interval: {interval} seconds")
        logger.info("🔒 Using 100% REAL market data - NO FAKE DATA")
        
        while True:
            try:
                # Scan for signals
                signals = self.scan_all_pairs_realtime()
                
                if signals:
                    # Log high-quality signals
                    for signal in signals:
                        if signal['confidence'] >= 85:
                            logger.info(f"💎 HIGH QUALITY: {signal['pair']} {signal['signal_type']} "
                                      f"@ {signal['confidence']}% - Timer: {signal['smart_timer']['countdown_minutes']} min")
                
                # Wait for next scan
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Scan interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Scan error: {e}")
                time.sleep(10)  # Wait before retry

def main():
    """Main entry point for HTTP real-time VENOM"""
    venom = ApexVenomV7HTTPRealtime()
    
    # Run continuous scanning
    venom.run_continuous_scan(interval=30)

if __name__ == "__main__":
    main()