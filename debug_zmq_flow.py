#!/usr/bin/env python3
"""
Debug the ZMQ message flow to understand why EA isn't receiving commands
"""

import zmq
import json
import time
from datetime import datetime

def test_push_pull_pattern():
    """Test if EA is receiving on PULL pattern"""
    print("=" * 60)
    print("🔍 ZMQ PATTERN DEBUG")
    print("=" * 60)
    
    # The fire_router_service binds PUSH on port 5555
    # EA should connect as PULL client
    
    print("\n1️⃣ CURRENT SETUP:")
    print("  fire_router_service: PUSH socket, BINDS port 5555")
    print("  EA v2.03: PULL socket, CONNECTS to port 5555")
    print("  Pattern: PUSH (server) → PULL (EA)")
    
    # Test sending through the bound socket
    context = zmq.Context()
    
    # Try connecting as PUSH client (what we've been doing)
    print("\n2️⃣ TEST 1: Connect as PUSH client (current approach)")
    socket1 = context.socket(zmq.PUSH)
    socket1.connect("tcp://localhost:5555")
    
    test_msg = {
        "type": "test",
        "message": "Testing PUSH client to bound PUSH server",
        "timestamp": datetime.now().isoformat()
    }
    
    socket1.send_json(test_msg)
    print("  Sent test message as PUSH client")
    print("  Result: Message goes to fire_router_service, not EA!")
    socket1.close()
    
    # The problem: We have TWO PUSH sockets!
    # - fire_router_service BINDS as PUSH on 5555
    # - We're CONNECTING as PUSH to 5555
    # - EA CONNECTS as PULL to 5555
    
    print("\n3️⃣ THE PROBLEM:")
    print("  ❌ We're sending PUSH → PUSH (fire_router_service)")
    print("  ❌ EA is PULL client expecting from PUSH server")
    print("  ❌ Our messages go to fire_router_service, not EA!")
    
    print("\n4️⃣ CHECKING ACTUAL FLOW:")
    
    # Check what fire_router_service is doing
    print("\n  Fire Router Service (port 5555):")
    print("    - Binds PUSH socket on *:5555")
    print("    - EA connects as PULL client")
    print("    - Should forward commands to EA")
    
    print("\n  Fire Router (port 5554):")
    print("    - Internal communication")
    print("    - FireRouter → fire_router_service")
    
    # Monitor what's actually happening
    print("\n5️⃣ MONITORING ACTUAL MESSAGE FLOW:")
    
    # Send through the correct path
    print("\n  Sending via FireRouter → fire_router_service → EA...")
    
    # Connect to internal port 5554 (where fire_router_service listens)
    internal_socket = context.socket(zmq.PUSH)
    internal_socket.connect("tcp://localhost:5554")
    
    fire_command = {
        "source": "BittenCore",  # Required for validation
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 0,
        "stop_loss": 1.08500,
        "take_profit": 1.09500,
        "lot_size": 0.01,
        "signal_id": "DEBUG_TEST_" + str(int(time.time()))
    }
    
    print(f"\n  Sending to port 5554 (internal):")
    print(f"    {json.dumps(fire_command, indent=4)}")
    
    internal_socket.send_json(fire_command)
    print("\n  ✅ Sent to fire_router_service via port 5554")
    print("  📤 fire_router_service should forward to EA on port 5555")
    
    internal_socket.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS:")
    print("-" * 60)
    print("✅ CORRECT FLOW:")
    print("  1. WebApp → FireRouter (HTTP/API)")
    print("  2. FireRouter → port 5554 (PUSH)")
    print("  3. fire_router_service receives on 5554")
    print("  4. fire_router_service sends on 5555 (PUSH)")
    print("  5. EA receives on 5555 (PULL)")
    
    print("\n❌ WHAT WAS WRONG:")
    print("  We were sending directly to 5555")
    print("  This bypassed fire_router_service validation")
    print("  EA only accepts from fire_router_service")
    
    print("\n🔧 CHECK EA TERMINAL NOW:")
    print("  You should see the DEBUG_TEST command")
    print("  If not, check EA's target_uuid setting")
    print("=" * 60)

if __name__ == "__main__":
    test_push_pull_pattern()