#!/usr/bin/env python3
"""
Production readiness checklist for BITTEN v2.04 system
Run this before going live to ensure all systems are operational
"""
import sqlite3
import time
import os
import subprocess
import json

def check_mark(passed):
    return "✅" if passed else "❌"

def run_check(name, check_func):
    """Run a check and return result"""
    try:
        result = check_func()
        print(f"{check_mark(result)} {name}")
        return result
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        return False

def check_processes():
    """Check all required PM2 processes are running"""
    result = subprocess.run(['pm2', 'list', '--json'], capture_output=True, text=True)
    processes = json.loads(result.stdout)
    
    required = ['command_router', 'webapp', 'relay_to_telegram', 'confirm_listener']
    running = [p['name'] for p in processes if p['pm2_env']['status'] == 'online']
    
    return all(proc in running for proc in required)

def check_ea_metrics():
    """Check EA instances have metrics"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM ea_instances 
        WHERE last_equity IS NOT NULL 
        AND last_seen > ?
    """, (int(time.time()) - 300,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def check_equity_gate():
    """Check equity validation is in place"""
    with open('/root/HydraX-v2/webapp_server_optimized.py', 'r') as f:
        content = f.read()
    return 'ea_not_ready' in content and 'last_equity' in content

def check_no_dev_fallback():
    """Check COMMANDER_DEV_001 is properly gated"""
    with open('/root/HydraX-v2/webapp_server_optimized.py', 'r') as f:
        content = f.read()
    return 'if os.getenv("ENV") == "dev"' in content

def check_target_uuid_in_missions():
    """Check missions table has target_uuid column"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(missions)")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    return 'target_uuid' in columns

def check_fires_equity_tracking():
    """Check fires table has equity tracking columns"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(fires)")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    return 'equity_used' in columns and 'risk_pct_used' in columns

def check_firewall_rules():
    """Check port 5554 is blocked"""
    result = subprocess.run(['sudo', 'iptables', '-L', '-n'], capture_output=True, text=True)
    return '5554' in result.stdout and 'REJECT' in result.stdout

def check_zmq_ports():
    """Check ZMQ ports are listening"""
    result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
    ports = ['5555', '5556', '5557', '5558', '5560']
    return all(port in result.stdout for port in ports)

def check_athena_notification():
    """Check EA link notification is configured"""
    with open('/root/HydraX-v2/command_router.py', 'r') as f:
        content = f.read()
    return 'send_ea_linked_notification' in content

def check_operational_monitoring():
    """Check monitoring script exists"""
    return os.path.exists('/root/HydraX-v2/operational_monitor.py')

def main():
    print("=" * 60)
    print("🚀 BITTEN PRODUCTION READINESS CHECKLIST")
    print("=" * 60)
    print()
    
    checks = [
        ("Core processes running (PM2)", check_processes),
        ("EA metrics in database", check_ea_metrics),
        ("Equity validation gate active", check_equity_gate),
        ("Dev fallback properly gated", check_no_dev_fallback),
        ("Missions have target_uuid", check_target_uuid_in_missions),
        ("Fires track equity_used", check_fires_equity_tracking),
        ("Port 5554 firewall blocked", check_firewall_rules),
        ("ZMQ ports listening", check_zmq_ports),
        ("EA link notifications ready", check_athena_notification),
        ("Operational monitoring ready", check_operational_monitoring)
    ]
    
    results = []
    for name, check_func in checks:
        results.append(run_check(name, check_func))
    
    print()
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("🚀 SYSTEM IS READY FOR PRODUCTION!")
    else:
        print(f"⚠️ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("Please fix the failed items before going live.")
    
    print("=" * 60)
    
    # Additional info
    print("\n📊 Quick Stats:")
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM ea_instances")
    ea_count = cursor.fetchone()[0]
    print(f"  EA Instances: {ea_count}")
    
    cursor.execute("SELECT COUNT(*) FROM missions WHERE created_at > ?", (int(time.time()) - 86400,))
    mission_count = cursor.fetchone()[0]
    print(f"  Missions (24h): {mission_count}")
    
    cursor.execute("SELECT COUNT(*) FROM fires WHERE created_at > ?", (int(time.time()) - 86400,))
    fire_count = cursor.fetchone()[0]
    print(f"  Fires (24h): {fire_count}")
    
    conn.close()

if __name__ == "__main__":
    main()