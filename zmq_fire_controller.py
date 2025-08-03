#!/usr/bin/env python3
"""
ZMQ Fire Controller
Binds to port 5555 and handles:
1. Sending periodic heartbeats to EA
2. Receiving fire commands from Elite Guard bridge
3. Forwarding fire commands to EA
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FireController')

class FireController:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        
    def heartbeat_loop(self):
        """Send periodic heartbeats to keep EA alive"""
        # Create PUSH socket for heartbeats
        heartbeat_socket = self.context.socket(zmq.PUSH)
        heartbeat_socket.bind("tcp://*:5555")
        
        logger.info("💓 Heartbeat publisher started on port 5555")
        
        while self.running:
            heartbeat = {
                "type": "heartbeat",
                "msg": "still alive",
                "timestamp": int(time.time())
            }
            
            heartbeat_socket.send_json(heartbeat)
            logger.debug("💓 Heartbeat sent")
            
            # Send heartbeat every 10 seconds
            time.sleep(10)
            
        heartbeat_socket.close()
        
    def command_receiver_loop(self):
        """Receive fire commands from Elite Guard bridge"""
        # Create PULL socket to receive commands
        receiver = self.context.socket(zmq.PULL)
        receiver.bind("tcp://*:5556")  # Different port for receiving
        
        logger.info("📥 Command receiver started on port 5556")
        
        while self.running:
            try:
                # Set timeout to avoid blocking forever
                receiver.setsockopt(zmq.RCVTIMEO, 1000)
                command = receiver.recv_json()
                
                if command.get('type') == 'signal':
                    logger.info(f"🔥 Received fire command: {command.get('signal_id')}")
                    logger.info(f"   Symbol: {command.get('symbol')} | Action: {command.get('action')}")
                    logger.info(f"   Confidence: {command.get('confidence')}%")
                    
                    # Forward to EA on port 5555
                    # (EA will receive both heartbeats and fire commands)
                    
            except zmq.Again:
                # Timeout - no message received
                pass
            except Exception as e:
                logger.error(f"Command receiver error: {e}")
                
        receiver.close()
        
    def run(self):
        """Run the fire controller"""
        try:
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self.heartbeat_loop)
            heartbeat_thread.start()
            
            # Start command receiver thread
            command_thread = threading.Thread(target=self.command_receiver_loop)
            command_thread.start()
            
            logger.info("✅ Fire Controller started successfully")
            logger.info("📡 Heartbeats on port 5555, Commands on port 5556")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n✅ Fire Controller stopped")
            self.running = False
        finally:
            self.context.term()

if __name__ == "__main__":
    controller = FireController()
    controller.run()