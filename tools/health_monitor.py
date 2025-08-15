#!/usr/bin/env python3
"""System health monitor with auto-recovery"""
import os, time, subprocess, requests, redis, sqlite3

def check_port(port):
    """Check if a port is listening"""
    result = subprocess.run(f"ss -tln | grep -q :{port}", shell=True, capture_output=True)
    return result.returncode == 0

def check_webapp():
    """Check webapp health"""
    try:
        resp = requests.get("http://localhost:8888/healthz", timeout=2)
        return resp.status_code == 200
    except:
        return False

def check_redis():
    """Check Redis health"""
    try:
        r = redis.Redis(host="127.0.0.1", port=6379)
        r.ping()
        return True
    except:
        return False

def check_database():
    """Check SQLite database"""
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        conn.execute("SELECT 1")
        conn.close()
        return True
    except:
        return False

def restart_service(name):
    """Restart a PM2 service with backoff"""
    print(f"[HEALTH] Restarting {name}...")
    subprocess.run(f"pm2 restart {name}", shell=True, capture_output=True)
    time.sleep(5)

def clear_redis_backlog():
    """Clear stuck Redis messages"""
    try:
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        pending = r.xpending("alerts", "telegram")
        if pending and pending[0] > 10:
            print(f"[HEALTH] Clearing {pending[0]} stuck alerts...")
            # Force claim old messages
            r.xautoclaim("alerts", "telegram", "health_monitor", 60000, "-", count=100)
    except:
        pass

def monitor_loop():
    """Main monitoring loop"""
    print("[HEALTH] System health monitor started")
    
    while True:
        try:
            # Critical service checks
            checks = {
                "webapp": check_webapp(),
                "command_router": check_port(5555),
                "elite_guard": check_port(5557),
                "telemetry": check_port(5556),
                "confirmations": check_port(5558),
                "redis": check_redis(),
                "database": check_database()
            }
            
            # Auto-recovery actions
            if not checks["webapp"]:
                restart_service("webapp")
            
            if not checks["redis"]:
                print("[HEALTH] Redis down - critical failure!")
                
            # Clear Redis backlogs
            clear_redis_backlog()
            
            # Status report
            healthy = sum(checks.values())
            total = len(checks)
            status = "✅ HEALTHY" if healthy == total else f"⚠️ DEGRADED ({healthy}/{total})"
            print(f"[HEALTH] {status} - " + ", ".join([f"{k}:{'✓' if v else '✗'}" for k,v in checks.items()]))
            
        except Exception as e:
            print(f"[HEALTH] Monitor error: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_loop()