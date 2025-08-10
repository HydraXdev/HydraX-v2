#!/usr/bin/env python3
"""
Post-Mortem Tracking Monitor - BITTEN Signal Outcome Analysis
Monitors and analyzes signal completion rates, outcomes, and system health
"""

import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class PostMortemTrackingMonitor:
    def __init__(self):
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        self.stats = {
            'total_signals': 0,
            'completed_signals': 0,
            'active_signals': 0,
            'sent_to_users': 0,
            'user_executions': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'completion_rate': 0.0,
            'user_delivery_rate': 0.0
        }
        
    def analyze_truth_log(self, hours_back=24):
        """Analyze truth log for signal outcomes and completion rates"""
        if not os.path.exists(self.truth_log_path):
            return None, "Truth log file not found"
            
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        signals = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            signal = json.loads(line.strip())
                            # Parse timestamp
                            if 'generated_at' in signal:
                                gen_time = datetime.fromisoformat(signal['generated_at'].replace('Z', ''))
                                if gen_time > cutoff_time:
                                    signals.append(signal)
                        except json.JSONDecodeError as e:
                            print(f"Error parsing line: {e}")
                            continue
        except Exception as e:
            return None, f"Error reading truth log: {e}"
        
        return signals, None
    
    def calculate_statistics(self, signals):
        """Calculate comprehensive signal statistics"""
        if not signals:
            return
            
        # Reset stats
        stats = defaultdict(int)
        outcomes = Counter()
        symbols = Counter()
        signal_types = Counter()
        sessions = Counter()
        
        for signal in signals:
            stats['total_signals'] += 1
            
            # Track signal outcomes
            if signal.get('completed', False):
                stats['completed_signals'] += 1
                outcome = signal.get('outcome')
                if outcome:
                    outcomes[outcome] += 1
                    if outcome == 'win':
                        stats['wins'] += 1
                    elif outcome == 'loss':
                        stats['losses'] += 1
            else:
                stats['active_signals'] += 1
                
            # Track user delivery
            if signal.get('sent_to_users', False):
                stats['sent_to_users'] += 1
                
            # Track user executions
            if signal.get('execution_count', 0) > 0:
                stats['user_executions'] += 1
                
            # Track distributions
            symbols[signal.get('symbol', 'UNKNOWN')] += 1
            signal_types[signal.get('signal_type', 'UNKNOWN')] += 1
            sessions[signal.get('session', 'UNKNOWN')] += 1
        
        # Calculate rates
        if stats['total_signals'] > 0:
            stats['completion_rate'] = (stats['completed_signals'] / stats['total_signals']) * 100
            stats['user_delivery_rate'] = (stats['sent_to_users'] / stats['total_signals']) * 100
            
        if stats['wins'] + stats['losses'] > 0:
            stats['win_rate'] = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100
            
        self.stats = stats
        return {
            'stats': dict(stats),
            'outcomes': dict(outcomes),
            'symbols': dict(symbols),
            'signal_types': dict(signal_types),
            'sessions': dict(sessions)
        }
    
    def check_post_mortem_health(self, signals):
        """Check if post-mortem tracking is working correctly"""
        issues = []
        
        if not signals:
            issues.append("❌ No signals found in the specified timeframe")
            return issues
            
        # Check for missing critical fields
        required_fields = ['signal_id', 'generated_at', 'symbol', 'direction']
        outcome_fields = ['outcome', 'completed', 'pips_result', 'efficiency_score']
        
        for signal in signals:
            for field in required_fields:
                if field not in signal or signal[field] in [None, '', 'UNKNOWN']:
                    issues.append(f"⚠️ Signal {signal.get('signal_id', 'UNKNOWN')} missing {field}")
                    break
        
        # Check if any signals have been completed
        completed_signals = [s for s in signals if s.get('completed', False)]
        if not completed_signals and len(signals) > 10:
            issues.append("⚠️ No completed signals found - post-mortem tracking may not be working")
        
        # Check if signals are being sent to users
        sent_signals = [s for s in signals if s.get('sent_to_users', False)]
        if not sent_signals:
            issues.append("❌ No signals marked as sent to users - delivery pipeline may be broken")
        
        # Check for execution tracking
        executed_signals = [s for s in signals if s.get('execution_count', 0) > 0]
        if not executed_signals:
            issues.append("⚠️ No user executions recorded - /fire command may not be working")
        
        if not issues:
            issues.append("✅ Post-mortem tracking appears to be working correctly")
            
        return issues
    
    def generate_report(self, hours_back=24):
        """Generate comprehensive post-mortem tracking report"""
        print("=" * 80)
        print("📊 BITTEN POST-MORTEM TRACKING MONITOR")
        print("=" * 80)
        print(f"⏰ Analysis Period: Last {hours_back} hours")
        print(f"📅 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        # Load and analyze data
        signals, error = self.analyze_truth_log(hours_back)
        if error:
            print(f"❌ Error: {error}")
            return
            
        # Calculate statistics
        analysis = self.calculate_statistics(signals)
        if not analysis:
            print("❌ No data to analyze")
            return
            
        stats = analysis['stats']
        
        # Signal Overview
        print("\n📈 SIGNAL OVERVIEW:")
        print(f"   Total Signals: {stats['total_signals']}")
        print(f"   Completed: {stats['completed_signals']} ({stats['completion_rate']:.1f}%)")
        print(f"   Active: {stats['active_signals']}")
        print(f"   Sent to Users: {stats['sent_to_users']} ({stats['user_delivery_rate']:.1f}%)")
        print(f"   User Executions: {stats.get('user_executions', 0)}")
        
        # Performance Metrics
        print("\n🎯 PERFORMANCE METRICS:")
        print(f"   Win Rate: {stats.get('win_rate', 0):.1f}% ({stats.get('wins', 0)} wins, {stats.get('losses', 0)} losses)")
        print(f"   Completion Rate: {stats.get('completion_rate', 0):.1f}%")
        print(f"   User Delivery Rate: {stats.get('user_delivery_rate', 0):.1f}%")
        
        # Distribution Analysis
        print("\n📊 SIGNAL DISTRIBUTION:")
        print("   Symbols:")
        for symbol, count in analysis['symbols'].items():
            percentage = (count / stats['total_signals']) * 100
            print(f"      {symbol}: {count} ({percentage:.1f}%)")
        
        print("   Signal Types:")
        for sig_type, count in analysis['signal_types'].items():
            percentage = (count / stats['total_signals']) * 100
            print(f"      {sig_type}: {count} ({percentage:.1f}%)")
        
        print("   Sessions:")
        for session, count in analysis['sessions'].items():
            percentage = (count / stats['total_signals']) * 100
            print(f"      {session}: {count} ({percentage:.1f}%)")
        
        # Health Check
        print("\n🔍 SYSTEM HEALTH CHECK:")
        health_issues = self.check_post_mortem_health(signals)
        for issue in health_issues:
            print(f"   {issue}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if stats.get('user_delivery_rate', 0) < 50:
            print("   🚨 LOW USER DELIVERY RATE - Check signal relay and bot integration")
        if stats.get('completion_rate', 0) < 10 and stats['total_signals'] > 20:
            print("   ⚠️ LOW COMPLETION RATE - Signals may not be reaching SL/TP")
        if stats.get('user_executions', 0) == 0:
            print("   🔧 NO USER EXECUTIONS - Test /fire command functionality")
        if stats['total_signals'] == 0:
            print("   🔄 NO SIGNALS - Check signal generation engines")
        
        print("\n" + "=" * 80)
        print("📝 TIP: Run with different time periods: python3 post_mortem_tracking_monitor.py --hours 6")
        print("=" * 80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor post-mortem signal tracking')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--watch', action='store_true', help='Continuously monitor (refresh every 60s)')
    
    args = parser.parse_args()
    
    monitor = PostMortemTrackingMonitor()
    
    if args.watch:
        print("🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                monitor.generate_report(args.hours)
                print(f"\n⏳ Refreshing in 60 seconds...")
                time.sleep(60)
                print("\033[2J\033[H")  # Clear screen
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")
    else:
        monitor.generate_report(args.hours)

if __name__ == "__main__":
    main()