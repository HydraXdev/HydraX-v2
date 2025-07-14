"""
Enhanced Error Handling Integration for BITTEN
Integrates error handling, recovery, and monitoring systems
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .enhanced_error_handling import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity,
    global_error_handler, handle_errors, get_system_health
)
from .recovery_strategies import (
    recovery_manager, recover_database_issues,
    recover_network_issues, recover_telegram_issues,
    recover_webapp_issues, recover_system_issues
)
from .system_monitor import (
    system_monitor, start_system_monitoring,
    get_monitoring_status, force_monitoring_check
)
from .webapp_error_handlers import setup_webapp_error_handling

logger = logging.getLogger("bitten_integration")


class IntegratedErrorSystem:
    """Integrated error handling, recovery, and monitoring system"""
    
    def __init__(self):
        self.error_handler = global_error_handler
        self.recovery_manager = recovery_manager
        self.system_monitor = system_monitor
        self.auto_recovery_enabled = True
        self.monitoring_enabled = True
        self._setup_integrations()
    
    def _setup_integrations(self):
        """Setup integrations between systems"""
        # Register recovery strategies with error handler
        self.error_handler.recovery_registry.register_strategy(
            "DATABASE_CONNECTION_FAILED",
            lambda context: recover_database_issues(context.get("db_path", "")).get("success", False)
        )
        
        self.error_handler.recovery_registry.register_strategy(
            "NETWORK_TIMEOUT",
            lambda context: recover_network_issues().get("success", False)
        )
        
        self.error_handler.recovery_registry.register_strategy(
            "TELEGRAM_API_ERROR",
            lambda context: recover_telegram_issues(context.get("bot_token", "")).get("success", False)
        )
        
        self.error_handler.recovery_registry.register_strategy(
            "WEBAPP_SERVER_ERROR",
            lambda context: recover_webapp_issues().get("success", False)
        )
    
    def initialize_system(self):
        """Initialize the complete error handling system"""
        try:
            # Start monitoring if enabled
            if self.monitoring_enabled:
                self.system_monitor.start_monitoring()
                logger.info("System monitoring started")
            
            # Setup directories
            os.makedirs("data", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            
            # Initialize databases
            self.error_handler.setup_database()
            
            logger.info("Integrated error system initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize integrated error system: {e}")
            return False
    
    def shutdown_system(self):
        """Shutdown the error handling system"""
        try:
            if self.monitoring_enabled:
                self.system_monitor.stop_monitoring()
                logger.info("System monitoring stopped")
            
            logger.info("Integrated error system shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")
    
    def handle_critical_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle critical errors with full recovery attempt"""
        # Log the critical error
        result = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            error_code="CRITICAL_SYSTEM_ERROR",
            context=context
        )
        
        # If auto-recovery is enabled, attempt system-wide recovery
        if self.auto_recovery_enabled and not result.get("success", False):
            logger.warning("Attempting system-wide recovery for critical error")
            
            recovery_results = []
            
            # Try database recovery
            db_result = recover_database_issues(context.get("db_path", "data/engagement.db"))
            recovery_results.append(("database", db_result))
            
            # Try network recovery
            network_result = recover_network_issues()
            recovery_results.append(("network", network_result))
            
            # Try webapp recovery
            webapp_result = recover_webapp_issues()
            recovery_results.append(("webapp", webapp_result))
            
            # Try system recovery
            system_result = recover_system_issues()
            recovery_results.append(("system", system_result))
            
            # Check if any recovery succeeded
            any_success = any(result[1].get("success", False) for result in recovery_results)
            
            if any_success:
                logger.info("System recovery partially successful")
                result["system_recovery_attempted"] = True
                result["recovery_results"] = recovery_results
            else:
                logger.error("System recovery failed completely")
                result["system_recovery_failed"] = True
        
        return result
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including all subsystems"""
        try:
            # Get error handling stats
            error_stats = self.error_handler.get_error_stats(hours=24)
            
            # Get recovery status
            recovery_status = self.recovery_manager.get_recovery_status()
            
            # Get monitoring status
            monitoring_status = get_monitoring_status()
            
            # Get overall health
            health = get_system_health()
            
            # Calculate overall system score
            error_score = max(0, 100 - (error_stats.get("total_errors", 0) * 2))
            recovery_score = min(100, error_stats.get("recovery_success_rate", 0) + 20)
            monitoring_score = 100 if monitoring_status.get("monitoring_active", False) else 50
            
            overall_score = (error_score + recovery_score + monitoring_score) / 3
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_score": round(overall_score, 1),
                "status": "healthy" if overall_score >= 80 else 
                         "warning" if overall_score >= 60 else "critical",
                "subsystems": {
                    "error_handling": {
                        "status": "active",
                        "stats": error_stats,
                        "score": error_score
                    },
                    "recovery_system": {
                        "status": "active",
                        "info": recovery_status,
                        "score": recovery_score
                    },
                    "monitoring": {
                        "status": "active" if self.monitoring_enabled else "disabled",
                        "info": monitoring_status,
                        "score": monitoring_score
                    }
                },
                "health_summary": health,
                "auto_recovery_enabled": self.auto_recovery_enabled,
                "monitoring_enabled": self.monitoring_enabled
            }
        
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_score": 0,
                "status": "error",
                "error": str(e)
            }
    
    def run_system_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": [],
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Test database connectivity
            test_result = self._test_database_connectivity()
            diagnostics["tests_run"].append("database_connectivity")
            if not test_result["success"]:
                diagnostics["issues_found"].append(test_result["error"])
                diagnostics["recommendations"].append("Run database recovery")
            
            # Test network connectivity
            test_result = self._test_network_connectivity()
            diagnostics["tests_run"].append("network_connectivity")
            if not test_result["success"]:
                diagnostics["issues_found"].append(test_result["error"])
                diagnostics["recommendations"].append("Check internet connection")
            
            # Test webapp availability
            test_result = self._test_webapp_availability()
            diagnostics["tests_run"].append("webapp_availability")
            if not test_result["success"]:
                diagnostics["issues_found"].append(test_result["error"])
                diagnostics["recommendations"].append("Restart webapp server")
            
            # Check system resources
            test_result = self._check_system_resources()
            diagnostics["tests_run"].append("system_resources")
            if not test_result["success"]:
                diagnostics["issues_found"].append(test_result["error"])
                diagnostics["recommendations"].append("Free up system resources")
            
            # Check error rates
            test_result = self._check_error_rates()
            diagnostics["tests_run"].append("error_rates")
            if not test_result["success"]:
                diagnostics["issues_found"].append(test_result["error"])
                diagnostics["recommendations"].append("Investigate high error rates")
            
            diagnostics["overall_health"] = "good" if len(diagnostics["issues_found"]) == 0 else \
                                          "fair" if len(diagnostics["issues_found"]) <= 2 else "poor"
            
        except Exception as e:
            diagnostics["diagnostic_error"] = str(e)
            diagnostics["overall_health"] = "unknown"
        
        return diagnostics
    
    def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity"""
        try:
            import sqlite3
            
            db_paths = [
                "data/engagement.db",
                "data/battle_pass.db",
                "data/error_tracking.db"
            ]
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path, timeout=5)
                    conn.execute("SELECT 1")
                    conn.close()
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": f"Database connectivity failed: {e}"}
    
    def _test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity"""
        try:
            import requests
            
            response = requests.get("https://8.8.8.8", timeout=5)
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": f"Network connectivity failed: {e}"}
    
    def _test_webapp_availability(self) -> Dict[str, Any]:
        """Test webapp availability"""
        try:
            import requests
            
            response = requests.get("http://localhost:8888/health", timeout=5)
            if response.status_code in [200, 503]:
                return {"success": True}
            else:
                return {"success": False, "error": f"Webapp returned status {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": f"Webapp not available: {e}"}
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                return {"success": False, "error": f"High CPU usage: {cpu_percent}%"}
            
            # Check memory
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return {"success": False, "error": f"High memory usage: {memory.percent}%"}
            
            # Check disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                return {"success": False, "error": f"High disk usage: {disk_percent:.1f}%"}
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": f"Resource check failed: {e}"}
    
    def _check_error_rates(self) -> Dict[str, Any]:
        """Check recent error rates"""
        try:
            stats = self.error_handler.get_error_stats(hours=1)
            
            total_errors = stats.get("total_errors", 0)
            if total_errors > 20:  # More than 20 errors in last hour
                return {"success": False, "error": f"High error rate: {total_errors} errors in last hour"}
            
            critical_errors = stats.get("by_severity", {}).get("critical", 0)
            if critical_errors > 0:
                return {"success": False, "error": f"Critical errors detected: {critical_errors}"}
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": f"Error rate check failed: {e}"}


# Global integrated system instance
integrated_system = IntegratedErrorSystem()


def initialize_error_system():
    """Initialize the complete error handling system"""
    return integrated_system.initialize_system()


def shutdown_error_system():
    """Shutdown the error handling system"""
    integrated_system.shutdown_system()


def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    return integrated_system.get_comprehensive_status()


def run_diagnostics() -> Dict[str, Any]:
    """Run system diagnostics"""
    return integrated_system.run_system_diagnostics()


def handle_critical_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle critical errors with full recovery"""
    return integrated_system.handle_critical_error(error, context)


