#!/usr/bin/env python3
"""
SIMPLE TRUTH TRACKER - NO CORRUPTION
Just reads truth_log.jsonl and provides statistics
NEVER modifies or corrupts signals - READ ONLY!
"""

import json
import time
from datetime import datetime
from typing import Dict, List

class SimpleTruthTracker:
    def __init__(self):
        self.truth_file = "/root/HydraX-v2/truth_log.jsonl"
        print("🔍 Simple Truth Tracker started - READ ONLY mode")
        
    def read_signals(self) -> List[Dict]:
        """Read all signals from truth log - NO MODIFICATIONS"""
        signals = []
        try:
            with open(self.truth_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line != '[]':
                        try:
                            signal = json.loads(line)
                            signals.append(signal)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            print(f"⚠️ Truth log not found: {self.truth_file}")
        return signals
        
    def get_statistics(self) -> Dict:
        """Calculate statistics from existing signals"""
        signals = self.read_signals()
        
        # Filter out corrupted signals (entry_price = 0)
        clean_signals = [s for s in signals if s.get('entry_price', 0) > 0]
        completed_signals = [s for s in clean_signals if s.get('completed', False)]
        
        wins = [s for s in completed_signals if s.get('outcome') == 'win']
        losses = [s for s in completed_signals if s.get('outcome') == 'loss']
        
        total_pips = sum(s.get('pips', 0) for s in completed_signals)
        
        stats = {
            'total_signals': len(signals),
            'clean_signals': len(clean_signals),
            'corrupted_signals': len(signals) - len(clean_signals),
            'completed_signals': len(completed_signals),
            'active_signals': len(clean_signals) - len(completed_signals),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(completed_signals) * 100) if completed_signals else 0,
            'total_pips': total_pips,
            'avg_pips_per_trade': (total_pips / len(completed_signals)) if completed_signals else 0
        }
        
        return stats
    
    def log_statistics(self):
        """Print clean statistics"""
        stats = self.get_statistics()
        
        print(f"\n📊 Simple Truth Tracker Statistics:")
        print(f"   Total Signals: {stats['total_signals']}")
        print(f"   Clean Signals: {stats['clean_signals']}")
        print(f"   Corrupted (ignored): {stats['corrupted_signals']}")
        print(f"   Active: {stats['active_signals']}")  
        print(f"   Completed: {stats['completed_signals']}")
        print(f"   Wins: {stats['wins']}")
        print(f"   Losses: {stats['losses']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        print(f"   Total Pips: {stats['total_pips']:+.1f}")
        print(f"   Avg Pips/Trade: {stats['avg_pips_per_trade']:+.1f}")
        
    def run(self):
        """Run tracker - logs stats every 60 seconds"""
        print("🔍 Simple Truth Tracker running - NO CORRUPTION POSSIBLE")
        while True:
            try:
                self.log_statistics()
                time.sleep(60)  # Update every minute
            except KeyboardInterrupt:
                print("\n👋 Simple Truth Tracker stopped")
                break
            except Exception as e:
                print(f"⚠️ Error in tracker: {e}")
                time.sleep(5)

if __name__ == "__main__":
    tracker = SimpleTruthTracker()
    tracker.run()