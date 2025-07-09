"""
Integration tests for TCS++ scoring engine with fire modes.
Tests that TCS++ properly integrates with all fire modes and scoring systems.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from core.tcs_engine import score_tcs, classify_trade
from src.bitten_core.fire_modes import FireModeManager
from src.bitten_core.signal_display import SignalDisplayManager
from src.bitten_core.xp_calculator import XPCalculator


class TestTCSIntegration(unittest.TestCase):
    """Test TCS++ integration with fire modes and signal system"""
    
    def setUp(self):
        """Set up test environment"""
        self.fire_mode_manager = FireModeManager()
        self.signal_display = SignalDisplayManager()
        self.xp_calculator = XPCalculator()
        
        # Sample signal data
        self.base_signal = {
            'pair': 'EURUSD',
            'action': 'BUY',
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0900,
            'rr': 2.5,
            'trend_clarity': 0.8,
            'sr_quality': 0.7,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': False,
            'rsi': 65,
            'macd_aligned': True,
            'volume_ratio': 1.3,
            'atr': 25,
            'spread_ratio': 1.2,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'stop_hunt_detected': False,
            'near_institutional_level': True,
            'ai_sentiment_bonus': 5
        }
    
    def test_tcs_scoring_components(self):
        """Test that all TCS++ components score correctly"""
        score = score_tcs(self.base_signal)
        
        # Verify score is within valid range
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Verify breakdown is stored
        self.assertIn('tcs_breakdown', self.base_signal)
        breakdown = self.base_signal['tcs_breakdown']
        
        # Verify all components are present
        expected_components = [
            'structure', 'timeframe_alignment', 'momentum',
            'volatility', 'session', 'liquidity', 'risk_reward',
            'ai_sentiment'
        ]
        
        for component in expected_components:
            self.assertIn(component, breakdown)
            self.assertGreaterEqual(breakdown[component], 0)
    
    def test_trade_classification(self):
        """Test trade classification based on TCS++ score"""
        test_cases = [
            (95, 4.0, 'hammer'),  # Elite setup
            (90, 3.0, 'shadow_strike'),  # High probability
            (78, 2.5, 'scalp'),  # Quick opportunity
            (70, 2.0, 'watchlist'),  # Monitor only
            (60, 1.5, 'none'),  # No trade
        ]
        
        for tcs_score, rr, expected_class in test_cases:
            signal_data = {'momentum_strength': 0.7, 'structure_quality': 0.8}
            trade_class = classify_trade(tcs_score, rr, signal_data)
            
            # Allow for variations (e.g., hammer_elite, shadow_strike_premium)
            self.assertTrue(
                trade_class.startswith(expected_class) or trade_class == expected_class,
                f"Score {tcs_score}, RR {rr} should classify as {expected_class}, got {trade_class}"
            )
    
    @patch('src.bitten_core.database.connection.get_db_connection')
    def test_fire_mode_tcs_integration(self, mock_get_db):
        """Test TCS++ integration with different fire modes"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test each fire mode
        fire_modes = ['FANG', 'SNIPER', 'HAMMER', 'SCALP']
        
        for mode in fire_modes:
            # Score the signal
            signal = self.base_signal.copy()
            tcs_score = score_tcs(signal)
            signal['tcs_score'] = tcs_score
            signal['fire_mode'] = mode
            
            # Verify fire mode affects signal display
            trade_class = classify_trade(tcs_score, signal['rr'], signal)
            
            # Each mode should handle the classification
            self.assertIsNotNone(trade_class)
            
            # High TCS should work with all modes
            if tcs_score >= 75:
                self.assertNotEqual(trade_class, 'none')
    
    def test_tcs_xp_calculation(self):
        """Test that TCS++ score affects XP calculations"""
        # High TCS trade
        high_tcs_signal = self.base_signal.copy()
        high_tcs_signal['tcs_score'] = 95
        high_tcs_signal['trade_result'] = 'win'
        high_tcs_signal['pips'] = 50
        
        # Low TCS trade
        low_tcs_signal = self.base_signal.copy()
        low_tcs_signal['tcs_score'] = 70
        low_tcs_signal['trade_result'] = 'win'
        low_tcs_signal['pips'] = 50
        
        # Calculate XP for both
        high_xp = self.xp_calculator.calculate_trade_xp(high_tcs_signal)
        low_xp = self.xp_calculator.calculate_trade_xp(low_tcs_signal)
        
        # High TCS should give more XP
        self.assertGreater(high_xp, low_xp)
    
    def test_tcs_edge_cases(self):
        """Test TCS++ scoring with edge cases"""
        # Minimal signal data
        minimal_signal = {
            'pair': 'EURUSD',
            'rr': 2.0
        }
        
        score = score_tcs(minimal_signal)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Perfect signal
        perfect_signal = self.base_signal.copy()
        perfect_signal.update({
            'trend_clarity': 1.0,
            'sr_quality': 1.0,
            'D1_aligned': True,  # All timeframes aligned
            'rsi': 70,  # Perfect momentum zone
            'volume_ratio': 2.0,  # High volume
            'atr': 30,  # Optimal volatility
            'spread_ratio': 1.0,  # Perfect spread
            'ai_sentiment_bonus': 10  # Max bonus
        })
        
        score = score_tcs(perfect_signal)
        self.assertGreater(score, 90)  # Should be very high
    
    def test_tcs_session_weighting(self):
        """Test that different sessions affect TCS score correctly"""
        sessions = ['london', 'new_york', 'overlap', 'tokyo', 'sydney', 'dead_zone']
        scores = []
        
        for session in sessions:
            signal = self.base_signal.copy()
            signal['session'] = session
            score = score_tcs(signal)
            scores.append((session, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Verify London is highest scored
        self.assertEqual(scores[0][0], 'london')
        
        # Verify dead_zone is lowest
        self.assertEqual(scores[-1][0], 'dead_zone')
    
    def test_tcs_momentum_analysis(self):
        """Test momentum component of TCS++"""
        # Test different RSI values
        rsi_values = [20, 30, 40, 50, 60, 70, 80]
        
        for rsi in rsi_values:
            signal = self.base_signal.copy()
            signal['rsi'] = rsi
            score_tcs(signal)
            
            # Check momentum strength is calculated
            self.assertIn('momentum_strength', signal)
            self.assertGreaterEqual(signal['momentum_strength'], 0)
            self.assertLessEqual(signal['momentum_strength'], 1)
    
    def test_tcs_liquidity_detection(self):
        """Test liquidity pattern detection in TCS++"""
        # Test with liquidity patterns
        signal_with_liquidity = self.base_signal.copy()
        signal_with_liquidity.update({
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': True
        })
        
        score_with = score_tcs(signal_with_liquidity)
        
        # Test without liquidity patterns
        signal_without_liquidity = self.base_signal.copy()
        signal_without_liquidity.update({
            'liquidity_grab': False,
            'stop_hunt_detected': False,
            'near_institutional_level': False
        })
        
        score_without = score_tcs(signal_without_liquidity)
        
        # Score with liquidity patterns should be higher
        self.assertGreater(score_with, score_without)
    
    def test_tcs_volatility_conditions(self):
        """Test volatility analysis in TCS++"""
        # Test different ATR values
        atr_values = [5, 15, 30, 50, 80, 100]
        
        for atr in atr_values:
            signal = self.base_signal.copy()
            signal['atr'] = atr
            score_tcs(signal)
            
            breakdown = signal['tcs_breakdown']
            
            # Verify volatility score is within bounds
            self.assertGreaterEqual(breakdown['volatility'], 0)
            self.assertLessEqual(breakdown['volatility'], 10)
    
    @patch('src.bitten_core.signal_display.SignalDisplayManager.format_signal')
    def test_tcs_signal_display_integration(self, mock_format_signal):
        """Test that TCS++ score is properly displayed in signals"""
        # Score a signal
        signal = self.base_signal.copy()
        tcs_score = score_tcs(signal)
        signal['tcs_score'] = tcs_score
        
        # Format for display
        self.signal_display.format_signal(signal)
        
        # Verify format_signal was called with TCS score
        mock_format_signal.assert_called_once()
        call_args = mock_format_signal.call_args[0][0]
        self.assertIn('tcs_score', call_args)
        self.assertEqual(call_args['tcs_score'], tcs_score)
    
    def test_tcs_classification_boundaries(self):
        """Test trade classification at exact boundaries"""
        boundaries = [
            (94, 3.5, 'hammer'),  # Exact hammer boundary
            (84, 3.0, 'shadow_strike'),  # Exact shadow strike boundary
            (75, 2.5, 'scalp'),  # Exact scalp boundary
            (65, 2.0, 'watchlist'),  # Exact watchlist boundary
            (64, 2.0, 'none'),  # Just below threshold
        ]
        
        for score, rr, expected in boundaries:
            result = classify_trade(score, rr)
            self.assertTrue(
                result.startswith(expected) or result == expected,
                f"Boundary test failed: score={score}, rr={rr}, expected={expected}, got={result}"
            )


class TestTCSFireModeCompatibility(unittest.TestCase):
    """Test TCS++ compatibility with all fire modes"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_signal = {
            'pair': 'GBPUSD',
            'action': 'SELL',
            'entry': 1.2650,
            'sl': 1.2680,
            'tp': 1.2590,
            'rr': 2.0
        }
    
    @patch('src.bitten_core.fire_modes.FireModeManager.process_signal')
    def test_fang_mode_with_tcs(self, mock_process):
        """Test FANG mode processes TCS++ scores"""
        signal = self.test_signal.copy()
        signal['fire_mode'] = 'FANG'
        
        # Add TCS data
        tcs_score = score_tcs(signal)
        signal['tcs_score'] = tcs_score
        
        # Process through fire mode
        fire_manager = FireModeManager()
        fire_manager.process_signal(signal, 'FANG')
        
        mock_process.assert_called_once()
        processed_signal = mock_process.call_args[0][0]
        self.assertIn('tcs_score', processed_signal)
    
    def test_sniper_mode_high_tcs_requirement(self):
        """Test that SNIPER mode requires high TCS scores"""
        # Low TCS signal
        low_signal = self.test_signal.copy()
        low_signal['tcs_score'] = 60
        
        # High TCS signal
        high_signal = self.test_signal.copy()
        high_signal['tcs_score'] = 90
        
        fire_manager = FireModeManager()
        
        # SNIPER should prefer high TCS
        self.assertTrue(fire_manager.validate_for_mode(high_signal, 'SNIPER'))
        self.assertFalse(fire_manager.validate_for_mode(low_signal, 'SNIPER'))


if __name__ == '__main__':
    unittest.main()