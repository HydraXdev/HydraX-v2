#!/usr/bin/env python3
"""
🌉 BRIDGE SYMBOL INTEGRATION FOR BITTEN
Integrates the symbol mapper with MT5 bridge agents and HydraBridge EA

CAPABILITIES:
- Auto-discovery of user symbols during bridge initialization
- Real-time symbol translation during trade execution
- Integration with existing fire router and bridge systems
- Error handling and fallback mechanisms
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import socket
import time

# Import symbol mapper
from bitten_core.symbol_mapper import symbol_mapper, TranslationResult

logger = logging.getLogger(__name__)

class BridgeSymbolIntegration:
    """
    🌉 BRIDGE SYMBOL INTEGRATION
    
    Handles symbol discovery and translation for MT5 bridge connections
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
        self.symbol_discovery_timeout = 30  # seconds
        self.bridge_ports = {
            "bridge_001": 5555,
            "bridge_002": 5556, 
            "bridge_003": 5557,
            "bridge_004": 5558,
            "bridge_005": 5559
        }
        
        logger.info("🌉 Bridge Symbol Integration initialized")
    
    def discover_user_symbols(self, user_id: str, bridge_id: str, 
                            host: str = "127.0.0.1") -> Tuple[bool, Dict]:
        """
        Discover and initialize symbols for a user's MT5 terminal
        
        Args:
            user_id: User identifier
            bridge_id: Bridge identifier (e.g., "bridge_001")
            host: Bridge host address
            
        Returns:
            Tuple[bool, Dict]: (success, result_data)
        """
        try:
            logger.info(f"🔍 Discovering symbols for user {user_id} on {bridge_id}")
            
            # Get bridge port
            port = self.bridge_ports.get(bridge_id, 5555)
            
            # Send symbol discovery request to bridge
            discovery_request = {
                "action": "discover_symbols",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Connect to bridge and request symbols
            symbols_data = self._send_bridge_request(host, port, discovery_request)
            
            if not symbols_data or not symbols_data.get("success"):
                error_msg = symbols_data.get("error", "Unknown bridge error") if symbols_data else "Bridge connection failed"
                logger.error(f"❌ Symbol discovery failed for {user_id}: {error_msg}")
                return False, {"error": error_msg}
            
            # Extract symbol information
            symbols_list = symbols_data.get("symbols", [])
            broker_name = symbols_data.get("broker_name", "Unknown")
            
            if not symbols_list:
                logger.warning(f"⚠️ No symbols received for user {user_id}")
                return False, {"error": "No symbols received from bridge"}
            
            logger.info(f"📊 Received {len(symbols_list)} symbols for user {user_id}")
            
            # Initialize symbol mapping
            mapping_success = symbol_mapper.initialize_user_symbols(
                user_id, symbols_list, broker_name
            )
            
            if mapping_success:
                # Store connection info
                self.active_connections[user_id] = {
                    "bridge_id": bridge_id,
                    "host": host,
                    "port": port,
                    "broker_name": broker_name,
                    "symbols_count": len(symbols_list),
                    "last_discovery": datetime.now(timezone.utc),
                    "mapping_ready": True
                }
                
                # Get mapping status
                mapping_status = symbol_mapper.get_user_mapping_status(user_id)
                
                result = {
                    "user_id": user_id,
                    "bridge_id": bridge_id,
                    "broker_name": broker_name,
                    "total_symbols": len(symbols_list),
                    "pairs_mapped": mapping_status["pairs_mapped"],
                    "mapping_ready": True,
                    "discovery_time": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"✅ Symbol mapping completed for user {user_id}: {mapping_status['pairs_mapped']} pairs")
                return True, result
            else:
                logger.error(f"❌ Symbol mapping initialization failed for user {user_id}")
                return False, {"error": "Symbol mapping initialization failed"}
                
        except Exception as e:
            logger.error(f"❌ Symbol discovery error for user {user_id}: {e}")
            return False, {"error": str(e)}
    
    def translate_signal_for_user(self, user_id: str, signal: Dict) -> Tuple[bool, Dict]:
        """
        Translate a trading signal for a specific user's broker
        
        Args:
            user_id: User identifier
            signal: Trading signal dictionary
            
        Returns:
            Tuple[bool, Dict]: (success, translated_signal)
        """
        try:
            base_pair = signal.get("pair", signal.get("symbol", ""))
            
            if not base_pair:
                return False, {"error": "No pair/symbol found in signal"}
            
            logger.debug(f"🔄 Translating {base_pair} for user {user_id}")
            
            # Translate symbol
            translation_result = symbol_mapper.translate_symbol(user_id, base_pair)
            
            if not translation_result.success:
                logger.warning(f"⚠️ Symbol translation failed: {translation_result.error_message}")
                return False, {
                    "error": translation_result.error_message,
                    "base_pair": base_pair,
                    "user_id": user_id
                }
            
            # Create translated signal
            translated_signal = signal.copy()
            translated_signal["symbol"] = translation_result.translated_pair
            translated_signal["pair"] = translation_result.translated_pair
            
            # Add symbol-specific properties if available
            if translation_result.symbol_info:
                symbol_info = translation_result.symbol_info
                
                # Adjust lot size based on symbol constraints
                if "lot_size" in translated_signal or "volume" in translated_signal:
                    requested_lot = translated_signal.get("lot_size", translated_signal.get("volume", 0.01))
                    min_lot = symbol_info.get("volume_min", 0.01)
                    max_lot = symbol_info.get("volume_max", 100.0)
                    lot_step = symbol_info.get("volume_step", 0.01)
                    
                    # Adjust lot size to symbol constraints
                    adjusted_lot = max(min_lot, min(requested_lot, max_lot))
                    
                    # Round to lot step
                    if lot_step > 0:
                        adjusted_lot = round(adjusted_lot / lot_step) * lot_step
                    
                    translated_signal["lot_size"] = adjusted_lot
                    translated_signal["volume"] = adjusted_lot
                
                # Add symbol properties for validation
                translated_signal["symbol_info"] = {
                    "digits": symbol_info.get("digits", 5),
                    "point": symbol_info.get("point", 0.00001),
                    "min_lot": symbol_info.get("volume_min", 0.01),
                    "max_lot": symbol_info.get("volume_max", 100.0),
                    "lot_step": symbol_info.get("volume_step", 0.01)
                }
            
            # Add translation metadata
            translated_signal["translation_info"] = {
                "original_pair": base_pair,
                "translated_pair": translation_result.translated_pair,
                "fallback_used": translation_result.fallback_used,
                "translation_timestamp": translation_result.timestamp.isoformat()
            }
            
            logger.debug(f"✅ Translation successful: {base_pair} → {translation_result.translated_pair}")
            
            return True, translated_signal
            
        except Exception as e:
            logger.error(f"❌ Signal translation error for user {user_id}: {e}")
            return False, {"error": str(e)}
    
    def _send_bridge_request(self, host: str, port: int, request: Dict, 
                           timeout: int = 30) -> Optional[Dict]:
        """
        Send request to bridge and get response
        
        Args:
            host: Bridge host
            port: Bridge port
            request: Request dictionary
            timeout: Request timeout
            
        Returns:
            Optional[Dict]: Bridge response or None
        """
        sock = None
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            # Send request
            message = json.dumps(request).encode('utf-8')
            sock.send(message)
            
            # Receive response
            response_data = b""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    
                    # Try to parse JSON to see if we have complete response
                    try:
                        response = json.loads(response_data.decode('utf-8'))
                        return response
                    except json.JSONDecodeError:
                        # Continue receiving
                        continue
                        
                except socket.timeout:
                    break
            
            # Final parse attempt
            if response_data:
                try:
                    return json.loads(response_data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse bridge response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Bridge request failed: {e}")
            return None
            
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def refresh_user_symbols(self, user_id: str) -> Tuple[bool, Dict]:
        """
        Refresh symbol mapping for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple[bool, Dict]: (success, result)
        """
        try:
            # Check if user has active connection
            if user_id not in self.active_connections:
                return False, {"error": f"No active connection found for user {user_id}"}
            
            connection_info = self.active_connections[user_id]
            
            # Re-discover symbols
            return self.discover_user_symbols(
                user_id,
                connection_info["bridge_id"],
                connection_info["host"]
            )
            
        except Exception as e:
            logger.error(f"❌ Symbol refresh failed for user {user_id}: {e}")
            return False, {"error": str(e)}
    
    def get_user_connection_status(self, user_id: str) -> Dict:
        """Get connection and mapping status for a user"""
        try:
            connection_info = self.active_connections.get(user_id, {})
            mapping_status = symbol_mapper.get_user_mapping_status(user_id)
            
            return {
                "user_id": user_id,
                "connection_active": user_id in self.active_connections,
                "bridge_id": connection_info.get("bridge_id"),
                "broker_name": connection_info.get("broker_name"),
                "mapping_ready": connection_info.get("mapping_ready", False),
                "pairs_mapped": mapping_status.get("pairs_mapped", 0),
                "total_symbols": connection_info.get("symbols_count", 0),
                "last_discovery": connection_info.get("last_discovery", {}).isoformat() if connection_info.get("last_discovery") else None
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "connection_active": False,
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        try:
            total_users = len(self.active_connections)
            ready_users = sum(1 for conn in self.active_connections.values() if conn.get("mapping_ready", False))
            
            # Get translation stats
            translation_stats = symbol_mapper.get_translation_stats(24)
            
            return {
                "total_connected_users": total_users,
                "users_with_mapping": ready_users,
                "mapping_ready_percentage": (ready_users / total_users * 100) if total_users > 0 else 0,
                "active_bridges": list(set(conn["bridge_id"] for conn in self.active_connections.values())),
                "translation_stats_24h": translation_stats,
                "system_status": "OPERATIONAL" if ready_users > 0 else "INITIALIZING"
            }
            
        except Exception as e:
            return {
                "system_status": "ERROR",
                "error": str(e)
            }

# Global instance
bridge_integration = BridgeSymbolIntegration()

# Convenience functions
def discover_user_symbols(user_id: str, bridge_id: str, host: str = "127.0.0.1") -> Tuple[bool, Dict]:
    """Convenience function for symbol discovery"""
    return bridge_integration.discover_user_symbols(user_id, bridge_id, host)

def translate_signal_for_user(user_id: str, signal: Dict) -> Tuple[bool, Dict]:
    """Convenience function for signal translation"""
    return bridge_integration.translate_signal_for_user(user_id, signal)

def get_user_connection_status(user_id: str) -> Dict:
    """Convenience function for connection status"""
    return bridge_integration.get_user_connection_status(user_id)

def get_system_status() -> Dict:
    """Convenience function for system status"""
    return bridge_integration.get_system_status()

# Test function
def test_bridge_integration():
    """Test the bridge symbol integration"""
    print("🌉 Testing Bridge Symbol Integration...")
    
    # Test signal translation with mock data
    test_signal = {
        "pair": "XAUUSD",
        "direction": "BUY",
        "lot_size": 0.01,
        "sl": 250,
        "tp": 500,
        "risk": 2.0
    }
    
    # Mock user mapping for testing
    symbol_mapper.user_maps["test_user"] = {
        "XAUUSD": "XAU/USD.r",
        "EURUSD": "EURUSD.r"
    }
    
    symbol_mapper.user_symbol_info["test_user"] = {
        "XAU/USD.r": {
            "digits": 2,
            "point": 0.01,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01
        }
    }
    
    # Test signal translation
    success, translated_signal = translate_signal_for_user("test_user", test_signal)
    
    if success:
        print(f"✅ Signal translation successful:")
        print(f"   Original: {test_signal['pair']}")
        print(f"   Translated: {translated_signal['symbol']}")
        print(f"   Lot size: {translated_signal['lot_size']}")
    else:
        print(f"❌ Signal translation failed: {translated_signal.get('error')}")
    
    # Test connection status
    status = get_user_connection_status("test_user")
    print(f"📊 Connection status: {status}")
    
    # Test system status
    system_status = get_system_status()
    print(f"🏥 System status: {system_status['system_status']}")
    
    print("🎯 Bridge integration testing complete!")

if __name__ == "__main__":
    test_bridge_integration()