#!/usr/bin/env python3
"""
CITADEL State Reader - Helper module for loading live adjustments
Provides function get_adjustments(symbol) for VENOM and CITADEL integration
Read-only logic, no writing allowed from engine side
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Minimal logging to avoid engine noise
logger = logging.getLogger(__name__)

class CitadelStateReader:
    """Read-only helper for accessing CITADEL state adjustments"""
    
    def __init__(self, state_path: str = "/root/HydraX-v2/citadel_state.json"):
        self.state_path = Path(state_path)
        self._cache = {}
        self._last_modified = 0
        
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file with caching"""
        try:
            if not self.state_path.exists():
                return {}
            
            # Check if file has been modified
            current_modified = self.state_path.stat().st_mtime
            if current_modified == self._last_modified and self._cache:
                return self._cache
            
            # Load fresh data
            with open(self.state_path, 'r') as f:
                data = json.load(f)
            
            self._cache = data
            self._last_modified = current_modified
            return data
            
        except Exception as e:
            logger.warning(f"Error loading CITADEL state: {e}")
            return {}
    
    def get_adjustments(self, symbol: str) -> Dict[str, Any]:
        """
        Get adjustments for a specific symbol
        Returns dict with cooldowns, penalties, and thresholds
        """
        state = self._load_state()
        symbol_lower = symbol.lower()
        
        # Start with empty adjustments
        adjustments = {
            'status': 'active',
            'cooldown_until': None,
            'tcs_penalty': 0.0,
            'entry_delay_ms': 0,
            'min_runtime_minutes': 0,
            'reason': None
        }
        
        # Apply global adjustments first
        global_config = state.get('global', {})
        if global_config:
            if 'auto_close_seconds' in global_config:
                adjustments['auto_close_seconds'] = global_config['auto_close_seconds']
            
            if 'default_tcs_minimum' in global_config:
                adjustments['default_tcs_minimum'] = global_config['default_tcs_minimum']
            
            # Hour restrictions
            if 'hour_restriction' in global_config:
                current_hour = datetime.now(timezone.utc).hour
                restriction = global_config['hour_restriction']
                if restriction.get('restricted_hour') == current_hour:
                    adjustments['tcs_penalty'] = max(adjustments['tcs_penalty'], 
                                                   restriction.get('min_tcs_required', 85.0) - 70.0)
                    adjustments['reason'] = restriction.get('reason', 'Hour restriction active')
        
        # Apply symbol-specific adjustments
        symbol_config = state.get(symbol_lower, {})
        if symbol_config:
            # Check cooldown status
            if symbol_config.get('status') == 'cooldown':
                cooldown_until = symbol_config.get('cooldown_until')
                if cooldown_until:
                    try:
                        cooldown_time = datetime.fromisoformat(cooldown_until.replace('Z', '+00:00'))
                        if datetime.now(timezone.utc) < cooldown_time:
                            adjustments['status'] = 'cooldown'
                            adjustments['cooldown_until'] = cooldown_until
                            adjustments['reason'] = symbol_config.get('reason', 'Symbol in cooldown')
                        # If cooldown expired, status remains 'active'
                    except (ValueError, TypeError):
                        pass  # Invalid date format, ignore cooldown
            
            # Apply penalties and delays
            if 'tcs_penalty' in symbol_config:
                adjustments['tcs_penalty'] = max(adjustments['tcs_penalty'], 
                                               float(symbol_config['tcs_penalty']))
            
            if 'entry_delay_ms' in symbol_config:
                adjustments['entry_delay_ms'] = max(adjustments['entry_delay_ms'],
                                                  int(symbol_config['entry_delay_ms']))
            
            if 'min_runtime_minutes' in symbol_config:
                adjustments['min_runtime_minutes'] = max(adjustments['min_runtime_minutes'],
                                                        int(symbol_config['min_runtime_minutes']))
            
            # Use symbol-specific reason if available
            if symbol_config.get('reason') and not adjustments['reason']:
                adjustments['reason'] = symbol_config['reason']
        
        return adjustments
    
    def is_symbol_allowed(self, symbol: str) -> bool:
        """Quick check if symbol is allowed (not in cooldown)"""
        adjustments = self.get_adjustments(symbol)
        return adjustments['status'] != 'cooldown'
    
    def get_tcs_adjustment(self, symbol: str, base_tcs: float) -> float:
        """Get adjusted TCS score with penalties applied"""
        adjustments = self.get_adjustments(symbol)
        penalty = adjustments.get('tcs_penalty', 0.0)
        return base_tcs + penalty
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration settings"""
        state = self._load_state()
        return state.get('global', {})

# Global instance for easy importing
_reader_instance = None

def get_adjustments(symbol: str) -> Dict[str, Any]:
    """
    Global function to get adjustments for a symbol
    Used by VENOM and CITADEL to apply live adjustments
    """
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = CitadelStateReader()
    
    return _reader_instance.get_adjustments(symbol)

def is_symbol_allowed(symbol: str) -> bool:
    """Global function to check if symbol is allowed"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = CitadelStateReader()
    
    return _reader_instance.is_symbol_allowed(symbol)

def get_tcs_adjustment(symbol: str, base_tcs: float) -> float:
    """Global function to get adjusted TCS score"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = CitadelStateReader()
    
    return _reader_instance.get_tcs_adjustment(symbol, base_tcs)

def get_global_config() -> Dict[str, Any]:
    """Global function to get global configuration"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = CitadelStateReader()
    
    return _reader_instance.get_global_config()

# Example usage for testing
if __name__ == "__main__":
    # Test the reader
    reader = CitadelStateReader()
    
    test_symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    print("🛡️ CITADEL State Reader Test")
    print("=" * 40)
    
    for symbol in test_symbols:
        adjustments = reader.get_adjustments(symbol)
        allowed = reader.is_symbol_allowed(symbol)
        adjusted_tcs = reader.get_tcs_adjustment(symbol, 75.0)
        
        print(f"\n{symbol}:")
        print(f"  Status: {adjustments['status']}")
        print(f"  Allowed: {allowed}")
        print(f"  TCS Penalty: +{adjustments['tcs_penalty']}")
        print(f"  Adjusted TCS (75 → {adjusted_tcs})")
        print(f"  Entry Delay: {adjustments['entry_delay_ms']}ms")
        if adjustments['reason']:
            print(f"  Reason: {adjustments['reason']}")
    
    global_config = reader.get_global_config()
    if global_config:
        print(f"\nGlobal Config: {global_config}")