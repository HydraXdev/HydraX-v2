#!/usr/bin/env python3
"""
Simple TCS++ Engine Test
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.tcs_engine import score_tcs, classify_trade

def test_tcs_engine():
    """Test the TCS++ engine with various scenarios"""
    
    test_scenarios = [
        {
            "name": "Elite Hammer Setup (95+ TCS)",
            "data": {
                "trend_clarity": 0.95,
                "sr_quality": 0.95,
                "pattern_complete": True,
                "M15_aligned": True,
                "H1_aligned": True,
                "H4_aligned": True,
                "D1_aligned": True,
                "rsi": 28,
                "macd_aligned": True,
                "volume_ratio": 2.0,
                "atr": 40,
                "spread_ratio": 1.1,
                "volatility_stable": True,
                "session": "london",
                "liquidity_grab": True,
                "stop_hunt_detected": True,
                "near_institutional_level": True,
                "rr": 4.5,
                "ai_sentiment_bonus": 9
            }
        },
        {
            "name": "Shadow Strike Setup (84-93 TCS)",
            "data": {
                "trend_clarity": 0.8,
                "sr_quality": 0.85,
                "pattern_complete": True,
                "H1_aligned": True,
                "H4_aligned": True,
                "D1_aligned": True,
                "rsi": 32,
                "macd_aligned": True,
                "volume_ratio": 1.6,
                "atr": 30,
                "spread_ratio": 1.3,
                "volatility_stable": True,
                "session": "new_york",
                "liquidity_grab": True,
                "rr": 3.5,
                "ai_sentiment_bonus": 5
            }
        },
        {
            "name": "Scalp Setup (75-83 TCS)",
            "data": {
                "trend_clarity": 0.7,
                "sr_quality": 0.75,
                "pattern_complete": True,
                "H1_aligned": True,
                "H4_aligned": True,
                "rsi": 35,
                "macd_aligned": True,
                "volume_ratio": 1.3,
                "atr": 25,
                "spread_ratio": 1.4,
                "volatility_stable": True,
                "session": "london",
                "liquidity_grab": False,
                "rr": 2.5,
                "ai_sentiment_bonus": 3
            }
        },
        {
            "name": "Watchlist Setup (65-74 TCS)",
            "data": {
                "trend_clarity": 0.6,
                "sr_quality": 0.65,
                "pattern_forming": True,
                "H4_aligned": True,
                "rsi": 45,
                "macd_aligned": False,
                "volume_ratio": 1.1,
                "atr": 20,
                "spread_ratio": 1.5,
                "volatility_stable": True,
                "session": "overlap",
                "rr": 2.0,
                "ai_sentiment_bonus": 2
            }
        }
    ]
    
    print("TCS++ Engine Test Results")
    print("========================\n")
    
    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 50)
        
        # Calculate TCS score
        score = score_tcs(scenario['data'])
        
        # Get trade classification
        trade_type = classify_trade(score, scenario['data']['rr'], scenario['data'])
        
        # Get breakdown
        breakdown = scenario['data'].get('tcs_breakdown', {})
        
        print(f"TCS Score: {score}%")
        print(f"Trade Classification: {trade_type}")
        print(f"Risk/Reward: {scenario['data']['rr']}")
        print(f"Session: {scenario['data']['session']}")
        print("\nScore Breakdown:")
        for component, points in breakdown.items():
            print(f"  {component}: {points} points")
        
        # Determine if trade would be executed based on tier thresholds
        if score >= 94:
            print("\nExecution: HAMMER - Elite setup, maximum confidence")
        elif score >= 84:
            print("\nExecution: SHADOW STRIKE - High probability trade")
        elif score >= 75:
            print("\nExecution: SCALP - Quick opportunity")
        elif score >= 65:
            print("\nExecution: WATCHLIST - Monitor but don't execute")
        else:
            print("\nExecution: NO TRADE - Below minimum threshold")
        
        print("\n")

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("Edge Case Testing")
    print("================\n")
    
    # Test with minimal data
    minimal_data = {
        "rr": 2.0
    }
    
    score = score_tcs(minimal_data)
    trade_type = classify_trade(score, minimal_data['rr'], minimal_data)
    
    print(f"Minimal data test:")
    print(f"  TCS Score: {score}%")
    print(f"  Trade Type: {trade_type}")
    print()
    
    # Test with perfect conditions
    perfect_data = {
        "trend_clarity": 1.0,
        "sr_quality": 1.0,
        "pattern_complete": True,
        "M15_aligned": True,
        "H1_aligned": True,
        "H4_aligned": True,
        "D1_aligned": True,
        "rsi": 30,
        "macd_aligned": True,
        "volume_ratio": 2.5,
        "atr": 35,
        "spread_ratio": 1.0,
        "volatility_stable": True,
        "session": "london",
        "liquidity_grab": True,
        "stop_hunt_detected": True,
        "near_institutional_level": True,
        "rr": 5.0,
        "ai_sentiment_bonus": 10
    }
    
    score = score_tcs(perfect_data)
    trade_type = classify_trade(score, perfect_data['rr'], perfect_data)
    
    print(f"Perfect conditions test:")
    print(f"  TCS Score: {score}% (should be capped at 100)")
    print(f"  Trade Type: {trade_type}")
    print()

if __name__ == "__main__":
    test_tcs_engine()
    test_edge_cases()
    print("All tests completed successfully!")