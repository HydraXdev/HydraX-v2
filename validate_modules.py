#!/usr/bin/env python3
"""
Walk-Forward Validation for Phase 1 Universal Modules

PURPOSE:
    Validate all 5 Phase 1 modules using walk-forward validation to prevent overfitting
    Tests modules on truly unseen future data using TimeSeriesSplit

MODULES TESTED:
    1. Order Flow Analyzer (60-75% accuracy boost expected)
    2. Volume Analyzer (15-35% Sharpe improvement expected)
    3. Sentiment Analyzer (20% better confirmation expected)
    4. Multi-Timeframe Analyzer (70-80% win rate expected)
    5. Anomaly Detector (20-30% drawdown reduction expected)

USAGE:
    python3 validate_modules.py [--module MODULE_NAME] [--symbol SYMBOL]

VALIDATION CRITERIA:
    - avg_sharpe > 0.5 (baseline acceptable)
    - worst_case_sharpe > 0 (no catastrophic failures)
    - sharpe_stability < avg_sharpe * 0.5 (consistent performance)

OUTPUT:
    - Validation report per module
    - Pass/Fail status
    - Recommendations for refinement
"""

import os
import sys
import json
import argparse
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit

# Add services directory to path
sys.path.insert(0, '/root/HydraX-v2')

# Import Phase 1 modules
from services.order_flow_analyzer import OrderFlowAnalyzer
from services.volume_analyzer import VolumeAnalyzer
from services.sentiment_analyzer import SentimentAnalyzer
from services.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from services.anomaly_detector import AnomalyDetector

# Data directory
DATA_DIR = '/root/HydraX-v2/backtest_data'

