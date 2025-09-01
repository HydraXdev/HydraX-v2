#!/usr/bin/env python3
"""
🔍 TRUTH LOG QUERY CLI TOOL
Command-line interface for querying truth_log.jsonl
Provides analytics and debugging capabilities for operators
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class TruthLogQuery:
    """CLI tool for querying truth_log.jsonl"""
    
    def __init__(self, truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl"):
        self.truth_log_path = Path(truth_log_path)
        
        if not self.truth_log_path.exists():
            print(f"❌ Truth log not found: {self.truth_log_path}")
            sys.exit(1)
    
    def load_all_records(self) -> List[Dict[str, Any]]:
        """Load all records from truth log"""
        records = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        records.append(data)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Error parsing line {line_num}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Error loading truth log: {e}")
            sys.exit(1)
            
        return records
    
    def filter_by_pair(self, records: List[Dict], pair: str) -> List[Dict]:
        """Filter records by currency pair"""
        return [r for r in records if r.get('symbol', '').upper() == pair.upper()]
    
    def filter_by_result(self, records: List[Dict], result: str) -> List[Dict]:
        """Filter records by result (WIN/LOSS)"""
        return [r for r in records if r.get('result', '').upper() == result.upper()]
    
    def filter_by_time_window(self, records: List[Dict], hours: int) -> List[Dict]:
        """Filter records by time window"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        filtered = []
        
        for record in records:
            completed_at = record.get('completed_at')
            if completed_at:
                try:
                    if isinstance(completed_at, str):
                        ts = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).timestamp()
                    else:
                        ts = float(completed_at)
                    
                    if ts >= cutoff_time:
                        filtered.append(record)
                except:
                    continue
        
        return filtered
    
    def filter_by_tcs_range(self, records: List[Dict], min_tcs: float, max_tcs: float) -> List[Dict]:
        """Filter records by TCS score range"""
        filtered = []
        
        for record in records:
            tcs = record.get('tcs_score')
            if tcs is not None:
                try:
                    tcs_float = float(tcs)
                    if min_tcs <= tcs_float <= max_tcs:
                        filtered.append(record)
                except:
                    continue
        
        return filtered
    
    def filter_by_runtime(self, records: List[Dict], min_minutes: int, max_minutes: int) -> List[Dict]:
        """Filter records by runtime in minutes"""
        filtered = []
        
        for record in records:
            runtime = record.get('runtime_seconds')
            if runtime is not None:
                try:
                    runtime_minutes = float(runtime) / 60
                    if min_minutes <= runtime_minutes <= max_minutes:
                        filtered.append(record)
                except:
                    continue
        
        return filtered
    
    def display_summary(self, records: List[Dict]):
        """Display summary statistics"""
        if not records:
            print("📊 No records found matching criteria")
            return
        
        total = len(records)
        wins = sum(1 for r in records if r.get('result') == 'WIN')
        losses = sum(1 for r in records if r.get('result') == 'LOSS')
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Runtime analysis
        runtimes = []
        for record in records:
            runtime = record.get('runtime_seconds')
            if runtime is not None:
                try:
                    runtimes.append(float(runtime) / 60)  # Convert to minutes
                except:
                    continue
        
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0
        
        # TCS analysis
        tcs_scores = []
        for record in records:
            tcs = record.get('tcs_score')
            if tcs is not None:
                try:
                    tcs_scores.append(float(tcs))
                except:
                    continue
        
        avg_tcs = sum(tcs_scores) / len(tcs_scores) if tcs_scores else 0
        
        print(f"📊 TRUTH LOG SUMMARY")
        print(f"=" * 50)
        print(f"Total Records: {total}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")
        print(f"Black Box Confirmed Win Rate: {win_rate:.1f}%")
        print(f"Average Runtime: {avg_runtime:.1f} minutes")
        print(f"Average TCS Score: {avg_tcs:.1f}")
        
        # Pair breakdown
        pairs = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        for record in records:
            symbol = record.get('symbol', 'UNKNOWN')
            result = record.get('result')
            
            pairs[symbol]['total'] += 1
            if result == 'WIN':
                pairs[symbol]['wins'] += 1
            elif result == 'LOSS':
                pairs[symbol]['losses'] += 1
        
        if len(pairs) > 1:
            print(f"\n📈 PAIR BREAKDOWN")
            print(f"-" * 30)
            for symbol, stats in sorted(pairs.items(), key=lambda x: x[1]['total'], reverse=True):
                pair_win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"{symbol:8} | {stats['total']:3} trades | {pair_win_rate:5.1f}% win rate")
    
    def display_detailed(self, records: List[Dict], limit: int = 10):
        """Display detailed record information"""
        if not records:
            print("📊 No records found matching criteria")
            return
        
        print(f"📋 DETAILED RECORDS (showing {min(limit, len(records))} of {len(records)})")
        print(f"=" * 80)
        
        # Sort by completion time (most recent first)
        sorted_records = sorted(records, key=lambda x: x.get('completed_at', ''), reverse=True)
        
        for i, record in enumerate(sorted_records[:limit]):
            result = record.get('result', 'UNKNOWN')
            symbol = record.get('symbol', 'N/A')
            tcs = record.get('tcs_score', 'N/A')
            runtime = record.get('runtime_seconds', 0)
            exit_type = record.get('exit_type', 'N/A')
            signal_id = record.get('signal_id', 'N/A')
            
            runtime_min = float(runtime) / 60 if runtime else 0
            
            # Format timestamp
            completed_at = record.get('completed_at', 'N/A')
            if isinstance(completed_at, str) and completed_at != 'N/A':
                try:
                    dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = completed_at
            else:
                time_str = str(completed_at)
            
            # Color coding for result
            result_icon = "✅" if result == "WIN" else "❌" if result == "LOSS" else "❓"
            
            print(f"{i+1:2}. {result_icon} {result:4} | {symbol:8} | TCS: {tcs:>5} | "
                  f"Runtime: {runtime_min:5.1f}m | Exit: {exit_type:12} | {time_str}")
            
            if len(signal_id) < 50:  # Only show if not too long
                print(f"    Signal ID: {signal_id}")
            print()
    
    def export_csv(self, records: List[Dict], output_file: str):
        """Export records to CSV format"""
        if not records:
            print("❌ No records to export")
            return
        
        import csv
        
        try:
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ['signal_id', 'symbol', 'result', 'tcs_score', 'runtime_seconds', 
                             'exit_type', 'completed_at', 'signal_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in records:
                    row = {field: record.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            print(f"✅ Exported {len(records)} records to {output_file}")
            
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Query and analyze BITTEN truth_log.jsonl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Show all records summary
  python3 truth_log_query.py --summary
  
  # Show EURUSD wins in last 24 hours
  python3 truth_log_query.py --pair EURUSD --result WIN --time 24 --detailed
  
  # Find high TCS trades that lost
  python3 truth_log_query.py --result LOSS --tcs-min 85 --tcs-max 100 --detailed
  
  # Export all trades from last week to CSV
  python3 truth_log_query.py --time 168 --export trades_week.csv
  
  # Quick runtime analysis of losses
  python3 truth_log_query.py --result LOSS --runtime-max 30 --summary
        """
    )
    
    # Filter arguments
    parser.add_argument('--pair', type=str, help='Filter by currency pair (e.g., EURUSD)')
    parser.add_argument('--result', type=str, choices=['WIN', 'LOSS'], help='Filter by result')
    parser.add_argument('--time', type=int, help='Filter by hours back from now')
    parser.add_argument('--tcs-min', type=float, help='Minimum TCS score')
    parser.add_argument('--tcs-max', type=float, help='Maximum TCS score')
    parser.add_argument('--runtime-min', type=int, help='Minimum runtime in minutes')
    parser.add_argument('--runtime-max', type=int, help='Maximum runtime in minutes')
    
    # Display arguments
    parser.add_argument('--summary', action='store_true', help='Show summary statistics')
    parser.add_argument('--detailed', action='store_true', help='Show detailed records')
    parser.add_argument('--limit', type=int, default=10, help='Limit detailed results (default: 10)')
    
    # Export arguments
    parser.add_argument('--export', type=str, help='Export results to CSV file')
    
    # Source verification
    parser.add_argument('--verify-source', action='store_true', 
                       help='Only show entries tagged with "source": "venom_scalp_master"')
    
    # Truth log path
    parser.add_argument('--log-path', type=str, default='/root/HydraX-v2/truth_log.jsonl',
                       help='Path to truth_log.jsonl file')
    
    args = parser.parse_args()
    
    # Initialize query tool
    query_tool = TruthLogQuery(args.log_path)
    
    # Load all records
    print(f"🔍 Loading truth log: {args.log_path}")
    records = query_tool.load_all_records()
    print(f"📊 Loaded {len(records)} total records")
    
    # Apply filters
    if args.verify_source:
        records = [r for r in records if r.get('source') == 'venom_scalp_master']
        print(f"🔒 Filtered by verified source 'venom_scalp_master': {len(records)} records")
    
    if args.pair:
        records = query_tool.filter_by_pair(records, args.pair)
        print(f"🎯 Filtered by pair {args.pair}: {len(records)} records")
    
    if args.result:
        records = query_tool.filter_by_result(records, args.result)
        print(f"🎯 Filtered by result {args.result}: {len(records)} records")
    
    if args.time:
        records = query_tool.filter_by_time_window(records, args.time)
        print(f"🎯 Filtered by time window {args.time}h: {len(records)} records")
    
    if args.tcs_min is not None or args.tcs_max is not None:
        tcs_min = args.tcs_min if args.tcs_min is not None else 0
        tcs_max = args.tcs_max if args.tcs_max is not None else 100
        records = query_tool.filter_by_tcs_range(records, tcs_min, tcs_max)
        print(f"🎯 Filtered by TCS range {tcs_min}-{tcs_max}: {len(records)} records")
    
    if args.runtime_min is not None or args.runtime_max is not None:
        runtime_min = args.runtime_min if args.runtime_min is not None else 0
        runtime_max = args.runtime_max if args.runtime_max is not None else 999999
        records = query_tool.filter_by_runtime(records, runtime_min, runtime_max)
        print(f"🎯 Filtered by runtime {runtime_min}-{runtime_max}min: {len(records)} records")
    
    print()  # Empty line
    
    # Display results
    if args.export:
        query_tool.export_csv(records, args.export)
    elif args.detailed:
        query_tool.display_detailed(records, args.limit)
    elif args.summary or not any([args.detailed, args.export]):
        query_tool.display_summary(records)
    
    if not records and not args.export:
        print("\n💡 TIP: Try broader filter criteria or check if truth_log.jsonl has data")

if __name__ == "__main__":
    main()