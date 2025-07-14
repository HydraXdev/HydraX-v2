#!/usr/bin/env python3
"""
🧌 BRIDGE TROLL INTEGRATION UTILITIES
Helper functions for seamless integration with Enhanced Bridge Troll

USAGE EXAMPLES:
- Record trade execution: troll_record_fire(bridge_id, user_id, trade_data)
- Validate trade safety: troll_validate_fire(bridge_id, user_id, trade_data)
- Query user status: troll_get_user_info(telegram_id)
- Check bridge health: troll_check_bridge(bridge_id)
- Emergency controls: troll_emergency_stop(), troll_fireproof_toggle()
"""

import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from bridge_troll_enhanced import get_enhanced_bridge_troll, BridgeEvent, EventType, BridgeState, RiskTier

# Global configuration
TROLL_API_BASE = "http://localhost:8890/bridge_troll"
TROLL_TIMEOUT = 10

logger = logging.getLogger("TROLL_INTEGRATION")

class TrollIntegration:
    """Helper class for Bridge Troll integration"""
    
    def __init__(self):
        self.troll = get_enhanced_bridge_troll()
        self.api_base = TROLL_API_BASE
        
    def record_fire(self, bridge_id: str, telegram_id: int, trade_data: Dict) -> bool:
        """Record a fire (trade execution) event"""
        try:
            event = BridgeEvent(
                event_id=f"fire_{bridge_id}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.FIRE,
                bridge_id=bridge_id,
                user_id=trade_data.get("user_id"),
                account_id=trade_data.get("account_id"),
                telegram_id=telegram_id,
                symbol=trade_data.get("symbol"),
                lot_size=trade_data.get("lot_size"),
                entry_price=trade_data.get("entry_price"),
                sl=trade_data.get("sl"),
                tp=trade_data.get("tp"),
                balance=trade_data.get("balance"),
                equity=trade_data.get("equity"),
                error_message=None,
                metadata=trade_data.get("metadata", {})
            )
            
            self.troll.record_event(event)
            logger.info(f"🔥 Fire event recorded: {bridge_id} -> {trade_data.get('symbol')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record fire event: {e}")
            return False
            
    def record_init_sync(self, bridge_id: str, telegram_id: int, sync_data: Dict) -> bool:
        """Record an init_sync event"""
        try:
            event = BridgeEvent(
                event_id=f"sync_{bridge_id}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.INIT_SYNC,
                bridge_id=bridge_id,
                user_id=sync_data.get("user_id"),
                account_id=sync_data.get("account_id"),
                telegram_id=telegram_id,
                symbol=None,
                lot_size=None,
                entry_price=None,
                sl=None,
                tp=None,
                balance=sync_data.get("balance"),
                equity=sync_data.get("equity"),
                error_message=None,
                metadata=sync_data.get("metadata", {})
            )
            
            self.troll.record_event(event)
            logger.info(f"🔄 Init sync recorded: {bridge_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record sync event: {e}")
            return False
            
    def record_error(self, bridge_id: str, error_message: str, context: Dict = None) -> bool:
        """Record an error event"""
        try:
            event = BridgeEvent(
                event_id=f"error_{bridge_id}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.ERROR,
                bridge_id=bridge_id,
                user_id=context.get("user_id") if context else None,
                account_id=context.get("account_id") if context else None,
                telegram_id=context.get("telegram_id") if context else None,
                symbol=None,
                lot_size=None,
                entry_price=None,
                sl=None,
                tp=None,
                balance=None,
                equity=None,
                error_message=error_message,
                metadata=context or {}
            )
            
            self.troll.record_event(event)
            logger.error(f"💥 Error recorded: {bridge_id} - {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record error event: {e}")
            return False
            
    def validate_fire_safety(self, bridge_id: str, telegram_id: int, trade_data: Dict) -> Tuple[bool, str]:
        """Validate if fire request is safe to execute"""
        try:
            return self.troll.validate_fire_request(bridge_id, telegram_id, trade_data)
        except Exception as e:
            logger.error(f"❌ Fire validation error: {e}")
            return False, f"VALIDATION_ERROR: {e}"
            
    def get_bridge_status(self, bridge_id: str) -> Optional[Dict]:
        """Get comprehensive bridge status"""
        try:
            response = requests.get(f"{self.api_base}/status/{bridge_id}", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get bridge status: {e}")
            return None
            
    def get_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Get user bridge information"""
        try:
            response = requests.get(f"{self.api_base}/user/{telegram_id}", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get user info: {e}")
            return None
            
    def get_last_trade(self, bridge_id: str) -> Optional[Dict]:
        """Get last trade information"""
        try:
            response = requests.get(f"{self.api_base}/last_trade/{bridge_id}", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get last trade: {e}")
            return None
            
    def check_socket_health(self) -> Optional[Dict]:
        """Check health of all bridge sockets"""
        try:
            response = requests.get(f"{self.api_base}/check_socket_health", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to check socket health: {e}")
            return None
            
    def get_port_map(self) -> Optional[Dict]:
        """Get port assignment mapping"""
        try:
            response = requests.get(f"{self.api_base}/port_map", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get port map: {e}")
            return None
            
    def get_bridge_memory(self, bridge_id: str, limit: int = 50) -> Optional[List[Dict]]:
        """Get bridge event history"""
        try:
            response = requests.get(f"{self.api_base}/memory/{bridge_id}?limit={limit}", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get bridge memory: {e}")
            return None
            
    def emergency_stop(self) -> bool:
        """Activate emergency stop"""
        try:
            response = requests.post(f"{self.api_base}/emergency_stop", timeout=TROLL_TIMEOUT)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Failed to activate emergency stop: {e}")
            return False
            
    def toggle_fireproof_mode(self) -> Optional[bool]:
        """Toggle fireproof mode"""
        try:
            response = requests.post(f"{self.api_base}/fireproof_mode", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json().get("fireproof_mode")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to toggle fireproof mode: {e}")
            return None
            
    def get_troll_health(self) -> Optional[Dict]:
        """Get Bridge Troll health status"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=TROLL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get troll health: {e}")
            return None

