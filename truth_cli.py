#!/usr/bin/env python3
"""
🎯 TRUTH CLI - Command Line Interface for Signal Truth Tracking
Quick inspection and analysis of signal lifecycle data
"""

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import sys

def load_truth_log(truth_log_path: str) -> List[Dict]:
    """Load all entries from truth log"""
    entries = []
    
    try:
        with open(truth_log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entries.append(data)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"❌ Truth log not found: {truth_log_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading truth log: {e}")
        return []
    
    return entries

def inspect_signal(signal_id: str, truth_log_path: str):
    """Inspect specific signal lifecycle"""
    entries = load_truth_log(truth_log_path)
    signal_entries = [e for e in entries if e.get('signal_id') == signal_id]
    
    if not signal_entries:
        print(f"❌ No entries found for signal: {signal_id}")
        return
    
    print(f"\n🔍 SIGNAL LIFECYCLE: {signal_id}")
    print("=" * 80)
    
    # Sort by timestamp
    signal_entries.sort(key=lambda x: x.get('timestamp', ''))
    
    for i, entry in enumerate(signal_entries, 1):
        status = entry.get('status', 'unknown')
        timestamp = entry.get('timestamp', '')[:19]  # Remove microseconds
        result = entry.get('result', '')
        pips = entry.get('pips_result', '')
        runtime = entry.get('runtime_seconds', '')
        
        status_emoji = {
            'generated': '🎯',
            'fired': '🔥',
            'filtered': '🚫',
            'expired': '⏰',
            'completed': '✅' if result == 'WIN' else '❌'
        }.get(status, '❓')
        
        print(f"{i}. {status_emoji} {status.upper()} - {timestamp}")
        
        if status == 'generated':
            symbol = entry.get('symbol', '')
            direction = entry.get('direction', '')
            confidence = entry.get('confidence', 0)
            source = entry.get('source', '')
            print(f"   {symbol} {direction} @{confidence:.1f}% confidence ({source})")
            
            entry_price = entry.get('entry_price')
            stop_loss = entry.get('stop_loss')
            take_profit = entry.get('take_profit')
            if entry_price:
                print(f"   Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
        
        elif status == 'fired':
            user_count = entry.get('user_count', 0)
            print(f"   Dispatched to {user_count} user(s)")
        
        elif status == 'filtered':
            fire_reason = entry.get('fire_reason', 'unknown')
            print(f"   Filter reason: {fire_reason}")
        
        elif status == 'completed':
            if result and pips and runtime:
                print(f"   Result: {result} {pips:+.1f} pips ({runtime}s runtime)")
        
        print()

def show_recent_signals(count: int, truth_log_path: str):
    """Show recent signal entries"""
    entries = load_truth_log(truth_log_path)
    
    if not entries:
        print("❌ No signals found in truth log")
        return
    
    # Get last N entries
    recent_entries = entries[-count:] if len(entries) >= count else entries
    
    print(f"\n📊 RECENT {len(recent_entries)} SIGNAL ENTRIES")
    print("=" * 120)
    print(f"{'Timestamp':<20} {'Signal ID':<28} {'Symbol':<8} {'Status':<10} {'Confidence':<10} {'Result':<6} {'Pips':<8}")
    print("-" * 120)
    
    for entry in recent_entries:
        timestamp = entry.get('timestamp', '')[:19]
        signal_id = entry.get('signal_id', 'unknown')[:27]
        symbol = entry.get('symbol', '')
        status = entry.get('status', '')
        confidence = entry.get('confidence', 0)
        result = entry.get('result', '') or '-'
        pips = entry.get('pips_result', '')
        
        confidence_str = f"{confidence:.1f}%" if confidence > 0 else '-'
        pips_str = f"{pips:+.1f}" if pips != '' else '-'
        
        print(f"{timestamp:<20} {signal_id:<28} {symbol:<8} {status:<10} {confidence_str:<10} {result:<6} {pips_str:<8}")

def show_signal_stats(truth_log_path: str):
    """Show comprehensive signal statistics"""
    entries = load_truth_log(truth_log_path)
    
    if not entries:
        print("❌ No signals found in truth log")
        return
    
    # Analyze data
    status_counts = defaultdict(int)
    source_counts = defaultdict(int)
    symbol_counts = defaultdict(int)
    completed_signals = []
    
    for entry in entries:
        status = entry.get('status', 'unknown')
        source = entry.get('source', 'unknown')
        symbol = entry.get('symbol', '')
        
        status_counts[status] += 1
        source_counts[source] += 1
        if symbol:
            symbol_counts[symbol] += 1
        
        if status == 'completed':
            completed_signals.append(entry)
    
    print(f"\n📈 SIGNAL STATISTICS")
    print("=" * 60)
    print(f"Total Entries: {len(entries)}")
    print()
    
    # Status breakdown
    print("📊 Status Breakdown:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / len(entries)) * 100
        print(f"  {status.capitalize()}: {count} ({percentage:.1f}%)")
    print()
    
    # Source breakdown
    print("🔧 Source Breakdown:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(entries)) * 100
        print(f"  {source}: {count} ({percentage:.1f}%)")
    print()
    
    # Symbol breakdown (top 10)
    print("💱 Top 10 Symbols:")
    top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for symbol, count in top_symbols:
        percentage = (count / len(entries)) * 100
        print(f"  {symbol}: {count} ({percentage:.1f}%)")
    print()
    
    # Performance analysis
    if completed_signals:
        wins = [s for s in completed_signals if s.get('result') == 'WIN']
        losses = [s for s in completed_signals if s.get('result') == 'LOSS']
        
        win_rate = (len(wins) / len(completed_signals)) * 100
        total_pips = sum(s.get('pips_result', 0) for s in completed_signals)
        avg_runtime = sum(s.get('runtime_seconds', 0) for s in completed_signals) / len(completed_signals)
        
        print("🎯 Performance Analysis:")
        print(f"  Completed Signals: {len(completed_signals)}")
        print(f"  Win Rate: {len(wins)}/{len(completed_signals)} ({win_rate:.1f}%)")
        print(f"  Total Pips: {total_pips:+.1f}")
        print(f"  Average Runtime: {avg_runtime:.0f} seconds")
        
        if wins:
            avg_win_pips = sum(s.get('pips_result', 0) for s in wins) / len(wins)
            print(f"  Average Win: +{avg_win_pips:.1f} pips")
        
        if losses:
            avg_loss_pips = sum(s.get('pips_result', 0) for s in losses) / len(losses)
            print(f"  Average Loss: {avg_loss_pips:.1f} pips")

def show_active_signals(truth_log_path: str):
    """Show currently active signals"""
    entries = load_truth_log(truth_log_path)
    
    # Find signals that are generated or fired but not completed/expired/filtered
    active_signals = {}
    
    for entry in entries:
        signal_id = entry.get('signal_id')
        status = entry.get('status')
        
        if signal_id:
            if status in ['generated', 'fired']:
                active_signals[signal_id] = entry
            elif status in ['completed', 'expired', 'filtered']:
                # Remove from active if it was there
                active_signals.pop(signal_id, None)
    
    if not active_signals:
        print("✅ No active signals - all signals have been completed, expired, or filtered")
        return
    
    print(f"\n⚡ ACTIVE SIGNALS ({len(active_signals)})")
    print("=" * 100)
    print(f"{'Signal ID':<28} {'Symbol':<8} {'Direction':<4} {'Status':<8} {'Confidence':<10} {'Age (min)':<10}")
    print("-" * 100)
    
    current_time = datetime.now(timezone.utc)
    
    for signal_id, entry in sorted(active_signals.items()):
        symbol = entry.get('symbol', '')
        direction = entry.get('direction', '')
        status = entry.get('status', '')
        confidence = entry.get('confidence', 0)
        timestamp_str = entry.get('timestamp', '')
        
        # Calculate age
        try:
            signal_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_minutes = (current_time - signal_time).total_seconds() / 60
            age_str = f"{age_minutes:.0f}"
        except:
            age_str = "unknown"
        
        confidence_str = f"{confidence:.1f}%" if confidence > 0 else '-'
        
        print(f"{signal_id:<28} {symbol:<8} {direction:<4} {status:<8} {confidence_str:<10} {age_str:<10}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Truth CLI - Signal lifecycle inspection tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 truth_cli.py --recent 20                           # Show recent 20 entries
  python3 truth_cli.py --inspect VENOM_EURUSD_000123         # Inspect specific signal
  python3 truth_cli.py --stats                               # Show comprehensive stats
  python3 truth_cli.py --active                              # Show active signals
  python3 truth_cli.py --log /path/to/custom_truth_log.jsonl # Use custom log file
        """
    )
    
    parser.add_argument('--recent', type=int, default=10, help='Show recent N entries (default: 10)')
    parser.add_argument('--inspect', type=str, help='Inspect specific signal ID')
    parser.add_argument('--stats', action='store_true', help='Show comprehensive statistics')
    parser.add_argument('--active', action='store_true', help='Show active signals')
    parser.add_argument('--log', type=str, default='/root/HydraX-v2/truth_log.jsonl', help='Truth log file path')
    
    args = parser.parse_args()
    
    if args.inspect:
        inspect_signal(args.inspect, args.log)
    elif args.stats:
        show_signal_stats(args.log)
    elif args.active:
        show_active_signals(args.log)
    else:
        show_recent_signals(args.recent, args.log)

if __name__ == "__main__":
    main()