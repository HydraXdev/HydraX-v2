"""
BITTEN Monitoring System
Comprehensive production monitoring and alerting system.
"""

from .logging_config import setup_service_logging, get_logging_config
from .performance_monitor import get_performance_monitor, PerformanceMonitor
from .health_check import create_health_check_system, HealthCheckManager
from .alert_system import get_alert_manager, AlertManager
from .win_rate_monitor import get_win_rate_monitor, WinRateMonitor
from .log_manager import get_log_manager, LogManager
from .dashboard import create_dashboard_app

__version__ = "1.0.0"
__author__ = "BITTEN Trading System"

__all__ = [
    'setup_service_logging',
    'get_logging_config',
    'get_performance_monitor',
    'PerformanceMonitor',
    'create_health_check_system',
    'HealthCheckManager',
    'get_alert_manager',
    'AlertManager',
    'get_win_rate_monitor',
    'WinRateMonitor',
    'get_log_manager',
    'LogManager',
    'create_dashboard_app'
]