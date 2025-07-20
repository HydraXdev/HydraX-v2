#!/usr/bin/env python3
"""
MT5 Bridge Server - Enhanced production bridge for BITTEN
Handles socket commands: ping, fire
Auto-reconnects to MT5 and executes real trades
"""

import socket
import json
import threading
import logging
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add the project root to the path for imports
sys.path.append('/root/HydraX-v2')

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("WARNING: MetaTrader5 library not available. Install with: pip install MetaTrader5")

class MT5BridgeServer:
    """Enhanced MT5 Bridge Server for BITTEN production system"""
    
    def __init__(self, port=9000):
        self.port = port
        self.running = False
        self.socket = None
        
        # MT5 connection credentials (should be configured)
        self.mt5_account = None
        self.mt5_password = None
        self.mt5_server = None
        self.mt5_broker = "Unknown"
        
        # Supported symbols
        self.supported_symbols = ["XAUUSD", "GBPJPY", "USDJPY", "EURUSD"]
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize MT5 connection
        self.initialize_mt5()
        
    def setup_logging(self):
        """Setup logging with [BRIDGE] prefix"""
        # Create custom formatter
        class BridgeFormatter(logging.Formatter):
            def format(self, record):
                record.msg = f"[BRIDGE] {record.msg}"
                return super().format(record)
        
        # Setup logger
        self.logger = logging.getLogger('MT5Bridge')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(BridgeFormatter())
        
        # File handler
        file_handler = logging.FileHandler('/root/HydraX-v2/logs/mt5_bridge.log')
        file_handler.setFormatter(BridgeFormatter())
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Remove duplicate handlers
        self.logger.propagate = False
        
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection with auto-reconnect"""
        if not MT5_AVAILABLE:
            self.logger.error("MT5 library not available")
            return False
            
        try:
            # First try to initialize without credentials
            if not mt5.initialize():
                self.logger.warning("MT5 initialization failed, trying with credentials...")
                
                # Try with credentials if available
                if self.mt5_account and self.mt5_password and self.mt5_server:
                    if not mt5.initialize(
                        login=self.mt5_account, 
                        password=self.mt5_password, 
                        server=self.mt5_server
                    ):
                        error = mt5.last_error()
                        self.logger.error(f"MT5 initialization with credentials failed: {error}")
                        return False
                else:
                    error = mt5.last_error()
                    self.logger.error(f"MT5 initialization failed: {error}")
                    return False
            
            # Get account info
            account = mt5.account_info()
            if account:
                self.mt5_account = account.login
                self.mt5_broker = account.company
                self.logger.info(f"MT5 connected to account {self.mt5_account} | Broker: {self.mt5_broker}")
                return True
            else:
                self.logger.error("Failed to get MT5 account info")
                return False
                
        except Exception as e:
            self.logger.error(f"MT5 initialization error: {e}")
            return False
    
    def ensure_mt5_connected(self) -> bool:
        """Ensure MT5 is connected, reconnect if needed"""
        if not MT5_AVAILABLE:
            return False
            
        try:
            # Test connection by getting account info
            account = mt5.account_info()
            if account:
                return True
            else:
                self.logger.warning("MT5 connection lost, attempting reconnect...")
                return self.initialize_mt5()
        except Exception as e:
            self.logger.warning(f"MT5 connection check failed: {e}, attempting reconnect...")
            return self.initialize_mt5()
    
    def handle_ping(self) -> Dict[str, Any]:
        """Handle ping command - return terminal status"""
        self.logger.info("Command received: PING")
        
        if not self.ensure_mt5_connected():
            return {
                "status": "offline",
                "error": "MT5 not connected",
                "ping": "FAILED"
            }
        
        try:
            account = mt5.account_info()
            if account:
                self.logger.info(f"Account: {account.login} | Broker: {account.company} | Balance: {account.balance}")
                
                return {
                    "status": "online",
                    "account": account.login,
                    "broker": account.company,
                    "balance": account.balance,
                    "symbols": self.supported_symbols,
                    "ping": "OK"
                }
            else:
                return {
                    "status": "offline",
                    "error": "No account info available",
                    "ping": "FAILED"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling ping: {e}")
            return {
                "status": "offline",
                "error": str(e),
                "ping": "FAILED"
            }
    
    def handle_fire(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fire command - execute trade"""
        symbol = trade_data.get('symbol', 'UNKNOWN')
        volume = trade_data.get('volume', 0.0)
        direction = trade_data.get('direction', 'UNKNOWN')
        
        self.logger.info(f"Command received: FIRE {symbol} {volume} lots {direction}")
        
        if not self.ensure_mt5_connected():
            return {
                "retcode": 10018,  # TRADE_RETCODE_CONNECTION
                "error": "MT5 not connected"
            }
        
        try:
            # Validate symbol
            if symbol not in self.supported_symbols:
                return {
                    "retcode": 10013,  # TRADE_RETCODE_INVALID_SYMBOL
                    "error": f"Symbol {symbol} not supported"
                }
            
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if direction.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "price": mt5.symbol_info_tick(symbol).ask if direction.upper() == 'BUY' else mt5.symbol_info_tick(symbol).bid,
                "deviation": 20,
                "magic": 234000,
                "comment": "BITTEN_BRIDGE_TRADE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if 'stop_loss' in trade_data and trade_data['stop_loss'] > 0:
                request['sl'] = float(trade_data['stop_loss'])
            if 'take_profit' in trade_data and trade_data['take_profit'] > 0:
                request['tp'] = float(trade_data['take_profit'])
            
            # Execute order
            result = mt5.order_send(request)
            
            if result:
                self.logger.info(f"Order sent. Retcode: {result.retcode} | Ticket: {result.order}")
                
                # Return full MT5 result as JSON
                return {
                    "retcode": result.retcode,
                    "ticket": result.order,
                    "symbol": symbol,
                    "volume": volume,
                    "price": result.price,
                    "sl": request.get('sl', 0),
                    "tp": request.get('tp', 0),
                    "comment": result.comment,
                    "request_id": result.request_id,
                    "bid": result.bid,
                    "ask": result.ask,
                    "volume_executed": result.volume
                }
            else:
                error = mt5.last_error()
                self.logger.error(f"Order failed: {error}")
                return {
                    "retcode": 10014,  # TRADE_RETCODE_REJECT
                    "error": f"Order send failed: {error}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {
                "retcode": 10014,  # TRADE_RETCODE_REJECT
                "error": str(e)
            }
    
    def handle_client(self, client_socket: socket.socket, addr: tuple):
        """Handle client connection"""
        try:
            client_socket.settimeout(30.0)
            
            # Receive command
            data = client_socket.recv(4096)
            if not data:
                return
            
            try:
                command = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON from {addr}: {e}")
                error_response = {"error": "Invalid JSON"}
                client_socket.send(json.dumps(error_response).encode('utf-8'))
                return
            
            # Process command
            if command.get('command') == 'ping':
                response = self.handle_ping()
            elif command.get('command') == 'fire':
                response = self.handle_fire(command.get('trade_data', {}))
            else:
                response = {"error": "Unknown command. Use 'ping' or 'fire'"}
            
            # Send response
            client_socket.send(json.dumps(response, indent=2).encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
    
    def start(self):
        """Start the bridge server"""
        self.running = True
        
        # Create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.logger.info(f"MT5 Bridge Server listening on port {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    # Handle each client in a separate thread
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    thread.start()
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Accept error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
    
    def stop(self):
        """Stop the bridge server"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Shutdown MT5
        if MT5_AVAILABLE:
            mt5.shutdown()
            
        self.logger.info("Bridge server stopped")

def main():
    """Main function"""
    print("🚀 Starting MT5 Bridge Server...")
    
    # Check if MT5 is available
    if not MT5_AVAILABLE:
        print("❌ MetaTrader5 library not installed!")
        print("Install with: pip install MetaTrader5")
        sys.exit(1)
    
    # Create and start server
    server = MT5BridgeServer(port=9000)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        server.stop()
    except Exception as e:
        print(f"❌ Server error: {e}")
        server.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()