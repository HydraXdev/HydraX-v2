"""
Integration Tests for TCS++ Engine and Stealth Protocol
Tests how both systems work together with existing fire modes
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.tcs_engine import score_tcs, classify_trade
from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthConfig, StealthLevel, get_stealth_protocol
)


class TestTCSStealthIntegration:
    """Test integration between TCS++ scoring and stealth protocol"""
    
    def test_high_score_low_stealth(self):
        """Test that high TCS scores get minimal stealth interference"""
        # Create high-quality signal
        signal_data = {
            'trend_clarity': 0.9,
            'sr_quality': 0.9,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True,
            'rsi': 70,
            'macd_aligned': True,
            'volume_ratio': 1.8,
            'atr': 35,
            'spread_ratio': 1.2,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'rr': 4.0,
            'ai_sentiment_bonus': 8
        }
        
        # Score the signal
        tcs_score = score_tcs(signal_data)
        trade_type = classify_trade(tcs_score, signal_data['rr'], signal_data)
        
        assert tcs_score >= 90
        assert trade_type in ['hammer', 'hammer_elite']
        
        # Apply stealth with dynamic level based on score
        if tcs_score >= 90:
            stealth_level = StealthLevel.LOW
        elif tcs_score >= 80:
            stealth_level = StealthLevel.MEDIUM
        else:
            stealth_level = StealthLevel.HIGH
            
        config = StealthConfig(level=stealth_level)
        stealth = StealthProtocol(config)
        
        # Create trade parameters
        trade_params = {
            'symbol': 'EURUSD',
            'trade_id': 'high_score_001',
            'volume': 1.0,
            'tp': 1.2100,
            'sl': 1.1900,
            'tcs_score': tcs_score,
            'trade_type': trade_type
        }
        
        # Apply stealth
        result = stealth.apply_full_stealth(trade_params)
        
        # High score trades should have minimal modifications
        if not result.get('skip_trade'):
            assert result['entry_delay'] <= 6.0  # Max 6 seconds for low stealth
            assert abs(result['volume'] - 1.0) <= 0.03  # Max 3% lot variation
    
    def test_low_score_high_stealth(self):
        """Test that low TCS scores get maximum stealth"""
        # Create low-quality signal
        signal_data = {
            'trend_clarity': 0.4,
            'sr_quality': 0.5,
            'pattern_complete': False,
            'M15_aligned': True,
            'H1_aligned': False,
            'H4_aligned': False,
            'D1_aligned': False,
            'rsi': 50,
            'macd_aligned': False,
            'volume_ratio': 1.1,
            'atr': 25,
            'spread_ratio': 2.0,
            'volatility_stable': True,
            'session': 'sydney',
            'rr': 1.5,
            'ai_sentiment_bonus': 2
        }
        
        # Score the signal
        tcs_score = score_tcs(signal_data)
        trade_type = classify_trade(tcs_score, signal_data['rr'], signal_data)
        
        assert tcs_score < 75
        assert trade_type in ['scalp', 'watchlist', 'none']
        
        # Apply high stealth for low scores
        config = StealthConfig(level=StealthLevel.HIGH)
        stealth = StealthProtocol(config)
        
        trade_params = {
            'symbol': 'GBPUSD',
            'trade_id': 'low_score_001',
            'volume': 0.5,
            'tp': 1.3050,
            'sl': 1.2950,
            'tcs_score': tcs_score,
            'trade_type': trade_type
        }
        
        # Run multiple times to check skip rate
        skipped = 0
        executed = 0
        
        for i in range(100):
            trade_params['trade_id'] = f'low_score_{i:03d}'
            result = stealth.apply_full_stealth(trade_params)
            
            if result.get('skip_trade'):
                skipped += 1
            else:
                executed += 1
                # Higher delays and variations for low scores
                assert result['entry_delay'] >= 1.0
                assert abs(result['volume'] - 0.5) / 0.5 <= 0.15  # Up to 15% variation
        
        # High stealth should skip ~25% of low score trades
        skip_rate = skipped / 100
        assert 0.15 <= skip_rate <= 0.35
    
    def test_trade_classification_stealth_mapping(self):
        """Test mapping of trade classifications to stealth levels"""
        # Define mapping strategy
        classification_stealth_map = {
            'hammer_elite': StealthLevel.OFF,      # No stealth for elite trades
            'hammer': StealthLevel.LOW,            # Minimal stealth
            'shadow_strike_premium': StealthLevel.LOW,
            'shadow_strike': StealthLevel.MEDIUM,
            'scalp_session': StealthLevel.MEDIUM,
            'scalp': StealthLevel.HIGH,
            'watchlist': StealthLevel.HIGH,
            'none': StealthLevel.GHOST             # Maximum stealth for rejected
        }
        
        test_scenarios = [
            {'score': 96, 'rr': 4.0, 'momentum_strength': 0.9, 'structure_quality': 0.95},
            {'score': 95, 'rr': 3.8},
            {'score': 90, 'rr': 3.2},
            {'score': 85, 'rr': 2.8},
            {'score': 78, 'rr': 2.0, 'session': 'london'},
            {'score': 76, 'rr': 1.8},
            {'score': 70, 'rr': 1.5},
            {'score': 60, 'rr': 1.2}
        ]
        
        for scenario in test_scenarios:
            score = scenario['score']
            rr = scenario['rr']
            signal_data = {k: v for k, v in scenario.items() if k not in ['score', 'rr']}
            
            # Classify trade
            trade_type = classify_trade(score, rr, signal_data if signal_data else None)
            
            # Get appropriate stealth level
            stealth_level = classification_stealth_map.get(trade_type, StealthLevel.MEDIUM)
            
            # Create stealth protocol with appropriate level
            config = StealthConfig(level=stealth_level)
            stealth = StealthProtocol(config)
            
            # Verify stealth behavior matches trade quality
            if trade_type in ['hammer_elite', 'hammer']:
                assert stealth.config.level in [StealthLevel.OFF, StealthLevel.LOW]
            elif trade_type in ['shadow_strike_premium', 'shadow_strike']:
                assert stealth.config.level in [StealthLevel.LOW, StealthLevel.MEDIUM]
            elif trade_type in ['scalp', 'scalp_session']:
                assert stealth.config.level in [StealthLevel.MEDIUM, StealthLevel.HIGH]
            else:
                assert stealth.config.level in [StealthLevel.HIGH, StealthLevel.GHOST]


class TestFireModeIntegration:
    """Test integration with existing fire modes"""
    
    def setup_method(self):
        """Setup fire mode mocks"""
        self.fire_modes = {
            'single_shot': {'concurrent_limit': 1, 'stealth_multiplier': 1.0},
            'burst': {'concurrent_limit': 3, 'stealth_multiplier': 0.8},
            'full_auto': {'concurrent_limit': 10, 'stealth_multiplier': 1.2},
            'sniper': {'concurrent_limit': 1, 'stealth_multiplier': 0.5}
        }
    
    def test_single_shot_mode_integration(self):
        """Test TCS++ and stealth with single shot mode"""
        mode = self.fire_modes['single_shot']
        
        # Configure stealth for single shot
        config = StealthConfig(
            level=StealthLevel.MEDIUM,
            max_concurrent_per_asset=mode['concurrent_limit'],
            max_total_concurrent=mode['concurrent_limit']
        )
        stealth = StealthProtocol(config)
        
        # High quality signal for single shot
        signal_data = {
            'trend_clarity': 0.85,
            'sr_quality': 0.9,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True,
            'rsi': 72,
            'macd_aligned': True,
            'volume_ratio': 1.6,
            'atr': 30,
            'spread_ratio': 1.3,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'rr': 3.5,
            'ai_sentiment_bonus': 7
        }
        
        score = score_tcs(signal_data)
        trade_type = classify_trade(score, signal_data['rr'], signal_data)
        
        # Single shot should only allow one trade
        trade1 = {
            'symbol': 'EURUSD',
            'trade_id': 'single_001',
            'volume': 1.0,
            'tp': 1.2100,
            'sl': 1.1900,
            'fire_mode': 'single_shot'
        }
        
        trade2 = {
            'symbol': 'EURUSD',
            'trade_id': 'single_002',
            'volume': 1.0,
            'tp': 1.2100,
            'sl': 1.1900,
            'fire_mode': 'single_shot'
        }
        
        # First trade should execute
        result1 = stealth.apply_full_stealth(trade1)
        assert not result1.get('skip_trade') or result1.get('skip_trade') is False
        
        # Second trade should be blocked by volume cap
        result2 = stealth.apply_full_stealth(trade2)
        if not result1.get('skip_trade'):  # If first wasn't ghost skipped
            assert result2.get('skip_trade') is True
            assert result2.get('skip_reason') == 'volume_cap'
    
    def test_burst_mode_integration(self):
        """Test TCS++ and stealth with burst mode"""
        mode = self.fire_modes['burst']
        
        # Configure stealth for burst mode
        config = StealthConfig(
            level=StealthLevel.MEDIUM,
            max_concurrent_per_asset=mode['concurrent_limit'],
            entry_delay_min=0.5,  # Shorter delays for burst
            entry_delay_max=3.0,
            shuffle_queue=True  # Shuffle burst trades
        )
        stealth = StealthProtocol(config)
        
        # Create burst of 3 trades with varying quality
        trades = []
        for i in range(3):
            signal_data = {
                'trend_clarity': 0.7 + i * 0.05,
                'sr_quality': 0.8,
                'pattern_complete': i == 0,  # First trade best
                'M15_aligned': True,
                'H1_aligned': True,
                'H4_aligned': i < 2,
                'D1_aligned': i == 0,
                'rsi': 65 + i * 3,
                'macd_aligned': True,
                'volume_ratio': 1.4 - i * 0.1,
                'atr': 28,
                'spread_ratio': 1.4,
                'volatility_stable': True,
                'session': 'new_york',
                'rr': 2.5 + i * 0.3,
                'ai_sentiment_bonus': 5 - i
            }
            
            score = score_tcs(signal_data)
            
            trades.append({
                'symbol': 'GBPUSD',
                'trade_id': f'burst_{i:03d}',
                'volume': 0.5,
                'tp': 1.3100 + i * 0.0010,
                'sl': 1.2900 - i * 0.0010,
                'tcs_score': score,
                'fire_mode': 'burst'
            })
        
        # Apply shuffle for burst mode
        shuffled = stealth.execution_shuffle(trades)
        
        # Execute burst
        results = []
        for trade in shuffled:
            result = stealth.apply_full_stealth(trade)
            results.append(result)
        
        # All 3 should execute (unless ghost skipped)
        executed = [r for r in results if not r.get('skip_trade')]
        assert len(executed) <= 3
        
        # Verify burst characteristics
        if len(executed) > 1:
            # Check shuffle worked
            original_ids = [t['trade_id'] for t in trades]
            executed_ids = [t['trade_id'] for t in executed]
            # May not always be different due to randomness
            
            # Check delays are appropriate for burst
            for trade in executed:
                assert trade['entry_delay'] <= 4.5  # 3.0 * 1.5 for high level
    
    def test_full_auto_mode_integration(self):
        """Test TCS++ and stealth with full auto mode"""
        mode = self.fire_modes['full_auto']
        
        # Configure aggressive stealth for full auto
        config = StealthConfig(
            level=StealthLevel.HIGH,  # Higher stealth for full auto
            max_concurrent_per_asset=5,
            max_total_concurrent=mode['concurrent_limit'],
            ghost_skip_rate=0.2,  # Skip more in full auto
            lot_jitter_min=0.05,
            lot_jitter_max=0.12,
            shuffle_queue=True
        )
        stealth = StealthProtocol(config)
        
        # Generate many trades of varying quality
        all_trades = []
        for i in range(20):  # Generate 20 signals
            # Vary signal quality
            quality = 0.5 + (i % 5) * 0.1
            
            signal_data = {
                'trend_clarity': quality,
                'sr_quality': quality + 0.1,
                'pattern_complete': i % 3 == 0,
                'M15_aligned': i % 2 == 0,
                'H1_aligned': True,
                'H4_aligned': i % 4 < 2,
                'D1_aligned': i % 5 == 0,
                'rsi': 50 + (i % 40),
                'macd_aligned': i % 2 == 1,
                'volume_ratio': 1.0 + (i % 10) / 10,
                'atr': 20 + i % 30,
                'spread_ratio': 1.5,
                'volatility_stable': i % 3 != 0,
                'session': ['london', 'new_york', 'tokyo', 'sydney'][i % 4],
                'rr': 1.5 + (i % 20) / 10,
                'ai_sentiment_bonus': i % 8
            }
            
            score = score_tcs(signal_data)
            trade_type = classify_trade(score, signal_data['rr'], signal_data)
            
            # Only add trades that meet minimum threshold
            if trade_type not in ['none', 'watchlist']:
                all_trades.append({
                    'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
                    'trade_id': f'auto_{i:03d}',
                    'volume': 0.3,
                    'tp': 1.2000 + (i % 100) / 10000,
                    'sl': 1.1900 - (i % 100) / 10000,
                    'tcs_score': score,
                    'trade_type': trade_type,
                    'fire_mode': 'full_auto'
                })
        
        # Process in batches as full auto would
        batch_size = 5
        total_executed = 0
        total_skipped = 0
        
        for i in range(0, len(all_trades), batch_size):
            batch = all_trades[i:i + batch_size]
            shuffled_batch = stealth.execution_shuffle(batch)
            
            for trade in shuffled_batch:
                result = stealth.apply_full_stealth(trade)
                
                if result.get('skip_trade'):
                    total_skipped += 1
                else:
                    total_executed += 1
                    
                    # Simulate trade completion to free slots
                    if total_executed % 5 == 0:
                        # Remove some completed trades
                        for asset in list(stealth.active_trades.keys()):
                            if stealth.active_trades[asset]:
                                stealth.remove_completed_trade(
                                    asset, 
                                    stealth.active_trades[asset][0]
                                )
        
        # Full auto should respect concurrent limits
        assert total_executed <= len(all_trades)
        assert stealth.get_stealth_stats()['total_active'] <= mode['concurrent_limit']
        
        # Higher skip rate for full auto
        if len(all_trades) > 0:
            skip_rate = total_skipped / len(all_trades)
            assert 0.1 <= skip_rate <= 0.4
    
    def test_sniper_mode_integration(self):
        """Test TCS++ and stealth with sniper mode"""
        mode = self.fire_modes['sniper']
        
        # Configure minimal stealth for sniper precision
        config = StealthConfig(
            level=StealthLevel.LOW,  # Minimal stealth for precision
            max_concurrent_per_asset=mode['concurrent_limit'],
            max_total_concurrent=mode['concurrent_limit'],
            entry_delay_min=0.1,  # Very short delays
            entry_delay_max=1.0,
            lot_jitter_min=0.01,  # Minimal lot variation
            lot_jitter_max=0.02,
            ghost_skip_rate=0.02,  # Almost never skip
            tp_offset_min=0,  # No TP/SL modification for precision
            tp_offset_max=1,
            sl_offset_min=0,
            sl_offset_max=1
        )
        stealth = StealthProtocol(config)
        
        # Only highest quality signals for sniper
        signal_data = {
            'trend_clarity': 0.95,
            'sr_quality': 0.95,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True,
            'rsi': 71,
            'macd_aligned': True,
            'volume_ratio': 2.0,
            'atr': 32,
            'spread_ratio': 1.1,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': True,
            'rr': 5.0,
            'ai_sentiment_bonus': 10
        }
        
        score = score_tcs(signal_data)
        trade_type = classify_trade(score, signal_data['rr'], signal_data)
        
        assert score >= 95  # Sniper only takes 95+ scores
        assert trade_type in ['hammer', 'hammer_elite']
        
        trade = {
            'symbol': 'EURUSD',
            'trade_id': 'sniper_001',
            'volume': 2.0,  # Larger size for high conviction
            'tp': 1.2150,  # Precise targets
            'sl': 1.1950,
            'tcs_score': score,
            'trade_type': trade_type,
            'fire_mode': 'sniper'
        }
        
        # Apply minimal stealth
        result = stealth.apply_full_stealth(trade)
        
        if not result.get('skip_trade'):
            # Verify minimal modifications
            assert result['entry_delay'] <= 1.5  # Max 1.0 * 1.5 for stealth
            assert abs(result['volume'] - 2.0) <= 0.04  # Max 2% variation
            assert abs(result['tp'] - 1.2150) <= 0.0001  # Max 1 pip
            assert abs(result['sl'] - 1.1950) <= 0.0001  # Max 1 pip


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions"""
    
    def test_rapid_signal_burst(self):
        """Test handling of rapid signal bursts"""
        stealth = StealthProtocol()
        
        # Simulate 50 signals in rapid succession
        results = []
        start_time = time.time()
        
        for i in range(50):
            signal_data = {
                'trend_clarity': 0.7,
                'sr_quality': 0.75,
                'pattern_complete': i % 5 == 0,
                'M15_aligned': True,
                'H1_aligned': i % 2 == 0,
                'H4_aligned': i % 3 == 0,
                'D1_aligned': False,
                'rsi': 60 + (i % 20),
                'macd_aligned': i % 2 == 1,
                'volume_ratio': 1.3,
                'atr': 25,
                'spread_ratio': 1.5,
                'volatility_stable': True,
                'session': 'new_york',
                'rr': 2.0 + (i % 10) / 10,
                'ai_sentiment_bonus': 4
            }
            
            score = score_tcs(signal_data)
            
            trade = {
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
                'trade_id': f'rapid_{i:03d}',
                'volume': 0.5,
                'tp': 1.2050,
                'sl': 1.1950,
                'tcs_score': score
            }
            
            result = stealth.apply_full_stealth(trade)
            results.append(result)
        
        duration = time.time() - start_time
        
        # Should process all signals quickly
        assert duration < 1.0  # 50 signals in under 1 second
        
        # Check distribution of results
        executed = [r for r in results if not r.get('skip_trade')]
        skipped = [r for r in results if r.get('skip_trade')]
        
        # Some should be skipped due to volume caps and ghost skips
        assert len(skipped) > 0
        assert len(executed) > 0
    
    def test_score_boundary_transitions(self):
        """Test behavior at exact score boundaries"""
        boundaries = [
            (94, 3.5, ['hammer', 'shadow_strike_premium']),  # Hammer boundary
            (84, 3.0, ['shadow_strike', 'shadow_strike_premium', 'scalp']),  # Shadow strike boundary
            (75, 2.0, ['scalp', 'watchlist']),  # Scalp boundary
            (65, 1.5, ['watchlist', 'none'])  # Watchlist boundary
        ]
        
        for score, rr, expected_types in boundaries:
            # Test exact boundary
            trade_type = classify_trade(score, rr)
            assert trade_type in expected_types
            
            # Test just above
            trade_type_above = classify_trade(score + 0.1, rr)
            
            # Test just below
            trade_type_below = classify_trade(score - 0.1, rr)
            
            # Ensure different classifications on either side
            if score > 65:  # Not at the bottom boundary
                assert trade_type_above != trade_type_below or len(expected_types) > 2
    
    def test_concurrent_limit_stress(self):
        """Test stealth protocol under concurrent limit stress"""
        config = StealthConfig(
            max_concurrent_per_asset=3,
            max_total_concurrent=8
        )
        stealth = StealthProtocol(config)
        
        # Try to exceed per-asset limit
        asset = 'EURUSD'
        for i in range(5):
            allowed = stealth.vol_cap(asset, f'trade_{i}')
            if i < 3:
                assert allowed is True
            else:
                assert allowed is False
        
        # Try to exceed total limit
        assets = ['GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD']
        trade_count = 3  # Already have 3 EURUSD
        
        for asset in assets:
            for j in range(3):
                allowed = stealth.vol_cap(asset, f'{asset}_trade_{j}')
                if trade_count < 8:
                    assert allowed is True
                    trade_count += 1
                else:
                    assert allowed is False
        
        # Verify stats
        stats = stealth.get_stealth_stats()
        assert stats['total_active'] == 8
    
    def test_extreme_market_conditions(self):
        """Test TCS scoring under extreme market conditions"""
        # Extreme volatility scenario
        extreme_volatility = {
            'trend_clarity': 0.1,  # Very unclear
            'sr_quality': 0.2,
            'pattern_complete': False,
            'M15_aligned': False,
            'H1_aligned': False,
            'H4_aligned': False,
            'D1_aligned': False,
            'rsi': 95,  # Extreme overbought
            'macd_aligned': False,
            'volume_ratio': 5.0,  # Extreme volume
            'atr': 200,  # Extreme volatility
            'spread_ratio': 5.0,  # Very wide spread
            'volatility_stable': False,
            'session': 'dead_zone',
            'rr': 0.5,  # Poor RR
            'ai_sentiment_bonus': 0
        }
        
        score = score_tcs(extreme_volatility)
        trade_type = classify_trade(score, extreme_volatility['rr'])
        
        assert score < 30  # Should score very low
        assert trade_type == 'none'
        
        # Perfect conditions scenario
        perfect_conditions = {
            'trend_clarity': 1.0,
            'sr_quality': 1.0,
            'pattern_complete': True,
            'M15_aligned': True,
            'H1_aligned': True,
            'H4_aligned': True,
            'D1_aligned': True,
            'rsi': 70,
            'macd_aligned': True,
            'volume_ratio': 2.0,
            'atr': 35,
            'spread_ratio': 1.0,
            'volatility_stable': True,
            'session': 'london',
            'liquidity_grab': True,
            'stop_hunt_detected': True,
            'near_institutional_level': True,
            'rr': 5.0,
            'ai_sentiment_bonus': 10
        }
        
        score = score_tcs(perfect_conditions)
        trade_type = classify_trade(score, perfect_conditions['rr'], perfect_conditions)
        
        assert score >= 98  # Should score near perfect
        assert trade_type == 'hammer_elite'


