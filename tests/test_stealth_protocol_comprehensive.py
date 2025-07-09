"""
Comprehensive Test Suite for Stealth Protocol
Tests all stealth functions, edge cases, and integration scenarios
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import secrets
import json
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthConfig, StealthLevel, StealthAction,
    get_stealth_protocol
)


class TestStealthProtocolInitialization:
    """Test stealth protocol initialization and configuration"""
    
    def test_default_initialization(self):
        """Test default stealth protocol initialization"""
        stealth = StealthProtocol()
        
        assert stealth.config.enabled is True
        assert stealth.config.level == StealthLevel.MEDIUM
        assert stealth.config.entry_delay_min == 1.0
        assert stealth.config.entry_delay_max == 12.0
        assert stealth.config.lot_jitter_min == 0.03
        assert stealth.config.lot_jitter_max == 0.07
        assert stealth.config.ghost_skip_rate == 0.167
        assert stealth.active_trades == {}
        assert stealth.action_log == []
    
    def test_custom_configuration(self):
        """Test initialization with custom configuration"""
        config = StealthConfig(
            enabled=False,
            level=StealthLevel.HIGH,
            entry_delay_min=2.0,
            entry_delay_max=20.0,
            lot_jitter_min=0.05,
            lot_jitter_max=0.15,
            ghost_skip_rate=0.25
        )
        
        stealth = StealthProtocol(config)
        
        assert stealth.config.enabled is False
        assert stealth.config.level == StealthLevel.HIGH
        assert stealth.config.entry_delay_min == 2.0
        assert stealth.config.entry_delay_max == 20.0
    
    def test_singleton_pattern(self):
        """Test that get_stealth_protocol returns singleton"""
        stealth1 = get_stealth_protocol()
        stealth2 = get_stealth_protocol()
        
        assert stealth1 is stealth2


class TestEntryDelay:
    """Test entry delay functionality"""
    
    def test_entry_delay_disabled(self):
        """Test entry delay when stealth is disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        delay = stealth.entry_delay({'symbol': 'EURUSD'})
        assert delay == 0.0
    
    def test_entry_delay_ranges_by_level(self):
        """Test that delay ranges vary by stealth level"""
        trade_params = {'symbol': 'GBPUSD'}
        
        # Test each level
        levels_and_multipliers = [
            (StealthLevel.LOW, 0.5),
            (StealthLevel.MEDIUM, 1.0),
            (StealthLevel.HIGH, 1.5),
            (StealthLevel.GHOST, 2.0)
        ]
        
        for level, multiplier in levels_and_multipliers:
            config = StealthConfig(level=level, entry_delay_min=1.0, entry_delay_max=10.0)
            stealth = StealthProtocol(config)
            
            # Test multiple times to ensure randomness
            delays = [stealth.entry_delay(trade_params) for _ in range(100)]
            
            min_expected = config.entry_delay_min
            max_expected = config.entry_delay_max * multiplier
            
            assert all(min_expected <= d <= max_expected for d in delays)
            assert min(delays) < max(delays), "Should have variation in delays"
    
    def test_entry_delay_logging(self):
        """Test that entry delays are properly logged"""
        stealth = StealthProtocol()
        trade_params = {'symbol': 'USDJPY'}
        
        initial_log_count = len(stealth.action_log)
        delay = stealth.entry_delay(trade_params)
        
        assert len(stealth.action_log) == initial_log_count + 1
        
        last_action = stealth.action_log[-1]
        assert last_action.action_type == "entry_delay"
        assert last_action.original_value == 0
        assert last_action.modified_value == delay
        assert last_action.details['pair'] == 'USDJPY'
        assert last_action.details['delay_seconds'] == delay
    
    def test_entry_delay_randomness(self):
        """Test that delays are truly random and well-distributed"""
        stealth = StealthProtocol()
        trade_params = {'symbol': 'EURUSD'}
        
        # Generate many delays
        delays = [stealth.entry_delay(trade_params) for _ in range(1000)]
        
        # Check distribution
        avg_delay = sum(delays) / len(delays)
        expected_avg = (stealth.config.entry_delay_min + stealth.config.entry_delay_max) / 2
        
        # Allow 10% deviation from expected average
        assert abs(avg_delay - expected_avg) < expected_avg * 0.1
        
        # Check uniqueness (should have many unique values)
        unique_delays = set(delays)
        assert len(unique_delays) > 900  # At least 90% unique


