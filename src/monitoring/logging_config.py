#!/usr/bin/env python3
"""
BITTEN Production Logging Configuration
Comprehensive structured logging system for all BITTEN services.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import traceback
from pathlib import Path

class BittenLogFormatter(logging.Formatter):
    """Custom JSON formatter for BITTEN logs"""
    
    def __init__(self, service_name: str = "bitten-core"):
        super().__init__()
        self.service_name = service_name
        
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'trade_id'):
            log_entry["trade_id"] = record.trade_id
        if hasattr(record, 'signal_id'):
            log_entry["signal_id"] = record.signal_id
        if hasattr(record, 'action'):
            log_entry["action"] = record.action
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration
        if hasattr(record, 'performance_metrics'):
            log_entry["metrics"] = record.performance_metrics
        
        return json.dumps(log_entry)

class BittenLoggingConfig:
    """Centralized logging configuration for BITTEN system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.log_dir = Path(self.config.get('log_dir', '/var/log/bitten'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default logging configuration"""
        return {
            'log_dir': '/var/log/bitten',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'backup_count': 10,
            'console_logging': True,
            'file_logging': True,
            'json_logging': True,
            'services': {
                'bitten-core': {'level': 'INFO'},
                'signal-generator': {'level': 'INFO'},
                'trade-executor': {'level': 'INFO'},
                'health-monitor': {'level': 'INFO'},
                'performance-monitor': {'level': 'INFO'},
                'mt5-bridge': {'level': 'INFO'},
                'telegram-bot': {'level': 'INFO'},
                'risk-manager': {'level': 'INFO'},
                'alert-system': {'level': 'INFO'}
            }
        }
    
    def setup_logging(self, service_name: str = "bitten-core") -> logging.Logger:
        """Setup logging for a specific service"""
        logger = logging.getLogger(service_name)
        logger.setLevel(getattr(logging, self.config['log_level']))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        if self.config.get('console_logging', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            if self.config.get('json_logging', True):
                console_handler.setFormatter(BittenLogFormatter(service_name))
            else:
                console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                console_handler.setFormatter(logging.Formatter(console_format))
            
            logger.addHandler(console_handler)
        
        # File handler
        if self.config.get('file_logging', True):
            log_file = self.log_dir / f"{service_name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count']
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(BittenLogFormatter(service_name))
            logger.addHandler(file_handler)
        
        # Error file handler (separate file for errors)
        error_file = self.log_dir / f"{service_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count']
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(BittenLogFormatter(service_name))
        logger.addHandler(error_handler)
        
        return logger
    
    def get_performance_logger(self, service_name: str = "performance") -> logging.Logger:
        """Get a dedicated performance logger"""
        logger = logging.getLogger(f"{service_name}-performance")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Performance log file
        perf_file = self.log_dir / f"{service_name}_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_file,
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count']
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(BittenLogFormatter(f"{service_name}-performance"))
        logger.addHandler(perf_handler)
        
        return logger
    
    def get_signal_logger(self) -> logging.Logger:
        """Get dedicated signal generation logger"""
        logger = logging.getLogger("signal-generator")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Signal log file
        signal_file = self.log_dir / "signals.log"
        signal_handler = logging.handlers.RotatingFileHandler(
            signal_file,
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count']
        )
        signal_handler.setLevel(logging.INFO)
        signal_handler.setFormatter(BittenLogFormatter("signal-generator"))
        logger.addHandler(signal_handler)
        
        return logger
    
    def get_trade_logger(self) -> logging.Logger:
        """Get dedicated trade execution logger"""
        logger = logging.getLogger("trade-executor")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Trade log file
        trade_file = self.log_dir / "trades.log"
        trade_handler = logging.handlers.RotatingFileHandler(
            trade_file,
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count']
        )
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(BittenLogFormatter("trade-executor"))
        logger.addHandler(trade_handler)
        
        return logger
    
    def get_health_logger(self) -> logging.Logger:
        """Get dedicated health monitoring logger"""
        logger = logging.getLogger("health-monitor")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Health log file
        health_file = self.log_dir / "health.log"
        health_handler = logging.handlers.RotatingFileHandler(
            health_file,
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count']
        )
        health_handler.setLevel(logging.INFO)
        health_handler.setFormatter(BittenLogFormatter("health-monitor"))
        logger.addHandler(health_handler)
        
        return logger
    
    def setup_audit_logging(self) -> logging.Logger:
        """Setup audit logging for security events"""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Audit log file (no rotation for security)
        audit_file = self.log_dir / "audit.log"
        audit_handler = logging.FileHandler(audit_file)
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(BittenLogFormatter("audit"))
        logger.addHandler(audit_handler)
        
        return logger

class LoggingContextManager:
    """Context manager for adding context to logs"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
        
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)

# Performance monitoring decorators
def log_performance(logger: logging.Logger, action: str = None):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            action_name = action or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                with LoggingContextManager(logger, action=action_name, duration=duration):
                    logger.info(f"Action completed successfully: {action_name}")
                
                return result
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                with LoggingContextManager(logger, action=action_name, duration=duration):
                    logger.error(f"Action failed: {action_name}", exc_info=True)
                raise
        return wrapper
    return decorator

def log_signal_generation(logger: logging.Logger):
    """Decorator to log signal generation events"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                signal_data = {
                    'signal_count': len(result) if isinstance(result, list) else 1,
                    'generation_time_ms': duration,
                    'timestamp': start_time.isoformat()
                }
                
                with LoggingContextManager(logger, performance_metrics=signal_data):
                    logger.info("Signal generation completed")
                
                return result
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                with LoggingContextManager(logger, duration=duration):
                    logger.error("Signal generation failed", exc_info=True)
                raise
        return wrapper
    return decorator

def log_trade_execution(logger: logging.Logger):
    """Decorator to log trade execution events"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                trade_data = {
                    'execution_time_ms': duration,
                    'timestamp': start_time.isoformat(),
                    'success': result.get('success', False) if isinstance(result, dict) else True
                }
                
                with LoggingContextManager(logger, performance_metrics=trade_data):
                    logger.info("Trade execution completed")
                
                return result
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                with LoggingContextManager(logger, duration=duration):
                    logger.error("Trade execution failed", exc_info=True)
                raise
        return wrapper
    return decorator

# Global logging configuration instance
_logging_config = None

def get_logging_config(config: Optional[Dict[str, Any]] = None) -> BittenLoggingConfig:
    """Get global logging configuration instance"""
    global _logging_config
    if _logging_config is None:
        _logging_config = BittenLoggingConfig(config)
    return _logging_config

def setup_service_logging(service_name: str, config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Setup logging for a service"""
    logging_config = get_logging_config(config)
    return logging_config.setup_logging(service_name)

# Example usage
if __name__ == "__main__":
    # Setup logging for core service
    logger = setup_service_logging("bitten-core")
    
    # Test logging
    logger.info("BITTEN Core logging initialized")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test context logging
    with LoggingContextManager(logger, user_id=12345, action="test_action"):
        logger.info("Context logging test")
    
    # Test performance logging
    @log_performance(logger, "test_function")
    def test_function():
        import time
        time.sleep(0.1)
        return "success"
    
    test_function()