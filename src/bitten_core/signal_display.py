"""
Mock Signal Display for Testing
This is a simplified version for testing purposes only.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SignalDisplay:
    """Mock signal display for testing"""
    
    def __init__(self):
        self.signals = []
        logger.info("Mock Signal Display initialized")
    
    def add_signal(self, signal: Dict[str, Any]) -> None:
        """Mock add signal"""
        self.signals.append(signal)
        logger.info(f"Mock signal added: {signal.get('symbol', 'UNKNOWN')}")
    
    def get_signals(self) -> List[Dict[str, Any]]:
        """Mock get signals"""
        return self.signals
    
    def clear_signals(self) -> None:
        """Mock clear signals"""
        self.signals.clear()
        logger.info("Mock signals cleared")
    
    def format_signal(self, signal: Dict[str, Any]) -> str:
        """Mock format signal"""
        return f"{signal.get('symbol', 'UNKNOWN')} {signal.get('type', 'UNKNOWN')} TCS:{signal.get('tcs_score', 0)}%"
    
    def display_signal(self, signal: Dict[str, Any]) -> str:
        """Mock display signal"""
        formatted = self.format_signal(signal)
        logger.info(f"Mock signal displayed: {formatted}")
        return formatted


def create_signal_display() -> SignalDisplay:
    """Create signal display instance"""
    return SignalDisplay()


def format_signal_for_display(signal: Dict[str, Any], format_type: str = "default") -> str:
    """Format signal for display"""
    symbol = signal.get('symbol', 'UNKNOWN')
    signal_type = signal.get('type', 'UNKNOWN')
    tcs_score = signal.get('tcs_score', 0)
    
    if format_type == "markdown":
        return f"**{symbol}** {signal_type.upper()} TCS:{tcs_score}%"
    elif format_type == "html":
        return f"<b>{symbol}</b> {signal_type.upper()} TCS:{tcs_score}%"
    else:
        return f"{symbol} {signal_type.upper()} TCS:{tcs_score}%"