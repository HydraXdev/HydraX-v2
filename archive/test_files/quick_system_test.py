#!/usr/bin/env python3
"""
Quick System Test - Verify BITTEN pipeline is working
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

def test_mission_generation():
    """Test that missions can be created"""
    print("🧪 Testing mission generation...")
    
    try:
        sys.path.append('/root/HydraX-v2/src')
        from bitten_core.mission_briefing_generator_v5 import generate_mission
        
        signal = {
            'symbol': 'GBPUSD',
            'type': 'sell',
            'tp': 1.2650,
            'sl': 1.2750,
            'tcs_score': 78
        }
        
        mission = generate_mission(signal, '7176191872')
        mission_id = mission['mission_id']
        
        # Check file was created
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if os.path.exists(mission_file):
            print(f"✅ Mission file created: {mission_id}")
            return mission_id
        else:
            print(f"❌ Mission file not found: {mission_file}")
            return None
            
    except Exception as e:
        print(f"❌ Mission generation failed: {e}")
        return None

def test_webapp_api(mission_id):
    """Test WebApp API endpoints"""
    print("🌐 Testing WebApp API...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8888/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"⚠️ Health endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test mission status endpoint
    if mission_id:
        try:
            response = requests.get(f"http://localhost:8888/api/mission-status/{mission_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Mission API working - Time remaining: {data.get('time_remaining', 'N/A')}s")
                return True
            else:
                print(f"❌ Mission API returned: {response.status_code}")
        except Exception as e:
            print(f"❌ Mission API failed: {e}")
    
    return False

def test_telegram_connector():
    """Test Telegram connector is monitoring"""
    print("📡 Testing Telegram connector...")
    
    # Check if process is running
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'apex_telegram_connector'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Telegram connector process found")
            return True
        else:
            print("⚠️ Telegram connector not running")
            return False
    except Exception as e:
        print(f"❌ Process check failed: {e}")
        return False

def test_apex_engine():
    """Test APEX engine is running"""
    print("🚀 Testing APEX engine...")
    
    # Check if log file exists and has recent entries
    log_file = "/root/HydraX-v2/apex_v5_live_real.log"
    if os.path.exists(log_file):
        try:
            stat = os.stat(log_file)
            age = time.time() - stat.st_mtime
            if age < 3600:  # Modified within last hour
                print(f"✅ APEX log file is recent (modified {age:.0f}s ago)")
                return True
            else:
                print(f"⚠️ APEX log file is old (modified {age:.0f}s ago)")
        except Exception as e:
            print(f"❌ Error checking log file: {e}")
    else:
        print("❌ APEX log file not found")
    
    return False

def test_missions_directory():
    """Test missions directory and cleanup"""
    print("📁 Testing missions directory...")
    
    missions_dir = "/root/HydraX-v2/missions"
    if os.path.exists(missions_dir):
        files = [f for f in os.listdir(missions_dir) if f.endswith('.json')]
        print(f"✅ Missions directory exists with {len(files)} mission files")
        return True
    else:
        print("❌ Missions directory not found")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🎯 BITTEN SYSTEM QUICK TEST")
    print("="*60)
    print(f"🕐 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Test components
    results.append(test_missions_directory())
    mission_id = test_mission_generation()
    results.append(mission_id is not None)
    results.append(test_webapp_api(mission_id))
    results.append(test_telegram_connector())
    results.append(test_apex_engine())
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print()
    print("="*60)
    print(f"📊 TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 System is mostly operational!")
    elif success_rate >= 60:
        print("⚠️ System has some issues but core functions work")
    else:
        print("❌ System needs attention")
    
    print("="*60)

if __name__ == "__main__":
    main()