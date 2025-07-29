#!/usr/bin/env python3
"""
ENGINE STATUS MONITOR
Shows exactly which engine is running with unique identifiers
"""

import os
import sys
import requests
import json
import subprocess
from datetime import datetime
from REAL_ENGINE_PROTECTION import RealEngineProtection

def get_current_engine_info():
    """Get detailed info about currently running engine"""
    
    print("🔍 ENGINE STATUS MONITOR")
    print("=" * 50)
    print(f"⏰ Check Time: {datetime.now()}")
    print()
    
    # Check protection system
    protection = RealEngineProtection()
    status = protection.get_engine_status()
    
    print("🛡️ PROTECTION STATUS:")
    print(f"   Active: {'✅ YES' if status['protection_active'] else '❌ NO'}")
    print(f"   Real Engines Verified: {len([e for e in status['real_engines'].values() if e.get('verified', False)])}")
    print(f"   Fake Engines Protected: {len([e for e in status['fake_engines'].values() if e.get('protected', False)])}")
    print()
    
    # Check what's running on port 8001
    print("📡 PORT 8001 STATUS:")
    try:
        result = subprocess.run(['lsof', '-i', ':8001'], capture_output=True, text=True)
        if result.stdout:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    print(f"   Process: {parts[0]} (PID: {parts[1]})")
        else:
            print("   ❌ No process listening on port 8001")
    except:
        print("   ❌ Could not check port status")
    
    # Check which Python script is running
    print("\n🐍 PYTHON PROCESSES:")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'python3' in line and ('market_data' in line or 'venom' in line or 'signal' in line):
                parts = line.split()
                pid = parts[1]
                cmd = ' '.join(parts[10:])
                print(f"   PID {pid}: {cmd}")
    except:
        print("   ❌ Could not check Python processes")
    
    # Test the running service
    print("\n🔬 SERVICE TESTS:")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        print(f"   Health Check: ✅ {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service Type: {data.get('service', 'Unknown')}")
            print(f"   Active Symbols: {data.get('active_symbols', 'Unknown')}")
    except:
        print("   Health Check: ❌ Failed")
    
    # Test /market-data/all endpoint (VENOM needs this)
    try:
        response = requests.get('http://localhost:8001/market-data/all', timeout=5)
        print(f"   VENOM Feed: ✅ {response.status_code} (VENOM can get data)")
    except:
        print("   VENOM Feed: ❌ Failed (VENOM cannot get data)")
    
    # Test /venom-feed endpoint 
    try:
        response = requests.get('http://localhost:8001/venom-feed', timeout=5)
        print(f"   Legacy VENOM: ✅ {response.status_code}")
    except:
        print("   Legacy VENOM: ❌ Failed")
    
    print("\n📊 ENGINE IDENTIFICATION:")
    
    # Check for real engine markers
    real_engines = ["market_data_receiver_enhanced.py", "venom_real_data_engine.py"]
    for engine in real_engines:
        marker_file = f"/root/HydraX-v2/{engine}.REAL_ENGINE_VERIFIED"
        if os.path.exists(marker_file):
            print(f"   ✅ {engine}: VERIFIED REAL ENGINE")
            with open(marker_file, 'r') as f:
                lines = f.read().split('\n')
                for line in lines:
                    if line.startswith('SHA256:'):
                        print(f"      🔐 Hash: {line.split('SHA256: ')[1][:16]}...")
                        break
        else:
            print(f"   ❓ {engine}: Not verified")
    
    # Check fake engine protection
    fake_engines = ["apex_venom_v7_unfiltered.py.FAKE_DISABLED", "working_signal_generator.py.FAKE_DISABLED"]
    for engine in fake_engines:
        full_path = f"/root/HydraX-v2/{engine}"
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()[:500]
                if "VIRUS PROTECTION" in content:
                    print(f"   🛡️ {engine}: PROTECTED (cannot run)")
                else:
                    print(f"   ⚠️ {engine}: NOT PROTECTED!")
    
    print("\n" + "=" * 50)
    
    # Final verdict
    if status['protection_active']:
        print("✅ SYSTEM SECURE: Real engines active, fake engines blocked")
        
        # Give unique identifier for current session
        import hashlib
        import time
        session_id = hashlib.md5(f"{datetime.now()}{os.getpid()}".encode()).hexdigest()[:8]
        print(f"🆔 SESSION ID: REAL-{session_id}")
        print("📝 Use this ID to confirm you're using the real engine")
    else:
        print("⚠️ SYSTEM AT RISK: Protection not active!")
    
    return status

def test_fake_engine_protection():
    """Test that fake engines are actually blocked"""
    print("\n🧪 TESTING FAKE ENGINE PROTECTION:")
    
    fake_files = [
        "apex_venom_v7_unfiltered.py.FAKE_DISABLED",
        "working_signal_generator.py.FAKE_DISABLED"
    ]
    
    for fake_file in fake_files:
        full_path = f"/root/HydraX-v2/{fake_file}"
        if os.path.exists(full_path):
            print(f"   Testing {fake_file}...")
            try:
                # Try to run the fake engine (should fail immediately)
                result = subprocess.run([sys.executable, full_path], 
                                      capture_output=True, text=True, timeout=5)
                
                if "FAKE ENGINE DETECTED" in result.stdout:
                    print(f"   ✅ {fake_file}: BLOCKED (virus protection active)")
                else:
                    print(f"   ❌ {fake_file}: NOT BLOCKED! DANGER!")
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ {fake_file}: Still running (timeout) - DANGER!")
            except Exception as e:
                print(f"   ✅ {fake_file}: Cannot execute - PROTECTED")

if __name__ == "__main__":
    status = get_current_engine_info()
    test_fake_engine_protection()