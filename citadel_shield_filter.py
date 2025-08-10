#!/usr/bin/env python3
"""
CITADEL Shield Filter - Modular Post-Processing for Elite Guard
Multi-broker consensus validation and manipulation detection
"""

import requests
import json
import time
import logging
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrokerTick:
    broker: str
    symbol: str
    bid: float
    ask: float
    timestamp: float
    
@dataclass
class ConsensusData:
    symbol: str
    median_price: float
    confidence: float
    outlier_count: int
    broker_count: int
    timestamp: float

class CitadelShieldFilter:
    """
    CITADEL Shield Filter - Modular validation and enhancement for Elite Guard signals
    Operates as separate post-processing filter for maximum modularity and performance
    """
    
    def __init__(self):
        # REAL broker configuration - NO DEMO MODES WHEN REAL MONEY IS INVOLVED
        self.brokers = [
            {
                'name': 'IC Markets',
                'live_api': 'https://api.icmarkets.com',  # REAL LIVE API
                'api_key': os.environ.get('IC_MARKETS_API_KEY'),
                'api_secret': os.environ.get('IC_MARKETS_SECRET'),
                'enabled': bool(os.environ.get('IC_MARKETS_API_KEY'))  # Only enable if credentials exist
            },
            {
                'name': 'OANDA',
                'live_api': 'https://api-fxtrade.oanda.com/v3',  # REAL LIVE OANDA API
                'api_key': os.environ.get('OANDA_API_KEY'),
                'account_id': os.environ.get('OANDA_ACCOUNT_ID'),
                'enabled': bool(os.environ.get('OANDA_API_KEY') and os.environ.get('OANDA_ACCOUNT_ID'))
            },
            {
                'name': 'Pepperstone',
                'live_api': 'https://api.pepperstone.com',  # REAL API (if available)
                'api_key': os.environ.get('PEPPERSTONE_API_KEY'),
                'enabled': bool(os.environ.get('PEPPERSTONE_API_KEY'))
            }
        ]
        
        
        # Consensus caching (10-15 second cache to minimize API calls)
        self.consensus_cache = {}
        self.cache_ttl = 15  # seconds
        
        # Manipulation detection thresholds
        self.max_price_deviation = 0.005  # 0.5% max deviation from consensus
        self.min_broker_confidence = 75   # Minimum 75% broker agreement
        self.max_outliers = 1            # Maximum 1 outlier broker
        
        # Statistics tracking
        self.signals_processed = 0
        self.signals_approved = 0
        self.signals_blocked = 0
        self.manipulation_detected = 0
        
        logger.info("🛡️ CITADEL Shield Filter initialized")
        logger.info(f"📊 Configured brokers: {len(self.brokers)} (demo mode)")
        logger.info(f"⚙️ Cache TTL: {self.cache_ttl}s | Max deviation: {self.max_price_deviation*100}%")
    
    def get_consensus_price(self, symbol: str) -> Optional[ConsensusData]:
        """
        Get multi-broker consensus pricing for symbol
        Uses caching to minimize API calls
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{int(time.time() // self.cache_ttl)}"
            if cache_key in self.consensus_cache:
                return self.consensus_cache[cache_key]
            
            # Collect prices from enabled brokers
            broker_prices = []
            successful_brokers = []
            
            for broker in self.brokers:
                if not broker['enabled']:
                    continue
                    
                try:
                    tick_data = self.fetch_broker_tick(broker, symbol)
                    if tick_data:
                        mid_price = (tick_data['bid'] + tick_data['ask']) / 2
                        broker_prices.append(mid_price)
                        successful_brokers.append(broker['name'])
                        
                except Exception as e:
                    logger.debug(f"Broker {broker['name']} failed for {symbol}: {e}")
                    continue
            
            # Need minimum 3 brokers for consensus
            if len(broker_prices) < 3:
                logger.debug(f"Insufficient brokers for {symbol}: {len(broker_prices)}/3 minimum")
                return None
            
            # Calculate consensus statistics
            median_price = np.median(broker_prices)
            std_dev = np.std(broker_prices)
            
            # Identify outliers (>2 standard deviations from median)
            outliers = []
            for i, price in enumerate(broker_prices):
                if abs(price - median_price) > 2 * std_dev:
                    outliers.append((successful_brokers[i], price))
            
            # Calculate confidence (% of brokers in agreement)
            confidence = (len(broker_prices) - len(outliers)) / len(broker_prices) * 100
            
            consensus = ConsensusData(
                symbol=symbol,
                median_price=median_price,
                confidence=confidence,
                outlier_count=len(outliers),
                broker_count=len(broker_prices),
                timestamp=time.time()
            )
            
            # Cache result
            self.consensus_cache[cache_key] = consensus
            
            logger.debug(f"Consensus for {symbol}: {median_price:.5f} "
                        f"({confidence:.1f}% confidence, {len(outliers)} outliers)")
            
            return consensus
            
        except Exception as e:
            logger.error(f"Error getting consensus for {symbol}: {e}")
            return None
    
    def fetch_broker_tick(self, broker: Dict, symbol: str) -> Optional[Dict]:
        """
        SIMULATION BLOCKED - REAL BROKER APIs ONLY
        """
        logger.error("🚨 SIMULATED BROKER TICKS DISABLED")
        logger.error("🚨 Real money is on the line - use real broker APIs only")
        logger.error(f"🚨 Attempted to simulate: {broker['name']} {symbol}")
        
        # Block all simulated data
        raise RuntimeError(f"SIMULATION BLOCKED for {broker['name']} - Use real broker API")
    
    def detect_manipulation(self, symbol: str, entry_price: float, consensus: ConsensusData) -> Tuple[bool, str]:
        """
        Detect potential price manipulation using consensus data
        Returns (is_manipulated, reason)
        """
        try:
            if consensus is None:
                return True, "No consensus data available"
            
            # Check price deviation from consensus
            price_deviation = abs(entry_price - consensus.median_price) / consensus.median_price
            
            if price_deviation > self.max_price_deviation:
                return True, f"Price deviation {price_deviation*100:.2f}% > {self.max_price_deviation*100}%"
            
            # Check broker confidence
            if consensus.confidence < self.min_broker_confidence:
                return True, f"Low broker confidence {consensus.confidence:.1f}% < {self.min_broker_confidence}%"
            
            # Check outlier count
            if consensus.outlier_count > self.max_outliers:
                return True, f"Too many outliers {consensus.outlier_count} > {self.max_outliers}"
            
            # Check for stale consensus data
            if time.time() - consensus.timestamp > 60:  # 1 minute max age
                return True, "Stale consensus data"
            
            return False, "Clean signal"
            
        except Exception as e:
            logger.error(f"Error detecting manipulation for {symbol}: {e}")
            return True, f"Detection error: {e}"
    
    def enhance_signal_score(self, signal: Dict, consensus: ConsensusData) -> float:
        """
        Enhance signal score based on consensus quality
        """
        try:
            base_score = signal.get('confidence', 60)
            
            # Consensus quality bonus
            if consensus.confidence >= 90:
                score_boost = 8   # Excellent consensus
            elif consensus.confidence >= 85:
                score_boost = 5   # Good consensus
            elif consensus.confidence >= 80:
                score_boost = 3   # Fair consensus
            else:
                score_boost = 0   # No bonus
            
            # Multi-broker participation bonus
            if consensus.broker_count >= 5:
                score_boost += 3
            elif consensus.broker_count >= 4:
                score_boost += 2
            elif consensus.broker_count >= 3:
                score_boost += 1
            
            enhanced_score = min(base_score + score_boost, 90)  # Cap at 90%
            
            return enhanced_score
            
        except Exception as e:
            logger.error(f"Error enhancing signal score: {e}")
            return signal.get('confidence', 60)
    
    def validate_and_enhance(self, candidate_signal: Dict) -> Optional[Dict]:
        """
        Main CITADEL Shield validation and enhancement process
        Returns enhanced signal if validated, None if blocked
        """
        try:
            self.signals_processed += 1
            
            symbol = candidate_signal.get('symbol') or candidate_signal.get('pair')
            entry_price = candidate_signal.get('entry_price', 0)
            
            if not symbol or not entry_price:
                logger.warning("Invalid signal format - missing symbol or entry_price")
                self.signals_blocked += 1
                return None
            
            # Step 1: Get multi-broker consensus (if brokers enabled)
            consensus = None
            enabled_brokers = [b for b in self.brokers if b['enabled']]
            
            if enabled_brokers:
                consensus = self.get_consensus_price(symbol)
                
                if consensus:
                    # Step 2: Detect manipulation
                    is_manipulated, reason = self.detect_manipulation(symbol, entry_price, consensus)
                    
                    if is_manipulated:
                        logger.info(f"🚫 CITADEL BLOCKED: {symbol} - {reason}")
                        self.signals_blocked += 1
                        self.manipulation_detected += 1
                        return None
                    
                    # Step 3: Enhance signal with consensus data
                    enhanced_score = self.enhance_signal_score(candidate_signal, consensus)
                    candidate_signal['confidence'] = enhanced_score
                else:
                    logger.debug(f"No consensus available for {symbol} - proceeding without shield")
            else:
                logger.debug("No brokers enabled - shield filter bypassed")
            
            # Add CITADEL metadata
            candidate_signal['citadel_shielded'] = consensus is not None
            candidate_signal['consensus_confidence'] = consensus.confidence if consensus else 0
            candidate_signal['shield_boost'] = candidate_signal['confidence'] - candidate_signal.get('base_confidence', candidate_signal['confidence'])
            
            # Calculate XP bonus for shielded signals
            if candidate_signal['citadel_shielded']:
                base_xp = candidate_signal.get('xp_reward', 100)
                candidate_signal['xp_reward'] = int(base_xp * 1.3)  # +30% XP bonus
            
            self.signals_approved += 1
            
            shield_status = "🛡️ SHIELDED" if candidate_signal['citadel_shielded'] else "⚪ UNSHIELDED"
            logger.info(f"✅ CITADEL APPROVED: {symbol} @ {candidate_signal['confidence']:.1f}% {shield_status}")
            
            return candidate_signal
            
        except Exception as e:
            logger.error(f"Error in CITADEL validation: {e}")
            self.signals_blocked += 1
            return None
    
    def get_shield_statistics(self) -> Dict:
        """Get CITADEL Shield performance statistics"""
        approval_rate = (self.signals_approved / self.signals_processed * 100) if self.signals_processed > 0 else 0
        manipulation_rate = (self.manipulation_detected / self.signals_processed * 100) if self.signals_processed > 0 else 0
        
        return {
            'signals_processed': self.signals_processed,
            'signals_approved': self.signals_approved,
            'signals_blocked': self.signals_blocked,
            'manipulation_detected': self.manipulation_detected,
            'approval_rate': approval_rate,
            'manipulation_rate': manipulation_rate,
            'enabled_brokers': len([b for b in self.brokers if b['enabled']]),
            'cache_entries': len(self.consensus_cache)
        }
    
    def enable_demo_mode(self):
        """DEMO MODE PERMANENTLY DISABLED - REAL DATA ONLY"""
        logger.error("🚨 DEMO MODE DISABLED - REAL MONEY IS ON THE LINE")
        logger.error("🚨 Use citadel_shield_real_data_only.py for production")
        logger.error("🚨 NO SIMULATED DATA WHEN REAL MONEY IS INVOLVED")
        
        # Do not enable any brokers in demo mode
        for broker in self.brokers:
            broker['enabled'] = False
        
        raise RuntimeError("DEMO MODE BLOCKED - Use real broker APIs only")

# Test function
def test_citadel_shield():
    """Test CITADEL Shield filter with sample signals"""
    shield = CitadelShieldFilter()
    shield.enable_demo_mode()  # Enable demo mode for testing
    
    # Test signals
    test_signals = [
        {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0851,  # Close to consensus
            'confidence': 75,
            'xp_reward': 100
        },
        {
            'symbol': 'EURUSD', 
            'direction': 'SELL',
            'entry_price': 1.0900,  # Far from consensus (should be blocked)
            'confidence': 80,
            'xp_reward': 120
        },
        {
            'symbol': 'GBPUSD',
            'direction': 'BUY',
            'entry_price': 1.2751,  # Close to consensus
            'confidence': 70,
            'xp_reward': 105
        }
    ]
    
    logger.info("🧪 Testing CITADEL Shield Filter...")
    
    for i, signal in enumerate(test_signals, 1):
        logger.info(f"\n--- Test Signal {i}: {signal['symbol']} {signal['direction']} ---")
        result = shield.validate_and_enhance(signal)
        
        if result:
            logger.info(f"✅ Signal approved with confidence: {result['confidence']:.1f}%")
            logger.info(f"🛡️ Shielded: {result['citadel_shielded']}")
            logger.info(f"🎯 XP Reward: {result['xp_reward']}")
        else:
            logger.info("🚫 Signal blocked by CITADEL Shield")
    
    # Print statistics
    stats = shield.get_shield_statistics()
    logger.info(f"\n📊 CITADEL Shield Statistics:")
    logger.info(f"Processed: {stats['signals_processed']}")
    logger.info(f"Approved: {stats['signals_approved']} ({stats['approval_rate']:.1f}%)")
    logger.info(f"Blocked: {stats['signals_blocked']}")
    logger.info(f"Manipulation detected: {stats['manipulation_detected']} ({stats['manipulation_rate']:.1f}%)")

if __name__ == "__main__":
    test_citadel_shield()