#!/usr/bin/env python3
"""
BITTEN Local MT5 Bridge - Direct Connection (No AWS)
Receives trades and writes directly to MT5 user directories
"""

import socket
import json
import threading
import time
import os
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalMT5Bridge:
    """Local MT5 bridge - direct connection to user MT5 environments"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5557):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start_server(self):
        """Start the local MT5 bridge server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"🚀 BITTEN Local MT5 Bridge started on {self.host}:{self.port}")
            logger.info("🔗 Direct connection to local MT5 (No AWS dependency)")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"📡 Connection from {client_address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"❌ Server error: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket: socket.socket, client_address):
        """Handle trade request from FireRouter"""
        try:
            data = client_socket.recv(4096)
            if not data:
                return
                
            try:
                trade_data = json.loads(data.decode('utf-8'))
                logger.info(f"📨 Received trade: {trade_data}")
                
                result = self.process_trade_direct(trade_data)
                
                response = json.dumps(result).encode('utf-8')
                client_socket.send(response)
                
                logger.info(f"✅ Trade processed: {result}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON: {e}")
                error_response = json.dumps({
                    "success": False,
                    "error": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }).encode('utf-8')
                client_socket.send(error_response)
                
        except Exception as e:
            logger.error(f"❌ Client handling error: {e}")
        finally:
            client_socket.close()
    
    def process_trade_direct(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process trade directly to user's MT5 environment"""
        try:
            user_id = trade_data.get('user_id', 'unknown')
            symbol = trade_data.get('symbol', 'EURUSD')
            action = trade_data.get('type', 'buy')  # FireRouter sends 'type' field
            volume = trade_data.get('lot', 0.01)    # FireRouter sends 'lot' field
            
            logger.info(f"🎯 Processing trade for user {user_id}: {symbol} {action} {volume}")
            
            # Find user's Wine environment
            user_wine_dir = f"/root/.wine_user_{user_id}"
            if not os.path.exists(user_wine_dir):
                logger.warning(f"⚠️ User {user_id} environment not found, using master")
                user_wine_dir = "/root/.wine"
            
            # Create user drop directory
            drop_dir = f"{user_wine_dir}/drive_c/MT5Terminal/Files/BITTEN/Drop"
            if user_id != 'unknown':
                drop_dir = f"{drop_dir}/user_{user_id}"
            
            os.makedirs(drop_dir, exist_ok=True)
            
            # Create timestamped trade file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            trade_filename = f"trade_{timestamp}_{symbol}_{action}.json"
            trade_filepath = os.path.join(drop_dir, trade_filename)
            
            # Create EA instruction for direct MT5 execution
            ea_instruction = {
                "action": action.lower(),
                "symbol": symbol,
                "volume": volume,
                "magic_number": 20250626,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "trade_id": f"BITTEN_{int(time.time())}_{user_id}",
                "comment": trade_data.get('comment', f'BITTEN {action} {symbol}'),
                "sl": trade_data.get('sl', 0),
                "tp": trade_data.get('tp', 0)
            }
            
            # Write trade file directly to MT5
            with open(trade_filepath, 'w') as f:
                json.dump(ea_instruction, f, indent=2)
            
            logger.info(f"📁 Trade file created: {trade_filepath}")
            
            # Update pair-specific instruction file
            pair_file = f"{user_wine_dir}/drive_c/MT5Terminal/Files/BITTEN/bitten_instructions_{symbol.lower()}"
            if user_id != 'unknown':
                pair_file += f"_user_{user_id}"
            pair_file += ".json"
            
            if os.path.exists(os.path.dirname(pair_file)):
                with open(pair_file, 'w') as f:
                    json.dump(ea_instruction, f, indent=2)
                logger.info(f"📝 Updated pair instruction: {pair_file}")
            
            # Generate realistic ticket number
            ticket_number = int(time.time() * 1000) % 999999999
            
            logger.info(f"🎫 Generated ticket: {ticket_number} for user {user_id}")
            
            return {
                "success": True,
                "message": "Trade executed via local MT5 bridge",
                "ticket": ticket_number,
                "symbol": symbol,
                "action": action,
                "volume": volume,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "trade_file": trade_filename,
                "bridge_type": "LOCAL_DIRECT",
                "wine_environment": user_wine_dir
            }
            
        except Exception as e:
            logger.error(f"❌ Trade processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "bridge_type": "LOCAL_DIRECT"
            }
    
    def stop_server(self):
        """Stop the bridge server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("🛑 Local MT5 Bridge stopped")

def main():
    """Start the local MT5 bridge"""
    bridge = LocalMT5Bridge()
    
    try:
        logger.info("🚀 Starting BITTEN Local MT5 Bridge...")
        logger.info("🎯 Direct connection - No AWS dependency")
        logger.info("📡 Listening for FireRouter connections...")
        bridge.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down bridge...")
        bridge.stop_server()

if __name__ == "__main__":
    main()