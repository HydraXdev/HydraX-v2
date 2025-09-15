"""
BITTEN Event Bus System
Professional ZMQ-based event bus for the BITTEN trading platform
"""

from .event_bus import EventBus, EventBusClient, Event, EventType
from .event_schema import EventSchemaValidator, validate_event, get_schema_info
from .data_collector import DataCollector
from .event_bridge import (
    event_bridge,
    signal_generated,
    fire_command, 
    trade_executed,
    balance_update,
    system_health,
    user_action,
    market_data
)

__version__ = "1.0.0"
__all__ = [
    "EventBus",
    "EventBusClient", 
    "Event",
    "EventType",
    "EventSchemaValidator",
    "validate_event",
    "get_schema_info",
    "DataCollector",
    "event_bridge",
    "signal_generated",
    "fire_command",
    "trade_executed", 
    "balance_update",
    "system_health",
    "user_action",
    "market_data"
]