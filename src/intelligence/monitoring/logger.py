"""
Advanced logging system for intelligence components
Provides structured logging, performance tracking, and error monitoring
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, asdict
import time
from functools import wraps

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
component_var: ContextVar[Optional[str]] = ContextVar('component', default=None)

@dataclass
class LogContext:
    """Context information for structured logging"""
    request_id: Optional[str] = None
    component: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
        
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if available
        if self.include_context:
            request_id = request_id_var.get()
            component = component_var.get()
            if request_id:
                log_data['request_id'] = request_id
            if component:
                log_data['component'] = component
                
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data)

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._metrics: Dict[str, List[float]] = {}
        
    def log_timing(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log operation timing"""
        log_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            log_data['metadata'] = metadata
            
        self.logger.info("Performance metric", extra={'extra_fields': log_data})
        
        # Store for aggregation
        if operation not in self._metrics:
            self._metrics[operation] = []
        self._metrics[operation].append(duration)
        
    def get_metrics_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        if operation:
            metrics = self._metrics.get(operation, [])
            if not metrics:
                return {}
            return {
                'operation': operation,
                'count': len(metrics),
                'avg_ms': sum(metrics) / len(metrics) * 1000,
                'min_ms': min(metrics) * 1000,
                'max_ms': max(metrics) * 1000
            }
        else:
            summary = {}
            for op, metrics in self._metrics.items():
                if metrics:
                    summary[op] = {
                        'count': len(metrics),
                        'avg_ms': sum(metrics) / len(metrics) * 1000,
                        'min_ms': min(metrics) * 1000,
                        'max_ms': max(metrics) * 1000
                    }
            return summary

class IntelligenceLogger:
    """Main logger for intelligence system"""
    
    def __init__(self, name: str = "intelligence", config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self.performance = PerformanceLogger(self.logger)
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger with handlers and formatters"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level
        log_level = self.config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level))
        
        # Console handler
        if self.config.get('console_logging', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = StructuredFormatter() if self.config.get('structured_logs', True) else logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
        # File handler
        if self.config.get('file_logging', True):
            log_dir = Path(self.config.get('log_dir', 'logs/intelligence'))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = RotatingFileHandler(
                log_dir / f"{self.name}.log",
                maxBytes=self.config.get('max_log_size', 10 * 1024 * 1024),  # 10MB
                backupCount=self.config.get('backup_count', 5)
            )
            file_formatter = StructuredFormatter()
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Error file handler
            error_handler = RotatingFileHandler(
                log_dir / f"{self.name}_errors.log",
                maxBytes=self.config.get('max_log_size', 10 * 1024 * 1024),
                backupCount=self.config.get('backup_count', 5)
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            self.logger.addHandler(error_handler)
            
    def get_logger(self, component: str) -> logging.Logger:
        """Get logger for specific component"""
        return logging.getLogger(f"{self.name}.{component}")
        
    def set_context(self, **kwargs):
        """Set logging context"""
        if 'request_id' in kwargs:
            request_id_var.set(kwargs['request_id'])
        if 'component' in kwargs:
            component_var.set(kwargs['component'])
            
    def clear_context(self):
        """Clear logging context"""
        request_id_var.set(None)
        component_var.set(None)
        
    def log_event(self, event_type: str, event_data: Dict[str, Any], level: str = 'INFO'):
        """Log a structured event"""
        log_data = {
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.log(getattr(logging, level), f"Event: {event_type}", extra={'extra_fields': log_data})
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.error(f"Error occurred: {error}", exc_info=True, extra={'extra_fields': error_data})
        
    def log_metric(self, metric_name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Log a metric value"""
        metric_data = {
            'metric_name': metric_name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.info(f"Metric: {metric_name}={value}", extra={'extra_fields': metric_data})

def timed_operation(operation_name: Optional[str] = None):
    """Decorator to time function execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                name = operation_name or f"{func.__module__}.{func.__name__}"
                # Log timing if logger is available
                if hasattr(args[0], 'logger') and hasattr(args[0].logger, 'performance'):
                    args[0].logger.performance.log_timing(name, duration)
                    
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                name = operation_name or f"{func.__module__}.{func.__name__}"
                # Log timing if logger is available
                if hasattr(args[0], 'logger') and hasattr(args[0].logger, 'performance'):
                    args[0].logger.performance.log_timing(name, duration)
                    
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class LoggerManager:
    """Manages loggers for different components"""
    
    _instance = None
    _loggers: Dict[str, IntelligenceLogger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    @classmethod
    def get_logger(cls, name: str, config: Optional[Dict[str, Any]] = None) -> IntelligenceLogger:
        """Get or create logger for component"""
        if name not in cls._loggers:
            cls._loggers[name] = IntelligenceLogger(name, config)
        return cls._loggers[name]
        
    @classmethod
    def configure_all(cls, config: Dict[str, Any]):
        """Configure all loggers with global config"""
        for logger in cls._loggers.values():
            logger.config.update(config)
            logger._setup_logger()