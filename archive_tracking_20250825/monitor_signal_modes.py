#!/usr/bin/env python3
"""
Monitor signal modes in real-time to see RAPID vs SNIPER classification
"""
import json
import time
import sys

def monitor_signals():
    print("\n🎯 DUAL-MODE SIGNAL MONITOR")
    print("=" * 60)
    print("Watching for new signals... (Ctrl+C to stop)\n")
    
    last_position = 0
    
    try:
        while True:
            with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()
                
                for line in new_lines:
                    if line.strip():
                        try:
                            signal = json.loads(line)
                            signal_id = signal.get('signal_id', '')
                            
                            # Skip old signals
                            if 'signal_mode' not in signal:
                                continue
                                
                            symbol = signal.get('symbol', '')
                            direction = signal.get('direction', '')
                            confidence = signal.get('confidence', 0)
                            tp_pips = signal.get('target_pips', 0)
                            rr_ratio = signal.get('risk_reward', 0)
                            pattern = signal.get('pattern_type', '')
                            mode = signal.get('signal_mode', 'UNKNOWN')
                            
                            # Determine icon
                            if mode == 'SNIPER' or tp_pips >= 30:
                                icon = '🎯 SNIPER'
                                color = '\033[94m'  # Blue
                            else:
                                icon = '⚡ RAPID'
                                color = '\033[93m'  # Yellow
                            
                            # Format output
                            print(f"{color}{icon}\033[0m {symbol} {direction}")
                            print(f"  Pattern: {pattern}")
                            print(f"  Confidence: {confidence}%")
                            print(f"  TP: {tp_pips} pips | R:R: {rr_ratio}:1")
                            print(f"  Mode: {mode}")
                            print("-" * 40)
                            
                        except json.JSONDecodeError:
                            pass
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Signal monitor stopped")
        
if __name__ == "__main__":
    monitor_signals()