#!/usr/bin/env python3
"""
Production Guard System - v2.04_locked
Ensures production code immutability and stability
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from pathlib import Path

PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "true").lower() == "true"
LOCKFILE = Path("/root/HydraX-v2/.production_lock")

class ProductionGuard:
    """Enforces production immutability rules"""
    
    def __init__(self):
        self.locked = self._check_lock()
        self.critical_processes = {
            "elite_guard_with_citadel.py": "Signal Generation",
            "webapp_server_optimized.py": "Web Interface",
            "bitten_production_bot.py": "Telegram Bot",
            "command_router_service.py": "EA Router",
            "zmq_telemetry_bridge_debug.py": "Market Data"
        }
        
    def _check_lock(self):
        """Check if production is locked"""
        if LOCKFILE.exists():
            with open(LOCKFILE) as f:
                lock_data = json.load(f)
                return lock_data.get("locked", False)
        return False
        
    def verify_integrity(self):
        """Verify critical file integrity"""
        if not self.locked:
            return True
            
        violations = []
        for filename in self.critical_processes:
            filepath = Path(f"/root/HydraX-v2/{filename}")
            if filepath.exists():
                # Check modification time
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                lock_time = datetime.fromisoformat(self._get_lock_time())
                if mtime > lock_time:
                    violations.append(f"{filename} modified after lock")
                    
        if violations:
            print(f"⚠️ PRODUCTION GUARD VIOLATIONS:")
            for v in violations:
                print(f"  - {v}")
            return False
        return True
        
    def _get_lock_time(self):
        """Get production lock timestamp"""
        if LOCKFILE.exists():
            with open(LOCKFILE) as f:
                return json.load(f).get("timestamp", datetime.now().isoformat())
        return datetime.now().isoformat()
        
    def lock_production(self):
        """Lock production with current state"""
        lock_data = {
            "locked": True,
            "timestamp": datetime.now().isoformat(),
            "version": "v2.04_locked",
            "processes": self.critical_processes
        }
        
        with open(LOCKFILE, 'w') as f:
            json.dump(lock_data, f, indent=2)
            
        print("🔒 Production locked at v2.04")
        return True
        
    def check_process_health(self):
        """Verify critical processes are running"""
        import subprocess
        
        missing = []
        for process in self.critical_processes:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", process],
                    capture_output=True,
                    text=True
                )
                if not result.stdout.strip():
                    missing.append(process)
            except:
                pass
                
        if missing:
            print("⚠️ Missing critical processes:")
            for p in missing:
                print(f"  - {p} ({self.critical_processes[p]})")
            return False
        return True

# Production safety checks
def enforce_production_safety():
    """Main production safety enforcement"""
    if not PRODUCTION_MODE:
        return True
        
    guard = ProductionGuard()
    
    # Lock if not already locked
    if not guard.locked:
        guard.lock_production()
    
    # Verify integrity
    if not guard.verify_integrity():
        print("❌ Production integrity check failed")
        return False
        
    # Check process health
    if not guard.check_process_health():
        print("⚠️ Some processes need restart")
        
    return True

if __name__ == "__main__":
    if enforce_production_safety():
        print("✅ Production guard active - v2.04_locked")
    else:
        print("❌ Production guard detected issues")
        sys.exit(1)