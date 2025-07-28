"""
Centralized Logging Configuration for HydraX v2
Configures logging for all components including engagement system and fusion dashboard
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )
        
        # Add color to logger name
        if hasattr(record, 'name'):
            record.name = f"{self.COLORS['DEBUG']}{record.name}{self.COLORS['RESET']}"
        
        return super().format(record)

class StructuredFormatter(logging.Formatter):
    """Structured formatter for log files"""
    
    def format(self, record):
        """Format log record with structured data"""
        # Add timestamp
        record.timestamp = datetime.now().isoformat()
        
        # Add component info
        if hasattr(record, 'component'):
            record.component = record.component
        else:
            record.component = record.name.split('.')[-1]
        
        # Add process info
        record.process_name = record.processName
        record.thread_name = record.threadName
        
        return super().format(record)

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_structured: bool = True,
    max_file_size: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 5
) -> Dict[str, Any]:
    """
    Setup centralized logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/hydrax.log)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_structured: Enable structured logging
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Dictionary with logging configuration details
    """
    
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Set default log file
    if log_file is None:
        log_file = LOGS_DIR / "hydrax.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        if enable_structured:
            console_format = (
                "%(asctime)s | %(levelname)-8s | %(component)-15s | "
                "%(filename)s:%(lineno)d | %(message)s"
            )
            console_formatter = ColoredFormatter(console_format)
        else:
            console_formatter = ColoredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        handlers.append(("console", console_handler))
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        if enable_structured:
            file_format = (
                "%(timestamp)s | %(levelname)-8s | %(component)-15s | "
                "%(process_name)s:%(thread_name)s | %(filename)s:%(lineno)d | "
                "%(funcName)s | %(message)s"
            )
            file_formatter = StructuredFormatter(file_format)
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        handlers.append(("file", file_handler))
    
    # Component-specific loggers
    component_loggers = setup_component_loggers(log_level)
    
    # Create separate log files for specific components
    component_files = {}
    if enable_file:
        component_files = setup_component_files(log_level, max_file_size, backup_count)
    
    config = {
        "level": level,
        "log_file": str(log_file),
        "handlers": handlers,
        "component_loggers": component_loggers,
        "component_files": component_files,
        "structured_logging": enable_structured,
        "setup_time": datetime.now().isoformat()
    }
    
    # Log the configuration
    logger = logging.getLogger("logging_config")
    logger.info(f"Logging configured: level={level}, file={log_file}, structured={enable_structured}")
    logger.info(f"Component loggers: {list(component_loggers.keys())}")
    
    return config

def setup_component_loggers(base_level: int) -> Dict[str, logging.Logger]:
    """Setup loggers for specific components"""
    
    components = {
        # Core components
        "engagement_system": logging.INFO,
        "fusion_dashboard": logging.INFO,
        "database": logging.WARNING,
        "cache": logging.WARNING,
        
        # Bitten core components
        "bitten_core": logging.INFO,
        "signal_fusion": logging.INFO,
        "trading_engine": logging.INFO,
        "risk_management": logging.INFO,
        
        # Infrastructure
        "webapp": logging.INFO,
        "telegram_bot": logging.INFO,
        "webhook_server": logging.INFO,
        "mt5_bridge": logging.INFO,
        
        # Third party (more restrictive)
        "sqlalchemy": logging.WARNING,
        "flask": logging.WARNING,
        "socketio": logging.WARNING,
        "requests": logging.WARNING,
        "urllib3": logging.WARNING,
        "werkzeug": logging.WARNING,
        
        # Test components
        "test_engagement": logging.DEBUG,
        "test_fusion": logging.DEBUG}
    
    loggers = {}
    
    for component, level in components.items():
        logger = logging.getLogger(component)
        logger.setLevel(min(base_level, level))
        loggers[component] = logger
    
    return loggers

def setup_component_files(
    base_level: int,
    max_file_size: int,
    backup_count: int
) -> Dict[str, logging.handlers.RotatingFileHandler]:
    """Setup separate log files for specific components"""
    
    component_files = {
        "engagement_system": LOGS_DIR / "engagement.log",
        "fusion_dashboard": LOGS_DIR / "fusion_dashboard.log",
        "database": LOGS_DIR / "database.log",
        "trading_engine": LOGS_DIR / "trading.log",
        "webapp": LOGS_DIR / "webapp.log",
        "telegram_bot": LOGS_DIR / "telegram.log",
        "errors": LOGS_DIR / "errors.log"}
    
    handlers = {}
    
    for component, file_path in component_files.items():
        # Create handler
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set level
        if component == "errors":
            handler.setLevel(logging.ERROR)
        else:
            handler.setLevel(base_level)
        
        # Set formatter
        formatter = StructuredFormatter(
            "%(timestamp)s | %(levelname)-8s | %(component)-15s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )
        handler.setFormatter(formatter)
        
        # Add to specific logger
        logger = logging.getLogger(component)
        logger.addHandler(handler)
        
        handlers[component] = handler
    
    # Add error handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handlers["errors"])
    
    return handlers

def get_logger(name: str, component: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional component tagging
    
    Args:
        name: Logger name
        component: Component name for tagging
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if component:
        # Add component info to all log records
        class ComponentFilter(logging.Filter):
            def filter(self, record):
                record.component = component
                return True
        
        logger.addFilter(ComponentFilter())
    
    return logger

def log_system_info():
    """Log system information for debugging"""
    logger = get_logger("system_info", "startup")
    
    logger.info("=== HydraX v2 System Information ===")
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Log directory: {LOGS_DIR}")
    logger.info(f"Process ID: {os.getpid()}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Log important environment variables
    env_vars = [
        'ENGAGEMENT_DB_URL',
        'ENGAGEMENT_LOG_LEVEL',
        'ENGAGEMENT_DEBUG',
        'REDIS_URL',
        'FUSION_DASHBOARD_PORT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive information
            if 'url' in var.lower() or 'password' in var.lower():
                value = '***masked***'
            logger.info(f"{var}: {value}")
    
    logger.info("=== End System Information ===")

def setup_error_reporting():
    """Setup error reporting and monitoring"""
    logger = get_logger("error_reporting", "monitoring")
    
    # Custom error handler
    class ErrorReportingHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                # Log critical errors with additional context
                logger.error(f"Critical error in {record.name}: {record.getMessage()}")
                
                # Add stack trace for exceptions
                if record.exc_info:
                    import traceback
                    logger.error(f"Stack trace: {traceback.format_exception(*record.exc_info)}")
    
    # Add error reporting handler
    root_logger = logging.getLogger()
    root_logger.addHandler(ErrorReportingHandler())
    
    logger.info("Error reporting configured")

def configure_third_party_logging():
    """Configure logging for third-party libraries"""
    
    # Suppress noisy third-party loggers
    noisy_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'werkzeug',
        'socketio.client',
        'engineio.client']
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Configure SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    # Only show SQL queries in DEBUG mode
    if os.getenv('ENGAGEMENT_DEBUG', 'false').lower() == 'true':
        sqlalchemy_logger.setLevel(logging.INFO)

# Convenience functions for common logging patterns
def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None):
    """Log function call with arguments"""
    logger = get_logger("function_calls", "debug")
    
    args_str = ", ".join(str(arg) for arg in args)
    kwargs_str = ", ".join(f"{k}={v}" for k, v in (kwargs or {}).items())
    
    all_args = ", ".join(filter(None, [args_str, kwargs_str]))
    logger.debug(f"Calling {func_name}({all_args})")

def log_performance(operation: str, duration: float, **context):
    """Log performance metrics"""
    logger = get_logger("performance", "metrics")
    
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"Performance: {operation} took {duration:.3f}s | {context_str}")

def log_user_action(user_id: str, action: str, **details):
    """Log user actions for analytics"""
    logger = get_logger("user_actions", "analytics")
    
    details_str = ", ".join(f"{k}={v}" for k, v in details.items())
    logger.info(f"User {user_id} performed {action} | {details_str}")

# Default configuration
def setup_default_logging():
    """Setup default logging configuration"""
    level = os.getenv('ENGAGEMENT_LOG_LEVEL', 'INFO')
    debug = os.getenv('ENGAGEMENT_DEBUG', 'false').lower() == 'true'
    
    if debug:
        level = 'DEBUG'
    
    config = setup_logging(
        level=level,
        enable_console=True,
        enable_file=True,
        enable_structured=True
    )
    
    # Setup additional configurations
    configure_third_party_logging()
    setup_error_reporting()
    log_system_info()
    
    return config

# Export public interface
__all__ = [
    'setup_logging',
    'setup_default_logging',
    'get_logger',
    'log_system_info',
    'log_function_call',
    'log_performance',
    'log_user_action',
    'ColoredFormatter',
    'StructuredFormatter'
]

# Auto-setup if this module is imported
if __name__ != "__main__":
    # Only setup if not already configured
    if not logging.getLogger().handlers:
        setup_default_logging()