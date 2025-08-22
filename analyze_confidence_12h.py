#!/usr/bin/env python3
"""12-hour confidence correlation analysis for comparison"""

import json
from datetime import datetime, timedelta
import os
from collections import defaultdict

def analyze_confidence_correlation(hours=12):
    """Analyze win rate by detailed confidence levels"""
    try:
        tracking_file = '/root/HydraX-v2/optimized_tracking.jsonl'
        
        if not os.path.exists(tracking_file):
            print("📊 No optimized_tracking.jsonl yet")
            return
            
        # Read and filter for last N hours
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)
        
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
                        
                        if signal_time >= cutoff_time:
                            recent.append(signal)
        
        if not recent:
            print(f"📊 No data in last {hours} hours")
            return
        
        # Group by exact confidence score
        confidence_groups = defaultdict(lambda: {'wins': 0, 'total': 0})
        
        for signal in recent:
            conf = signal.get('confidence', 0)
            confidence_groups[conf]['total'] += 1
            if signal.get('win', False):
                confidence_groups[conf]['wins'] += 1
        
        print("="*70)
        print(f"📊 WIN RATE BY EXACT CONFIDENCE SCORE (Last {hours} Hours)")
        print("="*70)
        print(f"{'Confidence':<12} {'Signals':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12}")
        print("-"*70)
        
        # Sort by confidence score - show only summary
        total_signals = 0
        total_wins = 0
        
        for conf in sorted(confidence_groups.keys()):
            data = confidence_groups[conf]
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            losses = data['total'] - data['wins']
            total_signals += data['total']
            total_wins += data['wins']
            
            # Only show confidence levels with 5+ signals
            if data['total'] >= 5:
                print(f"{conf:<12.1f} {data['total']:<10} {data['wins']:<10} {losses:<10} {win_rate:<12.1f}%")
        
        overall_wr = (total_wins / total_signals * 100) if total_signals > 0 else 0
        print("-"*70)
        print(f"{'TOTAL':<12} {total_signals:<10} {total_wins:<10} {total_signals-total_wins:<10} {overall_wr:<12.1f}%")
        
        # Detailed confidence bins
        print("\n" + "="*70)
        print(f"📊 WIN RATE BY CONFIDENCE BINS (Last {hours} Hours)")
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
        
        print(f"{'Bin':<12} {'Signals':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12} {'Expected':<12} {'Delta':<12} {'Status'}")
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
                
                delta_str = f"{delta:+.1f}%"
                if abs(delta) < 5:
                    status = "✅ OK"
                elif abs(delta) < 15:
                    status = "⚠️ WARN"
                else:
                    status = "🔴 CRITICAL"
                
                print(f"{bin_name:<12} {total:<10} {wins:<10} {losses:<10} {win_rate:<12.1f}% {expected:<12.1f}% {delta_str:<12} {status}")
        
        # Statistical summary
        print("\n" + "="*70)
        print(f"📊 COMPARATIVE ANALYSIS: 6H vs 12H")
        print("="*70)
        
        # Calculate for both time periods
        six_hours_ago = now - timedelta(hours=6)
        
        recent_6h = [s for s in recent if datetime.fromisoformat(s['timestamp'].split('.')[0] if '.' in s['timestamp'] else s['timestamp'].replace('Z', '')) >= six_hours_ago]
        recent_12h = recent
        
        # High/Low confidence comparison
        high_6h = [s for s in recent_6h if s.get('confidence', 0) >= 85]
        low_6h = [s for s in recent_6h if s.get('confidence', 0) < 85]
        high_12h = [s for s in recent_12h if s.get('confidence', 0) >= 85]
        low_12h = [s for s in recent_12h if s.get('confidence', 0) < 85]
        
        # Calculate win rates
        high_wr_6h = (sum(1 for s in high_6h if s.get('win', False)) / len(high_6h) * 100) if high_6h else 0
        low_wr_6h = (sum(1 for s in low_6h if s.get('win', False)) / len(low_6h) * 100) if low_6h else 0
        high_wr_12h = (sum(1 for s in high_12h if s.get('win', False)) / len(high_12h) * 100) if high_12h else 0
        low_wr_12h = (sum(1 for s in low_12h if s.get('win', False)) / len(low_12h) * 100) if low_12h else 0
        
        overall_6h = (sum(1 for s in recent_6h if s.get('win', False)) / len(recent_6h) * 100) if recent_6h else 0
        overall_12h = (sum(1 for s in recent_12h if s.get('win', False)) / len(recent_12h) * 100) if recent_12h else 0
        
        print(f"{'Metric':<25} {'6 Hours':<20} {'12 Hours':<20} {'Change'}")
        print("-"*70)
        print(f"{'Total Signals':<25} {len(recent_6h):<20} {len(recent_12h):<20} {len(recent_12h)-len(recent_6h):+d}")
        print(f"{'Overall Win Rate':<25} {overall_6h:<20.1f}% {overall_12h:<20.1f}% {overall_12h-overall_6h:+.1f}%")
        print(f"{'High Conf (≥85%) Signals':<25} {len(high_6h):<20} {len(high_12h):<20} {len(high_12h)-len(high_6h):+d}")
        print(f"{'High Conf Win Rate':<25} {high_wr_6h:<20.1f}% {high_wr_12h:<20.1f}% {high_wr_12h-high_wr_6h:+.1f}%")
        print(f"{'Low Conf (<85%) Signals':<25} {len(low_6h):<20} {len(low_12h):<20} {len(low_12h)-len(low_6h):+d}")
        print(f"{'Low Conf Win Rate':<25} {low_wr_6h:<20.1f}% {low_wr_12h:<20.1f}% {low_wr_12h-low_wr_6h:+.1f}%")
        print(f"{'Conf Predictiveness':<25} {high_wr_6h-low_wr_6h:<20.1f}% {high_wr_12h-low_wr_12h:<20.1f}% {(high_wr_12h-low_wr_12h)-(high_wr_6h-low_wr_6h):+.1f}%")
        
        # Pattern breakdown by confidence for 12H
        print("\n" + "="*70)
        print(f"📊 PATTERN PERFORMANCE BY CONFIDENCE (12 Hours)")
        print("="*70)
        
        patterns = set(s.get('pattern', 'UNKNOWN') for s in recent)
        
        for pattern in sorted(patterns):
            if pattern == 'UNKNOWN':
                continue
                
            pattern_signals = [s for s in recent if s.get('pattern') == pattern]
            total_p = len(pattern_signals)
            wins_p = sum(1 for s in pattern_signals if s.get('win', False))
            wr_p = (wins_p / total_p * 100) if total_p > 0 else 0
            
            print(f"\n🎯 {pattern}: {wins_p}/{total_p} overall ({wr_p:.1f}% win rate)")
            
            # Group by confidence ranges for this pattern
            ranges = [(70, 80), (80, 83), (83, 85), (85, 87), (87, 90), (90, 100)]
            
            for low, high in ranges:
                range_signals = [s for s in pattern_signals if low <= s.get('confidence', 0) < high]
                if range_signals:
                    wins = sum(1 for s in range_signals if s.get('win', False))
                    total = len(range_signals)
                    win_rate = (wins / total * 100) if total > 0 else 0
                    expected = (low + high) / 2
                    delta = win_rate - expected
                    
                    status = "✅" if abs(delta) < 10 else "⚠️" if abs(delta) < 20 else "🔴"
                    print(f"  {low:>3}-{high:<3}%: {wins:>3}/{total:<3} ({win_rate:>5.1f}% vs {expected:>5.1f}% expected) {status} {delta:+.1f}%")
        
        # Confidence score distribution analysis
        print("\n" + "="*70)
        print("📊 CONFIDENCE SCORE DISTRIBUTION")
        print("="*70)
        
        # Count frequency of each confidence score
        conf_freq = defaultdict(int)
        for s in recent:
            conf = round(s.get('confidence', 0), 1)
            conf_freq[conf] += 1
        
        # Find top 10 most common confidence scores
        top_confs = sorted(conf_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print(f"{'Confidence':<15} {'Count':<10} {'Percentage':<15} {'Cumulative'}")
        print("-"*70)
        
        cumulative = 0
        for conf, count in top_confs:
            pct = (count / len(recent) * 100)
            cumulative += pct
            bar = '█' * int(pct / 2)  # Visual bar
            print(f"{conf:<15.1f} {count:<10} {pct:<15.1f}% {cumulative:<.1f}% {bar}")
        
        # Check if 85.0 is being overused
        if 85.0 in conf_freq and conf_freq[85.0] / len(recent) > 0.3:
            print(f"\n⚠️ WARNING: {conf_freq[85.0]} signals ({conf_freq[85.0]/len(recent)*100:.1f}%) have exactly 85.0% confidence")
            print("   This suggests a DEFAULT VALUE being overused!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 12-HOUR CONFIDENCE ANALYSIS")
    print("="*70)
    analyze_confidence_correlation(12)