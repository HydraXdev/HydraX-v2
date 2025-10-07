#!/usr/bin/env python3
"""
STEP MF-2: Controlled confirmation listener for EA responses
Listens on port 5558 for EA trade confirmations
"""
import zmq
import json
import time
from datetime import datetime

def capture_confirmation(timeout_seconds=60):
    """Capture EA confirmation from port 5558"""
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://*:5558")
    socket.setsockopt(zmq.RCVTIMEO, timeout_seconds * 1000)

    print(f"🎯 CONTROLLED CONFIRMATION LISTENER: Binding port 5558")
    print(f"   Waiting for EA trade confirmation...")
    print(f"   Timeout: {timeout_seconds} seconds")

    confirmations = []

    try:
        while len(confirmations) == 0:
            try:
                # Receive confirmation data
                message = socket.recv().decode('utf-8')
                timestamp = datetime.now().isoformat()

                print(f"📨 RAW CONFIRMATION: {message}")

                # Parse confirmation
                try:
                    conf_data = json.loads(message)
                    conf_data['received_at'] = timestamp
                    confirmations.append(conf_data)
                    print(f"✅ PARSED CONFIRMATION: {json.dumps(conf_data, indent=2)}")
                    break

                except json.JSONDecodeError:
                    # Store raw message
                    confirmations.append({
                        'raw_message': message,
                        'received_at': timestamp,
                        'parsed': False
                    })
                    print(f"📄 RAW CONFIRMATION (unparsable): {message}")
                    break

            except zmq.Again:
                print(f"⏰ TIMEOUT: No confirmations received in {timeout_seconds} seconds")
                break

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")

    finally:
        socket.close()
        context.term()

    return confirmations

if __name__ == "__main__":
    confirmations = capture_confirmation(60)
    if confirmations:
        print(f"\n🎯 SUCCESS: {len(confirmations)} confirmation(s) captured")
        for i, conf in enumerate(confirmations):
            print(f"   [{i+1}] {json.dumps(conf, indent=4)}")
    else:
        print(f"\n❌ FAILED: No confirmations received")