#!/usr/bin/env python3
"""
APEX Control - Simple management script
"""

import os
import sys
import json
import psutil
import subprocess
from pathlib import Path

def show_status():
    """Show current APEX status"""
    print("\n📊 APEX Status")
    print("=" * 40)
    
    # Check if running
    pid_file = Path('.apex_engine.pid')
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            process = psutil.Process(pid)
            print(f"✅ Running (PID: {pid})")
            print(f"   CPU: {process.cpu_percent(interval=1)}%")
            print(f"   Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        except:
            print("❌ Not running (stale PID file)")
    else:
        print("❌ Not running")
    
    # Show config
    config = json.load(open('apex_config.json'))
    print(f"\n⚙️ Current Settings:")
    print(f"   Signals/hour target: {config['signal_generation']['signals_per_hour_target']}")
    print(f"   TCS threshold: {config['signal_generation']['min_tcs_threshold']}%")
    print(f"   Scan interval: {config['signal_generation']['scan_interval_seconds']}s")
    print(f"   Trading pairs: {len(config['trading_pairs']['pairs'])}")

def start_apex():
    """Start APEX engine"""
    print("\n🚀 Starting APEX...")
    subprocess.Popen(['python3', 'apex_v5_lean.py'], 
                     stdout=open('apex_lean.log', 'a'),
                     stderr=subprocess.STDOUT)
    print("✅ Started! Check apex_lean.log for output")

def stop_apex():
    """Stop APEX engine"""
    print("\n🛑 Stopping APEX...")
    pid_file = Path('.apex_engine.pid')
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            os.kill(pid, 15)  # SIGTERM
            print("✅ Stopped")
        except:
            print("❌ Failed to stop")
    else:
        print("❌ Not running")

def tune_config():
    """Interactive config tuning"""
    config = json.load(open('apex_config.json'))
    
    print("\n🎛️ Tune Configuration")
    print("=" * 40)
    print("Current settings:")
    print(f"1. Signals/hour target: {config['signal_generation']['signals_per_hour_target']}")
    print(f"2. TCS threshold: {config['signal_generation']['min_tcs_threshold']}%")
    print(f"3. Scan interval: {config['signal_generation']['scan_interval_seconds']}s")
    print(f"4. Max spread: {config['signal_generation']['max_spread_allowed']}")
    print("5. Exit")
    
    choice = input("\nSelect option to change (1-5): ")
    
    if choice == '1':
        new_val = int(input("New signals/hour target (10-100): "))
        config['signal_generation']['signals_per_hour_target'] = new_val
    elif choice == '2':
        new_val = int(input("New TCS threshold (65-90): "))
        config['signal_generation']['min_tcs_threshold'] = new_val
    elif choice == '3':
        new_val = int(input("New scan interval seconds (15-120): "))
        config['signal_generation']['scan_interval_seconds'] = new_val
    elif choice == '4':
        new_val = int(input("New max spread (20-100): "))
        config['signal_generation']['max_spread_allowed'] = new_val
    else:
        return
    
    # Save config
    with open('apex_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("✅ Configuration saved! Restart APEX to apply changes.")

def view_logs():
    """Show recent log entries"""
    print("\n📜 Recent Signals")
    print("=" * 40)
    
    log_file = Path('apex_lean.log')
    if log_file.exists():
        lines = log_file.read_text().splitlines()
        # Show last 20 signals
        signal_lines = [l for l in lines if '🎯 SIGNAL' in l][-20:]
        for line in signal_lines:
            # Extract just the signal part
            parts = line.split(' - ')
            if len(parts) >= 4:
                print(f"{parts[0][-8:]} - {parts[3]}")
    else:
        print("No logs found")

def main():
    """Main menu"""
    while True:
        print("\n🎯 APEX Control Center")
        print("=" * 40)
        print("1. Show Status")
        print("2. Start APEX")
        print("3. Stop APEX")
        print("4. Tune Configuration")
        print("5. View Recent Signals")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            show_status()
        elif choice == '2':
            start_apex()
        elif choice == '3':
            stop_apex()
        elif choice == '4':
            tune_config()
        elif choice == '5':
            view_logs()
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()