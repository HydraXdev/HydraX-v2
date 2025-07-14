#!/usr/bin/env python3
"""
🌉 BRIDGE SYMBOL DISCOVERY FOR BITTEN
Python bridge agent integration for symbol discovery and translation

CAPABILITIES:
- MT5 symbol discovery via MetaTrader5 library
- Bridge communication with BITTEN fire server
- Symbol mapping initialization for new users
- Real-time symbol validation and translation
"""

import MetaTrader5 as mt5
import json
import socket
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# Import BITTEN components
import sys
import os
sys.path.append('/root/HydraX-v2/src')

try:
    from bitten_core.symbol_mapper import symbol_mapper
    from bitten_core.bridge_symbol_integration import bridge_integration
except ImportError as e:
    print(f"⚠️ BITTEN components not available: {e}")
    # Continue with standalone functionality

logger = logging.getLogger(__name__)

class MT5SymbolDiscovery:
    """
    🔍 MT5 SYMBOL DISCOVERY AGENT
    
    Handles symbol discovery and communication with BITTEN fire server
    """
    
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 5555):
        self.server_host = server_host
        self.server_port = server_port
        self.mt5_initialized = False
        self.user_id = None
        self.bridge_id = None
        self.discovered_symbols = []
        self.broker_info = {}
        
        # Socket server for receiving commands
        self.socket_server = None
        self.running = False
        
        logger.info(f"🔍 MT5 Symbol Discovery Agent initialized on {server_host}:{server_port}")
    
    def initialize_mt5(self, login: int = None, password: str = None, 
                      server: str = None) -> bool:
        """
        Initialize MT5 connection
        
        Args:
            login: MT5 account login
            password: MT5 account password  
            server: MT5 server name
            
        Returns:
            bool: Initialization success
        """
        try:
            # Initialize MT5
            if not mt5.initialize():
                logger.error("❌ MT5 initialization failed")
                return False
            
            # Login if credentials provided
            if login and password and server:
                if not mt5.login(login, password=password, server=server):
                    logger.error(f"❌ MT5 login failed for account {login}")
                    return False
                
                logger.info(f"✅ MT5 logged in: Account {login} on {server}")
            
            self.mt5_initialized = True
            
            # Get broker information
            account_info = mt5.account_info()
            if account_info:
                self.broker_info = {
                    "name": account_info.company,
                    "server": account_info.server,
                    "currency": account_info.currency,
                    "leverage": account_info.leverage,
                    "margin_mode": account_info.margin_mode,
                    "trade_mode": account_info.trade_mode
                }
                
                logger.info(f"📊 Broker: {self.broker_info['name']} ({self.broker_info['server']})")
            
            # Discover symbols
            self._discover_all_symbols()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ MT5 initialization error: {e}")
            return False
    
    def _discover_all_symbols(self) -> bool:
        """Discover all available symbols from MT5"""
        try:
            if not self.mt5_initialized:
                logger.error("❌ MT5 not initialized")
                return False
            
            logger.info("🔍 Discovering MT5 symbols...")
            
            # Get all symbols
            symbols = mt5.symbols_get()
            
            if not symbols:
                logger.warning("⚠️ No symbols found")
                return False
            
            self.discovered_symbols = []
            
            for symbol in symbols:
                try:
                    # Get symbol info
                    symbol_info = mt5.symbol_info(symbol.name)
                    
                    if symbol_info and symbol_info.visible:
                        symbol_data = {
                            "name": symbol.name,
                            "description": getattr(symbol, 'description', ''),
                            "digits": symbol_info.digits,
                            "point": symbol_info.point,
                            "volume_min": symbol_info.volume_min,
                            "volume_max": symbol_info.volume_max,
                            "volume_step": symbol_info.volume_step,
                            "volume_limit": symbol_info.volume_limit,
                            "margin_rate": getattr(symbol_info, 'margin_rate', 1.0),
                            "swap_long": symbol_info.swap_long,
                            "swap_short": symbol_info.swap_short,
                            "contract_size": symbol_info.contract_size,
                            "trade_mode": symbol_info.trade_mode,
                            "currency_base": symbol_info.currency_base,
                            "currency_profit": symbol_info.currency_profit,
                            "currency_margin": symbol_info.currency_margin,
                            "time": symbol_info.time,
                            "bid": symbol_info.bid,
                            "ask": symbol_info.ask,
                            "last": symbol_info.last,
                            "spread": symbol_info.spread
                        }
                        
                        self.discovered_symbols.append(symbol_data)
                        
                except Exception as e:
                    logger.debug(f"⚠️ Error processing symbol {symbol.name}: {e}")
                    continue
            
            logger.info(f"✅ Discovered {len(self.discovered_symbols)} tradable symbols")
            return True
            
        except Exception as e:
            logger.error(f"❌ Symbol discovery error: {e}")
            return False
    
    def start_socket_server(self) -> bool:
        """Start socket server to receive symbol discovery requests"""
        try:
            self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_server.bind((self.server_host, self.server_port))
            self.socket_server.listen(5)
            
            self.running = True
            
            logger.info(f"🔗 Socket server started on {self.server_host}:{self.server_port}")
            
            # Start server thread
            server_thread = threading.Thread(target=self._handle_connections, daemon=True)
            server_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Socket server start error: {e}")
            return False
    
    def _handle_connections(self):
        """Handle incoming socket connections"""
        while self.running:
            try:
                client_socket, address = self.socket_server.accept()
                logger.debug(f"🔗 Connection from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Connection handling error: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple):
        """Handle individual client requests"""
        try:
            # Receive request
            data = client_socket.recv(4096)
            if not data:
                return
            
            request = json.loads(data.decode('utf-8'))
            logger.debug(f"📩 Request from {address}: {request.get('action', 'unknown')}")
            
            # Process request
            response = self._process_request(request)
            
            # Send response
            response_data = json.dumps(response).encode('utf-8')
            client_socket.send(response_data)
            
        except Exception as e:
            logger.error(f"❌ Client handling error: {e}")
            
            # Send error response
            try:
                error_response = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                client_socket.send(json.dumps(error_response).encode('utf-8'))
            except:
                pass
        
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _process_request(self, request: Dict) -> Dict:
        """Process symbol discovery requests"""
        try:
            action = request.get("action", "")
            
            if action == "discover_symbols":
                return self._handle_symbol_discovery_request(request)
            elif action == "validate_symbol":
                return self._handle_symbol_validation_request(request)
            elif action == "get_symbol_info":
                return self._handle_symbol_info_request(request)
            elif action == "refresh_symbols":
                return self._handle_refresh_symbols_request(request)
            elif action == "ping":
                return {"success": True, "message": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request processing error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _handle_symbol_discovery_request(self, request: Dict) -> Dict:
        """Handle symbol discovery request"""
        try:
            user_id = request.get("user_id")
            
            if not user_id:
                return {
                    "success": False,
                    "error": "Missing user_id in request"
                }
            
            if not self.mt5_initialized:
                return {
                    "success": False,
                    "error": "MT5 not initialized"
                }
            
            # Refresh symbols if needed
            if not self.discovered_symbols:
                self._discover_all_symbols()
            
            response = {
                "success": True,
                "user_id": user_id,
                "broker_name": self.broker_info.get("name", "Unknown"),
                "broker_server": self.broker_info.get("server", "Unknown"),
                "symbols_count": len(self.discovered_symbols),
                "symbols": self.discovered_symbols,
                "discovery_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ Symbol discovery completed for user {user_id}: {len(self.discovered_symbols)} symbols")
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Symbol discovery error: {str(e)}"
            }
    
    def _handle_symbol_validation_request(self, request: Dict) -> Dict:
        """Handle symbol validation request"""
        try:
            symbol_name = request.get("symbol")
            
            if not symbol_name:
                return {
                    "success": False,
                    "error": "Missing symbol in request"
                }
            
            if not self.mt5_initialized:
                return {
                    "success": False,
                    "error": "MT5 not initialized"
                }
            
            # Get symbol info from MT5
            symbol_info = mt5.symbol_info(symbol_name)
            
            if symbol_info:
                return {
                    "success": True,
                    "symbol": symbol_name,
                    "valid": True,
                    "tradable": symbol_info.trade_mode > 0,
                    "digits": symbol_info.digits,
                    "point": symbol_info.point,
                    "volume_min": symbol_info.volume_min,
                    "volume_max": symbol_info.volume_max
                }
            else:
                return {
                    "success": True,
                    "symbol": symbol_name,
                    "valid": False,
                    "error": "Symbol not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Symbol validation error: {str(e)}"
            }
    
    def _handle_symbol_info_request(self, request: Dict) -> Dict:
        """Handle symbol info request"""
        try:
            symbol_name = request.get("symbol")
            
            if not symbol_name:
                return {
                    "success": False,
                    "error": "Missing symbol in request"
                }
            
            # Find symbol in discovered symbols
            for symbol_data in self.discovered_symbols:
                if symbol_data["name"] == symbol_name:
                    return {
                        "success": True,
                        "symbol_info": symbol_data
                    }
            
            return {
                "success": False,
                "error": f"Symbol {symbol_name} not found in discovered symbols"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Symbol info error: {str(e)}"
            }
    
    def _handle_refresh_symbols_request(self, request: Dict) -> Dict:
        """Handle refresh symbols request"""
        try:
            if not self.mt5_initialized:
                return {
                    "success": False,
                    "error": "MT5 not initialized"
                }
            
            # Re-discover symbols
            success = self._discover_all_symbols()
            
            if success:
                return {
                    "success": True,
                    "symbols_count": len(self.discovered_symbols),
                    "refresh_timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Symbol refresh failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Symbol refresh error: {str(e)}"
            }
    
    def stop_server(self):
        """Stop the socket server"""
        try:
            self.running = False
            
            if self.socket_server:
                self.socket_server.close()
            
            logger.info("🛑 Socket server stopped")
            
        except Exception as e:
            logger.error(f"❌ Server stop error: {e}")
    
    def shutdown(self):
        """Shutdown the discovery agent"""
        try:
            self.stop_server()
            
            if self.mt5_initialized:
                mt5.shutdown()
                logger.info("🛑 MT5 shutdown")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BITTEN Bridge Symbol Discovery Agent")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5555, help="Server port")
    parser.add_argument("--login", type=int, help="MT5 login")
    parser.add_argument("--password", help="MT5 password")
    parser.add_argument("--server", help="MT5 server")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🌉 BITTEN Bridge Symbol Discovery Agent")
    print("=" * 50)
    
    # Create discovery agent
    discovery_agent = MT5SymbolDiscovery(args.host, args.port)
    
    # Initialize MT5
    if not discovery_agent.initialize_mt5(args.login, args.password, args.server):
        print("❌ Failed to initialize MT5")
        return
    
    # Start server
    if not discovery_agent.start_socket_server():
        print("❌ Failed to start socket server")
        return
    
    print(f"✅ Symbol discovery agent running on {args.host}:{args.port}")
    print("Press Ctrl+C to stop...")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        discovery_agent.shutdown()

if __name__ == "__main__":
    main()