#!/usr/bin/env python3
"""
SIMULATE MODULE ENHANCEMENT ON REAL SIGNALS

Takes the 26 real Elite Guard signals from last 30 days (15.4% WR)
Simulates what would happen if module enhancement was active
Shows: base confidence → calibrated confidence → would we have filtered it?

This proves the enhancement logic works before going live.
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, '/root/HydraX-v2')

from services.pattern_module_enhancer import PatternModuleEnhancer

def load_candles(symbol, timeframe):
    """Load historical candles from JSON"""
    json_file = f'/root/HydraX-v2/backtest_data/{symbol}_{timeframe}.json'
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            return data.get('candles', [])
    except FileNotFoundError:
        return []

def find_candles_at_time(candles, target_time, count=100, before=True):
    """Find candles before or after a timestamp"""
    # Sort by timestamp
    sorted_candles = sorted(candles, key=lambda x: x['timestamp'])

    # Find index closest to target_time
    idx = 0
    for i, candle in enumerate(sorted_candles):
        if candle['timestamp'] >= target_time:
            idx = i
            break

    if before:
        # Get candles BEFORE signal time
        start = max(0, idx - count)
        return sorted_candles[start:idx]
    else:
        # Get candles AFTER signal time
        return sorted_candles[idx:idx + count]

def main():
    print("\n" + "="*80)
    print("🔬 MODULE ENHANCEMENT SIMULATION - Backtest on Real Signals")
    print("="*80 + "\n")

    # Initialize module enhancer
    print("🔧 Initializing Pattern Module Enhancer...")
    enhancer = PatternModuleEnhancer(
        elite_guard_baseline_wr=0.68,
        finnhub_api_key='d3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
    )
    print("✅ Ready\n")

    # Load historical candles
    print("📊 Loading historical candle data...")
    eurusd_m1 = load_candles('EURUSD', 'M1')
    eurusd_h4 = load_candles('EURUSD', 'H4')
    gbpusd_m1 = load_candles('GBPUSD', 'M1')
    gbpusd_h4 = load_candles('GBPUSD', 'H4')

    candle_data = {
        'EURUSD': {'M1': eurusd_m1, 'H4': eurusd_h4},
        'GBPUSD': {'M1': gbpusd_m1, 'H4': gbpusd_h4}
    }

    print(f"✅ Loaded candles:")
    for symbol, data in candle_data.items():
        print(f"   {symbol}: {len(data['M1'])} M1, {len(data['H4'])} H4")
    print()

    # Connect to database
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch the same 26 signals
    thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())

    query = """
    SELECT
        signal_id, symbol, pattern_type, direction, confidence,
        entry, sl, tp, created_at, outcome
    FROM signals
    WHERE created_at >= ?
    AND signal_id LIKE 'ELITE%'
    ORDER BY created_at DESC
    LIMIT 100
    """

    cursor.execute(query, (thirty_days_ago,))
    signals = cursor.fetchall()

    print(f"✅ Found {len(signals)} Elite Guard signals\n")
    print("="*80)
    print("🔬 SIMULATING MODULE ENHANCEMENT")
    print("="*80 + "\n")

    # Track results
    results = {
        'total': 0,
        'enhanced_successfully': 0,
        'enhancement_failed': 0,
        'baseline_wins': 0,
        'baseline_losses': 0,
        'simulated': []
    }

    for signal in signals:
        symbol = signal['symbol']
        signal_time = signal['created_at']
        outcome = signal['outcome']

        # Skip if no candle data for this symbol
        if symbol not in candle_data:
            print(f"⚠️  Skipping {signal['signal_id'][:30]}... - No candle data for {symbol}")
            continue

        # Get M1 and H4 candles BEFORE signal time
        m1_candles = find_candles_at_time(candle_data[symbol]['M1'], signal_time, count=100, before=True)
        h4_candles = find_candles_at_time(candle_data[symbol]['H4'], signal_time, count=50, before=True)

        if len(m1_candles) < 50 or len(h4_candles) < 20:
            print(f"⚠️  Skipping {signal['signal_id'][:30]}... - Insufficient candles (M1: {len(m1_candles)}, H4: {len(h4_candles)})")
            continue

        results['total'] += 1

        # Track baseline outcome
        if outcome == 'WIN':
            results['baseline_wins'] += 1
        elif outcome == 'LOSS':
            results['baseline_losses'] += 1

        # Simulate module enhancement
        try:
            # Create pattern signal dict
            pattern_signal = {
                'pattern': signal['pattern_type'],
                'direction': signal['direction'],
                'confidence': signal['confidence'],
                'entry_price': signal['entry'],
                'sl': signal['sl'],
                'tp': signal['tp'],
                'symbol': symbol
            }

            # ENHANCE WITH MODULES
            enhanced = enhancer.enhance_pattern(
                pattern_signal=pattern_signal,
                symbol=symbol,
                m1_candles=m1_candles,
                h4_candles=h4_candles
            )

            results['enhanced_successfully'] += 1

            base_conf = enhanced['base_confidence']
            calib_conf = enhanced['calibrated_confidence']
            evidence = enhanced['evidence_score']

            # Determine if we would have filtered this signal
            # Using 75% threshold for auto-fire
            would_fire_baseline = base_conf >= 75
            would_fire_enhanced = calib_conf >= 75

            outcome_emoji = "✅" if outcome == "WIN" else "❌" if outcome == "LOSS" else "⏸️"

            print(f"{outcome_emoji} {signal['pattern_type'][:20]:20} {symbol:8} | "
                  f"Base: {base_conf:5.1f}% → Calib: {calib_conf:5.1f}% | "
                  f"Evidence: {evidence:+.2f} | "
                  f"Outcome: {outcome or 'PENDING':8}")

            # Store simulation result
            results['simulated'].append({
                'signal_id': signal['signal_id'],
                'pattern': signal['pattern_type'],
                'symbol': symbol,
                'outcome': outcome,
                'base_confidence': base_conf,
                'calibrated_confidence': calib_conf,
                'evidence_score': evidence,
                'would_fire_baseline': would_fire_baseline,
                'would_fire_enhanced': would_fire_enhanced
            })

        except Exception as e:
            results['enhancement_failed'] += 1
            print(f"❌ Enhancement failed: {signal['signal_id'][:30]}... - {str(e)[:50]}")

    # Analysis
    print(f"\n" + "="*80)
    print(f"📊 SIMULATION RESULTS")
    print(f"="*80 + "\n")

    print(f"Total Signals Processed: {results['total']}")
    print(f"  - Enhanced Successfully: {results['enhanced_successfully']}")
    print(f"  - Enhancement Failed: {results['enhancement_failed']}")

    # Filter completed signals only
    completed = [s for s in results['simulated'] if s['outcome'] in ['WIN', 'LOSS']]

    if completed:
        # Baseline performance
        baseline_wins = sum(1 for s in completed if s['outcome'] == 'WIN')
        baseline_total = len(completed)
        baseline_wr = (baseline_wins / baseline_total * 100) if baseline_total > 0 else 0

        # Simulated enhanced performance (if we only fired high calib_conf)
        enhanced_fired = [s for s in completed if s['would_fire_enhanced']]
        enhanced_wins = sum(1 for s in enhanced_fired if s['outcome'] == 'WIN')
        enhanced_total = len(enhanced_fired)
        enhanced_wr = (enhanced_wins / enhanced_total * 100) if enhanced_total > 0 else 0

        # Signals FILTERED by enhancement
        filtered = [s for s in completed if s['would_fire_baseline'] and not s['would_fire_enhanced']]
        filtered_wins = sum(1 for s in filtered if s['outcome'] == 'WIN')
        filtered_losses = sum(1 for s in filtered if s['outcome'] == 'LOSS')

        print(f"\n🎯 BASELINE (Without Modules):")
        print(f"   Signals: {baseline_total}")
        print(f"   Wins: {baseline_wins} | Losses: {baseline_total - baseline_wins}")
        print(f"   Win Rate: {baseline_wr:.1f}%")

        print(f"\n🔧 ENHANCED (With Module Filtering at 75% threshold):")
        print(f"   Signals: {enhanced_total}")
        print(f"   Wins: {enhanced_wins} | Losses: {enhanced_total - enhanced_wins}")
        print(f"   Win Rate: {enhanced_wr:.1f}%")

        if enhanced_wr > baseline_wr:
            improvement = enhanced_wr - baseline_wr
            print(f"   ✅ IMPROVEMENT: +{improvement:.1f}%")
        elif enhanced_wr < baseline_wr:
            print(f"   ⚠️  DECLINE: {enhanced_wr - baseline_wr:.1f}%")
        else:
            print(f"   ➖ NO CHANGE")

        print(f"\n🚫 SIGNALS FILTERED OUT:")
        print(f"   Total Filtered: {len(filtered)}")
        print(f"   Would Have Won: {filtered_wins}")
        print(f"   Would Have Lost: {filtered_losses}")
        if filtered:
            filtered_wr = (filtered_wins / len(filtered) * 100)
            print(f"   Filtered Win Rate: {filtered_wr:.1f}%")
            if filtered_losses > filtered_wins:
                print(f"   ✅ GOOD FILTERING - Removed more losers than winners")
            else:
                print(f"   ⚠️  AGGRESSIVE FILTERING - Removed more winners than losers")

        # Confidence calibration analysis
        avg_base_conf = sum(s['base_confidence'] for s in completed) / len(completed)
        avg_calib_conf = sum(s['calibrated_confidence'] for s in completed) / len(completed)

        print(f"\n📊 CONFIDENCE CALIBRATION:")
        print(f"   Avg Base Confidence: {avg_base_conf:.1f}%")
        print(f"   Avg Calibrated Confidence: {avg_calib_conf:.1f}%")
        print(f"   Actual Win Rate: {baseline_wr:.1f}%")
        print(f"   Calibration Gap (Base): {abs(avg_base_conf - baseline_wr):.1f}%")
        print(f"   Calibration Gap (Enhanced): {abs(avg_calib_conf - baseline_wr):.1f}%")

        if abs(avg_calib_conf - baseline_wr) < abs(avg_base_conf - baseline_wr):
            print(f"   ✅ BETTER CALIBRATION with modules")
        else:
            print(f"   ⚠️  Calibration needs tuning")

    print(f"\n" + "="*80)
    print(f"✅ SIMULATION COMPLETE")
    print(f"="*80)

    if enhanced_wr > baseline_wr:
        print(f"\n🎯 CONCLUSION: Module enhancement IMPROVES performance")
        print(f"   Baseline: {baseline_wr:.1f}% → Enhanced: {enhanced_wr:.1f}%")
        print(f"   Safe to restart Elite Guard with enhancements ✅")
    elif enhanced_total < baseline_total / 2:
        print(f"\n⚠️  CONCLUSION: Enhancement filters too aggressively")
        print(f"   Consider lowering threshold from 75% to 70%")
    else:
        print(f"\n📊 CONCLUSION: Enhancement ready for testing")
        print(f"   Monitor live performance to validate")

    conn.close()

if __name__ == '__main__':
    main()
