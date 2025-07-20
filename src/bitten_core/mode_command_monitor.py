#!/usr/bin/env python3
"""
Mode Command Health Monitor
Continuous monitoring system for fire mode command stability
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModeCommandMonitor:
    """Monitors and maintains fire mode command health"""
    
    def __init__(self):
        self.health_log_path = "/root/HydraX-v2/data/mode_command_health.log"
        self.last_check = None
        self.consecutive_failures = 0
        self.max_failures = 3  # Trigger emergency recovery after 3 failures
    
    def check_database_health(self) -> Dict[str, any]:
        """Check fire mode database health"""
        try:
            from .fire_mode_database import fire_mode_db
            
            # Test basic operations
            test_user = "health_check_user"
            
            # Test get operation
            mode_info = fire_mode_db.get_user_mode(test_user)
            
            # Test set operation
            result = fire_mode_db.set_user_mode(test_user, "SELECT", "Health check")
            
            if result and mode_info:
                return {"status": "healthy", "message": "Database operations successful"}
            else:
                return {"status": "degraded", "message": "Database operations partially failed"}
                
        except Exception as e:
            return {"status": "critical", "message": f"Database error: {str(e)}"}
    
    def check_handler_imports(self) -> Dict[str, any]:
        """Check if fire mode handlers can be imported"""
        try:
            from .fire_mode_handlers import FireModeHandlers
            from .fire_mode_executor import fire_mode_executor
            
            # Test a simple validation
            valid, _ = FireModeHandlers.validate_fire_mode_access("COMMANDER", "AUTO")
            
            if valid:
                return {"status": "healthy", "message": "All handlers imported and functional"}
            else:
                return {"status": "degraded", "message": "Handlers imported but validation failed"}
                
        except ImportError as e:
            return {"status": "critical", "message": f"Import error: {str(e)}"}
        except Exception as e:
            return {"status": "degraded", "message": f"Handler error: {str(e)}"}
    
    def check_threshold_consistency(self) -> Dict[str, any]:
        """Check TCS threshold consistency across modules"""
        try:
            from ..config.fire_mode_config import FireModeConfig
            
            # Verify expected threshold
            sniper_threshold = FireModeConfig.TCS_THRESHOLDS.get("SNIPER_OPS", 0)
            
            if sniper_threshold == 87:
                return {"status": "healthy", "message": "TCS thresholds consistent"}
            else:
                return {"status": "warning", "message": f"Unexpected SNIPER_OPS threshold: {sniper_threshold}%"}
                
        except Exception as e:
            return {"status": "warning", "message": f"Threshold check failed: {str(e)}"}
    
    def run_health_check(self) -> Dict[str, any]:
        """Run comprehensive health check"""
        self.last_check = datetime.now()
        
        checks = {
            "database": self.check_database_health(),
            "handlers": self.check_handler_imports(),
            "thresholds": self.check_threshold_consistency()
        }
        
        # Determine overall health
        critical_count = sum(1 for check in checks.values() if check["status"] == "critical")
        degraded_count = sum(1 for check in checks.values() if check["status"] == "degraded")
        warning_count = sum(1 for check in checks.values() if check["status"] == "warning")
        
        if critical_count > 0:
            overall_status = "critical"
            self.consecutive_failures += 1
        elif degraded_count > 0:
            overall_status = "degraded"
            self.consecutive_failures += 1
        elif warning_count > 0:
            overall_status = "warning"
            self.consecutive_failures = 0  # Reset on non-critical issues
        else:
            overall_status = "healthy"
            self.consecutive_failures = 0
        
        result = {
            "timestamp": self.last_check.isoformat(),
            "overall_status": overall_status,
            "consecutive_failures": self.consecutive_failures,
            "checks": checks
        }
        
        # Log result
        self.log_health_check(result)
        
        # Trigger emergency recovery if needed
        if self.consecutive_failures >= self.max_failures:
            self.trigger_emergency_recovery()
        
        return result
    
    def log_health_check(self, result: Dict[str, any]):
        """Log health check result"""
        try:
            os.makedirs(os.path.dirname(self.health_log_path), exist_ok=True)
            
            with open(self.health_log_path, "a") as f:
                f.write(f"{result['timestamp']} - {result['overall_status'].upper()}")
                
                if result['overall_status'] != 'healthy':
                    f.write(f" - Failures: {result['consecutive_failures']}")
                    
                for check_name, check_result in result['checks'].items():
                    if check_result['status'] != 'healthy':
                        f.write(f" | {check_name}: {check_result['status']} - {check_result['message']}")
                
                f.write("\n")
                
        except Exception as e:
            logger.error(f"Failed to log health check: {e}")
    
    def trigger_emergency_recovery(self):
        """Trigger emergency recovery procedures"""
        logger.critical(f"MODE COMMAND EMERGENCY: {self.consecutive_failures} consecutive failures detected")
        
        try:
            # Attempt database repair
            self.repair_database()
            
            # Reset failure counter after attempted repair
            self.consecutive_failures = 0
            
            logger.info("Emergency recovery procedures completed")
            
        except Exception as e:
            logger.error(f"Emergency recovery failed: {e}")
    
    def repair_database(self):
        """Attempt to repair database issues"""
        try:
            from .fire_mode_database import FireModeDatabase
            
            # Reinitialize database
            db = FireModeDatabase()
            db.init_database()
            
            logger.info("Database repair completed")
            
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            raise
    
    def get_health_summary(self) -> str:
        """Get formatted health summary"""
        if not self.last_check:
            return "❓ Mode command health: Not checked yet"
        
        result = self.run_health_check()
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "degraded": "🔶",
            "critical": "🔴"
        }
        
        emoji = status_emoji.get(result['overall_status'], "❓")
        
        summary = f"{emoji} Mode command health: {result['overall_status'].upper()}"
        
        if result['consecutive_failures'] > 0:
            summary += f" (Failures: {result['consecutive_failures']})"
        
        return summary

# Singleton instance
mode_command_monitor = ModeCommandMonitor()