class TestLotSizeJitter:
    """Test lot size jitter functionality"""
    
    def test_lot_jitter_disabled(self):
        """Test lot jitter when stealth is disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        original_lot = 1.0
        modified_lot = stealth.lot_size_jitter(original_lot, 'EURUSD')
        assert modified_lot == original_lot
    
    def test_lot_jitter_ranges_by_level(self):
        """Test jitter ranges for different stealth levels"""
        original_lot = 1.0
        
        level_ranges = {
            StealthLevel.LOW: (0.01, 0.03),
            StealthLevel.MEDIUM: (0.03, 0.07),
            StealthLevel.HIGH: (0.05, 0.10),
            StealthLevel.GHOST: (0.07, 0.15)
        }
        
        for level, (min_jitter, max_jitter) in level_ranges.items():
            config = StealthConfig(level=level)
            stealth = StealthProtocol(config)
            
            # Test multiple times
            modified_lots = [stealth.lot_size_jitter(original_lot, 'EURUSD') for _ in range(100)]
            
            for lot in modified_lots:
                deviation = abs(lot - original_lot) / original_lot
                assert deviation <= max_jitter
                
                # Check that we get both increases and decreases
            assert any(lot > original_lot for lot in modified_lots)
            assert any(lot < original_lot for lot in modified_lots)
    
    def test_lot_jitter_decimal_precision(self):
        """Test that lot sizes maintain proper decimal precision"""
        stealth = StealthProtocol()
        
        test_lots = [0.01, 0.1, 1.0, 2.5, 10.0]
        
        for original in test_lots:
            modified = stealth.lot_size_jitter(original, 'GBPUSD')
            
            # Check decimal places (max 2 for lot sizes)
            decimal_str = str(modified).split('.')
            if len(decimal_str) > 1:
                assert len(decimal_str[1]) <= 2
    
    def test_lot_jitter_logging(self):
        """Test lot jitter action logging"""
        stealth = StealthProtocol()
        
        original_lot = 2.0
        modified_lot = stealth.lot_size_jitter(original_lot, 'AUDUSD')
        
        last_action = stealth.action_log[-1]
        assert last_action.action_type == "lot_size_jitter"
        assert last_action.original_value == original_lot
        assert last_action.modified_value == modified_lot
        assert 'jitter_percent' in last_action.details
        assert last_action.details['pair'] == 'AUDUSD'


class TestTPSLOffset:
    """Test TP/SL offset functionality"""
    
    def test_tp_sl_offset_disabled(self):
        """Test TP/SL offset when stealth is disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        tp, sl = 1.2000, 1.1900
        new_tp, new_sl = stealth.tp_sl_offset(tp, sl, 'EURUSD')
        
        assert new_tp == tp
        assert new_sl == sl
    
    def test_tp_sl_offset_pip_calculation(self):
        """Test correct pip value calculation for different pairs"""
        stealth = StealthProtocol()
        
        # Test non-JPY pair (4 decimal places)
        tp, sl = 1.2000, 1.1900
        new_tp, new_sl = stealth.tp_sl_offset(tp, sl, 'EURUSD')
        
        # Should be offset by 1-3 pips (0.0001-0.0003)
        tp_diff = abs(new_tp - tp)
        sl_diff = abs(new_sl - sl)
        
        assert 0.0001 <= tp_diff <= 0.0003
        assert 0.0001 <= sl_diff <= 0.0003
        
        # Test JPY pair (2 decimal places)
        tp_jpy, sl_jpy = 110.00, 109.50
        new_tp_jpy, new_sl_jpy = stealth.tp_sl_offset(tp_jpy, sl_jpy, 'USDJPY')
        
        # Should be offset by 1-3 pips (0.01-0.03)
        tp_diff_jpy = abs(new_tp_jpy - tp_jpy)
        sl_diff_jpy = abs(new_sl_jpy - sl_jpy)
        
        assert 0.01 <= tp_diff_jpy <= 0.03
        assert 0.01 <= sl_diff_jpy <= 0.03
    
    def test_tp_sl_offset_level_multipliers(self):
        """Test offset multipliers for different stealth levels"""
        tp, sl = 1.3000, 1.2900
        
        level_multipliers = {
            StealthLevel.LOW: 0.5,
            StealthLevel.MEDIUM: 1.0,
            StealthLevel.HIGH: 1.5,
            StealthLevel.GHOST: 2.0
        }
        
        for level, multiplier in level_multipliers.items():
            config = StealthConfig(level=level)
            stealth = StealthProtocol(config)
            
            # Test multiple times to check range
            for _ in range(50):
                new_tp, new_sl = stealth.tp_sl_offset(tp, sl, 'GBPUSD')
                
                max_offset = 0.0003 * multiplier  # 3 pips max * multiplier
                
                assert abs(new_tp - tp) <= max_offset
                assert abs(new_sl - sl) <= max_offset
    
    def test_tp_sl_offset_direction_randomness(self):
        """Test that offsets can be both positive and negative"""
        stealth = StealthProtocol()
        tp, sl = 1.5000, 1.4900
        
        results = []
        for _ in range(100):
            new_tp, new_sl = stealth.tp_sl_offset(tp, sl, 'EURUSD')
            results.append({
                'tp_direction': 'positive' if new_tp > tp else 'negative',
                'sl_direction': 'positive' if new_sl > sl else 'negative'
            })
        
        # Check we get both directions
        tp_positive = sum(1 for r in results if r['tp_direction'] == 'positive')
        sl_positive = sum(1 for r in results if r['sl_direction'] == 'positive')
        
        # Should be roughly 50/50 distribution (allow 30-70% range)
        assert 30 <= tp_positive <= 70
        assert 30 <= sl_positive <= 70