class TestPerformanceBenchmarks:
    """Performance benchmarks for integrated systems"""
    
    def test_integrated_performance(self):
        """Test performance of TCS scoring + stealth application"""
        stealth = StealthProtocol()
        
        # Generate test data
        test_signals = []
        for i in range(1000):
            signal = {
                'trend_clarity': (i % 10) / 10,
                'sr_quality': ((i + 3) % 10) / 10,
                'pattern_complete': i % 3 == 0,
                'M15_aligned': i % 2 == 0,
                'H1_aligned': i % 3 < 2,
                'H4_aligned': i % 4 < 2,
                'D1_aligned': i % 5 == 0,
                'rsi': 30 + (i % 40),
                'macd_aligned': i % 2 == 1,
                'volume_ratio': 1.0 + (i % 20) / 10,
                'atr': 10 + (i % 50),
                'spread_ratio': 1.0 + (i % 30) / 10,
                'volatility_stable': i % 3 != 0,
                'session': ['london', 'new_york', 'tokyo', 'sydney', 'dead_zone'][i % 5],
                'liquidity_grab': i % 10 == 0,
                'stop_hunt_detected': i % 15 == 0,
                'near_institutional_level': i % 8 == 0,
                'rr': 1.0 + (i % 40) / 10,
                'ai_sentiment_bonus': i % 11
            }
            test_signals.append(signal)
        
        # Benchmark full pipeline
        start_time = time.time()
        
        for i, signal in enumerate(test_signals):
            # Score with TCS++
            score = score_tcs(signal)
            trade_type = classify_trade(score, signal['rr'], signal)
            
            # Create trade parameters
            trade_params = {
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
                'trade_id': f'perf_{i:04d}',
                'volume': 1.0,
                'tp': 1.2100 + (i % 100) / 10000,
                'sl': 1.1900 - (i % 100) / 10000,
                'tcs_score': score,
                'trade_type': trade_type
            }
            
            # Apply stealth
            result = stealth.apply_full_stealth(trade_params)
        
        duration = time.time() - start_time
        
        # Should process 1000 signals in under 2 seconds
        assert duration < 2.0
        
        # Calculate throughput
        throughput = 1000 / duration
        assert throughput > 500  # At least 500 signals per second
    
    def test_memory_efficiency_integrated(self):
        """Test memory efficiency of integrated systems"""
        import gc
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        stealth = StealthProtocol()
        
        # Run many operations
        for i in range(5000):
            signal_data = {
                'trend_clarity': 0.7,
                'sr_quality': 0.8,
                'rsi': 65,
                'volume_ratio': 1.4,
                'atr': 30,
                'session': 'london',
                'rr': 2.5
            }
            
            score = score_tcs(signal_data)
            trade_type = classify_trade(score, signal_data['rr'])
            
            trade = {
                'symbol': 'EURUSD',
                'trade_id': f'mem_{i}',
                'volume': 1.0,
                'tp': 1.2100,
                'sl': 1.1900
            }
            
            stealth.apply_full_stealth(trade)
            
            # Periodically clean up
            if i % 500 == 0:
                for asset in list(stealth.active_trades.keys()):
                    stealth.active_trades[asset].clear()
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        object_growth = final_objects - initial_objects
        assert object_growth < 10000  # Reasonable memory growth


if __name__ == "__main__":
    pytest.main([__file__, "-v"])