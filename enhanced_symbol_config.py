#!/usr/bin/env python3
"""
Enhanced Symbol Configuration for Elite Guard
Expanded from 10 to 17 pairs for more trading opportunities
"""

# Original 10 symbols
ORIGINAL_SYMBOLS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 
    'AUDUSD', 'NZDUSD', 'USDCHF', 'EURJPY',
    'GBPJPY', 'XAUUSD'
]

# New symbols added for expansion (7 additional)
NEW_SYMBOLS = [
    'USDJPY',   # Already in original but confirming
    'USDCNH',   # Chinese Yuan 
    'USDSEK',   # Swedish Krona
    'EURJPY',   # Already in original but confirming
    'EURGBP',   # Range trader
    'EURAUD',   # Trend follower
    'GBPCAD',   # Volatility pair
    'AUDJPY',   # Risk sentiment
    'NZDJPY',   # Carry trade
    'XAGUSD'    # Silver
]

# Complete list of all trading symbols (removing duplicates)
ALL_SYMBOLS = list(set([
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 
    'AUDUSD', 'NZDUSD', 'USDCHF', 'EURJPY',
    'GBPJPY', 'XAUUSD', 'USDCNH', 'USDSEK',
    'EURGBP', 'EURAUD', 'GBPCAD', 'AUDJPY',
    'NZDJPY', 'XAGUSD'
]))

# Symbol-specific configurations
SYMBOL_CONFIG = {
    # Major Pairs
    'EURUSD': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00008,
        'max_spread': 0.00025,
        'session_preference': ['LONDON', 'NY', 'OVERLAP'],
        'volatility_multiplier': 1.0
    },
    'GBPUSD': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00010,
        'max_spread': 0.00035,
        'session_preference': ['LONDON', 'NY', 'OVERLAP'],
        'volatility_multiplier': 1.2
    },
    'USDJPY': {
        'pip_size': 0.01,
        'pip_value': 9.5,
        'atr_period': 14,
        'min_spread': 0.008,
        'max_spread': 0.025,
        'session_preference': ['ASIAN', 'NY', 'OVERLAP'],
        'volatility_multiplier': 0.9
    },
    'USDCAD': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00010,
        'max_spread': 0.00030,
        'session_preference': ['NY', 'OVERLAP'],
        'volatility_multiplier': 0.8
    },
    'AUDUSD': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00008,
        'max_spread': 0.00025,
        'session_preference': ['ASIAN', 'NY'],
        'volatility_multiplier': 0.9
    },
    'NZDUSD': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00012,
        'max_spread': 0.00035,
        'session_preference': ['ASIAN', 'NY'],
        'volatility_multiplier': 0.85
    },
    'USDCHF': {
        'pip_size': 0.0001,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.00010,
        'max_spread': 0.00028,
        'session_preference': ['LONDON', 'NY'],
        'volatility_multiplier': 0.7
    },
    
    # Cross Pairs
    'EURJPY': {
        'pip_size': 0.01,
        'pip_value': 9.5,
        'atr_period': 14,
        'min_spread': 0.012,
        'max_spread': 0.040,
        'session_preference': ['LONDON', 'ASIAN', 'OVERLAP'],
        'volatility_multiplier': 1.3
    },
    'GBPJPY': {
        'pip_size': 0.01,
        'pip_value': 9.5,
        'atr_period': 14,
        'min_spread': 0.020,
        'max_spread': 0.060,
        'session_preference': ['LONDON', 'ASIAN', 'OVERLAP'],
        'volatility_multiplier': 1.5
    },
    'EURGBP': {
        'pip_size': 0.0001,
        'pip_value': 12.5,
        'atr_period': 14,
        'min_spread': 0.00010,
        'max_spread': 0.00030,
        'session_preference': ['LONDON', 'OVERLAP'],
        'volatility_multiplier': 0.6
    },
    'EURAUD': {
        'pip_size': 0.0001,
        'pip_value': 7.5,
        'atr_period': 14,
        'min_spread': 0.00020,
        'max_spread': 0.00050,
        'session_preference': ['LONDON', 'ASIAN'],
        'volatility_multiplier': 1.1
    },
    'GBPCAD': {
        'pip_size': 0.0001,
        'pip_value': 7.8,
        'atr_period': 14,
        'min_spread': 0.00025,
        'max_spread': 0.00060,
        'session_preference': ['LONDON', 'NY'],
        'volatility_multiplier': 1.3
    },
    'AUDJPY': {
        'pip_size': 0.01,
        'pip_value': 9.5,
        'atr_period': 14,
        'min_spread': 0.015,
        'max_spread': 0.045,
        'session_preference': ['ASIAN', 'NY'],
        'volatility_multiplier': 1.2
    },
    'NZDJPY': {
        'pip_size': 0.01,
        'pip_value': 9.5,
        'atr_period': 14,
        'min_spread': 0.018,
        'max_spread': 0.050,
        'session_preference': ['ASIAN', 'NY'],
        'volatility_multiplier': 1.1
    },
    
    # Exotic Pairs
    'USDCNH': {
        'pip_size': 0.0001,
        'pip_value': 1.5,
        'atr_period': 20,
        'min_spread': 0.0003,
        'max_spread': 0.0015,
        'session_preference': ['ASIAN'],
        'volatility_multiplier': 0.5
    },
    'USDSEK': {
        'pip_size': 0.0001,
        'pip_value': 1.2,
        'atr_period': 20,
        'min_spread': 0.0030,
        'max_spread': 0.0100,
        'session_preference': ['LONDON', 'NY'],
        'volatility_multiplier': 0.9
    },
    
    # Metals
    'XAUUSD': {
        'pip_size': 0.1,
        'pip_value': 10,
        'atr_period': 14,
        'min_spread': 0.15,
        'max_spread': 0.50,
        'session_preference': ['LONDON', 'NY', 'OVERLAP'],
        'volatility_multiplier': 2.0
    },
    'XAGUSD': {
        'pip_size': 0.01,
        'pip_value': 50,
        'atr_period': 14,
        'min_spread': 0.02,
        'max_spread': 0.08,
        'session_preference': ['LONDON', 'NY', 'OVERLAP'],
        'volatility_multiplier': 2.5
    }
}

