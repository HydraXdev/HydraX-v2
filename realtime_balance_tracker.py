#\!/usr/bin/env python3
import zmq
import json
import time
from datetime import datetime

print("🎯 REAL-TIME BALANCE TRACKER")

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5558")

print("✅ Listening for confirmations with EXACT balance data...")

while True:
    try:
        message = socket.recv_string(zmq.NOBLOCK)
        data = json.loads(message)
        
        if data.get('type') == 'confirmation':
            print(f"\n🔥 CONFIRMATION RECEIVED:")
            print(f"⏰ Time: {datetime.now()}")
            print(f"🎫 Ticket: {data.get('ticket', 'N/A')}")
            print(f"📊 Symbol: {data.get('symbol', 'N/A')}")
            print(f"💰 EXACT Balance: ${data.get('balance', 'N/A')}")
            print(f"📈 EXACT Equity: ${data.get('equity', 'N/A')}")
            print(f"💸 Free Margin: ${data.get('free_margin', 'N/A')}")
            print(f"📊 Margin Level: {data.get('margin_level', 'N/A')}%")
            print(f"✅ Status: {data.get('status', 'N/A')}")
            
            # THIS IS THE DATA WE NEED TO PUSH TO USER DISPLAYS
            user_data = {
                'uuid': data.get('user_uuid'),
                'balance': float(data.get('balance', 0)),
                'equity': float(data.get('equity', 0)),
                'free_margin': float(data.get('free_margin', 0)),
                'last_trade': data.get('ticket'),
                'last_update': datetime.now().isoformat()
            }
            
            print(f"📦 USER DATA PACKET: {json.dumps(user_data, indent=2)}")
            print("=" * 60)
            
    except zmq.Again:
        time.sleep(0.1)
    except KeyboardInterrupt:
        break
    except Exception as e:
        if "Invalid argument" not in str(e):
            print(f"Waiting for confirmations...")
        time.sleep(0.5)

socket.close()
context.term()
