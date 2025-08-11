#!/usr/bin/env python3
"""
Monitor ZMQ traffic between EA and server
"""

import zmq
import json
import threading
import time
from datetime import datetime

def monitor_market_data():
    """Monitor port 5556 for incoming market data from EA"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 1000)
    
    count = 0
    while count < 5:  # Just show 5 ticks
        try:
            message = socket.recv_string()
            if "TICK" in message:
                count += 1
                print(f"📈 Market Data: {message[:100]}...")
        except zmq.Again:
            pass
    
    socket.close()
    context.term()

def monitor_confirmations():
    """Monitor port 5558 for trade confirmations from EA"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5558")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    
    print("📡 Monitoring port 5558 for confirmations...")
    
    for _ in range(10):  # Monitor for 50 seconds
        try:
            message = socket.recv_string()
            print(f"\n✅ CONFIRMATION: {message}")
            if "ticket" in message.lower() or "order" in message.lower():
                print("🎯 TRADE CONFIRMATION DETECTED!")
                try:
                    # Try to parse as JSON
                    if message.startswith('{'):
                        data = json.loads(message)
                        print(json.dumps(data, indent=2))
                except:
                    pass
        except zmq.Again:
            print(".", end="", flush=True)
    
    socket.close()
    context.term()

def send_test_fire():
    """Send a test fire command directly to port 5555"""
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5555")
    
    test_command = {
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "entry": 1.10000,
        "sl": 1.09900,
        "tp": 1.10200,
        "lot": 0.01,
        "timestamp": datetime.now().isoformat(),
        "signal_id": "TEST_DIRECT_" + str(int(time.time())),
        "validated": True
    }
    
    print(f"\n📤 Sending test fire command directly to EA:")
    print(json.dumps(test_command, indent=2))
    
    socket.send_json(test_command)
    print("✅ Test command sent to port 5555")
    
    socket.close()
    context.term()

def main():
    print("=" * 60)
    print("🔍 EA TRAFFIC MONITOR")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)
    
    # Check connections
    print("\n📡 Active EA Connections:")
    import subprocess
    result = subprocess.run(
        "netstat -an | grep ESTABLISHED | grep -E '555[0-9]' | grep -v 127.0.0.1",
        shell=True, capture_output=True, text=True
    )
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"  {line}")
    
    # Monitor market data briefly
    print("\n📈 Checking Market Data Flow (5 ticks)...")
    market_thread = threading.Thread(target=monitor_market_data)
    market_thread.start()
    market_thread.join(timeout=5)
    
    # Send test fire command
    print("\n🔥 Sending Test Fire Command...")
    send_test_fire()
    
    # Monitor for confirmations
    print("\n⏳ Monitoring for EA Confirmations (50 seconds)...")
    monitor_confirmations()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()