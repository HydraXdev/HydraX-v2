#!/usr/bin/env python3
"""
ZMQ Market Data Receiver for HydraX
Replaces HTTP-based market_data_receiver with high-performance ZMQ subscriber
"""

import zmq
import json
import time
import signal
import sys
import logging
from datetime import datetime
from threading import Thread, Event, Lock
from collections import defaultdict, deque
from typing import Dict, Optional
import os
from flask import Flask, jsonify, request
from cachetools import TTLCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ZMQMarketReceiver')

# Flask app for compatibility with existing system
app = Flask(__name__)

class ZMQMarketDataReceiver:
    """
    High-performance market data receiver using ZMQ
    Drop-in replacement for HTTP-based receiver
    """
    
    def __init__(self, zmq_endpoint="tcp://localhost:5555"):
        self.zmq_endpoint = zmq_endpoint
        
        # ZMQ setup
        self.context = None
        self.socket = None
        self.poller = None
        
        # Data storage with TTL cache (same as enhanced receiver)
        self.tick_cache = TTLCache(maxsize=500, ttl=30)  # 30 second TTL
        self.metrics_cache = TTLCache(maxsize=100, ttl=5)  # 5 second TTL
        self.activity_cache = TTLCache(maxsize=20, ttl=60)  # 60 second TTL
        
        # State tracking
        self.running = Event()
        self.connected = False
        self.last_update = {}
        
        # Performance metrics
        self.stats = {
            'messages_received': 0,
            'bytes_received': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def connect(self) -> bool:
        """Connect to ZMQ publisher"""
        try:
            # Create context
            self.context = zmq.Context()
            
            # Create SUB socket
            self.socket = self.context.socket(zmq.SUB)
            
            # Socket options for reliability
            self.socket.setsockopt(zmq.RCVHWM, 100000)  # High water mark
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
            self.socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 120)
            self.socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
            
            # Subscribe to all messages
            self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
            
            # Connect
            self.socket.connect(self.zmq_endpoint)
            
            # Setup poller
            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)
            
            self.connected = True
            logger.info(f"✅ Connected to ZMQ publisher at {self.zmq_endpoint}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False
            
    def process_tick(self, data: Dict):
        """Process incoming tick data"""
        try:
            symbol = data.get('symbol', '')
            if not symbol:
                return
                
            # Create cache key
            cache_key = f"tick_{symbol}"
            
            # Store in cache
            self.tick_cache[cache_key] = {
                'symbol': symbol,
                'bid': data.get('bid', 0),
                'ask': data.get('ask', 0),
                'spread': data.get('spread', 0),
                'volume': data.get('volume', 0),
                'timestamp': data.get('timestamp', time.time()),
                'account_balance': data.get('account_balance', 0),
                'broker': data.get('broker', 'Unknown'),
                'source': data.get('source', 'MT5_LIVE'),
                'volatility': 0.0002  # Default volatility
            }
            
            # Track last update
            self.last_update[symbol] = time.time()
            
            # Update activity
            activity_key = f"activity_{symbol}"
            self.activity_cache[activity_key] = time.time()
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            self.stats['errors'] += 1
            
    def run(self):
        """Main ZMQ receive loop"""
        self.running.set()
        
        # Connect to publisher
        if not self.connect():
            logger.error("Failed to connect to ZMQ publisher")
            return
            
        logger.info("🚀 ZMQ Market Data Receiver running...")
        
        while self.running.is_set():
            try:
                # Poll for messages
                events = dict(self.poller.poll(100))
                
                if self.socket in events and events[self.socket] == zmq.POLLIN:
                    # Receive message
                    message = self.socket.recv_string(flags=zmq.NOBLOCK)
                    self.stats['messages_received'] += 1
                    self.stats['bytes_received'] += len(message)
                    
                    # Parse JSON
                    data = json.loads(message)
                    
                    # Process based on type
                    msg_type = data.get('type', 'tick')
                    
                    if msg_type == 'tick':
                        self.process_tick(data)
                    elif msg_type == 'heartbeat':
                        logger.debug(f"Heartbeat: {data}")
                    elif msg_type == 'shutdown':
                        logger.warning("Publisher shutdown detected")
                        break
                        
            except zmq.Again:
                # No message available
                continue
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                self.stats['errors'] += 1
                
            except Exception as e:
                logger.error(f"Receive error: {e}")
                self.stats['errors'] += 1
                
        # Clean shutdown
        if self.socket:
            self.poller.unregister(self.socket)
            self.socket.close()
            
        if self.context:
            self.context.term()
            
        logger.info("ZMQ receiver stopped")
        
    def stop(self):
        """Stop the receiver"""
        self.running.clear()
        self.connected = False
        
    def get_market_data(self):
        """Get all current market data (Flask endpoint compatibility)"""
        result = {}
        
        # Get all tick data from cache
        for key in list(self.tick_cache.keys()):
            if key.startswith('tick_'):
                symbol = key.replace('tick_', '')
                result[symbol] = self.tick_cache[key]
                
        return result
        
    def get_venom_feed(self, symbol='EURUSD'):
        """Get data for VENOM feed (single symbol)"""
        cache_key = f"tick_{symbol}"
        return self.tick_cache.get(cache_key, {})


# Global receiver instance
receiver = None

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if receiver and receiver.connected:
        active_symbols = len(receiver.get_market_data())
        return jsonify({
            'status': 'healthy',
            'active_symbols': active_symbols,
            'streaming': True,
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        return jsonify({'status': 'unhealthy', 'error': 'Not connected'}), 503

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Get all market data"""
    if receiver:
        data = receiver.get_market_data()
        
        # Support fast parameter for compatibility
        if request.args.get('fast') == 'true':
            # Return only top 10 most active
            sorted_symbols = sorted(data.keys(), 
                                  key=lambda s: receiver.last_update.get(s, 0), 
                                  reverse=True)[:10]
            data = {s: data[s] for s in sorted_symbols if s in data}
            
        return jsonify({
            'status': 'success',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        return jsonify({'status': 'error', 'error': 'Receiver not initialized'}), 503

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """Get single symbol data for VENOM"""
    symbol = request.args.get('symbol', 'EURUSD')
    
    if receiver:
        data = receiver.get_venom_feed(symbol)
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'No data available'}), 404
    else:
        return jsonify({'error': 'Receiver not initialized'}), 503

@app.route('/market-data', methods=['POST'])
def legacy_post_endpoint():
    """Legacy endpoint for compatibility - now does nothing"""
    return jsonify({'status': 'deprecated', 'message': 'Use ZMQ streaming'}), 200


def start_zmq_receiver(endpoint):
    """Start ZMQ receiver in background thread"""
    global receiver
    receiver = ZMQMarketDataReceiver(endpoint)
    receiver_thread = Thread(target=receiver.run, daemon=True)
    receiver_thread.start()
    logger.info("ZMQ receiver thread started")


if __name__ == '__main__':
    # Get ZMQ endpoint from environment or default
    zmq_endpoint = os.environ.get('ZMQ_ENDPOINT', 'tcp://localhost:5555')
    
    # Start ZMQ receiver
    start_zmq_receiver(zmq_endpoint)
    
    # Give receiver time to connect
    time.sleep(2)
    
    # Start Flask app
    logger.info("Starting Flask API on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=False, processes=1)