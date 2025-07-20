#!/usr/bin/env python3
"""
Emergency webapp starter with health check
"""
import sys
import os
import time
import subprocess
import threading
import requests

sys.path.insert(0, '/root/HydraX-v2/src')

def start_webapp():
    try:
        os.chdir('/root/HydraX-v2')
        
        # Import and start webapp
        from bitten_core.web_app import app, socketio
        
        print("🚀 Starting BITTEN WebApp on port 5000...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ WebApp start failed: {e}")
        import traceback
        traceback.print_exc()

def health_check():
    """Wait and check if webapp is responding"""
    time.sleep(5)  # Wait for startup
    
    for attempt in range(10):
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ WebApp health check PASSED on attempt {attempt + 1}")
                return True
        except:
            print(f"⏳ Health check attempt {attempt + 1} failed, retrying...")
            time.sleep(2)
    
    print("❌ WebApp health check FAILED")
    return False

def create_watchdog():
    """Create watchdog script for permanent monitoring"""
    watchdog_content = '''#!/bin/bash
# BITTEN WebApp Watchdog
while true; do
    if ! curl -s http://localhost:5000/health > /dev/null; then
        echo "$(date): WebApp down, restarting..."
        systemctl restart bitten-webapp.service
    fi
    sleep 30
done
'''
    
    with open('/root/HydraX-v2/webapp_watchdog.sh', 'w') as f:
        f.write(watchdog_content)
    
    os.chmod('/root/HydraX-v2/webapp_watchdog.sh', 0o755)
    print("✅ Watchdog script created")

if __name__ == "__main__":
    print("🚨 EMERGENCY WEBAPP STARTUP")
    print("=" * 40)
    
    # Start webapp in background thread
    webapp_thread = threading.Thread(target=start_webapp, daemon=True)
    webapp_thread.start()
    
    # Create watchdog
    create_watchdog()
    
    # Run health check
    if health_check():
        print("🎉 WEBAPP RECOVERY SUCCESSFUL")
    else:
        print("💥 WEBAPP RECOVERY FAILED")
    
    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Webapp stopped")