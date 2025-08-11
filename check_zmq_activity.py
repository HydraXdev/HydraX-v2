#!/usr/bin/env python3
"""
Check ZMQ activity on all BITTEN ports
"""

import zmq
import json
import time
from datetime import datetime

def monitor_ports():
    """Monitor all ZMQ ports for activity"""
    
    print("=" * 60)
    print("ZMQ PORT MONITOR")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Monitor port 5556 (market data from EA)
    print("\n📊 Monitoring port 5556 (EA → Server market data)...")
    sub_5556 = context.socket(zmq.SUB)
    sub_5556.connect("tcp://localhost:5556")
    sub_5556.setsockopt_string(zmq.SUBSCRIBE, "")
    sub_5556.setsockopt(zmq.RCVTIMEO, 1000)
    
    for i in range(3):
        try:
            msg = sub_5556.recv_string()
            print(f"✅ Port 5556 active! Received: {msg[:100]}...")
            try:
                data = json.loads(msg)
                print(f"   Type: {data.get('type')}, Symbol: {data.get('symbol')}")
            except:
                pass
            break
        except zmq.error.Again:
            print(f"   Attempt {i+1}/3: No data")
    
    # Monitor port 5557 (Elite Guard signals)
    print("\n🎯 Monitoring port 5557 (Elite Guard signals)...")
    sub_5557 = context.socket(zmq.SUB)
    sub_5557.connect("tcp://localhost:5557")
    sub_5557.setsockopt_string(zmq.SUBSCRIBE, "")
    sub_5557.setsockopt(zmq.RCVTIMEO, 1000)
    
    for i in range(3):
        try:
            msg = sub_5557.recv_string()
            print(f"✅ Port 5557 active! Signal detected")
            break
        except zmq.error.Again:
            print(f"   Attempt {i+1}/3: No signals")
    
    # Check if we can receive from port 5560 (relayed market data)
    print("\n📡 Monitoring port 5560 (Relayed market data)...")
    sub_5560 = context.socket(zmq.SUB)
    sub_5560.connect("tcp://localhost:5560")
    sub_5560.setsockopt_string(zmq.SUBSCRIBE, "")
    sub_5560.setsockopt(zmq.RCVTIMEO, 1000)
    
    for i in range(3):
        try:
            msg = sub_5560.recv_string()
            print(f"✅ Port 5560 active! Data flowing")
            try:
                data = json.loads(msg)
                print(f"   Type: {data.get('type')}, UUID: {data.get('user_uuid')}")
                if data.get('user_uuid'):
                    print(f"\n🔑 FOUND EA UUID: {data.get('user_uuid')}")
            except:
                pass
            break
        except zmq.error.Again:
            print(f"   Attempt {i+1}/3: No data")
    
    # Test sending a command with discovered UUID
    print("\n🔥 Testing fire command delivery...")
    
    # Try to get UUID from market data
    print("Listening for market data to find UUID...")
    found_uuid = None
    
    sub_any = context.socket(zmq.SUB)
    sub_any.connect("tcp://localhost:5560")
    sub_any.setsockopt_string(zmq.SUBSCRIBE, "")
    sub_any.setsockopt(zmq.RCVTIMEO, 2000)
    
    for i in range(5):
        try:
            msg = sub_any.recv_string()
            try:
                data = json.loads(msg)
                if data.get('user_uuid'):
                    found_uuid = data.get('user_uuid')
                    print(f"✅ Found UUID from {data.get('type')} message: {found_uuid}")
                    break
            except:
                pass
        except zmq.error.Again:
            pass
    
    if found_uuid:
        print(f"\n🎯 Sending test fire command with UUID: {found_uuid}")
        
        pusher = context.socket(zmq.PUSH)
        pusher.connect("tcp://localhost:5555")
        
        fire_command = {
            "type": "fire",
            "target_uuid": found_uuid,  # Use discovered UUID
            "symbol": "EURUSD",
            "entry": 1.0850,
            "sl": 1.0830,
            "tp": 1.0890,
            "lot": 0.01,
            "timestamp": datetime.utcnow().isoformat(),
            "signal_id": f"TEST_{int(time.time())}"
        }
        
        pusher.send_json(fire_command)
        print("✅ Fire command sent with correct UUID!")
        pusher.close()
    else:
        print("\n⚠️ Could not find EA UUID from market data")
        print("EA might not be sending data or UUID might be in handshake only")
    
    # Cleanup
    sub_5556.close()
    sub_5557.close()
    sub_5560.close()
    sub_any.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Monitor complete")
    print("=" * 60)

if __name__ == "__main__":
    monitor_ports()