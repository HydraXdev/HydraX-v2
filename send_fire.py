#!/usr/bin/env python3
import zmq
import json
from datetime import datetime

context = zmq.Context()
command_socket = context.socket(zmq.PUSH)
command_socket.connect('tcp://127.0.0.1:5555')

# Send fire command with proper stops
fire_command = {
    'type': 'fire',
    'target_uuid': 'COMMANDER_DEV_001',
    'symbol': 'EURUSD',
    'entry': 1.0950,
    'sl': 1.0920,  # 30 pips below
    'tp': 1.1010,  # 60 pips above  
    'lot': 0.01
}

command_socket.send_string(json.dumps(fire_command))
print(f'🔥 FIRE SENT: EURUSD BUY 0.01 @ 1.0950, SL: 1.0920, TP: 1.1010')
command_socket.close()
context.term()