# Global integration instance
TROLL_INTEGRATION = TrollIntegration()

# Convenience functions for easy import
def troll_record_fire(bridge_id: str, telegram_id: int, trade_data: Dict) -> bool:
    """Record a fire (trade execution) event"""
    return TROLL_INTEGRATION.record_fire(bridge_id, telegram_id, trade_data)

def troll_record_sync(bridge_id: str, telegram_id: int, sync_data: Dict) -> bool:
    """Record an init_sync event"""
    return TROLL_INTEGRATION.record_init_sync(bridge_id, telegram_id, sync_data)

def troll_record_error(bridge_id: str, error_message: str, context: Dict = None) -> bool:
    """Record an error event"""
    return TROLL_INTEGRATION.record_error(bridge_id, error_message, context)

def troll_validate_fire(bridge_id: str, telegram_id: int, trade_data: Dict) -> Tuple[bool, str]:
    """Validate if fire request is safe to execute"""
    return TROLL_INTEGRATION.validate_fire_safety(bridge_id, telegram_id, trade_data)

def troll_get_bridge_status(bridge_id: str) -> Optional[Dict]:
    """Get comprehensive bridge status"""
    return TROLL_INTEGRATION.get_bridge_status(bridge_id)

def troll_get_user_info(telegram_id: int) -> Optional[Dict]:
    """Get user bridge information"""
    return TROLL_INTEGRATION.get_user_info(telegram_id)

def troll_get_last_trade(bridge_id: str) -> Optional[Dict]:
    """Get last trade information"""
    return TROLL_INTEGRATION.get_last_trade(bridge_id)

def troll_check_sockets() -> Optional[Dict]:
    """Check health of all bridge sockets"""
    return TROLL_INTEGRATION.check_socket_health()

def troll_get_ports() -> Optional[Dict]:
    """Get port assignment mapping"""
    return TROLL_INTEGRATION.get_port_map()

def troll_get_memory(bridge_id: str, limit: int = 50) -> Optional[List[Dict]]:
    """Get bridge event history"""
    return TROLL_INTEGRATION.get_bridge_memory(bridge_id, limit)

def troll_emergency_stop() -> bool:
    """Activate emergency stop"""
    return TROLL_INTEGRATION.emergency_stop()

def troll_fireproof_toggle() -> Optional[bool]:
    """Toggle fireproof mode"""
    return TROLL_INTEGRATION.toggle_fireproof_mode()

def troll_health() -> Optional[Dict]:
    """Get Bridge Troll health status"""
    return TROLL_INTEGRATION.get_troll_health()

# Example usage functions
def example_trade_flow():
    """Example of complete trade flow with Bridge Troll integration"""
    print("🧌 Example: Complete Trade Flow with Bridge Troll")
    
    bridge_id = "bridge_001"
    telegram_id = 123456789
    
    # 1. Check bridge status
    bridge_status = troll_get_bridge_status(bridge_id)
    print(f"📊 Bridge Status: {bridge_status}")
    
    # 2. Validate fire request
    trade_data = {
        "symbol": "EURUSD",
        "lot_size": 0.01,
        "entry_price": 1.0850,
        "sl": 1.0800,
        "tp": 1.0900,
        "balance": 1000.0,
        "equity": 1000.0
    }
    
    is_safe, reason = troll_validate_fire(bridge_id, telegram_id, trade_data)
    print(f"🔒 Fire Validation: {is_safe} - {reason}")
    
    if is_safe:
        # 3. Record fire event
        success = troll_record_fire(bridge_id, telegram_id, trade_data)
        print(f"🔥 Fire Recorded: {success}")
        
        # 4. Check last trade
        last_trade = troll_get_last_trade(bridge_id)
        print(f"📈 Last Trade: {last_trade}")
    
    # 5. Get user info
    user_info = troll_get_user_info(telegram_id)
    print(f"👤 User Info: {user_info}")

def example_monitoring():
    """Example of monitoring functions"""
    print("🧌 Example: Bridge Monitoring")
    
    # Check all socket health
    socket_health = troll_check_sockets()
    print(f"🔌 Socket Health: {socket_health}")
    
    # Get port mapping
    port_map = troll_get_ports()
    print(f"🚪 Port Map: {port_map}")
    
    # Get Bridge Troll health
    troll_status = troll_health()
    print(f"🧌 Troll Health: {troll_status}")

if __name__ == "__main__":
    print("🧌 BRIDGE TROLL INTEGRATION UTILITIES")
    print("=" * 50)
    
    # Run examples
    example_trade_flow()
    print()
    example_monitoring()
    
    print("\n🔗 Available Functions:")
    print("  troll_record_fire(bridge_id, telegram_id, trade_data)")
    print("  troll_record_sync(bridge_id, telegram_id, sync_data)")
    print("  troll_record_error(bridge_id, error_message, context)")
    print("  troll_validate_fire(bridge_id, telegram_id, trade_data)")
    print("  troll_get_bridge_status(bridge_id)")
    print("  troll_get_user_info(telegram_id)")
    print("  troll_get_last_trade(bridge_id)")
    print("  troll_check_sockets()")
    print("  troll_get_ports()")
    print("  troll_get_memory(bridge_id, limit)")
    print("  troll_emergency_stop()")
    print("  troll_fireproof_toggle()")
    print("  troll_health()")