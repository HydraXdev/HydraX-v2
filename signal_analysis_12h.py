#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

# Get 12 hours ago timestamp (make timezone aware)
now = datetime.now(pytz.UTC)
twelve_hours_ago = now - timedelta(hours=12)

# Data structures for analysis
pattern_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0, 'win_rate': 0.0})
recent_signals = []

print('=== SIGNAL ANALYSIS: Last 12 Hours ===')
print(f'Analysis Period: {twelve_hours_ago.strftime("%Y-%m-%d %H:%M")} to {now.strftime("%Y-%m-%d %H:%M")}')
print()

# Parse comprehensive tracking data
try:
    with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    signal = json.loads(line.strip())
                    
                    # Parse timestamp
                    timestamp_str = signal.get('time_utc', signal.get('timestamp', ''))
                    if timestamp_str:
                        try:
                            if isinstance(timestamp_str, str) and 'T' in timestamp_str:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            elif isinstance(timestamp_str, (int, float)):
                                timestamp = datetime.fromtimestamp(float(timestamp_str), tz=pytz.UTC)
                            else:
                                continue
                        except:
                            continue
                            
                        # Only analyze signals from last 12 hours
                        if timestamp >= twelve_hours_ago:
                            pattern = signal.get('pattern_type', signal.get('pattern', 'UNKNOWN'))
                            win = signal.get('win')
                            
                            pattern_stats[pattern]['total'] += 1
                            
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
                                'confidence': signal.get('confidence', signal.get('confidence_score', 'N/A')),
                                'signal_id': signal.get('signal_id', 'N/A')[-12:]  # Last 12 chars
                            })
                            
                except json.JSONDecodeError:
                    continue
except FileNotFoundError:
    print("ERROR: comprehensive_tracking.jsonl not found")
    exit(1)

# Calculate win rates
for pattern in pattern_stats:
    completed = pattern_stats[pattern]['wins'] + pattern_stats[pattern]['losses']
    if completed > 0:
        pattern_stats[pattern]['win_rate'] = (pattern_stats[pattern]['wins'] / completed) * 100

# Sort patterns by performance
sorted_patterns = sorted(pattern_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)

print('=== PATTERN PERFORMANCE SUMMARY ===')
header = f"{'Pattern':<25} {'Total':<6} {'Wins':<5} {'Loss':<5} {'Pend':<5} {'Win%':<6} {'Status':<10}"
print(header)
print('-' * 75)

total_signals = 0
total_wins = 0
total_losses = 0
total_pending = 0

for pattern, stats in sorted_patterns:
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
    
    row = f"{pattern:<25} {stats['total']:<6} {stats['wins']:<5} {stats['losses']:<5} {stats['pending']:<5} {stats['win_rate']:<6.1f} {status:<10}"
    print(row)

print('-' * 75)
overall_completed = total_wins + total_losses
overall_win_rate = (total_wins / overall_completed * 100) if overall_completed > 0 else 0

overall_row = f"{'OVERALL':<25} {total_signals:<6} {total_wins:<5} {total_losses:<5} {total_pending:<5} {overall_win_rate:<6.1f}"
print(overall_row)
print()

print('=== RECENT SIGNALS DETAIL (Last 20) ===')
detail_header = f"{'Time':<6} {'Pattern':<20} {'Pair':<8} {'Dir':<4} {'Win':<4} {'Conf':<5} {'Signal ID':<12}"
print(detail_header)
print('-' * 65)

# Show last 20 signals
for signal in recent_signals[-20:]:
    win_status = '✅' if signal['win'] is True else '❌' if signal['win'] is False else '⏳'
    detail_row = f"{signal['timestamp']:<6} {signal['pattern']:<20} {signal['pair']:<8} {signal['direction']:<4} {win_status:<4} {signal['confidence']:<5} {signal['signal_id']:<12}"
    print(detail_row)

print()
print(f'Total Signals Analyzed: {len(recent_signals)}')
print(f'Analysis completed at: {now.strftime("%H:%M:%S")}')