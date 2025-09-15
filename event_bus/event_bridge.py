#!/usr/bin/env python3
"""
BITTEN Event Bridge - Integration with Existing System
Hooks into existing components to publish events to the new event bus
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from event_bus import EventBusClient, EventType

logger = logging.getLogger('EventBridge')


class EventBridge:
    """Bridge between existing BITTEN system and new event bus"""
    
    def __init__(self, push_port: int = 5571):
        self.client = EventBusClient(push_port)
        self.enabled = True
        
    def publish_signal_generated(self, signal_data: Dict[str, Any], source: str = "elite_guard"):
        """Publish signal generation event"""
        if not self.enabled:
            return
            
        try:
            # Extract signal information
            data = {
                "signal_id": signal_data.get("signal_id"),
                "symbol": signal_data.get("symbol"),
                "direction": signal_data.get("direction"),
                "confidence": signal_data.get("confidence"),
                "pattern_type": signal_data.get("pattern_type"),
                "entry_price": signal_data.get("entry_price"),
                "stop_pips": signal_data.get("stop_pips"),
                "target_pips": signal_data.get("target_pips"),
                "expires_at": signal_data.get("expires_at")
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.client.publish(
                event_type=EventType.SIGNAL_GENERATED.value,
                source=source,
                data=data,
                correlation_id=signal_data.get("signal_id")
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish signal_generated event: {e}")
    
    def publish_fire_command(self, fire_data: Dict[str, Any], user_id: str, source: str = "webapp"):
        """Publish fire command event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "fire_id": fire_data.get("fire_id"),
                "signal_id": fire_data.get("signal_id"),
                "user_id": user_id,
                "symbol": fire_data.get("symbol"),
                "direction": fire_data.get("direction"),
                "lot_size": fire_data.get("lot_size") or fire_data.get("volume"),
                "sl_price": fire_data.get("sl_price") or fire_data.get("sl"),
                "tp_price": fire_data.get("tp_price") or fire_data.get("tp"),
                "execution_mode": fire_data.get("execution_mode", "MANUAL")
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.client.publish(
                event_type=EventType.FIRE_COMMAND.value,
                source=source,
                data=data,
                user_id=user_id,
                correlation_id=fire_data.get("fire_id")
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish fire_command event: {e}")
    
    def publish_trade_executed(self, trade_data: Dict[str, Any], source: str = "mt5_adapter"):
        """Publish trade execution event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "fire_id": trade_data.get("fire_id"),
                "ticket": trade_data.get("ticket"),
                "symbol": trade_data.get("symbol"),
                "direction": trade_data.get("direction"),
                "volume": trade_data.get("volume") or trade_data.get("lot_size"),
                "open_price": trade_data.get("open_price") or trade_data.get("price"),
                "sl_price": trade_data.get("sl_price"),
                "tp_price": trade_data.get("tp_price"),
                "execution_time": trade_data.get("execution_time", time.time())
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.client.publish(
                event_type=EventType.TRADE_EXECUTED.value,
                source=source,
                data=data,
                correlation_id=trade_data.get("fire_id")
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish trade_executed event: {e}")
    
    def publish_balance_update(self, balance_data: Dict[str, Any], user_id: str, source: str = "mt5_adapter"):
        """Publish balance update event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "user_id": user_id,
                "account_number": balance_data.get("account_number") or balance_data.get("login"),
                "balance": balance_data.get("balance"),
                "equity": balance_data.get("equity"),
                "margin": balance_data.get("margin"),
                "free_margin": balance_data.get("free_margin")
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.client.publish(
                event_type=EventType.BALANCE_UPDATE.value,
                source=source,
                data=data,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish balance_update event: {e}")
    
    def publish_system_health(self, component: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Publish system health event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "component": component,
                "status": status
            }
            
            if details:
                data.update(details)
            
            self.client.publish(
                event_type=EventType.SYSTEM_HEALTH.value,
                source=component,
                data=data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish system_health event: {e}")
    
    def publish_user_action(self, user_id: str, action: str, details: Optional[Dict[str, Any]] = None, 
                           source: str = "webapp"):
        """Publish user action event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "user_id": user_id,
                "action": action
            }
            
            if details:
                data["details"] = details
            
            self.client.publish(
                event_type=EventType.USER_ACTION.value,
                source=source,
                data=data,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish user_action event: {e}")
    
    def publish_market_data(self, symbol: str, bid: float, ask: float, 
                           volume: Optional[int] = None, source: str = "mt5_feed"):
        """Publish market data event"""
        if not self.enabled:
            return
            
        try:
            data = {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "timestamp": time.time()
            }
            
            if volume is not None:
                data["volume"] = volume
            
            self.client.publish(
                event_type=EventType.MARKET_DATA.value,
                source=source,
                data=data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish market_data event: {e}")
    
    def disable(self):
        """Disable event publishing (for testing or debugging)"""
        self.enabled = False
        logger.info("⚠️ Event Bridge disabled")
    
    def enable(self):
        """Enable event publishing"""
        self.enabled = True
        logger.info("✅ Event Bridge enabled")
    
    def close(self):
        """Close the event bridge"""
        if self.client:
            self.client.close()


# Global event bridge instance
event_bridge = EventBridge()


# Convenience functions for easy integration
def signal_generated(signal_data: Dict[str, Any], source: str = "elite_guard"):
    """Convenience function to publish signal generation"""
    event_bridge.publish_signal_generated(signal_data, source)


def fire_command(fire_data: Dict[str, Any], user_id: str, source: str = "webapp"):
    """Convenience function to publish fire command"""
    event_bridge.publish_fire_command(fire_data, user_id, source)


def trade_executed(trade_data: Dict[str, Any], source: str = "mt5_adapter"):
    """Convenience function to publish trade execution"""
    event_bridge.publish_trade_executed(trade_data, source)


def balance_update(balance_data: Dict[str, Any], user_id: str, source: str = "mt5_adapter"):
    """Convenience function to publish balance update"""
    event_bridge.publish_balance_update(balance_data, user_id, source)


def system_health(component: str, status: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to publish system health"""
    event_bridge.publish_system_health(component, status, details)


def user_action(user_id: str, action: str, details: Optional[Dict[str, Any]] = None, source: str = "webapp"):
    """Convenience function to publish user action"""
    event_bridge.publish_user_action(user_id, action, details, source)


def market_data(symbol: str, bid: float, ask: float, volume: Optional[int] = None, source: str = "mt5_feed"):
    """Convenience function to publish market data"""
    event_bridge.publish_market_data(symbol, bid, ask, volume, source)