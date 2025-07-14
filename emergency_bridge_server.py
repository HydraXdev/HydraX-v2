#!/usr/bin/env python3
"""
🚨 EMERGENCY BRIDGE SERVER
Minimal socket bridge for emergency trade execution
"""

import socket
import json
import threading
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EmergencyBridge')

class EmergencyBridgeServer:
    def __init__(self, port=9000):
        self.port = port
        self.running = False
        self.trades_received = 0
        
    def start(self):
        """Start the emergency bridge server"""
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(5)
            logger.info(f"🚨 Emergency Bridge Server listening on port {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, addr)
                    )
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    if self.running:
                        logger.error(f"Accept error: {e}")
                        
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            server_socket.close()
            
    def handle_client(self, client_socket, addr):
        """Handle client connection and trade requests"""
        try:
            # Set socket timeout
            client_socket.settimeout(10.0)
            
            # Receive data
            data = client_socket.recv(4096)
            if not data:
                return
                
            # Parse trade request
            try:
                trade_request = json.loads(data.decode('utf-8'))
                self.trades_received += 1
                
                logger.info(f"📨 Trade received from {addr}: {trade_request.get('symbol', 'UNKNOWN')} {trade_request.get('type', 'UNKNOWN')}")
                
                # Simulate trade processing
                response = {
                    "success": True,
                    "message": "Trade received by emergency bridge",
                    "trade_id": f"EMG_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "bridge_id": "emergency_bridge_001"
                }
                
                # Send response
                client_socket.send(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {addr}: {e}")
                error_response = {"success": False, "error": "Invalid JSON"}
                client_socket.send(json.dumps(error_response).encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            client_socket.close()
            
    def stop(self):
        """Stop the bridge server"""
        self.running = False
        logger.info("🛑 Emergency bridge server stopped")
        
    def get_stats(self):
        """Get bridge statistics"""
        return {
            "port": self.port,
            "trades_received": self.trades_received,
            "status": "running" if self.running else "stopped"
        }

def main():
    """Start emergency bridge server"""
    server = EmergencyBridgeServer(port=9000)
    
    try:
        logger.info("🚨 Starting Emergency Bridge Server...")
        server.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Shutdown requested")
        server.stop()

if __name__ == "__main__":
    main()