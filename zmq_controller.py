#!/usr/bin/env python3
"""
ZMQ Controller - Central Server for BITTEN System
Binds to ports and receives data from thousands of MT5 EAs
Controller is the ONLY server - EAs are always clients
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ZMQController')

class ZMQController:
    """
    Central ZMQ Controller for BITTEN
    - Binds PULL socket on 5555 for receiving market data from EAs
    - Binds PUSH socket on 5556 for sending commands to EAs
    - Manages data flow to VENOM engine
    """
    
    def __init__(self,
                 pull_port: int = 5555,  # EA data comes here
                 push_port: int = 5556,  # Commands go out here
                 bind_address: str = "0.0.0.0"):
        """
        Initialize the ZMQ Controller
        
        Args:
            pull_port: Port to receive data from EAs
            push_port: Port to send commands to EAs
            bind_address: Interface to bind on
        """
        self.pull_port = pull_port
        self.push_port = push_port
        self.bind_address = bind_address
        
        # ZMQ setup
        self.context = None
        self.pull_socket = None  # Receives from EAs
        self.push_socket = None  # Sends to EAs
        
        # State tracking
        self.running = False
        self.market_data = {}
        self.data_lock = threading.Lock()
        
        # Statistics
        self.ea_connections = defaultdict(float)  # Track last seen time
        self.tick_count = defaultdict(int)
        self.total_ticks = 0
        self.start_time = time.time()
        
        # VENOM feed
        self.venom_publisher = None
        self.venom_port = 5557  # Local port for VENOM
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("ZMQ Controller initialized")
        logger.info(f"PULL (from EAs): tcp://{bind_address}:{pull_port}")
        logger.info(f"PUSH (to EAs): tcp://{bind_address}:{push_port}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def start(self) -> bool:
        """Start the controller"""
        try:
            # Create context
            self.context = zmq.Context()
            
            # Create PULL socket (receive from EAs)
            self.pull_socket = self.context.socket(zmq.PULL)
            self.pull_socket.setsockopt(zmq.RCVHWM, 100000)
            pull_endpoint = f"tcp://{self.bind_address}:{self.pull_port}"
            self.pull_socket.bind(pull_endpoint)
            logger.info(f"✅ PULL socket bound to {pull_endpoint} (receiving from EAs)")
            
            # Create PUSH socket (send to EAs)
            self.push_socket = self.context.socket(zmq.PUSH)
            self.push_socket.setsockopt(zmq.SNDHWM, 100000)
            push_endpoint = f"tcp://{self.bind_address}:{self.push_port}"
            self.push_socket.bind(push_endpoint)
            logger.info(f"✅ PUSH socket bound to {push_endpoint} (sending to EAs)")
            
            # Create PUB socket for VENOM (local only)
            self.venom_publisher = self.context.socket(zmq.PUB)
            venom_endpoint = f"tcp://127.0.0.1:{self.venom_port}"
            self.venom_publisher.bind(venom_endpoint)
            logger.info(f"✅ PUB socket bound to {venom_endpoint} (feeding VENOM)")
            
            self.running = True
            logger.info("🚀 ZMQ Controller started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start controller: {e}")
            self.cleanup()
            return False
            
    def cleanup(self):
        """Clean up resources"""
        if self.pull_socket:
            self.pull_socket.close()
        if self.push_socket:
            self.push_socket.close()
        if self.venom_publisher:
            self.venom_publisher.close()
        if self.context:
            self.context.term()
        logger.info("Controller resources cleaned up")
        
    def process_ea_data(self, message: str) -> Optional[Dict]:
        """
        Process data from EA
        Expected format: {"ea_id": "...", "type": "market_data", "data": {...}}
        """
        try:
            # Parse message
            msg = json.loads(message)
            
            # Extract EA identifier
            ea_id = msg.get('ea_id', 'unknown')
            msg_type = msg.get('type', 'unknown')
            
            # Update connection tracking
            self.ea_connections[ea_id] = time.time()
            
            if msg_type == 'market_data':
                # Process market tick
                data = msg.get('data', {})
                symbol = data.get('symbol', 'UNKNOWN')
                
                # Validate LIVE data
                if data.get('source') != 'MT5_LIVE':
                    logger.warning(f"❌ Rejected non-live data from {ea_id}")
                    return None
                    
                # Update statistics
                self.tick_count[symbol] += 1
                self.total_ticks += 1
                
                # Store market data
                with self.data_lock:
                    self.market_data[symbol] = {
                        'bid': float(data.get('bid', 0)),
                        'ask': float(data.get('ask', 0)),
                        'spread': float(data.get('spread', 0)),
                        'volume': int(data.get('volume', 0)),
                        'timestamp': data.get('timestamp', int(time.time())),
                        'broker': data.get('broker', 'Unknown'),
                        'ea_id': ea_id,
                        'source': 'MT5_LIVE'
                    }
                    
                # Special handling for GOLD
                if symbol == "XAUUSD":
                    logger.info(f"🏆 GOLD tick from {ea_id}: ${data.get('bid', 0):.2f}")
                    
                return self.market_data[symbol]
                
            elif msg_type == 'heartbeat':
                logger.debug(f"💓 Heartbeat from {ea_id}")
                return None
                
            elif msg_type == 'status':
                logger.info(f"📊 Status from {ea_id}: {msg.get('status', 'unknown')}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing EA data: {e}")
            return None
            
    def publish_to_venom(self, tick_data: Dict):
        """Publish tick to VENOM engine"""
        try:
            symbol = tick_data.get('symbol', 'UNKNOWN')
            
            # Format for VENOM
            venom_msg = {
                'type': 'market_tick',
                'data': tick_data,
                'controller_time': datetime.utcnow().isoformat()
            }
            
            # Topic-prefixed publishing
            message = f"{symbol} {json.dumps(venom_msg)}"
            self.venom_publisher.send_string(message, zmq.NOBLOCK)
            
        except Exception as e:
            logger.error(f"Error publishing to VENOM: {e}")
            
    def send_command_to_eas(self, command: Dict):
        """Send command to all connected EAs"""
        try:
            # Add timestamp
            command['timestamp'] = int(time.time())
            
            # Send command
            message = json.dumps(command)
            self.push_socket.send_string(message, zmq.NOBLOCK)
            
            logger.info(f"📤 Sent command to EAs: {command.get('type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            
    def run(self):
        """Main event loop"""
        logger.info("🚀 Starting ZMQ Controller main loop...")
        
        if not self.start():
            return
            
        # Setup poller
        poller = zmq.Poller()
        poller.register(self.pull_socket, zmq.POLLIN)
        
        last_stats_time = time.time()
        last_cleanup_time = time.time()
        
        while self.running:
            try:
                # Poll for messages
                events = dict(poller.poll(1000))  # 1 second timeout
                
                if self.pull_socket in events:
                    # Receive from EA
                    message = self.pull_socket.recv_string(zmq.NOBLOCK)
                    
                    # Process data
                    tick_data = self.process_ea_data(message)
                    
                    if tick_data:
                        # Publish to VENOM
                        self.publish_to_venom(tick_data)
                        
                # Print statistics every 30 seconds
                if time.time() - last_stats_time > 30:
                    self.print_stats()
                    last_stats_time = time.time()
                    
                # Cleanup stale connections every 60 seconds
                if time.time() - last_cleanup_time > 60:
                    self.cleanup_stale_connections()
                    last_cleanup_time = time.time()
                    
            except zmq.Again:
                # No message available
                continue
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                
        self.cleanup()
        logger.info("✅ Controller stopped")
        
    def cleanup_stale_connections(self):
        """Remove stale EA connections"""
        current_time = time.time()
        stale_threshold = 300  # 5 minutes
        
        stale_eas = []
        for ea_id, last_seen in self.ea_connections.items():
            if current_time - last_seen > stale_threshold:
                stale_eas.append(ea_id)
                
        for ea_id in stale_eas:
            del self.ea_connections[ea_id]
            logger.info(f"🧹 Removed stale EA: {ea_id}")
            
    def print_stats(self):
        """Print controller statistics"""
        runtime = time.time() - self.start_time
        active_eas = len(self.ea_connections)
        
        logger.info("=" * 60)
        logger.info("📊 ZMQ CONTROLLER STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Runtime: {runtime:.2f} seconds")
        logger.info(f"Connected EAs: {active_eas}")
        logger.info(f"Total ticks: {self.total_ticks:,}")
        logger.info(f"Rate: {self.total_ticks/runtime:.2f} ticks/second")
        
        # Top symbols
        top_symbols = sorted(self.tick_count.items(), 
                            key=lambda x: x[1], reverse=True)[:5]
        logger.info("\nTop 5 symbols:")
        for symbol, count in top_symbols:
            rate = count / runtime
            is_gold = " 🏆" if symbol == "XAUUSD" else ""
            logger.info(f"  {symbol}: {count:,} ticks ({rate:.2f}/sec){is_gold}")
            
        # Recent EAs
        logger.info(f"\nActive EAs: {active_eas}")
        current_time = time.time()
        recent_eas = sorted(self.ea_connections.items(), 
                           key=lambda x: x[1], reverse=True)[:5]
        for ea_id, last_seen in recent_eas:
            age = current_time - last_seen
            logger.info(f"  {ea_id}: last seen {age:.1f}s ago")
            
    def stop(self):
        """Stop the controller"""
        logger.info("Stopping ZMQ Controller...")
        self.running = False
        
    def get_market_snapshot(self) -> Dict:
        """Get current market data snapshot"""
        with self.data_lock:
            return self.market_data.copy()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZMQ Controller for BITTEN')
    parser.add_argument('--pull-port', type=int, default=5555,
                        help='Port to receive data from EAs')
    parser.add_argument('--push-port', type=int, default=5556,
                        help='Port to send commands to EAs')
    parser.add_argument('--bind', type=str, default='0.0.0.0',
                        help='Interface to bind on')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create and run controller
    controller = ZMQController(
        pull_port=args.pull_port,
        push_port=args.push_port,
        bind_address=args.bind
    )
    
    try:
        controller.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        controller.stop()


if __name__ == "__main__":
    main()