class TestGhostSkip:
    """Test ghost skip functionality"""
    
    def test_ghost_skip_disabled(self):
        """Test ghost skip when stealth is disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        # Should never skip when disabled
        for _ in range(100):
            assert stealth.ghost_skip({'symbol': 'EURUSD'}) is False
    
    def test_ghost_skip_rates_by_level(self):
        """Test skip rates for different stealth levels"""
        trade_params = {'symbol': 'GBPUSD'}
        
        level_rates = {
            StealthLevel.LOW: 0.05,
            StealthLevel.MEDIUM: 0.167,
            StealthLevel.HIGH: 0.25,
            StealthLevel.GHOST: 0.33
        }
        
        for level, expected_rate in level_rates.items():
            config = StealthConfig(level=level)
            stealth = StealthProtocol(config)
            
            # Run many times to check statistical distribution
            skips = sum(stealth.ghost_skip(trade_params) for _ in range(1000))
            actual_rate = skips / 1000
            
            # Allow 20% deviation from expected rate
            assert abs(actual_rate - expected_rate) < expected_rate * 0.2
    
    def test_ghost_skip_logging(self):
        """Test that ghost skips are logged properly"""
        stealth = StealthProtocol()
        trade_params = {'symbol': 'USDJPY'}
        
        # Keep trying until we get a skip
        skip_found = False
        for _ in range(100):
            if stealth.ghost_skip(trade_params):
                skip_found = True
                break
        
        if skip_found:
            last_action = stealth.action_log[-1]
            assert last_action.action_type == "ghost_skip"
            assert last_action.original_value == "EXECUTE"
            assert last_action.modified_value == "SKIP"
            assert last_action.details['pair'] == 'USDJPY'
            assert last_action.details['reason'] == 'stealth_protocol'


class TestVolumeCap:
    """Test volume cap functionality"""
    
    def test_vol_cap_disabled(self):
        """Test volume cap when stealth is disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        # Should always allow when disabled
        for i in range(20):
            assert stealth.vol_cap('EURUSD', f'trade_{i}') is True
    
    def test_per_asset_limit(self):
        """Test per-asset trade limits"""
        config = StealthConfig(max_concurrent_per_asset=3)
        stealth = StealthProtocol(config)
        
        # Add trades up to limit
        assert stealth.vol_cap('EURUSD', 'trade_1') is True
        assert stealth.vol_cap('EURUSD', 'trade_2') is True
        assert stealth.vol_cap('EURUSD', 'trade_3') is True
        
        # Should deny next trade
        assert stealth.vol_cap('EURUSD', 'trade_4') is False
        
        # But allow for different asset
        assert stealth.vol_cap('GBPUSD', 'trade_5') is True
    
    def test_total_limit(self):
        """Test total concurrent trade limit"""
        config = StealthConfig(
            max_concurrent_per_asset=5,
            max_total_concurrent=10
        )
        stealth = StealthProtocol(config)
        
        # Add trades across multiple assets
        trade_id = 0
        for asset in ['EURUSD', 'GBPUSD', 'USDJPY']:
            for _ in range(3):
                assert stealth.vol_cap(asset, f'trade_{trade_id}') is True
                trade_id += 1
        
        # Now at 9 trades, one more should work
        assert stealth.vol_cap('AUDUSD', f'trade_{trade_id}') is True
        trade_id += 1
        
        # But 11th trade should fail
        assert stealth.vol_cap('NZDUSD', f'trade_{trade_id}') is False
    
    def test_vol_cap_tracking(self):
        """Test that volume cap properly tracks active trades"""
        stealth = StealthProtocol()
        
        # Add some trades
        stealth.vol_cap('EURUSD', 'trade_1')
        stealth.vol_cap('EURUSD', 'trade_2')
        stealth.vol_cap('GBPUSD', 'trade_3')
        
        assert len(stealth.active_trades['EURUSD']) == 2
        assert len(stealth.active_trades['GBPUSD']) == 1
        assert 'trade_1' in stealth.active_trades['EURUSD']
        assert 'trade_2' in stealth.active_trades['EURUSD']
        assert 'trade_3' in stealth.active_trades['GBPUSD']
    
    def test_remove_completed_trade(self):
        """Test removing completed trades from tracking"""
        stealth = StealthProtocol()
        
        # Add trades
        stealth.vol_cap('EURUSD', 'trade_1')
        stealth.vol_cap('EURUSD', 'trade_2')
        
        # Remove one
        stealth.remove_completed_trade('EURUSD', 'trade_1')
        
        assert len(stealth.active_trades['EURUSD']) == 1
        assert 'trade_1' not in stealth.active_trades['EURUSD']
        assert 'trade_2' in stealth.active_trades['EURUSD']


