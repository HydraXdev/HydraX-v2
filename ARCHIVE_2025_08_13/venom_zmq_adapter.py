#!/usr/bin/env python3
"""
VENOM ZMQ Adapter - Receives LIVE market data via ZMQ
Replaces HTTP polling with real-time ZMQ subscription
Integrates with existing VENOM v8 engine
100% REAL DATA ONLY
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Callable
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VENOMZMQAdapter')

class VENOMZMQAdapter:
    """
    ZMQ adapter for VENOM engine
    Subscribes to market data and feeds VENOM in real-time
    """
    
    def __init__(self, 
                 zmq_endpoint: str = "tcp://127.0.0.1:5557",
                 venom_callback: Optional[Callable] = None):
        """
        Initialize VENOM ZMQ adapter
        
        Args:
            zmq_endpoint: Market data publisher endpoint
            venom_callback: Callback function for VENOM processing
        """
        self.zmq_endpoint = zmq_endpoint
        self.venom_callback = venom_callback
        
        # ZMQ setup
        self.context = None
        self.subscriber = None
        self.poller = None
        
        # State tracking
        self.running = False
        self.connected = False
        
        # Market data cache
        self.market_data = {}
        self.data_lock = threading.Lock()
        
        # Statistics
        self.stats = defaultdict(int)
        self.last_update = defaultdict(float)
        
        # VENOM integration
        self.venom_engine = None
        
        logger.info(f"VENOM ZMQ Adapter initialized")
        logger.info(f"Subscribing to: {zmq_endpoint}")
        
    def connect(self) -> bool:
        """Connect to ZMQ publisher"""
        try:
            # Create context
            self.context = zmq.Context()
            
            # Create subscriber socket
            self.subscriber = self.context.socket(zmq.SUB)
            
            # Socket options
            self.subscriber.setsockopt(zmq.RCVHWM, 100000)
            self.subscriber.setsockopt(zmq.LINGER, 0)
            self.subscriber.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Subscribe to all topics initially
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
            
            # Connect
            self.subscriber.connect(self.zmq_endpoint)
            
            # Setup poller
            self.poller = zmq.Poller()
            self.poller.register(self.subscriber, zmq.POLLIN)
            
            self.connected = True
            logger.info(f"✅ Connected to market data stream at {self.zmq_endpoint}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from ZMQ"""
        if self.subscriber:
            self.poller.unregister(self.subscriber)
            self.subscriber.close()
            
        if self.context:
            self.context.term()
            
        self.connected = False
        logger.info("Disconnected from market stream")
        
    def process_market_tick(self, message: str) -> Optional[Dict]:
        """
        Process incoming market tick
        
        Expected format: "SYMBOL {venom_message}"
        """
        try:
            # Parse topic-prefixed message
            space_idx = message.find(' ')
            
            if space_idx > 0:
                symbol = message[:space_idx]
                json_str = message[space_idx + 1:]
                
                # Parse VENOM message
                venom_msg = json.loads(json_str)
                
                if venom_msg.get('type') != 'market_tick':
                    return None
                    
                tick_data = venom_msg.get('data', {})
                
                # CRITICAL: Verify REAL data
                if tick_data.get('source') != 'MT5_LIVE':
                    logger.warning(f"❌ REJECTED non-live data for {symbol}")
                    return None
                    
                # Update cache
                with self.data_lock:
                    self.market_data[symbol] = tick_data
                    
                # Update stats
                self.stats[symbol] += 1
                self.last_update[symbol] = time.time()
                
                return tick_data
                
        except Exception as e:
            logger.error(f"Error processing market tick: {e}")
            return None
            
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get latest market data for symbol"""
        with self.data_lock:
            return self.market_data.get(symbol)
            
    def get_all_market_data(self) -> Dict:
        """Get all market data snapshot"""
        with self.data_lock:
            return self.market_data.copy()
            
    def feed_venom(self, tick_data: Dict):
        """Feed tick data to VENOM engine"""
        if not self.venom_callback:
            return
            
        try:
            # Call VENOM with real tick data
            self.venom_callback(tick_data)
            
        except Exception as e:
            logger.error(f"Error feeding VENOM: {e}")
            
    def run_subscriber(self):
        """Run subscriber in thread"""
        logger.info("🚀 Starting VENOM ZMQ subscriber...")
        
        if not self.connect():
            logger.error("Failed to connect to market stream")
            return
            
        self.running = True
        
        while self.running:
            try:
                # Poll for messages
                events = dict(self.poller.poll(1000))
                
                if self.subscriber in events:
                    # Receive message
                    message = self.subscriber.recv_string(zmq.NOBLOCK)
                    
                    # Process tick
                    tick_data = self.process_market_tick(message)
                    
                    if tick_data:
                        # Feed to VENOM
                        self.feed_venom(tick_data)
                        
                        # Special handling for GOLD
                        if tick_data.get('symbol') == 'XAUUSD':
                            logger.info(f"🏆 GOLD fed to VENOM: ${tick_data['bid']:.2f}")
                            
            except zmq.Again:
                # No message available
                continue
                
            except Exception as e:
                logger.error(f"Subscriber error: {e}")
                
        self.disconnect()
        logger.info("✅ VENOM subscriber stopped")
        
    def start(self):
        """Start subscriber thread"""
        self.subscriber_thread = threading.Thread(
            target=self.run_subscriber,
            daemon=True
        )
        self.subscriber_thread.start()
        logger.info("VENOM ZMQ adapter started")
        
    def stop(self):
        """Stop subscriber"""
        logger.info("Stopping VENOM adapter...")
        self.running = False
        
        if hasattr(self, 'subscriber_thread'):
            self.subscriber_thread.join(timeout=5)
            
    def print_stats(self):
        """Print adapter statistics"""
        total_ticks = sum(self.stats.values())
        active_symbols = len(self.stats)
        
        logger.info("=" * 50)
        logger.info("📊 VENOM ADAPTER STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total ticks received: {total_ticks:,}")
        logger.info(f"Active symbols: {active_symbols}")
        
        # Per-symbol stats
        for symbol, count in sorted(self.stats.items()):
            last_update = self.last_update.get(symbol, 0)
            age = time.time() - last_update if last_update > 0 else 999
            
            status = "✅" if age < 60 else "⚠️"
            is_gold = " 🏆" if symbol == "XAUUSD" else ""
            
            logger.info(f"{status} {symbol}: {count:,} ticks (last: {age:.1f}s ago){is_gold}")


def integrate_with_venom():
    """
    Integration function to connect with existing VENOM engine
    """
    try:
        # Import existing VENOM components
        from venom_stream_pipeline import VenomStreamEngine
        
        # Create VENOM engine
        venom_engine = VenomStreamEngine()
        logger.info("✅ VENOM v8 engine loaded")
        
        # Create adapter with VENOM callback
        def venom_callback(tick_data: Dict):
            """Process tick through VENOM"""
            symbol = tick_data.get('symbol')
            
            # Feed to VENOM's process_market_tick
            if hasattr(venom_engine, 'process_market_tick'):
                venom_engine.process_market_tick(symbol, tick_data)
            else:
                # Fallback to standard processing
                logger.warning(f"VENOM missing process_market_tick for {symbol}")
                
        adapter = VENOMZMQAdapter(
            zmq_endpoint="tcp://127.0.0.1:5556",
            venom_callback=venom_callback
        )
        
        # Start adapter
        adapter.start()
        logger.info("🚀 VENOM ZMQ integration active")
        
        return adapter, venom_engine
        
    except ImportError:
        logger.error("❌ Could not import VENOM engine")
        return None, None


def main():
    """Main entry point for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VENOM ZMQ Adapter')
    parser.add_argument('--endpoint', type=str,
                        default='tcp://127.0.0.1:5556',
                        help='ZMQ publisher endpoint')
    parser.add_argument('--integrate', action='store_true',
                        help='Integrate with VENOM engine')
    
    args = parser.parse_args()
    
    if args.integrate:
        # Full VENOM integration
        adapter, venom = integrate_with_venom()
        
        if adapter and venom:
            try:
                # Run until interrupted
                while True:
                    time.sleep(30)
                    adapter.print_stats()
                    
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                adapter.stop()
                
    else:
        # Standalone adapter (for testing)
        def test_callback(tick_data: Dict):
            symbol = tick_data.get('symbol', 'UNKNOWN')
            bid = tick_data.get('bid', 0)
            logger.info(f"📈 {symbol}: ${bid:.5f}")
            
        adapter = VENOMZMQAdapter(
            zmq_endpoint=args.endpoint,
            venom_callback=test_callback
        )
        
        adapter.start()
        
        try:
            while True:
                time.sleep(30)
                adapter.print_stats()
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            adapter.stop()


if __name__ == "__main__":
    main()