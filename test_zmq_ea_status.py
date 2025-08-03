#!/usr/bin/env python3
"""
Test ZMQ EA Status - Check if EA is connected
"""

import zmq
import json
import time
import sys

def test_ea_connection():
    """Test if EA is connected to ZMQ ports"""
    
    print("🔍 Testing ZMQ EA Connection Status...")
    print("="*50)
    
    context = zmq.Context()
    
    # Test 1: Try to connect as a client to see if ports are bound
    print("\n1️⃣ Testing if ZMQ ports are listening...")
    try:
        # Test command port
        test_socket = context.socket(zmq.REQ)
        test_socket.setsockopt(zmq.LINGER, 0)
        test_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        test_socket.connect("tcp://localhost:5555")
        
        # Send a ping
        ping_msg = json.dumps({"type": "ping", "timestamp": time.time()})
        test_socket.send_string(ping_msg)
        
        try:
            reply = test_socket.recv_string()
            print("✅ Command port 5555: Received response")
        except zmq.Again:
            print("⚠️ Command port 5555: No response (server may be PUSH only)")
            
        test_socket.close()
    except Exception as e:
        print(f"❌ Command port 5555 error: {e}")
    
    # Test 2: Check feedback port
    print("\n2️⃣ Monitoring feedback port for EA heartbeats...")
    try:
        # Connect to feedback port as subscriber
        sub_socket = context.socket(zmq.SUB)
        sub_socket.connect("tcp://localhost:5556")
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
        sub_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        
        print("⏳ Waiting 5 seconds for EA heartbeat/telemetry...")
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < 5:
            try:
                message = sub_socket.recv_string()
                data = json.loads(message)
                message_count += 1
                print(f"📡 Received: {data.get('type', 'unknown')} from {data.get('uuid', 'unknown')}")
                
                # If we see telemetry or heartbeat, EA is connected
                if data.get('type') in ['telemetry', 'heartbeat']:
                    print(f"✅ EA CONNECTED! UUID: {data.get('uuid')}")
                    
            except zmq.Again:
                # Timeout, no message
                pass
            except json.JSONDecodeError:
                print(f"⚠️ Received non-JSON message")
            except Exception as e:
                print(f"❌ Error: {e}")
                
        if message_count == 0:
            print("❌ No messages received - EA may not be connected")
        else:
            print(f"\n📊 Total messages received: {message_count}")
            
        sub_socket.close()
        
    except Exception as e:
        print(f"❌ Feedback port 5556 error: {e}")
    
    # Test 3: Check if we can see any connection attempts
    print("\n3️⃣ Checking for connection attempts...")
    import subprocess
    try:
        result = subprocess.run(
            ["netstat", "-an"], 
            capture_output=True, 
            text=True
        )
        
        connections = []
        for line in result.stdout.split('\n'):
            if '5555' in line or '5556' in line:
                if 'ESTABLISHED' in line or 'SYN' in line:
                    connections.append(line.strip())
                    
        if connections:
            print("✅ Active connections found:")
            for conn in connections:
                print(f"   {conn}")
        else:
            print("❌ No active connections to ZMQ ports")
            
    except Exception as e:
        print(f"⚠️ Could not check connections: {e}")
    
    context.term()
    
    print("\n" + "="*50)
    print("🏁 Test Complete")
    
    # Summary
    print("\n📋 SUMMARY:")
    print("- ZMQ Controller: Running on ports 5555/5556")
    print("- EA Connection: Check feedback port messages above")
    print("- If no heartbeats, EA may need to be restarted")
    print("\n💡 TIP: EA v7 should send heartbeats every 30-60 seconds")

if __name__ == "__main__":
    test_ea_connection()