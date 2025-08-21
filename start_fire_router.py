#!/usr/bin/env python3
"""
Fire Router Service - Routes trade commands to MT5 via ZMQ
Manages the critical fire execution pipeline
"""

import zmq
import json
import time
import logging
from datetime import datetime
import signal
import sys
import os

# Add HydraX to path
sys.path.insert(0, '/root/HydraX-v2')

from src.bitten_core.fire_router import FireRouter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FireRouterService:
    def __init__(self):
        self.running = True
        self.context = zmq.Context()
        self.fire_router = None
        self.command_socket = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info("🛑 Shutdown signal received, cleaning up...")
        self.running = False
        if self.command_socket:
            self.command_socket.close()
        if self.context:
            self.context.term()
        sys.exit(0)
    
    def setup_command_listener(self):
        """Setup ZMQ socket to receive fire commands"""
        try:
            # Listen for fire commands from webapp
            self.command_socket = self.context.socket(zmq.PULL)
            self.command_socket.connect("ipc:///tmp/bitten_fire_commands")
            self.command_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            logger.info("✅ Connected to fire command queue at ipc:///tmp/bitten_fire_commands")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup command listener: {e}")
            return False
    
    def process_fire_command(self, command):
        """Process incoming fire command"""
        try:
            logger.info(f"🔫 Processing fire command: {command.get('signal_id')}")
            
            # Extract required fields
            user_id = command.get('user_id', '7176191872')  # Default to commander
            signal_id = command.get('signal_id')
            
            if not signal_id:
                logger.error("❌ No signal_id in command")
                return
            
            # Execute via FireRouter
            result = self.fire_router.execute_fire_command(
                user_id=user_id,
                signal_id=signal_id
            )
            
            if result.get('success'):
                logger.info(f"✅ Fire executed successfully: {result}")
            else:
                logger.error(f"❌ Fire failed: {result}")
                
        except Exception as e:
            logger.error(f"❌ Error processing fire command: {e}")
    
    def run(self):
        """Main service loop"""
        logger.info("🚀 Starting Fire Router Service...")
        
        # Initialize FireRouter
        try:
            self.fire_router = FireRouter()
            logger.info("✅ FireRouter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize FireRouter: {e}")
            return
        
        # Setup command listener
        if not self.setup_command_listener():
            return
        
        logger.info("🎯 Fire Router Service ready and listening for commands...")
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # Check for incoming commands (non-blocking with timeout)
                try:
                    command = self.command_socket.recv_json(flags=zmq.NOBLOCK)
                    self.process_fire_command(command)
                except zmq.Again:
                    # No message available, continue
                    pass
                
                # Send heartbeat every 30 seconds
                if time.time() - last_heartbeat > 30:
                    logger.info("💓 Fire Router Service heartbeat - alive and listening")
                    last_heartbeat = time.time()
                
                # Brief sleep to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(1)  # Wait before retry

if __name__ == "__main__":
    service = FireRouterService()
    service.run()