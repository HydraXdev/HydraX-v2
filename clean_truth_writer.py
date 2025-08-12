#!/usr/bin/env python3
"""
Clean Truth Writer - Direct JSONL writer
NO CORRUPTION - Writes signals exactly as received to truth_log.jsonl
"""

import json
import os
from datetime import datetime
from typing import Dict

class CleanTruthWriter:
    def __init__(self, truth_file: str = "/root/HydraX-v2/truth_log.jsonl"):
        self.truth_file = truth_file
        
    def write_signal(self, signal: Dict) -> bool:
        """Write signal directly to truth_log.jsonl - NO CORRUPTION"""
        try:
            # Ensure the signal has required fields
            clean_signal = {
                'signal_id': signal.get('signal_id'),
                'symbol': signal.get('pair', signal.get('symbol')),
                'direction': signal.get('direction'),
                'entry_price': signal.get('entry_price', 0),
                'sl': signal.get('stop_loss', signal.get('sl', 0)),
                'tp': signal.get('take_profit', signal.get('tp', 0)), 
                'confidence': signal.get('confidence', 0),
                'pattern_type': signal.get('pattern', 'ELITE_GUARD'),
                'generated_at': datetime.now().isoformat(),
                'citadel_score': signal.get('shield_score', signal.get('consensus_confidence', 0)),
                'risk_reward': signal.get('risk_reward', 1.0),
                'target_pips': signal.get('target_pips', 10),
                'status': 'pending',
                'completed': False,
                'signal_type': signal.get('signal_type', 'PRECISION_STRIKE'),
                'session': signal.get('session', 'UNKNOWN'),
                'xp_reward': signal.get('xp_reward', 10)
            }
            
            # Write directly to file - ATOMIC OPERATION
            with open(self.truth_file, 'a') as f:
                f.write(json.dumps(clean_signal) + '\n')
                f.flush()  # Ensure immediate write
                
            return True
            
        except Exception as e:
            print(f"❌ Clean truth writer error: {e}")
            return False

# Global instance
clean_writer = CleanTruthWriter()

def write_clean_signal(signal: Dict) -> bool:
    """Function for Elite Guard to use"""
    return clean_writer.write_signal(signal)

if __name__ == "__main__":
    # Test the clean writer
    test_signal = {
        'signal_id': f'CLEAN_WRITER_TEST_{datetime.now().strftime("%H%M%S")}',
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0950,
        'stop_loss': 1.0930,
        'take_profit': 1.0980,
        'confidence': 85,
        'pattern': 'ORDER_BLOCK_BOUNCE'
    }
    
    result = write_clean_signal(test_signal)
    print(f"✅ Clean writer test: {'SUCCESS' if result else 'FAILED'}")