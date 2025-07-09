# Test runner for TCS++ Engine

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.tcs_engine import score_tcs, classify_trade

# Test Case 1: Elite Hammer Setup
print("=== Test Case 1: Elite Hammer Setup ===")
elite_signal = {
    "trend_clarity": 0.9,
    "sr_quality": 0.95,
    "pattern_complete": True,
    "M15_aligned": True,
    "H1_aligned": True,
    "H4_aligned": True,
    "D1_aligned": True,
    "rsi": 32,
    "macd_aligned": True,
    "volume_ratio": 1.8,
    "atr": 35,
    "spread_ratio": 1.2,
    "volatility_stable": True,
    "session": "london",
    "liquidity_grab": True,
    "near_institutional_level": True,
    "rr": 4.2,
    "ai_sentiment_bonus": 8
}

score = score_tcs(elite_signal)
trade_type = classify_trade(score, elite_signal["rr"], elite_signal)
print(f"TCS Score: {score}")
print(f"Trade Type: {trade_type}")
print(f"Score Breakdown: {elite_signal.get('tcs_breakdown', {})}")
print()

# Test Case 2: Shadow Strike Setup
print("=== Test Case 2: Shadow Strike Setup ===")
shadow_signal = {
    "trend_clarity": 0.75,
    "sr_quality": 0.85,
    "pattern_complete": True,
    "H1_aligned": True,
    "H4_aligned": True,
    "D1_aligned": True,
    "rsi": 35,
    "macd_aligned": True,
    "volume_ratio": 1.6,
    "atr": 30,
    "spread_ratio": 1.4,
    "volatility_stable": True,
    "session": "new_york",
    "liquidity_grab": True,
    "rr": 3.2,
    "ai_sentiment_bonus": 5
}

score = score_tcs(shadow_signal)
trade_type = classify_trade(score, shadow_signal["rr"], shadow_signal)
print(f"TCS Score: {score}")
print(f"Trade Type: {trade_type}")
print(f"Score Breakdown: {shadow_signal.get('tcs_breakdown', {})}")
print()

# Test Case 3: Scalp Setup
print("=== Test Case 3: Scalp Setup ===")
scalp_signal = {
    "trend_clarity": 0.65,
    "sr_quality": 0.75,
    "pattern_forming": True,
    "H1_aligned": True,
    "H4_aligned": True,
    "rsi": 40,
    "macd_aligned": True,
    "volume_ratio": 1.4,
    "atr": 25,
    "spread_ratio": 1.3,
    "volatility_stable": True,
    "session": "london",
    "stop_hunt_detected": True,
    "rr": 2.5,
    "ai_sentiment_bonus": 3
}

score = score_tcs(scalp_signal)
trade_type = classify_trade(score, scalp_signal["rr"], scalp_signal)
print(f"TCS Score: {score}")
print(f"Trade Type: {trade_type}")
print(f"Score Breakdown: {scalp_signal.get('tcs_breakdown', {})}")
print()

# Test Case 4: Poor Setup (No Trade)
print("=== Test Case 4: Poor Setup ===")
poor_signal = {
    "trend_clarity": 0.3,
    "sr_quality": 0.4,
    "rsi": 50,
    "volume_ratio": 0.8,
    "atr": 12,
    "spread_ratio": 2.5,
    "volatility_stable": False,
    "session": "dead_zone",
    "rr": 1.5,
    "ai_sentiment_bonus": 0
}

score = score_tcs(poor_signal)
trade_type = classify_trade(score, poor_signal["rr"], poor_signal)
print(f"TCS Score: {score}")
print(f"Trade Type: {trade_type}")
print(f"Score Breakdown: {poor_signal.get('tcs_breakdown', {})}")
print()

# Test Case 5: Proper Scalp Setup
print("=== Test Case 5: Proper Scalp Setup ===")
proper_scalp_signal = {
    "trend_clarity": 0.75,
    "sr_quality": 0.8,
    "pattern_complete": True,
    "M15_aligned": True,
    "H1_aligned": True,
    "H4_aligned": True,
    "rsi": 30,
    "macd_aligned": True,
    "volume_ratio": 1.4,
    "atr": 28,
    "spread_ratio": 1.3,
    "volatility_stable": True,
    "session": "london",  # Session-optimized scalp
    "liquidity_grab": True,
    "rr": 2.5,
    "ai_sentiment_bonus": 4
}

score = score_tcs(proper_scalp_signal)
trade_type = classify_trade(score, proper_scalp_signal["rr"], proper_scalp_signal)
print(f"TCS Score: {score}")
print(f"Trade Type: {trade_type}")
print(f"Score Breakdown: {proper_scalp_signal.get('tcs_breakdown', {})}")
