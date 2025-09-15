#!/usr/bin/env python3
"""
BITTEN Event Schema Validator
Ensures consistent event structure across the system
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('EventSchema')


class ValidationError(Exception):
    """Custom exception for schema validation errors"""
    pass


class FieldType(Enum):
    """Supported field types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    OBJECT = "object"
    ARRAY = "array"
    OPTIONAL = "optional"


@dataclass
class FieldRule:
    """Validation rule for a field"""
    field_type: FieldType
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None


class EventSchemaValidator:
    """Validates events against predefined schemas"""
    
    def __init__(self):
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict[str, FieldRule]]:
        """Load event schemas for validation"""
        return {
            # Core event structure
            "base_event": {
                "event_type": FieldRule(FieldType.STRING, required=True, max_length=100),
                "timestamp": FieldRule(FieldType.TIMESTAMP, required=True),
                "source": FieldRule(FieldType.STRING, required=True, max_length=100),
                "data": FieldRule(FieldType.OBJECT, required=True),
                "correlation_id": FieldRule(FieldType.STRING, required=False, max_length=200),
                "user_id": FieldRule(FieldType.STRING, required=False, max_length=50),
                "session_id": FieldRule(FieldType.STRING, required=False, max_length=100),
            },
            
            # Signal generation events
            "signal_generated": {
                "signal_id": FieldRule(FieldType.STRING, required=True, max_length=200),
                "symbol": FieldRule(FieldType.STRING, required=True, max_length=10),
                "direction": FieldRule(FieldType.STRING, required=True, 
                                     allowed_values=["BUY", "SELL"]),
                "confidence": FieldRule(FieldType.FLOAT, required=True, 
                                      min_value=0.0, max_value=100.0),
                "pattern_type": FieldRule(FieldType.STRING, required=True, max_length=100),
                "entry_price": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "stop_pips": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "target_pips": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "expires_at": FieldRule(FieldType.TIMESTAMP, required=False),
            },
            
            # Fire command events
            "fire_command": {
                "fire_id": FieldRule(FieldType.STRING, required=True, max_length=200),
                "signal_id": FieldRule(FieldType.STRING, required=True, max_length=200),
                "user_id": FieldRule(FieldType.STRING, required=True, max_length=50),
                "symbol": FieldRule(FieldType.STRING, required=True, max_length=10),
                "direction": FieldRule(FieldType.STRING, required=True,
                                     allowed_values=["BUY", "SELL"]),
                "lot_size": FieldRule(FieldType.FLOAT, required=True, min_value=0.01),
                "sl_price": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "tp_price": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "execution_mode": FieldRule(FieldType.STRING, required=True,
                                          allowed_values=["MANUAL", "AUTO", "SEMI_AUTO"]),
            },
            
            # Trade execution events
            "trade_executed": {
                "fire_id": FieldRule(FieldType.STRING, required=True, max_length=200),
                "ticket": FieldRule(FieldType.INTEGER, required=True, min_value=1),
                "symbol": FieldRule(FieldType.STRING, required=True, max_length=10),
                "direction": FieldRule(FieldType.STRING, required=True,
                                     allowed_values=["BUY", "SELL"]),
                "volume": FieldRule(FieldType.FLOAT, required=True, min_value=0.01),
                "open_price": FieldRule(FieldType.FLOAT, required=True, min_value=0.0),
                "sl_price": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "tp_price": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "execution_time": FieldRule(FieldType.TIMESTAMP, required=True),
            },
            
            # Balance update events
            "balance_update": {
                "user_id": FieldRule(FieldType.STRING, required=True, max_length=50),
                "account_number": FieldRule(FieldType.STRING, required=True, max_length=50),
                "balance": FieldRule(FieldType.FLOAT, required=True, min_value=0.0),
                "equity": FieldRule(FieldType.FLOAT, required=True, min_value=0.0),
                "margin": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "free_margin": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
            },
            
            # System health events
            "system_health": {
                "component": FieldRule(FieldType.STRING, required=True, max_length=100),
                "status": FieldRule(FieldType.STRING, required=True,
                                  allowed_values=["starting", "running", "stopping", "error"]),
                "uptime": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "memory_usage": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "cpu_usage": FieldRule(FieldType.FLOAT, required=False, min_value=0.0),
                "message": FieldRule(FieldType.STRING, required=False, max_length=500),
            },
            
            # Market data events
            "market_data": {
                "symbol": FieldRule(FieldType.STRING, required=True, max_length=10),
                "bid": FieldRule(FieldType.FLOAT, required=True, min_value=0.0),
                "ask": FieldRule(FieldType.FLOAT, required=True, min_value=0.0),
                "volume": FieldRule(FieldType.INTEGER, required=False, min_value=0),
                "timestamp": FieldRule(FieldType.TIMESTAMP, required=True),
            },
            
            # User action events
            "user_action": {
                "user_id": FieldRule(FieldType.STRING, required=True, max_length=50),
                "action": FieldRule(FieldType.STRING, required=True, max_length=100),
                "details": FieldRule(FieldType.OBJECT, required=False),
                "ip_address": FieldRule(FieldType.STRING, required=False, max_length=45),
                "user_agent": FieldRule(FieldType.STRING, required=False, max_length=500),
            }
        }
    
    def validate_event(self, event_data: Dict[str, Any]) -> bool:
        """Validate an event against its schema"""
        try:
            # First validate base event structure
            self._validate_fields(event_data, self.schemas["base_event"])
            
            # Then validate event-specific data
            event_type = event_data.get("event_type")
            if event_type in self.schemas:
                data = event_data.get("data", {})
                self._validate_fields(data, self.schemas[event_type])
            
            return True
            
        except ValidationError as e:
            logger.error(f"❌ Event validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected validation error: {e}")
            return False
    
    def _validate_fields(self, data: Dict[str, Any], schema: Dict[str, FieldRule]):
        """Validate fields against schema rules"""
        # Check required fields
        for field_name, rule in schema.items():
            if rule.required and field_name not in data:
                raise ValidationError(f"Required field '{field_name}' is missing")
        
        # Validate each field present in data
        for field_name, value in data.items():
            if field_name in schema:
                self._validate_field_value(field_name, value, schema[field_name])
    
    def _validate_field_value(self, field_name: str, value: Any, rule: FieldRule):
        """Validate a single field value"""
        # Skip validation for None values on optional fields
        if value is None and not rule.required:
            return
            
        # Type validation
        if rule.field_type == FieldType.STRING and not isinstance(value, str):
            if value is not None:  # Allow None for optional string fields
                raise ValidationError(f"Field '{field_name}' must be a string")
        elif rule.field_type == FieldType.INTEGER and not isinstance(value, int):
            raise ValidationError(f"Field '{field_name}' must be an integer")
        elif rule.field_type == FieldType.FLOAT and not isinstance(value, (int, float)):
            raise ValidationError(f"Field '{field_name}' must be a number")
        elif rule.field_type == FieldType.BOOLEAN and not isinstance(value, bool):
            raise ValidationError(f"Field '{field_name}' must be a boolean")
        elif rule.field_type == FieldType.TIMESTAMP:
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValidationError(f"Field '{field_name}' must be a valid timestamp")
        elif rule.field_type == FieldType.OBJECT and not isinstance(value, dict):
            raise ValidationError(f"Field '{field_name}' must be an object")
        elif rule.field_type == FieldType.ARRAY and not isinstance(value, list):
            raise ValidationError(f"Field '{field_name}' must be an array")
        
        # Range validation
        if rule.min_value is not None and isinstance(value, (int, float)):
            if value < rule.min_value:
                raise ValidationError(f"Field '{field_name}' must be >= {rule.min_value}")
        
        if rule.max_value is not None and isinstance(value, (int, float)):
            if value > rule.max_value:
                raise ValidationError(f"Field '{field_name}' must be <= {rule.max_value}")
        
        # Length validation
        if rule.min_length is not None and isinstance(value, (str, list)):
            if len(value) < rule.min_length:
                raise ValidationError(f"Field '{field_name}' must be at least {rule.min_length} characters/items")
        
        if rule.max_length is not None and isinstance(value, (str, list)):
            if len(value) > rule.max_length:
                raise ValidationError(f"Field '{field_name}' must be at most {rule.max_length} characters/items")
        
        # Allowed values validation
        if rule.allowed_values is not None:
            if value not in rule.allowed_values:
                raise ValidationError(f"Field '{field_name}' must be one of: {rule.allowed_values}")
    
    def get_schema_info(self, event_type: str) -> Dict[str, Any]:
        """Get schema information for documentation"""
        if event_type not in self.schemas:
            return {"error": f"Schema for '{event_type}' not found"}
        
        schema = self.schemas[event_type]
        return {
            "event_type": event_type,
            "fields": {
                field_name: {
                    "type": rule.field_type.value,
                    "required": rule.required,
                    "constraints": {
                        k: v for k, v in {
                            "min_value": rule.min_value,
                            "max_value": rule.max_value,
                            "min_length": rule.min_length,
                            "max_length": rule.max_length,
                            "allowed_values": rule.allowed_values,
                        }.items() if v is not None
                    }
                }
                for field_name, rule in schema.items()
            }
        }


# Global validator instance
validator = EventSchemaValidator()


def validate_event(event_data: Dict[str, Any]) -> bool:
    """Convenience function for event validation"""
    return validator.validate_event(event_data)


def get_schema_info(event_type: str) -> Dict[str, Any]:
    """Get schema information for an event type"""
    return validator.get_schema_info(event_type)