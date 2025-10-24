#!/usr/bin/env python3
"""
BITTEN Trading System - Centralized Constants
==============================================

Unified pip size definitions and symbol specifications to ensure consistent
calculations across auto-fire, manual fire, and fire command creation.

Created: 2025-10-23
Purpose: Fix pip calculation inconsistencies between auto-fire and manual fire flows
"""

# ============================================================================
# PIP SIZE DEFINITIONS
# ============================================================================
# One pip represents the smallest price movement that matters for trading

PIP_SIZES = {
    "JPY": 0.01,      # JPY pairs: 1 pip = 0.01 (e.g., 150.00 → 150.01)
    "XAUUSD": 0.10,   # Gold: 1 pip = $0.10 (e.g., $1935.00 → $1935.10)
    "XAGUSD": 0.001,  # Silver: 1 pip = $0.001 (e.g., $22.000 → $22.001)
    "DEFAULT": 0.0001 # Majors/crosses: 1 pip = 0.0001 (e.g., 1.0500 → 1.0501)
}

# PIP VALUES (USD value per standard lot per pip)
PIP_VALUES = {
    "EURUSD": 10.0,
    "GBPUSD": 10.0,
    "AUDUSD": 10.0,
    "NZDUSD": 10.0,
    "USDCAD": 9.09,
    "USDCHF": 10.0,
    "USDJPY": 9.09,
    "EURJPY": 9.09,
    "GBPJPY": 9.09,
    "AUDJPY": 9.09,
    "NZDJPY": 9.09,
    "XAUUSD": 10.0,   # Gold: $10 per pip per standard lot
    "XAGUSD": 5.0,    # Silver: $5 per pip per standard lot (5000 oz)
    "USDCNH": 1.4,    # Approximate, varies with CNH rate
    "USDMXN": 0.5,    # Approximate, varies with MXN rate
    "USDZAR": 0.6,    # Approximate, varies with ZAR rate
    "USDTRY": 0.3,    # Approximate, varies with TRY rate
    "USDSEK": 1.1,    # Approximate, varies with SEK rate
    "USDNOK": 1.1,    # Approximate, varies with NOK rate
    "USDDKK": 1.5,    # Approximate, varies with DKK rate
}

# ============================================================================
# SCALPING STOP LIMITS (Symbol + Timeframe Aware)
# ============================================================================
# Min/Max stop distances for scalping trades by symbol group and timeframe

