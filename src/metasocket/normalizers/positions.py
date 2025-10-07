"""
normalizers/positions.py - Position event normalization mirroring TypeScript logic
Maps MetaSocket position events to normalized v1 schema with defensive parsing
"""

import time
from typing import Dict, Any, Set, Optional, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

def normalize_trade_event(ev: Any) -> Dict[str, Any]:
    """
    Normalize MetaSocket position event to v1 schema
    Mirrors TypeScript normalizeTradeEvent() function exactly

    Args:
        ev: Broker MetaSocket event with position data

    Returns:
        Normalized position event dict
    """
    # Defensive state mapping
    state = None
    if hasattr(ev, "state") and ev.state:
        state = str(ev.state).upper()
    elif isinstance(ev, dict) and ev.get("state"):
        state = str(ev["state"]).upper()

    # Reason detection with defensive parsing
    reason = "other"
    raw_reason = None

    # Extract reason from various possible formats
    if hasattr(ev, "reason") and ev.reason:
        raw_reason = ev.reason
    elif isinstance(ev, dict) and ev.get("reason"):
        raw_reason = ev["reason"]

    if raw_reason:
        r = str(raw_reason).lower()
        if "sl" in r:
            reason = "sl"
        elif "tp" in r:
            reason = "tp"
        elif "manual" in r:
            reason = "manual"

    # Extract ticket with fallback
    ticket = None
    if hasattr(ev, "ticket"):
        ticket = str(ev.ticket)
    elif isinstance(ev, dict) and ev.get("ticket"):
        ticket = str(ev["ticket"])
    else:
        ticket = "unknown"

    # Extract symbol
    symbol = None
    if hasattr(ev, "symbol"):
        symbol = ev.symbol
    elif isinstance(ev, dict):
        symbol = ev.get("symbol")

    # Extract side with defensive uppercase
    side = None
    if hasattr(ev, "side") and ev.side:
        side = str(ev.side).upper()
    elif isinstance(ev, dict) and ev.get("side"):
        side = str(ev["side"]).upper()

    # Extract numeric values with defensive conversion
    def safe_float(value) -> Optional[float]:
        """Safely convert to float, return None if invalid"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # Price extraction
    price = 0.0
    if hasattr(ev, "price"):
        price = safe_float(ev.price) or 0.0
    elif isinstance(ev, dict):
        price = safe_float(ev.get("price")) or 0.0

    # Volume extraction
    volume = 0.0
    if hasattr(ev, "volume"):
        volume = safe_float(ev.volume) or 0.0
    elif isinstance(ev, dict):
        volume = safe_float(ev.get("volume")) or 0.0

    # SL/TP extraction (can be null)
    sl = None
    tp = None

    if hasattr(ev, "sl"):
        sl = safe_float(ev.sl)
    elif isinstance(ev, dict) and "sl" in ev:
        sl = safe_float(ev["sl"])

    if hasattr(ev, "tp"):
        tp = safe_float(ev.tp)
    elif isinstance(ev, dict) and "tp" in ev:
        tp = safe_float(ev["tp"])

    # Timestamp extraction with fallback to current time
    ts_epoch_ms = int(time.time() * 1000)  # Default fallback

    if hasattr(ev, "ts_epoch_ms"):
        try:
            ts_epoch_ms = int(float(ev.ts_epoch_ms))
        except (ValueError, TypeError):
            pass
    elif isinstance(ev, dict) and ev.get("ts_epoch_ms"):
        try:
            ts_epoch_ms = int(float(ev["ts_epoch_ms"]))
        except (ValueError, TypeError):
            pass

    return {
        "ticket": ticket,
        "symbol": symbol,
        "side": side,           # "BUY"|"SELL"
        "state": state,         # "OPEN"|"CLOSE"
        "reason": reason,       # "sl"|"tp"|"manual"|"other"
        "price": price,
        "volume": volume,
        "sl": sl,
        "tp": tp,
        "ts_epoch_ms": ts_epoch_ms,
        "src": "metasocket"
    }

def idempotency_key(pe: Dict[str, Any]) -> str:
    """
    Generate idempotency key for position event
    Mirrors TypeScript idempotencyKey() function exactly

    Args:
        pe: Position event dictionary

    Returns:
        Unique key string for deduplication
    """
    ticket = pe.get("ticket", "unknown")
    state = pe.get("state", "unknown")
    ts_epoch_ms = pe.get("ts_epoch_ms", 0)

    return f"{ticket}::{state}::{ts_epoch_ms}"