class WalkForwardValidator:
    """
    Walk-forward validation for time series strategies

    Prevents overfitting by testing on unseen future data using rolling windows
    """

    def __init__(self, n_splits: int = 5, baseline_sharpe: float = 0.5):
        """
        Args:
            n_splits: Number of walk-forward splits (default 5)
            baseline_sharpe: Minimum acceptable Sharpe ratio
        """
        self.n_splits = n_splits
        self.baseline_sharpe = baseline_sharpe
        self.tscv = TimeSeriesSplit(n_splits=n_splits)

    def calculate_sharpe(self, returns: List[float]) -> float:
        """
        Calculate Sharpe ratio from returns

        Args:
            returns: List of returns (1.0 = breakeven, >1.0 = profit, <1.0 = loss)

        Returns:
            Sharpe ratio (higher is better, >0.5 acceptable)
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Convert to excess returns (subtract 1.0)
        excess_returns = [r - 1.0 for r in returns]

        # Calculate Sharpe: mean / std
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns)

        if std_return == 0:
            return 0.0

        # Annualize assuming daily data
        sharpe = (mean_return / std_return) * np.sqrt(252)

        return sharpe

    def validate_module(
        self,
        module,
        candles: List[Dict],
        symbol: str,
        test_func
    ) -> Dict:
        """
        Run walk-forward validation on a module

        Args:
            module: Module instance (OrderFlowAnalyzer, etc.)
            candles: Historical candle data
            symbol: Symbol being tested
            test_func: Function to test module (returns signal or analysis)

        Returns:
            Dict with validation results
        """
        print(f"\n{'='*80}")
        print(f"🔍 WALK-FORWARD VALIDATION: {module.__class__.__name__}")
        print(f"{'='*80}")

        split_results = []

        for split_num, (train_idx, test_idx) in enumerate(self.tscv.split(candles)):
            print(f"\n📊 Split {split_num + 1}/{self.n_splits}")
            print(f"   Train: {len(train_idx)} candles ({train_idx[0]}-{train_idx[-1]})")
            print(f"   Test:  {len(test_idx)} candles ({test_idx[0]}-{test_idx[-1]})")

            # Get test data
            test_data = [candles[i] for i in test_idx]

            # Run module on test data
            signals = []
            returns = []

            for i in range(len(test_data) - 100):  # Need lookback
                window = test_data[i:i+100]

                try:
                    result = test_func(module, symbol, window)

                    if result and result.get('signal') in ['BUY', 'SELL']:
                        signals.append(result)

                        # Simulate trade outcome (simplified)
                        # In reality, would need TP/SL tracking
                        entry_price = window[-1]['close']

                        # Look ahead 50 candles for outcome
                        if i + 150 < len(test_data):
                            future = test_data[i+100:i+150]

                            # Check if TP hit (simplified: 30 pips)
                            tp_distance = 30 / 10000  # Convert pips to price
                            sl_distance = 15 / 10000

                            if result['signal'] == 'BUY':
                                tp_price = entry_price + tp_distance
                                sl_price = entry_price - sl_distance

                                # Check outcome
                                for candle in future:
                                    if candle['high'] >= tp_price:
                                        returns.append(2.0)  # 2:1 R/R
                                        break
                                    elif candle['low'] <= sl_price:
                                        returns.append(0.0)  # Full loss
                                        break
                                else:
                                    returns.append(1.0)  # Breakeven

                            else:  # SELL
                                tp_price = entry_price - tp_distance
                                sl_price = entry_price + sl_distance

                                for candle in future:
                                    if candle['low'] <= tp_price:
                                        returns.append(2.0)
                                        break
                                    elif candle['high'] >= sl_price:
                                        returns.append(0.0)
                                        break
                                else:
                                    returns.append(1.0)

                except Exception as e:
                    print(f"   ⚠️  Error testing candle {i}: {e}")
                    continue

            # Calculate Sharpe for this split
            sharpe = self.calculate_sharpe(returns) if returns else 0.0
            win_rate = (len([r for r in returns if r > 1.0]) / len(returns) * 100) if returns else 0.0

            split_result = {
                'split': split_num + 1,
                'signals': len(signals),
                'trades': len(returns),
                'sharpe': sharpe,
                'win_rate': win_rate,
                'returns': returns
            }

            split_results.append(split_result)

            print(f"   ✅ Signals: {len(signals)}, Trades: {len(returns)}")
            print(f"   📊 Sharpe: {sharpe:.2f}, Win Rate: {win_rate:.1f}%")

        # Calculate aggregate statistics
        sharpe_values = [r['sharpe'] for r in split_results]
        avg_sharpe = np.mean(sharpe_values)
        worst_case = np.min(sharpe_values)
        sharpe_std = np.std(sharpe_values)

        # Validation criteria
        is_valid = (
            avg_sharpe > self.baseline_sharpe and
            worst_case > 0 and
            sharpe_std < avg_sharpe * 0.5
        )

        return {
            'module': module.__class__.__name__,
            'symbol': symbol,
            'splits': self.n_splits,
            'avg_sharpe': avg_sharpe,
            'worst_case_sharpe': worst_case,
            'sharpe_stability': sharpe_std,
            'is_valid': is_valid,
            'split_results': split_results,
            'validation_criteria': {
                'avg_sharpe_threshold': self.baseline_sharpe,
                'avg_sharpe_pass': avg_sharpe > self.baseline_sharpe,
                'worst_case_threshold': 0.0,
                'worst_case_pass': worst_case > 0,
                'stability_threshold': avg_sharpe * 0.5,
                'stability_pass': sharpe_std < avg_sharpe * 0.5
            }
        }


def load_candles(symbol: str, timeframe: str) -> List[Dict]:
    """Load candles from JSON file"""
    filepath = f"{DATA_DIR}/{symbol}_{timeframe}.json"

    if not os.path.exists(filepath):
        print(f"❌ Data file not found: {filepath}")
        print(f"   Run fetch_historical_data.py first!")
        return []

    with open(filepath, 'r') as f:
        data = json.load(f)

    return data['candles']


def test_order_flow(module, symbol: str, candles: List[Dict]) -> Dict:
    """Test Order Flow Analyzer"""
    return module.get_order_flow_signal(symbol, candles)


def test_volume(module, symbol: str, candles: List[Dict]) -> Dict:
    """Test Volume Analyzer"""
    return module.get_volume_signal(symbol, candles)


def test_sentiment(module, symbol: str, candles: List[Dict]) -> Dict:
    """Test Sentiment Analyzer (less frequent)"""
    # Only test every 60 candles (sentiment changes slower)
    if len(candles) % 60 == 0:
        return module.get_sentiment_signal(symbol)
    return {}


def test_mtf(module, symbol: str, candles: List[Dict]) -> Dict:
    """Test Multi-Timeframe Analyzer"""
    # Need H4 candles too
    h4_candles = load_candles(symbol.replace('_', ''), 'H4')

    if len(h4_candles) < 100:
        return {}

    # Use last 100 H4 candles
    htf = h4_candles[-100:]

    return module.get_mtf_signal(symbol, htf, candles)


def test_anomaly(module, symbol: str, candles: List[Dict]) -> Dict:
    """Test Anomaly Detector"""
    result = module.get_anomaly_signal(symbol, candles)

    # Convert to signal format
    if result.get('overall_risk') in ['EXTREME', 'HIGH']:
        return {'signal': 'AVOID'}

    return {}


def main():
    """Run walk-forward validation on all Phase 1 modules"""

    parser = argparse.ArgumentParser(description='Validate Phase 1 modules')
    parser.add_argument('--module', help='Specific module to test', choices=[
        'order_flow', 'volume', 'sentiment', 'mtf', 'anomaly', 'all'
    ], default='all')
    parser.add_argument('--symbol', help='Symbol to test', default='EURUSD')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("🛡️  WALK-FORWARD VALIDATION - PHASE 1 UNIVERSAL MODULES")
    print("="*80 + "\n")

    # Load data
    print(f"📊 Loading {args.symbol} M1 candles...")
    candles = load_candles(args.symbol, 'M1')

    if not candles:
        print("❌ Failed to load candle data")
        return

    print(f"✅ Loaded {len(candles):,} candles\n")

    # Initialize validator
    validator = WalkForwardValidator(n_splits=5, baseline_sharpe=0.5)

    # Initialize modules
    modules_to_test = []

    if args.module in ['order_flow', 'all']:
        modules_to_test.append(('order_flow', OrderFlowAnalyzer(), test_order_flow))

    if args.module in ['volume', 'all']:
        modules_to_test.append(('volume', VolumeAnalyzer(), test_volume))

    if args.module in ['sentiment', 'all']:
        finnhub_key = 'd3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
        modules_to_test.append(('sentiment', SentimentAnalyzer(finnhub_key), test_sentiment))

    if args.module in ['mtf', 'all']:
        modules_to_test.append(('mtf', MultiTimeframeAnalyzer(), test_mtf))

    if args.module in ['anomaly', 'all']:
        modules_to_test.append(('anomaly', AnomalyDetector(), test_anomaly))

    # Run validation
    results = []

    for name, module, test_func in modules_to_test:
        result = validator.validate_module(module, candles, args.symbol, test_func)
        results.append(result)

        # Print summary
        print(f"\n{'='*80}")
        print(f"📋 VALIDATION SUMMARY: {result['module']}")
        print(f"{'='*80}")
        print(f"   Avg Sharpe:       {result['avg_sharpe']:.2f} (threshold: {result['validation_criteria']['avg_sharpe_threshold']:.2f})")
        print(f"   Worst Case:       {result['worst_case_sharpe']:.2f} (threshold: {result['validation_criteria']['worst_case_threshold']:.2f})")
        print(f"   Stability (std):  {result['sharpe_stability']:.2f} (threshold: {result['validation_criteria']['stability_threshold']:.2f})")
        print(f"   Status:           {'✅ PASS' if result['is_valid'] else '❌ FAIL'}")

    # Save results
    output_file = f"{DATA_DIR}/validation_results_{args.symbol}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'symbol': args.symbol,
            'candles_tested': len(candles),
            'modules': results
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Overall summary
    passed = sum(1 for r in results if r['is_valid'])
    total = len(results)

    print(f"\n{'='*80}")
    print(f"🎯 OVERALL VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"   Modules Tested: {total}")
    print(f"   Passed:         {passed}")
    print(f"   Failed:         {total - passed}")
    print(f"   Pass Rate:      {passed/total*100:.1f}%")

    if passed == total:
        print(f"\n✅ ALL MODULES PASSED - Ready for integration!")
    else:
        print(f"\n⚠️  {total - passed} module(s) need refinement")
        print(f"   See {output_file} for details")

    print()


if __name__ == '__main__':
    main()
