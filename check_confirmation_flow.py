#!/usr/bin/env python3
"""
Check where confirmations are going
"""

import zmq
import json
import threading
import time
from datetime import datetime

def monitor_port_5558():
    """Monitor the confirmation port"""
    context = zmq.Context()
    
    # Try subscribing to port 5558
    print("📡 Method 1: SUB socket on port 5558...")
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5558")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    
    try:
        message = socket.recv_string()
        print(f"✅ Received on SUB: {message}")
    except zmq.Again:
        print("  No messages on SUB socket")
    
    socket.close()
    
    # Try PULL pattern (since confirmation_receiver uses PULL)
    print("\n📡 Method 2: Another PULL socket (will conflict)...")
    # Can't bind another PULL since confirmation_receiver already bound
    
    print("\n📡 Method 3: Check what confirmation_receiver is getting...")
    # The confirmation_receiver.py is already bound to 5558 as PULL
    # EA should be PUSHing to it
    
    context.term()

def check_confirmation_receiver_process():
    """Check if confirmation receiver is actually receiving"""
    import subprocess
    
    print("\n🔍 Checking confirmation_receiver.py process...")
    
    # Check if it's running
    result = subprocess.run(
        "ps aux | grep confirmation_receiver",
        shell=True, capture_output=True, text=True
    )
    
    for line in result.stdout.split('\n'):
        if 'python3' in line and 'confirmation_receiver.py' in line:
            pid = line.split()[1]
            print(f"✅ confirmation_receiver.py running (PID: {pid})")
            
            # Check if it has any output
            print(f"\n📋 Checking file descriptors for PID {pid}...")
            fd_result = subprocess.run(
                f"ls -la /proc/{pid}/fd/ 2>/dev/null | grep -E 'log|txt'",
                shell=True, capture_output=True, text=True
            )
            if fd_result.stdout:
                print(f"  Output files: {fd_result.stdout}")
            else:
                print("  No log files found (output to console)")
            
            # Check if we can see its output
            print(f"\n📋 Checking for any logs...")
            log_files = [
                "/root/HydraX-v2/confirmation_receiver.log",
                "/root/HydraX-v2/confirmations.log",
                "/var/log/confirmations.log"
            ]
            
            for log_file in log_files:
                result = subprocess.run(
                    f"ls -la {log_file} 2>/dev/null",
                    shell=True, capture_output=True, text=True
                )
                if result.stdout:
                    print(f"  Found: {log_file}")
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"  Last entries:")
                            for line in lines[-5:]:
                                print(f"    {line.strip()}")
            
            return pid
    
    print("❌ confirmation_receiver.py not running!")
    return None

def test_send_and_receive():
    """Send a test command and check all possible confirmation paths"""
    print("\n🧪 SENDING TEST COMMAND AND MONITORING ALL PATHS...")
    
    # Send test command through proper channel
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5554")
    
    test_command = {
        "source": "BittenCore",
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 0,
        "stop_loss": 1.08500,
        "take_profit": 1.09500,
        "lot_size": 0.01,
        "signal_id": "CONFIRM_TEST_" + str(int(time.time()))
    }
    
    print(f"\n📤 Sending test command: {test_command['signal_id']}")
    socket.send_json(test_command)
    socket.close()
    
    # Wait for processing
    time.sleep(3)
    
    # Check fire_router_service log
    print("\n📋 Checking fire_router_service.log for forwarding...")
    import subprocess
    result = subprocess.run(
        f"tail -20 /root/HydraX-v2/fire_router_service.log | grep {test_command['signal_id']}",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        print(f"✅ Command forwarded to EA: {test_command['signal_id']}")
    else:
        print("❌ Command not found in fire_router_service.log")
    
    context.term()

def check_netstat():
    """Check actual network connections"""
    print("\n🌐 CHECKING NETWORK CONNECTIONS...")
    
    import subprocess
    result = subprocess.run(
        "netstat -an | grep 5558",
        shell=True, capture_output=True, text=True
    )
    
    print("Port 5558 connections:")
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"  {line}")
    
    # Check if EA is connected as PUSH client
    if "185.244.67.11" in result.stdout and "5558" in result.stdout:
        print("\n✅ EA is connected to port 5558 from ForexVPS")
        print("   EA should be PUSHing confirmations here")
    else:
        print("\n⚠️ EA connection to 5558 not clear")

def main():
    print("=" * 60)
    print("🔍 CONFIRMATION FLOW INVESTIGATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)
    
    # Check confirmation receiver
    pid = check_confirmation_receiver_process()
    
    # Check network
    check_netstat()
    
    # Monitor port
    monitor_port_5558()
    
    # Send test
    test_send_and_receive()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS:")
    print("-" * 60)
    print("EXPECTED FLOW:")
    print("  1. EA executes trade")
    print("  2. EA sends confirmation via PUSH to port 5558")
    print("  3. confirmation_receiver.py (PULL) receives it")
    print("  4. confirmation_receiver.py logs/processes it")
    
    print("\nWHAT TO CHECK:")
    print("  1. Is confirmation_receiver.py actually logging output?")
    print("  2. Check MT5 terminal - does it show 'Confirmation sent'?")
    print("  3. The confirmation might be received but not logged visibly")
    
    print("\nNEXT STEP:")
    print("  Kill and restart confirmation_receiver.py with visible output")
    print("=" * 60)

if __name__ == "__main__":
    main()