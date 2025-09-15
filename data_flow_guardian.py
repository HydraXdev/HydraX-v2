#!/usr/bin/env python3
"""
Data Flow Guardian - Monitors and protects critical data flows in BITTEN system
Prevents breakages and automatically recovers from failures
"""

import time
import json
import sqlite3
import subprocess
import os
import zmq
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import signal
import sys

class DataFlowGuardian:
    """Monitors all critical data flows and ensures they stay operational"""
    
    def __init__(self):
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.tracking_files = [
            "/root/HydraX-v2/comprehensive_tracking.jsonl",
            "/root/HydraX-v2/dynamic_tracking.jsonl",
            "/root/HydraX-v2/ml_training_data.jsonl"
        ]
        self.critical_processes = {
            # LOCKED components - must always be running
            "elite_guard": {
                "name": "elite_guard_with_citadel.py",
                "pm2_name": "elite_guard",
                "check_interval": 60,
                "last_check": 0,
                "restart_on_fail": True,
                "max_restarts": 3,
                "restart_count": 0
            },
            "command_router": {
                "name": "command_router.py", 
                "pm2_name": "command_router",
                "check_interval": 30,
                "last_check": 0,
                "restart_on_fail": True,
                "max_restarts": 3,
                "restart_count": 0
            },
            "webapp": {
                "name": "webapp_server_optimized.py",
                "pm2_name": "webapp",
                "check_interval": 60,
                "last_check": 0,
                "restart_on_fail": True,
                "max_restarts": 3,
                "restart_count": 0
            },
            "telemetry_bridge": {
                "name": "zmq_telemetry_bridge_debug.py",
                "pm2_name": "zmq_telemetry_bridge",
                "check_interval": 60,
                "last_check": 0,
                "restart_on_fail": True,
                "max_restarts": 3,
                "restart_count": 0
            },
            "relay": {
                "name": "elite_guard_zmq_relay.py",
                "pm2_name": "relay_to_telegram",
                "check_interval": 60,
                "last_check": 0,
                "restart_on_fail": True,
                "max_restarts": 3,
                "restart_count": 0
            }
        }
        
        self.zmq_ports = {
            5555: "command_router",
            5556: "market_data_in",
            5557: "elite_signals", 
            5558: "confirmations",
            5560: "market_relay"
        }
        
        self.health_status = {
            "last_signal": None,
            "last_tick": None,
            "last_fire": None,
            "signals_24h": 0,
            "fires_24h": 0,
            "ea_freshness": None,
            "process_health": {},
            "port_health": {},
            "data_flow_health": {}
        }
        
        self.running = True
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        print("\n⚠️ Data Flow Guardian shutting down...")
        self.running = False
        sys.exit(0)
        
    def check_process_health(self) -> Dict[str, bool]:
        """Check if critical processes are running"""
        health = {}
        current_time = time.time()
        
        for key, proc in self.critical_processes.items():
            # Check if we should check this process
            if current_time - proc["last_check"] < proc["check_interval"]:
                continue
                
            proc["last_check"] = current_time
            
            # Check PM2 status
            try:
                result = subprocess.run(
                    ["pm2", "jlist"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    pm2_data = json.loads(result.stdout)
                    is_running = False
                    
                    for app in pm2_data:
                        if app.get("name") == proc["pm2_name"]:
                            is_running = app.get("pm2_env", {}).get("status") == "online"
                            break
                    
                    health[key] = is_running
                    
                    # Auto-restart if needed
                    if not is_running and proc["restart_on_fail"]:
                        if proc["restart_count"] < proc["max_restarts"]:
                            print(f"⚠️ {key} is DOWN - attempting restart...")
                            self.restart_process(proc["pm2_name"])
                            proc["restart_count"] += 1
                        else:
                            print(f"❌ {key} max restarts reached - manual intervention needed")
                else:
                    health[key] = False
                    
            except Exception as e:
                print(f"Error checking {key}: {e}")
                health[key] = False
                
        self.health_status["process_health"] = health
        return health
        
    def restart_process(self, pm2_name: str):
        """Restart a PM2 process"""
        try:
            subprocess.run(["pm2", "restart", pm2_name], timeout=10)
            print(f"✅ Restarted {pm2_name}")
            time.sleep(3)  # Give it time to start
        except Exception as e:
            print(f"❌ Failed to restart {pm2_name}: {e}")
            
    def check_zmq_ports(self) -> Dict[int, bool]:
        """Check if ZMQ ports are bound"""
        health = {}
        
        try:
            result = subprocess.run(
                ["ss", "-tulpen"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for port, name in self.zmq_ports.items():
                health[port] = f":{port}" in result.stdout
                
        except Exception as e:
            print(f"Error checking ports: {e}")
            for port in self.zmq_ports:
                health[port] = False
                
        self.health_status["port_health"] = health
        return health
        
    def check_data_flows(self) -> Dict[str, Dict]:
        """Check critical data flows"""
        flows = {}
        
        # 1. Check signal flow (last signal time)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check latest signal
            cursor.execute("""
                SELECT signal_id, created_at 
                FROM signals 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                signal_age = int(time.time()) - result[1]
                flows["signal_generation"] = {
                    "last_signal": result[0],
                    "age_seconds": signal_age,
                    "healthy": signal_age < 3600  # Healthy if signal in last hour
                }
                self.health_status["last_signal"] = result[0]
            else:
                flows["signal_generation"] = {
                    "last_signal": None,
                    "age_seconds": None,
                    "healthy": False
                }
                
            # Check 24h signal count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM signals 
                WHERE created_at > strftime('%s', 'now', '-24 hours')
            """)
            self.health_status["signals_24h"] = cursor.fetchone()[0]
            
            # Check EA freshness
            cursor.execute("""
                SELECT target_uuid, (strftime('%s','now') - last_seen) AS age
                FROM ea_instances
                WHERE target_uuid = 'COMMANDER_DEV_001'
            """)
            result = cursor.fetchone()
            
            if result:
                ea_age = result[1]
                flows["ea_connection"] = {
                    "uuid": result[0],
                    "age_seconds": ea_age,
                    "healthy": ea_age < 120  # Healthy if heartbeat < 2 min
                }
                self.health_status["ea_freshness"] = ea_age
            else:
                flows["ea_connection"] = {
                    "uuid": None,
                    "age_seconds": None,
                    "healthy": False
                }
                
            # Check fire executions
            cursor.execute("""
                SELECT COUNT(*)
                FROM fires
                WHERE created_at > strftime('%s', 'now', '-24 hours')
            """)
            self.health_status["fires_24h"] = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            print(f"Database error: {e}")
            flows["signal_generation"] = {"healthy": False, "error": str(e)}
            flows["ea_connection"] = {"healthy": False, "error": str(e)}
            
        # 2. Check tracking file updates
        for filepath in self.tracking_files:
            try:
                if os.path.exists(filepath):
                    mtime = os.path.getmtime(filepath)
                    age = time.time() - mtime
                    flows[os.path.basename(filepath)] = {
                        "age_seconds": int(age),
                        "healthy": age < 7200  # Healthy if updated in last 2 hours
                    }
                else:
                    flows[os.path.basename(filepath)] = {
                        "exists": False,
                        "healthy": False
                    }
            except Exception as e:
                flows[os.path.basename(filepath)] = {
                    "healthy": False,
                    "error": str(e)
                }
                
        self.health_status["data_flow_health"] = flows
        return flows
        
    def generate_status_report(self) -> str:
        """Generate comprehensive status report"""
        report = []
        report.append("=" * 70)
        report.append("🛡️ DATA FLOW GUARDIAN STATUS REPORT")
        report.append("=" * 70)
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        
        # Process Health
        report.append("📊 PROCESS HEALTH:")
        report.append("-" * 50)
        for name, healthy in self.health_status.get("process_health", {}).items():
            status = "✅ RUNNING" if healthy else "❌ DOWN"
            report.append(f"{name:20} {status}")
            
        # Port Health
        report.append("")
        report.append("🔌 ZMQ PORT STATUS:")
        report.append("-" * 50)
        for port, healthy in self.health_status.get("port_health", {}).items():
            status = "✅ BOUND" if healthy else "❌ UNBOUND"
            name = self.zmq_ports.get(port, "unknown")
            report.append(f"Port {port:5} ({name:15}) {status}")
            
        # Data Flow Health
        report.append("")
        report.append("📈 DATA FLOW STATUS:")
        report.append("-" * 50)
        
        for flow_name, flow_data in self.health_status.get("data_flow_health", {}).items():
            if flow_data.get("healthy"):
                status = "✅ HEALTHY"
            else:
                status = "⚠️ STALE" if flow_data.get("age_seconds", 0) > 0 else "❌ BROKEN"
                
            age = flow_data.get("age_seconds")
            if age is not None:
                if age < 60:
                    age_str = f"{age}s ago"
                elif age < 3600:
                    age_str = f"{age//60}m ago"
                else:
                    age_str = f"{age//3600}h ago"
            else:
                age_str = "unknown"
                
            report.append(f"{flow_name:30} {status:12} ({age_str})")
            
        # Summary Stats
        report.append("")
        report.append("📊 24-HOUR STATISTICS:")
        report.append("-" * 50)
        report.append(f"Signals Generated: {self.health_status.get('signals_24h', 0)}")
        report.append(f"Trades Executed: {self.health_status.get('fires_24h', 0)}")
        
        ea_fresh = self.health_status.get("ea_freshness")
        if ea_fresh is not None:
            ea_status = "✅ CONNECTED" if ea_fresh < 120 else "⚠️ STALE"
            report.append(f"EA Connection: {ea_status} (last seen {ea_fresh}s ago)")
        else:
            report.append("EA Connection: ❌ DISCONNECTED")
            
        report.append("=" * 70)
        
        return "\n".join(report)
        
    def write_health_file(self):
        """Write health status to JSON file for other processes"""
        try:
            with open("/root/HydraX-v2/data_flow_health.json", "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "health_status": self.health_status,
                    "all_healthy": all([
                        all(self.health_status.get("process_health", {}).values()),
                        all(self.health_status.get("port_health", {}).values()),
                        all([f.get("healthy", False) for f in self.health_status.get("data_flow_health", {}).values()])
                    ])
                }, f, indent=2)
        except Exception as e:
            print(f"Error writing health file: {e}")
            
    def monitor_loop(self):
        """Main monitoring loop"""
        print("🛡️ Data Flow Guardian starting...")
        print("Monitoring critical data flows and processes")
        print("Press Ctrl+C to stop")
        print("")
        
        last_report = 0
        report_interval = 300  # Report every 5 minutes
        
        while self.running:
            try:
                # Check all health metrics
                self.check_process_health()
                self.check_zmq_ports()
                self.check_data_flows()
                
                # Write health file
                self.write_health_file()
                
                # Print report periodically
                current_time = time.time()
                if current_time - last_report > report_interval:
                    print(self.generate_status_report())
                    last_report = current_time
                    
                # Check for critical failures
                critical_failures = []
                
                # Check processes
                for name, healthy in self.health_status.get("process_health", {}).items():
                    if not healthy and name in ["elite_guard", "command_router", "webapp"]:
                        critical_failures.append(f"{name} process DOWN")
                        
                # Check ports
                for port, healthy in self.health_status.get("port_health", {}).items():
                    if not healthy and port in [5555, 5556, 5560]:
                        critical_failures.append(f"Port {port} UNBOUND")
                        
                # Check EA connection
                ea_fresh = self.health_status.get("ea_freshness")
                if ea_fresh is None or ea_fresh > 300:
                    critical_failures.append("EA disconnected")
                    
                # Alert on critical failures
                if critical_failures:
                    print("\n🚨 CRITICAL FAILURES DETECTED:")
                    for failure in critical_failures:
                        print(f"  ❌ {failure}")
                    print("")
                    
                # Sleep before next check
                time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(30)
                
        print("\n✅ Data Flow Guardian stopped")
        
if __name__ == "__main__":
    guardian = DataFlowGuardian()
    guardian.monitor_loop()