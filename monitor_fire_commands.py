#!/usr/bin/env python3
"""
Monitor fire commands being sent through the ZMQ pipeline
"""

import zmq
import json
import threading
import time

def monitor_internal_commands():
    """Monitor port 5554 - commands from FireRouter to fire_router_service"""
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://127.0.0.1:15554")  # Bind to different port for monitoring
    
    print("📡 Monitoring internal commands (would be on port 5554)...")
    print("Note: This is a parallel monitor, not intercepting actual traffic")
    print("-" * 60)

def monitor_ea_commands():
    """Monitor port 5555 - commands from fire_router_service to EA"""  
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 1000)
    
    print("📡 Monitoring EA commands on port 5555...")
    print("-" * 60)
    
    while True:
        try:
            message = socket.recv_json()
            print(f"\n🔥 FIRE COMMAND TO EA:")
            print(f"  Type: {message.get('type')}")
            print(f"  Symbol: {message.get('symbol')}")
            print(f"  Entry: {message.get('entry')}")
            print(f"  SL: {message.get('sl')} pips")
            print(f"  TP: {message.get('tp')} pips")
            print(f"  Lot: {message.get('lot')}")
            print(f"  Signal ID: {message.get('signal_id')}")
            print(f"  Target UUID: {message.get('target_uuid')}")
            print("-" * 60)
        except zmq.Again:
            pass
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 FIRE COMMAND MONITOR")
    print("=" * 60)
    print("\nWaiting for fire commands...")
    print("Send a test fire command from the webapp to see the data flow\n")
    
    # Monitor EA commands
    monitor_ea_commands()