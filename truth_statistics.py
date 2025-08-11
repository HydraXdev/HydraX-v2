#!/usr/bin/env python3
"""
TRUTH STATISTICS ANALYZER
Provides comprehensive statistics on ALL signals - fired and unfired
Shows true opportunity win rate and optimization insights
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

class TruthStatistics:
    def __init__(self):
        self.truth_log = "/root/HydraX-v2/truth_log.jsonl"
        
    def analyze(self):
        """Analyze all signals and provide comprehensive statistics"""
        signals = self.load_all_signals()
        
        # Separate by status
        all_signals = [s for s in signals if s.get('signal_id') and 'ELITE_GUARD' in s.get('signal_id', '')]
        completed = [s for s in all_signals if s.get('completed') == True]
        pending = [s for s in all_signals if s.get('status') == 'pending' and not s.get('completed')]
        executed = [s for s in signals if s.get('action') == 'trade_executed']
        
        # Outcomes
        wins = [s for s in completed if s.get('outcome') == 'win']
        losses = [s for s in completed if s.get('outcome') == 'loss']
        timeouts = [s for s in completed if s.get('outcome') == 'timeout']
        
        # By symbol
        by_symbol = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'timeouts': 0})
        for signal in all_signals:
            symbol = signal.get('symbol', 'UNKNOWN')
            by_symbol[symbol]['total'] += 1
            
        for signal in completed:
            symbol = signal.get('symbol', 'UNKNOWN')
            outcome = signal.get('outcome')
            if outcome == 'win':
                by_symbol[symbol]['wins'] += 1
            elif outcome == 'loss':
                by_symbol[symbol]['losses'] += 1
            elif outcome == 'timeout':
                by_symbol[symbol]['timeouts'] += 1
                
        # By pattern
        by_pattern = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0})
        for signal in all_signals:
            pattern = signal.get('pattern_type', 'UNKNOWN')
            by_pattern[pattern]['total'] += 1
            
        for signal in completed:
            pattern = signal.get('pattern_type', 'UNKNOWN')
            outcome = signal.get('outcome')
            if outcome == 'win':
                by_pattern[pattern]['wins'] += 1
            elif outcome == 'loss':
                by_pattern[pattern]['losses'] += 1
                
        # Calculate pip totals
        total_pips = sum(s.get('pips_result', 0) for s in completed if s.get('pips_result'))
        winning_pips = sum(s.get('pips_result', 0) for s in wins if s.get('pips_result'))
        losing_pips = sum(s.get('pips_result', 0) for s in losses if s.get('pips_result'))
        
        # Print comprehensive report
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE SIGNAL TRUTH STATISTICS")
        print("="*60)
        
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Signals Generated: {len(all_signals)}")
        print(f"   Signals Completed: {len(completed)}")
        print(f"   Signals Pending: {len(pending)}")
        print(f"   Signals Executed: {len(executed)}")
        
        if completed:
            win_rate = (len(wins) / len(completed)) * 100
            print(f"\n🎯 OPPORTUNITY WIN RATE: {win_rate:.1f}%")
            print(f"   Wins: {len(wins)}")
            print(f"   Losses: {len(losses)}")
            print(f"   Timeouts: {len(timeouts)}")
        else:
            print(f"\n⏳ No completed signals yet for win rate calculation")
            
        print(f"\n💰 PIP PERFORMANCE:")
        print(f"   Total Pips: {total_pips:+.1f}")
        print(f"   Winning Pips: {winning_pips:+.1f}")
        print(f"   Losing Pips: {losing_pips:+.1f}")
        
        print(f"\n📊 BY SYMBOL PERFORMANCE:")
        for symbol, stats in sorted(by_symbol.items()):
            if stats['total'] > 0:
                symbol_wr = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0
                print(f"   {symbol}: {stats['total']} signals, {stats['wins']}W/{stats['losses']}L/{stats['timeouts']}T = {symbol_wr:.1f}% WR")
                
        print(f"\n🎯 BY PATTERN PERFORMANCE:")
        for pattern, stats in sorted(by_pattern.items()):
            if stats['total'] > 0:
                pattern_wr = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0
                print(f"   {pattern}: {stats['total']} signals, {stats['wins']}W/{stats['losses']}L = {pattern_wr:.1f}% WR")
                
        # Optimization insights
        print(f"\n💡 OPTIMIZATION INSIGHTS:")
        
        # Best performing symbol
        if by_symbol:
            best_symbol = max(by_symbol.items(), key=lambda x: x[1]['wins'] if x[1]['total'] > 0 else 0)
            print(f"   Best Symbol: {best_symbol[0]} ({best_symbol[1]['wins']} wins)")
        
        # Best performing pattern
        if by_pattern:
            best_pattern = max(by_pattern.items(), key=lambda x: x[1]['wins'] if x[1]['total'] > 0 else 0)
            print(f"   Best Pattern: {best_pattern[0]} ({best_pattern[1]['wins']} wins)")
        
        # Execution rate
        if all_signals:
            exec_rate = (len(executed) / len(all_signals)) * 100
            print(f"   Execution Rate: {exec_rate:.1f}% of signals fired")
            
        # What-if analysis
        print(f"\n🤔 WHAT-IF ANALYSIS:")
        if completed:
            theoretical_profit = total_pips * 10  # $10 per pip at 0.01 lots
            print(f"   If all signals fired: ${theoretical_profit:+.2f} theoretical")
            print(f"   Opportunity cost of unfired signals: {len(all_signals) - len(executed)} signals")
            
        print("\n" + "="*60)
        
    def load_all_signals(self) -> List[Dict]:
        """Load all entries from truth log"""
        entries = []
        try:
            with open(self.truth_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"❌ Truth log not found: {self.truth_log}")
        return entries

if __name__ == "__main__":
    analyzer = TruthStatistics()
    analyzer.analyze()