#!/usr/bin/env python3
"""
Symbol-specific pip/point conversion and trading parameter helpers
Ensures correct calculation across all symbols and broker configurations
"""

import toml
from pathlib import Path
from typing import Dict, Optional, Tuple

# Load symbol configurations
CONFIG_PATH = Path("/root/HydraX-v2/config/symbols.toml")
SYMBOL_CONFIG = toml.load(CONFIG_PATH) if CONFIG_PATH.exists() else {}

def get_symbol_config(symbol: str) -> Dict:
    """Get configuration for a specific symbol with fallback to DEFAULT"""
    return SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG.get("DEFAULT", {
        "points_per_pip": 10,
        "min_stop_pips_default": 5,
        "be_offset_min_pips": 2,
        "trail_min_pips": 12,
        "atr_mult_default": 2.0
    }))

def get_pip_size(symbol: str) -> float:
    """Get the pip size for a symbol"""
    if symbol == "XAUUSD":
        return 0.1  # Gold: 1 pip = $0.10
    elif symbol == "XAGUSD":
        return 0.001  # Silver: 1 pip = $0.001
    elif "JPY" in symbol:
        return 0.01  # JPY pairs: 1 pip = 0.01
    else:
        return 0.0001  # Standard pairs: 1 pip = 0.0001

def pips_to_points(symbol: str, pips: float) -> int:
    """Convert pips to MT5 points for a symbol"""
    config = get_symbol_config(symbol)
    return int(pips * config["points_per_pip"])

def points_to_pips(symbol: str, points: int) -> float:
    """Convert MT5 points to pips for a symbol"""
    config = get_symbol_config(symbol)
    return points / config["points_per_pip"]

def price_plus_pips(symbol: str, entry: float, direction: str, pips: float, 
                   side: str = "mid") -> float:
    """
    Add pips to a price considering direction and market side
    
    Args:
        symbol: Trading symbol
        entry: Base price
        direction: "BUY" or "SELL"
        pips: Number of pips to add
        side: "bid", "ask", or "mid" (for which price to use)
    
    Returns:
        Adjusted price
    """
    pip_size = get_pip_size(symbol)
    pip_value = pips * pip_size
    
    if direction.upper() == "BUY":
        result = entry + pip_value
    else:  # SELL
        result = entry - pip_value
    
    # Round to appropriate decimal places
    if pip_size >= 0.01:  # JPY pairs, Gold
        return round(result, 2)
    elif pip_size >= 0.001:  # Silver
        return round(result, 3)
    else:  # Standard pairs
        return round(result, 5)

def spread_pips(symbol: str, bid: float, ask: float) -> float:
    """Calculate spread in pips between bid and ask"""
    pip_size = get_pip_size(symbol)
    return abs(ask - bid) / pip_size

def min_stop_pips(symbol: str, broker_min: Optional[int] = None) -> int:
    """
    Get minimum stop distance in pips
    Uses broker-provided value if available, otherwise config default
    """
    if broker_min is not None:
        return points_to_pips(symbol, broker_min)
    
    config = get_symbol_config(symbol)
    return config["min_stop_pips_default"]

def be_offset_pips(symbol: str, current_spread_pips: float, 
                  broker_min_stop: Optional[int] = None) -> float:
    """
    Calculate safe BE offset considering spread and minimum stop distance
    
    Args:
        symbol: Trading symbol
        current_spread_pips: Current spread in pips
        broker_min_stop: Broker's minimum stop distance in points
    
    Returns:
        BE offset in pips that ensures the position won't be stopped immediately
    """
    config = get_symbol_config(symbol)
    min_offset = config["be_offset_min_pips"]
    
    # Consider spread (double it for safety)
    spread_offset = current_spread_pips * 2
    
    # Consider broker minimum stop
    min_stop = min_stop_pips(symbol, broker_min_stop)
    
    # Take the maximum of all constraints
    return max(min_offset, spread_offset, min_stop)

def trail_min_pips(symbol: str) -> float:
    """Get minimum trailing stop distance in pips"""
    config = get_symbol_config(symbol)
    return config["trail_min_pips"]

def calculate_trail_distance(symbol: str, atr_value: float, 
                            method: str = "ATR") -> float:
    """
    Calculate trailing stop distance based on method
    
    Args:
        symbol: Trading symbol
        atr_value: Current ATR value in price units
        method: "ATR" or "STEP"
    
    Returns:
        Trail distance in pips
    """
    config = get_symbol_config(symbol)
    min_trail = config["trail_min_pips"]
    
    if method == "ATR" and atr_value > 0:
        # Convert ATR to pips
        pip_size = get_pip_size(symbol)
        atr_pips = atr_value / pip_size
        
        # Apply multiplier
        atr_mult = config.get("atr_mult_default", 2.0)
        trail_dist = atr_pips * atr_mult
        
        # Ensure minimum distance
        return max(trail_dist, min_trail)
    else:
        # Use fixed step trailing
        return max(20, min_trail)  # Default 20 pip steps

def normalize_price(symbol: str, price: float) -> float:
    """Normalize price to correct decimal places for symbol"""
    pip_size = get_pip_size(symbol)
    
    if pip_size >= 0.01:  # JPY pairs, Gold
        return round(price, 2)
    elif pip_size >= 0.001:  # Silver
        return round(price, 3)
    else:  # Standard pairs
        return round(price, 5)

def validate_sl_distance(symbol: str, entry: float, sl: float, 
                        direction: str) -> Tuple[bool, str]:
    """
    Validate that SL is at safe distance from entry
    
    Returns:
        (is_valid, error_message)
    """
    sl_pips = abs(price_to_pips(symbol, entry, sl))
    min_pips = min_stop_pips(symbol)
    
    if sl_pips < min_pips:
        return False, f"SL too close: {sl_pips:.1f} pips < {min_pips} minimum"
    
    # Check direction consistency
    if direction.upper() == "BUY" and sl >= entry:
        return False, f"BUY SL must be below entry"
    elif direction.upper() == "SELL" and sl <= entry:
        return False, f"SELL SL must be above entry"
    
    return True, ""

def price_to_pips(symbol: str, price1: float, price2: float) -> float:
    """Calculate pip distance between two prices"""
    pip_size = get_pip_size(symbol)
    return abs(price1 - price2) / pip_size