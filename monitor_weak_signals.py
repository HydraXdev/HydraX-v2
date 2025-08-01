#!/usr/bin/env python3
"""
Monitor weak signals (50-65 score) during benchmarking period
"""
import zmq
import json
import time
from datetime import datetime

print("🔍 Monitoring for weak signals (50-65 score)...")
print("=" * 60)

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5557")  # Elite Guard signal publisher
subscriber.subscribe(b"")

weak_signals = []
strong_signals = []
start_time = time.time()

try:
    while True:
        try:
            # Non-blocking receive with timeout
            if subscriber.poll(1000):  # 1 second timeout
                signal = subscriber.recv_json()
                
                score = signal.get('confidence', 0)
                symbol = signal.get('symbol', 'UNKNOWN')
                direction = signal.get('direction', 'UNKNOWN')
                pattern = signal.get('pattern', 'UNKNOWN')
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if 50 <= score < 65:
                    weak_signals.append(signal)
                    print(f"🟨 [{timestamp}] WEAK SIGNAL: {symbol} {direction} - Score: {score:.1f}% - Pattern: {pattern}")
                    print(f"   CITADEL: {signal.get('citadel_shield', {}).get('classification', 'N/A')}")
                elif score >= 65:
                    strong_signals.append(signal)
                    print(f"🟩 [{timestamp}] STRONG SIGNAL: {symbol} {direction} - Score: {score:.1f}% - Pattern: {pattern}")
                
                # Stats every 10 signals
                total = len(weak_signals) + len(strong_signals)
                if total > 0 and total % 10 == 0:
                    print(f"\n📊 Stats: {len(weak_signals)} weak, {len(strong_signals)} strong")
                    print(f"📈 Weak signal ratio: {len(weak_signals)/total*100:.1f}%\n")
                    
        except zmq.Again:
            # No message, just continue
            pass
        except Exception as e:
            print(f"Error: {e}")
            
        # Print status every minute
        if int(time.time() - start_time) % 60 == 0:
            elapsed = int((time.time() - start_time) / 60)
            print(f"⏱️ Monitoring for {elapsed} minutes... Weak: {len(weak_signals)}, Strong: {len(strong_signals)}")
            
except KeyboardInterrupt:
    print(f"\n\n📊 Final Report:")
    print(f"Total signals: {len(weak_signals) + len(strong_signals)}")
    print(f"Weak signals (50-65): {len(weak_signals)}")
    print(f"Strong signals (65+): {len(strong_signals)}")
    if weak_signals:
        print(f"Weak signal percentage: {len(weak_signals)/(len(weak_signals)+len(strong_signals))*100:.1f}%")
        
    print("\n🔍 Weak signals will be tracked by truth system for outcome analysis")