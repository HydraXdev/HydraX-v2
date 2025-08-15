#!/usr/bin/env python3
"""
🎯 VENOM ZMQ Market Data Intake - Direct Connection
Bypasses HTTP market data receiver for direct ZMQ consumption
"""

import zmq
import json
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - VENOM-ZMQ - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MarketTick:
    """Market tick data from EA"""
    symbol: str
    bid: float
    ask: float
    spread: float
    volume: int
    timestamp: float
    
class VenomZMQIntake:
    """Direct ZMQ market data consumer for VENOM"""
    
    def __init__(self, zmq_host: str = "tcp://localhost:5555"):
        self.zmq_host = zmq_host
        self.context = zmq.Context()
        self.socket = None
        self.running = False
        self.receiver_thread = None
        
        # Market data cache
        self.market_data: Dict[str, MarketTick] = {}
        
        logger.info(f"🎯 VENOM ZMQ Intake initialized - connecting to {zmq_host}")
        
    def connect(self):
        """Bind to receive ZMQ market data feed"""
        try:
            # For market data, we need to BIND as the server
            # EA will CONNECT to us as a publisher
            self.socket = self.context.socket(zmq.PULL)
            
            # Use a different port for market data intake
            market_port = "tcp://*:5557"
            self.socket.bind(market_port)
            self.socket.setsockopt(zmq.RCVTIMEO, 100)  # 100ms timeout for responsive polling
            
            logger.info(f"✅ Bound to {market_port} - waiting for EA market data")
            logger.info("💡 EA should connect to tcp://134.199.204.67:5557 as PUSH")
            
            # Start receiver thread
            self.running = True
            self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receiver_thread.start()
            logger.info("🚀 ZMQ receiver thread started")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to ZMQ: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from ZMQ"""
        self.running = False
        if self.receiver_thread:
            self.receiver_thread.join(timeout=2)
        if self.socket:
            self.socket.close()
        self.context.term()
        logger.info("🔌 Disconnected from ZMQ")
        
    def process_market_data(self, data: Dict) -> Optional[MarketTick]:
        """Process incoming market data"""
        try:
            # Handle different data formats from EA
            if 'ticks' in data:
                # Process tick array format
                for tick_data in data.get('ticks', []):
                    symbol = tick_data.get('symbol')
                    if symbol:
                        tick = MarketTick(
                            symbol=symbol,
                            bid=tick_data.get('bid', 0),
                            ask=tick_data.get('ask', 0),
                            spread=tick_data.get('spread', 0),
                            volume=tick_data.get('volume', 0),
                            timestamp=time.time()
                        )
                        self.market_data[symbol] = tick
                        logger.debug(f"📊 {symbol}: {tick.bid}/{tick.ask} spread={tick.spread}")
                        
            elif 'symbol' in data:
                # Single tick format
                tick = MarketTick(
                    symbol=data['symbol'],
                    bid=data.get('bid', 0),
                    ask=data.get('ask', 0),
                    spread=data.get('spread', 0),
                    volume=data.get('volume', 0),
                    timestamp=time.time()
                )
                self.market_data[data['symbol']] = tick
                return tick
                
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            
        return None
        
    def get_market_snapshot(self) -> Dict[str, Dict]:
        """Get current market snapshot for VENOM"""
        snapshot = {}
        
        for symbol, tick in self.market_data.items():
            # Only include fresh data (< 5 seconds old)
            if (time.time() - tick.timestamp) < 5.0:
                snapshot[symbol] = {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.spread,
                    'volume': tick.volume,
                    'timestamp': tick.timestamp
                }
                
        return snapshot
        
    def run_intake_loop(self, callback=None):
        """Run the market data intake loop"""
        if not self.socket:
            if not self.connect():
                return
                
        self.running = True
        logger.info("🚀 Starting ZMQ market data intake loop")
        
        last_log = time.time()
        message_count = 0
        
        while self.running:
            try:
                # Receive ZMQ message
                message = self.socket.recv_string()
                message_count += 1
                
                # Parse JSON data
                data = json.loads(message)
                
                # Process market data
                self.process_market_data(data)
                
                # Call callback if provided (for VENOM integration)
                if callback:
                    snapshot = self.get_market_snapshot()
                    if snapshot:
                        callback(snapshot)
                
                # Periodic status log
                if time.time() - last_log > 10:
                    logger.info(f"📡 ZMQ intake active - {message_count} messages, {len(self.market_data)} symbols")
                    last_log = time.time()
                    message_count = 0
                    
            except zmq.Again:
                # Timeout - no message received
                pass
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                
            except Exception as e:
                logger.error(f"ZMQ intake error: {e}")
                time.sleep(1)  # Brief pause on error
                
    def stop(self):
        """Stop the intake loop"""
        self.running = False
        logger.info("⏹️ Stopping ZMQ intake")
        
    def _receive_loop(self):
        """Background thread to continuously receive market data"""
        logger.info("📡 ZMQ receive loop started")
        message_count = 0
        last_log = time.time()
        
        while self.running:
            try:
                # Try to receive a message
                message = self.socket.recv_string()
                message_count += 1
                
                # Parse JSON data
                data = json.loads(message)
                
                # Process market data
                self.process_market_data(data)
                
                # Periodic status log
                if time.time() - last_log > 10:
                    logger.info(f"📡 ZMQ receiving - {message_count} messages, {len(self.market_data)} symbols active")
                    last_log = time.time()
                    message_count = 0
                    
            except zmq.Again:
                # Timeout - no message received, this is normal
                pass
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"ZMQ receive error: {e}")
                time.sleep(0.1)  # Brief pause on error
        
        logger.info("📡 ZMQ receive loop stopped")
        

def test_zmq_connection():
    """Test ZMQ market data connection"""
    intake = VenomZMQIntake()
    
    if intake.connect():
        logger.info("🧪 Testing ZMQ market data reception...")
        
        # Try to receive a few messages
        received = 0
        for i in range(10):
            try:
                message = intake.socket.recv_string()
                data = json.loads(message)
                logger.info(f"✅ Received: {list(data.keys())}")
                received += 1
                
                if received >= 3:
                    break
                    
            except zmq.Again:
                logger.info("⏳ Waiting for market data...")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                
        intake.disconnect()
        
        if received > 0:
            logger.info(f"✅ Test successful - received {received} messages")
        else:
            logger.warning("⚠️ No market data received - EA might not be sending")
            
            
if __name__ == "__main__":
    test_zmq_connection()