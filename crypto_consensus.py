# crypto_consensus.py
import statistics
from typing import Dict, Tuple

class Consensus:
    def __init__(self, mid: float, spread_bps: float, depth_usd: float, conf: float, nx: int):
        self.mid = mid
        self.spread_bps = spread_bps  # median L1 spread in basis points
        self.depth_usd = depth_usd    # approx depth at ±5bps
        self.conf = conf              # fraction of agreeing venues
        self.nx = nx                  # venues used

def compute_consensus(quotes: Dict[str, dict]) -> Consensus:
    """
    quotes[venue] = {"bid":..., "ask":..., "mid":..., "spread_bps":..., "depth5bps_usd":...}
    Outlier rejection: 2σ on mid prices.
    """
    mids = [q["mid"] for q in quotes.values() if "mid" in q]
    if not mids: return Consensus(0.0, 0.0, 0.0, 0.0, 0)
    med = statistics.median(mids)
    stdev = statistics.pstdev(mids) if len(mids) > 1 else 0.0
    keep = {}
    for v,q in quotes.items():
        if stdev == 0 or abs(q["mid"] - med) <= 2.0*stdev:
            keep[v] = q
    mids_k   = [q["mid"] for q in keep.values()]
    spreads  = [q["spread_bps"] for q in keep.values() if "spread_bps" in q]
    depths   = [q.get("depth5bps_usd", 0.0) for q in keep.values()]
    if not mids_k: return Consensus(0.0,0.0,0.0,0.0,0)
    mid = statistics.median(mids_k)
    spread_bps = statistics.median(spreads) if spreads else 0.0
    depth_usd  = statistics.median(depths) if depths else 0.0
    conf = len(keep)/max(1,len(quotes))
    return Consensus(mid, spread_bps, depth_usd, conf, len(keep))