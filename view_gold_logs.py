#!/usr/bin/env python3
"""View and analyze gold signal delivery logs"""

import json
import os
from datetime import datetime
from collections import defaultdict

def view_gold_logs():
    """Display gold signal delivery logs"""
    
    log_file = "/root/HydraX-v2/logs/gold_dm_log.jsonl"
    
    print("🏆 GOLD SIGNAL DELIVERY LOG VIEWER")
    print("=" * 80)
    
    if not os.path.exists(log_file):
        print("❌ No gold signal logs found yet.")
        print(f"   Log file will be created at: {log_file}")
        return
    
    # Read all log entries
    logs = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except:
                continue
    
    if not logs:
        print("📭 Log file exists but is empty.")
        return
    
    # Display summary
    print(f"\n📊 SUMMARY")
    print(f"Total Gold Signals Delivered: {len(logs)}")
    
    # Group by user
    user_stats = defaultdict(lambda: {'count': 0, 'total_xp': 0, 'signals': []})
    
    for log in logs:
        user_id = log.get('user_id', 'unknown')
        telegram_id = log.get('telegram_id', 'unknown')
        user_key = f"{user_id} ({telegram_id})"
        
        user_stats[user_key]['count'] += 1
        user_stats[user_key]['total_xp'] += log.get('xp_awarded', 0)
        user_stats[user_key]['signals'].append(log)
    
    # Display user statistics
    print(f"\n👥 USER STATISTICS")
    print("-" * 80)
    print(f"{'User':<30} {'Signals':<10} {'Total XP':<10} {'Region':<10}")
    print("-" * 80)
    
    for user_key, stats in user_stats.items():
        last_signal = stats['signals'][-1]
        region = last_signal.get('user_region', 'unknown')
        print(f"{user_key:<30} {stats['count']:<10} {stats['total_xp']:<10} {region:<10}")
    
    # Display recent signals
    print(f"\n📨 RECENT GOLD SIGNALS (Last 10)")
    print("-" * 80)
    
    for log in logs[-10:]:
        timestamp = log.get('timestamp', 'unknown')
        user_id = log.get('user_id', 'unknown')
        telegram_id = log.get('telegram_id', 'unknown')
        signal_id = log.get('signal_id', 'unknown')
        direction = log.get('direction', 'unknown')
        entry = log.get('entry', 0)
        tp = log.get('tp', 0)
        sl = log.get('sl', 0)
        confidence = log.get('confidence', 0)
        
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            time_str = timestamp
        
        print(f"\n🕒 {time_str}")
        print(f"   User: {user_id} ({telegram_id})")
        print(f"   Signal: {signal_id}")
        print(f"   Trade: {direction} XAUUSD @ {entry}")
        print(f"   TP: {tp} | SL: {sl}")
        print(f"   Confidence: {confidence}%")
        print(f"   XP Awarded: +200")
    
    # Direction statistics
    print(f"\n📈 DIRECTION STATISTICS")
    buy_count = sum(1 for log in logs if log.get('direction', '').upper() == 'BUY')
    sell_count = sum(1 for log in logs if log.get('direction', '').upper() == 'SELL')
    print(f"BUY Signals: {buy_count}")
    print(f"SELL Signals: {sell_count}")
    
    # Signal type statistics
    print(f"\n⚡ SIGNAL TYPE DISTRIBUTION")
    signal_types = defaultdict(int)
    for log in logs:
        signal_type = log.get('signal_type', 'unknown')
        signal_types[signal_type] += 1
    
    for signal_type, count in signal_types.items():
        percentage = (count / len(logs)) * 100
        print(f"{signal_type}: {count} ({percentage:.1f}%)")
    
    print("\n" + "=" * 80)
    print("✅ Gold signal logging is active and tracking all XAUUSD deliveries")

if __name__ == "__main__":
    view_gold_logs()