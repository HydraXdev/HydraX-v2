# liquidation_feed.py
# Capture liquidation clusters (from venue websockets if available); stub otherwise.
from collections import defaultdict, deque
import time

class LiquidationFeed:
    def __init__(self, window_sec=300):
        self.window = window_sec
        self.events = defaultdict(lambda: deque())
    def record(self, symbol: str, side: str, notional_usd: float):
        now = time.time()
        self.events[symbol].append((now, side, notional_usd))
        self._prune(symbol, now)
    def cluster_stats(self, symbol: str):
        now = time.time()
        self._prune(symbol, now)
        q = self.events[symbol]
        total = sum(n for (_,_,n) in q)
        buys = sum(n for (_,s,n) in q if s == "BUY")
        sells= sum(n for (_,s,n) in q if s == "SELL")
        return {"total": total, "buy": buys, "sell": sells, "count": len(q)}
    def _prune(self, symbol, now):
        q = self.events[symbol]
        while q and now - q[0][0] > self.window:
            q.popleft()