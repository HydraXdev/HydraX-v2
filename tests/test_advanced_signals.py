"""
Test suite for advanced signal intelligence system
"""

import pytest
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.bitten_core.advanced_intelligence_aggregator import (
    AdvancedIntelligenceAggregator,
    OrderFlowIntelligence,
    MLPredictionIntelligence,
    AdvancedSentimentIntelligence,
    CrossAssetIntelligence
)
from src.bitten_core.signal_fusion import IntelSource, FusedSignal, ConfidenceTier
from src.bitten_core.smart_execution_layer import SmartExecutionEngine, ExecutionStrategy
from src.bitten_core.advanced_signal_integration import AdvancedSignalIntegration


class TestAdvancedIntelligence:
    """Test advanced intelligence components"""
    
    @pytest.fixture
    def market_data(self):
        """Sample market data for testing"""
        return {
            'pair': 'EURUSD',
            'timestamp': datetime.now(),
            'current_price': 1.0850,
            'volume': 50000,
            'spread': 1.2,
            'normal_spread': 1.5,
            'atr': 25,
            'rsi': 55,
            'macd': 0.0002,
            'bb_upper': 1.0870,
            'bb_lower': 1.0830,
            'volume_ratio': 1.2,
            'price_history': [1.0840 + i * 0.0001 for i in range(100)],
            'order_book': {
                'bids': [(1.0849, 1000), (1.0848, 2000), (1.0847, 1500)],
                'asks': [(1.0851, 1200), (1.0852, 1800), (1.0853, 2200)],
                'timestamp': datetime.now()
            }
        }
    
    def test_order_flow_intelligence(self, market_data):
        """Test order flow analysis"""
        order_flow = OrderFlowIntelligence()
        
        # Mock the order flow scorer
        if order_flow.order_flow_scorer is None:
            pytest.skip("Order flow module not available")
        
        # Test with sample data
        result = asyncio.run(order_flow.analyze('EURUSD', market_data))
        
        if result:
            assert isinstance(result, IntelSource)
            assert result.source_type == 'order_flow'
            assert result.signal in ['BUY', 'SELL']
            assert 0 <= result.confidence <= 100
    
    def test_ml_prediction_intelligence(self, market_data):
        """Test ML prediction"""
        ml_intel = MLPredictionIntelligence()
        
        if ml_intel.inference_engine is None:
            pytest.skip("ML module not available")
        
        result = asyncio.run(ml_intel.analyze('EURUSD', market_data))
        
        if result:
            assert isinstance(result, IntelSource)
            assert result.source_type == 'ai_ml'
            assert result.signal in ['BUY', 'SELL']
            assert 0 <= result.confidence <= 100
    
    def test_advanced_aggregator(self, market_data):
        """Test the complete aggregator"""
        aggregator = AdvancedIntelligenceAggregator()
        
        # Test intelligence collection
        sources = asyncio.run(aggregator.collect_all_intelligence('EURUSD', market_data))
        
        assert isinstance(sources, list)
        assert len(sources) >= 3  # Should have at least basic sources
        
        # Test signal fusion
        signal = asyncio.run(aggregator.generate_fused_signal('EURUSD', market_data))
        
        if signal:
            assert isinstance(signal, FusedSignal)
            assert signal.direction in ['BUY', 'SELL']
            assert signal.confidence >= 60  # Minimum threshold
            assert signal.tier in ConfidenceTier


