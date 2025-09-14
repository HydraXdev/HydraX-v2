#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Simple timezone-naive analysis for last 12 hours
now = datetime.now()
twelve_hours_ago = now - timedelta(hours=12)

# Data structures for analysis
pattern_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0, 'win_rate': 0.0, 'avg_confidence': 0.0, 'confidences': []})
recent_signals = []

print('=== COMPREHENSIVE SIGNAL ANALYSIS: Last 12 Hours ===')
print(f'Analysis Period: {twelve_hours_ago.strftime("%Y-%m-%d %H:%M")} to {now.strftime("%Y-%m-%d %H:%M")}')
print()

# Parse comprehensive tracking data
try:
    signal_count = 0
    with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    signal = json.loads(line.strip())
                    signal_count += 1
                    
                    # Parse timestamp - handle different formats
                    timestamp = None
                    timestamp_str = signal.get('timestamp', '')
                    
                    if 'timestamp' in signal:
                        # New format with timestamp field
                        timestamp_val = signal['timestamp']
                        if isinstance(timestamp_val, str):
                            try:
                                timestamp = datetime.fromisoformat(timestamp_val.replace('Z', ''))
                            except:
                                continue
                        elif isinstance(timestamp_val, (int, float)):
                            try:
                                timestamp = datetime.fromtimestamp(float(timestamp_val))
                            except:
                                continue
                    
                    if timestamp and timestamp >= twelve_hours_ago:
                        # Get pattern from either field
                        pattern = signal.get('pattern', signal.get('pattern_type', 'UNKNOWN'))
                        win = signal.get('win')
                        confidence = signal.get('confidence', signal.get('quality_score', 0))
                        
                        pattern_stats[pattern]['total'] += 1
                        
                        # Track confidence for averaging
                        if confidence:
                            pattern_stats[pattern]['confidences'].append(float(confidence))
                        
                        if win is True:
                            pattern_stats[pattern]['wins'] += 1
                        elif win is False:
                            pattern_stats[pattern]['losses'] += 1
                        else:
                            pattern_stats[pattern]['pending'] += 1
                            
                        # Store recent signal for detailed view
                        recent_signals.append({
                            'timestamp': timestamp.strftime('%H:%M'),
                            'pattern': pattern,
                            'pair': signal.get('pair', signal.get('symbol', 'N/A')),
                            'direction': signal.get('direction', 'N/A'),
                            'win': win,
                            'confidence': confidence,
                            'signal_class': signal.get('signal_class', 'N/A'),
                            'signal_id': signal.get('signal_id', 'N/A')[-12:]  # Last 12 chars
                        })
                        
                except json.JSONDecodeError:
                    continue
                    
    print(f'Processed {signal_count} total signals from log file')
    
except FileNotFoundError:
    print("ERROR: comprehensive_tracking.jsonl not found")
    exit(1)

# Calculate win rates and average confidence
for pattern in pattern_stats:
    completed = pattern_stats[pattern]['wins'] + pattern_stats[pattern]['losses']
    if completed > 0:
        pattern_stats[pattern]['win_rate'] = (pattern_stats[pattern]['wins'] / completed) * 100
    
    # Calculate average confidence
    if pattern_stats[pattern]['confidences']:
        pattern_stats[pattern]['avg_confidence'] = sum(pattern_stats[pattern]['confidences']) / len(pattern_stats[pattern]['confidences'])

# Sort patterns by total signals (most active first)
sorted_patterns = sorted(pattern_stats.items(), key=lambda x: x[1]['total'], reverse=True)

print('=== PATTERN PERFORMANCE SUMMARY (All Patterns) ===')
header = f"{'Pattern':<25} {'Total':<6} {'Wins':<5} {'Loss':<5} {'Pend':<5} {'Win%':<6} {'AvgConf':<8} {'Status':<10}"
print(header)
print('-' * 85)

total_signals = 0
total_wins = 0
total_losses = 0
total_pending = 0

