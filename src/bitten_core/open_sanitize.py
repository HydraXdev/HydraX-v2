# src/bitten_core/open_sanitize.py
EXIT_KEYS = {
    "tp", "tp_price", "tp1", "tp2", "tp3", "targets",
    "trail", "trailing", "trail_pips", "trail_points",
    "rr", "rr_target", "exit_profile"
}

def sanitize_open(payload: dict) -> dict:
    """Remove any client-provided exits; tiered exit manager will take over."""
    if not isinstance(payload, dict):
        return payload
    clean = dict(payload)
    for k in list(clean.keys()):
        if k.lower() in EXIT_KEYS:
            clean.pop(k, None)
    # make it explicit we expect server-managed exits
    clean["managed_exits"] = True
    # force TP to None so EA doesn't set one
    clean["tp"] = None
    return clean