class TestExecutionShuffle:
    """Test execution shuffle functionality"""
    
    def test_shuffle_disabled(self):
        """Test shuffle when disabled"""
        config = StealthConfig(enabled=False)
        stealth = StealthProtocol(config)
        
        original_queue = [
            {'symbol': 'EURUSD', 'id': 1},
            {'symbol': 'GBPUSD', 'id': 2},
            {'symbol': 'USDJPY', 'id': 3}
        ]
        
        shuffled = stealth.execution_shuffle(original_queue)
        assert shuffled == original_queue
    
    def test_shuffle_empty_or_single(self):
        """Test shuffle with empty or single-item queues"""
        stealth = StealthProtocol()
        
        # Empty queue
        assert stealth.execution_shuffle([]) == []
        
        # Single item
        single = [{'symbol': 'EURUSD', 'id': 1}]
        assert stealth.execution_shuffle(single) == single
    
    def test_shuffle_randomness(self):
        """Test that shuffle produces random orders"""
        stealth = StealthProtocol()
        
        original_queue = [
            {'symbol': f'PAIR{i}', 'id': i}
            for i in range(10)
        ]
        
        # Track different orders seen
        orders_seen = set()
        
        for _ in range(100):
            shuffled = stealth.execution_shuffle(original_queue.copy())
            order_tuple = tuple(t['id'] for t in shuffled)
            orders_seen.add(order_tuple)
        
        # Should see multiple different orders
        assert len(orders_seen) > 10
    
    def test_shuffle_delays(self):
        """Test that shuffle adds delays between trades"""
        config = StealthConfig(
            shuffle_delay_min=0.5,
            shuffle_delay_max=2.0
        )
        stealth = StealthProtocol(config)
        
        queue = [
            {'symbol': f'PAIR{i}', 'id': i}
            for i in range(5)
        ]
        
        shuffled = stealth.execution_shuffle(queue)
        
        # First trade should not have delay
        assert 'shuffle_delay' not in shuffled[0]
        
        # Others should have delays
        for trade in shuffled[1:]:
            assert 'shuffle_delay' in trade
            assert 0.5 <= trade['shuffle_delay'] <= 2.0
    
    def test_shuffle_preserves_data(self):
        """Test that shuffle preserves all trade data"""
        stealth = StealthProtocol()
        
        queue = [
            {
                'symbol': 'EURUSD',
                'id': 1,
                'volume': 1.0,
                'tp': 1.2100,
                'sl': 1.1900,
                'custom_field': 'test'
            }
        ]
        
        shuffled = stealth.execution_shuffle(queue)
        
        # Check all fields preserved
        assert shuffled[0]['symbol'] == 'EURUSD'
        assert shuffled[0]['id'] == 1
        assert shuffled[0]['volume'] == 1.0
        assert shuffled[0]['tp'] == 1.2100
        assert shuffled[0]['sl'] == 1.1900
        assert shuffled[0]['custom_field'] == 'test'


