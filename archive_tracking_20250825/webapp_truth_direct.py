#!/usr/bin/env python3
"""
WebApp Direct Truth Connection
Bypasses corrupt Black Box, reads truth_log.jsonl directly
NO CORRUPTION - CLEAN DATA ONLY
"""

import json
from datetime import datetime
from typing import Dict, List

class WebAppTruthDirect:
    def __init__(self):
        self.truth_file = "/root/HydraX-v2/truth_log.jsonl"
        
    def get_clean_signals(self) -> List[Dict]:
        """Get signals from truth log, filter out corrupt ones"""
        signals = []
        try:
            with open(self.truth_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line != '[]':
                        try:
                            signal = json.loads(line)
                            # ONLY include signals with real prices (not corrupted)
                            if signal.get('entry_price', 0) > 0:
                                signals.append(signal)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return signals
        
    def get_active_signals(self) -> List[Dict]:
        """Get active (not completed) signals"""
        signals = self.get_clean_signals()
        return [s for s in signals if not s.get('completed', False)]
        
    def get_completed_signals(self) -> List[Dict]:
        """Get completed signals"""
        signals = self.get_clean_signals()
        return [s for s in signals if s.get('completed', False)]
        
    def get_signal_by_id(self, signal_id: str) -> Dict:
        """Get specific signal by ID"""
        signals = self.get_clean_signals()
        for signal in signals:
            if signal.get('signal_id') == signal_id:
                return signal
        return {}
        
    def get_stats(self) -> Dict:
        """Get clean statistics"""
        signals = self.get_clean_signals()
        completed = self.get_completed_signals()
        
        wins = [s for s in completed if s.get('outcome') == 'win']
        losses = [s for s in completed if s.get('outcome') == 'loss']
        total_pips = sum(s.get('pips', 0) for s in completed)
        
        return {
            'total_signals': len(signals),
            'active_signals': len(signals) - len(completed),
            'completed_signals': len(completed),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(completed) * 100) if completed else 0,
            'total_pips': total_pips,
            'avg_pips_per_trade': (total_pips / len(completed)) if completed else 0
        }

# Global instance for webapp to use
webapp_truth = WebAppTruthDirect()

def get_active_signals():
    """Function for webapp compatibility"""
    return webapp_truth.get_active_signals()
    
def get_signal_by_id(signal_id):
    """Function for webapp compatibility"""
    return webapp_truth.get_signal_by_id(signal_id)
    
def get_latest_signal():
    """Function for webapp compatibility"""
    signals = webapp_truth.get_active_signals()
    return signals[-1] if signals else {}

if __name__ == "__main__":
    # Test the direct connection
    direct = WebAppTruthDirect()
    print("🔍 WebApp Direct Truth Connection Test:")
    print(f"Active signals: {len(direct.get_active_signals())}")
    print(f"Completed signals: {len(direct.get_completed_signals())}")
    print("Stats:", direct.get_stats())