# Session-specific adjustments
SESSION_ADJUSTMENTS = {
    'ASIAN': {
        'confidence_modifier': 0.9,  # Slightly lower confidence in Asian session
        'preferred_patterns': ['SUPPORT_RESISTANCE_BOUNCE', 'FAIR_VALUE_GAP_FILL'],
        'avoid_patterns': ['BREAKOUT_MOMENTUM']  # Less breakouts in quiet session
    },
    'LONDON': {
        'confidence_modifier': 1.1,  # Higher confidence in London
        'preferred_patterns': ['BREAKOUT_MOMENTUM', 'LIQUIDITY_SWEEP_REVERSAL'],
        'avoid_patterns': []
    },
    'NY': {
        'confidence_modifier': 1.05,
        'preferred_patterns': ['VOLUME_CLIMAX_REVERSAL', 'BREAKOUT_MOMENTUM'],
        'avoid_patterns': []
    },
    'OVERLAP': {
        'confidence_modifier': 1.15,  # Highest confidence during overlap
        'preferred_patterns': ['LIQUIDITY_SWEEP_REVERSAL', 'BREAKOUT_MOMENTUM'],
        'avoid_patterns': []
    },
    'OFF_HOURS': {
        'confidence_modifier': 0.8,
        'preferred_patterns': ['SUPPORT_RESISTANCE_BOUNCE'],
        'avoid_patterns': ['BREAKOUT_MOMENTUM', 'VOLUME_CLIMAX_REVERSAL']
    }
}

# Pattern-specific settings per symbol type
PATTERN_PREFERENCES = {
    'MAJORS': {  # EURUSD, GBPUSD, USDJPY, etc.
        'LIQUIDITY_SWEEP_REVERSAL': 1.0,
        'SUPPORT_RESISTANCE_BOUNCE': 1.0,
        'BREAKOUT_MOMENTUM': 1.0,
        'FAIR_VALUE_GAP_FILL': 0.9,
        'VOLUME_CLIMAX_REVERSAL': 1.0
    },
    'CROSSES': {  # EURJPY, GBPJPY, EURGBP, etc.
        'LIQUIDITY_SWEEP_REVERSAL': 0.9,
        'SUPPORT_RESISTANCE_BOUNCE': 1.1,  # Works well on crosses
        'BREAKOUT_MOMENTUM': 0.8,
        'FAIR_VALUE_GAP_FILL': 1.0,
        'VOLUME_CLIMAX_REVERSAL': 0.9
    },
    'EXOTICS': {  # USDCNH, USDSEK
        'LIQUIDITY_SWEEP_REVERSAL': 0.7,
        'SUPPORT_RESISTANCE_BOUNCE': 1.2,  # Best for exotics
        'BREAKOUT_MOMENTUM': 0.6,
        'FAIR_VALUE_GAP_FILL': 0.8,
        'VOLUME_CLIMAX_REVERSAL': 0.7
    },
    'METALS': {  # XAUUSD, XAGUSD
        'LIQUIDITY_SWEEP_REVERSAL': 1.2,  # Great for metals
        'SUPPORT_RESISTANCE_BOUNCE': 0.9,
        'BREAKOUT_MOMENTUM': 1.1,
        'FAIR_VALUE_GAP_FILL': 0.8,
        'VOLUME_CLIMAX_REVERSAL': 1.3  # Excellent for metals
    }
}

def get_symbol_type(symbol: str) -> str:
    """Determine symbol type for pattern preferences"""
    if symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD', 'NZDUSD', 'USDCHF']:
        return 'MAJORS'
    elif symbol in ['EURJPY', 'GBPJPY', 'EURGBP', 'EURAUD', 'GBPCAD', 'AUDJPY', 'NZDJPY']:
        return 'CROSSES'
    elif symbol in ['USDCNH', 'USDSEK']:
        return 'EXOTICS'
    elif symbol in ['XAUUSD', 'XAGUSD']:
        return 'METALS'
    else:
        return 'MAJORS'  # Default

def get_pip_size(symbol: str) -> float:
    """Get pip size for a symbol"""
    return SYMBOL_CONFIG.get(symbol, {}).get('pip_size', 0.0001)

def get_session_adjustment(session: str, pattern: str) -> float:
    """Get confidence adjustment for session and pattern combo"""
    session_data = SESSION_ADJUSTMENTS.get(session, {})
    base_modifier = session_data.get('confidence_modifier', 1.0)
    
    if pattern in session_data.get('preferred_patterns', []):
        return base_modifier * 1.1
    elif pattern in session_data.get('avoid_patterns', []):
        return base_modifier * 0.8
    else:
        return base_modifier

def should_trade_symbol(symbol: str, session: str) -> bool:
    """Check if symbol should be traded in current session"""
    config = SYMBOL_CONFIG.get(symbol, {})
    preferred_sessions = config.get('session_preference', [])
    
    # Always trade if no preference set
    if not preferred_sessions:
        return True
    
    # Trade if current session is preferred
    return session in preferred_sessions

def get_spread_filter(symbol: str, current_spread: float) -> bool:
    """Check if spread is acceptable for trading"""
    config = SYMBOL_CONFIG.get(symbol, {})
    max_spread = config.get('max_spread', float('inf'))
    
    return current_spread <= max_spread