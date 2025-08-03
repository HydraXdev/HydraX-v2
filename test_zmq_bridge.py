#!/usr/bin/env python3
"""
Test ZMQ Bridge System
Verifies the complete ZMQ bridge functionality
"""

import zmq
import json
import time
import threading
from datetime import datetime

class ZMQBridgeTester:
    def __init__(self):
        self.telemetry_received = []
        self.trade_results = []
        self.running = True
        
    def telemetry_listener(self, port=9101):
        """Listen for telemetry in a separate thread"""
        ctx = zmq.Context()
        socket = ctx.socket(zmq.PULL)
        socket.bind(f"tcp://*:{port}")
        socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        
        print(f"📡 Telemetry listener started on port {port}")
        
        while self.running:
            try:
                message = socket.recv()
                data = json.loads(message.decode())
                
                if data.get('type') == 'trade_result':
                    self.trade_results.append(data)
                    print(f"🔥 Trade result received: {data}")
                else:
                    self.telemetry_received.append(data)
                    print(f"📊 Telemetry received: Balance=${data.get('balance', 0):,.2f}")
                    
            except zmq.Again:
                continue
            except Exception as e:
                print(f"❌ Telemetry error: {e}")
        
        socket.close()
        ctx.term()
    
    def send_fire_command(self, action="BUY", symbol="XAUUSD", lot=0.1, tp=40, sl=20):
        """Send a fire command"""
        ctx = zmq.Context()
        socket = ctx.socket(zmq.PUB)
        socket.bind("tcp://*:9001")
        
        time.sleep(1)  # Allow connection
        
        fire_packet = {
            "uuid": "user-001",
            "action": action,
            "symbol": symbol,
            "lot": lot,
            "tp": tp,
            "sl": sl,
            "timestamp": int(time.time())
        }
        
        message = json.dumps(fire_packet)
        socket.send_string(message)
        
        print(f"\n✅ Fire command sent:")
        print(f"   {message}")
        
        time.sleep(0.5)
        socket.close()
        ctx.term()
    
    def run_test(self):
        """Run the complete test sequence"""
        print("🚀 ZMQ Bridge Test Suite")
        print("=" * 60)
        print(f"Time: {datetime.now()}")
        print("=" * 60)
        
        # Start telemetry listener
        telemetry_thread = threading.Thread(target=self.telemetry_listener)
        telemetry_thread.start()
        
        print("\n📋 Test Sequence:")
        print("1. Wait for initial telemetry (5 seconds)")
        print("2. Send BUY command")
        print("3. Wait for trade result")
        print("4. Send SELL command") 
        print("5. Verify results\n")
        
        # Wait for initial telemetry
        print("⏳ Waiting for telemetry...")
        time.sleep(5)
        
        if self.telemetry_received:
            print(f"✅ Received {len(self.telemetry_received)} telemetry messages")
            latest = self.telemetry_received[-1]
            print(f"   Latest balance: ${latest.get('balance', 0):,.2f}")
            print(f"   Latest equity: ${latest.get('equity', 0):,.2f}")
        else:
            print("⚠️ No telemetry received - EA might not be running")
        
        # Test BUY command
        print("\n🔥 TEST 1: Sending BUY command...")
        self.send_fire_command("BUY", "XAUUSD", 0.1, 40, 20)
        
        # Wait for result
        time.sleep(3)
        
        # Test SELL command
        print("\n🔥 TEST 2: Sending SELL command...")
        self.send_fire_command("SELL", "EURUSD", 0.01, 50, 25)
        
        # Wait for final results
        time.sleep(3)
        
        # Stop telemetry listener
        self.running = False
        telemetry_thread.join()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        
        print(f"\nTelemetry Messages: {len(self.telemetry_received)}")
        if self.telemetry_received:
            latest = self.telemetry_received[-1]
            print(f"  Final Balance: ${latest.get('balance', 0):,.2f}")
            print(f"  Final Equity: ${latest.get('equity', 0):,.2f}")
            print(f"  Open Positions: {latest.get('positions', 0)}")
        
        print(f"\nTrade Results: {len(self.trade_results)}")
        for i, result in enumerate(self.trade_results):
            success = "✅" if result.get('success') else "❌"
            print(f"  Trade {i+1}: {success} {result.get('message', '')} (Ticket: {result.get('ticket', 0)})")
        
        # Overall test result
        print("\n" + "=" * 60)
        if self.telemetry_received and len(self.trade_results) >= 1:
            print("✅ ZMQ BRIDGE TEST: PASSED")
            print("   - Telemetry flow working")
            print("   - Fire commands executed")
            print("   - Bidirectional communication verified")
        else:
            print("❌ ZMQ BRIDGE TEST: FAILED")
            if not self.telemetry_received:
                print("   - No telemetry received")
            if not self.trade_results:
                print("   - No trade results received")
            print("\n⚠️ Make sure:")
            print("   1. EA is compiled and attached to chart")
            print("   2. libzmq.dll is in MT5 Libraries folder")
            print("   3. EA parameters match (ports 9001, 9101)")

def main():
    tester = ZMQBridgeTester()
    tester.run_test()

if __name__ == "__main__":
    main()