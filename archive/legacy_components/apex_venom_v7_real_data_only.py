#!/usr/bin/env python3
"""
VENOM v7.0 REAL DATA ONLY - Victory Engine with Neural Optimization Matrix
NO SYNTHETIC DATA - Uses HTTP market data feed from EAs

This version:
- Connects to market_data_receiver.py for real tick data
- NO fake data generation methods
- Falls back to empty data if no real data available
- Will not generate signals without real market data
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, Optional

# Base VENOM imports
from apex_venom_v7_with_smart_timer import ApexVenomV7WithTimer as ApexVenomV7WithSmartTimer

logger = logging.getLogger(__name__)

class ApexVenomV7RealDataOnly(ApexVenomV7WithSmartTimer):
    """
    VENOM v7 that ONLY uses real market data from HTTP feed
    NO SYNTHETIC DATA GENERATION ALLOWED
    """
    
    def __init__(self, 
                 symbols=None,
                 market_data_url="http://localhost:8001",
                 require_real_data=True):
        """
        Initialize VENOM with real data requirements
        
        Args:
            symbols: List of symbols to trade
            market_data_url: URL of market data receiver
            require_real_data: If True, won't generate signals without real data
        """
        # Call parent constructor without symbols argument
        super().__init__()
        
        self.market_data_url = market_data_url
        self.require_real_data = require_real_data
        
        # Override symbols to ensure NO XAUUSD
        self.symbols = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
        ]
        
        logger.info("🔐 VENOM v7 REAL DATA ONLY initialized")
        logger.info(f"📡 Market data source: {self.market_data_url}")
        logger.info(f"🚫 Synthetic data: DISABLED")
        logger.info(f"✅ Valid symbols: {len(self.symbols)} pairs (NO XAUUSD)")
    
    def get_real_mt5_data(self, pair: str) -> Dict:
        """
        Get REAL market data from HTTP endpoint
        NO FALLBACK TO FAKE DATA
        """
        try:
            # Block XAUUSD explicitly
            if pair == "XAUUSD" or "XAU" in pair:
                logger.error(f"❌ BLOCKED: Attempted to get data for {pair}")
                return {}
            
            # Request real data from market data receiver
            response = requests.get(
                f"{self.market_data_url}/market-data/venom-feed",
                params={'symbol': pair},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify we got real data
                if data and data.get('is_real', False):
                    logger.debug(f"✅ Real data received for {pair}")
                    return data
                else:
                    logger.warning(f"⚠️ No real data available for {pair}")
                    return {}
            else:
                logger.warning(f"⚠️ Market data service error for {pair}: {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get real data for {pair}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error getting data for {pair}: {e}")
            return {}
    
    def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict:
        """
        DISABLED - NO FAKE DATA GENERATION ALLOWED
        This method will raise an error if called
        """
        raise RuntimeError(
            f"FAKE DATA GENERATION FORBIDDEN! "
            f"Attempted to generate synthetic data for {pair}. "
            f"Only real market data from HTTP feed is allowed."
        )
    
    def generate_venom_signal(self, pair: str, timestamp: datetime) -> Optional[Dict]:
        """
        Generate signal ONLY if real data is available
        """
        # Get real market data
        market_data = self.get_real_mt5_data(pair)
        
        # If no real data and we require it, skip signal generation
        if not market_data and self.require_real_data:
            logger.info(f"⏭️ Skipping {pair} - no real market data available")
            return None
        
        # If we have data, use parent's signal generation
        if market_data:
            # Temporarily store the data for parent method
            self._temp_market_data = market_data
            
            # Call parent method which will use our real data
            signal = super().generate_venom_signal(pair, timestamp)
            
            # Clean up
            self._temp_market_data = None
            
            return signal
        
        return None
    
    def get_market_data_status(self) -> Dict:
        """Check status of market data connection"""
        try:
            response = requests.get(
                f"{self.market_data_url}/market-data/health",
                timeout=2
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def validate_data_sources(self) -> Dict[str, bool]:
        """Validate which symbols have real data available"""
        try:
            response = requests.get(
                f"{self.market_data_url}/market-data/all",
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                symbols_data = data.get('symbols', {})
                
                result = {}
                for symbol in self.symbols:
                    symbol_info = symbols_data.get(symbol, {})
                    # Symbol is valid if it has data and it's not stale
                    is_valid = (
                        symbol in symbols_data and 
                        not symbol_info.get('is_stale', True) and
                        symbol_info.get('source_count', 0) > 0
                    )
                    result[symbol] = is_valid
                
                return result
            else:
                # If service is down, all symbols invalid
                return {symbol: False for symbol in self.symbols}
                
        except Exception as e:
            logger.error(f"Failed to validate data sources: {e}")
            return {symbol: False for symbol in self.symbols}


def main():
    """Test the real data only VENOM"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create real data only engine
    engine = ApexVenomV7RealDataOnly()
    
    # Check market data status
    print("\n📊 Market Data Status:")
    status = engine.get_market_data_status()
    print(json.dumps(status, indent=2))
    
    # Validate data sources
    print("\n✅ Data Source Validation:")
    validation = engine.validate_data_sources()
    for symbol, is_valid in validation.items():
        print(f"  {symbol}: {'✅ Valid' if is_valid else '❌ No data'}")
    
    # Try to generate a signal
    print("\n🎯 Testing Signal Generation:")
    
    # Test with EURUSD
    signal = engine.generate_venom_signal("EURUSD", datetime.now())
    if signal:
        print(f"✅ Generated signal: {signal['signal_id']}")
    else:
        print("❌ No signal generated (likely no real data)")
    
    # Test blocking XAUUSD
    print("\n🚫 Testing XAUUSD blocking:")
    try:
        data = engine.get_real_mt5_data("XAUUSD")
        print(f"Data received: {data}")
    except Exception as e:
        print(f"✅ Correctly blocked: {e}")


if __name__ == "__main__":
    main()