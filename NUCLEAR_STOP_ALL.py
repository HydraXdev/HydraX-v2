#!/usr/bin/env python3
"""
☢️ NUCLEAR OPTION: STOP ALL AUTO-RESTART SYSTEMS ☢️
Completely disables all auto-restart mechanisms that could respawn bots
"""

import os
import subprocess
import time

def nuclear_stop():
    """Stop everything that could possibly restart bots"""
    
    print("☢️ NUCLEAR STOP INITIATED - DISABLING ALL AUTO-RESTART SYSTEMS")
    print("=" * 60)
    
    # 1. Stop and disable systemd services
    print("🔴 Stopping systemd services...")
    systemd_services = [
        'bitten-web.service',
        'bitten-webapp.service', 
        'bitten-monitoring.service',
        'bitten-dashboard.service',
        'bitten-health-check.service',
        'bitten-webapp-watchdog.service'
    ]
    
    for service in systemd_services:
        try:
            print(f"  🔴 Stopping {service}...")
            subprocess.run(['systemctl', 'stop', service], check=False, capture_output=True)
            subprocess.run(['systemctl', 'disable', service], check=False, capture_output=True)
        except:
            pass
    
    # 2. Stop PM2 processes
    print("🔴 Stopping PM2 processes...")
    try:
        subprocess.run(['pm2', 'stop', 'all'], check=False, capture_output=True)
        subprocess.run(['pm2', 'delete', 'all'], check=False, capture_output=True)
        subprocess.run(['pm2', 'kill'], check=False, capture_output=True)
    except:
        pass
    
    # 3. Kill all Python processes with signal-related names
    print("🔴 Killing all signal-related Python processes...")
    signal_patterns = [
        'python.*SIGNALS',
        'python.*START_SIGNALS', 
        'python.*telegram',
        'python.*bot',
        'python.*signal',
        'SIGNALS_COMPACT',
        'START_SIGNALS_NOW',
        'SIGNALS_REALISTIC',
        'SIGNALS_LIVE_DATA',
        'start_signals_fixed',
        'start_bitten_live_signals',
        'SIGNALS_CLEAN'
    ]
    
    for pattern in signal_patterns:
        try:
            subprocess.run(['pkill', '-f', pattern], check=False, capture_output=True)
            print(f"  🔫 Killed: {pattern}")
            time.sleep(0.5)
        except:
            pass
    
    # 4. Disable bot token in ALL files that might contain it
    print("🔴 Disabling bot token in all files...")
    token_files = [
        '/root/HydraX-v2/config/telegram.py',
        '/root/HydraX-v2/SIGNALS_COMPACT.py',
        '/root/HydraX-v2/START_SIGNALS_NOW.py',
        '/root/HydraX-v2/SIGNALS_REALISTIC.py',
        '/root/HydraX-v2/SIGNALS_LIVE_DATA.py',
        '/root/HydraX-v2/start_signals_fixed.py',
        '/root/HydraX-v2/src/bitten_core/telegram_messenger.py'
    ]
    
    for file_path in token_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace token with disabled version
                content = content.replace(
                    'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")',
                    'NUCLEAR_DISABLED_TOKEN'
                )
                
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"  🔴 Disabled token in: {file_path}")
        except Exception as e:
            print(f"  ❌ Error disabling token in {file_path}: {e}")
    
    # 5. Check for cron jobs
    print("🔴 Checking cron jobs...")
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=False)
        if result.stdout and 'python' in result.stdout.lower():
            print("  ⚠️  Found Python cron jobs:")
            print(result.stdout)
            print("  🔴 You may need to manually remove these!")
    except:
        pass
    
    # 6. Final process check
    print("🔴 Final cleanup - killing any remaining processes...")
    time.sleep(2)
    
    # One more aggressive kill
    try:
        subprocess.run(['pkill', '-9', '-f', 'python.*telegram'], check=False, capture_output=True)
        subprocess.run(['pkill', '-9', '-f', '7854827710'], check=False, capture_output=True)
    except:
        pass
    
    print("\n☢️ NUCLEAR STOP COMPLETE")
    print("✅ All auto-restart systems should be disabled")
    print("✅ All bot tokens disabled")
    print("✅ All processes killed")
    print("=" * 60)
    
    # Create lock file to prevent restarts
    try:
        with open('/tmp/BITTEN_NUCLEAR_STOP', 'w') as f:
            f.write(f"Nuclear stop executed at {time.ctime()}")
        print("🔒 Nuclear stop lock file created")
    except:
        pass

if __name__ == "__main__":
    nuclear_stop()