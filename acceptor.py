# acceptor.py
import time, random, math
from session_clock import current_session

# Thresholds - RAISED to reduce signal volume and improve quality
H, L = 88, 75          # High always pass; Low usually reject (was 85/72, now 88/75)
K, S0 = 0.25, 78       # Logistic slope & midpoint for mid-band probability
DUP_LOOKBACK = 15*60   # 15 minutes
APLUS_DUP_WINDOW = 6*60

class TokenBucket:
    def __init__(self, rate_per_hr:float, burst:int):
        self.rate = rate_per_hr/3600.0
        self.tokens = float(burst)
        self.last = time.time()
        self.burst = float(burst)
    def refill(self):
        now = time.time()
        self.tokens = min(self.burst, self.tokens + (now - self.last)*self.rate)
        self.last = now
    def take(self)->bool:
        self.refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

BUCKETS = {
    'LONDON':   TokenBucket(1.0, burst=2),  # Was 2.0/hr, now 1.0/hr
    'NY':       TokenBucket(1.0, burst=2),  # Was 2.0/hr, now 1.0/hr  
    'OVERLAP':  TokenBucket(1.5, burst=2),  # Was 3.0/hr, now 1.5/hr
    'ASIAN':    TokenBucket(0.3, burst=1),  # Was 0.5/hr, now 0.3/hr
}

_recent_fingerprint = {}  # (basket, dir, pattern) -> last_ts

def _logistic_p(score:int)->float:
    return 1.0 / (1.0 + math.exp(-K*(score - S0)))

def _dup_key(sig)->tuple:
    return (sig.get('basket','GEN'), sig['direction'], sig['pattern'])

def _is_duplicate(sig, now_ts)->bool:
    last = _recent_fingerprint.get(_dup_key(sig), 0)
    return (now_ts - last) < DUP_LOOKBACK

def _mark(sig, now_ts):
    _recent_fingerprint[_dup_key(sig)] = now_ts

def accept(sig:dict, count_24h:int, active_hours_left:float)->bool:
    """
    sig: dict with keys ['final_score','ev','pattern','direction','timestamp_ts','basket']
    count_24h: number of published signals in last 24h
    active_hours_left: hours remaining in active sessions today
    """
    now_ts = sig.get('timestamp_ts', time.time())
    score = int(sig['final_score'])
    ev    = float(sig.get('ev', 0.0))
    rarity_q = float(sig.get('rarity_qtile', 0.5))
    sess = current_session()
    bucket = BUCKETS[sess]

    # Pace state
    target_mid = 25
    quota_left = max(0, target_mid - count_24h)
    need_rate = quota_left / max(0.25, active_hours_left)
    behind = need_rate > 1.8
    ahead  = need_rate < 0.8
    prob_scale = 1.20 if behind else (0.85 if ahead else 1.00)

    # Immediate pass: A+ score, strong EV, or rare pattern
    high_override = (ev >= 0.20) or (rarity_q >= 0.75)
    if score >= H or high_override:
        # allow one similar within shorter window for A+
        key = _dup_key(sig)
        last = _recent_fingerprint.get(key, 0)
        if (now_ts - last) >= APLUS_DUP_WINDOW:
            _mark(sig, now_ts)
            return True

    # Low tier: only allow small trickle if behind pace
    if score < L:
        if behind and bucket.take() and random.random() < 0.15:
            if not _is_duplicate(sig, now_ts):
                _mark(sig, now_ts)
                return True
        return False

    # Mid band: probabilistic + token bucket + dup guard
    p = min(0.98, _logistic_p(score) * prob_scale)
    if random.random() < p and bucket.take():
        if (not _is_duplicate(sig, now_ts)) or score >= (H-3):
            _mark(sig, now_ts)
            return True
    return False