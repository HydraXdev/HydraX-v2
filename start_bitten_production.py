#!/usr/bin/env python3
"""
BITTEN Production Startup Script
Orchestrates the complete signal-to-mission-to-execution pipeline
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime
import multiprocessing
from pathlib import Path
import psutil

def print_banner():
    print("="*60)
    print("🎯 BITTEN v2.1 - PRODUCTION DEPLOYMENT")
    print("⚡ Signal-to-Mission-to-Execution Pipeline")
    print("="*60)
    print(f"📅 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_requirements():
    """Check that all required components are in place"""
    print("🔍 Checking system requirements...")
    
    # Check directories
    dirs_to_check = [
        "/root/HydraX-v2/missions",
        "/root/HydraX-v2/logs", 
        "/root/HydraX-v2/src/api",
        "/root/HydraX-v2/src/bitten_core"
    ]
    
    for dir_path in dirs_to_check:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check key files
    key_files = [
        "/root/HydraX-v2/apex_v5_live_real.py",
        "/root/HydraX-v2/apex_telegram_connector.py", 
        "/root/HydraX-v2/src/bitten_core/mission_briefing_generator_v5.py",
        "/root/HydraX-v2/src/api/mission_endpoints.py",
        "/root/HydraX-v2/src/bitten_core/fire_router.py",
        "/root/HydraX-v2/webapp_server.py"
    ]
    
    missing_files = []
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {os.path.basename(file_path)}")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files. Please check deployment.")
        return False
    
    print("✅ All requirements satisfied!")
    return True

def start_apex_engine():
    """Start the v5.0 signal generation engine"""
    print("\n🚀 Starting v5.0 Signal Engine...")
    
    # Check if already running
    pid_file = Path('/root/HydraX-v2/.apex_engine.pid')
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process is actually running
            os.kill(pid, 0)  # This will raise an exception if process doesn't exist
            print(f"✅ already running with PID {pid}")
            return psutil.Process(pid)
        except (OSError, ValueError, psutil.NoSuchProcess):
            # Process not running, clean up stale PID file
            print("🧹 Cleaning up stale PID file")
            pid_file.unlink()
    
    try:
        os.chdir("/root/HydraX-v2")
        proc = subprocess.Popen([
            sys.executable, "apex_v5_live_real.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Engine started (PID: {proc.pid})")
        return proc
        
    except Exception as e:
        print(f"❌ Failed to start Engine: {e}")
        return None

def start_telegram_connector():
    """Start the Telegram signal connector"""
    print("\n📡 Starting Telegram Signal Connector...")
    
    try:
        os.chdir("/root/HydraX-v2")
        proc = subprocess.Popen([
            sys.executable, "apex_telegram_connector.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Telegram Connector started (PID: {proc.pid})")
        return proc
        
    except Exception as e:
        print(f"❌ Failed to start Telegram Connector: {e}")
        return None

def start_webapp_server():
    """Start the WebApp server with mission endpoints"""
    print("\n🌐 Starting WebApp Server...")
    
    try:
        os.chdir("/root/HydraX-v2")
        proc = subprocess.Popen([
            sys.executable, "webapp_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ WebApp Server started (PID: {proc.pid})")
        print("🌐 Available at: https://joinbitten.com")
        return proc
        
    except Exception as e:
        print(f"❌ Failed to start WebApp Server: {e}")
        return None

def monitor_system(processes):
    """Monitor all processes and restart if needed"""
    print("\n👁️ Monitoring system health...")
    
    while True:
        try:
            for name, proc in processes.items():
                if proc and proc.poll() is not None:
                    print(f"⚠️ {name} stopped (exit code: {proc.returncode})")
                    # Could implement restart logic here
                    
            # Check mission files
            mission_count = len([f for f in os.listdir("/root/HydraX-v2/missions") 
                               if f.endswith('.json')])
            
            # Status update every 60 seconds
            print(f"📊 Status: {len([p for p in processes.values() if p and p.poll() is None])}/3 processes running, "
                  f"{mission_count} active missions")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
            break
        except Exception as e:
            print(f"⚠️ Monitor error: {e}")
            time.sleep(5)

def shutdown_handler(signum, frame):
    """Handle graceful shutdown"""
    print(f"\n🛑 Received signal {signum}, initiating shutdown...")
    
    # Kill all child processes
    current_pid = os.getpid()
    try:
        # Get all child processes
        children = subprocess.check_output(
            f"pgrep -P {current_pid}", shell=True
        ).decode().strip().split('\n')
        
        for child_pid in children:
            if child_pid:
                try:
                    os.kill(int(child_pid), signal.SIGTERM)
                    print(f"🔪 Terminated process {child_pid}")
                except:
                    pass
    except:
        pass
    
    print("✅ Shutdown complete")
    sys.exit(0)

def main():
    """Main execution flow"""
    print_banner()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Start all components
    processes = {}
    
    # Start engine
    apex_proc = start_apex_engine()
    processes['Engine'] = apex_proc
    time.sleep(2)
    
    # Start Telegram connector
    telegram_proc = start_telegram_connector()
    processes['Telegram Connector'] = telegram_proc
    time.sleep(2)
    
    # Start WebApp server
    webapp_proc = start_webapp_server()
    processes['WebApp Server'] = webapp_proc
    time.sleep(2)
    
    print("\n" + "="*60)
    print("🎉 BITTEN PRODUCTION SYSTEM ONLINE")
    print("="*60)
    print("📡 Signal Flow: Bridge → → Telegram → WebApp → Execution")
    print("🎯 Mission Storage: /root/HydraX-v2/missions/")
    print("📊 Logs: /root/HydraX-v2/apex_v5_live_real.log")
    print("🌐 WebApp: https://joinbitten.com")
    print("🤖 Bot: @BIT_COMMANDER_BOT")
    print("="*60)
    
    # Monitor system
    try:
        monitor_system(processes)
    except KeyboardInterrupt:
        shutdown_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()