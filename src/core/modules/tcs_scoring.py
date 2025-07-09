# tcs_scoring.py
# Trade Confidence Score engine (0–100) - Wrapper for TCS++ Engine

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from core.tcs_engine import score_tcs, classify_trade

def calculate_tcs(trade_context):
    """
    Returns a TCS (Trade Confidence Score) from 0 to 100
    based on provided confluence factors in trade_context.
    Uses the new TCS++ engine for comprehensive scoring.
    """
    # Map trade_context to signal_data format expected by TCS++ engine
    signal_data = {
        'rsi': trade_context.get('rsi', 50),
        'volume_ratio': trade_context.get('volume_ratio', 1.0),
        'atr': trade_context.get('atr', 20),
        'spread_ratio': trade_context.get('spread_ratio', 1.0),
        'session': trade_context.get('session', 'unknown'),
        'rr': trade_context.get('risk_reward', 2.0),
        'trend_clarity': trade_context.get('trend_clarity', 0.5),
        'sr_quality': trade_context.get('sr_quality', 0.5),
        'pattern_complete': trade_context.get('pattern_complete', False),
        'M15_aligned': trade_context.get('M15_aligned', False),
        'H1_aligned': trade_context.get('H1_aligned', False),
        'H4_aligned': trade_context.get('H4_aligned', False),
        'D1_aligned': trade_context.get('D1_aligned', False),
        'macd_aligned': trade_context.get('macd_aligned', False),
        'liquidity_grab': trade_context.get('liquidity_grab', False),
        'ai_sentiment_bonus': trade_context.get('ai_sentiment_bonus', 0)
    }
    
    # Calculate TCS using the new engine
    score = score_tcs(signal_data)
    
    # Classify the trade
    trade_type = classify_trade(score, signal_data.get('rr', 2.0), signal_data)
    
    # Store additional info in trade_context
    trade_context['tcs_score'] = score
    trade_context['trade_classification'] = trade_type
    trade_context['tcs_breakdown'] = signal_data.get('tcs_breakdown', {})
    
    return score

def get_trade_classification(tcs_score, risk_reward, signal_data=None):
    """
    Get trade classification based on TCS score and risk/reward
    """
    return classify_trade(tcs_score, risk_reward, signal_data)

if __name__ == "__main__":
    # Test with comprehensive sample data
    sample = {
        "rsi": 30,
        "volume_ratio": 1.8,
        "atr": 25,
        "spread_ratio": 1.2,
        "session": "london",
        "risk_reward": 3.5,
        "trend_clarity": 0.8,
        "sr_quality": 0.9,
        "pattern_complete": True,
        "H1_aligned": True,
        "H4_aligned": True,
        "macd_aligned": True,
        "liquidity_grab": True,
        "ai_sentiment_bonus": 5
    }
    
    score = calculate_tcs(sample)
    classification = sample.get('trade_classification', 'unknown')
    breakdown = sample.get('tcs_breakdown', {})
    
    print(f"TCS Score: {score}")
    print(f"Trade Classification: {classification}")
    print(f"Score Breakdown: {breakdown}")