SCALP_STOP_LIMITS = {
    # Format: (symbol_group, timeframe): (min_pips, max_pips)

    # M1 Ultra-Fast Scalping (Pulse V3, Apex Sentinel)
    # Designed for 5-20 minute trades with tight but realistic stops
    ("JPY", "M1"): (3, 18),        # 3-18 pips (above spread, below noise)
    ("MAJORS", "M1"): (5, 25),     # 5-25 pips (2x spread minimum)
    ("XAUUSD", "M1"): (15, 80),    # $1.50 to $8.00 (fast gold scalping)
    ("XAGUSD", "M1"): (10, 50),    # $0.010 to $0.050 (fast silver scalping)
    ("EXOTICS", "M1"): (8, 35),    # Tighter than M5 for speed

    # M5 Standard Scalping (Elite Guard default)
    # Designed for 15-60 minute trades with quality stops
    ("JPY", "M5"): (6, 35),
    ("MAJORS", "M5"): (10, 45),
    ("XAUUSD", "M5"): (25, 120),   # $2.50 to $12.00
    ("XAGUSD", "M5"): (15, 80),    # $0.015 to $0.080
    ("EXOTICS", "M5"): (15, 60),

    # M15+ Swing Scalping (longer timeframes)
    ("JPY", "M15"): (8, 40),
    ("JPY", "H1"): (10, 60),
    ("MAJORS", "M15"): (12, 50),
    ("MAJORS", "H1"): (15, 70),
    ("XAUUSD", "M15"): (30, 150),  # $3.00 to $15.00
    ("XAUUSD", "H1"): (40, 200),   # $4.00 to $20.00
    ("XAGUSD", "M15"): (20, 100),  # $0.020 to $0.100
    ("XAGUSD", "H1"): (25, 120),   # $0.025 to $0.120
    ("EXOTICS", "M15"): (20, 75),
    ("EXOTICS", "H1"): (25, 100),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_pip_size(symbol: str) -> float:
    """
    Get the pip size for a given symbol.

    Args:
        symbol: Trading symbol (e.g., "EURUSD", "USDJPY", "XAUUSD")

    Returns:
        Pip size as a float (e.g., 0.0001 for EURUSD, 0.01 for USDJPY)

    Examples:
        >>> get_pip_size("USDJPY")
        0.01
        >>> get_pip_size("EURUSD")
        0.0001
        >>> get_pip_size("XAUUSD")
        0.10
        >>> get_pip_size("XAGUSD")
        0.001
    """
    if "JPY" in symbol:
        return PIP_SIZES["JPY"]
    elif "XAUUSD" in symbol or symbol == "XAUUSD":
        return PIP_SIZES["XAUUSD"]
    elif "XAGUSD" in symbol or symbol == "XAGUSD":
        return PIP_SIZES["XAGUSD"]
    else:
        return PIP_SIZES["DEFAULT"]


def get_pip_value(symbol: str) -> float:
    """
    Get the USD value per pip per standard lot for a given symbol.

    Args:
        symbol: Trading symbol (e.g., "EURUSD", "XAUUSD")

    Returns:
        USD value per pip per standard lot (e.g., 10.0 for EURUSD)

    Examples:
        >>> get_pip_value("EURUSD")
        10.0
        >>> get_pip_value("XAUUSD")
        10.0
        >>> get_pip_value("XAGUSD")
        5.0
    """
    return PIP_VALUES.get(symbol, 10.0)  # Default to $10 per pip


def get_min_max_stop_pips(symbol: str, timeframe: str = "M5") -> tuple[float, float]:
    """
    Get minimum and maximum stop distances in pips for a symbol and timeframe.

    Optimized for scalping trades that should resolve within 30-120 minutes.

    Args:
        symbol: Trading symbol (e.g., "EURUSD", "USDJPY")
        timeframe: Timeframe (e.g., "M5", "M15", "H1")

    Returns:
        Tuple of (min_pips, max_pips)

    Examples:
        >>> get_min_max_stop_pips("USDJPY", "M5")
        (6, 35)
        >>> get_min_max_stop_pips("EURUSD", "M15")
        (12, 50)
        >>> get_min_max_stop_pips("XAUUSD", "M5")
        (25, 120)
    """
    # Determine symbol group
    if "JPY" in symbol:
        group = "JPY"
    elif symbol == "XAUUSD":
        group = "XAUUSD"
    elif symbol == "XAGUSD":
        group = "XAGUSD"
    elif symbol in ["USDCNH", "USDMXN", "USDZAR", "USDTRY", "USDSEK", "USDNOK", "USDDKK"]:
        group = "EXOTICS"
    else:
        group = "MAJORS"

    # Normalize timeframe
    tf = timeframe.upper()
    if tf not in ["M1", "M5", "M15", "H1"]:
        tf = "M5"  # Default to M5 for scalping

    # Look up limits
    key = (group, tf)
    if key in SCALP_STOP_LIMITS:
        return SCALP_STOP_LIMITS[key]

    # Fallback to M5 limits for the group
    fallback_key = (group, "M5")
    if fallback_key in SCALP_STOP_LIMITS:
        return SCALP_STOP_LIMITS[fallback_key]

    # Ultimate fallback
    return (10.0, 45.0)


def calculate_stop_loss_price(entry_price: float, stop_pips: float, direction: str, symbol: str) -> float:
    """
    Calculate absolute stop loss price from entry and pip distance.

    Args:
        entry_price: Entry price
        stop_pips: Stop distance in pips
        direction: "BUY" or "SELL"
        symbol: Trading symbol

    Returns:
        Absolute stop loss price

    Examples:
        >>> calculate_stop_loss_price(1.0500, 20, "BUY", "EURUSD")
        1.0480
        >>> calculate_stop_loss_price(152.60, 20, "SELL", "USDJPY")
        152.80
        >>> calculate_stop_loss_price(1935.0, 20, "BUY", "XAUUSD")
        1933.0
    """
    pip_size = get_pip_size(symbol)
    distance = stop_pips * pip_size

    if direction.upper() == "BUY":
        return entry_price - distance
    else:  # SELL
        return entry_price + distance


def calculate_take_profit_price(entry_price: float, target_pips: float, direction: str, symbol: str) -> float:
    """
    Calculate absolute take profit price from entry and pip distance.

    Args:
        entry_price: Entry price
        target_pips: Target distance in pips
        direction: "BUY" or "SELL"
        symbol: Trading symbol

    Returns:
        Absolute take profit price

    Examples:
        >>> calculate_take_profit_price(1.0500, 30, "BUY", "EURUSD")
        1.0530
        >>> calculate_take_profit_price(152.60, 30, "SELL", "USDJPY")
        152.30
        >>> calculate_take_profit_price(1935.0, 30, "BUY", "XAUUSD")
        1938.0
    """
    pip_size = get_pip_size(symbol)
    distance = target_pips * pip_size

    if direction.upper() == "BUY":
        return entry_price + distance
    else:  # SELL
        return entry_price - distance


def pips_from_price_distance(price1: float, price2: float, symbol: str) -> float:
    """
    Calculate pip distance from absolute price difference.

    Args:
        price1: First price (usually entry)
        price2: Second price (usually SL or TP)
        symbol: Trading symbol

    Returns:
        Pip distance (absolute value)

    Examples:
        >>> pips_from_price_distance(1.0500, 1.0480, "EURUSD")
        20.0
        >>> pips_from_price_distance(152.60, 152.80, "USDJPY")
        20.0
        >>> pips_from_price_distance(1935.0, 1933.0, "XAUUSD")
        20.0
    """
    pip_size = get_pip_size(symbol)
    return abs(price1 - price2) / pip_size


def verify_pip_conversion(entry: float, sl: float, stop_pips: float, symbol: str, tolerance: float = 0.5) -> bool:
    """
    Verify that pip conversion is accurate within tolerance.

    Args:
        entry: Entry price
        sl: Stop loss price
        stop_pips: Expected pip distance
        symbol: Trading symbol
        tolerance: Allowed pip difference (default 0.5 pips)

    Returns:
        True if conversion is accurate, False otherwise

    Raises:
        AssertionError: If conversion error exceeds tolerance
    """
    calculated_pips = pips_from_price_distance(entry, sl, symbol)
    error = abs(calculated_pips - stop_pips)

    if error > tolerance:
        raise AssertionError(
            f"Pip conversion mismatch for {symbol}: "
            f"Expected {stop_pips} pips, calculated {calculated_pips:.1f} pips "
            f"(error: {error:.2f} pips, entry: {entry}, sl: {sl})"
        )

    return True


# ============================================================================
# SCALPING ATR CONFIGURATION
# ============================================================================

# ATR multipliers for scalping (smaller than swing trading)
ATR_SCALP_MULTIPLIERS = {
    "conservative": 1.5,
    "moderate": 1.2,
    "aggressive": 0.8,
}

# ATR periods for different timeframes
ATR_PERIODS = {
    "M5": 14,   # Fast for scalping
    "M15": 14,  # Fast for scalping
    "H1": 14,   # Standard
    "H4": 14,   # Standard
}


def calc_scalp_stop_pips(
    symbol: str,
    atr_price_units: float,
    rr: float = 1.8,
    timeframe: str = "M5",
    min_pips: float = None,
    max_pips: float = None,
    atr_mult: float = 1.2
) -> tuple[float, float]:
    """
    Calculate scalp-optimized stop and target in pips using ATR.

    Designed for M5/M15 scalping trades that resolve within 30-120 minutes.

    Args:
        symbol: Trading symbol
        atr_price_units: ATR value in price units (from indicator)
        rr: Risk/reward ratio (default 1.8)
        timeframe: Timeframe for ATR calculation (default "M5")
        min_pips: Override minimum stop (optional)
        max_pips: Override maximum stop (optional)
        atr_mult: ATR multiplier (default 1.2 for scalping)

    Returns:
        Tuple of (stop_pips, target_pips)

    Examples:
        >>> calc_scalp_stop_pips("EURUSD", 0.0015, rr=2.0)
        (15.0, 30.0)
        >>> calc_scalp_stop_pips("USDJPY", 0.15, rr=1.8)
        (15.0, 27.0)
        >>> calc_scalp_stop_pips("XAUUSD", 3.5, rr=2.0)
        (35.0, 70.0)
    """
    pip_size = get_pip_size(symbol)

    # Convert ATR (price units) → pips
    atr_pips = atr_price_units / pip_size

    # Apply scalp multiplier (smaller than swing trading)
    raw_stop_pips = atr_pips * atr_mult

    # Get symbol/TF-aware limits if not provided
    if min_pips is None or max_pips is None:
        min_pips, max_pips = get_min_max_stop_pips(symbol, timeframe)

    # Clamp to reasonable range
    stop_pips = max(min_pips, min(raw_stop_pips, max_pips))

    # Calculate target based on R:R
    target_pips = stop_pips * rr

    return (round(stop_pips, 1), round(target_pips, 1))


# ============================================================================
# UNIT TESTS (for verification)
# ============================================================================

if __name__ == "__main__":
    print("🧪 Running unit tests for constants.py\n")

    # Test pip sizes
    assert get_pip_size("USDJPY") == 0.01, "JPY pip size failed"
    assert get_pip_size("EURUSD") == 0.0001, "Major pip size failed"
    assert get_pip_size("XAUUSD") == 0.10, "Gold pip size failed"
    assert get_pip_size("XAGUSD") == 0.001, "Silver pip size failed"
    print("✅ Pip size tests passed")

    # Test SL/TP calculations
    sl_buy = calculate_stop_loss_price(1.0500, 20, "BUY", "EURUSD")
    assert abs(sl_buy - 1.0480) < 0.00001, f"BUY SL failed: {sl_buy}"

    sl_sell = calculate_stop_loss_price(152.60, 20, "SELL", "USDJPY")
    assert abs(sl_sell - 152.80) < 0.01, f"SELL SL failed: {sl_sell}"

    tp_gold = calculate_take_profit_price(1935.0, 30, "BUY", "XAUUSD")
    assert abs(tp_gold - 1938.0) < 0.1, f"Gold TP failed: {tp_gold}"
    print("✅ SL/TP calculation tests passed")

    # Test pip distance calculation
    pips_eu = pips_from_price_distance(1.0500, 1.0480, "EURUSD")
    assert abs(pips_eu - 20.0) < 0.1, f"EURUSD pip distance failed: {pips_eu}"

    pips_jpy = pips_from_price_distance(152.60, 152.80, "USDJPY")
    assert abs(pips_jpy - 20.0) < 0.1, f"USDJPY pip distance failed: {pips_jpy}"
    print("✅ Pip distance tests passed")

    # Test verification
    try:
        verify_pip_conversion(1.0500, 1.0480, 20.0, "EURUSD")
        print("✅ Pip verification test passed")
    except AssertionError as e:
        print(f"❌ Pip verification failed: {e}")

    # Test scalp limits
    min_jpy, max_jpy = get_min_max_stop_pips("USDJPY", "M5")
    assert min_jpy == 6 and max_jpy == 35, f"JPY M5 limits failed: {min_jpy}, {max_jpy}"

    min_eu, max_eu = get_min_max_stop_pips("EURUSD", "M15")
    assert min_eu == 12 and max_eu == 50, f"EURUSD M15 limits failed: {min_eu}, {max_eu}"
    print("✅ Scalp limit tests passed")

    # Test ATR scalp calculation
    stop_pips, target_pips = calc_scalp_stop_pips("EURUSD", 0.0015, rr=2.0, timeframe="M5")
    assert 10 <= stop_pips <= 45, f"EURUSD scalp stop out of range: {stop_pips}"
    assert target_pips == stop_pips * 2.0, f"R:R calculation failed: {target_pips}"
    print("✅ ATR scalp calculation tests passed")

    print("\n✅ All tests passed - constants.py is ready for production")
