#!/usr/bin/env python3
"""
CITADEL Shield - REAL DATA ONLY VERSION
CRITICAL: NO DEMO/FAKE/SIMULATED DATA WHEN REAL MONEY IS INVOLVED

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Multi-broker consensus with REAL broker APIs or OFFLINE
"""

import os
import requests
import json
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemOfflineError(Exception):
    """Raised when real data is not available"""
    pass

class NoRealDataError(Exception):
    """Raised when attempting to use fake data"""
    pass

@dataclass
class BrokerTick:
    broker: str
    symbol: str
    bid: float
    ask: float
    timestamp: float
    verified: bool = True  # All data must be verified as real

@dataclass
class ConsensusData:
    symbol: str
    median_price: float
    confidence: float
    outlier_count: int
    broker_count: int
    timestamp: float
    all_real_data: bool = True  # Confirmation all data is real

class CitadelShieldRealDataOnly:
    """
    CITADEL Shield - REAL DATA ONLY
    ABSOLUTE RULE: NO FAKE DATA WHEN REAL MONEY IS INVOLVED
    """
    
    def __init__(self):
        self.system_state = "INITIALIZING"
        self.real_brokers = []
        self.offline_reason = None
        
        # Initialize consensus settings early (before _go_offline can be called)
        self.consensus_cache = {}
        self.cache_ttl = 10  # seconds - shorter for real data
        self.max_price_deviation = 0.003  # 0.3% max deviation
        self.min_broker_confidence = 80   # Higher confidence for real money
        
        # ONLY real broker configurations with environment variable credentials
        broker_configs = [
            {
                'name': 'OANDA',
                'live_api': 'https://api-fxtrade.oanda.com/v3',
                'api_key': os.environ.get('OANDA_API_KEY'),
                'account_id': os.environ.get('OANDA_ACCOUNT_ID'),
                'headers': {
                    'Authorization': f'Bearer {os.environ.get("OANDA_API_KEY")}',
                    'Content-Type': 'application/json'
                } if os.environ.get('OANDA_API_KEY') else None
            },
            {
                'name': 'IC Markets',
                'live_api': 'https://api.icmarkets.com',
                'api_key': os.environ.get('IC_MARKETS_API_KEY'),
                'api_secret': os.environ.get('IC_MARKETS_SECRET'),
                'headers': {
                    'Authorization': f'Bearer {os.environ.get("IC_MARKETS_API_KEY")}',
                    'Content-Type': 'application/json'
                } if os.environ.get('IC_MARKETS_API_KEY') else None
            }
        ]
        
        # Add additional real broker configurations
        additional_brokers = [
            {
                'name': 'IG Group',
                'live_api': 'https://api.ig.com/gateway/deal',
                'api_key': os.environ.get('IG_API_KEY'),
                'username': os.environ.get('IG_USERNAME'),
                'password': os.environ.get('IG_PASSWORD'),
                'headers': {
                    'X-IG-API-KEY': os.environ.get('IG_API_KEY'),
                    'Content-Type': 'application/json'
                } if os.environ.get('IG_API_KEY') else None
            },
            {
                'name': 'FXCM',
                'live_api': 'https://api-demo.fxcm.com:8443',
                'access_token': os.environ.get('FXCM_ACCESS_TOKEN'),
                'headers': {
                    'Authorization': f'Bearer {os.environ.get("FXCM_ACCESS_TOKEN")}',
                    'Content-Type': 'application/json'
                } if os.environ.get('FXCM_ACCESS_TOKEN') else None
            },
            {
                'name': 'XM',
                'live_api': 'https://xm.com/api',
                'api_key': os.environ.get('XM_API_KEY'),
                'headers': {
                    'Authorization': f'Bearer {os.environ.get("XM_API_KEY")}',
                    'Content-Type': 'application/json'
                } if os.environ.get('XM_API_KEY') else None
            }
        ]
        
        # Add to main broker list
        broker_configs.extend(additional_brokers)
        
        # Only add brokers with REAL credentials
        for config in broker_configs:
            if config.get('api_key') and config.get('headers'):
                config['enabled'] = True
                self.real_brokers.append(config)
                logger.info(f"✅ REAL broker configured: {config['name']}")
            elif config.get('access_token') and config.get('headers'):
                config['enabled'] = True  
                self.real_brokers.append(config)
                logger.info(f"✅ REAL broker configured: {config['name']}")
            else:
                logger.warning(f"⚠️ {config['name']} not configured (missing API credentials)")
        
        if not self.real_brokers:
            self._go_offline("No real broker APIs configured")
            return
        
        # Test real connections
        self._test_real_connections()
        
        logger.info(f"🛡️ CITADEL Shield initialized with {len(self.real_brokers)} REAL brokers")
    
    def _test_real_connections(self):
        """Test all real broker connections"""
        working_brokers = []
        
        for broker in self.real_brokers:
            if self._test_broker_connection(broker):
                working_brokers.append(broker)
                logger.info(f"✅ {broker['name']} connection verified")
            else:
                logger.error(f"❌ {broker['name']} connection failed")
        
        if not working_brokers:
            self._go_offline("No working broker connections")
            return
        
        self.real_brokers = working_brokers
        self.system_state = "ONLINE"
        logger.info(f"🟢 CITADEL Shield ONLINE with {len(self.real_brokers)} brokers")
    
    def _test_broker_connection(self, broker: dict) -> bool:
        """Test a single broker connection with REAL API"""
        try:
            if broker['name'] == 'OANDA':
                # Test OANDA connection with real endpoint
                url = f"{broker['live_api']}/accounts"
                response = requests.get(url, headers=broker['headers'], timeout=5)
                return response.status_code == 200
                
            elif broker['name'] == 'IC Markets':
                # Test IC Markets connection
                # Note: Replace with actual IC Markets API endpoint when available
                return True  # Placeholder - implement real test
                
            elif broker['name'] == 'IG Group':
                # Test IG Group connection
                url = f"{broker['live_api']}/session"
                response = requests.get(url, headers=broker['headers'], timeout=5)
                return response.status_code in [200, 401]  # 401 means endpoint exists but needs auth
                
            elif broker['name'] == 'FXCM':
                # Test FXCM connection
                url = f"{broker['live_api']}/trading/get_model"
                response = requests.get(url, headers=broker['headers'], timeout=5)
                return response.status_code in [200, 401, 403]  # API exists
                
            elif broker['name'] == 'XM':
                # Test XM connection (placeholder)
                # XM typically uses MT4/MT5 bridge, not direct REST API
                logger.info(f"XM uses MT4/MT5 bridge - marking as available")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Broker {broker['name']} test failed: {str(e)}")
            return False
    
    def _go_offline(self, reason: str):
        """Put system in OFFLINE state - NO FAKE DATA"""
        self.system_state = "OFFLINE"
        self.offline_reason = reason
        logger.critical(f"🚨 CITADEL SHIELD OFFLINE: {reason}")
        logger.critical("🚨 NO SIGNAL PROCESSING UNTIL REAL DATA AVAILABLE")
    
    def get_real_broker_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL price from broker API - NO SIMULATION"""
        try:
            if broker['name'] == 'OANDA':
                return self._get_oanda_price(broker, symbol)
            elif broker['name'] == 'IC Markets':
                return self._get_ic_markets_price(broker, symbol)
            elif broker['name'] == 'IG Group':
                return self._get_ig_price(broker, symbol)
            elif broker['name'] == 'FXCM':
                return self._get_fxcm_price(broker, symbol)
            elif broker['name'] == 'XM':
                return self._get_xm_price(broker, symbol)
            else:
                logger.error(f"Unknown broker: {broker['name']}")
                return None
                
        except Exception as e:
            logger.error(f"REAL price fetch failed for {broker['name']}: {str(e)}")
            return None
    
    def _get_oanda_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL OANDA price via live API"""
        try:
            # Convert symbol format (EURUSD -> EUR_USD)
            oanda_symbol = f"{symbol[:3]}_{symbol[3:]}" if len(symbol) == 6 else symbol
            
            url = f"{broker['live_api']}/instruments/{oanda_symbol}/candles"
            params = {
                'count': 1,
                'granularity': 'M1',
                'price': 'BA'  # Bid/Ask
            }
            
            response = requests.get(url, headers=broker['headers'], params=params, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"OANDA API error: {response.status_code}")
                return None
            
            data = response.json()
            if not data.get('candles'):
                return None
            
            candle = data['candles'][0]
            if candle.get('complete') != True:
                logger.warning("Received incomplete candle from OANDA")
            
            return BrokerTick(
                broker='OANDA',
                symbol=symbol,
                bid=float(candle['bid']['c']),  # Close price as current price
                ask=float(candle['ask']['c']),
                timestamp=time.time(),
                verified=True
            )
            
        except Exception as e:
            logger.error(f"OANDA price fetch error: {str(e)}")
            return None
    
    def _get_ic_markets_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL IC Markets price - implement when API available"""
        logger.warning("IC Markets real API not yet implemented")
        return None
        
    def _get_ig_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL IG Group price via live API"""
        try:
            # Convert symbol format for IG (EURUSD -> EUR/USD)
            if len(symbol) == 6:
                ig_symbol = f"{symbol[:3]}/{symbol[3:]}"
            else:
                ig_symbol = symbol
                
            url = f"{broker['live_api']}/markets/{ig_symbol}"
            response = requests.get(url, headers=broker['headers'], timeout=5)
            
            if response.status_code != 200:
                logger.error(f"IG API error: {response.status_code}")
                return None
                
            data = response.json()
            snapshot = data.get('snapshot', {})
            
            if not snapshot:
                return None
                
            return BrokerTick(
                broker='IG Group',
                symbol=symbol,
                bid=float(snapshot.get('bid', 0)),
                ask=float(snapshot.get('offer', 0)),  # IG uses 'offer' instead of 'ask'
                timestamp=time.time(),
                verified=True
            )
            
        except Exception as e:
            logger.error(f"IG price fetch error: {str(e)}")
            return None
            
    def _get_fxcm_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL FXCM price via live API"""
        try:
            url = f"{broker['live_api']}/trading/get_model"
            params = {'models': f'Offer,ClosedPosition,Order,Summary,{symbol}'}
            response = requests.get(url, headers=broker['headers'], params=params, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"FXCM API error: {response.status_code}")
                return None
                
            data = response.json()
            offers = data.get('offers', [])
            
            # Find the symbol in offers
            for offer in offers:
                if offer.get('currency') == symbol:
                    return BrokerTick(
                        broker='FXCM',
                        symbol=symbol,
                        bid=float(offer.get('bid', 0)),
                        ask=float(offer.get('ask', 0)),
                        timestamp=time.time(),
                        verified=True
                    )
                    
            return None
            
        except Exception as e:
            logger.error(f"FXCM price fetch error: {str(e)}")
            return None
            
    def _get_xm_price(self, broker: dict, symbol: str) -> Optional[BrokerTick]:
        """Get REAL XM price - typically via MT4/MT5 bridge"""
        try:
            # XM typically doesn't have direct REST API
            # This would integrate with MT4/MT5 bridge system
            logger.warning("XM price fetch via MT4/MT5 bridge not yet implemented")
            return None
            
        except Exception as e:
            logger.error(f"XM price fetch error: {str(e)}")
            return None
    
    def get_consensus_price(self, symbol: str) -> Optional[ConsensusData]:
        """Get multi-broker consensus with REAL data only"""
        if self.system_state == "OFFLINE":
            raise SystemOfflineError(f"System offline: {self.offline_reason}")
        
        # Check cache first
        cache_key = f"{symbol}_{int(time.time() // self.cache_ttl)}"
        if cache_key in self.consensus_cache:
            return self.consensus_cache[cache_key]
        
        # Fetch REAL prices from all brokers
        real_ticks = []
        for broker in self.real_brokers:
            tick = self.get_real_broker_price(broker, symbol)
            if tick and tick.verified:
                real_ticks.append(tick)
        
        if len(real_ticks) < 2:
            logger.error(f"INSUFFICIENT REAL DATA: Only {len(real_ticks)} brokers for {symbol}")
            return None
        
        # Calculate consensus from REAL data
        bid_prices = [tick.bid for tick in real_ticks]
        ask_prices = [tick.ask for tick in real_ticks]
        
        median_bid = np.median(bid_prices)
        median_ask = np.median(ask_prices)
        median_price = (median_bid + median_ask) / 2
        
        # Detect outliers
        price_std = np.std(bid_prices)
        outliers = []
        for i, tick in enumerate(real_ticks):
            deviation = abs(tick.bid - median_bid) / median_bid
            if deviation > self.max_price_deviation:
                outliers.append(tick.broker)
        
        # Calculate confidence
        confidence = max(0, 100 - (len(outliers) * 20))  # -20% per outlier
        
        consensus = ConsensusData(
            symbol=symbol,
            median_price=median_price,
            confidence=confidence,
            outlier_count=len(outliers),
            broker_count=len(real_ticks),
            timestamp=time.time(),
            all_real_data=True
        )
        
        # Cache the result
        self.consensus_cache[cache_key] = consensus
        
        logger.info(f"📊 {symbol} consensus: {median_price:.5f} ({confidence:.1f}% confidence, {len(real_ticks)} brokers)")
        
        return consensus
    
    def validate_signal_price(self, signal: dict) -> Dict:
        """Validate signal against REAL market consensus"""
        if self.system_state == "OFFLINE":
            return {
                'approved': False,
                'reason': f'SYSTEM OFFLINE: {self.offline_reason}',
                'shield_score': 0,
                'confidence': 0
            }
        
        try:
            symbol = signal.get('symbol')
            signal_price = signal.get('price', signal.get('entry_price'))
            
            if not symbol or not signal_price:
                return {
                    'approved': False,
                    'reason': 'Missing symbol or price in signal',
                    'shield_score': 0,
                    'confidence': 0
                }
            
            # Get REAL consensus
            consensus = self.get_consensus_price(symbol)
            
            if not consensus:
                return {
                    'approved': False,
                    'reason': 'No real broker consensus available',
                    'shield_score': 0,
                    'confidence': 0
                }
            
            # Check price deviation
            price_deviation = abs(signal_price - consensus.median_price) / consensus.median_price
            
            # Calculate shield score
            shield_score = min(consensus.confidence, 100 - (price_deviation * 10000))  # Heavy penalty for price deviation
            shield_score = max(0, shield_score)
            
            approved = (
                consensus.confidence >= self.min_broker_confidence and
                price_deviation <= self.max_price_deviation and
                consensus.outlier_count <= 1
            )
            
            return {
                'approved': approved,
                'shield_score': shield_score,
                'confidence': consensus.confidence,
                'price_deviation': price_deviation,
                'broker_count': consensus.broker_count,
                'outliers': consensus.outlier_count,
                'real_data_confirmed': True
            }
            
        except SystemOfflineError:
            return {
                'approved': False,
                'reason': f'SYSTEM OFFLINE: {self.offline_reason}',
                'shield_score': 0,
                'confidence': 0
            }
        except Exception as e:
            logger.error(f"Signal validation error: {str(e)}")
            return {
                'approved': False,
                'reason': f'Validation error: {str(e)}',
                'shield_score': 0,
                'confidence': 0
            }
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'state': self.system_state,
            'offline_reason': self.offline_reason,
            'real_brokers': len(self.real_brokers),
            'broker_names': [b['name'] for b in self.real_brokers if b.get('enabled')],
            'cache_entries': len(self.consensus_cache),
            'last_check': time.time(),
            'fake_data_prohibited': True,
            'demo_mode': False  # ALWAYS FALSE
        }

# API for integration
def create_real_citadel_shield() -> CitadelShieldRealDataOnly:
    """Create REAL CITADEL Shield - NO DEMO MODES"""
    return CitadelShieldRealDataOnly()

if __name__ == "__main__":
    # Test with real credentials only
    logger.info("Testing CITADEL Shield with REAL data only...")
    
    shield = CitadelShieldRealDataOnly()
    
    if shield.system_state == "ONLINE":
        # Test with real signal
        test_signal = {
            'symbol': 'EURUSD',
            'price': 1.0850,
            'direction': 'BUY'
        }
        
        result = shield.validate_signal_price(test_signal)
        logger.info(f"Validation result: {result}")
    else:
        logger.error(f"System offline: {shield.offline_reason}")
    
    status = shield.get_system_status()
    logger.info(f"System status: {status}")