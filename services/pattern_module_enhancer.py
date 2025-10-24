#!/usr/bin/env python3
"""
PATTERN MODULE ENHANCER - Phase 1 Universal Module Integration

PURPOSE:
    Hook Phase 1 modules into Elite Guard's pattern detection pipeline
    Enhance pattern confidence with institutional intelligence layers

USAGE:
    enhancer = PatternModuleEnhancer()
    enhanced_signal = enhancer.enhance_pattern(pattern_signal, symbol, m1_candles, h4_candles)

MODULES INTEGRATED:
    1. Order Flow Analyzer - Institutional buying/selling pressure
    2. Volume Analyzer - Smart money volume confirmation
    3. Sentiment Analyzer - News/social sentiment overlay
    4. Multi-Timeframe Analyzer - HTF/LTF confluence
    5. Anomaly Detector - Extreme risk detection

CALIBRATION:
    Bayesian confidence calibrator ensures scores match real win rates
    Prior: Elite Guard's 68% historical win rate
"""

import sys
from typing import Dict, List, Optional

sys.path.insert(0, '/root/HydraX-v2')

# Import Phase 1 modules
from services.order_flow_analyzer import OrderFlowAnalyzer
from services.volume_analyzer import VolumeAnalyzer
from services.sentiment_analyzer import SentimentAnalyzer
from services.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from services.anomaly_detector import AnomalyDetector

# Import Bayesian confidence calibrator
from services.confidence_calibrator import ConfidenceCalibrator


class PatternModuleEnhancer:
    """
    Enhances Elite Guard pattern signals with Phase 1 universal modules

    Integration point: After pattern detection, before ML filter
    """

    def __init__(self, elite_guard_baseline_wr: float = 0.68, finnhub_api_key: str = 'd3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'):
        """
        Initialize all Phase 1 modules and calibrator

        Args:
            elite_guard_baseline_wr: Elite Guard's proven historical win rate
            finnhub_api_key: Finnhub API key for sentiment analysis
        """
        print("🔧 Initializing Pattern Module Enhancer...")

        # Initialize all 5 Phase 1 modules
        self.order_flow = OrderFlowAnalyzer()
        self.volume = VolumeAnalyzer()
        self.sentiment = SentimentAnalyzer(finnhub_api_key=finnhub_api_key)
        self.mtf = MultiTimeframeAnalyzer()
        self.anomaly = AnomalyDetector()

        # Initialize Bayesian confidence calibrator
        # Prior: Elite Guard's 68% win rate over 100 trades
        self.calibrator = ConfidenceCalibrator(
            prior_win_rate=elite_guard_baseline_wr,
            total_trades=100
        )

        print(f"✅ Module Enhancer ready (baseline: {elite_guard_baseline_wr:.1%})")

    def enhance_pattern(
        self,
        pattern_signal: Dict,
        symbol: str,
        m1_candles: List[Dict],
        h4_candles: List[Dict],
        pattern_history: Optional[Dict] = None
    ) -> Dict:
        """
        Enhance pattern signal with Phase 1 modules + Bayesian calibration

        Args:
            pattern_signal: Dict with 'pattern', 'direction', 'confidence', etc.
            symbol: Trading symbol
            m1_candles: M1 candles (minimum 100 for modules)
            h4_candles: H4 candles (minimum 50 for MTF)
            pattern_history: Optional pattern-specific win/loss history

        Returns:
            Enhanced signal dict with:
                - Original signal fields
                - calibrated_confidence: Bayesian-adjusted confidence
                - module_signals: Dict of module results
                - evidence_score: Cumulative evidence adjustment
                - confidence_interval: (lower, upper) 95% CI
        """
        # Extract pattern info
        base_confidence = pattern_signal.get('confidence', 70)
        direction = pattern_signal.get('direction', 'BUY')
        pattern_type = pattern_signal.get('pattern', 'UNKNOWN')

        print(f"\n🔍 Enhancing {pattern_type} {direction} signal on {symbol}")
        print(f"   Base confidence: {base_confidence}%")

        # 1. ORDER FLOW ANALYSIS
        order_flow_result = {'signal': 'NEUTRAL'}
        if len(m1_candles) >= 50:
            try:
                order_flow_result = self.order_flow.get_order_flow_signal(symbol, m1_candles[-100:])
                print(f"   📊 Order Flow: {order_flow_result['signal']} (conf: {order_flow_result.get('confidence', 0)}%)")
            except Exception as e:
                print(f"   ⚠️  Order Flow failed: {e}")
        else:
            print(f"   ⚠️  Order Flow skipped: need 50+ M1 candles, have {len(m1_candles)}")

        # 2. VOLUME ANALYSIS
        volume_result = {'signal': 'NEUTRAL'}
        if len(m1_candles) >= 50:
            try:
                volume_result = self.volume.get_volume_signal(symbol, m1_candles[-100:])
                print(f"   📊 Volume: {volume_result['signal']} (spike: {volume_result.get('volume_spike', False)})")
            except Exception as e:
                print(f"   ⚠️  Volume failed: {e}")
        else:
            print(f"   ⚠️  Volume skipped: need 50+ M1 candles")

        # 3. SENTIMENT ANALYSIS
        sentiment_result = {'signal': 'NEUTRAL'}
        try:
            sentiment_result = self.sentiment.get_sentiment_signal(symbol)
            print(f"   📊 Sentiment: {sentiment_result['signal']} (score: {sentiment_result.get('composite_score', 0):.1f})")
        except Exception as e:
            print(f"   ⚠️  Sentiment failed: {e}")

        # 4. MULTI-TIMEFRAME ANALYSIS
        mtf_result = {'signal': 'NEUTRAL'}
        if len(h4_candles) >= 50 and len(m1_candles) >= 50:
            try:
                mtf_result = self.mtf.get_mtf_signal(symbol, h4_candles[-50:], m1_candles[-100:])
                print(f"   📊 MTF: {mtf_result['signal']} (aligned: {mtf_result.get('htf_ltf_aligned', False)})")
            except Exception as e:
                print(f"   ⚠️  MTF failed: {e}")
        else:
            print(f"   ⚠️  MTF skipped: need 50+ H4 and 50+ M1 candles")

        # 5. ANOMALY DETECTION
        anomaly_result = {'overall_risk': 'NONE'}
        if len(m1_candles) >= 50:
            try:
                anomaly_result = self.anomaly.get_anomaly_signal(symbol, m1_candles[-100:])
                print(f"   📊 Anomaly: {anomaly_result['overall_risk']} risk")
            except Exception as e:
                print(f"   ⚠️  Anomaly failed: {e}")
        else:
            print(f"   ⚠️  Anomaly skipped: need 50+ M1 candles")

        # BAYESIAN CONFIDENCE CALIBRATION
        module_signals = {
            'pattern_direction': direction,
            'order_flow': order_flow_result.get('signal', 'NEUTRAL'),
            'volume': volume_result.get('signal', 'NEUTRAL'),
            'volume_spike': volume_result.get('volume_spike', False),
            'sentiment': sentiment_result.get('signal', 'NEUTRAL'),
            'mtf_aligned': mtf_result.get('htf_ltf_aligned', False),
            'contrarian': sentiment_result.get('contrarian_opportunity', False),
            'anomaly_risk': anomaly_result.get('overall_risk', 'NONE')
        }

        calibration_result = self.calibrator.calibrate(
            base_confidence=base_confidence,
            module_signals=module_signals,
            pattern_history=pattern_history
        )

        print(f"   🎯 Calibrated confidence: {calibration_result['calibrated_confidence']}%")
        print(f"   📈 Evidence score: {calibration_result['evidence_score']:+.2f}")
        print(f"   📊 95% CI: [{calibration_result['confidence_interval'][0]}%, {calibration_result['confidence_interval'][1]}%]")

        # Build enhanced signal
        enhanced_signal = pattern_signal.copy()
        enhanced_signal.update({
            'base_confidence': base_confidence,
            'calibrated_confidence': calibration_result['calibrated_confidence'],
            'expected_win_rate': calibration_result['expected_win_rate'],
            'evidence_score': calibration_result['evidence_score'],
            'confidence_interval': calibration_result['confidence_interval'],
            'module_signals': module_signals,
            'module_results': {
                'order_flow': order_flow_result,
                'volume': volume_result,
                'sentiment': sentiment_result,
                'mtf': mtf_result,
                'anomaly': anomaly_result
            },
            'evidence_breakdown': calibration_result.get('evidence_breakdown', [])
        })

        return enhanced_signal

    def update_pattern_history(self, pattern_type: str, win: bool):
        """
        Update pattern-specific history for better calibration

        Args:
            pattern_type: Pattern name (VCB_BREAKOUT, LIQUIDITY_SWEEP, etc.)
            win: True if signal hit TP, False if hit SL
        """
        # This would update a persistent pattern history database
        # For now, just update the calibrator's global prior
        self.calibrator.update_from_result(win)

        current_baseline = self.calibrator.get_current_baseline()
        print(f"📊 Updated baseline win rate: {current_baseline:.1%}")


