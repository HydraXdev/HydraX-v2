#!/usr/bin/env python3
"""
Analyze pattern performance from comprehensive tracking data
"""
import json
from collections import defaultdict
from datetime import datetime

def analyze_performance():
    stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'timeouts': 0})
    
    # Try multiple tracking file locations
    tracking_files = [
        '/root/HydraX-v2/comprehensive_tracking.jsonl',
        '/root/HydraX-v2/optimized_tracking.jsonl',
        '/root/HydraX-v2/logs/comprehensive_tracking.jsonl'
    ]
    
    for tracking_file in tracking_files:
        try:
            with open(tracking_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        pattern = data.get('pattern_type')
                        outcome = data.get('outcome')
                        
                        if pattern and pattern != 'UNKNOWN':
                            stats[pattern]['total'] += 1
                            
                            if outcome == 'WIN':
                                stats[pattern]['wins'] += 1
                            elif outcome == 'LOSS':
                                stats[pattern]['losses'] += 1
                            elif outcome == 'TIMEOUT':
                                stats[pattern]['timeouts'] += 1
                                
                    except json.JSONDecodeError:
                        continue
                    except Exception:
                        continue
                        
        except FileNotFoundError:
            print(f"File not found: {tracking_file}")
            continue
    
    print(f"\n🎯 PATTERN PERFORMANCE ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if not stats:
        print("❌ NO PATTERN DATA FOUND IN TRACKING FILES")
        return
    
    # Sort by total signals
    for pattern, data in sorted(stats.items(), key=lambda x: -x[1]['total']):
        total = data['total']
        wins = data['wins']
        losses = data['losses']
        timeouts = data['timeouts']
        
        if total > 0:
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            # Determine action based on win rate
            if win_rate >= 40:
                action = "✅ PROMOTE (lower threshold to 55%)"
                emoji = "🔥"
            elif win_rate >= 35:
                action = "⚠️ MONITOR (keep at 65%)"
                emoji = "👀"
            elif win_rate >= 30:
                action = "🔻 RESTRICT (raise to 75%)"
                emoji = "⚠️"
            else:
                action = "❌ DISABLE (raise to 90%)"
                emoji = "🔴"
            
            print(f"\n{emoji} {pattern:30s}")
            print(f"   Total: {total:4d} | Wins: {wins:3d} | Losses: {losses:3d} | Timeouts: {timeouts:3d}")
            print(f"   Win Rate: {win_rate:5.1f}% | {action}")

if __name__ == "__main__":
    analyze_performance()