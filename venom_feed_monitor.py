#!/usr/bin/env python3
"""
VENOM Feed Monitor - Maintains connection to hydrax_engine_node_v7
Ensures VENOM v7 receives continuous real-time tick data
"""

import time
import logging
import subprocess
import json
from datetime import datetime
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, '/root/HydraX-v2/src')
from venom_activity_logger import log_feed_monitor_start, log_feed_monitor_heartbeat, log_error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - VENOM-FEED - %(message)s')
logger = logging.getLogger(__name__)

class VenomFeedMonitor:
    """Monitors and maintains VENOM v7 connection to signal feed terminal"""
    
    def __init__(self):
        self.container_name = "hydrax_engine_node_v7"
        self.feed_type = "engine_feed"
        self.status_file = "/root/HydraX-v2/venom_feed_status.json"
        
        logger.info("🧠 VENOM Feed Monitor initialized")
        logger.info(f"📡 Monitoring container: {self.container_name}")
        logger.info(f"🎯 Purpose: 24/7 real-time tick data for VENOM v7")
        
        # Log startup to heartbeat system
        log_feed_monitor_start(self.container_name, "initialized")
    
    def check_container_health(self):
        """Check if feed container is healthy"""
        try:
            result = subprocess.run([
                'docker', 'ps', '--filter', f'name={self.container_name}', 
                '--format', '{{.Status}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and 'Up' in result.stdout:
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Container health check failed: {e}")
            return False
    
    def check_mt5_active(self):
        """Verify MT5 is running and connected"""
        try:
            result = subprocess.run([
                'docker', 'exec', self.container_name, 
                'ps', 'aux'
            ], capture_output=True, text=True)
            
            if 'terminal64.exe' in result.stdout:
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ MT5 check failed: {e}")
            return False
    
    def check_tick_data_flow(self):
        """Verify tick data is flowing (simplified check)"""
        try:
            # Check if charts are loaded
            result = subprocess.run([
                'docker', 'exec', self.container_name,
                'ls', '/wine/drive_c/MetaTrader5/Profiles/LastProfile/charts/'
            ], capture_output=True, text=True)
            
            chart_count = len(result.stdout.strip().split('\n'))
            return chart_count >= 15
            
        except Exception as e:
            logger.error(f"❌ Tick data check failed: {e}")
            return False
    
    def restart_mt5_if_needed(self):
        """Restart MT5 if it's not running"""
        try:
            logger.warning("⚠️ Restarting MT5 in feed container...")
            
            subprocess.run([
                'docker', 'exec', self.container_name,
                'bash', '-c', 
                'DISPLAY=:99 nohup wine "/wine/drive_c/Program Files/MetaTrader 5/terminal64.exe" /portable >/dev/null 2>&1 &'
            ], check=True)
            
            time.sleep(10)  # Allow startup time
            logger.info("✅ MT5 restart attempt completed")
            
        except Exception as e:
            logger.error(f"❌ MT5 restart failed: {e}")
    
    def update_status(self, status_data):
        """Update feed status file"""
        try:
            status_data['last_updated'] = datetime.now().isoformat()
            status_data['container'] = self.container_name
            status_data['type'] = self.feed_type
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Status update failed: {e}")
    
    def monitor_feed(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting VENOM feed monitoring...")
        
        # Log monitor start
        log_feed_monitor_start(self.container_name, "monitoring_started")
        
        while True:
            try:
                # Check container health
                container_healthy = self.check_container_health()
                mt5_active = self.check_mt5_active()
                tick_flow = self.check_tick_data_flow()
                
                status = {
                    'container_healthy': container_healthy,
                    'mt5_active': mt5_active,
                    'tick_data_flowing': tick_flow,
                    'overall_status': 'healthy' if all([container_healthy, mt5_active, tick_flow]) else 'degraded'
                }
                
                # Log status
                if status['overall_status'] == 'healthy':
                    logger.info("✅ VENOM Feed: HEALTHY - Tick data flowing")
                else:
                    logger.warning(f"⚠️ VENOM Feed: DEGRADED - Container:{container_healthy} MT5:{mt5_active} Ticks:{tick_flow}")
                
                # Attempt recovery if needed
                if container_healthy and not mt5_active:
                    self.restart_mt5_if_needed()
                
                # Update status file
                self.update_status(status)
                
                # Log heartbeat to VENOM activity logger
                log_feed_monitor_heartbeat(self.container_name, status)
                
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")
                log_error("VenomFeedMonitor", f"Monitor loop error: {e}", {"container": self.container_name})
                time.sleep(30)

def main():
    """Main function"""
    monitor = VenomFeedMonitor()
    monitor.monitor_feed()

if __name__ == "__main__":
    main()