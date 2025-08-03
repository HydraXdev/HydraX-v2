#!/usr/bin/env python3
"""
ZMQ Fire Bridge - Integrates BITTEN fire commands with ZMQ
Replaces file-based fire.txt with real-time ZMQ communication
"""

import zmq
import json
import time
import logging
from typing import Dict, Optional, Callable
from collections import defaultdict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ZMQFireBridge')

class ZMQFireBridge:
    """
    Bridge between BITTEN fire router and MT5 via ZMQ
    Replaces file-based communication with sockets
    """
    
    def __init__(self, fire_port=9001, telemetry_port=9101):
        self.fire_port = fire_port
        self.telemetry_port = telemetry_port
        
        # ZMQ contexts
        self.ctx = zmq.Context()
        self.fire_socket = None
        self.telemetry_socket = None
        
        # User tracking
        self.user_sockets = {}  # uuid -> (fire_port, telemetry_port)
        self.user_telemetry = defaultdict(dict)
        self.trade_callbacks = {}  # uuid -> callback function
        
        # Threading
        self.running = False
        self.telemetry_thread = None
        
        logger.info(f"ZMQ Fire Bridge initialized")
        
    def start(self):
        """Start the bridge services"""
        self.running = True
        
        # Start telemetry listener
        self.telemetry_thread = threading.Thread(target=self._telemetry_listener)
        self.telemetry_thread.start()
        
        logger.info("✅ ZMQ Fire Bridge started")
        
    def stop(self):
        """Stop the bridge services"""
        self.running = False
        
        if self.telemetry_thread:
            self.telemetry_thread.join()
            
        # Close all sockets
        for uuid, (fire_socket, _) in self.user_sockets.items():
            if fire_socket:
                fire_socket.close()
                
        self.ctx.term()
        logger.info("ZMQ Fire Bridge stopped")
        
    def register_user(self, uuid: str, fire_port: int = None, telemetry_port: int = None):
        """
        Register a user with specific ports
        For multi-user support, each user gets unique ports
        """
        if fire_port is None:
            fire_port = self.fire_port + hash(uuid) % 1000
        if telemetry_port is None:
            telemetry_port = self.telemetry_port + hash(uuid) % 1000
            
        # Create fire socket for user
        fire_socket = self.ctx.socket(zmq.PUB)
        fire_socket.bind(f"tcp://*:{fire_port}")
        
        self.user_sockets[uuid] = (fire_socket, telemetry_port)
        
        logger.info(f"Registered user {uuid} - Fire: {fire_port}, Telemetry: {telemetry_port}")
        return fire_port, telemetry_port
        
    def execute_trade(self, uuid: str, signal_data: Dict, callback: Optional[Callable] = None) -> bool:
        """
        Execute a trade via ZMQ (replaces fire.txt write)
        
        Args:
            uuid: User identifier
            signal_data: Trade signal data
            callback: Optional callback for trade result
        
        Returns:
            bool: True if command sent successfully
        """
        # Get user's fire socket
        if uuid not in self.user_sockets:
            logger.error(f"User {uuid} not registered")
            return False
            
        fire_socket, _ = self.user_sockets[uuid]
        
        # Prepare fire packet
        fire_packet = {
            "uuid": uuid,
            "signal_id": signal_data.get('signal_id', ''),
            "action": signal_data.get('type', 'BUY').upper(),
            "symbol": signal_data.get('symbol', 'EURUSD'),
            "lot": signal_data.get('lot', 0.01),
            "tp": signal_data.get('tp_pips', 0),
            "sl": signal_data.get('sl_pips', 0),
            "timestamp": int(time.time())
        }
        
        # Store callback if provided
        if callback:
            self.trade_callbacks[uuid] = callback
            
        # Send fire command
        try:
            message = json.dumps(fire_packet)
            fire_socket.send_string(message, zmq.NOBLOCK)
            
            logger.info(f"🔥 Fire command sent for {uuid}: {signal_data.get('symbol')} {signal_data.get('type')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send fire command: {e}")
            return False
            
    def get_user_telemetry(self, uuid: str) -> Dict:
        """Get latest telemetry for a user"""
        return self.user_telemetry.get(uuid, {})
        
    def _telemetry_listener(self):
        """Background thread to listen for telemetry"""
        # Create telemetry socket
        telemetry_socket = self.ctx.socket(zmq.PULL)
        telemetry_socket.bind(f"tcp://*:{self.telemetry_port}")
        telemetry_socket.setsockopt(zmq.RCVTIMEO, 1000)
        
        logger.info(f"📡 Telemetry listener started on port {self.telemetry_port}")
        
        while self.running:
            try:
                message = telemetry_socket.recv()
                data = json.loads(message.decode())
                
                uuid = data.get('uuid', 'unknown')
                msg_type = data.get('type', 'telemetry')
                
                if msg_type == 'trade_result':
                    # Handle trade result
                    self._handle_trade_result(uuid, data)
                else:
                    # Update telemetry
                    self.user_telemetry[uuid] = data
                    
            except zmq.Again:
                continue
            except Exception as e:
                logger.error(f"Telemetry error: {e}")
                
        telemetry_socket.close()
        
    def _handle_trade_result(self, uuid: str, result: Dict):
        """Handle trade execution result"""
        success = result.get('success', False)
        message = result.get('message', '')
        ticket = result.get('ticket', 0)
        
        logger.info(f"📊 Trade result for {uuid}: {'✅ Success' if success else '❌ Failed'} - {message}")
        
        # Call callback if registered
        if uuid in self.trade_callbacks:
            callback = self.trade_callbacks.pop(uuid)
            try:
                callback(success, result)
            except Exception as e:
                logger.error(f"Callback error: {e}")