class TestSmartExecution:
    """Test smart execution layer"""
    
    @pytest.fixture
    def sample_signal(self):
        """Sample signal for testing"""
        return {
            'signal_id': 'TEST_001',
            'pair': 'EURUSD',
            'action': 'BUY',
            'entry': 1.0850,
            'sl': 1.0830,
            'tp': 1.0870,
            'confidence': 85,
            'tier': 'precision'
        }
    
    def test_execution_plan_creation(self, sample_signal, market_data):
        """Test execution plan creation"""
        engine = SmartExecutionEngine()
        
        plan = asyncio.run(engine.create_execution_plan(sample_signal, market_data))
        
        assert plan.signal_id == 'TEST_001'
        assert isinstance(plan.strategy, ExecutionStrategy)
        assert len(plan.entry_levels) > 0
        assert len(plan.sizes) == len(plan.entry_levels)
        assert sum(plan.sizes) == pytest.approx(1.0, 0.01)
    
    def test_different_strategies(self, market_data):
        """Test different execution strategies"""
        engine = SmartExecutionEngine()
        
        # High confidence signal
        high_conf_signal = {
            'signal_id': 'HIGH_001',
            'pair': 'EURUSD',
            'action': 'BUY',
            'entry': 1.0850,
            'confidence': 92,
            'tier': 'sniper'
        }
        
        plan = asyncio.run(engine.create_execution_plan(high_conf_signal, market_data))
        assert plan.strategy in [ExecutionStrategy.IMMEDIATE, ExecutionStrategy.TWAP]
        
        # Low confidence signal
        low_conf_signal = {
            'signal_id': 'LOW_001',
            'pair': 'EURUSD',
            'action': 'SELL',
            'entry': 1.0850,
            'confidence': 65,
            'tier': 'training'
        }
        
        plan = asyncio.run(engine.create_execution_plan(low_conf_signal, market_data))
        assert plan.strategy in [ExecutionStrategy.PATIENT, ExecutionStrategy.SCALED]


class TestIntegration:
    """Test complete integration"""
    
    def test_signal_integration_init(self):
        """Test integration initialization"""
        integration = AdvancedSignalIntegration()
        
        assert integration.advanced_aggregator is not None
        assert integration.telegram_router is not None
        assert integration.signal_display is not None
        assert len(integration.monitored_pairs) > 0
    
    def test_market_data_collection(self):
        """Test market data collection"""
        integration = AdvancedSignalIntegration()
        
        data = asyncio.run(integration._collect_market_data('EURUSD'))
        
        assert data['pair'] == 'EURUSD'
        assert 'current_price' in data
        assert 'order_book' in data
        assert 'volume' in data
    
    def test_signal_conversion(self):
        """Test signal format conversion"""
        integration = AdvancedSignalIntegration()
        
        # Create mock fused signal
        sources = [
            IntelSource('test1', 'technical', 'BUY', 80, 0.5),
            IntelSource('test2', 'sentiment', 'BUY', 75, 0.5)
        ]
        
        fused_signal = FusedSignal(
            signal_id='FUSED_TEST',
            pair='EURUSD',
            direction='BUY',
            confidence=85,
            tier=ConfidenceTier.PRECISION,
            entry=1.0850,
            sl=1.0830,
            tp=1.0870,
            sources=sources,
            fusion_scores={'weighted_confidence': 77.5}
        )
        
        bitten_signal = integration._convert_to_bitten_format(fused_signal)
        
        assert bitten_signal['signal_id'] == 'FUSED_TEST'
        assert bitten_signal['action'] == 'BUY'
        assert bitten_signal['confidence'] == 85
        assert bitten_signal['tier'] == 'precision'


def test_system_stats():
    """Test system statistics gathering"""
    integration = AdvancedSignalIntegration()
    
    stats = integration.get_system_stats()
    
    assert 'monitoring_active' in stats
    assert 'monitored_pairs' in stats
    assert 'performance' in stats
    assert 'tier_routing' in stats


if __name__ == '__main__':
    # Run specific tests
    print("Testing Advanced Signal Intelligence System...")
    
    # Test components
    test_intel = TestAdvancedIntelligence()
    market_data = test_intel.market_data()
    
    print("✓ Testing Order Flow Intelligence...")
    test_intel.test_order_flow_intelligence(market_data)
    
    print("✓ Testing ML Prediction...")
    test_intel.test_ml_prediction_intelligence(market_data)
    
    print("✓ Testing Advanced Aggregator...")
    test_intel.test_advanced_aggregator(market_data)
    
    # Test execution
    test_exec = TestSmartExecution()
    signal = test_exec.sample_signal()
    
    print("✓ Testing Execution Plans...")
    test_exec.test_execution_plan_creation(signal, market_data)
    
    print("✓ Testing Strategy Selection...")
    test_exec.test_different_strategies(market_data)
    
    # Test integration
    print("✓ Testing System Integration...")
    test_integration = TestIntegration()
    test_integration.test_signal_integration_init()
    test_integration.test_market_data_collection()
    
    print("\n✅ All tests completed!")