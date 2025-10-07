# Test runner for TCS Engine

from core.tcs_engine import classify_trade, score_tcs

sample = {
    "structure": True,
    "tf_alignment": True,
    "momentum": True,
    "volatility": True,
    "session": "NY",
    "liquidity_zone": True,
    "rr": 3.8,
    "ai_sentiment_bonus": 6,
}

score = score_tcs(sample)
trade_type = classify_trade(score, sample["rr"])
print(f"TCS Score: {score}, Trade Type: {trade_type}")
