# src/bitten_core/open_sanitize.py
EXIT_KEYS = {
    "tp", "tp_price", "tp1", "tp2", "tp3", "targets",
    "trail", "trailing", "trail_pips", "trail_points",
    "rr", "rr_target", "exit_profile"
}

def sanitize_open(payload: dict) -> dict:
    """Keep TP/SL for proper trade execution - DO NOT strip them"""
    if not isinstance(payload, dict):
        return payload
    clean = dict(payload)
    # KEEP TP and SL - they are essential for trade execution
    # Removing them causes trades to execute without proper exits
    # The EA needs these values to manage the position
    return clean