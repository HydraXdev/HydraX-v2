#!/usr/bin/env python3
"""
Monitor Elite Guard signals overnight with 66% threshold
"""

import json
import time
import os
from datetime import datetime
import subprocess

def main():
    print("=" * 60)
    print("🌙 OVERNIGHT SIGNAL MONITOR")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print("Threshold: 66% TCS Score")
    print("Monitoring Elite Guard signals...")
    print("-" * 60)
    
    # Track signals
    signals_generated = []
    last_check = 0
    
    while True:
        try:
            # Check for new mission files
            result = subprocess.run(
                "ls -t /root/HydraX-v2/missions/ELITE_GUARD*.json 2>/dev/null | head -10",
                shell=True, capture_output=True, text=True
            )
            
            if result.stdout:
                mission_files = result.stdout.strip().split('\n')
                
                for mission_file in mission_files:
                    if not mission_file:
                        continue
                        
                    # Check if this is a new signal
                    file_mtime = os.path.getmtime(mission_file)
                    
                    if file_mtime > last_check:
                        # Load and display signal
                        with open(mission_file, 'r') as f:
                            signal = json.load(f)
                        
                        signal_id = signal.get('signal_id', 'UNKNOWN')
                        
                        if signal_id not in signals_generated:
                            signals_generated.append(signal_id)
                            
                            print(f"\n🎯 NEW SIGNAL at {datetime.now().strftime('%H:%M:%S')}")
                            print(f"  ID: {signal_id}")
                            print(f"  Symbol: {signal.get('symbol')}")
                            print(f"  Direction: {signal.get('direction')}")
                            print(f"  Confidence: {signal.get('confidence', 0):.1f}%")
                            print(f"  Entry: {signal.get('entry_price')}")
                            print(f"  SL: {signal.get('stop_loss')}")
                            print(f"  TP: {signal.get('take_profit')}")
                            print(f"  Pattern: {signal.get('pattern_type', 'N/A')}")
                            print(f"  Session: {signal.get('session', 'N/A')}")
                            
                            # Log to file for analysis
                            with open("/root/HydraX-v2/overnight_signals.jsonl", "a") as log:
                                log_entry = {
                                    "timestamp": datetime.now().isoformat(),
                                    "signal_id": signal_id,
                                    "symbol": signal.get('symbol'),
                                    "direction": signal.get('direction'),
                                    "confidence": signal.get('confidence'),
                                    "pattern": signal.get('pattern_type'),
                                    "session": signal.get('session'),
                                    "entry": signal.get('entry_price'),
                                    "sl": signal.get('stop_loss'),
                                    "tp": signal.get('take_profit')
                                }
                                log.write(json.dumps(log_entry) + "\n")
            
            # Update last check time
            last_check = time.time()
            
            # Status update every 5 minutes
            if int(time.time()) % 300 == 0:
                print(f"\n📊 Status at {datetime.now().strftime('%H:%M')}")
                print(f"  Total signals: {len(signals_generated)}")
                
                # Check Elite Guard is still running
                result = subprocess.run(
                    "ps aux | grep elite_guard_with_citadel | grep -v grep",
                    shell=True, capture_output=True, text=True
                )
                
                if result.stdout:
                    print("  Elite Guard: ✅ Running")
                else:
                    print("  Elite Guard: ❌ Stopped - restarting...")
                    subprocess.run(
                        "nohup python3 /root/HydraX-v2/elite_guard_with_citadel.py > /root/HydraX-v2/elite_guard.log 2>&1 &",
                        shell=True
                    )
            
            # Sleep for 10 seconds between checks
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(30)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 OVERNIGHT SUMMARY")
    print(f"  Total signals generated: {len(signals_generated)}")
    print(f"  Monitoring ended: {datetime.now().isoformat()}")
    
    if signals_generated:
        print("\n  Signal IDs captured:")
        for sig_id in signals_generated[-10:]:  # Last 10
            print(f"    - {sig_id}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()