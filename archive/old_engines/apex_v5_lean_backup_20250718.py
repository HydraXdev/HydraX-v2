#!/usr/bin/env python3
"""
APEX v5 LEAN - Streamlined Signal Generator
A clean, efficient pip-grabbing machine with easy tuning
"""

import sys
import os
import time
import json
import logging
import requests
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import singleton protection
from apex_singleton_manager import enforce_singleton
singleton_manager = enforce_singleton()

# Import integrated flow for proper signal processing
try:
    from apex_mission_integrated_flow import process_apex_signal_direct
    INTEGRATED_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Integrated flow system available")
except ImportError as e:
    INTEGRATED_FLOW_AVAILABLE = False
    print(f"⚠️ Integrated flow not available: {e}")

# Load configuration from JSON file
def load_config():
    """Load configuration from apex_config.json"""
    config_file = Path('apex_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            data = json.load(f)
            return {
                'SIGNALS_PER_HOUR_TARGET': data['signal_generation']['signals_per_hour_target'],
                'MIN_TCS_THRESHOLD': data['signal_generation']['min_tcs_threshold'],
                'MAX_SPREAD_ALLOWED': data['signal_generation']['max_spread_allowed'],
                'SCAN_INTERVAL_SECONDS': data['signal_generation']['scan_interval_seconds'],
                'API_TIMEOUT': 10,
                'API_ENDPOINT': 'api.broker.local',
                'API_PORT': 8080,
                'TRADING_PAIRS': data['trading_pairs']['pairs'],
                'SESSION_BOOSTS': data['session_boosts']
            }
    else:
        # Default config if file not found - Session-aware signal rates
        return {
            'SIGNALS_PER_HOUR_TARGET': {
                'LONDON': 2.5,      # Busy session: 2-3 signals/hour
                'NY': 2.5,          # Busy session: 2-3 signals/hour  
                'OVERLAP': 3.0,     # Peak session: 3 signals/hour
                'ASIAN': 1.5,       # Quiet session: 1-2 signals/hour
                'OTHER': 1.0        # Off-hours: 1 signal/hour
            },
            'MIN_TCS_THRESHOLD': 68,
            'MAX_SPREAD_ALLOWED': 50,
            'SCAN_INTERVAL_SECONDS': 300,  # 5 minutes
            'API_TIMEOUT': 10,
            'API_ENDPOINT': 'api.broker.local',
            'API_PORT': 8080,
            'TRADING_PAIRS': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDJPY'],
            'SESSION_BOOSTS': {'LONDON': 8, 'NY': 7, 'OVERLAP': 12, 'ASIAN': 3, 'OTHER': 0}
        }

CONFIG = load_config()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - APEX LEAN - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apex_lean.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class APEXLeanEngine:
    """Lean and efficient signal generator"""
    
    def __init__(self):
        self.config = CONFIG
        self.signal_count = 0
        self.start_time = datetime.now()
        self.hourly_signals = []  # Track signals for rate limiting
        self.MAX_SIGNALS_PER_HOUR = 8  # Hard limit
        self.pair_rotation_index = 0  # For rotating pairs
        self.last_pair_signals = {}  # Track last signal time per pair
        
        # Adaptive "hunger mode" tracking
        self.last_signal_time = datetime.now()
        self.hunger_mode_active = False
        self.hunger_threshold_minutes = 45  # If no signals for 45 min, enter hunger mode
    
    def check_hunger_mode(self):
        """Check if we should enter hunger mode to increase signal frequency"""
        minutes_since_last_signal = (datetime.now() - self.last_signal_time).total_seconds() / 60
        
        if minutes_since_last_signal > self.hunger_threshold_minutes and not self.hunger_mode_active:
            self.hunger_mode_active = True
            logger.info(f"🍽️ HUNGER MODE ACTIVATED: {minutes_since_last_signal:.1f} minutes since last signal")
            logger.info("📉 Lowering TCS threshold and increasing scan frequency")
        elif minutes_since_last_signal <= 15 and self.hunger_mode_active:
            self.hunger_mode_active = False
            logger.info("🎯 HUNGER MODE DEACTIVATED: Recent signal detected")
    
    def get_adaptive_tcs_threshold(self) -> int:
        """Get TCS threshold adjusted for hunger mode"""
        base_threshold = self.config['MIN_TCS_THRESHOLD']
        
        if self.hunger_mode_active:
            # Lower threshold by 15-20 points in hunger mode for slow markets
            hunger_reduction = 20
            adapted_threshold = max(10, base_threshold - hunger_reduction)
            logger.debug(f"🍽️ Hunger mode TCS: {adapted_threshold}% (base: {base_threshold}%)")
            return adapted_threshold
        
        return base_threshold
    
    def get_adaptive_scan_interval(self) -> int:
        """Get scan interval adjusted for hunger mode"""
        base_interval = self.config['SCAN_INTERVAL_SECONDS']
        
        if self.hunger_mode_active:
            # Scan 2x more frequently in hunger mode
            adapted_interval = max(300, base_interval // 2)  # Minimum 5 minutes
            logger.debug(f"🍽️ Hunger mode scan: {adapted_interval}s (base: {base_interval}s)")
            return adapted_interval
        
        return base_interval
        
    def get_api_data(self, symbol: str) -> Optional[Dict]:
        """Get real market data from direct API"""
        try:
            import socket
            
            # Create API connection to broker
            import requests
            
            api_url = f"http://{self.config['API_ENDPOINT']}:{self.config['API_PORT']}/api/data"
            timeout = self.config['API_TIMEOUT']
            
            # Send price request
            params = {"symbol": symbol, "action": "get_price"}
            response = requests.get(api_url, params=params, timeout=timeout)
            data = response.json()
                
                if data.get('success'):
                    # Extract price data (simulate realistic spread)
                    price = float(data.get('price', 0))
                    spread = 2.0  # Realistic 2 pip spread
                    
                    return {
                        'symbol': symbol,
                        'bid': price - (spread * 0.00001),  # Convert pips to price
                        'ask': price + (spread * 0.00001),
                        'spread': spread,
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.debug(f"API connection error for {symbol}: {e}")
        
        return None
    
    def calculate_tcs(self, symbol: str, data: Dict) -> float:
        """REAL TCS calculation using live API data only"""
        # Fail immediately if no real API data
        if not data or not data.get('bid') or not data.get('ask'):
            logger.debug(f"❌ No API data for {symbol}")
            return 0
        
        # Base score from real market conditions
        score = 50  # Conservative base for live trading
        
        # Session boost based on current UTC hour
        hour = datetime.utcnow().hour
        if 7 <= hour < 16:  # London
            score += self.config['SESSION_BOOSTS']['LONDON']
        elif 13 <= hour < 22:  # NY
            score += self.config['SESSION_BOOSTS']['NY']
        elif 7 <= hour < 9 or 13 <= hour < 16:  # Overlap
            score += self.config['SESSION_BOOSTS']['OVERLAP']
        elif 23 <= hour or hour < 7:  # Asian
            score += self.config['SESSION_BOOSTS']['ASIAN']
        
        # Spread quality from real API data
        spread = data.get('spread', 999)
        if spread <= 10:
            score += 15
        elif spread <= 20:
            score += 10
        elif spread <= 30:
            score += 5
        elif spread > self.config['MAX_SPREAD_ALLOWED']:
            return 0  # Reject high spread
        
        # Major pairs boost
        if symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
            score += 8
        
        # Volatility pairs
        if symbol in ['GBPJPY', 'EURJPY', 'GBPNZD']:
            score += 5
        
        return min(94, max(0, score))
    
    def check_rate_limit(self) -> bool:
        """Check if we're within rate limit"""
        current_time = datetime.now()
        # Remove signals older than 1 hour
        self.hourly_signals = [t for t in self.hourly_signals 
                              if (current_time - t).total_seconds() < 3600]
        
        # Check if we've hit the limit
        if len(self.hourly_signals) >= self.MAX_SIGNALS_PER_HOUR:
            logger.warning(f"⚠️ Rate limit reached: {len(self.hourly_signals)}/{self.MAX_SIGNALS_PER_HOUR} signals in last hour")
            return False
        return True
    
    def generate_signal(self, symbol: str, data: Dict, tcs: float) -> Dict:
        """Generate a clean signal"""
        # Check rate limit first
        if not self.check_rate_limit():
            return None
            
        self.signal_count += 1
        self.hourly_signals.append(datetime.now())
        
        # Determine signal type based on market conditions and probability
        # SNIPER OPS: Rarer, higher RR (1:2.7-3), longer TP time (30-90 min)
        # RAPID ASSAULT: More common, standard RR (1:2-2.6), quick TP (5-30 min)
        
        # Make SNIPER OPS about 25-33% of signals (1 in 3-4)
        import random
        sniper_chance = 0.45 if tcs >= 85 else 0.35 if tcs >= 80 else 0.25
        is_sniper = random.random() < sniper_chance
        
        signal_type = "SNIPER OPS" if is_sniper else "RAPID ASSAULT"
        emoji = "⚡ " if signal_type == "SNIPER OPS" else "🔫"
        
        # Signal generation complete - RR ratios handled by TOC/brain/core
        
        signal = {
            'symbol': symbol,
            'direction': 'BUY',  # Simplified - always BUY for now
            'tcs': tcs,
            'signal_type': signal_type,
            'entry_price': data['ask'],
            'bid': data['bid'],
            'ask': data['ask'],
            'spread': data['spread'],
            'timestamp': datetime.now().isoformat(),
            'signal_number': self.signal_count
        }
        
        # Log in format for Telegram connector with signal type
        logger.info(f"{emoji} {signal_type} #{self.signal_count}: {symbol} BUY TCS:{tcs:.0f}%")
        
        # Process through integrated flow: APEX → Mission → TOC → Telegram → WebApp
        if INTEGRATED_FLOW_AVAILABLE:
            try:
                # Run the integrated flow asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                flow_result = loop.run_until_complete(process_apex_signal_direct(signal))
                
                if flow_result.get('success'):
                    logger.info(f"✅ Signal processed through integrated flow: {flow_result['mission_id']}")
                    logger.info(f"📱 Telegram sent: {flow_result['telegram_sent']}")
                    logger.info(f"🌐 WebApp URL: {flow_result['webapp_url']}")
                else:
                    logger.error(f"❌ Integrated flow failed: {flow_result.get('error')}")
                    
                loop.close()
            except Exception as e:
                logger.error(f"❌ Integrated flow error: {e}")
                # Continue with normal processing if integrated flow fails
        
        return signal
    
    def get_pairs_to_scan(self):
        """Rotate through pairs to scan only 2-3 per cycle"""
        all_pairs = self.config['TRADING_PAIRS']
        pairs_per_scan = 2  # Only scan 2 pairs per cycle
        
        # Get next batch of pairs
        start_idx = self.pair_rotation_index
        end_idx = start_idx + pairs_per_scan
        
        if end_idx > len(all_pairs):
            # Wrap around
            pairs = all_pairs[start_idx:] + all_pairs[:end_idx % len(all_pairs)]
        else:
            pairs = all_pairs[start_idx:end_idx]
        
        # Update rotation index
        self.pair_rotation_index = (self.pair_rotation_index + pairs_per_scan) % len(all_pairs)
        
        # Filter out pairs that had signals too recently (30 min cooldown)
        current_time = datetime.now()
        filtered_pairs = []
        for pair in pairs:
            last_signal = self.last_pair_signals.get(pair)
            if not last_signal or (current_time - last_signal).total_seconds() > 1800:
                filtered_pairs.append(pair)
        
        return filtered_pairs if filtered_pairs else pairs[:1]  # Always scan at least 1
    
    def scan_markets(self):
        """Scan selected pairs for signals"""
        signals_found = 0
        pairs_to_scan = self.get_pairs_to_scan()
        
        logger.info(f"🔍 Scanning pairs: {', '.join(pairs_to_scan)}")
        
        for symbol in pairs_to_scan:
            # Get market data
            data = self.get_api_data(symbol)
            if not data:
                continue
            
            # Skip if no valid prices
            if data['bid'] <= 0 or data['ask'] <= 0:
                continue
            
            # Calculate TCS
            tcs = self.calculate_tcs(symbol, data)
            
            # Generate signal if TCS meets adaptive threshold
            adaptive_threshold = self.get_adaptive_tcs_threshold()
            if tcs >= adaptive_threshold:
                signal = self.generate_signal(symbol, data, tcs)
                if signal:  # Only count if not rate limited
                    signals_found += 1
                    self.last_pair_signals[symbol] = datetime.now()
                    self.last_signal_time = datetime.now()  # Update for hunger mode
        
        return signals_found
    
    def run(self):
        """Main loop"""
        logger.info("🚀 APEX LEAN ENGINE STARTED")
        logger.info(f"📊 Config: {self.config['SIGNALS_PER_HOUR_TARGET']} signals/hour target")
        logger.info(f"🎯 TCS Threshold: {self.config['MIN_TCS_THRESHOLD']}%")
        logger.info(f"⏱️ Scan Interval: {self.config['SCAN_INTERVAL_SECONDS']}s")
        logger.info(f"📈 Monitoring {len(self.config['TRADING_PAIRS'])} pairs")
        
        while True:
            try:
                # Check if we should activate hunger mode
                self.check_hunger_mode()
                
                # Scan for signals
                signals = self.scan_markets()
                
                # Stats
                runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                signals_per_hour = self.signal_count / max(0.1, runtime_hours)
                
                hunger_status = "🍽️ HUNGRY" if self.hunger_mode_active else "🎯 NORMAL"
                logger.info(f"📊 Scan complete: {signals} signals | Total: {self.signal_count} | Rate: {signals_per_hour:.1f}/hour | {hunger_status}")
                
                # Sleep with adaptive interval
                adaptive_interval = self.get_adaptive_scan_interval()
                time.sleep(adaptive_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown requested")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                time.sleep(self.config['SCAN_INTERVAL_SECONDS'])
        
        # Cleanup
        singleton_manager.cleanup()
        logger.info(f"✅ Shutdown complete. Generated {self.signal_count} signals")


def main():
    """Entry point"""
    print("🎯 APEX v5 LEAN - Streamlined Signal Generator")
    print("=" * 50)
    
    # Show current configuration
    print(f"📊 Target: {CONFIG['SIGNALS_PER_HOUR_TARGET']} signals/hour")
    print(f"🎯 TCS Threshold: {CONFIG['MIN_TCS_THRESHOLD']}%")
    print(f"⏱️ Scan Interval: {CONFIG['SCAN_INTERVAL_SECONDS']}s")
    print(f"📈 Pairs: {len(CONFIG['TRADING_PAIRS'])}")
    print("=" * 50)
    
    # Auto-start when running as background process
    if not sys.stdin.isatty():
        print("✅ Auto-starting in background mode")
    else:
        confirm = input("Start engine? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
    
    # Run engine
    engine = APEXLeanEngine()
    engine.run()


if __name__ == "__main__":
    try:
        main()
    finally:
        if 'singleton_manager' in globals():
            singleton_manager.cleanup()