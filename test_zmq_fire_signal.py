#!/usr/bin/env python3
"""
Test ZMQ Fire Signal - Send test trade via ZMQ
"""

import zmq
import json
import time
import sys
from datetime import datetime

def send_test_signal():
    """Send a test trade signal via ZMQ"""
    
    context = zmq.Context()
    
    try:
        # Connect to command socket as client
        command_socket = context.socket(zmq.PUSH)
        command_socket.connect("tcp://localhost:5555")
        
        # Prepare test signal
        test_signal = {
            "type": "signal",
            "signal_id": "ZMQ_TEST_001",
            "symbol": "EURUSD",
            "action": "buy",
            "lot": 0.01,
            "sl": 50,
            "tp": 100,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print("🚀 Sending test ZMQ signal:")
        print(json.dumps(test_signal, indent=2))
        
        # Send signal
        command_socket.send_string(json.dumps(test_signal))
        
        print("\n✅ Signal sent to ZMQ command channel (port 5555)")
        print("⏳ Monitoring for trade result...")
        
        # Monitor feedback channel for result
        feedback_socket = context.socket(zmq.SUB)
        feedback_socket.connect("tcp://localhost:5556")
        feedback_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        feedback_socket.setsockopt(zmq.RCVTIMEO, 30000)  # 30 second timeout
        
        start_time = time.time()
        result_found = False
        
        while time.time() - start_time < 30:
            try:
                message = feedback_socket.recv_string()
                data = json.loads(message)
                
                # Check if this is our trade result
                if data.get('type') == 'trade_result' and data.get('signal_id') == 'ZMQ_TEST_001':
                    print(f"\n🎯 Trade Result Received:")
                    print(json.dumps(data, indent=2))
                    result_found = True
                    break
                elif data.get('type') == 'telemetry':
                    print(f"📊 Telemetry: Balance: ${data['account']['balance']}, Equity: ${data['account']['equity']}")
                    
            except zmq.Again:
                print(".", end="", flush=True)
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
                
        if not result_found:
            print("\n❌ No trade result received within 30 seconds")
            print("Possible reasons:")
            print("- EA may not be processing signals")
            print("- Symbol EURUSD may not be available")
            print("- Account may not have sufficient margin")
            
        command_socket.close()
        feedback_socket.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        context.term()

if __name__ == "__main__":
    send_test_signal()