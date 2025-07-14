"""
Mock Signal Alerts for Testing
This is a simplified version for testing purposes only.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SignalAlert:
    """Mock signal alert data class"""
    alert_type: str
    message: str
    data: Dict[str, Any]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class SignalAlerts:
    """Mock signal alerts for testing"""
    
    def __init__(self):
        self.alerts = []
        self.alert_handlers = []
        logger.info("Mock Signal Alerts initialized")
    
    def add_alert_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Mock add alert handler"""
        self.alert_handlers.append(handler)
        logger.info("Mock alert handler added")
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Mock send alert"""
        self.alerts.append({
            "timestamp": datetime.now().isoformat(),
            "data": alert_data
        })
        
        # Call all handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.info(f"Mock alert sent: {alert_data}")
        return True
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Mock get alerts"""
        return self.alerts
    
    def clear_alerts(self) -> None:
        """Mock clear alerts"""
        self.alerts.clear()
        logger.info("Mock alerts cleared")
    
    def format_alert(self, alert_data: Dict[str, Any]) -> str:
        """Mock format alert"""
        return f"Alert: {alert_data.get('message', 'Unknown alert')}"

# Alias for compatibility
SignalAlertSystem = SignalAlerts

def create_signal_alerts() -> SignalAlerts:
    """Create signal alerts instance"""
    return SignalAlerts()


def send_signal_alert(alert_type: str, message: str, data: Dict[str, Any] = None) -> bool:
    """Send a signal alert"""
    alert_data = {
        "type": alert_type,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Mock signal alert sent: {alert_type} - {message}")
    return True


def format_alert_message(alert_type: str, signal_data: Dict[str, Any]) -> str:
    """Format alert message"""
    symbol = signal_data.get('symbol', 'UNKNOWN')
    signal_type = signal_data.get('type', 'UNKNOWN')
    tcs_score = signal_data.get('tcs_score', 0)
    
    if alert_type == "signal_detected":
        return f"🎯 Signal Detected: {symbol} {signal_type.upper()} TCS:{tcs_score}%"
    elif alert_type == "mission_created":
        return f"📋 Mission Created: {symbol} {signal_type.upper()}"
    elif alert_type == "trade_executed":
        return f"⚡ Trade Executed: {symbol} {signal_type.upper()}"
    else:
        return f"📢 Alert: {symbol} {signal_type.upper()}"