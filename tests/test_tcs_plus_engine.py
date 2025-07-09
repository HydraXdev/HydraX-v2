"""
Comprehensive Test Suite for TCS++ Engine
Tests scoring accuracy, trade classification, and integration
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tcs_engine import (
    score_tcs, classify_trade, analyze_market_structure,
    check_timeframe_alignment, assess_momentum_strength,
    analyze_volatility_conditions, calculate_session_weight,
    detect_liquidity_patterns, evaluate_risk_reward
)


class TestTCSScoringAccuracy:
    """Test TCS++ scoring accuracy with various market conditions"""
    
    def test_perfect_trade_conditions(self):
        """Test scoring with ideal market conditions (should score 95+)"""
        signal_data = {
            # Market structure
            'trend_clarity': 0.9,
            'sr_quality': 0.95,
            'pattern_complete': True,
            
            # Timeframe alignment
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True,
            
            # Momentum
            'rsi': 70,
            'macd_aligned': True,
            'volume_ratio': 1.8,
            
            # Volatility
            'atr': 35,
            'spread_ratio': 1.2,
            'volatility_stable': True,
            
            # Session
            'session': 'london',
            
            # Liquidity
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': True,
            
            # Risk/Reward
            'rr': 4.5,
            
            # AI bonus
            'ai_sentiment_bonus': 8
        }
        
        score = score_tcs(signal_data)
        
        assert score >= 95, f"Perfect conditions should score 95+, got {score}"
        assert score <= 100, f"Score cannot exceed 100, got {score}"
        assert 'tcs_breakdown' in signal_data
        
        # Verify all components are maxed out
        breakdown = signal_data['tcs_breakdown']
        assert breakdown['structure'] >= 18
        assert breakdown['timeframe_alignment'] == 15
        assert breakdown['momentum'] >= 13
        assert breakdown['volatility'] >= 9
        assert breakdown['session'] == 10
        assert breakdown['liquidity'] == 10
        assert breakdown['risk_reward'] == 10
        assert breakdown['ai_sentiment'] == 8
    
    def test_poor_trade_conditions(self):
        """Test scoring with poor market conditions (should score <50)"""
        signal_data = {
            'trend_clarity': 0.1,
            'sr_quality': 0.2,
            'pattern_complete': False,
            'M15_aligned': False,
            'H1_aligned': False,
            'H4_aligned': False,
            'D1_aligned': False,
            'rsi': 50,
            'macd_aligned': False,
            'volume_ratio': 0.8,
            'atr': 5,
            'spread_ratio': 3.0,
            'volatility_stable': False,
            'session': 'dead_zone',
            'liquidity_grab': False,
            'stop_hunt_detected': False,
            'near_institutional_level': False,
            'rr': 1.0,
            'ai_sentiment_bonus': 0
        }
        
        score = score_tcs(signal_data)
        
        assert score < 50, f"Poor conditions should score <50, got {score}"
        assert score >= 0, f"Score cannot be negative, got {score}"
    
    def test_medium_quality_trade(self):
        """Test scoring with medium quality conditions (should score 60-80)"""
        signal_data = {
            'trend_clarity': 0.6,
            'sr_quality': 0.7,
            'pattern_complete': False,
            'pattern_forming': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': False,
            'D1_aligned': True,
            'rsi': 65,
            'macd_aligned': True,
            'volume_ratio': 1.3,
            'atr': 25,
            'spread_ratio': 1.7,
            'volatility_stable': True,
            'session': 'new_york',
            'liquidity_grab': False,
            'stop_hunt_detected': True,
            'near_institutional_level': False,
            'rr': 2.5,
            'ai_sentiment_bonus': 5
        }
        
        score = score_tcs(signal_data)
        
        assert 60 <= score <= 85, f"Medium conditions should score 60-85, got {score}"
    
    def test_edge_case_values(self):
        """Test scoring with edge case values"""
        # Test with missing values
        signal_data = {}
        score = score_tcs(signal_data)
        assert score >= 0, "Should handle missing values gracefully"
        
        # Test with extreme values
        signal_data = {
            'trend_clarity': 2.0,  # Above max
            'sr_quality': -1.0,    # Below min
            'rsi': 150,            # Above valid range
            'volume_ratio': 0,     # Zero volume
            'atr': 1000,           # Extreme volatility
            'rr': 0.5,             # Very poor RR
            'ai_sentiment_bonus': 20  # Above cap
        }
        
        score = score_tcs(signal_data)
        assert 0 <= score <= 100, f"Score must be in valid range, got {score}"
        assert signal_data['tcs_breakdown']['ai_sentiment'] == 10, "AI bonus should be capped at 10"


class TestTradeClassification:
    """Test trade classification logic"""
    
    def test_hammer_classification(self):
        """Test hammer trade classification"""
        # Basic hammer
        trade_type = classify_trade(95, 4.0)
        assert trade_type == "hammer"
        
        # Elite hammer with extra data
        signal_data = {
            'momentum_strength': 0.9,
            'structure_quality': 0.95
        }
        trade_type = classify_trade(96, 4.0, signal_data)
        assert trade_type == "hammer_elite"
        
        # Just below hammer threshold
        trade_type = classify_trade(93, 4.0)
        assert trade_type != "hammer"
    
    def test_shadow_strike_classification(self):
        """Test shadow strike classification"""
        # Basic shadow strike
        trade_type = classify_trade(87, 2.5)
        assert trade_type == "shadow_strike"
        
        # Premium shadow strike
        trade_type = classify_trade(90, 3.5)
        assert trade_type == "shadow_strike_premium"
        
        # Edge cases
        trade_type = classify_trade(84, 2.0)
        assert trade_type == "shadow_strike"
        
        trade_type = classify_trade(83, 3.0)
        assert trade_type != "shadow_strike"
    
    def test_scalp_classification(self):
        """Test scalp trade classification"""
        # Basic scalp
        trade_type = classify_trade(78, 1.5)
        assert trade_type == "scalp"
        
        # Session-optimized scalp
        signal_data = {'session': 'london'}
        trade_type = classify_trade(80, 2.0, signal_data)
        assert trade_type == "scalp_session"
        
        # Another session
        signal_data = {'session': 'new_york'}
        trade_type = classify_trade(77, 1.8, signal_data)
        assert trade_type == "scalp_session"
        
        # Non-optimal session
        signal_data = {'session': 'tokyo'}
        trade_type = classify_trade(79, 1.5, signal_data)
        assert trade_type == "scalp"
    
    def test_watchlist_and_no_trade(self):
        """Test watchlist and no-trade classifications"""
        # Watchlist
        trade_type = classify_trade(70, 2.0)
        assert trade_type == "watchlist"
        
        # No trade
        trade_type = classify_trade(60, 1.5)
        assert trade_type == "none"
        
        trade_type = classify_trade(30, 0.8)
        assert trade_type == "none"
    
    def test_classification_boundaries(self):
        """Test exact boundary conditions"""
        # Test exact boundaries
        assert classify_trade(94, 3.5) == "hammer"
        assert classify_trade(93, 3.5) == "shadow_strike_premium"
        assert classify_trade(84, 2.0) == "shadow_strike"
        assert classify_trade(83, 2.0) == "scalp"
        assert classify_trade(75, 1.5) == "scalp"
        assert classify_trade(74, 1.5) == "watchlist"
        assert classify_trade(65, 1.5) == "watchlist"
        assert classify_trade(64, 1.5) == "none"


class TestComponentFunctions:
    """Test individual scoring component functions"""
    
    def test_market_structure_analysis(self):
        """Test market structure scoring"""
        # Perfect structure
        signal_data = {
            'trend_clarity': 0.9,
            'sr_quality': 0.9,
            'pattern_complete': True
        }
        score = analyze_market_structure(signal_data)
        assert score == 20, f"Perfect structure should score 20, got {score}"
        assert signal_data['structure_quality'] == 1.0
        
        # Medium structure
        signal_data = {
            'trend_clarity': 0.5,
            'sr_quality': 0.6,
            'pattern_forming': True
        }
        score = analyze_market_structure(signal_data)
        assert 10 <= score <= 15
        
        # Poor structure
        signal_data = {
            'trend_clarity': 0.2,
            'sr_quality': 0.3
        }
        score = analyze_market_structure(signal_data)
        assert score < 10
    
    def test_timeframe_alignment(self):
        """Test timeframe alignment scoring"""
        # Perfect alignment
        signal_data = {
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True
        }
        score = check_timeframe_alignment(signal_data)
        assert score == 15, "Perfect alignment should score 15"
        
        # Partial alignment
        signal_data = {
            'M15_aligned': False,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': False
        }
        score = check_timeframe_alignment(signal_data)
        assert score == 9, "Should score based on weighted timeframes"
        
        # No alignment
        signal_data = {}
        score = check_timeframe_alignment(signal_data)
        assert score == 0
    
    def test_momentum_assessment(self):
        """Test momentum scoring"""
        # Strong bullish momentum
        signal_data = {
            'rsi': 70,
            'macd_aligned': True,
            'volume_ratio': 2.0
        }
        score = assess_momentum_strength(signal_data)
        assert score >= 13
        assert signal_data['momentum_strength'] > 0.8
        
        # Strong bearish momentum
        signal_data = {
            'rsi': 30,
            'macd_aligned': True,
            'volume_ratio': 1.8
        }
        score = assess_momentum_strength(signal_data)
        assert score >= 13
        
        # Weak momentum
        signal_data = {
            'rsi': 50,
            'macd_aligned': False,
            'volume_ratio': 0.9
        }
        score = assess_momentum_strength(signal_data)
        assert score < 5
    
    def test_volatility_analysis(self):
        """Test volatility condition scoring"""
        # Optimal volatility
        signal_data = {
            'atr': 30,
            'spread_ratio': 1.2,
            'volatility_stable': True
        }
        score = analyze_volatility_conditions(signal_data)
        assert score == 10
        
        # High volatility
        signal_data = {
            'atr': 100,
            'spread_ratio': 2.5,
            'volatility_stable': False
        }
        score = analyze_volatility_conditions(signal_data)
        assert score < 5
        
        # Low volatility
        signal_data = {
            'atr': 5,
            'spread_ratio': 1.0,
            'volatility_stable': True
        }
        score = analyze_volatility_conditions(signal_data)
        assert score < 5
    
    def test_session_weight(self):
        """Test session-based scoring"""
        sessions = {
            'london': 10,
            'new_york': 9,
            'overlap': 8,
            'tokyo': 6,
            'sydney': 5,
            'dead_zone': 2,
            'unknown': 0
        }
        
        for session, expected_score in sessions.items():
            signal_data = {'session': session}
            score = calculate_session_weight(signal_data)
            assert score == expected_score, f"Session {session} should score {expected_score}"
    
    def test_liquidity_patterns(self):
        """Test liquidity pattern detection scoring"""
        # All patterns detected
        signal_data = {
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': True
        }
        score = detect_liquidity_patterns(signal_data)
        assert score == 10
        
        # Some patterns
        signal_data = {
            'liquidity_grab': True,
            'stop_hunt_detected': False,
            'near_institutional_level': True
        }
        score = detect_liquidity_patterns(signal_data)
        assert score == 7
        
        # No patterns
        signal_data = {}
        score = detect_liquidity_patterns(signal_data)
        assert score == 0
    
    def test_risk_reward_evaluation(self):
        """Test risk/reward scoring"""
        rr_tests = [
            (5.0, 10),
            (4.0, 10),
            (3.5, 9),
            (3.0, 8),
            (2.5, 6),
            (2.0, 4),
            (1.5, 2),
            (1.0, 0),
            (0.5, 0)
        ]
        
        for rr, expected_score in rr_tests:
            signal_data = {'rr': rr}
            score = evaluate_risk_reward(signal_data)
            assert score == expected_score, f"RR {rr} should score {expected_score}"


class TestIntegrationScenarios:
    """Test realistic trading scenarios"""
    
    def test_london_session_momentum_trade(self):
        """Test typical London session momentum setup"""
        signal_data = {
            'trend_clarity': 0.8,
            'sr_quality': 0.85,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': False,
            'rsi': 68,
            'macd_aligned': True,
            'volume_ratio': 1.6,
            'atr': 40,
            'spread_ratio': 1.3,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'stop_hunt_detected': False,
            'near_institutional_level': True,
            'rr': 3.2,
            'ai_sentiment_bonus': 6
        }
        
        score = score_tcs(signal_data)
        trade_type = classify_trade(score, signal_data['rr'], signal_data)
        
        assert 85 <= score <= 95
        assert trade_type in ["shadow_strike", "shadow_strike_premium", "hammer"]
        
        # Verify breakdown makes sense
        breakdown = signal_data['tcs_breakdown']
        assert breakdown['session'] == 10  # London gets max points
        assert breakdown['momentum'] >= 10  # Good momentum
    
    def test_asian_session_range_trade(self):
        """Test Asian session range trading setup"""
        signal_data = {
            'trend_clarity': 0.3,
            'sr_quality': 0.9,  # Strong S/R in range
            'pattern_complete': False,
            'pattern_forming': True,
            'M15_aligned': True,
            'H1_aligned': False,
            'H4_aligned': False,
            'D1_aligned': False,
            'rsi': 45,
            'macd_aligned': False,
            'volume_ratio': 0.9,
            'atr': 15,
            'spread_ratio': 1.4,
            'volatility_stable': True,
            'session': 'tokyo',
            'liquidity_grab': False,
            'stop_hunt_detected': False,
            'near_institutional_level': True,
            'rr': 2.0,
            'ai_sentiment_bonus': 3
        }
        
        score = score_tcs(signal_data)
        trade_type = classify_trade(score, signal_data['rr'], signal_data)
        
        assert 65 <= score <= 80
        assert trade_type in ["scalp", "scalp_session", "watchlist"]
    
    def test_news_volatility_scenario(self):
        """Test high volatility news scenario"""
        signal_data = {
            'trend_clarity': 0.2,  # Choppy during news
            'sr_quality': 0.4,
            'pattern_complete': False,
            'M15_aligned': False,
            'H1_aligned': False,
            'H4_aligned': True,
            'D1_aligned': True,
            'rsi': 85,  # Extreme reading
            'macd_aligned': True,
            'volume_ratio': 3.0,  # High volume
            'atr': 120,  # Extreme volatility
            'spread_ratio': 3.5,  # Wide spread
            'volatility_stable': False,
            'session': 'new_york',
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': False,
            'rr': 5.0,  # Good RR but risky
            'ai_sentiment_bonus': 2
        }
        
        score = score_tcs(signal_data)
        trade_type = classify_trade(score, signal_data['rr'], signal_data)
        
        # Should score lower due to poor conditions despite some positives
        assert score < 70
        assert trade_type in ["watchlist", "none"]


class TestPerformanceBenchmarks:
    """Test performance characteristics of TCS++ engine"""
    
    def test_scoring_performance(self):
        """Test that scoring is fast enough for real-time use"""
        import time
        
        signal_data = {
            'trend_clarity': 0.7,
            'sr_quality': 0.8,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': False,
            'D1_aligned': True,
            'rsi': 65,
            'macd_aligned': True,
            'volume_ratio': 1.4,
            'atr': 30,
            'spread_ratio': 1.5,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'stop_hunt_detected': False,
            'near_institutional_level': True,
            'rr': 3.0,
            'ai_sentiment_bonus': 5
        }
        
        # Test single scoring
        start = time.time()
        score = score_tcs(signal_data)
        duration = time.time() - start
        
        assert duration < 0.001, f"Single scoring too slow: {duration}s"
        
        # Test batch scoring
        start = time.time()
        for _ in range(1000):
            score = score_tcs(signal_data)
            classify_trade(score, signal_data['rr'], signal_data)
        duration = time.time() - start
        
        assert duration < 0.1, f"Batch scoring too slow: {duration}s for 1000 operations"
    
    def test_memory_efficiency(self):
        """Test that TCS++ doesn't leak memory"""
        import gc
        import sys
        
        # Get initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many scoring operations
        for i in range(10000):
            signal_data = {
                'trend_clarity': i % 10 / 10,
                'sr_quality': (i % 8) / 10,
                'rsi': 30 + (i % 40),
                'volume_ratio': 1 + (i % 20) / 10,
                'atr': 10 + (i % 50),
                'session': ['london', 'new_york', 'tokyo'][i % 3],
                'rr': 1 + (i % 40) / 10
            }
            score = score_tcs(signal_data)
            classify_trade(score, signal_data['rr'])
        
        # Check memory after
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow for some growth but not excessive
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Too many objects created: {object_growth}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])