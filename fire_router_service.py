#!/usr/bin/env python3
"""
Fire Router Service - Binds port 5555 for EA connections
Replaces final_fire_publisher with proper rule-validated execution
All trades MUST come through BittenCore validation first
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
import sys

sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

from src.bitten_core.fire_router import get_fire_router, ExecutionMode, TradeRequest, TradeDirection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FireRouterService')

class FireRouterService:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        self.fire_router = get_fire_router(ExecutionMode.LIVE)
        
    def command_listener_loop(self):
        """Listen for validated fire commands from BittenCore"""
        # Bind as PUSH server for EA to connect as PULL client
        publisher = self.context.socket(zmq.PUSH)
        publisher.bind("tcp://*:5555")
        
        logger.info("🔥 Fire Router Service started on port 5555")
        logger.info("⚠️ Only accepts validated commands from BittenCore")
        
        # Also listen for commands from BittenCore (internal)
        command_receiver = self.context.socket(zmq.PULL)
        command_receiver.bind("tcp://127.0.0.1:5554")  # Internal port for BittenCore
        
        logger.info("📡 Listening for BittenCore commands on port 5554")
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # Check for commands from BittenCore
                command_receiver.setsockopt(zmq.RCVTIMEO, 100)
                
                try:
                    command = command_receiver.recv_json()
                    logger.info(f"📨 Received command from BittenCore: {command.get('signal_id')}")
                    
                    # Validate it's from BittenCore
                    if command.get('source') != 'BittenCore':
                        logger.warning("❌ Rejected command - not from BittenCore")
                        continue
                    
                    # Forward to EA as fire command
                    # EA v2.03 expects explicit direction field
                    direction = command.get('direction', 'BUY').upper()
                    
                    # EA v2.03 can handle explicit direction, so we can use entry price
                    fire_command = {
                        "type": "fire",
                        "target_uuid": command.get('target_uuid', 'COMMANDER_DEV_001'),
                        "symbol": command.get('symbol'),
                        "direction": direction,  # EA v2.03 uses this field!
                        "entry": command.get('entry_price', 0),  # Can use actual entry or 0 for market
                        "sl": command.get('stop_loss', 0),  # Use actual price level from FireRouter
                        "tp": command.get('take_profit', 0),  # Use actual price level from FireRouter
                        "lot": command.get('lot_size', 0.01),
                        "timestamp": datetime.utcnow().isoformat(),
                        "signal_id": command.get('signal_id'),
                        "validated": True  # Mark as validated by BittenCore
                    }
                    
                    # Log the exact command being sent to EA
                    logger.info(f"📤 Sending to EA: {json.dumps(fire_command, indent=2)}")
                    publisher.send_json(fire_command)
                    logger.info(f"✅ Forwarded validated command to EA: {command.get('signal_id')}")
                    
                except zmq.Again:
                    pass  # No commands, continue
                
                # Send heartbeat to EA
                if time.time() - last_heartbeat >= 10:
                    heartbeat = {
                        "type": "heartbeat",
                        "msg": "fire_router_service",
                        "timestamp": int(time.time())
                    }
                    publisher.send_json(heartbeat)
                    logger.debug("💓 Heartbeat sent to EA")
                    last_heartbeat = time.time()
                    
            except Exception as e:
                logger.error(f"Command listener error: {e}")
                
        publisher.close()
        command_receiver.close()
        
    def run(self):
        """Run the fire router service"""
        try:
            # Start command listener
            listener_thread = threading.Thread(target=self.command_listener_loop)
            listener_thread.start()
            
            logger.info("✅ Fire Router Service operational")
            logger.info("🔒 All trades must be validated through BittenCore")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Fire Router Service stopped")
            self.running = False
        finally:
            self.context.term()

if __name__ == "__main__":
    service = FireRouterService()
    service.run()