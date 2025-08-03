#!/usr/bin/env python3
"""
ZMQ Tick Receiver - Production-Ready Market Data Stream
Future-proofed for XAUUSD (Gold) routing separation
"""

import zmq
import json
import time
import signal
import sys
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, Optional, Callable
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/zmq_tick_receiver.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ZMQTickReceiver')


class ZMQTickReceiver:
    """
    High-performance ZMQ tick receiver with future-proofed gold routing
    """
    
    def __init__(self, zmq_endpoint: str = "tcp://localhost:5555"):
        """
        Initialize the tick receiver
        
        Args:
            zmq_endpoint: ZMQ publisher endpoint (e.g., tcp://192.168.1.100:5555)
        """
        self.zmq_endpoint = zmq_endpoint
        
        # ZMQ setup
        self.context = None
        self.socket = None
        self.poller = None
        
        # State tracking
        self.running = False
        self.connected = False
        
        # Statistics per symbol
        self.tick_counts = defaultdict(int)
        self.last_tick_time = defaultdict(float)
        self.start_time = time.time()
        
        # Routing configuration (future-proofed)
        self.gold_symbols = ["XAUUSD"]  # Can add more gold pairs later
        self.route_gold_separately = False  # Toggle for future gold routing
        
        # Handlers
        self.market_data_handler: Optional[Callable] = None
        self.gold_data_handler: Optional[Callable] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"ZMQ Tick Receiver initialized for {zmq_endpoint}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def connect(self) -> bool:
        """Connect to ZMQ publisher"""
        try:
            # Create context
            self.context = zmq.Context()
            logger.debug("ZMQ context created")
            
            # Create SUB socket
            self.socket = self.context.socket(zmq.SUB)
            
            # Socket options for reliability and performance
            self.socket.setsockopt(zmq.RCVHWM, 100000)  # High water mark
            self.socket.setsockopt(zmq.LINGER, 0)        # Don't wait on close
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)   # 5 second timeout
            self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1) # Enable keepalive
            self.socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 300)
            self.socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
            
            # Subscribe to all topics for now
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")
            logger.info("Subscribed to all topics")
            
            # Connect to publisher
            self.socket.connect(self.zmq_endpoint)
            logger.info(f"✅ Connected to ZMQ publisher at {self.zmq_endpoint}")
            
            # Setup poller for non-blocking receives
            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False
            
    def disconnect(self):
        """Disconnect from ZMQ publisher"""
        if self.socket:
            self.poller.unregister(self.socket)
            self.socket.close()
            self.socket = None
            
        if self.context:
            self.context.term()
            self.context = None
            
        self.connected = False
        logger.info("Disconnected from ZMQ publisher")
        
    def parse_message(self, message: str) -> tuple[str, Dict]:
        """
        Parse incoming message with topic prefix
        
        Expected format: "SYMBOL {json_data}"
        
        Returns:
            tuple: (symbol, parsed_data)
        """
        try:
            # Find first space to separate topic from JSON
            space_idx = message.find(' ')
            
            if space_idx > 0:
                # Topic-prefixed message
                topic = message[:space_idx]
                json_str = message[space_idx + 1:]
            else:
                # No topic prefix, try parsing as pure JSON
                topic = None
                json_str = message
                
            # Parse JSON
            data = json.loads(json_str)
            
            # Extract symbol from topic or data
            if topic:
                symbol = topic
                # Ensure symbol is in payload
                if 'symbol' not in data:
                    data['symbol'] = symbol
            else:
                symbol = data.get('symbol', 'UNKNOWN')
                
            return symbol, data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            logger.debug(f"Raw message: {message[:100]}...")
            raise
        except Exception as e:
            logger.error(f"Message parsing error: {e}")
            raise
            
    def process_tick(self, symbol: str, data: Dict):
        """
        Process incoming tick data with gold routing
        
        Args:
            symbol: Trading symbol
            data: Tick data dictionary
        """
        # Update statistics
        self.tick_counts[symbol] += 1
        self.last_tick_time[symbol] = time.time()
        
        # Tag gold symbols
        if symbol in self.gold_symbols:
            data['gold'] = True
            logger.info(f"⚡ GOLD tick received - {symbol}: "
                       f"bid={data.get('bid', 'N/A')}, "
                       f"ask={data.get('ask', 'N/A')}")
        
        # Route to appropriate handler
        if self.route_gold_separately and symbol in self.gold_symbols:
            # Future: Route gold to separate handler
            if self.gold_data_handler:
                self.gold_data_handler(data)
            else:
                self.process_market_data(data)
        else:
            # Route all to main handler for now
            self.process_market_data(data)
            
        # Log statistics periodically
        if self.tick_counts[symbol] % 100 == 0:
            logger.info(f"📊 {symbol}: {self.tick_counts[symbol]} ticks received")
            
    def process_market_data(self, payload: Dict):
        """
        Main market data processing function
        
        Args:
            payload: Market data with symbol, bid, ask, etc.
        """
        # Call custom handler if set
        if self.market_data_handler:
            self.market_data_handler(payload)
        else:
            # Default processing - just print for now
            symbol = payload.get('symbol', 'UNKNOWN')
            bid = payload.get('bid', 0)
            ask = payload.get('ask', 0)
            is_gold = payload.get('gold', False)
            
            print(f"[{symbol}] Bid: {bid:.5f}, Ask: {ask:.5f}, "
                  f"Gold: {is_gold}, Ticks: {self.tick_counts[symbol]}")
            
    def run(self):
        """Main event loop"""
        logger.info("🚀 Starting ZMQ Tick Receiver...")
        
        # Connect to publisher
        if not self.connect():
            logger.error("Failed to connect to publisher")
            return
            
        self.running = True
        reconnect_attempts = 0
        
        while self.running:
            try:
                # Poll for messages with timeout
                events = dict(self.poller.poll(1000))  # 1 second timeout
                
                if self.socket in events and events[self.socket] == zmq.POLLIN:
                    # Reset reconnect counter on successful receive
                    reconnect_attempts = 0
                    
                    # Receive message
                    message = self.socket.recv_string(flags=zmq.NOBLOCK)
                    
                    # Parse and process
                    try:
                        symbol, data = self.parse_message(message)
                        self.process_tick(symbol, data)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        continue
                        
            except zmq.Again:
                # No message available (normal for non-blocking)
                continue
                
            except zmq.error.ZMQError as e:
                if e.errno == zmq.ETERM:
                    logger.info("Context terminated, exiting...")
                    break
                else:
                    logger.error(f"ZMQ Error: {e}")
                    # Try to reconnect
                    reconnect_attempts += 1
                    if reconnect_attempts <= 3:
                        logger.info(f"Attempting reconnect ({reconnect_attempts}/3)...")
                        self.disconnect()
                        time.sleep(2 ** reconnect_attempts)  # Exponential backoff
                        if not self.connect():
                            logger.error("Reconnect failed")
                    else:
                        logger.error("Max reconnect attempts reached, exiting...")
                        break
                        
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue
                
        # Clean shutdown
        self.disconnect()
        self.print_statistics()
        logger.info("✅ ZMQ Tick Receiver stopped")
        
    def stop(self):
        """Stop the receiver"""
        logger.info("Stopping ZMQ Tick Receiver...")
        self.running = False
        
    def print_statistics(self):
        """Print final statistics"""
        runtime = time.time() - self.start_time
        logger.info("=" * 60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Runtime: {runtime:.2f} seconds")
        logger.info(f"Total symbols: {len(self.tick_counts)}")
        
        total_ticks = sum(self.tick_counts.values())
        logger.info(f"Total ticks: {total_ticks}")
        
        if runtime > 0:
            logger.info(f"Average rate: {total_ticks/runtime:.2f} ticks/second")
            
        logger.info("\nPer-symbol breakdown:")
        for symbol, count in sorted(self.tick_counts.items(), 
                                   key=lambda x: x[1], reverse=True):
            rate = count / runtime if runtime > 0 else 0
            is_gold = " ⚡GOLD" if symbol in self.gold_symbols else ""
            logger.info(f"  {symbol}: {count} ticks ({rate:.2f}/sec){is_gold}")
            
    def set_market_handler(self, handler: Callable):
        """Set custom market data handler"""
        self.market_data_handler = handler
        
    def set_gold_handler(self, handler: Callable):
        """Set custom gold data handler (for future use)"""
        self.gold_data_handler = handler
        
    def enable_gold_routing(self, enable: bool = True):
        """Enable separate gold routing (future feature)"""
        self.route_gold_separately = enable
        if enable:
            logger.info("🏆 Gold routing ENABLED - XAUUSD will route separately")
        else:
            logger.info("Gold routing DISABLED - All symbols route together")


def example_market_handler(data: Dict):
    """Example custom market data handler"""
    symbol = data.get('symbol', 'UNKNOWN')
    if data.get('gold'):
        print(f"🏆 GOLD HANDLER: {symbol} - Special gold processing...")
    else:
        print(f"📈 MARKET HANDLER: {symbol} - Standard processing...")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZMQ Tick Receiver')
    parser.add_argument('--endpoint', type=str, 
                        default='tcp://localhost:5555',
                        help='ZMQ publisher endpoint (default: tcp://localhost:5555)')
    parser.add_argument('--enable-gold-routing', action='store_true',
                        help='Enable separate gold routing')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create receiver
    receiver = ZMQTickReceiver(args.endpoint)
    
    # Set custom handler (optional)
    # receiver.set_market_handler(example_market_handler)
    
    # Enable gold routing if requested
    if args.enable_gold_routing:
        receiver.enable_gold_routing(True)
        
    # Run forever
    try:
        receiver.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        receiver.stop()


if __name__ == "__main__":
    main()