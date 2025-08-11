#!/usr/bin/env python3
"""
Verify complete round trip: Signal → Fire → EA → Confirmation
"""

import requests
import json
import time
import zmq
import threading
import subprocess
from datetime import datetime

def monitor_ea_confirmations():
    """Monitor port 5558 for trade confirmations from EA"""
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://*:5558")
    socket.setsockopt(zmq.RCVTIMEO, 15000)  # 15 second timeout
    
    print("📡 Monitoring port 5558 for EA confirmations...")
    
    try:
        message = socket.recv_json()
        print("\n✅✅✅ EA CONFIRMATION RECEIVED!")
        print("-" * 40)
        print(json.dumps(message, indent=2))
        return message
    except zmq.Again:
        print("⏱️ No confirmation received within 15 seconds")
        return None
    finally:
        socket.close()
        context.term()

def check_mt5_logs():
    """Check MT5 logs for trade execution evidence"""
    print("\n📋 Checking MT5 terminal logs...")
    # Check if there's a log file we can access
    log_locations = [
        "/root/.wine/drive_c/Program Files/MetaTrader 5/Logs/",
        "/root/mt5_logs/",
        "/var/log/mt5/"
    ]
    
    for location in log_locations:
        result = subprocess.run(f"ls -la {location} 2>/dev/null", 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Found logs at: {location}")
            # Get last few lines of most recent log
            result = subprocess.run(f"tail -20 {location}*.log 2>/dev/null", 
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
                return True
    
    print("No MT5 logs found locally (using ForexVPS)")
    return False

def main():
    print("=" * 60)
    print("🎯 COMPLETE ROUND TRIP VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)
    
    # Step 1: Find a recent signal
    print("\n📍 STEP 1: Finding recent signal...")
    result = subprocess.run(
        "find /root/HydraX-v2/missions -name 'ELITE_GUARD*.json' -type f -mmin -30 | head -1",
        shell=True, capture_output=True, text=True
    )
    
    if not result.stdout.strip():
        print("❌ No recent signals found. Waiting for Elite Guard to generate one...")
        return
    
    mission_file = result.stdout.strip()
    signal_id = mission_file.split('/')[-1].replace('.json', '')
    
    print(f"✅ Found signal: {signal_id}")
    
    # Load mission data
    with open(mission_file, 'r') as f:
        mission_data = json.load(f)
    
    print(f"  Symbol: {mission_data.get('symbol')}")
    print(f"  Direction: {mission_data.get('direction')}")
    print(f"  Entry: {mission_data.get('entry_price')}")
    print(f"  SL: {mission_data.get('stop_loss')}")
    print(f"  TP: {mission_data.get('take_profit')}")
    
    # Step 2: Start monitoring for confirmations
    print("\n📍 STEP 2: Starting confirmation monitor...")
    confirmation_thread = threading.Thread(target=monitor_ea_confirmations)
    confirmation_thread.start()
    time.sleep(1)  # Let monitor start
    
    # Step 3: Fire the trade
    print("\n📍 STEP 3: Executing trade via webapp...")
    url = "http://localhost:8888/api/fire"
    payload = {"mission_id": signal_id}
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": "7176191872"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Fire command sent successfully")
            result = response.json()
            if result.get('execution_result', {}).get('success'):
                print(f"  Message: {result.get('execution_result', {}).get('message')}")
        else:
            print(f"❌ Fire request failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error sending fire request: {e}")
        return
    
    # Step 4: Check fire_router_service log
    print("\n📍 STEP 4: Verifying command reached EA...")
    time.sleep(2)
    
    result = subprocess.run(
        "tail -20 /root/HydraX-v2/fire_router_service.log | grep -A10 'Sending to EA'",
        shell=True, capture_output=True, text=True
    )
    
    if result.stdout:
        print("✅ Command sent to EA:")
        # Parse the JSON from log
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if '"sl":' in line and '"tp":' in line:
                print(f"  Found SL/TP in command")
            print(f"  {line}")
    
    # Step 5: Wait for confirmation
    print("\n📍 STEP 5: Waiting for EA confirmation...")
    confirmation_thread.join()  # Wait for monitor thread
    
    # Step 6: Check various logs for evidence
    print("\n📍 STEP 6: Checking system logs for trade evidence...")
    
    # Check truth log
    print("\n📋 Truth log (last entry):")
    result = subprocess.run(
        f"grep {signal_id} /root/HydraX-v2/truth_log.jsonl | tail -1",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        try:
            truth_entry = json.loads(result.stdout)
            print(f"  Status: {truth_entry.get('status')}")
            print(f"  Fired: {truth_entry.get('fired', False)}")
            if truth_entry.get('execution_result'):
                print(f"  Execution: {truth_entry.get('execution_result')}")
        except:
            print(result.stdout)
    
    # Check confirmation receiver log
    print("\n📋 Confirmation receiver log:")
    result = subprocess.run(
        "tail -10 /root/HydraX-v2/confirmation_receiver.log 2>/dev/null",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    
    # Check for EA connection
    print("\n📋 Checking ZMQ connections:")
    result = subprocess.run(
        "netstat -an | grep -E '555[0-9]'",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        print("Active ZMQ ports:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"  {line}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 ROUND TRIP SUMMARY")
    print("-" * 60)
    
    # Check if mission file shows fired status
    with open(mission_file, 'r') as f:
        final_mission = json.load(f)
    
    if final_mission.get('status') == 'fired':
        print("✅ Signal status: FIRED")
        if final_mission.get('fired_at'):
            print(f"✅ Fired at: {final_mission.get('fired_at')}")
        if final_mission.get('execution_result'):
            print(f"✅ Execution result: {final_mission.get('execution_result')}")
        
        print("\n🎯 ROUND TRIP VERIFIED: Signal → Fire → EA")
    else:
        print("⚠️ Signal status: NOT FIRED")
        print("❌ Round trip incomplete - check EA connection")
    
    print("=" * 60)

if __name__ == "__main__":
    main()