for pattern, stats in sorted_patterns:
    if stats['total'] == 0:  # Skip empty patterns
        continue
        
    total_signals += stats['total']
    total_wins += stats['wins']
    total_losses += stats['losses']
    total_pending += stats['pending']
    
    # Status indicator
    if stats['win_rate'] >= 70:
        status = '🟢 STRONG'
    elif stats['win_rate'] >= 50:
        status = '🟡 OK'
    elif stats['win_rate'] > 0:
        status = '🔴 WEAK'
    else:
        status = '⚪ N/A'
    
    row = f"{pattern:<25} {stats['total']:<6} {stats['wins']:<5} {stats['losses']:<5} {stats['pending']:<5} {stats['win_rate']:<6.1f} {stats['avg_confidence']:<8.1f} {status:<10}"
    print(row)

print('-' * 85)
overall_completed = total_wins + total_losses
overall_win_rate = (total_wins / overall_completed * 100) if overall_completed > 0 else 0

overall_row = f"{'OVERALL':<25} {total_signals:<6} {total_wins:<5} {total_losses:<5} {total_pending:<5} {overall_win_rate:<6.1f}"
print(overall_row)
print()

# Group by signal class if available
print('=== PERFORMANCE BY SIGNAL CLASS ===')
class_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0})
for signal in recent_signals:
    signal_class = signal['signal_class']
    class_stats[signal_class]['total'] += 1
    if signal['win'] is True:
        class_stats[signal_class]['wins'] += 1
    elif signal['win'] is False:
        class_stats[signal_class]['losses'] += 1

for sig_class, stats in class_stats.items():
    completed = stats['wins'] + stats['losses']
    if completed > 0:
        stats['win_rate'] = (stats['wins'] / completed) * 100
    print(f"{sig_class:<12} Total: {stats['total']:<4} Wins: {stats['wins']:<3} Losses: {stats['losses']:<3} Win Rate: {stats['win_rate']:<6.1f}%")

print()
print('=== TOP/BOTTOM PERFORMERS (Minimum 5 signals) ===')
qualified_patterns = [(p, s) for p, s in sorted_patterns if s['total'] >= 5 and s['wins'] + s['losses'] > 0]

if qualified_patterns:
    # Best performers
    best = sorted(qualified_patterns, key=lambda x: x[1]['win_rate'], reverse=True)[:3]
    print('🟢 TOP PERFORMERS:')
    for pattern, stats in best:
        print(f"   {pattern}: {stats['win_rate']:.1f}% win rate ({stats['wins']}/{stats['wins']+stats['losses']} signals)")
    
    # Worst performers  
    worst = sorted(qualified_patterns, key=lambda x: x[1]['win_rate'])[:3]
    print('🔴 BOTTOM PERFORMERS:')
    for pattern, stats in worst:
        print(f"   {pattern}: {stats['win_rate']:.1f}% win rate ({stats['wins']}/{stats['wins']+stats['losses']} signals)")

print()
print('=== RECENT SIGNALS DETAIL (Last 15) ===')
detail_header = f"{'Time':<6} {'Pattern':<20} {'Pair':<8} {'Dir':<4} {'Win':<4} {'Conf':<5} {'Class':<8}"
print(detail_header)
print('-' * 60)

# Show last 15 signals
for signal in recent_signals[-15:]:
    win_status = '✅' if signal['win'] is True else '❌' if signal['win'] is False else '⏳'
    detail_row = f"{signal['timestamp']:<6} {signal['pattern']:<20} {signal['pair']:<8} {signal['direction']:<4} {win_status:<4} {signal['confidence']:<5.1f} {signal['signal_class']:<8}"
    print(detail_row)

print()
print(f'📊 SUMMARY:')
print(f'• Total Patterns Found: {len([p for p in pattern_stats if pattern_stats[p]["total"] > 0])}')
print(f'• Total Signals (12h): {len(recent_signals)}')
print(f'• Overall Win Rate: {overall_win_rate:.1f}%')
print(f'• Analysis Time: {now.strftime("%H:%M:%S")}')