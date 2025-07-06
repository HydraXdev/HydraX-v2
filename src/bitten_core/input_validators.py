"""
Input validation utilities for security
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_currency_code(currency: str) -> bool:
    """Validate currency code format (3 uppercase letters)"""
    return bool(re.match(r'^[A-Z]{3}$', currency))

def sanitize_event_name(name: str, max_length: int = 200) -> str:
    """Sanitize event name to prevent injection attacks"""
    if not name:
        return ""
    
    # Remove any HTML/script tags
    name = re.sub(r'<[^>]+>', '', name)
    
    # Remove potentially dangerous characters
    name = re.sub(r'[<>\"\'\\]', '', name)
    
    # Normalize whitespace
    name = ' '.join(name.split())
    
    # Limit length
    return name[:max_length]

def sanitize_numeric_string(value: Optional[str]) -> Optional[str]:
    """Sanitize numeric string values (like forecast, previous)"""
    if not value:
        return None
    
    # Extract numeric part and unit
    match = re.match(r'^([-+]?\d*\.?\d+)\s*(%|K|M|B)?$', str(value).strip())
    if match:
        return match.group(0)
    
    return None

def validate_datetime_string(date_str: str, format_str: str) -> Optional[datetime]:
    """Safely parse datetime string"""
    try:
        # Limit string length to prevent DoS
        if len(date_str) > 50:
            return None
        
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None

def validate_impact_level(impact: str, valid_levels: List[str]) -> Optional[str]:
    """Validate impact level against allowed values"""
    if not impact:
        return None
    
    impact_lower = impact.lower()
    for level in valid_levels:
        if impact_lower in [str(v).lower() for v in level]:
            return level[0] if isinstance(level, list) else level
    
    return None

def sanitize_api_response(data: Any, max_items: int = 1000) -> Any:
    """Sanitize API response data recursively"""
    if isinstance(data, str):
        return sanitize_event_name(data)
    elif isinstance(data, list):
        # Limit list size to prevent memory exhaustion
        return [sanitize_api_response(item) for item in data[:max_items]]
    elif isinstance(data, dict):
        return {k: sanitize_api_response(v) for k, v in data.items()}
    else:
        return data

def validate_hours_parameter(hours_str: str, min_hours: int = 1, max_hours: int = 168) -> Optional[int]:
    """Validate hours parameter for queries"""
    try:
        hours = int(hours_str)
        if min_hours <= hours <= max_hours:
            return hours
    except (ValueError, TypeError):
        pass
    
    return None

def sanitize_log_message(message: str, max_length: int = 500) -> str:
    """Sanitize message for logging to prevent log injection"""
    # Remove newlines and control characters
    message = re.sub(r'[\r\n\t\x00-\x1f]', ' ', message)
    
    # Limit length
    return message[:max_length]

# JSON Schema for news event validation
NEWS_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
            "maxLength": 10
        },
        "time": {
            "type": "string",
            "maxLength": 20
        },
        "country": {
            "type": "string",
            "pattern": "^[A-Z]{3}$",
            "maxLength": 3
        },
        "impact": {
            "type": "string",
            "maxLength": 20
        },
        "title": {
            "type": "string",
            "maxLength": 200
        },
        "forecast": {
            "type": ["string", "null"],
            "maxLength": 50
        },
        "previous": {
            "type": ["string", "null"],
            "maxLength": 50
        },
        "actual": {
            "type": ["string", "null"],
            "maxLength": 50
        }
    },
    "required": ["date", "country", "title"],
    "additionalProperties": False
}

def validate_news_event(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate and sanitize a news event"""
    try:
        # Basic type check
        if not isinstance(event_data, dict):
            return None
        
        # Extract and validate required fields
        date = event_data.get('date', '')
        country = event_data.get('country', '')
        title = event_data.get('title', '')
        
        if not all([date, country, title]):
            return None
        
        # Validate currency code
        if not validate_currency_code(country):
            return None
        
        # Build sanitized event
        sanitized = {
            'date': date[:10],  # Limit length
            'time': event_data.get('time', '')[:20],
            'country': country,
            'impact': event_data.get('impact', '')[:20],
            'title': sanitize_event_name(title),
            'forecast': sanitize_numeric_string(event_data.get('forecast')),
            'previous': sanitize_numeric_string(event_data.get('previous')),
            'actual': sanitize_numeric_string(event_data.get('actual'))
        }
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Event validation error: {sanitize_log_message(str(e))}")
        return None