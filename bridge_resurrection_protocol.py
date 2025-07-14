#!/usr/bin/env python3
"""
🛡️ BRIDGE RESURRECTION PROTOCOL
Automatically detects and revives failed bridge infrastructure
"""

import subprocess
import socket
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class BridgeResurrectionProtocol:
    """Emergency bridge revival system"""
    
    def __init__(self):
        self.required_bridges = [
            {"port": 9000, "bridge_id": "bridge_001", "priority": "critical"},
            {"port": 9001, "bridge_id": "bridge_002", "priority": "high"},
            {"port": 9002, "bridge_id": "bridge_003", "priority": "backup"}
        ]
        
    def diagnose_bridge_failure(self) -> Dict:
        """Comprehensive bridge failure analysis"""
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "total_bridges_expected": len(self.required_bridges),
            "bridges_alive": 0,
            "critical_bridges_down": 0,
            "failed_ports": [],
            "resurrection_needed": False
        }
        
        for bridge in self.required_bridges:
            port = bridge["port"]
            is_alive = self._check_port_alive(port)
            
            if not is_alive:
                diagnosis["failed_ports"].append({
                    "port": port,
                    "bridge_id": bridge["bridge_id"],
                    "priority": bridge["priority"]
                })
                
                if bridge["priority"] == "critical":
                    diagnosis["critical_bridges_down"] += 1
            else:
                diagnosis["bridges_alive"] += 1
        
        # Determine if resurrection needed
        if diagnosis["critical_bridges_down"] > 0 or diagnosis["bridges_alive"] == 0:
            diagnosis["resurrection_needed"] = True
            
        return diagnosis
    
    def _check_port_alive(self, port: int) -> bool:
        """Check if a port is alive and responding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2.0)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def resurrect_critical_bridges(self) -> Dict:
        """Resurrect failed bridge infrastructure"""
        logger.info("🚨 INITIATING BRIDGE RESURRECTION PROTOCOL")
        
        resurrection_log = {
            "started_at": datetime.now().isoformat(),
            "actions_taken": [],
            "bridges_revived": 0,
            "success": False
        }
        
        try:
            # 1. Kill any zombie bridge processes
            self._terminate_zombie_bridges(resurrection_log)
            
            # 2. Start fortress bridge system
            self._start_fortress_bridges(resurrection_log)
            
            # 3. Verify resurrection success
            time.sleep(5)  # Allow startup time
            verification = self._verify_resurrection()
            
            resurrection_log.update(verification)
            resurrection_log["completed_at"] = datetime.now().isoformat()
            
            if verification["success"]:
                logger.info("✅ BRIDGE RESURRECTION SUCCESSFUL")
            else:
                logger.error("❌ BRIDGE RESURRECTION FAILED")
                
        except Exception as e:
            resurrection_log["error"] = str(e)
            logger.error(f"🚨 Resurrection protocol failed: {e}")
            
        return resurrection_log
    
    def _terminate_zombie_bridges(self, log: Dict):
        """Terminate any stuck bridge processes"""
        try:
            # Kill fortress bridge processes
            result = subprocess.run(
                ["pkill", "-f", "fortress.*bridge"], 
                capture_output=True, text=True
            )
            log["actions_taken"].append("Terminated zombie bridge processes")
            
        except Exception as e:
            log["actions_taken"].append(f"Failed to terminate zombies: {e}")
    
    def _start_fortress_bridges(self, log: Dict):
        """Start the fortress bridge system"""
        try:
            # Start primary fortress bridge
            cmd = [
                "python3", "/root/HydraX-v2/fortress_spe.py", 
                "--bridge-id", "bridge_001",
                "--port", "9000"
            ]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            log["actions_taken"].append("Started fortress bridge bridge_001 on port 9000")
            
        except Exception as e:
            log["actions_taken"].append(f"Failed to start fortress bridge: {e}")
    
    def _verify_resurrection(self) -> Dict:
        """Verify that resurrection was successful"""
        verification = {
            "bridges_online": 0,
            "critical_online": 0,
            "success": False
        }
        
        for bridge in self.required_bridges:
            if self._check_port_alive(bridge["port"]):
                verification["bridges_online"] += 1
                if bridge["priority"] == "critical":
                    verification["critical_online"] += 1
        
        # Success if at least one critical bridge is online
        verification["success"] = verification["critical_online"] > 0
        
        return verification

def emergency_bridge_revival():
    """Emergency function to revive bridge infrastructure"""
    protocol = BridgeResurrectionProtocol()
    
    # Diagnose the failure
    diagnosis = protocol.diagnose_bridge_failure()
    print(f"🔍 Bridge Diagnosis: {json.dumps(diagnosis, indent=2)}")
    
    if diagnosis["resurrection_needed"]:
        # Attempt resurrection
        result = protocol.resurrect_critical_bridges()
        print(f"🛡️ Resurrection Result: {json.dumps(result, indent=2)}")
        return result
    else:
        print("✅ All critical bridges are operational")
        return {"success": True, "message": "No resurrection needed"}

if __name__ == "__main__":
    emergency_bridge_revival()