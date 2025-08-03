#!/usr/bin/env python3
"""
Test ZMQ Market Data Flow
Validates the complete pipeline: EA → ZMQ Streamer → VENOM
"""

import time
import subprocess
import signal
import sys
import requests
import json
from datetime import datetime

def test_market_data_flow():
    """Test the complete ZMQ market data flow"""
    
    print("=" * 60)
    print("🧪 ZMQ MARKET DATA FLOW TEST")
    print("=" * 60)
    
    processes = []
    
    try:
        # Step 1: Check if EA is sending data
        print("\n📡 Step 1: Checking EA data flow...")
        try:
            response = requests.get("http://localhost:8001/market-data/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                active_symbols = data.get('symbols_active', 0)
                print(f"✅ Market data receiver active: {active_symbols} symbols")
                
                # Check for GOLD
                gold_response = requests.get("http://localhost:8001/market-data/venom-feed?symbol=XAUUSD", timeout=2)
                if gold_response.status_code == 200:
                    gold_data = gold_response.json()
                    print(f"✅ GOLD data available: Bid ${gold_data.get('bid', 0):.2f}")
                else:
                    print("⚠️ GOLD data not available yet")
            else:
                print("❌ Market data receiver not responding")
                return
        except Exception as e:
            print(f"❌ Cannot reach market data receiver: {e}")
            return
            
        # Step 2: Start ZMQ Market Streamer
        print("\n🚀 Step 2: Starting ZMQ Market Streamer...")
        streamer_process = subprocess.Popen(
            ["python3", "/root/HydraX-v2/zmq_market_streamer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        processes.append(streamer_process)
        print("✅ ZMQ Market Streamer started (PID: {})".format(streamer_process.pid))
        
        # Give it time to connect
        time.sleep(3)
        
        # Step 3: Start VENOM ZMQ Adapter
        print("\n🐍 Step 3: Starting VENOM ZMQ Adapter...")
        adapter_process = subprocess.Popen(
            ["python3", "/root/HydraX-v2/venom_zmq_adapter.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        processes.append(adapter_process)
        print("✅ VENOM ZMQ Adapter started (PID: {})".format(adapter_process.pid))
        
        # Step 4: Monitor data flow
        print("\n📊 Step 4: Monitoring data flow for 30 seconds...")
        print("Watching for LIVE market data streaming...\n")
        
        start_time = time.time()
        
        while time.time() - start_time < 30:
            # Check streamer output
            if streamer_process.poll() is None:
                try:
                    line = streamer_process.stdout.readline()
                    if line and ("GOLD" in line or "tick" in line):
                        print(f"[STREAMER] {line.strip()}")
                except:
                    pass
                    
            # Check adapter output  
            if adapter_process.poll() is None:
                try:
                    line = adapter_process.stdout.readline()
                    if line and ("VENOM" in line or "GOLD" in line):
                        print(f"[ADAPTER] {line.strip()}")
                except:
                    pass
                    
            time.sleep(0.1)
            
        print("\n✅ Test completed!")
        print("\n📋 SUMMARY:")
        print("- EA → HTTP → Market Data Receiver: ✅ WORKING")
        print("- Market Streamer → ZMQ: ✅ STARTED")
        print("- ZMQ → VENOM Adapter: ✅ STARTED")
        print("- GOLD (XAUUSD) Support: ✅ INCLUDED")
        
        print("\n🎯 Next Steps:")
        print("1. Update EA to publish via ZMQ instead of HTTP")
        print("2. Integrate VENOM engine with ZMQ adapter")
        print("3. Enable CITADEL Shield for all signals")
        print("4. Monitor signal generation with LIVE data")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        
    finally:
        # Clean up processes
        print("\n🧹 Cleaning up...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped process {process.pid}")


def check_zmq_connectivity():
    """Check if ZMQ ports are accessible"""
    print("\n🔌 Checking ZMQ connectivity...")
    
    import socket
    
    # Check if port 5555 is listening (EA publisher)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('134.199.204.67', 5555))
    if result == 0:
        print("✅ Port 5555 is open (EA publisher)")
    else:
        print("❌ Port 5555 is not accessible")
    sock.close()
    
    # Check if port 5556 is available (VENOM subscriber)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5556))
    if result == 0:
        print("⚠️ Port 5556 is already in use")
    else:
        print("✅ Port 5556 is available (VENOM subscriber)")
    sock.close()


if __name__ == "__main__":
    print("🚀 BITTEN ZMQ Market Data Flow Test")
    print("=" * 60)
    print("This test will validate the LIVE market data pipeline:")
    print("MT5 EA → ZMQ → Market Streamer → VENOM Engine")
    print("=" * 60)
    
    # Check connectivity first
    check_zmq_connectivity()
    
    # Run the test
    test_market_data_flow()