#!/usr/bin/env python3
"""
ZMQ VENOM Integration - Connect tick receiver to existing pipeline
Shows how to route market data with future gold separation
"""

import json
import time
from datetime import datetime
from typing import Dict
import logging

# Import the tick receiver
from zmq_tick_receiver import ZMQTickReceiver

# Import existing VENOM components (if available)
try:
    from venom_stream_pipeline import VenomStreamEngine
    VENOM_AVAILABLE = True
except ImportError:
    VENOM_AVAILABLE = False
    print("⚠️ VENOM not available - using mock processor")

logger = logging.getLogger('ZMQVenomIntegration')


class VenomMarketProcessor:
    """
    Market data processor that integrates with VENOM pipeline
    Future-proofed for gold-specific processing
    """
    
    def __init__(self):
        self.venom_engine = None
        self.gold_processor = None
        self.stats = {
            'regular_ticks': 0,
            'gold_ticks': 0,
            'signals_generated': 0,
            'gold_signals': 0
        }
        
        # Initialize VENOM if available
        if VENOM_AVAILABLE:
            try:
                self.venom_engine = VenomStreamEngine()
                logger.info("✅ VENOM engine initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VENOM: {e}")
                
    def process_market_tick(self, data: Dict):
        """
        Process market tick data through VENOM pipeline
        
        Args:
            data: Tick data with symbol, bid, ask, etc.
        """
        symbol = data.get('symbol', 'UNKNOWN')
        is_gold = data.get('gold', False)
        
        # Update stats
        if is_gold:
            self.stats['gold_ticks'] += 1
        else:
            self.stats['regular_ticks'] += 1
            
        # Route to appropriate processor
        if is_gold and self.gold_processor:
            # Future: Special gold processing
            self.process_gold_tick(data)
        else:
            # Standard VENOM processing
            self.process_standard_tick(data)
            
    def process_standard_tick(self, data: Dict):
        """Process standard (non-gold) ticks through VENOM"""
        if self.venom_engine:
            try:
                # Convert to VENOM format if needed
                venom_data = self._convert_to_venom_format(data)
                
                # Process through VENOM
                signal = self.venom_engine.process_tick_stream(venom_data)
                
                if signal:
                    self.stats['signals_generated'] += 1
                    logger.info(f"🎯 Signal generated: {signal}")
                    
            except Exception as e:
                logger.error(f"VENOM processing error: {e}")
        else:
            # Mock processing for testing
            self._mock_venom_process(data)
            
    def process_gold_tick(self, data: Dict):
        """
        Special processing for gold ticks
        Can implement different strategies, risk management, etc.
        """
        symbol = data.get('symbol')
        bid = data.get('bid', 0)
        ask = data.get('ask', 0)
        spread = ask - bid
        
        # Example: Gold-specific analysis
        logger.info(f"🏆 GOLD PROCESSING: {symbol}")
        logger.info(f"   Bid: ${bid:.2f}, Ask: ${ask:.2f}, Spread: ${spread:.2f}")
        
        # Future: Implement gold-specific strategies
        # - Different TCS thresholds
        # - Special liquidity analysis
        # - Gold-specific risk management
        # - Correlation with DXY, bonds, etc.
        
        if self.venom_engine:
            # Process through VENOM with gold-specific parameters
            signal = self._process_gold_through_venom(data)
            if signal:
                self.stats['gold_signals'] += 1
                logger.info(f"⚡ GOLD Signal: {signal}")
                
    def _convert_to_venom_format(self, data: Dict) -> Dict:
        """Convert ZMQ tick format to VENOM format"""
        # VENOM expects certain fields
        return {
            'symbol': data.get('symbol', ''),
            'bid': float(data.get('bid', 0)),
            'ask': float(data.get('ask', 0)),
            'volume': int(data.get('volume', 0)),
            'timestamp': data.get('timestamp', time.time()),
            'broker': data.get('broker', 'Unknown'),
            'source': data.get('source', 'MT5_LIVE')
        }
        
    def _process_gold_through_venom(self, data: Dict) -> Dict:
        """Process gold with special parameters"""
        # Convert to VENOM format
        venom_data = self._convert_to_venom_format(data)
        
        # Add gold-specific parameters
        venom_data['is_gold'] = True
        venom_data['min_tcs'] = 85  # Higher threshold for gold
        venom_data['risk_multiplier'] = 0.5  # Lower risk for gold volatility
        
        # Process through VENOM
        if self.venom_engine:
            return self.venom_engine.process_tick_stream(venom_data)
        return None
        
    def _mock_venom_process(self, data: Dict):
        """Mock VENOM processing for testing"""
        symbol = data.get('symbol')
        bid = data.get('bid', 0)
        
        # Simulate signal generation (1% chance)
        import random
        if random.random() < 0.01:
            signal = {
                'signal_id': f"MOCK_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'direction': 'BUY' if random.random() > 0.5 else 'SELL',
                'confidence': random.uniform(75, 95),
                'entry': bid
            }
            self.stats['signals_generated'] += 1
            logger.info(f"🎯 [MOCK] Signal: {signal}")
            
    def print_stats(self):
        """Print processing statistics"""
        logger.info("=" * 50)
        logger.info("📊 PROCESSING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Regular ticks: {self.stats['regular_ticks']}")
        logger.info(f"Gold ticks: {self.stats['gold_ticks']}")
        logger.info(f"Signals generated: {self.stats['signals_generated']}")
        logger.info(f"Gold signals: {self.stats['gold_signals']}")
        
        total_ticks = self.stats['regular_ticks'] + self.stats['gold_ticks']
        if total_ticks > 0:
            gold_percentage = (self.stats['gold_ticks'] / total_ticks) * 100
            logger.info(f"Gold percentage: {gold_percentage:.2f}%")


def main():
    """Example integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZMQ VENOM Integration')
    parser.add_argument('--endpoint', type=str, 
                        default='tcp://localhost:5555',
                        help='ZMQ publisher endpoint')
    parser.add_argument('--enable-gold-routing', action='store_true',
                        help='Enable separate gold routing')
    
    args = parser.parse_args()
    
    # Create processor
    processor = VenomMarketProcessor()
    
    # Create tick receiver
    receiver = ZMQTickReceiver(args.endpoint)
    
    # Set the processor as handler
    receiver.set_market_handler(processor.process_market_tick)
    
    # Enable gold routing if requested
    if args.enable_gold_routing:
        receiver.enable_gold_routing(True)
        logger.info("🏆 Gold routing enabled")
        
    # Run
    logger.info("🚀 Starting ZMQ VENOM Integration...")
    logger.info(f"📡 Connecting to: {args.endpoint}")
    
    try:
        receiver.run()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Stopped by user")
    finally:
        processor.print_stats()
        

if __name__ == "__main__":
    main()