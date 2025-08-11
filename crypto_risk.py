# crypto_risk.py
from typing import Tuple
from crypto_session_clock import current_session

# Venue-level spread gates (bps = basis points; 1bp = 0.01%)
SPREAD_GATES_BPS = {
    "BTCUSD": {"ASIA": 2.0, "EU": 1.2, "US": 1.2, "GRAVEYARD": 2.5},  # ~20% tighter
    "ETHUSD": {"ASIA": 3.0, "EU": 1.7, "US": 1.7, "GRAVEYARD": 3.5},  # ~20% tighter
    "XRPUSD": {"ASIA": 7.0, "EU": 4.0, "US": 4.0, "GRAVEYARD": 8.0},   # ~20% tighter
}

# Allowed consensus deviation vs median mid (tight for majors)
CONSENSUS_MAX_DEV_PCT = {"BTCUSD": 0.12, "ETHUSD": 0.18, "XRPUSD": 0.30}  # % tighter

def spread_ok(symbol: str, spread_bps: float) -> bool:
    sess = current_session()
    gate = SPREAD_GATES_BPS.get(symbol, SPREAD_GATES_BPS["BTCUSD"]).get(sess, 3.0)
    return spread_bps <= gate

def consensus_ok(symbol: str, venue_mid: float, cons_mid: float) -> bool:
    if cons_mid <= 0: return True
    dev_pct = abs(venue_mid - cons_mid) / cons_mid * 100.0
    return dev_pct <= CONSENSUS_MAX_DEV_PCT.get(symbol, 0.25)

def est_slippage_cost_bps(depth_usd: float, notional_usd: float) -> float:
    """
    Simple impact proxy: cost ∝ notional / (depth at ±5bps).
    """
    if depth_usd <= 0: return 10.0  # worst case: 10bps
    return min(6.0, 5.0 * (notional_usd / depth_usd))  # cap stricter at 6bps