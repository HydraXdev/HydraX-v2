#!/usr/bin/env python3
"""
Quick live performance display from comprehensive_tracking.jsonl
Shows REAL win/loss data - no fake data
"""

import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def main():
    tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
    
    # Parse hours argument
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            pass
    
    cutoff = datetime.now().timestamp() - (hours * 3600)
    
    # Load signals
    signals = []
    with open(tracking_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    sig = json.loads(line)
                    # Skip old format with string timestamps
                    if isinstance(sig.get('timestamp'), (int, float)):
                        if sig['timestamp'] > cutoff:
                            signals.append(sig)
                except:
                    continue
    
    # Calculate stats
    wins = [s for s in signals if s.get('outcome') == 'WIN']
    losses = [s for s in signals if s.get('outcome') == 'LOSS']
    pending = [s for s in signals if s.get('outcome') is None]
    
    total_completed = len(wins) + len(losses)
    win_rate = (len(wins) / total_completed * 100) if total_completed > 0 else 0
    
    # Pattern stats
    pattern_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})
    for s in signals:
        pattern = s.get('pattern_type', 'UNKNOWN')
        if s.get('outcome') == 'WIN':
            pattern_stats[pattern]['wins'] += 1
        elif s.get('outcome') == 'LOSS':
            pattern_stats[pattern]['losses'] += 1
    
    # Display
    print(f"\n📊 LIVE PERFORMANCE - LAST {hours} HOURS")
    print("=" * 50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Data: comprehensive_tracking.jsonl (REAL OUTCOMES)")
    print("=" * 50)
    
    print(f"\n📈 SUMMARY")
    print(f"Total Signals: {len(signals)}")
    print(f"Completed: {total_completed}")
    print(f"Active: {len(pending)}")
    print(f"✅ Wins: {len(wins)}")
    print(f"❌ Losses: {len(losses)}")
    print(f"🎯 Win Rate: {win_rate:.1f}%")
    
    if pattern_stats:
        print(f"\n🔍 PATTERN PERFORMANCE")
        print("-" * 50)
        for pattern, stats in sorted(pattern_stats.items()):
            total = stats['wins'] + stats['losses']
            if total > 0:
                wr = stats['wins'] / total * 100
                print(f"{pattern:30} {stats['wins']:3}W {stats['losses']:3}L = {wr:5.1f}%")
    
    print("\n" + "=" * 50)
    print("💡 Signals track to actual TP/SL - NO TIMEOUTS")
    print("=" * 50)

if __name__ == "__main__":
    main()