def setup_flask_error_handling(app):
    """Setup Flask error handling integration"""
    # Setup webapp error handlers
    webapp_handler = setup_webapp_error_handling(app)
    
    # Add integration endpoints
    @app.route('/api/system/status')
    def system_status():
        return get_system_status()
    
    @app.route('/api/system/diagnostics')
    def system_diagnostics():
        return run_diagnostics()
    
    @app.route('/api/system/force-check')
    def force_system_check():
        return force_monitoring_check()
    
    return webapp_handler


# Auto-start monitoring when module is imported
if __name__ != "__main__":
    try:
        # Initialize on import
        initialize_error_system()
    except Exception as e:
        print(f"Failed to auto-initialize error system: {e}")


if __name__ == "__main__":
    # Test the integrated system
    print("Testing integrated error handling system...")
    
    # Initialize
    success = initialize_error_system()
    print(f"Initialization: {'Success' if success else 'Failed'}")
    
    # Run diagnostics
    diagnostics = run_diagnostics()
    print(f"Diagnostics: {diagnostics['overall_health']}")
    print(f"Issues found: {len(diagnostics['issues_found'])}")
    
    # Get status
    status = get_system_status()
    print(f"Overall score: {status['overall_score']}")
    print(f"Status: {status['status']}")
    
    # Test error handling
    try:
        raise ValueError("Test error for integrated system")
    except Exception as e:
        result = handle_critical_error(e, {"test": True})
        print(f"Error handling result: {result.get('success', False)}")
    
    # Shutdown
    shutdown_error_system()
    print("Test completed.")