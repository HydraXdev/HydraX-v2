#!/usr/bin/env python3
"""
MARKET SAFETY CHECK - Prevents fake signal generation during live markets
Created: August 8, 2025
Purpose: Ensure only real market data triggers signals
"""

import sys
import os
from datetime import datetime, timezone

def is_market_open():
    """Check if forex market is open"""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()
    hour = now.hour
    
    # Market closed: Friday 21:00 UTC to Sunday 21:00 UTC
    if weekday == 4 and hour >= 21:  # Friday after 21:00
        return False
    elif weekday == 5:  # Saturday
        return False
    elif weekday == 6 and hour < 21:  # Sunday before 21:00
        return False
    
    return True

def check_processes():
    """Check for test signal generators"""
    import subprocess
    
    # Check for Elite Guard processes
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    processes = result.stdout
    
    dangerous_processes = []
    
    # Check for test/simulation processes
    if 'elite_guard' in processes.lower():
        if is_market_open():
            print("✅ Market is OPEN - Elite Guard can run with real data")
        else:
            print("⚠️ Market is CLOSED - Elite Guard should NOT be running!")
            dangerous_processes.append("elite_guard")
    
    if 'test_signal' in processes.lower():
        print("❌ Test signal generator detected - should be stopped!")
        dangerous_processes.append("test_signal_generator")
    
    if 'simulation' in processes.lower() or 'simulate' in processes.lower():
        print("❌ Simulation process detected - should be stopped!")
        dangerous_processes.append("simulation")
    
    return dangerous_processes

def enforce_safety():
    """Enforce market safety rules"""
    print("🔒 MARKET SAFETY CHECK")
    print("=" * 50)
    
    market_open = is_market_open()
    now = datetime.now(timezone.utc)
    
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Day: {now.strftime('%A')}")
    print(f"Market status: {'OPEN ✅' if market_open else 'CLOSED ❌'}")
    print("-" * 50)
    
    if not market_open:
        print("\n⚠️ SAFETY RULES WHEN MARKET CLOSED:")
        print("1. NO Elite Guard signal generation")
        print("2. NO test signal generators")
        print("3. ONLY EA connection testing allowed")
        print("4. ONLY infrastructure testing allowed")
        
        # Kill any Elite Guard processes
        os.system("pkill -f elite_guard_with_citadel 2>/dev/null")
        os.system("pkill -f elite_guard_zmq_relay 2>/dev/null")
        os.system("systemctl stop elite-relay.service 2>/dev/null")
        print("\n✅ Stopped all signal generation processes")
    else:
        print("\n✅ Market is OPEN - Signal generation allowed")
        print("Elite Guard can analyze real market data")
    
    print("\n📋 Service Status:")
    os.system("systemctl is-enabled elite-relay.service 2>/dev/null | xargs -I {} echo 'elite-relay.service: {}'")
    
    print("\n✅ Safety check complete")

if __name__ == "__main__":
    enforce_safety()