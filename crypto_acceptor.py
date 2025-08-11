# crypto_acceptor.py (tighter for 10/day)
import time, random, math
from crypto_session_clock import current_session, hours_left_active

H, L = 90, 78          # stricter gates (was 88, 74)
K, S0 = 0.22, 82       # mid-band probability curve
DUP_LOOKBACK = 15*60   # 15 minutes (was 12)
APLUS_DUP_WINDOW = 7*60 # was 5 minutes

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

# Stricter pacing favoring EU/US sessions
BUCKETS = {
    'ASIA':      TokenBucket(0.2, burst=1),  # was 1.0
    'EU':        TokenBucket(0.6, burst=2),  # was 2.0
    'US':        TokenBucket(0.9, burst=2),  # was 2.5
    'GRAVEYARD': TokenBucket(0.1, burst=1),  # was 0.5
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

def accept(sig:dict, count_24h:int)->bool:
    """
    sig requires: ['final_score','ev','pattern','direction','timestamp_ts','basket']
    """
    now_ts = sig.get('timestamp_ts', time.time())
    score = int(sig['final_score'])
    ev    = float(sig.get('ev', 0.0))
    rarity_q = float(sig.get('rarity_qtile', 0.5))
    sess = current_session()
    bucket = BUCKETS[sess]

    # Target 10/day instead of 25/day
    target_mid = 10
    quota_left = max(0, target_mid - count_24h)
    need_rate = quota_left / hours_left_active()
    behind = need_rate > 1.6  # was 1.8
    ahead  = need_rate < 0.6  # was 0.8
    prob_scale = 1.25 if behind else (0.80 if ahead else 1.00)

    # Stronger A+ overrides
    high_override = (ev >= 0.25) or (rarity_q >= 0.80)  # was 0.22 and 0.75
    if score >= H or high_override:
        key = _dup_key(sig)
        last = _recent_fingerprint.get(key, 0)
        if (now_ts - last) >= APLUS_DUP_WINDOW:
            _mark(sig, now_ts)
            return True

    if score < L:
        if behind and bucket.take() and random.random() < 0.08:  # was 0.12
            if not _is_duplicate(sig, now_ts):
                _mark(sig, now_ts)
                return True
        return False

    p = min(0.98, _logistic_p(score) * prob_scale)
    if random.random() < p and bucket.take():
        if (not _is_duplicate(sig, now_ts)) or score >= (H-2):
            _mark(sig, now_ts)
            return True
    return False