#!/usr/bin/env python3
"""
🚨 EMERGENCY BOT KILL SWITCH 🚨
Immediately stops ALL Telegram bots to prevent multiple bot conflicts
"""

import os
import sys
import signal
import subprocess
import time

def emergency_stop_all_bots():
    """Kill all Python processes that might be running Telegram bots"""
    
    print("🚨 EMERGENCY BOT SHUTDOWN INITIATED")
    print("=" * 50)
    
    try:
        # Method 1: Kill by process name
        print("🔫 Killing all Python Telegram processes...")
        subprocess.run(['pkill', '-f', 'python.*telegram'], check=False)
        subprocess.run(['pkill', '-f', 'SIGNALS_'], check=False)
        subprocess.run(['pkill', '-f', 'START_SIGNALS'], check=False)
        subprocess.run(['pkill', '-f', 'telegram.*bot'], check=False)
        
        time.sleep(2)
        
        # Method 2: Kill by bot token pattern
        print("🔫 Killing processes using bot token...")
        subprocess.run(['pkill', '-f', '7854827710'], check=False)
        
        time.sleep(2)
        
        # Method 3: Kill specific files
        bot_files = [
            'SIGNALS_COMPACT.py',
            'START_SIGNALS_NOW.py', 
            'SIGNALS_REALISTIC.py',
            'SIGNALS_LIVE_DATA.py',
            'start_signals_fixed.py',
            'start_bitten_live_signals.py',
            'SIGNALS_CLEAN.py'
        ]
        
        for bot_file in bot_files:
            print(f"🔫 Killing {bot_file}...")
            subprocess.run(['pkill', '-f', bot_file], check=False)
        
        time.sleep(2)
        
        # Method 4: Check what's still running
        print("\n📊 Checking remaining Python processes...")
        try:
            result = subprocess.run(['pgrep', '-f', 'python'], capture_output=True, text=True)
            if result.stdout.strip():
                print(f"⚠️  Still running Python PIDs: {result.stdout.strip()}")
            else:
                print("✅ No Python processes detected")
        except:
            print("❓ Could not check running processes")
            
        print("\n✅ EMERGENCY SHUTDOWN COMPLETE")
        print("🔐 All Telegram bots should now be stopped")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during emergency shutdown: {e}")
        print("🔧 Manual intervention may be required")

if __name__ == "__main__":
    emergency_stop_all_bots()