#!/usr/bin/env python3
"""
ZMQ Market Data Streamer - LIVE MT5 to VENOM Pipeline
Replaces HTTP POST with high-performance ZMQ streaming
100% REAL DATA - No simulation allowed
"""

import zmq
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ZMQMarketStreamer')

# VALID SYMBOLS - Including GOLD
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "XAUUSD", "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

class ZMQMarketStreamer:
    """
    High-performance market data streamer using ZMQ
    Subscribes to EA publisher and streams to VENOM
    """
    
    def __init__(self, 
                 zmq_subscribe_endpoint: str = "tcp://134.199.204.67:5555",
                 venom_endpoint: str = "tcp://127.0.0.1:5556"):
        """
        Initialize the market streamer
        
        Args:
            zmq_subscribe_endpoint: EA publisher endpoint
            venom_endpoint: VENOM subscriber endpoint
        """
        self.zmq_subscribe_endpoint = zmq_subscribe_endpoint
        self.venom_endpoint = venom_endpoint
        
        # ZMQ contexts and sockets
        self.context = None
        self.subscriber = None
        self.publisher = None
        
        # State tracking
        self.running = False
        self.connected = False
        self.stats = defaultdict(int)
        self.last_tick_time = defaultdict(float)
        self.start_time = time.time()
        
        # Market data cache (for VENOM)
        self.market_data = {}
        self.data_lock = threading.Lock()
        
        logger.info(f"ZMQ Market Streamer initialized")
        logger.info(f"Subscribing to: {zmq_subscribe_endpoint}")
        logger.info(f"Publishing to: {venom_endpoint}")
        
    def connect(self) -> bool:
        """Connect to ZMQ endpoints"""
        try:
            # Create context
            self.context = zmq.Context()
            
            # Create subscriber socket (connect to EA)
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.setsockopt(zmq.RCVHWM, 100000)
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all
            self.subscriber.connect(self.zmq_subscribe_endpoint)
            logger.info(f"✅ Connected to EA publisher at {self.zmq_subscribe_endpoint}")
            
            # Create publisher socket (for VENOM)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.setsockopt(zmq.SNDHWM, 100000)
            self.publisher.bind(self.venom_endpoint)
            logger.info(f"✅ Publishing for VENOM at {self.venom_endpoint}")
            
            # Setup poller
            self.poller = zmq.Poller()
            self.poller.register(self.subscriber, zmq.POLLIN)
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.cleanup()
            return False
            
    def cleanup(self):
        """Clean up ZMQ resources"""
        if self.subscriber:
            self.subscriber.close()
        if self.publisher:
            self.publisher.close()
        if self.context:
            self.context.term()
        self.connected = False
        
    def process_tick(self, message: str) -> Optional[Dict]:
        """
        Process incoming tick message from EA
        
        Expected format: "SYMBOL {json_data}"
        """
        try:
            # Parse topic-prefixed message
            space_idx = message.find(' ')
            
            if space_idx > 0:
                symbol = message[:space_idx]
                json_str = message[space_idx + 1:]
            else:
                # Try parsing as pure JSON
                data = json.loads(message)
                symbol = data.get('symbol', 'UNKNOWN')
                
            # Validate symbol
            if symbol not in VALID_SYMBOLS:
                return None
                
            # Parse tick data
            tick_data = json.loads(json_str) if space_idx > 0 else data
            
            # CRITICAL: Verify REAL data source
            if tick_data.get('source') != 'MT5_LIVE':
                logger.warning(f"❌ REJECTED non-live data from {symbol}")
                return None
                
            # Extract essential data
            processed_tick = {
                'symbol': symbol,
                'bid': float(tick_data.get('bid', 0)),
                'ask': float(tick_data.get('ask', 0)),
                'spread': float(tick_data.get('spread', 0)),
                'volume': int(tick_data.get('volume', 0)),
                'timestamp': tick_data.get('timestamp', int(time.time())),
                'broker': tick_data.get('broker', 'Unknown'),
                'source': 'MT5_LIVE'  # ENFORCE real data
            }
            
            # Update stats
            self.stats[symbol] += 1
            self.last_tick_time[symbol] = time.time()
            
            # Update market data cache
            with self.data_lock:
                self.market_data[symbol] = processed_tick
                
            # Special handling for GOLD
            if symbol == "XAUUSD":
                processed_tick['is_gold'] = True
                logger.info(f"🏆 GOLD tick: Bid ${processed_tick['bid']:.2f}")
                
            return processed_tick
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            return None
            
    def publish_to_venom(self, tick_data: Dict):
        """Publish processed tick to VENOM"""
        try:
            # Format for VENOM consumption
            venom_message = {
                'type': 'market_tick',
                'data': tick_data,
                'server_time': datetime.utcnow().isoformat()
            }
            
            # Publish with topic prefix
            topic = tick_data['symbol']
            message = f"{topic} {json.dumps(venom_message)}"
            
            self.publisher.send_string(message, zmq.NOBLOCK)
            
        except zmq.Again:
            # No subscribers yet, that's OK
            pass
        except Exception as e:
            logger.error(f"Error publishing to VENOM: {e}")
            
    def get_market_snapshot(self) -> Dict:
        """Get current market snapshot for VENOM"""
        with self.data_lock:
            return self.market_data.copy()
            
    def run(self):
        """Main event loop"""
        logger.info("🚀 Starting ZMQ Market Streamer...")
        
        if not self.connect():
            logger.error("Failed to establish connections")
            return
            
        self.running = True
        reconnect_attempts = 0
        last_stats_time = time.time()
        
        while self.running:
            try:
                # Poll with timeout
                events = dict(self.poller.poll(1000))
                
                if self.subscriber in events:
                    # Receive message
                    message = self.subscriber.recv_string(zmq.NOBLOCK)
                    
                    # Process tick
                    tick_data = self.process_tick(message)
                    
                    if tick_data:
                        # Publish to VENOM
                        self.publish_to_venom(tick_data)
                        
                # Print stats every 30 seconds
                if time.time() - last_stats_time > 30:
                    self.print_stats()
                    last_stats_time = time.time()
                    
            except zmq.Again:
                # No message available
                continue
                
            except zmq.error.ZMQError as e:
                logger.error(f"ZMQ Error: {e}")
                reconnect_attempts += 1
                
                if reconnect_attempts <= 3:
                    logger.info(f"Reconnecting... ({reconnect_attempts}/3)")
                    self.cleanup()
                    time.sleep(2 ** reconnect_attempts)
                    if not self.connect():
                        logger.error("Reconnection failed")
                else:
                    logger.error("Max reconnect attempts reached")
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
        self.cleanup()
        logger.info("✅ Market Streamer stopped")
        
    def stop(self):
        """Stop the streamer"""
        logger.info("Stopping market streamer...")
        self.running = False
        
    def print_stats(self):
        """Print streaming statistics"""
        runtime = time.time() - self.start_time
        total_ticks = sum(self.stats.values())
        
        logger.info("=" * 60)
        logger.info("📊 MARKET STREAMING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Runtime: {runtime:.2f} seconds")
        logger.info(f"Total ticks: {total_ticks:,}")
        logger.info(f"Rate: {total_ticks/runtime:.2f} ticks/second")
        logger.info(f"Active symbols: {len(self.stats)}")
        
        # Top 5 symbols by volume
        top_symbols = sorted(self.stats.items(), key=lambda x: x[1], reverse=True)[:5]
        logger.info("\nTop 5 symbols:")
        for symbol, count in top_symbols:
            rate = count / runtime
            is_gold = " 🏆" if symbol == "XAUUSD" else ""
            logger.info(f"  {symbol}: {count:,} ticks ({rate:.2f}/sec){is_gold}")
            
    def get_venom_feed(self, symbol: str) -> Optional[Dict]:
        """Get latest tick for VENOM consumption"""
        with self.data_lock:
            return self.market_data.get(symbol)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZMQ Market Data Streamer')
    parser.add_argument('--subscribe', type=str, 
                        default='tcp://134.199.204.67:5555',
                        help='EA publisher endpoint')
    parser.add_argument('--publish', type=str,
                        default='tcp://127.0.0.1:5556', 
                        help='VENOM subscriber endpoint')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create and run streamer
    streamer = ZMQMarketStreamer(
        zmq_subscribe_endpoint=args.subscribe,
        venom_endpoint=args.publish
    )
    
    try:
        streamer.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        streamer.stop()


if __name__ == "__main__":
    main()