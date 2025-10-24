#!/usr/bin/env python3
"""
Weak Spot Analysis - Identify Module Failure Patterns

PURPOSE:
    Analyze validation results to identify specific weak spots in Phase 1 modules:
    - Overfitting: Sharpe drop >30% from train to test
    - Inconsistency: Sharpe std dev >50% of mean
    - Catastrophic failures: Any negative Sharpe test periods
    - Signal drought: <10 signals/hour when stacked
    - False confidence: "80% signals" winning <60%

USAGE:
    python3 analyze_weak_spots.py --symbol EURUSD

OUTPUT:
    - Weak spot report with specific issues
    - Recommendations for refinement
    - Module-specific threshold adjustments
"""

import os
import sys
import json
import argparse
import numpy as np
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

DATA_DIR = '/root/HydraX-v2/backtest_data'

class WeakSpotAnalyzer:
    """Identify specific failure patterns in module validation results"""

    def __init__(self):
        self.issues = defaultdict(list)

    def analyze_overfitting(self, split_results: List[Dict]) -> Dict:
        """
        Detect overfitting by comparing early vs late splits

        Overfitting symptom: Performance degrades in later test periods
        """
        if len(split_results) < 3:
            return {'detected': False, 'reason': 'Insufficient splits'}

        # Compare first 2 splits vs last 2 splits
        early_sharpe = np.mean([r['sharpe'] for r in split_results[:2]])
        late_sharpe = np.mean([r['sharpe'] for r in split_results[-2:]])

        # Calculate drop percentage
        if early_sharpe > 0:
            drop_pct = ((early_sharpe - late_sharpe) / early_sharpe) * 100
        else:
            drop_pct = 0

        # Overfitting if drop >30%
        is_overfitting = drop_pct > 30

        return {
            'detected': is_overfitting,
            'early_sharpe': early_sharpe,
            'late_sharpe': late_sharpe,
            'drop_percentage': drop_pct,
            'threshold': 30,
            'severity': 'HIGH' if drop_pct > 50 else 'MEDIUM' if is_overfitting else 'LOW'
        }

    def analyze_inconsistency(self, split_results: List[Dict]) -> Dict:
        """
        Detect inconsistent performance across splits

        Inconsistency symptom: High variance in Sharpe ratio
        """
        sharpe_values = [r['sharpe'] for r in split_results]
        mean_sharpe = np.mean(sharpe_values)
        std_sharpe = np.std(sharpe_values)

        # Calculate coefficient of variation
        if mean_sharpe != 0:
            cv = (std_sharpe / abs(mean_sharpe)) * 100
        else:
            cv = 0

        # Inconsistent if CV >50%
        is_inconsistent = cv > 50

        return {
            'detected': is_inconsistent,
            'mean_sharpe': mean_sharpe,
            'std_sharpe': std_sharpe,
            'coefficient_variation': cv,
            'threshold': 50,
            'severity': 'HIGH' if cv > 100 else 'MEDIUM' if is_inconsistent else 'LOW'
        }

    def analyze_catastrophic_failures(self, split_results: List[Dict]) -> Dict:
        """
        Detect catastrophic failure periods (negative Sharpe)

        Catastrophic failure: Any test period with negative Sharpe
        """
        negative_splits = [r for r in split_results if r['sharpe'] < 0]
        has_failures = len(negative_splits) > 0

        return {
            'detected': has_failures,
            'failure_count': len(negative_splits),
            'total_splits': len(split_results),
            'failure_rate': (len(negative_splits) / len(split_results)) * 100,
            'worst_sharpe': min([r['sharpe'] for r in split_results]),
            'severity': 'EXTREME' if len(negative_splits) > 2 else 'HIGH' if has_failures else 'NONE'
        }

    def analyze_signal_drought(self, split_results: List[Dict]) -> Dict:
        """
        Detect signal drought (too few signals generated)

        Signal drought symptom: <10 signals per hour
        """
        total_signals = sum([r['signals'] for r in split_results])
        total_trades = sum([r['trades'] for r in split_results])

        # Estimate hours (assuming M1 data, 60 candles = 1 hour)
        total_candles = sum([len(r.get('returns', [])) for r in split_results])
        estimated_hours = total_candles / 60 if total_candles > 0 else 1

        signals_per_hour = total_signals / estimated_hours if estimated_hours > 0 else 0

        # Drought if <10 signals/hour
        has_drought = signals_per_hour < 10

        return {
            'detected': has_drought,
            'signals_per_hour': signals_per_hour,
            'total_signals': total_signals,
            'total_trades': total_trades,
            'threshold': 10,
            'severity': 'HIGH' if signals_per_hour < 5 else 'MEDIUM' if has_drought else 'LOW'
        }

    def analyze_confidence_calibration(self, split_results: List[Dict]) -> Dict:
        """
        Detect confidence theater (scores don't match reality)

        Confidence theater: Win rate significantly below expected
        """
        all_returns = []
        for r in split_results:
            all_returns.extend(r.get('returns', []))

        if not all_returns:
            return {'detected': False, 'reason': 'No returns data'}

        # Calculate actual win rate
        wins = len([r for r in all_returns if r > 1.0])
        total = len(all_returns)
        actual_win_rate = (wins / total) * 100 if total > 0 else 0

        # Expected win rate (assume module claimed 70%)
        expected_win_rate = 70

        # Gap between expected and actual
        gap = expected_win_rate - actual_win_rate

        # Confidence theater if gap >15%
        is_theater = gap > 15

        return {
            'detected': is_theater,
            'expected_win_rate': expected_win_rate,
            'actual_win_rate': actual_win_rate,
            'gap_percentage': gap,
            'threshold': 15,
            'severity': 'HIGH' if gap > 25 else 'MEDIUM' if is_theater else 'LOW'
        }

    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate specific recommendations based on weak spots found"""
        recommendations = []

        # Overfitting recommendations
        if analysis['overfitting']['detected']:
            recommendations.append({
                'issue': 'OVERFITTING',
                'severity': analysis['overfitting']['severity'],
                'description': f"Performance drops {analysis['overfitting']['drop_percentage']:.1f}% in later test periods",
                'fixes': [
                    "Add more regularization (increase confidence thresholds)",
                    "Reduce lookback periods (less historical dependence)",
                    "Add safety margins to thresholds (e.g., ATR × 1.2 instead of × 1.0)",
                    "Test on different market regimes (trending vs ranging)"
                ]
            })

        # Inconsistency recommendations
        if analysis['inconsistency']['detected']:
            recommendations.append({
                'issue': 'INCONSISTENCY',
                'severity': analysis['inconsistency']['severity'],
                'description': f"Sharpe ratio varies wildly (CV: {analysis['inconsistency']['coefficient_variation']:.1f}%)",
                'fixes': [
                    "Add market regime filters (only trade trending markets)",
                    "Implement session awareness (avoid Asian session)",
                    "Add volume filters (require minimum liquidity)",
                    "Use adaptive thresholds based on recent volatility"
                ]
            })

        # Catastrophic failure recommendations
        if analysis['catastrophic_failures']['detected']:
            recommendations.append({
                'issue': 'CATASTROPHIC_FAILURES',
                'severity': analysis['catastrophic_failures']['severity'],
                'description': f"{analysis['catastrophic_failures']['failure_count']} splits with negative Sharpe (worst: {analysis['catastrophic_failures']['worst_sharpe']:.2f})",
                'fixes': [
                    "Add anomaly detection to avoid extreme volatility",
                    "Implement circuit breakers (stop trading after 2 consecutive losses)",
                    "Tighten stop loss distances during high volatility",
                    "Skip trading during major news events"
                ]
            })

        # Signal drought recommendations
        if analysis['signal_drought']['detected']:
            recommendations.append({
                'issue': 'SIGNAL_DROUGHT',
                'severity': analysis['signal_drought']['severity'],
                'description': f"Only {analysis['signal_drought']['signals_per_hour']:.1f} signals/hour (target: 10+)",
                'fixes': [
                    "Lower confidence thresholds (e.g., 70% instead of 80%)",
                    "Reduce minimum confluence requirements (3 instead of 4 factors)",
                    "Expand symbol coverage (test on more pairs)",
                    "Implement tiered system (Light mode with lower filters)"
                ]
            })

        # Confidence calibration recommendations
        if analysis['confidence_calibration']['detected']:
            recommendations.append({
                'issue': 'CONFIDENCE_THEATER',
                'severity': analysis['confidence_calibration']['severity'],
                'description': f"Actual win rate {analysis['confidence_calibration']['actual_win_rate']:.1f}% vs expected {analysis['confidence_calibration']['expected_win_rate']:.1f}%",
                'fixes': [
                    "Implement Bayesian calibration (tie scores to real wins)",
                    "Lower base confidence scores (start at 60% instead of 70%)",
                    "Add penalty for failed signals (reduce future confidence)",
                    "Track actual performance and auto-adjust thresholds"
                ]
            })

        return recommendations

    def analyze(self, validation_results: Dict) -> Dict:
        """Run all weak spot analyses"""
        module_analyses = []

        for module_result in validation_results['modules']:
            analysis = {
                'module': module_result['module'],
                'symbol': module_result['symbol'],
                'overfitting': self.analyze_overfitting(module_result['split_results']),
                'inconsistency': self.analyze_inconsistency(module_result['split_results']),
                'catastrophic_failures': self.analyze_catastrophic_failures(module_result['split_results']),
                'signal_drought': self.analyze_signal_drought(module_result['split_results']),
                'confidence_calibration': self.analyze_confidence_calibration(module_result['split_results'])
            }

            # Generate recommendations
            analysis['recommendations'] = self.generate_recommendations(analysis)

            # Overall health score (0-100)
            severity_scores = {
                'NONE': 0, 'LOW': 10, 'MEDIUM': 25, 'HIGH': 50, 'EXTREME': 100
            }

            total_severity = sum([
                severity_scores.get(analysis['overfitting'].get('severity', 'NONE'), 0),
                severity_scores.get(analysis['inconsistency'].get('severity', 'NONE'), 0),
                severity_scores.get(analysis['catastrophic_failures'].get('severity', 'NONE'), 0),
                severity_scores.get(analysis['signal_drought'].get('severity', 'NONE'), 0),
                severity_scores.get(analysis['confidence_calibration'].get('severity', 'NONE'), 0)
            ])

            health_score = max(0, 100 - total_severity)

            analysis['health_score'] = health_score
            analysis['status'] = (
                'EXCELLENT' if health_score >= 80 else
                'GOOD' if health_score >= 60 else
                'FAIR' if health_score >= 40 else
                'POOR'
            )

            module_analyses.append(analysis)

        return module_analyses


def main():
    """Analyze weak spots in validation results"""

    parser = argparse.ArgumentParser(description='Analyze weak spots in module validation')
    parser.add_argument('--symbol', default='EURUSD', help='Symbol to analyze')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("🔍 WEAK SPOT ANALYSIS - PHASE 1 MODULES")
    print("="*80 + "\n")

    # Load validation results
    results_file = f"{DATA_DIR}/validation_results_{args.symbol}.json"

    if not os.path.exists(results_file):
        print(f"❌ Validation results not found: {results_file}")
        print(f"   Run validate_modules.py first!")
        return

    with open(results_file, 'r') as f:
        validation_results = json.load(f)

    print(f"📊 Loaded validation results for {args.symbol}")
    print(f"   Modules tested: {len(validation_results['modules'])}")
    print(f"   Candles: {validation_results['candles_tested']:,}\n")

    # Run analysis
    analyzer = WeakSpotAnalyzer()
    analyses = analyzer.analyze(validation_results)

    # Print detailed analysis for each module
    for analysis in analyses:
        print(f"\n{'='*80}")
        print(f"📋 MODULE: {analysis['module']}")
        print(f"{'='*80}")
        print(f"   Health Score: {analysis['health_score']}/100 ({analysis['status']})")
        print()

        # Overfitting
        if analysis['overfitting']['detected']:
            print(f"   ⚠️  OVERFITTING DETECTED ({analysis['overfitting']['severity']})")
            print(f"      Early Sharpe: {analysis['overfitting']['early_sharpe']:.2f}")
            print(f"      Late Sharpe:  {analysis['overfitting']['late_sharpe']:.2f}")
            print(f"      Drop:         {analysis['overfitting']['drop_percentage']:.1f}%")
        else:
            print(f"   ✅ No overfitting detected")

        # Inconsistency
        if analysis['inconsistency']['detected']:
            print(f"   ⚠️  INCONSISTENCY DETECTED ({analysis['inconsistency']['severity']})")
            print(f"      Mean Sharpe:  {analysis['inconsistency']['mean_sharpe']:.2f}")
            print(f"      Std Dev:      {analysis['inconsistency']['std_sharpe']:.2f}")
            print(f"      CV:           {analysis['inconsistency']['coefficient_variation']:.1f}%")
        else:
            print(f"   ✅ Consistent performance")

        # Catastrophic failures
        if analysis['catastrophic_failures']['detected']:
            print(f"   ❌ CATASTROPHIC FAILURES ({analysis['catastrophic_failures']['severity']})")
            print(f"      Failures:     {analysis['catastrophic_failures']['failure_count']}/{analysis['catastrophic_failures']['total_splits']}")
            print(f"      Worst Sharpe: {analysis['catastrophic_failures']['worst_sharpe']:.2f}")
        else:
            print(f"   ✅ No catastrophic failures")

        # Signal drought
        if analysis['signal_drought']['detected']:
            print(f"   ⚠️  SIGNAL DROUGHT ({analysis['signal_drought']['severity']})")
            print(f"      Signals/hour: {analysis['signal_drought']['signals_per_hour']:.1f}")
            print(f"      Total signals: {analysis['signal_drought']['total_signals']}")
        else:
            print(f"   ✅ Adequate signal volume")

        # Confidence calibration
        if analysis['confidence_calibration']['detected']:
            print(f"   ⚠️  CONFIDENCE THEATER ({analysis['confidence_calibration']['severity']})")
            print(f"      Expected: {analysis['confidence_calibration']['expected_win_rate']:.1f}%")
            print(f"      Actual:   {analysis['confidence_calibration']['actual_win_rate']:.1f}%")
            print(f"      Gap:      {analysis['confidence_calibration']['gap_percentage']:.1f}%")
        else:
            print(f"   ✅ Well-calibrated confidence")

        # Recommendations
        if analysis['recommendations']:
            print(f"\n   📋 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                print(f"\n      Issue: {rec['issue']} ({rec['severity']})")
                print(f"      {rec['description']}")
                print(f"      Fixes:")
                for fix in rec['fixes']:
                    print(f"        • {fix}")

    # Save analysis
    output_file = f"{DATA_DIR}/weak_spot_analysis_{args.symbol}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'symbol': args.symbol,
            'analyses': analyses
        }, f, indent=2)

    print(f"\n💾 Analysis saved to: {output_file}")

    # Overall summary
    print(f"\n{'='*80}")
    print(f"🎯 OVERALL WEAK SPOT SUMMARY")
    print(f"{'='*80}")

    avg_health = np.mean([a['health_score'] for a in analyses])

    print(f"   Average Health Score: {avg_health:.1f}/100")
    print(f"   Modules Analyzed: {len(analyses)}")
    print()

    for status in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']:
        count = len([a for a in analyses if a['status'] == status])
        if count > 0:
            print(f"   {status}: {count} module(s)")

    print(f"\n   Next steps:")
    if avg_health >= 80:
        print(f"   ✅ Modules ready for integration - proceed to production!")
    elif avg_health >= 60:
        print(f"   ⚠️  Minor refinements recommended before integration")
    else:
        print(f"   ❌ Major refinements required - address weak spots first")

    print()


if __name__ == '__main__':
    main()
