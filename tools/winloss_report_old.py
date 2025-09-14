#!/usr/bin/env python3
"""
WINLOSS REPORT - Truth Only
Standardized report for signal performance analysis
Uses broker outcomes for executed trades, shadow outcomes for non-executed
"""

import sys
import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class WinLossReport:
    """Truth-only win/loss report with standardized output"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def run_report(self, 
                   from_time: str,
                   to_time: str,
                   population: str = "FIRED",
                   timeout_policy: str = "loss",
                   bins_type: str = "calibrated") -> None:
        """Generate and print the standardized winloss report"""
        
        # Convert times to unix timestamps
        from_ts = int(datetime.fromisoformat(from_time.replace('Z', '+00:00')).timestamp())
        to_ts = int(datetime.fromisoformat(to_time.replace('Z', '+00:00')).timestamp())
        
        # Print header
        print("=" * 80)
        print("WINLOSS REPORT - Truth Only")
        print("=" * 80)
        print(f"Period: {from_time} to {to_time}")
        print(f"Population: {population}")
        print(f"Timeout Policy: {timeout_policy}")
        print(f"Confidence Type: {bins}")
        print("=" * 80)
        
        # Get unified data
        signals = self._get_unified_signals(from_ts, to_ts, population, timeout_policy)
        
        if not signals:
            print("\nNo signals found in specified time range")
            return
            
        total_signals = len(signals)
        pending_signals = len([s for s in signals if s['outcome'] == 'PENDING'])
        analyzed_signals = total_signals - pending_signals
        
        print(f"\nTotal Signals: {total_signals}")
        print(f"Analyzed: {analyzed_signals}")
        print(f"Pending: {pending_signals}")
        
        if analyzed_signals == 0:
            print("\nNo completed signals to analyze")
            return
            
        # Filter out pending for analysis
        analyzed = [s for s in signals if s['outcome'] != 'PENDING']
        
        # Table A - Confidence Bins
        print("\n" + "=" * 80)
        print("TABLE A - CONFIDENCE BINS")
        print("=" * 80)
        self._print_confidence_bins(analyzed, bins, timeout_policy)
        
        # Table B - Patterns
        print("\n" + "=" * 80)
        print("TABLE B - PATTERN PERFORMANCE")
        print("=" * 80)
        self._print_pattern_stats(analyzed, timeout_policy)
        
        # Table C - Sessions
        print("\n" + "=" * 80)
        print("TABLE C - SESSION PERFORMANCE")  
        print("=" * 80)
        self._print_session_stats(analyzed, timeout_policy)
        
        # Top/Bottom Performers
        print("\n" + "=" * 80)
        print("TOP/BOTTOM PERFORMERS (Min N=20)")
        print("=" * 80)
        self._print_top_bottom(analyzed, timeout_policy)
        
        # Footnotes
        print("\n" + "=" * 80)
        print("FOOTNOTES")
        print("=" * 80)
        print(f"- Timeout Policy: {timeout_policy.upper()}")
        print("- TRAIL counted as TP if achieved_r > 0, else SL")
        print("- MANUAL counted based on achieved_r (positive=TP, negative=SL)")
        print(f"- Excluded {pending_signals} pending signals from analysis")
        print("=" * 80)
    
    def _get_unified_signals(self, from_ts: int, to_ts: int, 
                             population: str, timeout_policy: str) -> List[Dict]:
        """Get signals from unified view or fallback to direct queries"""
        
        # First try to get from unified view
        query = """
        SELECT 
            signal_id, ts_fire, symbol, side, pattern, session,
            raw_confidence, calibrated_confidence, risk_reward,
            stop_pips, target_pips, outcome, achieved_r, duration_min, source
        FROM unified_outcomes
        WHERE ts_fire BETWEEN ? AND ?
        ORDER BY ts_fire DESC
        """
        
        cursor = self.conn.execute(query, (from_ts, to_ts))
        results = [dict(row) for row in cursor.fetchall()]
        
        if results:
            return results
            
        # Fallback: Build from existing tables
        print("\n[INFO] Unified view empty, building from existing tables...")
        return self._build_unified_from_legacy(from_ts, to_ts)
    
    def _build_unified_from_legacy(self, from_ts: int, to_ts: int) -> List[Dict]:
        """Build unified data from legacy tables"""
        
        # Get signals from main signals table
        query = """
        SELECT 
            signal_id, 
            created_at as ts_fire,
            symbol,
            direction as side,
            pattern_type as pattern,
            session,
            confidence as raw_confidence,
            calibrated_confidence,
            CASE 
                WHEN target_pips > 0 AND stop_pips > 0 
                THEN CAST(target_pips AS REAL) / CAST(stop_pips AS REAL)
                ELSE 1.0
            END as risk_reward,
            stop_pips,
            target_pips,
            outcome,
            pips_result
        FROM signals
        WHERE created_at BETWEEN ? AND ?
        ORDER BY created_at DESC
        """
        
        cursor = self.conn.execute(query, (from_ts, to_ts))
        signals = []
        
        for row in cursor.fetchall():
            signal = dict(row)
            
            # Get verified outcome if exists
            verified = self.conn.execute("""
                SELECT outcome, achieved_r, duration_min 
                FROM signal_outcomes_verified
                WHERE signal_id = ?
            """, (signal['signal_id'],)).fetchone()
            
            if verified:
                signal['outcome'] = verified['outcome']
                signal['achieved_r'] = verified['achieved_r']
                signal['duration_min'] = verified['duration_min']
                signal['source'] = 'BROKER'
            else:
                # Check shadow outcome
                shadow = self.conn.execute("""
                    SELECT outcome, 
                           CASE 
                               WHEN outcome = 'TP' THEN rr_target
                               WHEN outcome = 'SL' THEN -1.0
                               ELSE 0
                           END as achieved_r,
                           CAST((resolved_at - signaled_at) AS REAL) / 60 as duration_min
                    FROM signal_outcomes
                    WHERE signal_id = ?
                """, (signal['signal_id'],)).fetchone()
                
                if shadow:
                    signal['outcome'] = shadow['outcome']
                    signal['achieved_r'] = shadow['achieved_r'] 
                    signal['duration_min'] = shadow['duration_min']
                    signal['source'] = 'SHADOW'
                else:
                    signal['outcome'] = 'PENDING'
                    signal['achieved_r'] = 0
                    signal['duration_min'] = 0
                    signal['source'] = 'PENDING'
                    
            # Default session if missing
            if not signal['session']:
                hour = datetime.fromtimestamp(signal['ts_fire']).hour
                if 22 <= hour or hour < 8:
                    signal['session'] = 'ASIAN'
                elif 8 <= hour < 12:
                    signal['session'] = 'LONDON'
                elif 12 <= hour < 17:
                    signal['session'] = 'NY'
                else:
                    signal['session'] = 'OVERLAP'
                    
            # Use raw confidence if calibrated missing
            if not signal['calibrated_confidence']:
                signal['calibrated_confidence'] = signal['raw_confidence']
                
            signals.append(signal)
            
        return signals
    
    def _print_confidence_bins(self, signals: List[Dict], bins: str, timeout_policy: str):
        """Print confidence bin statistics"""
        
        conf_field = 'calibrated_confidence' if bins == 'calibrated' else 'raw_confidence'
        
        bin_ranges = [
            (70, 75, '70-75'),
            (75, 80, '75-80'),
            (80, 85, '80-85'),
            (85, 90, '85-90'),
            (90, 95, '90-95'),
            (95, 100, '95+')
        ]
        
        print(f"\n{'Bin':<10} {'N':<6} {'TP':<6} {'SL':<6} {'TO':<6} {'Win%':<8} {'Exp(R)':<8} {'Med(min)':<10} {'Coverage%':<10}")
        print("-" * 80)
        
        total_n = len(signals)
        
        for min_conf, max_conf, label in bin_ranges:
            bin_signals = [s for s in signals 
                          if min_conf <= (s[conf_field] or 0) < max_conf]
            
            if label == '95+':
                bin_signals = [s for s in signals if (s[conf_field] or 0) >= 95]
                
            if not bin_signals:
                print(f"{label:<10} {0:<6} {'-':<6} {'-':<6} {'-':<6} {'-':<8} {'-':<8} {'-':<10} {0:<10.1f}%")
                continue
                
            stats = self._calculate_stats(bin_signals, timeout_policy)
            coverage = (len(bin_signals) / total_n * 100) if total_n > 0 else 0
            
            print(f"{label:<10} {stats['n']:<6} {stats['tp']:<6} {stats['sl']:<6} "
                  f"{stats['timeout']:<6} {stats['win_pct']:<8.1f}% {stats['expectancy']:<8.2f} "
                  f"{stats['median_time']:<10.0f} {coverage:<10.1f}%")
    
    def _print_pattern_stats(self, signals: List[Dict], timeout_policy: str):
        """Print pattern performance statistics"""
        
        patterns = {}
        for signal in signals:
            pattern = signal['pattern'] or 'UNKNOWN'
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(signal)
        
        print(f"\n{'Pattern':<30} {'N':<8} {'Win%':<10} {'Exp(R)':<10} {'Med(min)':<10}")
        print("-" * 80)
        
        for pattern in sorted(patterns.keys()):
            pattern_signals = patterns[pattern]
            stats = self._calculate_stats(pattern_signals, timeout_policy)
            
            print(f"{pattern:<30} {stats['n']:<8} {stats['win_pct']:<10.1f}% "
                  f"{stats['expectancy']:<10.2f} {stats['median_time']:<10.0f}")
    
    def _print_session_stats(self, signals: List[Dict], timeout_policy: str):
        """Print session performance statistics"""
        
        sessions = {}
        for signal in signals:
            session = signal['session'] or 'UNKNOWN'
            if session not in sessions:
                sessions[session] = []
            sessions[session].append(signal)
        
        print(f"\n{'Session':<15} {'N':<8} {'Win%':<10} {'Exp(R)':<10} {'Med(min)':<10}")
        print("-" * 80)
        
        session_order = ['ASIAN', 'LONDON', 'NY', 'OVERLAP', 'UNKNOWN']
        
        for session in session_order:
            if session in sessions:
                session_signals = sessions[session]
                stats = self._calculate_stats(session_signals, timeout_policy)
                
                print(f"{session:<15} {stats['n']:<8} {stats['win_pct']:<10.1f}% "
                      f"{stats['expectancy']:<10.2f} {stats['median_time']:<10.0f}")
    
    def _print_top_bottom(self, signals: List[Dict], timeout_policy: str):
        """Print top and bottom performers by expectancy"""
        
        # Group by pattern and calculate stats
        pattern_stats = {}
        for signal in signals:
            pattern = signal['pattern'] or 'UNKNOWN'
            if pattern not in pattern_stats:
                pattern_stats[pattern] = []
            pattern_stats[pattern].append(signal)
        
        # Calculate expectancy for each pattern with min N=20
        performers = []
        for pattern, pattern_signals in pattern_stats.items():
            if len(pattern_signals) >= 20:
                stats = self._calculate_stats(pattern_signals, timeout_policy)
                performers.append((pattern, stats['expectancy'], stats['n'], stats['win_pct']))
        
        if not performers:
            print("\nNo patterns with N >= 20")
            return
            
        # Sort by expectancy
        performers.sort(key=lambda x: x[1], reverse=True)
        
        # Top 3
        print("\nTOP PERFORMERS:")
        for i, (pattern, exp, n, win_pct) in enumerate(performers[:3], 1):
            print(f"{i}. {pattern}: Exp={exp:.2f}, N={n}, Win%={win_pct:.1f}%")
            
        # Bottom 3
        print("\nBOTTOM PERFORMERS:")
        for i, (pattern, exp, n, win_pct) in enumerate(performers[-3:], 1):
            print(f"{i}. {pattern}: Exp={exp:.2f}, N={n}, Win%={win_pct:.1f}%")
    
    def _calculate_stats(self, signals: List[Dict], timeout_policy: str) -> Dict:
        """Calculate statistics for a group of signals"""
        
        if not signals:
            return {
                'n': 0, 'tp': 0, 'sl': 0, 'timeout': 0,
                'win_pct': 0, 'expectancy': 0, 'median_time': 0
            }
        
        n = len(signals)
        tp = 0
        sl = 0
        timeout = 0
        achieved_rs = []
        durations = []
        
        for signal in signals:
            outcome = signal['outcome']
            achieved_r = signal['achieved_r'] or 0
            duration = signal['duration_min'] or 0
            
            # Map outcomes to buckets
            if outcome == 'TP':
                tp += 1
            elif outcome == 'TRAIL' or outcome == 'TRAIL_CLOSE':
                if achieved_r > 0:
                    tp += 1
                else:
                    sl += 1
            elif outcome == 'MANUAL' or outcome == 'MANUAL_CLOSE':
                if achieved_r > 0:
                    tp += 1
                else:
                    sl += 1
            elif outcome == 'SL':
                sl += 1
            elif outcome == 'TIMEOUT':
                timeout += 1
                if timeout_policy == 'loss':
                    sl += 1  # Count timeout as loss
            
            if outcome != 'PENDING':
                achieved_rs.append(achieved_r)
                if duration > 0:
                    durations.append(duration)
        
        # Calculate win percentage
        total_counted = tp + sl
        if timeout_policy != 'loss':
            total_counted += timeout
            
        win_pct = (tp / total_counted * 100) if total_counted > 0 else 0
        
        # Calculate expectancy
        expectancy = sum(achieved_rs) / len(achieved_rs) if achieved_rs else 0
        
        # Calculate median duration
        if durations:
            durations.sort()
            mid = len(durations) // 2
            median_time = durations[mid]
        else:
            median_time = 0
            
        return {
            'n': n,
            'tp': tp,
            'sl': sl,
            'timeout': timeout,
            'win_pct': win_pct,
            'expectancy': expectancy,
            'median_time': median_time
        }
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time string to unix timestamp"""
        
        # Handle common aliases
        now = datetime.utcnow()
        
        if time_str == 'now':
            return int(now.timestamp())
        elif time_str == 'today':
            return int(now.replace(hour=0, minute=0, second=0).timestamp())
        elif time_str == 'yesterday':
            yesterday = now - timedelta(days=1)
            return int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
        elif time_str.endswith('h'):
            # e.g., "24h" means 24 hours ago
            hours = int(time_str[:-1])
            past = now - timedelta(hours=hours)
            return int(past.timestamp())
        elif time_str.endswith('d'):
            # e.g., "7d" means 7 days ago
            days = int(time_str[:-1])
            past = now - timedelta(days=days)
            return int(past.timestamp())
        else:
            # Try parsing as datetime string
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                return int(dt.timestamp())
            except:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d")
                    return int(dt.timestamp())
                except:
                    # Assume it's already a unix timestamp
                    return int(time_str)


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(description='WINLOSS Report - Truth Only Performance Tracking')
    
    # Time range arguments
    parser.add_argument('--from', dest='from_time', default='24h',
                       help='Start time (e.g., "24h", "2025-09-01", "yesterday")')
    parser.add_argument('--to', dest='to_time', default='now',
                       help='End time (e.g., "now", "today", "2025-09-05")')
    
    # Report options
    parser.add_argument('--population', default='FIRED',
                       choices=['FIRED', 'ALL'],
                       help='Signal population to analyze')
    parser.add_argument('--timeout_policy', default='loss',
                       choices=['loss', 'exclude'],
                       help='How to count timeouts')
    parser.add_argument('--bins', default='calibrated',
                       choices=['calibrated', 'raw'],
                       help='Confidence type for binning')
    
    # Quick aliases
    parser.add_argument('alias', nargs='?', 
                       choices=['last24h', 'today', 'yesterday', 'last7d'],
                       help='Quick time range aliases')
    
    args = parser.parse_args()
    
    # Handle aliases
    if args.alias:
        if args.alias == 'last24h':
            args.from_time = '24h'
            args.to_time = 'now'
        elif args.alias == 'today':
            args.from_time = 'today'
            args.to_time = 'now'
        elif args.alias == 'yesterday':
            args.from_time = 'yesterday'
            args.to_time = 'today'
        elif args.alias == 'last7d':
            args.from_time = '7d'
            args.to_time = 'now'
    
    # Run report
    report = WinLossReport()
    report.run_report(
        from_time=args.from_time,
        to_time=args.to_time,
        population=args.population,
        timeout_policy=args.timeout_policy,
        bins=args.bins
    )


if __name__ == '__main__':
    main()