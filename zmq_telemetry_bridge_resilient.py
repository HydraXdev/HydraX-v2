#!/usr/bin/env python3
"""
Resilient ZMQ Telemetry Bridge with Anti-Freeze Protection
Receives telemetry on port 5556 and republishes on port 5560
Features:
- Non-blocking recv with timeout
- Heartbeat monitoring 
- Auto-recovery from stuck states
- Data flow metrics
"""

import zmq
import json
import logging
import time
import signal
import sys
from datetime import datetime
from time import monotonic
from src.bitten_core.tiered_exit_integration import drive_exits_for_active_positions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ResilientTelemetryBridge')

class ResilientTelemetryBridge:
    def __init__(self):
        self.context = zmq.Context()
        self.receiver = None
        self.publisher = None
        self.message_count = 0
        self.last_message_time = time.time()
        self.last_heartbeat_time = time.time()
        self.running = True
        
        # Metrics for monitoring
        self.ticks_per_minute = 0
        self.last_minute_mark = time.time()
        self.minute_tick_count = 0
        
        # Hook B: Track quotes and drive exit FSM
        self.quotes = {}  # symbol -> {"bid": x, "ask": y}
        self.last_drive_ts = 0.0
        self.DRIVE_MIN_GAP = 0.10  # 100ms debounce
        self.symbols_we_manage = {"USDJPY"}  # Canary symbol for testing
        
    def setup_sockets(self):
        """Setup ZMQ sockets with proper options"""
        # PULL socket with timeout
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        self.receiver.setsockopt(zmq.LINGER, 0)  # Don't hang on close
        self.receiver.bind("tcp://*:5556")
        logger.info("✅ Bound to port 5556 (PULL from EA) with 5s timeout")
        
        # PUB socket
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.setsockopt(zmq.LINGER, 0)
        self.publisher.bind("tcp://*:5560")
        logger.info("✅ Bound to port 5560 (PUB to subscribers)")
        
    def cleanup(self):
        """Clean shutdown of sockets"""
        logger.info("🛑 Shutting down telemetry bridge...")
        self.running = False
        if self.receiver:
            self.receiver.close()
        if self.publisher:
            self.publisher.close()
        if self.context:
            self.context.term()
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📌 Received signal {signum}")
        self.cleanup()
        sys.exit(0)
        
    def check_health(self):
        """Monitor bridge health and auto-recover if needed"""
        current_time = time.time()
        
        # Check if we haven't received data in 30 seconds
        if current_time - self.last_message_time > 30:
            logger.warning(f"⚠️ No data received for {int(current_time - self.last_message_time)} seconds")
            
            # If no data for 60 seconds, try to recover
            if current_time - self.last_message_time > 60:
                logger.error("🔴 No data for 60s - attempting recovery")
                self.recover_connection()
                
        # Calculate ticks per minute
        if current_time - self.last_minute_mark >= 60:
            self.ticks_per_minute = self.minute_tick_count
            logger.info(f"📊 Data rate: {self.ticks_per_minute} ticks/minute")
            self.minute_tick_count = 0
            self.last_minute_mark = current_time
            
    def recover_connection(self):
        """Attempt to recover from stuck state"""
        logger.info("🔄 Attempting connection recovery...")
        
        try:
            # Close existing sockets
            if self.receiver:
                self.receiver.close()
            if self.publisher:
                self.publisher.close()
                
            # Wait a moment
            time.sleep(2)
            
            # Recreate sockets
            self.setup_sockets()
            self.last_message_time = time.time()
            logger.info("✅ Recovery complete - sockets recreated")
            
        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")
            
    def process_message(self, message):
        """Process and republish messages"""
        self.message_count += 1
        self.last_message_time = time.time()
        
        # Track tick rate
        if "TICK" in message or "tick" in message:
            self.minute_tick_count += 1
        
        # Check for OHLC messages
        if message.startswith("OHLC "):
            self.publisher.send_string(message)
            if self.message_count % 100 == 1:
                try:
                    ohlc_data = json.loads(message[5:])
                    logger.info(f"📊 OHLC: {ohlc_data.get('symbol')} {ohlc_data.get('timeframe')}")
                except:
                    pass
                    
        elif message.startswith("HEARTBEAT"):
            self.publisher.send_string(message)
            self.last_heartbeat_time = time.time()
            if self.message_count % 30 == 0:
                logger.info(f"💓 Heartbeat #{self.message_count} - Healthy")
                
        else:
            # Try to parse as JSON (tick data)
            try:
                data = json.loads(message)
                
                # Log first 5 messages
                if self.message_count <= 5:
                    logger.info(f"📊 Message {self.message_count}: {data.get('symbol', 'unknown')}")
                
                # Detect position closes IMMEDIATELY
                try:
                    from src.bitten_core.position_close_detector import detect_position_closes
                    detect_position_closes(data)
                except Exception as e:
                    pass  # Silent fail, non-critical
                
                # Hook B: Accumulate quotes for exit FSM
                if 'symbol' in data and 'bid' in data and 'ask' in data:
                    symbol = data['symbol']
                    self.quotes[symbol] = {
                        "bid": float(data['bid']),
                        "ask": float(data['ask'])
                    }
                    
                    # Drive exits if it's time and we have the canary symbol
                    now = monotonic()
                    if now - self.last_drive_ts >= self.DRIVE_MIN_GAP:
                        # Filter for managed symbols only
                        snapshot = {s: self.quotes[s] for s in self.quotes.keys() & self.symbols_we_manage
                                  if "bid" in self.quotes[s] and "ask" in self.quotes[s]}
                        
                        if snapshot:
                            # 🔥 Hook B: Drive the exit FSM
                            try:
                                drive_exits_for_active_positions(snapshot)
                                if self.message_count % 500 == 0:  # Log periodically
                                    logger.info(f"🎯 Hook B: Driving exits for {list(snapshot.keys())}")
                            except Exception as e:
                                logger.error(f"Hook B error: {e}")
                            
                            # Check for position timeouts
                            try:
                                from src.bitten_core.tiered_exit_integration import _check_position_timeouts
                                _check_position_timeouts()
                            except Exception as e:
                                logger.error(f"Timeout check error: {e}")
                            
                            # Clean up stale positions every 50 messages (more frequent)
                            # This runs approximately every 5-10 seconds
                            if self.message_count % 50 == 0:
                                try:
                                    from src.bitten_core.position_close_updater import check_orphaned_positions
                                    check_orphaned_positions()
                                except Exception as e:
                                    logger.debug(f"Position cleanup: {e}")
                            
                            self.last_drive_ts = now
                    
                # Republish as JSON
                self.publisher.send_json(data)
                
            except json.JSONDecodeError:
                # Still republish as string
                self.publisher.send_string(message)
                
    def run(self):
        """Main loop with timeout protection"""
        logger.info("📡 Starting resilient telemetry bridge...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup sockets
        self.setup_sockets()
        
        last_health_check = time.time()
        
        while self.running:
            try:
                # Non-blocking receive with timeout
                try:
                    message = self.receiver.recv_string(flags=zmq.NOBLOCK)
                    self.process_message(message)
                    
                except zmq.Again:
                    # No message available (timeout) - this is normal
                    pass
                    
                except zmq.error.ZMQError as e:
                    if e.errno == zmq.EAGAIN:
                        # This is expected with NOBLOCK
                        pass
                    else:
                        logger.error(f"ZMQ Error: {e}")
                        time.sleep(1)
                        
                # Periodic health check
                if time.time() - last_health_check > 10:
                    self.check_health()
                    last_health_check = time.time()
                    
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(1)
                
        logger.info("🛑 Telemetry bridge stopped")

if __name__ == "__main__":
    bridge = ResilientTelemetryBridge()
    bridge.run()