# Singleton instance
_bridge_instance = None

def get_zmq_bridge() -> ZMQFireBridge:
    """Get or create the ZMQ bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ZMQFireBridge()
        _bridge_instance.start()
    return _bridge_instance

def execute_zmq_trade(uuid: str, signal_data: Dict) -> bool:
    """
    Convenience function to execute trade via ZMQ
    Drop-in replacement for file-based fire execution
    """
    bridge = get_zmq_bridge()
    
    # Register user if needed
    if uuid not in bridge.user_sockets:
        bridge.register_user(uuid)
        
    return bridge.execute_trade(uuid, signal_data)

if __name__ == "__main__":
    # Test the bridge
    import sys
    
    print("🚀 ZMQ Fire Bridge Test")
    print("=" * 50)
    
    bridge = ZMQFireBridge()
    bridge.start()
    
    # Register test user
    uuid = "test-user-001"
    fire_port, telemetry_port = bridge.register_user(uuid)
    
    print(f"User registered: {uuid}")
    print(f"Fire port: {fire_port}")
    print(f"Telemetry port: {telemetry_port}")
    
    # Wait for telemetry
    print("\n⏳ Waiting for telemetry...")
    time.sleep(3)
    
    telemetry = bridge.get_user_telemetry(uuid)
    if telemetry:
        print(f"✅ Telemetry received: Balance=${telemetry.get('balance', 0):,.2f}")
    
    # Send test trade
    if len(sys.argv) > 1 and sys.argv[1] == "fire":
        print("\n🔥 Sending test trade...")
        signal = {
            "signal_id": "TEST_001",
            "type": "BUY",
            "symbol": "XAUUSD",
            "lot": 0.1,
            "tp_pips": 40,
            "sl_pips": 20
        }
        
        def result_callback(success, data):
            print(f"\n📊 Trade callback: {'✅' if success else '❌'} {data}")
            
        bridge.execute_trade(uuid, signal, result_callback)
        
        # Wait for result
        time.sleep(5)
    
    # Cleanup
    bridge.stop()
    print("\n✅ Test complete")