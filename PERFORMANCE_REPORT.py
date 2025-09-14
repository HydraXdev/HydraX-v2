#!/usr/bin/env python3
"""
BITTEN PERFORMANCE REPORT - EASY WIN/LOSS TRACKING
Run this to get instant performance metrics!
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict

def generate_report(hours_back=6):
    """
    Generate comprehensive performance report
    """
    print("\n" + "="*70)
    print(f"🎯 BITTEN TRADING PERFORMANCE REPORT")
    print(f"📅 Last {hours_back} Hours | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("="*70)
    
    # Primary data source - REAL tracking only
    tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
    
    # Get cutoff time
    cutoff = datetime.now() - timedelta(hours=hours_back)
    
    # Initialize counters
    total_signals = 0
    wins = 0
    losses = 0
    pending = 0
    
    pattern_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    pair_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    confidence_buckets = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    
    # Read tracking data
    try:
        with open(tracking_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    
                    # Parse timestamp
                    timestamp = data.get('timestamp', 0)
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('T', ' ').split('.')[0])
                    else:
                        dt = datetime.fromtimestamp(float(timestamp))
                    
                    # Skip old data
                    if dt < cutoff:
                        continue
                    
                    total_signals += 1
                    
                    # Get data
                    pattern = data.get('pattern', data.get('pattern_type', 'UNKNOWN'))
                    pair = data.get('pair', data.get('symbol', 'UNKNOWN'))
                    confidence = data.get('confidence', data.get('confidence_score', 0))
                    outcome = data.get('outcome')
                    win = data.get('win')
                    
                    # Determine outcome
                    if win == True or outcome == 'WIN':
                        wins += 1
                        result = 'WIN'
                    elif win == False or outcome == 'LOSS':
                        losses += 1
                        result = 'LOSS'
                    else:
                        pending += 1
                        result = 'PENDING'
                    
                    # Track by pattern
                    pattern_stats[pattern]['total'] += 1
                    if result == 'WIN':
                        pattern_stats[pattern]['wins'] += 1
                    elif result == 'LOSS':
                        pattern_stats[pattern]['losses'] += 1
                    
                    # Track by pair
                    pair_stats[pair]['total'] += 1
                    if result == 'WIN':
                        pair_stats[pair]['wins'] += 1
                    elif result == 'LOSS':
                        pair_stats[pair]['losses'] += 1
                    
                    # Track by confidence
                    conf_bucket = f"{int(confidence//5)*5}-{int(confidence//5)*5+5}"
                    confidence_buckets[conf_bucket]['total'] += 1
                    if result == 'WIN':
                        confidence_buckets[conf_bucket]['wins'] += 1
                    elif result == 'LOSS':
                        confidence_buckets[conf_bucket]['losses'] += 1
                        
                except Exception as e:
                    continue
                    
    except FileNotFoundError:
        print("❌ Tracking file not found!")
        return
    
    # Print overall stats
    print("\n📊 OVERALL PERFORMANCE:")
    print("-"*40)
    print(f"Total Signals: {total_signals}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Pending: {pending}")
    
    if wins + losses > 0:
        win_rate = (wins / (wins + losses)) * 100
        print(f"Win Rate: {win_rate:.1f}%")
    else:
        print("Win Rate: No completed trades")
    
    # Print pattern performance
    if pattern_stats:
        print("\n📈 PERFORMANCE BY PATTERN:")
        print("-"*40)
        for pattern, stats in sorted(pattern_stats.items(), 
                                    key=lambda x: x[1]['total'], 
                                    reverse=True):
            if stats['wins'] + stats['losses'] > 0:
                wr = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100
                print(f"{pattern:30} W:{stats['wins']:3} L:{stats['losses']:3} (WR: {wr:.0f}%)")
    
    # Print pair performance
    if pair_stats:
        print("\n💱 PERFORMANCE BY PAIR:")
        print("-"*40)
        for pair, stats in sorted(pair_stats.items(), 
                                 key=lambda x: x[1]['total'], 
                                 reverse=True)[:10]:
            if stats['wins'] + stats['losses'] > 0:
                wr = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100
                print(f"{pair:10} W:{stats['wins']:3} L:{stats['losses']:3} (WR: {wr:.0f}%)")
    
    # Print confidence analysis
    if confidence_buckets:
        print("\n🎯 PERFORMANCE BY CONFIDENCE:")
        print("-"*40)
        for conf_range, stats in sorted(confidence_buckets.items()):
            if stats['wins'] + stats['losses'] > 0:
                wr = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100
                print(f"{conf_range:>8}% W:{stats['wins']:3} L:{stats['losses']:3} (WR: {wr:.0f}%)")
    
    # Key insights
    print("\n💡 KEY INSIGHTS:")
    print("-"*40)
    
    # Best performing pattern
    if pattern_stats:
        best_pattern = max([(p, s['wins']/(s['wins']+s['losses'])*100) 
                           for p, s in pattern_stats.items() 
                           if s['wins']+s['losses'] > 0], 
                          key=lambda x: x[1])
        print(f"Best Pattern: {best_pattern[0]} ({best_pattern[1]:.0f}% WR)")
    
    # Best performing pair
    if pair_stats:
        best_pair = max([(p, s['wins']/(s['wins']+s['losses'])*100) 
                        for p, s in pair_stats.items() 
                        if s['wins']+s['losses'] > 0], 
                       key=lambda x: x[1])
        print(f"Best Pair: {best_pair[0]} ({best_pair[1]:.0f}% WR)")
    
    # Best confidence range
    if confidence_buckets:
        best_conf = max([(c, s['wins']/(s['wins']+s['losses'])*100) 
                        for c, s in confidence_buckets.items() 
                        if s['wins']+s['losses'] > 0], 
                       key=lambda x: x[1])
        print(f"Best Confidence Range: {best_conf[0]}% ({best_conf[1]:.0f}% WR)")
    
    print("\n" + "="*70)
    print("📝 Data Source: /root/HydraX-v2/comprehensive_tracking.jsonl")
    print("🔄 Run Again: python3 /root/HydraX-v2/PERFORMANCE_REPORT.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    # Generate reports for different time periods
    import sys
    
    if len(sys.argv) > 1:
        hours = int(sys.argv[1])
        generate_report(hours)
    else:
        # Default to 6 hours
        generate_report(6)
        
        # Also show 24 hour summary
        print("\n" + "="*70)
        print("📊 24 HOUR SUMMARY")
        generate_report(24)