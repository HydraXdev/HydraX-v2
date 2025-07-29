"""
BITTEN Centralized Logging System
Structured logging with ForexVPS monitoring
"""
import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import os

from config.settings import LOGGING_CONFIG
from database.models import get_db, log_system_event

class BittenFormatter(logging.Formatter):
    """Custom formatter for BITTEN logs"""
    
    def format(self, record):
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add module information
        record.module_name = record.name
        
        # Format exception info
        if record.exc_info:
            record.exception_details = self.formatException(record.exc_info)
        else:
            record.exception_details = None
        
        # Create structured log entry
        log_entry = {
            "timestamp": record.timestamp,
            "level": record.levelname,
            "module": record.module_name,
            "message": record.getMessage(),
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Add exception details if present
        if hasattr(record, 'exception_details') and record.exception_details:
            log_entry["exception"] = record.exception_details
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'forexvps_response'):
            log_entry["forexvps_response"] = record.forexvps_response
        
        return json.dumps(log_entry)

class DatabaseHandler(logging.Handler):
    """Custom handler to log to database"""
    
    def emit(self, record):
        try:
            # Get database session
            db = next(get_db())
            
            # Extract user_id if present
            user_id = getattr(record, 'user_id', None)
            
            # Create metadata
            metadata = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
            
            # Add extra fields
            if hasattr(record, 'request_id'):
                metadata["request_id"] = record.request_id
            
            if hasattr(record, 'forexvps_response'):
                metadata["forexvps_response"] = record.forexvps_response
            
            # Log to database
            log_system_event(
                db=db,
                level=record.levelname,
                module=record.name,
                message=record.getMessage(),
                user_id=user_id,
                metadata=metadata
            )
            
            db.close()
            
        except Exception as e:
            # Fallback to stderr if database logging fails
            print(f"Database logging failed: {e}", file=sys.stderr)

class BittenLogger:
    """BITTEN centralized logger"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(BittenFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_dir = Path("/var/log/bitten")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "application.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(BittenFormatter())
        self.logger.addHandler(file_handler)
        
        # Database handler for important logs
        db_handler = DatabaseHandler()
        db_handler.setLevel(logging.WARNING)  # Only warnings and errors to database
        self.logger.addHandler(db_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(BittenFormatter())
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with extra fields"""
        extra = {}
        
        # Add user context
        if 'user_id' in kwargs:
            extra['user_id'] = kwargs.pop('user_id')
        
        # Add request context
        if 'request_id' in kwargs:
            extra['request_id'] = kwargs.pop('request_id')
        
        # Add ForexVPS response context
        if 'forexvps_response' in kwargs:
            extra['forexvps_response'] = kwargs.pop('forexvps_response')
        
        # Format message with remaining kwargs
        if kwargs:
            message = message.format(**kwargs)
        
        self.logger.log(level, message, extra=extra)

class ForexVPSLogger(BittenLogger):
    """Specialized logger for ForexVPS operations"""
    
    def log_api_request(self, endpoint: str, request_data: Dict[str, Any], user_id: str = None):
        """Log ForexVPS API request"""
        self.info(
            "ForexVPS API Request: {endpoint}",
            endpoint=endpoint,
            user_id=user_id,
            request_data=request_data
        )
    
    def log_api_response(self, endpoint: str, response_data: Dict[str, Any], 
                        response_time: int, user_id: str = None):
        """Log ForexVPS API response"""
        self.info(
            "ForexVPS API Response: {endpoint} ({response_time}ms)",
            endpoint=endpoint,
            response_time=response_time,
            user_id=user_id,
            forexvps_response=response_data
        )
    
    def log_api_error(self, endpoint: str, error: str, user_id: str = None):
        """Log ForexVPS API error"""
        self.error(
            "ForexVPS API Error: {endpoint} - {error}",
            endpoint=endpoint,
            error=error,
            user_id=user_id
        )
    
    def log_trade_execution(self, user_id: str, symbol: str, direction: str, 
                           result: Dict[str, Any]):
        """Log trade execution"""
        if result.get("status") == "success":
            self.info(
                "Trade executed successfully: {user_id} {symbol} {direction}",
                user_id=user_id,
                symbol=symbol,
                direction=direction,
                forexvps_response=result
            )
        else:
            self.error(
                "Trade execution failed: {user_id} {symbol} {direction} - {error}",
                user_id=user_id,
                symbol=symbol,
                direction=direction,
                error=result.get("error_message", "Unknown error"),
                forexvps_response=result
            )

class SecurityLogger(BittenLogger):
    """Specialized logger for security events"""
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str = None):
        """Log authentication attempt"""
        if success:
            self.info(
                "Authentication successful: {user_id}",
                user_id=user_id,
                ip_address=ip_address
            )
        else:
            self.warning(
                "Authentication failed: {user_id}",
                user_id=user_id,
                ip_address=ip_address
            )
    
    def log_authorization_failure(self, user_id: str, resource: str, required_tier: str):
        """Log authorization failure"""
        self.warning(
            "Authorization failed: {user_id} attempted to access {resource} (requires {required_tier})",
            user_id=user_id,
            resource=resource,
            required_tier=required_tier
        )
    
    def log_rate_limit_exceeded(self, user_id: str, endpoint: str):
        """Log rate limit exceeded"""
        self.warning(
            "Rate limit exceeded: {user_id} on {endpoint}",
            user_id=user_id,
            endpoint=endpoint
        )
    
    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.critical(
            "Suspicious activity detected: {user_id} - {activity}",
            user_id=user_id,
            activity=activity,
            **details
        )

# Logger factory
def get_logger(name: str) -> BittenLogger:
    """Get logger instance"""
    return BittenLogger(name)

def get_forexvps_logger() -> ForexVPSLogger:
    """Get ForexVPS logger instance"""
    return ForexVPSLogger("forexvps")

def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return SecurityLogger("security")

# Global loggers
app_logger = get_logger("bitten.app")
forexvps_logger = get_forexvps_logger()
security_logger = get_security_logger()

# Utility functions
def log_exception(logger: BittenLogger, message: str, **kwargs):
    """Log exception with traceback"""
    exc_info = traceback.format_exc()
    logger.error(f"{message}\nTraceback: {exc_info}", **kwargs)

def setup_logging():
    """Setup logging configuration"""
    # Create log directory
    log_dir = Path("/var/log/bitten")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set root logger level
    logging.getLogger().setLevel(logging.INFO)
    
    # Disable some noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    app_logger.info("Logging system initialized")

# Performance monitoring
class PerformanceLogger:
    """Performance monitoring logger"""
    
    def __init__(self):
        self.logger = get_logger("bitten.performance")
    
    def log_request_time(self, endpoint: str, response_time: float, user_id: str = None):
        """Log request response time"""
        self.logger.info(
            "Request completed: {endpoint} ({response_time:.3f}s)",
            endpoint=endpoint,
            response_time=response_time,
            user_id=user_id
        )
    
    def log_database_query(self, query: str, execution_time: float):
        """Log database query performance"""
        self.logger.debug(
            "Database query: {query} ({execution_time:.3f}s)",
            query=query[:100],  # Truncate long queries
            execution_time=execution_time
        )
    
    def log_forexvps_latency(self, endpoint: str, latency: float, user_id: str = None):
        """Log ForexVPS API latency"""
        if latency > 1.0:  # Log slow requests
            self.logger.warning(
                "Slow ForexVPS response: {endpoint} ({latency:.3f}s)",
                endpoint=endpoint,
                latency=latency,
                user_id=user_id
            )

performance_logger = PerformanceLogger()