# Test harness
if __name__ == '__main__':
    print("\n" + "="*80)
    print("🎯 PATTERN MODULE ENHANCER TEST")
    print("="*80 + "\n")

    # Initialize enhancer
    enhancer = PatternModuleEnhancer(elite_guard_baseline_wr=0.68)

    # Mock pattern signal (from Elite Guard)
    mock_pattern = {
        'pattern': 'VCB_BREAKOUT',
        'direction': 'BUY',
        'confidence': 70,
        'entry_price': 1.1000,
        'sl': 1.0950,
        'tp': 1.1100
    }

    # Mock candle data (simplified)
    mock_m1_candles = [
        {'open': 1.0990, 'high': 1.0995, 'low': 1.0985, 'close': 1.0992, 'volume': 1000}
        for _ in range(100)
    ]

    mock_h4_candles = [
        {'open': 1.0980, 'high': 1.1000, 'low': 1.0970, 'close': 1.0995, 'volume': 50000}
        for _ in range(50)
    ]

    # Enhance pattern
    enhanced = enhancer.enhance_pattern(
        pattern_signal=mock_pattern,
        symbol='EURUSD',
        m1_candles=mock_m1_candles,
        h4_candles=mock_h4_candles
    )

    print("\n" + "="*80)
    print("✅ ENHANCEMENT COMPLETE")
    print("="*80)
    print(f"Base confidence: {enhanced['base_confidence']}%")
    print(f"Calibrated confidence: {enhanced['calibrated_confidence']}%")
    print(f"Expected win rate: {enhanced['expected_win_rate']:.1%}")
    print(f"Evidence score: {enhanced['evidence_score']:+.2f}")
    print()
