#!/usr/bin/env python3
"""
🧪 VENOM Watchdog Test Script
Tests the watchdog functionality without running the full daemon
"""

import sys
import time
sys.path.append('/root/HydraX-v2/infra')

from venom_watchdog import VenomWatchdog

def test_watchdog():
    """Test watchdog functionality"""
    print("🧪 Testing VENOM Watchdog...")
    
    # Create watchdog instance
    watchdog = VenomWatchdog()
    
    # Test duplicate process check
    print("🔍 Testing duplicate process check...")
    has_duplicate = watchdog.check_duplicate_process()
    print(f"   Duplicate process: {'Yes' if has_duplicate else 'No'}")
    
    # Test process detection
    print("🔍 Testing VENOM process detection...")
    is_running = watchdog.is_venom_running()
    processes = watchdog.find_venom_processes()
    print(f"   VENOM running: {'Yes' if is_running else 'No'}")
    print(f"   Processes found: {len(processes)}")
    
    for proc in processes:
        try:
            print(f"   - PID {proc.pid}: {' '.join(proc.cmdline())}")
        except:
            print(f"   - PID {proc.pid}: <unable to read cmdline>")
    
    # Test alert formatting
    print("📱 Testing alert formatting...")
    startup_alert = watchdog.format_startup_alert()
    restart_alert = watchdog.format_restart_alert()
    
    print("   Startup alert preview:")
    print("   " + startup_alert.split('\n')[0])
    print("   Restart alert preview:")  
    print("   " + restart_alert.split('\n')[0])
    
    # Test logging
    print("📝 Testing logging...")
    watchdog.logger.info("🧪 Test log message from watchdog test")
    
    print("✅ Watchdog test completed successfully!")
    print(f"📝 Check log file: /root/HydraX-v2/infra/venom_watchdog.log")

if __name__ == "__main__":
    test_watchdog()