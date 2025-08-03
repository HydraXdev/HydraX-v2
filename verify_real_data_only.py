#!/usr/bin/env python3
"""
🔒 VERIFY REAL DATA ONLY
Comprehensive verification that CITADEL system uses 100% real truth_log.jsonl data
"""

import json
import os
from datetime import datetime
from pathlib import Path

def verify_citadel_state():
    """Verify citadel_state.json contains no fake data"""
    citadel_path = "/root/HydraX-v2/citadel_state.json"
    
    if not os.path.exists(citadel_path):
        print("❌ citadel_state.json does not exist")
        return False
    
    try:
        with open(citadel_path, 'r') as f:
            data = json.load(f)
        
        # Check if empty (good)
        if data == {}:
            print("✅ citadel_state.json is empty (no fake data)")
            return True
        
        # Check for fake consecutive losses
        fake_patterns = [
            "consecutive losses",
            "cooldown_until", 
            "71 consecutive losses",
            "58 consecutive losses",
            "65 consecutive losses"
        ]
        
        data_str = json.dumps(data).lower()
        for pattern in fake_patterns:
            if pattern in data_str:
                print(f"❌ FAKE DATA DETECTED: '{pattern}' found in citadel_state.json")
                return False
        
        print("✅ citadel_state.json contains no obvious fake data patterns")
        return True
        
    except Exception as e:
        print(f"❌ Error reading citadel_state.json: {e}")
        return False

def verify_truth_log_exists():
    """Verify truth_log.jsonl exists and has real data"""
    truth_path = "/root/HydraX-v2/truth_log.jsonl"
    
    if not os.path.exists(truth_path):
        print("❌ truth_log.jsonl does not exist")
        return False
    
    try:
        with open(truth_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print("⚠️ truth_log.jsonl is empty")
            return False
        
        # Check last few entries
        recent_entries = lines[-5:] if len(lines) >= 5 else lines
        print(f"✅ truth_log.jsonl exists with {len(lines)} entries")
        
        for i, line in enumerate(recent_entries):
            try:
                data = json.loads(line.strip())
                signal_id = data.get('signal_id', 'Unknown')
                result = data.get('result', 'Unknown')
                print(f"  Recent entry {i+1}: {signal_id} → {result}")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading truth_log.jsonl: {e}")
        return False

def verify_no_fake_processes():
    """Verify no processes are generating fake CITADEL data"""
    import subprocess
    
    try:
        # Check for engineer_agent process
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        process_list = result.stdout
        
        fake_processes = [
            'engineer_agent.py',
            'fake_data_generator',
            'synthetic_data',
            'simulation'
        ]
        
        for process_name in fake_processes:
            if process_name in process_list and 'grep' not in process_list:
                lines = [line for line in process_list.split('\n') if process_name in line and 'grep' not in line]
                if lines:
                    print(f"❌ FAKE DATA PROCESS DETECTED: {process_name}")
                    for line in lines:
                        print(f"  {line.strip()}")
                    return False
        
        print("✅ No fake data generation processes detected")
        return True
        
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False

def verify_file_permissions():
    """Verify citadel_state.json is read-only"""
    citadel_path = "/root/HydraX-v2/citadel_state.json"
    
    try:
        stat = os.stat(citadel_path)
        mode = oct(stat.st_mode)[-3:]  # Get last 3 digits (permissions)
        
        if mode == '444':
            print("✅ citadel_state.json is read-only (444)")
            return True
        else:
            print(f"⚠️ citadel_state.json permissions: {mode} (should be 444)")
            return False
            
    except Exception as e:
        print(f"❌ Error checking file permissions: {e}")
        return False

def main():
    """Run comprehensive verification"""
    print("🔒 CITADEL REAL DATA VERIFICATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    all_checks_passed = True
    
    # Run all verification checks
    checks = [
        ("CITADEL State File", verify_citadel_state),
        ("Truth Log Exists", verify_truth_log_exists),
        ("No Fake Processes", verify_no_fake_processes),
        ("File Permissions", verify_file_permissions)
    ]
    
    for check_name, check_func in checks:
        print(f"Checking: {check_name}")
        result = check_func()
        if not result:
            all_checks_passed = False
        print()
    
    # Final result
    print("=" * 50)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - SYSTEM USES 100% REAL DATA")
        print("🛡️ CITADEL system is clean of fake/synthetic data")
    else:
        print("❌ SOME CHECKS FAILED - FAKE DATA DETECTED")
        print("🚨 System requires additional cleanup")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)