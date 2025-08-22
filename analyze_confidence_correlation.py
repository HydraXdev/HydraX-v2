#!/usr/bin/env python3
"""Detailed confidence correlation analysis"""

import json
from datetime import datetime, timedelta
import os
from collections import defaultdict

def analyze_confidence_correlation():
    """Analyze win rate by detailed confidence levels"""
    try:
        tracking_file = '/root/HydraX-v2/optimized_tracking.jsonl'
        
        if not os.path.exists(tracking_file):
            print("📊 No optimized_tracking.jsonl yet")
            return
            
        # Read and filter for last 6 hours
        now = datetime.now()
        six_hours_ago = now - timedelta(hours=6)
        
        recent = []
        with open(tracking_file, 'r') as f:
            for line in f:
                if line.strip():
                    signal = json.loads(line)
                    if 'timestamp' in signal:
                        ts_str = signal['timestamp']
                        if 'T' in ts_str:
                            ts_str = ts_str.split('.')[0] if '.' in ts_str else ts_str.replace('Z', '')
                            signal_time = datetime.fromisoformat(ts_str)
                        else:
                            signal_time = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        
                        if signal_time >= six_hours_ago:
                            recent.append(signal)
        
        if not recent:
            print("📊 No data in last 6 hours")
            return
        
        # Group by exact confidence score
        confidence_groups = defaultdict(lambda: {'wins': 0, 'total': 0})
        
        for signal in recent:
            conf = signal.get('confidence', 0)
            confidence_groups[conf]['total'] += 1
            if signal.get('win', False):
                confidence_groups[conf]['wins'] += 1
        
        print("="*70)
        print("📊 WIN RATE BY EXACT CONFIDENCE SCORE (Last 6 Hours)")
        print("="*70)
        print(f"{'Confidence':<12} {'Signals':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12} {'Graph'}")
        print("-"*70)
        
        # Sort by confidence score
        for conf in sorted(confidence_groups.keys()):
            data = confidence_groups[conf]
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            losses = data['total'] - data['wins']
            
            # Create visual bar
            bar_length = int(win_rate / 2)  # Scale to 50 chars max
            bar = '█' * bar_length + '░' * (50 - bar_length)
            
            print(f"{conf:<12.1f} {data['total']:<10} {data['wins']:<10} {losses:<10} {win_rate:<12.1f}% {bar}")
        
        # Detailed confidence bins
        print("\n" + "="*70)
        print("📊 WIN RATE BY CONFIDENCE BINS")
        print("="*70)
        
        bins = [
            ("70-75%", 70, 75),
            ("75-80%", 75, 80),
            ("80-82%", 80, 82),
            ("82-84%", 82, 84),
            ("84-85%", 84, 85),
            ("85-86%", 85, 86),
            ("86-88%", 86, 88),
            ("88-90%", 88, 90),
            ("90-95%", 90, 95),
            ("95-100%", 95, 100)
        ]
        
        print(f"{'Bin':<12} {'Signals':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12} {'Expected':<12} {'Delta'}")
        print("-"*70)
        
        for bin_name, low, high in bins:
            bin_signals = [s for s in recent if low <= s.get('confidence', 0) < high]
            if bin_signals:
                wins = sum(1 for s in bin_signals if s.get('win', False))
                total = len(bin_signals)
                losses = total - wins
                win_rate = (wins / total * 100) if total > 0 else 0
                expected = (low + high) / 2  # Expected win rate is middle of bin
                delta = win_rate - expected
                
                delta_str = f"{delta:+.1f}%" if delta >= 0 else f"{delta:.1f}%"
                color = "🟢" if delta > 0 else "🔴" if delta < 0 else "⚪"
                
                print(f"{bin_name:<12} {total:<10} {wins:<10} {losses:<10} {win_rate:<12.1f}% {expected:<12.1f}% {color} {delta_str}")
        
        # Statistical summary
        print("\n" + "="*70)
        print("📊 STATISTICAL ANALYSIS")
        print("="*70)
        
        # Calculate correlation
        conf_values = []
        win_values = []
        
        for signal in recent:
            conf = signal.get('confidence', 0)
            win = 1 if signal.get('win', False) else 0
            conf_values.append(conf)
            win_values.append(win)
        
        if conf_values and win_values:
            # Simple correlation calculation
            avg_conf = sum(conf_values) / len(conf_values)
            avg_win = sum(win_values) / len(win_values)
            
            # Calculate if higher confidence = higher win rate
            high_conf_signals = [s for s in recent if s.get('confidence', 0) >= 85]
            low_conf_signals = [s for s in recent if s.get('confidence', 0) < 85]
            
            high_conf_wr = 0
            low_conf_wr = 0
            
            if high_conf_signals:
                high_wins = sum(1 for s in high_conf_signals if s.get('win', False))
                high_conf_wr = (high_wins / len(high_conf_signals) * 100)
            
            if low_conf_signals:
                low_wins = sum(1 for s in low_conf_signals if s.get('win', False))
                low_conf_wr = (low_wins / len(low_conf_signals) * 100)
            
            print(f"Average Confidence: {avg_conf:.1f}%")
            print(f"Overall Win Rate: {avg_win * 100:.1f}%")
            print(f"\nHigh Confidence (≥85%):")
            print(f"  Signals: {len(high_conf_signals)}")
            print(f"  Win Rate: {high_conf_wr:.1f}%")
            print(f"\nLow Confidence (<85%):")
            print(f"  Signals: {len(low_conf_signals)}")
            print(f"  Win Rate: {low_conf_wr:.1f}%")
            
            # Check if confidence is predictive
            if high_conf_wr > low_conf_wr:
                print(f"\n✅ Confidence IS predictive: High conf wins {high_conf_wr - low_conf_wr:.1f}% more")
            elif high_conf_wr < low_conf_wr:
                print(f"\n⚠️ Confidence NOT predictive: Low conf wins {low_conf_wr - high_conf_wr:.1f}% more")
            else:
                print(f"\n⚪ Confidence NEUTRAL: Same win rate for high and low")
        
        # Pattern breakdown by confidence
        print("\n" + "="*70)
        print("📊 PATTERN PERFORMANCE BY CONFIDENCE")
        print("="*70)
        
        patterns = set(s.get('pattern', 'UNKNOWN') for s in recent)
        
        for pattern in sorted(patterns):
            if pattern == 'UNKNOWN':
                continue
                
            print(f"\n🎯 {pattern}:")
            
            pattern_signals = [s for s in recent if s.get('pattern') == pattern]
            
            # Group by confidence ranges for this pattern
            ranges = [(80, 85), (85, 90), (90, 95)]
            
            for low, high in ranges:
                range_signals = [s for s in pattern_signals if low <= s.get('confidence', 0) < high]
                if range_signals:
                    wins = sum(1 for s in range_signals if s.get('win', False))
                    total = len(range_signals)
                    win_rate = (wins / total * 100) if total > 0 else 0
                    print(f"  {low}-{high}%: {wins}/{total} signals ({win_rate:.1f}% win rate)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_confidence_correlation()