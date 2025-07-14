#!/usr/bin/env python3
"""
🔥 FIRE ROUTER SYMBOL INTEGRATION
Integrates multi-broker symbol translation with the existing BITTEN fire router

CAPABILITIES:
- Pre-execution symbol translation for all trade signals
- User-specific symbol mapping validation
- Integration with existing fire router architecture
- Error handling and trade rejection for unsupported symbols
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

# Import existing components
from bitten_core.bridge_symbol_integration import bridge_integration, translate_signal_for_user
from bitten_core.symbol_mapper import symbol_mapper

logger = logging.getLogger(__name__)

@dataclass
class FireRouterResult:
    """Fire router execution result with symbol translation info"""
    success: bool
    user_id: str
    original_signal: Dict
    translated_signal: Optional[Dict]
    execution_result: Optional[Dict]
    translation_info: Optional[Dict]
    error_message: Optional[str]
    timestamp: datetime

class EnhancedFireRouter:
    """
    🔥 ENHANCED FIRE ROUTER WITH SYMBOL TRANSLATION
    
    Extends the existing fire router with multi-broker symbol support
    """
    
    def __init__(self):
        self.execution_log_path = "/root/HydraX-v2/data/fire_router_executions.log"
        self.supported_brokers = [
            "MetaQuotes", "ICMarkets", "Pepperstone", "XM", "FXCM", 
            "OANDA", "IG", "Admiral", "FxPro", "AvaTrade"
        ]
        
        logger.info("🔥 Enhanced Fire Router initialized with symbol translation")
    
    def execute_trade_with_translation(self, user_id: str, signal: Dict, 
                                     user_profile: Optional[Dict] = None) -> FireRouterResult:
        """
        Execute a trade with automatic symbol translation
        
        Args:
            user_id: User identifier
            signal: Trading signal dictionary
            user_profile: User profile information
            
        Returns:
            FireRouterResult: Execution result with translation info
        """
        timestamp = datetime.now(timezone.utc)
        
        try:
            logger.info(f"🔥 Executing trade for user {user_id}: {signal.get('pair', 'UNKNOWN')}")
            
            # Step 1: Validate user has symbol mapping
            connection_status = bridge_integration.get_user_connection_status(user_id)
            
            if not connection_status.get("mapping_ready", False):
                error_msg = f"Symbol mapping not ready for user {user_id}"
                logger.error(f"❌ {error_msg}")
                
                return FireRouterResult(
                    success=False,
                    user_id=user_id,
                    original_signal=signal,
                    translated_signal=None,
                    execution_result=None,
                    translation_info=connection_status,
                    error_message=error_msg,
                    timestamp=timestamp
                )
            
            # Step 2: Translate signal for user's broker
            translation_success, translated_signal = translate_signal_for_user(user_id, signal)
            
            if not translation_success:
                error_msg = f"Symbol translation failed: {translated_signal.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                
                return FireRouterResult(
                    success=False,
                    user_id=user_id,
                    original_signal=signal,
                    translated_signal=None,
                    execution_result=None,
                    translation_info=translated_signal,
                    error_message=error_msg,
                    timestamp=timestamp
                )
            
            logger.info(f"✅ Symbol translated: {signal.get('pair')} → {translated_signal.get('symbol')}")
            
            # Step 3: Validate translated signal
            validation_result = self._validate_translated_signal(translated_signal, user_profile)
            
            if not validation_result["valid"]:
                error_msg = f"Signal validation failed: {validation_result['error']}"
                logger.error(f"❌ {error_msg}")
                
                return FireRouterResult(
                    success=False,
                    user_id=user_id,
                    original_signal=signal,
                    translated_signal=translated_signal,
                    execution_result=None,
                    translation_info=validation_result,
                    error_message=error_msg,
                    timestamp=timestamp
                )
            
            # Step 4: Execute trade with translated signal
            execution_result = self._execute_translated_trade(user_id, translated_signal, user_profile)
            
            # Step 5: Create result
            result = FireRouterResult(
                success=execution_result.get("success", False),
                user_id=user_id,
                original_signal=signal,
                translated_signal=translated_signal,
                execution_result=execution_result,
                translation_info=translated_signal.get("translation_info", {}),
                error_message=execution_result.get("error") if not execution_result.get("success") else None,
                timestamp=timestamp
            )
            
            # Step 6: Log execution
            self._log_execution(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Trade execution error for user {user_id}: {e}")
            
            error_result = FireRouterResult(
                success=False,
                user_id=user_id,
                original_signal=signal,
                translated_signal=None,
                execution_result=None,
                translation_info=None,
                error_message=f"Execution error: {str(e)}",
                timestamp=timestamp
            )
            
            self._log_execution(error_result)
            return error_result
    
    def _validate_translated_signal(self, translated_signal: Dict, 
                                  user_profile: Optional[Dict] = None) -> Dict:
        """
        Validate the translated signal before execution
        
        Args:
            translated_signal: Translated signal dictionary
            user_profile: User profile for additional validation
            
        Returns:
            Dict: Validation result
        """
        try:
            # Basic required fields
            required_fields = ["symbol", "direction", "lot_size"]
            
            for field in required_fields:
                if field not in translated_signal:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Validate symbol info if available
            symbol_info = translated_signal.get("symbol_info", {})
            
            if symbol_info:
                lot_size = translated_signal.get("lot_size", 0)
                min_lot = symbol_info.get("min_lot", 0.01)
                max_lot = symbol_info.get("max_lot", 100.0)
                
                if lot_size < min_lot:
                    return {
                        "valid": False,
                        "error": f"Lot size {lot_size} below minimum {min_lot}"
                    }
                
                if lot_size > max_lot:
                    return {
                        "valid": False,
                        "error": f"Lot size {lot_size} above maximum {max_lot}"
                    }
            
            # Validate direction
            direction = translated_signal.get("direction", "").upper()
            if direction not in ["BUY", "SELL"]:
                return {
                    "valid": False,
                    "error": f"Invalid direction: {direction}"
                }
            
            # User profile validation (if provided)
            if user_profile:
                user_tier = user_profile.get("tier", "").lower()
                
                # Tier-specific validations
                if user_tier == "press_pass":
                    max_lot_tier = 0.01
                    if translated_signal.get("lot_size", 0) > max_lot_tier:
                        return {
                            "valid": False,
                            "error": f"Lot size exceeds tier limit: {max_lot_tier}"
                        }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def _execute_translated_trade(self, user_id: str, translated_signal: Dict, 
                                user_profile: Optional[Dict] = None) -> Dict:
        """
        Execute the translated trade signal
        
        Args:
            user_id: User identifier
            translated_signal: Translated signal dictionary
            user_profile: User profile information
            
        Returns:
            Dict: Execution result
        """
        try:
            # Get user's bridge connection info
            connection_status = bridge_integration.get_user_connection_status(user_id)
            bridge_id = connection_status.get("bridge_id")
            
            if not bridge_id:
                return {
                    "success": False,
                    "error": "No bridge connection found for user"
                }
            
            # Prepare trade payload for bridge
            trade_payload = {
                "action": "execute_trade",
                "user_id": user_id,
                "symbol": translated_signal["symbol"],
                "direction": translated_signal["direction"],
                "volume": translated_signal["lot_size"],
                "stop_loss": translated_signal.get("sl", 0),
                "take_profit": translated_signal.get("tp", 0),
                "comment": f"BITTEN_{translated_signal.get('translation_info', {}).get('original_pair', 'SIGNAL')}",
                "magic": 12345,  # BITTEN magic number
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add symbol-specific adjustments
            symbol_info = translated_signal.get("symbol_info", {})
            if symbol_info:
                # Adjust SL/TP based on symbol digits
                digits = symbol_info.get("digits", 5)
                point = symbol_info.get("point", 0.00001)
                
                if "sl_pips" in translated_signal:
                    sl_pips = translated_signal["sl_pips"]
                    entry_price = translated_signal.get("entry_price", 0)
                    
                    if translated_signal["direction"].upper() == "BUY":
                        trade_payload["stop_loss"] = entry_price - (sl_pips * point * 10)
                    else:
                        trade_payload["stop_loss"] = entry_price + (sl_pips * point * 10)
                
                if "tp_pips" in translated_signal:
                    tp_pips = translated_signal["tp_pips"]
                    entry_price = translated_signal.get("entry_price", 0)
                    
                    if translated_signal["direction"].upper() == "BUY":
                        trade_payload["take_profit"] = entry_price + (tp_pips * point * 10)
                    else:
                        trade_payload["take_profit"] = entry_price - (tp_pips * point * 10)
            
            # Execute via existing bridge system
            execution_result = self._send_to_bridge(bridge_id, trade_payload)
            
            if execution_result.get("success"):
                logger.info(f"✅ Trade executed successfully for user {user_id}")
                return {
                    "success": True,
                    "bridge_id": bridge_id,
                    "trade_payload": trade_payload,
                    "bridge_response": execution_result,
                    "execution_time": datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.error(f"❌ Bridge execution failed: {execution_result.get('error')}")
                return {
                    "success": False,
                    "error": execution_result.get("error", "Bridge execution failed"),
                    "bridge_response": execution_result
                }
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
    
    def _send_to_bridge(self, bridge_id: str, payload: Dict) -> Dict:
        """
        Send trade payload to bridge (integration with existing bridge system)
        
        Args:
            bridge_id: Bridge identifier
            payload: Trade payload
            
        Returns:
            Dict: Bridge response
        """
        try:
            # Import existing fire router if available
            try:
                from bitten_core.fire_router import BridgeConnector
                
                # Use existing bridge connector
                connector = BridgeConnector()
                result = connector.send_with_retry(payload)
                
                return result
                
            except ImportError:
                # Fallback to mock execution for testing
                logger.warning("⚠️ Fire router not available, using mock execution")
                
                return {
                    "success": True,
                    "message": "Mock execution successful",
                    "trade_id": f"MOCK_{int(datetime.now().timestamp())}",
                    "bridge_id": bridge_id
                }
                
        except Exception as e:
            logger.error(f"❌ Bridge send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_execution(self, result: FireRouterResult):
        """Log execution result"""
        try:
            log_entry = {
                "timestamp": result.timestamp.isoformat(),
                "user_id": result.user_id,
                "success": result.success,
                "original_pair": result.original_signal.get("pair", "UNKNOWN"),
                "translated_pair": result.translated_signal.get("symbol") if result.translated_signal else None,
                "fallback_used": result.translation_info.get("fallback_used", False) if result.translation_info else False,
                "error_message": result.error_message,
                "execution_result": result.execution_result.get("success") if result.execution_result else False
            }
            
            with open(self.execution_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Failed to log execution: {e}")
    
    def get_execution_stats(self, hours_back: int = 24) -> Dict:
        """Get execution statistics"""
        try:
            from datetime import timedelta
            
            stats = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "translation_failures": 0,
                "execution_failures": 0,
                "fallback_translations": 0,
                "popular_pairs": {},
                "user_activity": {}
            }
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            if not os.path.exists(self.execution_log_path):
                return stats
            
            with open(self.execution_log_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time >= cutoff_time:
                            stats["total_executions"] += 1
                            
                            if entry["success"]:
                                stats["successful_executions"] += 1
                            else:
                                stats["failed_executions"] += 1
                                
                                if not entry.get("translated_pair"):
                                    stats["translation_failures"] += 1
                                else:
                                    stats["execution_failures"] += 1
                            
                            if entry.get("fallback_used"):
                                stats["fallback_translations"] += 1
                            
                            # Track popular pairs
                            pair = entry["original_pair"]
                            stats["popular_pairs"][pair] = stats["popular_pairs"].get(pair, 0) + 1
                            
                            # Track user activity
                            user_id = entry["user_id"]
                            stats["user_activity"][user_id] = stats["user_activity"].get(user_id, 0) + 1
                            
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get execution stats: {e}")
            return {"error": str(e)}

# Global instance
enhanced_fire_router = EnhancedFireRouter()

# Convenience functions
def execute_trade_with_translation(user_id: str, signal: Dict, 
                                 user_profile: Optional[Dict] = None) -> FireRouterResult:
    """Convenience function for trade execution with translation"""
    return enhanced_fire_router.execute_trade_with_translation(user_id, signal, user_profile)

def get_execution_stats(hours_back: int = 24) -> Dict:
    """Convenience function for execution statistics"""
    return enhanced_fire_router.get_execution_stats(hours_back)

# Integration wrapper for existing fire router
class SymbolAwareFireRouter:
    """
    Wrapper class that adds symbol translation to existing fire router calls
    """
    
    def __init__(self, original_fire_router=None):
        self.original_router = original_fire_router
        self.enhanced_router = enhanced_fire_router
    
    def execute_trade(self, user_id: str, signal: Dict, **kwargs) -> Dict:
        """Execute trade with symbol translation"""
        user_profile = kwargs.get("user_profile")
        
        result = self.enhanced_router.execute_trade_with_translation(
            user_id, signal, user_profile
        )
        
        # Convert to legacy format for compatibility
        return {
            "success": result.success,
            "user_id": result.user_id,
            "error": result.error_message,
            "execution_result": result.execution_result,
            "translation_info": result.translation_info
        }

# Test function
def test_fire_router_integration():
    """Test the fire router symbol integration"""
    print("🔥 Testing Fire Router Symbol Integration...")
    
    # Mock user setup
    user_id = "test_user_123"
    
    # Add mock symbol mapping
    symbol_mapper.user_maps[user_id] = {
        "XAUUSD": "XAU/USD.r",
        "EURUSD": "EURUSD.r"
    }
    
    symbol_mapper.user_symbol_info[user_id] = {
        "XAU/USD.r": {
            "digits": 2,
            "point": 0.01,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01
        }
    }
    
    # Mock connection status
    bridge_integration.active_connections[user_id] = {
        "bridge_id": "bridge_001",
        "mapping_ready": True
    }
    
    # Test signal
    test_signal = {
        "pair": "XAUUSD",
        "direction": "BUY",
        "lot_size": 0.01,
        "sl": 1950.0,
        "tp": 1970.0,
        "risk": 2.0
    }
    
    # Test user profile
    test_profile = {
        "tier": "fang",
        "balance": 1000.0
    }
    
    # Execute trade
    result = execute_trade_with_translation(user_id, test_signal, test_profile)
    
    print(f"🎯 Execution Result:")
    print(f"   Success: {result.success}")
    print(f"   Original Pair: {result.original_signal.get('pair')}")
    
    if result.translated_signal:
        print(f"   Translated Pair: {result.translated_signal.get('symbol')}")
    
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test stats
    stats = get_execution_stats(1)
    print(f"📊 Execution Stats: {stats['total_executions']} total executions")
    
    print("🎯 Fire router integration testing complete!")

if __name__ == "__main__":
    import os
    test_fire_router_integration()