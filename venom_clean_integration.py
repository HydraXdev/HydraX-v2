#!/usr/bin/env python3
"""
VENOM v7.0 Clean Integration
Simplified data flow from Unified Market Service
100% REAL DATA - NO FAKE/SYNTHETIC
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Import base VENOM and CITADEL
import sys
sys.path.insert(0, '/root/HydraX-v2')
sys.path.insert(0, '/root/HydraX-v2/src')

from apex_venom_v7_unfiltered import ApexVenomV7Unfiltered
from citadel_core.citadel_analyzer import CitadelAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VenomCleanIntegration:
    """Clean VENOM + CITADEL integration with unified market service"""
    
    def __init__(self):
        self.market_url = "http://127.0.0.1:8001/market-data"
        self.webapp_url = "http://127.0.0.1:8888/api/signals"
        self.venom = ApexVenomV7Unfiltered()
        self.citadel = CitadelAnalyzer()
        
        logger.info("🐍 VENOM v7.0 Clean Integration Started")
        logger.info("📡 Market data: Unified service at port 8001")
        logger.info("🛡️ CITADEL Shield: Active")
        logger.info("🔒 100% REAL DATA GUARANTEED")
        
    def get_market_data(self, symbol: str) -> Dict:
        """Get real market data for a symbol"""
        try:
            response = requests.get(f"{self.market_url}/get/{symbol}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return {}
    
    def scan_for_signals(self) -> List[Dict]:
        """Scan all pairs for signals"""
        signals = []
        
        # Get all available market data
        try:
            response = requests.get(f"{self.market_url}/all", timeout=5)
            if response.status_code != 200:
                logger.error("Market data service unavailable")
                return signals
            
            all_data = response.json()
            logger.info(f"📊 Market data available for {len(all_data)} pairs")
            
            # Process each pair with data
            for symbol, data in all_data.items():
                # Skip if no valid data
                if not data or data.get('bid', 0) == 0:
                    continue
                
                # Convert to VENOM format
                market_data = {
                    'close': data['bid'],
                    'spread': data['spread'],
                    'volume': data['volume'],
                    'timestamp': datetime.now()
                }
                
                # VENOM expects the data to be returned by get_real_mt5_data
                # We'll temporarily override this method
                def get_data():
                    return market_data
                
                # Temporarily set the method
                original_method = getattr(self.venom, 'get_real_mt5_data', None)
                self.venom.get_real_mt5_data = lambda pair: market_data if pair == symbol else {}
                
                # Generate VENOM signal
                signal = self.venom.generate_venom_signal(symbol, datetime.now())
                
                # Restore original method if it existed
                if original_method:
                    self.venom.get_real_mt5_data = original_method
                
                if signal and signal.get('confidence', 0) > 0:
                    # Enhance with CITADEL
                    citadel_result = self.citadel.analyze_signal(signal, market_data)
                    
                    # Add CITADEL shield data
                    # Calculate risk multiplier based on classification
                    risk_multipliers = {
                        'SHIELD_APPROVED': 1.5,
                        'SHIELD_ACTIVE': 1.0,
                        'VOLATILITY_ZONE': 0.5,
                        'UNVERIFIED': 0.25
                    }
                    
                    signal['citadel_shield'] = {
                        'score': citadel_result['shield_score'],
                        'classification': citadel_result['classification'],
                        'risk_multiplier': risk_multipliers.get(citadel_result['classification'], 1.0)
                    }
                    
                    signals.append(signal)
                    logger.info(f"🎯 Signal: {symbol} {signal['direction']} @ {signal['confidence']}% | Shield: {citadel_result['shield_score']}/10")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error scanning for signals: {e}")
            return signals
    
    def send_to_webapp(self, signal: Dict) -> bool:
        """Send signal to WebApp/BittenCore"""
        try:
            response = requests.post(self.webapp_url, json=signal, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending signal to webapp: {e}")
            return False
    
    def run_scanner(self, interval=30):
        """Run continuous signal scanning"""
        logger.info(f"🚀 Starting signal scanner (interval: {interval}s)")
        
        while True:
            try:
                # Check market service health
                health_response = requests.get(f"{self.market_url}/health", timeout=2)
                if health_response.status_code != 200:
                    logger.error("Market service offline - waiting...")
                    time.sleep(10)
                    continue
                
                health = health_response.json()
                logger.info(f"✅ Market service healthy: {health['active_symbols']} active pairs")
                
                # Scan for signals
                signals = self.scan_for_signals()
                
                if signals:
                    logger.info(f"📈 Found {len(signals)} signals")
                    
                    # Send high-quality signals to webapp
                    for signal in signals:
                        shield_score = signal.get('citadel_shield', {}).get('score', 0)
                        if shield_score >= 4.0:  # Only send 4.0+ shield scores
                            if self.send_to_webapp(signal):
                                logger.info(f"✅ Signal sent: {signal['pair']} (Shield: {shield_score}/10)")
                            else:
                                logger.error(f"❌ Failed to send signal: {signal['pair']}")
                else:
                    logger.info("📊 No signals found this scan")
                
                # Wait for next scan
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    scanner = VenomCleanIntegration()
    scanner.run_scanner()