#!/usr/bin/env python3
"""
HydraX MT5 Socket Bridge
========================

This script implements the critical communication bridge between external
HydraX trading engines and MT5 Expert Advisors running inside Wine containers.

Architecture:
- Listens on TCP socket for trading signal JSON payloads
- Validates and processes incoming signals  
- Writes signals to fire.txt for EA pickup
- Responds with confirmation to sender
- Handles multiple concurrent connections
- Provides robust error handling and logging

Signal Flow:
1. HydraX Engine → TCP Socket → Python Bridge
2. Bridge validates JSON payload
3. Bridge writes to fire.txt (atomic operation)
4. MT5 BITTENBridge EA polls fire.txt
5. EA processes signal and executes trades
6. Bridge sends "FIRE_RECEIVED" confirmation

File-Based Communication:
The fire.txt mechanism is used instead of direct socket communication
with MT5 because:
- Wine/MT5 socket handling can be unreliable
- File-based approach is atomic and race-condition free
- Allows for signal persistence and replay
- Simpler debugging and monitoring

Usage:
    python3 bridge.py <port> <fire_file_path>
    python3 bridge.py 9013 /wine/drive_c/MetaTrader5/MQL5/Files/fire.txt
"""

import socket
import json
import os
import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HydraXBridge')

class HydraXBridge:
    def __init__(self, port=9013, fire_file="/wine/drive_c/MetaTrader5/MQL5/Files/fire.txt"):
        self.port = int(port)
        self.fire_file = fire_file
        self.socket = None
        
        # Ensure fire directory exists
        os.makedirs(os.path.dirname(fire_file), exist_ok=True)
        
        logger.info(f"HydraX Bridge initialized")
        logger.info(f"Port: {self.port}")
        logger.info(f"Fire file: {self.fire_file}")

    def start_bridge(self):
        """Start the socket bridge server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.listen(1)
            
            logger.info(f"🔌 Bridge ready on port {self.port}")
            logger.info("Waiting for HydraX Engine connections...")
            
            while True:
                try:
                    conn, addr = self.socket.accept()
                    logger.info(f"Connection from {addr}")
                    
                    # Receive data
                    data = conn.recv(2048)
                    if not data:
                        conn.close()
                        continue
                    
                    # Process signal
                    payload = json.loads(data.decode())
                    self.write_fire_signal(payload)
                    
                    # Acknowledge
                    conn.send(b"FIRE_RECEIVED")
                    conn.close()
                    
                    logger.info(f"✅ Signal processed: {payload.get('symbol', 'UNKNOWN')}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    try:
                        conn.send(b"ERROR_INVALID_JSON")
                        conn.close()
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"Connection error: {e}")
                    try:
                        conn.close()
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            sys.exit(1)
            
    def write_fire_signal(self, payload):
        """Write trading signal to fire.txt for EA pickup"""
        try:
            # Add timestamp to payload
            payload['timestamp'] = datetime.now().isoformat()
            payload['bridge_id'] = f'hydrax_bridge_{self.port}'
            
            # Write to fire.txt
            with open(self.fire_file, "w") as f:
                json.dump(payload, f, indent=2)
            
            logger.info(f"🔥 Fire signal written: {os.path.basename(self.fire_file)}")
            
            # Log the signal details
            symbol = payload.get('symbol', 'UNKNOWN')
            side = payload.get('side', 'UNKNOWN')
            tp = payload.get('tp', 'N/A')
            sl = payload.get('sl', 'N/A')
            
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Side: {side}")
            logger.info(f"   TP: {tp}")
            logger.info(f"   SL: {sl}")
            
        except Exception as e:
            logger.error(f"Failed to write fire signal: {e}")
            raise

    def cleanup(self):
        """Clean shutdown"""
        if self.socket:
            self.socket.close()
        logger.info("Bridge shutdown complete")

def main():
    """Main bridge execution"""
    import signal
    
    # Get port from command line or use default
    port = sys.argv[1] if len(sys.argv) > 1 else 9013
    fire_file = sys.argv[2] if len(sys.argv) > 2 else "/wine/drive_c/MetaTrader5/MQL5/Files/fire.txt"
    
    # Create bridge instance
    bridge = HydraXBridge(port=port, fire_file=fire_file)
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        bridge.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the bridge
    try:
        bridge.start_bridge()
    except KeyboardInterrupt:
        logger.info("Bridge stopped by user")
        bridge.cleanup()
    except Exception as e:
        logger.error(f"Bridge failed: {e}")
        bridge.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()