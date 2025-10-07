"""
BITTEN Monitoring System
Comprehensive production monitoring and alerting system.
"""

from .alert_system import AlertManager, get_alert_manager
from .dashboard import create_dashboard_app
from .health_check import HealthCheckManager, create_health_check_system
from .log_manager import LogManager, get_log_manager
from .logging_config import get_logging_config, setup_service_logging
from .performance_monitor import PerformanceMonitor, get_performance_monitor
from .win_rate_monitor import WinRateMonitor, get_win_rate_monitor

__version__ = "1.0.0"
__author__ = "BITTEN Trading System"

__all__ = [
    "setup_service_logging",
    "get_logging_config",
    "get_performance_monitor",
    "PerformanceMonitor",
    "create_health_check_system",
    "HealthCheckManager",
    "get_alert_manager",
    "AlertManager",
    "get_win_rate_monitor",
    "WinRateMonitor",
    "get_log_manager",
    "LogManager",
    "create_dashboard_app",
]