class TestFullStealthApplication:
    """Test full stealth protocol application"""
    
    def test_apply_full_stealth_skip_scenarios(self):
        """Test scenarios where trades are skipped"""
        stealth = StealthProtocol()
        
        # Test ghost skip
        with patch.object(stealth, 'ghost_skip', return_value=True):
            result = stealth.apply_full_stealth({'symbol': 'EURUSD'})
            assert result['skip_trade'] is True
            assert 'skip_reason' not in result
        
        # Test volume cap skip
        # Fill up the asset limit
        config = StealthConfig(max_concurrent_per_asset=1)
        stealth = StealthProtocol(config)
        stealth.vol_cap('GBPUSD', 'existing_trade')
        
        result = stealth.apply_full_stealth({
            'symbol': 'GBPUSD',
            'trade_id': 'new_trade'
        })
        assert result['skip_trade'] is True
        assert result['skip_reason'] == 'volume_cap'
    
    def test_apply_full_stealth_modifications(self):
        """Test that all modifications are applied correctly"""
        stealth = StealthProtocol()
        
        trade_params = {
            'symbol': 'EURUSD',
            'trade_id': 'test_123',
            'volume': 1.0,
            'tp': 1.2100,
            'sl': 1.1900
        }
        
        # Mock ghost skip to return False
        with patch.object(stealth, 'ghost_skip', return_value=False):
            result = stealth.apply_full_stealth(trade_params)
        
        # Check modifications applied
        assert 'entry_delay' in result
        assert result['entry_delay'] > 0
        
        assert result['volume'] != trade_params['volume']
        assert 0.93 <= result['volume'] <= 1.07  # ±7% for medium level
        
        assert result['tp'] != trade_params['tp']
        assert result['sl'] != trade_params['sl']
        
        # Original params unchanged
        assert trade_params['volume'] == 1.0
        assert trade_params['tp'] == 1.2100
    
    def test_apply_full_stealth_preserves_extra_fields(self):
        """Test that extra fields are preserved"""
        stealth = StealthProtocol()
        
        trade_params = {
            'symbol': 'USDJPY',
            'volume': 2.0,
            'tp': 110.50,
            'sl': 109.50,
            'comment': 'Test trade',
            'magic_number': 12345,
            'custom_data': {'strategy': 'momentum'}
        }
        
        with patch.object(stealth, 'ghost_skip', return_value=False):
            result = stealth.apply_full_stealth(trade_params)
        
        # Check extra fields preserved
        assert result['comment'] == 'Test trade'
        assert result['magic_number'] == 12345
        assert result['custom_data'] == {'strategy': 'momentum'}


