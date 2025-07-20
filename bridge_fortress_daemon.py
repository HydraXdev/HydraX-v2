#!/usr/bin/env python3
"""
BRIDGE FORTRESS DAEMON - Hardened Bridge with Heartbeat
Bulletproof bridge monitoring and resilience system
"""

import time
import json
import logging
import datetime
from pathlib import Path
from production_bridge_tunnel import get_production_tunnel

class BridgeFortressDaemon:
    """Hardened bridge daemon with heartbeat and resilience"""
    
    def __init__(self):
        self.heartbeat_file = Path("/var/run/bridge_troll_heartbeat.txt")
        self.status_file = Path("/var/run/bridge_troll_status.json")
        self.heartbeat_interval = 30  # seconds
        self.last_heartbeat = None
        
        # Get production tunnel
        self.tunnel = get_production_tunnel()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - BRIDGE_FORTRESS - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/bridge_fortress.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BRIDGE_FORTRESS")
        
        self.logger.info("🏰 BRIDGE FORTRESS DAEMON DEPLOYED")
        self.logger.info("🛡️ MISSION: BULLETPROOF BRIDGE RESILIENCE")
        
    def write_heartbeat(self):
        """Write heartbeat pulse every 30 seconds"""
        try:
            now = datetime.datetime.utcnow()
            heartbeat_data = {
                "timestamp": now.isoformat() + "Z",
                "status": "ALIVE",
                "daemon": "BRIDGE_FORTRESS",
                "uptime_seconds": int((now - self.start_time).total_seconds()) if hasattr(self, 'start_time') else 0
            }
            
            # Write heartbeat file
            with open(self.heartbeat_file, "w") as hb:
                hb.write(f"[HEARTBEAT] {heartbeat_data['timestamp']}\n")
            
            # Write detailed status
            status_data = {
                **heartbeat_data,
                "bridge_health": self.get_bridge_health(),
                "system_status": "OPERATIONAL"
            }
            
            with open(self.status_file, "w") as sf:
                json.dump(status_data, sf, indent=2)
            
            self.last_heartbeat = now
            self.logger.info(f"💓 HEARTBEAT: {heartbeat_data['timestamp']}")
            
        except Exception as e:
            self.logger.error(f"❌ Heartbeat write failed: {e}")
    
    def get_bridge_health(self):
        """Get comprehensive bridge health status"""
        try:
            status = self.tunnel.get_bridge_status()
            return {
                "aws_bridge": status["bridge_tunnel"]["status"],
                "response_time": status["bridge_health"]["response_time"],
                "signal_files": status["bridge_health"]["signal_files_count"],
                "server": status["connection_details"]["server"],
                "port": status["connection_details"]["primary_port"]
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "ERROR"
            }
    
    def monitor_and_maintain(self):
        """Main monitoring and maintenance loop"""
        self.logger.info("🔄 Starting bridge monitoring loop")
        
        while True:
            try:
                # Write heartbeat
                self.write_heartbeat()
                
                # Test bridge connectivity
                health = self.get_bridge_health()
                if health.get("status") == "ERROR":
                    self.logger.warning(f"⚠️ Bridge health warning: {health.get('error')}")
                
                # Sleep until next heartbeat
                time.sleep(self.heartbeat_interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Bridge fortress daemon stopped by user")
                break
            except Exception as e:
                self.logger.error(f"💥 Monitor loop error: {e}")
                time.sleep(5)  # Brief pause before retry
    
    def run(self):
        """Run the bridge fortress daemon"""
        self.start_time = datetime.datetime.utcnow()
        
        try:
            self.logger.info("🚀 BRIDGE FORTRESS DAEMON ONLINE")
            self.logger.info(f"💓 Heartbeat interval: {self.heartbeat_interval} seconds")
            self.logger.info(f"📁 Heartbeat file: {self.heartbeat_file}")
            self.logger.info(f"📊 Status file: {self.status_file}")
            
            # Write initial heartbeat
            self.write_heartbeat()
            
            # Start monitoring
            self.monitor_and_maintain()
            
        except Exception as e:
            self.logger.error(f"💥 Bridge fortress daemon crashed: {e}")
            raise

def main():
    """Main entry point for bridge fortress daemon"""
    daemon = BridgeFortressDaemon()
    daemon.run()

if __name__ == "__main__":
    main()