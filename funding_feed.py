# funding_feed.py
# Provide latest perp funding rates & recent flips; stub if no API yet.
from collections import defaultdict
import time

class FundingFeed:
    def __init__(self):
        self.data = defaultdict(lambda: {"rate": 0.0, "last_flip_ts": 0})
    def update(self, symbol: str, rate: float):
        now = time.time()
        prev = self.data[symbol]["rate"]
        if (prev >= 0 and rate < 0) or (prev <= 0 and rate > 0):
            self.data[symbol]["last_flip_ts"] = now
        self.data[symbol]["rate"] = rate
    def get(self, symbol: str):
        return self.data[symbol]