#!/usr/bin/env python3
"""
WINLOSS REPORT - Truth Only
Standardized report for signal performance analysis
PRIMARY SOURCE: comprehensive_tracking.jsonl (REAL tracked outcomes)
FALLBACK: Database for historical data
"""

import sys
import argparse
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class WinLossReport:
    """Truth-only win/loss report with standardized output"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db", 
                 tracking_file: str = "/root/HydraX-v2/comprehensive_tracking.jsonl"):
        self.db_path = db_path
        self.tracking_file = tracking_file
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.use_tracking_file = Path(tracking_file).exists()
        
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
        print(f"Confidence Type: {bins_type}")
        print("=" * 80)
        print()
        
        # Check if unified_outcomes exists, create if not
        self._ensure_unified_view()
        
        # Get data
        signals = self._get_signals(from_ts, to_ts, population)
        
        if not signals:
            print("No signals found in specified timeframe")
            return
            
        # Filter out PENDING signals
        analyzed = [s for s in signals if s['outcome'] != 'PENDING']
        pending = [s for s in signals if s['outcome'] == 'PENDING']
        
        print(f"Total Signals: {len(signals)}")
        print(f"Analyzed: {len(analyzed)}")
        print(f"Pending: {len(pending)}")
        print()
        
        if not analyzed:
            print("No completed signals to analyze")
            return
        
        # Table A - Confidence Bins
        print("TABLE A - CONFIDENCE BINS")
        print("-" * 80)
        self._print_confidence_bins(analyzed, bins_type, timeout_policy)
        print()
        
        # Table B - Patterns
        print("TABLE B - PATTERNS")
        print("-" * 80)
        self._print_patterns(analyzed, timeout_policy)
        print()
        
        # Table C - Sessions  
        print("TABLE C - SESSIONS")
        print("-" * 80)
        self._print_sessions(analyzed, timeout_policy)
        print()
        
        # Top/Bottom performers
        print("TOP/BOTTOM PERFORMERS (min N=20)")
        print("-" * 80)
        self._print_top_bottom(analyzed, timeout_policy)
        print()
        
        # Footnotes
        print("FOOTNOTES:")
        print("-" * 80)
        print(f"- Timeout Policy: {timeout_policy.upper()} (timeouts counted as {'losses' if timeout_policy == 'loss' else 'excluded'})")
        print(f"- TRAIL/MANUAL: Counted by achieved_r (positive→TP, negative→SL)")
        print(f"- Excluded as PENDING: {len(pending)} signals")
        print(f"- Report generated: {datetime.now(timezone.utc).isoformat()}")
        
    def _ensure_unified_view(self):
        """Ensure unified_outcomes view exists"""
        try:
            # Check if view exists
            cursor = self.conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='view' AND name='unified_outcomes'
            """)
            if not cursor.fetchone():
                print("[INFO] Unified view empty, building from existing tables...")
                # Create the view
                self.conn.execute("""
                    CREATE VIEW unified_outcomes AS
                    SELECT 
                        sa.signal_id,
                        sa.ts_fire,
                        sa.symbol,
                        sa.side,
                        sa.pattern,
                        sa.session,
                        sa.raw_confidence,
                        sa.calibrated_confidence,
                        sa.risk_reward,
                        COALESCE(
                            sov.outcome,
                            sos.outcome_shadow,
                            CASE 
                                WHEN strftime('%s', 'now') - sa.ts_fire > 7200 THEN 'TIMEOUT'
                                ELSE 'PENDING'
                            END
                        ) as outcome,
                        COALESCE(sov.achieved_r, sos.achieved_r_shadow, 0) as achieved_r,
                        COALESCE(sov.duration_min, sos.duration_min_shadow, 
                                 CAST((strftime('%s', 'now') - sa.ts_fire) / 60 AS INTEGER)) as duration_min
                    FROM signals_all sa
                    LEFT JOIN signal_outcomes_verified sov ON sa.signal_id = sov.signal_id
                    LEFT JOIN signal_outcomes_shadow sos ON sa.signal_id = sos.signal_id
                    WHERE sa.decision = 'FIRED'
                """)
                print("[INFO] Unified view created successfully")
        except sqlite3.OperationalError:
            # View already exists or other error
            pass
    
    def _get_signals(self, from_ts: int, to_ts: int, population: str) -> List[Dict]:
        """Get signals from tracking file or database"""
        
        # Try tracking file first (most recent, real data)
        if self.use_tracking_file:
            signals = self._get_signals_from_tracking(from_ts, to_ts, population)
            if signals:
                print(f"📊 Using REAL tracking data from: {self.tracking_file}")
                return signals
        
        # Fallback to database
        print("📊 Using database for historical data")
        
        query = """
        SELECT 
            signal_id,
            ts_fire,
            symbol,
            side,
            pattern,
            session,
            raw_confidence,
            calibrated_confidence,
            risk_reward,
            outcome,
            achieved_r,
            duration_min
        FROM unified_outcomes
        WHERE ts_fire BETWEEN ? AND ?
        """
        
        if population != "ALL":
            # Already filtered to FIRED in the view
            pass
            
        cursor = self.conn.execute(query, (from_ts, to_ts))
        return [dict(row) for row in cursor]
    
    def _get_signals_from_tracking(self, from_ts: int, to_ts: int, population: str) -> List[Dict]:
        """Get signals from comprehensive_tracking.jsonl file"""
        signals = []
        
        try:
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            signal = json.loads(line)
                            # Filter by timestamp (handle both float and ISO format)
                            ts_value = signal.get('timestamp', 0)
                            if isinstance(ts_value, str):
                                # ISO format string - skip these old entries
                                continue
                            signal_ts = float(ts_value) if ts_value else 0
                            if signal_ts >= from_ts and signal_ts <= to_ts:
                                # Convert to database-like format for compatibility
                                formatted = {
                                    'signal_id': signal.get('signal_id'),
                                    'ts_fire': signal.get('timestamp'),
                                    'symbol': signal.get('pair', signal.get('symbol')),
                                    'side': signal.get('direction'),
                                    'pattern': signal.get('pattern_type'),
                                    'session': signal.get('session'),
                                    'raw_confidence': signal.get('confidence', 0),
                                    'calibrated_confidence': signal.get('confidence', 0),
                                    'risk_reward': signal.get('risk_reward', 1.0),
                                    'outcome': signal.get('outcome', 'PENDING'),
                                    'achieved_r': None,
                                    'duration_min': signal.get('lifespan', 0) / 60 if signal.get('lifespan') else None,
                                    'fired': signal.get('fired', False),
                                    'pips_moved': signal.get('pips_moved', 0)
                                }
                                
                                # Map outcomes to database format
                                if formatted['outcome'] == 'WIN':
                                    formatted['outcome'] = 'TP'
                                elif formatted['outcome'] == 'LOSS':
                                    formatted['outcome'] = 'SL'
                                
                                # Calculate achieved_r if we have the data
                                if signal.get('tp_pips') and signal.get('sl_pips'):
                                    if formatted['outcome'] == 'TP':
                                        formatted['achieved_r'] = signal['tp_pips'] / signal['sl_pips'] if signal['sl_pips'] > 0 else 1.0
                                    elif formatted['outcome'] == 'SL':
                                        formatted['achieved_r'] = -1.0
                                    else:
                                        formatted['achieved_r'] = 0
                                
                                # Filter by population
                                if population == "ALL" or (population == "FIRED" and formatted.get('fired', False)):
                                    signals.append(formatted)
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except FileNotFoundError:
            print(f"Warning: Tracking file not found at {self.tracking_file}")
            return []
            
        return signals
    
    def _calculate_metrics(self, signals: List[Dict], timeout_policy: str) -> Dict:
        """Calculate standard metrics for a group of signals"""
        
        if not signals:
            return {
                'N': 0, 'TP': 0, 'SL': 0, 'TIMEOUT': 0,
                'Win%': 0.0, 'Expectancy': 0.0, 'Median_Time': 0
            }
        
        n = len(signals)
        
        # Count outcomes - map TRAIL/MANUAL based on achieved_r
        tp = sum(1 for s in signals if 
                s['outcome'] == 'TP' or 
                (s['outcome'] in ['TRAIL', 'TRAIL_CLOSE', 'MANUAL', 'MANUAL_CLOSE'] and s['achieved_r'] > 0))
        
        sl = sum(1 for s in signals if 
                s['outcome'] == 'SL' or 
                s['outcome'] == 'STOP_OUT' or
                (s['outcome'] in ['TRAIL', 'TRAIL_CLOSE', 'MANUAL', 'MANUAL_CLOSE'] and s['achieved_r'] <= 0))
        
        timeout = sum(1 for s in signals if s['outcome'] == 'TIMEOUT')
        
        # Calculate win% based on timeout policy
        if timeout_policy == 'loss':
            denominator = tp + sl + timeout
        else:  # exclude
            denominator = tp + sl
            
        win_pct = (tp / denominator * 100) if denominator > 0 else 0.0
        
        # Expectancy (average achieved R)
        r_values = [s['achieved_r'] for s in signals if s['achieved_r'] is not None]
        expectancy = sum(r_values) / len(r_values) if r_values else 0.0
        
        # Median time (simple average since SQLite doesn't have median)
        times = [s['duration_min'] for s in signals if s['duration_min'] is not None]
        median_time = sum(times) / len(times) if times else 0
        
        return {
            'N': n,
            'TP': tp,
            'SL': sl,
            'TIMEOUT': timeout,
            'Win%': win_pct,
            'Expectancy': expectancy,
            'Median_Time': median_time
        }
    
    def _print_confidence_bins(self, signals: List[Dict], bins_type: str, timeout_policy: str):
        """Print confidence bins table"""
        
        # Define bins
        bins = [
            ('70-75', 70, 75),
            ('75-80', 75, 80),
            ('80-85', 80, 85),
            ('85-90', 85, 90),
            ('90-95', 90, 95),
            ('95+', 95, 100)
        ]
        
        # Choose confidence field
        conf_field = 'calibrated_confidence' if bins_type == 'calibrated' else 'raw_confidence'
        
        # Header
        print(f"{'Bin':<10} {'N':>6} {'TP':>6} {'SL':>6} {'TO':>6} {'Win%':>8} {'Exp(R)':>8} {'Med(m)':>8} {'Cov%':>8}")
        print("-" * 80)
        
        total_n = len(signals)
        
        for bin_name, min_conf, max_conf in bins:
            if bin_name == '95+':
                bin_signals = [s for s in signals if s[conf_field] and s[conf_field] >= min_conf]
            else:
                bin_signals = [s for s in signals if s[conf_field] and min_conf <= s[conf_field] < max_conf]
            
            metrics = self._calculate_metrics(bin_signals, timeout_policy)
            coverage = (metrics['N'] / total_n * 100) if total_n > 0 else 0
            
            print(f"{bin_name:<10} {metrics['N']:>6} {metrics['TP']:>6} {metrics['SL']:>6} "
                  f"{metrics['TIMEOUT']:>6} {metrics['Win%']:>7.1f}% {metrics['Expectancy']:>8.2f} "
                  f"{metrics['Median_Time']:>7.0f}m {coverage:>7.1f}%")
    
    def _print_patterns(self, signals: List[Dict], timeout_policy: str):
        """Print patterns table"""
        
        # Group by pattern
        patterns = {}
        for s in signals:
            pattern = s['pattern'] or 'UNKNOWN'
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(s)
        
        # Header
        print(f"{'Pattern':<30} {'N':>6} {'Win%':>8} {'Exp(R)':>8} {'Med(m)':>8}")
        print("-" * 60)
        
        # Sort by N descending
        for pattern, pattern_signals in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
            metrics = self._calculate_metrics(pattern_signals, timeout_policy)
            print(f"{pattern:<30} {metrics['N']:>6} {metrics['Win%']:>7.1f}% "
                  f"{metrics['Expectancy']:>8.2f} {metrics['Median_Time']:>7.0f}m")
    
    def _print_sessions(self, signals: List[Dict], timeout_policy: str):
        """Print sessions table"""
        
        # Group by session
        sessions = {}
        for s in signals:
            session = s['session'] or 'UNKNOWN'
            if session not in sessions:
                sessions[session] = []
            sessions[session].append(s)
        
        # Header
        print(f"{'Session':<15} {'N':>6} {'Win%':>8} {'Exp(R)':>8} {'Med(m)':>8}")
        print("-" * 50)
        
        # Sort by predefined order
        session_order = ['ASIAN', 'LONDON', 'NY', 'OVERLAP', 'UNKNOWN']
        
        for session in session_order:
            if session in sessions:
                metrics = self._calculate_metrics(sessions[session], timeout_policy)
                print(f"{session:<15} {metrics['N']:>6} {metrics['Win%']:>7.1f}% "
                      f"{metrics['Expectancy']:>8.2f} {metrics['Median_Time']:>7.0f}m")
    
    def _print_top_bottom(self, signals: List[Dict], timeout_policy: str):
        """Print top/bottom performers by expectancy"""
        
        # Group by pattern+session combos
        buckets = {}
        for s in signals:
            bucket_key = f"{s['pattern'] or 'UNK'}_{s['session'] or 'UNK'}"
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(s)
        
        # Filter to min N=20 and calculate metrics
        qualified_buckets = []
        for bucket_key, bucket_signals in buckets.items():
            if len(bucket_signals) >= 20:
                metrics = self._calculate_metrics(bucket_signals, timeout_policy)
                qualified_buckets.append((bucket_key, metrics))
        
        if not qualified_buckets:
            print("No buckets with N≥20 signals")
            return
        
        # Sort by expectancy
        qualified_buckets.sort(key=lambda x: x[1]['Expectancy'], reverse=True)
        
        # Top 3
        print("TOP 3 PERFORMERS:")
        for i, (bucket, metrics) in enumerate(qualified_buckets[:3], 1):
            print(f"{i}. {bucket}: N={metrics['N']}, Win%={metrics['Win%']:.1f}%, Exp={metrics['Expectancy']:.2f}")
        
        print()
        
        # Bottom 3
        print("BOTTOM 3 PERFORMERS:")
        for i, (bucket, metrics) in enumerate(qualified_buckets[-3:], 1):
            print(f"{i}. {bucket}: N={metrics['N']}, Win%={metrics['Win%']:.1f}%, Exp={metrics['Expectancy']:.2f}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(description='WINLOSS Report - Truth Only')
    
    # Time aliases
    parser.add_argument('alias', nargs='?', 
                       choices=['last24h', 'today', 'yesterday', 'last7d'],
                       help='Time period alias')
    
    # Custom time range
    parser.add_argument('--from', dest='from_time', type=str,
                       help='Start time (UTC ISO format)')
    parser.add_argument('--to', dest='to_time', type=str,
                       help='End time (UTC ISO format)')
    
    # Options
    parser.add_argument('--population', choices=['FIRED', 'ALL'], 
                       default='FIRED',
                       help='Population to analyze (default: FIRED)')
    parser.add_argument('--timeout_policy', choices=['loss', 'exclude'],
                       default='loss',
                       help='How to count timeouts (default: loss)')
    parser.add_argument('--bins', choices=['calibrated', 'raw'],
                       default='calibrated', 
                       help='Confidence type for binning (default: calibrated)')
    
    args = parser.parse_args()
    
    # Determine time range
    now = datetime.now(timezone.utc)
    
    if args.alias:
        if args.alias == 'last24h':
            from_time = (now - timedelta(hours=24)).isoformat()
            to_time = now.isoformat()
        elif args.alias == 'today':
            from_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            to_time = now.isoformat()
        elif args.alias == 'yesterday':
            yesterday = now - timedelta(days=1)
            from_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            to_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        elif args.alias == 'last7d':
            from_time = (now - timedelta(days=7)).isoformat()
            to_time = now.isoformat()
    elif args.from_time and args.to_time:
        from_time = args.from_time
        to_time = args.to_time
    else:
        # Default to last 24h
        from_time = (now - timedelta(hours=24)).isoformat()
        to_time = now.isoformat()
    
    # Run report
    report = WinLossReport()
    try:
        report.run_report(
            from_time=from_time,
            to_time=to_time,
            population=args.population,
            timeout_policy=args.timeout_policy,
            bins_type=args.bins
        )
    finally:
        report.close()


if __name__ == '__main__':
    main()