class TestStealthStatistics:
    """Test stealth statistics and reporting"""
    
    def test_get_stealth_stats(self):
        """Test statistics retrieval"""
        config = StealthConfig(level=StealthLevel.HIGH)
        stealth = StealthProtocol(config)
        
        # Add some activity
        stealth.vol_cap('EURUSD', 'trade_1')
        stealth.vol_cap('EURUSD', 'trade_2')
        stealth.vol_cap('GBPUSD', 'trade_3')
        stealth.entry_delay({'symbol': 'EURUSD'})
        stealth.lot_size_jitter(1.0, 'GBPUSD')
        
        stats = stealth.get_stealth_stats()
        
        assert stats['enabled'] is True
        assert stats['level'] == 'high'
        assert stats['active_trades']['EURUSD'] == 2
        assert stats['active_trades']['GBPUSD'] == 1
        assert stats['total_active'] == 3
        assert stats['actions_logged'] >= 5
        assert len(stats['recent_actions']) >= 5
    
    def test_export_logs(self):
        """Test log export functionality"""
        stealth = StealthProtocol()
        
        # Create some actions
        start_time = datetime.now()
        
        stealth.entry_delay({'symbol': 'EURUSD'})
        time.sleep(0.1)
        mid_time = datetime.now()
        
        stealth.lot_size_jitter(1.0, 'GBPUSD')
        stealth.ghost_skip({'symbol': 'USDJPY'})
        
        end_time = datetime.now()
        
        # Export all logs
        all_logs = stealth.export_logs()
        assert len(all_logs) >= 3
        
        # Export with date filter
        filtered_logs = stealth.export_logs(start_date=mid_time)
        assert len(filtered_logs) >= 2
        
        # Check log format
        for log in all_logs:
            assert 'timestamp' in log
            assert 'action_type' in log
            assert 'original' in log
            assert 'modified' in log
            assert 'level' in log
            assert 'details' in log
    
    def test_set_level(self):
        """Test changing stealth level"""
        stealth = StealthProtocol()
        
        initial_level = stealth.config.level
        stealth.set_level(StealthLevel.GHOST)
        
        assert stealth.config.level == StealthLevel.GHOST
        
        # Check that level change was logged
        last_action = stealth.action_log[-1]
        assert last_action.action_type == "level_change"
        assert last_action.original_value == initial_level.value
        assert last_action.modified_value == "ghost"


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases"""
    
    def test_stealth_performance(self):
        """Test that stealth operations are fast"""
        stealth = StealthProtocol()
        
        trade_params = {
            'symbol': 'EURUSD',
            'volume': 1.0,
            'tp': 1.2100,
            'sl': 1.1900
        }
        
        # Time full stealth application
        start = time.time()
        for _ in range(1000):
            stealth.apply_full_stealth(trade_params)
        duration = time.time() - start
        
        # Should process 1000 trades in under 1 second
        assert duration < 1.0
    
    def test_concurrent_modifications(self):
        """Test thread safety considerations"""
        stealth = StealthProtocol()
        
        # Simulate concurrent access to active trades
        for i in range(100):
            stealth.vol_cap(f'PAIR{i % 10}', f'trade_{i}')
        
        # Verify consistency
        total_trades = sum(len(trades) for trades in stealth.active_trades.values())
        assert total_trades <= stealth.config.max_total_concurrent
    
    def test_extreme_values(self):
        """Test handling of extreme values"""
        stealth = StealthProtocol()
        
        # Test extreme lot sizes
        assert stealth.lot_size_jitter(0.01, 'EURUSD') > 0
        assert stealth.lot_size_jitter(100.0, 'EURUSD') > 0
        
        # Test extreme prices
        tp, sl = stealth.tp_sl_offset(0.00001, 0.00001, 'BTCUSD')
        assert tp > 0 and sl > 0
        
        tp, sl = stealth.tp_sl_offset(50000.0, 49000.0, 'BTCUSD')
        assert tp > 0 and sl > 0
    
    def test_memory_usage(self):
        """Test that stealth protocol doesn't leak memory"""
        import gc
        
        stealth = StealthProtocol()
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many operations
        for i in range(10000):
            trade_params = {
                'symbol': f'PAIR{i % 20}',
                'trade_id': f'trade_{i}',
                'volume': 1.0 + (i % 10) / 10,
                'tp': 1.2000 + (i % 100) / 10000,
                'sl': 1.1900 - (i % 100) / 10000
            }
            stealth.apply_full_stealth(trade_params)
            
            # Simulate some trades completing
            if i % 100 == 0 and i > 0:
                for asset in list(stealth.active_trades.keys()):
                    if stealth.active_trades[asset]:
                        trade_to_remove = stealth.active_trades[asset][0]
                        stealth.remove_completed_trade(asset, trade_to_remove)
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow for some growth but not excessive
        object_growth = final_objects - initial_objects
        assert object_growth < 5000  # Reasonable threshold


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_high_frequency_trading_scenario(self):
        """Test stealth in high-frequency trading scenario"""
        config = StealthConfig(
            level=StealthLevel.HIGH,
            entry_delay_min=0.1,
            entry_delay_max=0.5,
            max_concurrent_per_asset=5,
            max_total_concurrent=20
        )
        stealth = StealthProtocol(config)
        
        trades_executed = []
        trades_skipped = []
        
        # Simulate rapid-fire signals
        for i in range(100):
            trade = {
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'][i % 4],
                'trade_id': f'hft_{i}',
                'volume': 0.1,
                'tp': 1.2100 + (i % 10) / 10000,
                'sl': 1.1900 - (i % 10) / 10000
            }
            
            result = stealth.apply_full_stealth(trade)
            
            if result.get('skip_trade'):
                trades_skipped.append(result)
            else:
                trades_executed.append(result)
                
                # Simulate some trades closing
                if i % 10 == 0 and i > 0:
                    asset = trades_executed[0]['symbol']
                    trade_id = trades_executed[0]['trade_id']
                    stealth.remove_completed_trade(asset, trade_id)
                    trades_executed.pop(0)
        
        # Verify reasonable skip rate for high stealth
        skip_rate = len(trades_skipped) / 100
        assert 0.20 <= skip_rate <= 0.40  # High stealth should skip 20-40%
        
        # Verify volume caps were respected
        assert all(t.get('skip_reason') in [None, 'volume_cap'] for t in trades_skipped)
    
    def test_market_maker_scenario(self):
        """Test stealth for market maker with many simultaneous positions"""
        config = StealthConfig(
            level=StealthLevel.MEDIUM,
            max_concurrent_per_asset=10,
            max_total_concurrent=50,
            shuffle_queue=True
        )
        stealth = StealthProtocol(config)
        
        # Create batch of trades
        trade_batch = []
        for i in range(20):
            trade_batch.append({
                'symbol': 'EURUSD',
                'trade_id': f'mm_{i}',
                'volume': 0.5 + (i % 5) / 10,
                'tp': 1.2050 + (i % 20) / 10000,
                'sl': 1.1950 - (i % 20) / 10000
            })
        
        # Shuffle the batch
        shuffled_batch = stealth.execution_shuffle(trade_batch)
        
        # Verify shuffle occurred
        original_ids = [t['trade_id'] for t in trade_batch]
        shuffled_ids = [t['trade_id'] for t in shuffled_batch]
        assert original_ids != shuffled_ids or len(trade_batch) == 1
        
        # Apply stealth to each trade
        results = []
        for trade in shuffled_batch:
            result = stealth.apply_full_stealth(trade)
            results.append(result)
            
            # Respect shuffle delays
            if 'shuffle_delay' in trade:
                time.sleep(0.01)  # Simulate delay
        
        # Verify modifications applied
        for i, result in enumerate(results):
            if not result.get('skip_trade'):
                assert result['volume'] != trade_batch[i]['volume']
                assert 'entry_delay' in result
    
    def test_scalping_scenario(self):
        """Test stealth for scalping strategy"""
        config = StealthConfig(
            level=StealthLevel.LOW,  # Low stealth for quick execution
            entry_delay_min=0.1,
            entry_delay_max=0.5,
            lot_jitter_min=0.01,
            lot_jitter_max=0.03,
            ghost_skip_rate=0.05  # Very low skip rate
        )
        stealth = StealthProtocol(config)
        
        scalp_trades = []
        for i in range(50):
            trade = {
                'symbol': 'EURUSD',
                'trade_id': f'scalp_{i}',
                'volume': 1.0,
                'tp': 1.2010,  # 10 pip TP
                'sl': 1.1995   # 5 pip SL
            }
            
            result = stealth.apply_full_stealth(trade)
            scalp_trades.append(result)
        
        # Check appropriate modifications for scalping
        executed = [t for t in scalp_trades if not t.get('skip_trade')]
        skipped = [t for t in scalp_trades if t.get('skip_trade')]
        
        # Very few skips for scalping
        assert len(skipped) < 5  # Less than 10% skipped
        
        # Minimal delays
        delays = [t['entry_delay'] for t in executed]
        assert all(d <= 1.0 for d in delays)  # All delays under 1 second
        
        # Small lot variations
        for trade in executed:
            original = 1.0
            variation = abs(trade['volume'] - original) / original
            assert variation <= 0.03  # Max 3% variation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])