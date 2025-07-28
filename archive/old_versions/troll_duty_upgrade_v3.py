#!/usr/bin/env python3
"""
🧌 BRIDGE TROLL DUTY UPGRADE V3.0
Enhanced monitoring with automatic bridge resurrection capabilities
"""

import time
import logging
import requests
import json
from datetime import datetime, timedelta
from bridge_resurrection_protocol import BridgeResurrectionProtocol

logger = logging.getLogger(__name__)

class TrollDutyUpgradeV3:
    """Enhanced Bridge Troll with resurrection capabilities"""
    
    def __init__(self):
        self.resurrection_protocol = BridgeResurrectionProtocol()
        self.troll_base_url = "http://localhost:8890"
        self.consecutive_failures = 0
        self.max_failures_before_resurrection = 3
        self.last_resurrection_attempt = None
        self.resurrection_cooldown_minutes = 10
        
    def enhanced_bridge_monitoring(self):
        """Enhanced monitoring with automatic resurrection"""
        try:
            # Get current bridge status from troll
            response = requests.get(f"{self.troll_base_url}/bridge_troll/port_map", timeout=5)
            port_map = response.json()
            
            # Count healthy bridges
            healthy_bridges = 0
            total_bridges = 0
            
            for port, status in port_map.get("bridge_ports", {}).items():
                total_bridges += 1
                if status.get("status") == "healthy":
                    healthy_bridges += 1
            
            # Check if resurrection is needed
            if healthy_bridges == 0:
                self.consecutive_failures += 1
                logger.warning(f"🚨 NO HEALTHY BRIDGES DETECTED (failure #{self.consecutive_failures})")
                
                if self._should_attempt_resurrection():
                    self._attempt_emergency_resurrection()
                    
            else:
                # Reset failure counter on success
                if self.consecutive_failures > 0:
                    logger.info(f"✅ Bridges restored - resetting failure counter")
                self.consecutive_failures = 0
            
            return {
                "healthy_bridges": healthy_bridges,
                "total_bridges": total_bridges,
                "consecutive_failures": self.consecutive_failures,
                "health_percentage": (healthy_bridges / max(total_bridges, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Enhanced monitoring failed: {e}")
            return {"error": str(e)}
    
    def _should_attempt_resurrection(self) -> bool:
        """Determine if resurrection should be attempted"""
        # Check failure threshold
        if self.consecutive_failures < self.max_failures_before_resurrection:
            return False
        
        # Check cooldown period
        if self.last_resurrection_attempt:
            time_since_last = datetime.now() - self.last_resurrection_attempt
            if time_since_last < timedelta(minutes=self.resurrection_cooldown_minutes):
                logger.info(f"⏰ Resurrection in cooldown ({self.resurrection_cooldown_minutes} min)")
                return False
        
        return True
    
    def _attempt_emergency_resurrection(self):
        """Attempt emergency bridge resurrection"""
        logger.error("🚨 INITIATING EMERGENCY BRIDGE RESURRECTION")
        
        try:
            self.last_resurrection_attempt = datetime.now()
            
            # Diagnose the failure
            diagnosis = self.resurrection_protocol.diagnose_bridge_failure()
            logger.info(f"🔍 Bridge diagnosis: {diagnosis}")
            
            if diagnosis["resurrection_needed"]:
                # Attempt resurrection
                result = self.resurrection_protocol.resurrect_critical_bridges()
                
                if result.get("success"):
                    logger.info("✅ EMERGENCY RESURRECTION SUCCESSFUL")
                    self.consecutive_failures = 0  # Reset on success
                    
                    # Notify monitoring systems
                    self._notify_resurrection_success(result)
                else:
                    logger.error("❌ EMERGENCY RESURRECTION FAILED")
                    self._notify_resurrection_failure(result)
            else:
                logger.info("ℹ️ Diagnosis indicates no resurrection needed")
                
        except Exception as e:
            logger.error(f"🚨 Resurrection protocol exception: {e}")
            self._notify_resurrection_failure({"error": str(e)})
    
    def _notify_resurrection_success(self, result: dict):
        """Notify systems of successful resurrection"""
        try:
            # Could add Telegram notification here
            logger.info(f"📢 Resurrection success notification: {result}")
        except Exception as e:
            logger.error(f"Failed to send resurrection success notification: {e}")
    
    def _notify_resurrection_failure(self, result: dict):
        """Notify systems of failed resurrection"""
        try:
            # Could add critical alert here
            logger.error(f"📢 CRITICAL: Resurrection failed notification: {result}")
        except Exception as e:
            logger.error(f"Failed to send resurrection failure notification: {e}")
    
    def get_troll_upgrade_status(self) -> dict:
        """Get status of the troll upgrade system"""
        return {
            "upgrade_version": "3.0",
            "consecutive_failures": self.consecutive_failures,
            "max_failures_threshold": self.max_failures_before_resurrection,
            "last_resurrection_attempt": self.last_resurrection_attempt.isoformat() if self.last_resurrection_attempt else None,
            "cooldown_minutes": self.resurrection_cooldown_minutes,
            "resurrection_protocol_active": True
        }

def continuous_enhanced_monitoring():
    """Continuous enhanced monitoring loop"""
    troll_upgrade = TrollDutyUpgradeV3()
    
    logger.info("🧌 BRIDGE TROLL DUTY UPGRADE V3.0 - ENHANCED MONITORING STARTED")
    
    while True:
        try:
            status = troll_upgrade.enhanced_bridge_monitoring()
            
            if status.get("healthy_bridges", 0) == 0:
                logger.warning(f"⚠️ Bridge health: {status}")
            else:
                logger.info(f"✅ Bridge health: {status.get('health_percentage', 0):.1f}%")
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    continuous_enhanced_monitoring()