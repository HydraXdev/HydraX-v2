"""
Enhanced Error Handling & Recovery System for BITTEN
Provides comprehensive error management, logging, and recovery mechanisms
"""

import logging
import traceback
import sys
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from contextlib import contextmanager
import sqlite3
import requests

class ErrorSeverity(Enum):
    """Error severity levels for proper handling"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors for targeted recovery"""
    DATABASE = "database"
    NETWORK = "network"
    TELEGRAM = "telegram"
    MT5 = "mt5"
    WEBAPP = "webapp"
    SIGNAL = "signal"
    USER_AUTH = "user_auth"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    SYSTEM = "system"

@dataclass
class ErrorEvent:
    """Structured error event for tracking and analysis"""
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    error_code: str
    message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    resolved: bool = False
    recovery_attempts: int = 0
    resolution_time: Optional[datetime] = None

class ErrorRecoveryRegistry:
    """Registry for error recovery strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, Callable] = {}
        self.retry_configs: Dict[ErrorCategory, Dict] = {
            ErrorCategory.DATABASE: {"max_retries": 3, "delay": 1, "backoff": 2},
            ErrorCategory.NETWORK: {"max_retries": 5, "delay": 2, "backoff": 1.5},
            ErrorCategory.TELEGRAM: {"max_retries": 3, "delay": 3, "backoff": 2},
            ErrorCategory.MT5: {"max_retries": 2, "delay": 5, "backoff": 2},
            ErrorCategory.SIGNAL: {"max_retries": 1, "delay": 1, "backoff": 1}}
    
    def register_strategy(self, error_code: str, strategy: Callable):
        """Register a recovery strategy for specific error code"""
        self.strategies[error_code] = strategy
    
    def get_strategy(self, error_code: str) -> Optional[Callable]:
        """Get recovery strategy for error code"""
        return self.strategies.get(error_code)
    
    def get_retry_config(self, category: ErrorCategory) -> Dict:
        """Get retry configuration for error category"""
        return self.retry_configs.get(category, {"max_retries": 1, "delay": 1, "backoff": 1})

class EnhancedErrorHandler:
    """Main error handling system with logging and recovery"""
    
    def __init__(self, db_path: str = "data/error_tracking.db"):
        self.db_path = db_path
        self.recovery_registry = ErrorRecoveryRegistry()
        self.error_history: List[ErrorEvent] = []
        self.circuit_breakers: Dict[str, Dict] = {}
        self.setup_logging()
        self.setup_database()
        self.setup_recovery_strategies()
        self._lock = threading.Lock()
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Main error log
        self.logger = logging.getLogger("bitten_errors")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        file_handler = logging.FileHandler(f"{log_dir}/error_handling.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def setup_database(self):
        """Setup error tracking database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    error_code TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    stack_trace TEXT,
                    user_id TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    recovery_attempts INTEGER DEFAULT 0,
                    resolution_time TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_stats (
                    error_code TEXT PRIMARY KEY,
                    total_occurrences INTEGER DEFAULT 0,
                    successful_recoveries INTEGER DEFAULT 0,
                    last_occurrence TIMESTAMP,
                    avg_recovery_time REAL
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_category ON error_events(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_severity ON error_events(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_resolved ON error_events(resolved)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Failed to setup error tracking database: {e}")
    
    def setup_recovery_strategies(self):
        """Setup default recovery strategies"""
        
        # Database connection recovery
        def recover_database_connection(context: Dict) -> bool:
            """Attempt to recover database connection"""
            try:
                db_path = context.get("db_path", "data/engagement.db")
                conn = sqlite3.connect(db_path, timeout=10)
                conn.execute("SELECT 1")
                conn.close()
                return True
            except Exception:
                return False
        
        # Network connectivity recovery
        def recover_network_connection(context: Dict) -> bool:
            """Test network connectivity"""
            try:
                response = requests.get("https://httpbin.org/status/200", timeout=5)
                return response.status_code == 200
            except Exception:
                return False
        
        # Telegram API recovery
        def recover_telegram_api(context: Dict) -> bool:
            """Test Telegram API connectivity"""
            try:
                bot_token = context.get("bot_token")
                if not bot_token:
                    return False
                
                response = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/getMe",
                    timeout=10
                )
                return response.status_code == 200
            except Exception:
                return False
        
        # Signal validation recovery
        def recover_signal_validation(context: Dict) -> bool:
            """Validate signal data structure"""
            signal_data = context.get("signal_data", {})
            required_fields = ["symbol", "direction", "entry_price", "stop_loss", "take_profit"]
            return all(field in signal_data for field in required_fields)
        
        # Register strategies
        self.recovery_registry.register_strategy("DB_CONNECTION_FAILED", recover_database_connection)
        self.recovery_registry.register_strategy("NETWORK_TIMEOUT", recover_network_connection)
        self.recovery_registry.register_strategy("TELEGRAM_API_ERROR", recover_telegram_api)
        self.recovery_registry.register_strategy("SIGNAL_VALIDATION_ERROR", recover_signal_validation)
    
    def log_error(self, error_event: ErrorEvent):
        """Log error event to database and files"""
        try:
            # Log to file
            self.logger.error(
                f"[{error_event.category.value}] {error_event.error_code}: {error_event.message}"
            )
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO error_events 
                (timestamp, category, severity, error_code, message, context, 
                 stack_trace, user_id, recovery_attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                error_event.timestamp,
                error_event.category.value,
                error_event.severity.value,
                error_event.error_code,
                error_event.message,
                json.dumps(error_event.context),
                error_event.stack_trace,
                error_event.user_id,
                error_event.recovery_attempts
            ))
            
            conn.commit()
            conn.close()
            
            # Add to memory for quick access
            with self._lock:
                self.error_history.append(error_event)
                # Keep only last 1000 errors in memory
                if len(self.error_history) > 1000:
                    self.error_history = self.error_history[-1000:]
        
        except Exception as e:
            print(f"Failed to log error event: {e}")
    
    def attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt to recover from error using registered strategies"""
        strategy = self.recovery_registry.get_strategy(error_event.error_code)
        if not strategy:
            return False
        
        retry_config = self.recovery_registry.get_retry_config(error_event.category)
        max_retries = retry_config["max_retries"]
        delay = retry_config["delay"]
        backoff = retry_config["backoff"]
        
        for attempt in range(max_retries):
            try:
                error_event.recovery_attempts = attempt + 1
                
                self.logger.info(
                    f"Recovery attempt {attempt + 1}/{max_retries} for {error_event.error_code}"
                )
                
                if strategy(error_event.context):
                    error_event.resolved = True
                    error_event.resolution_time = datetime.now()
                    self.logger.info(f"Successfully recovered from {error_event.error_code}")
                    return True
                
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff
            
            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
        
        return False
    
    def handle_error(self, 
                    error: Exception,
                    category: ErrorCategory,
                    severity: ErrorSeverity,
                    error_code: str,
                    context: Dict[str, Any],
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """Main error handling entry point"""
        
        # Create error event
        error_event = ErrorEvent(
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            error_code=error_code,
            message=str(error),
            context=context,
            stack_trace=traceback.format_exc(),
            user_id=user_id
        )
        
        # Log the error
        self.log_error(error_event)
        
        # Attempt recovery for non-critical errors
        recovery_successful = False
        if severity != ErrorSeverity.CRITICAL:
            recovery_successful = self.attempt_recovery(error_event)
        
        # Check circuit breaker
        if self.should_break_circuit(error_code):
            self.logger.warning(f"Circuit breaker activated for {error_code}")
            return {
                "success": False,
                "error": "Service temporarily unavailable",
                "error_code": "CIRCUIT_BREAKER_ACTIVE",
                "retry_after": self.get_circuit_breaker_delay(error_code)
            }
        
        # Update circuit breaker
        self.update_circuit_breaker(error_code, recovery_successful)
        
        # Return appropriate response
        if recovery_successful:
            return {
                "success": True,
                "message": "Error recovered successfully",
                "recovery_attempts": error_event.recovery_attempts
            }
        else:
            return {
                "success": False,
                "error": self.get_user_friendly_message(error_event),
                "error_code": error_code,
                "severity": severity.value,
                "recovery_attempted": error_event.recovery_attempts > 0
            }
    
    def should_break_circuit(self, error_code: str) -> bool:
        """Check if circuit breaker should activate"""
        if error_code not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[error_code]
        failure_threshold = 5
        time_window = 300  # 5 minutes
        
        now = time.time()
        recent_failures = [
            timestamp for timestamp in breaker.get("failures", [])
            if now - timestamp < time_window
        ]
        
        return len(recent_failures) >= failure_threshold
    
    def update_circuit_breaker(self, error_code: str, success: bool):
        """Update circuit breaker state"""
        if error_code not in self.circuit_breakers:
            self.circuit_breakers[error_code] = {
                "failures": [],
                "last_success": None
            }
        
        breaker = self.circuit_breakers[error_code]
        now = time.time()
        
        if success:
            breaker["last_success"] = now
            breaker["failures"] = []  # Reset failures on success
        else:
            breaker["failures"].append(now)
    
    def get_circuit_breaker_delay(self, error_code: str) -> int:
        """Get delay before retrying when circuit breaker is active"""
        breaker = self.circuit_breakers.get(error_code, {})
        failure_count = len(breaker.get("failures", []))
        
        # Exponential backoff: 30s, 60s, 120s, 300s, 600s
        delays = [30, 60, 120, 300, 600]
        index = min(failure_count - 1, len(delays) - 1)
        return delays[index] if index >= 0 else 30
    
    def get_user_friendly_message(self, error_event: ErrorEvent) -> str:
        """Get user-friendly error message"""
        category_messages = {
            ErrorCategory.DATABASE: "Database temporarily unavailable. Please try again.",
            ErrorCategory.NETWORK: "Network connection issues. Please check your connection.",
            ErrorCategory.TELEGRAM: "Telegram service temporarily unavailable.",
            ErrorCategory.MT5: "Trading platform connection issues.",
            ErrorCategory.WEBAPP: "Web application error. Please refresh the page.",
            ErrorCategory.SIGNAL: "Signal processing error. Please try again.",
            ErrorCategory.USER_AUTH: "Authentication required. Please log in again.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment.",
            ErrorCategory.VALIDATION: "Invalid data provided. Please check your input.",
            ErrorCategory.SYSTEM: "System error. Our team has been notified."
        }
        
        base_message = category_messages.get(
            error_event.category, 
            "An unexpected error occurred."
        )
        
        if error_event.severity == ErrorSeverity.CRITICAL:
            return f"{base_message} Critical issue - please contact support."
        
        return base_message
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            # Total errors
            cursor.execute(
                "SELECT COUNT(*) FROM error_events WHERE timestamp > ?",
                (cutoff,)
            )
            total_errors = cursor.fetchone()[0]
            
            # Errors by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM error_events 
                WHERE timestamp > ?
                GROUP BY category
                ORDER BY count DESC
            """, (cutoff,))
            by_category = dict(cursor.fetchall())
            
            # Errors by severity
            cursor.execute("""
                SELECT severity, COUNT(*) as count
                FROM error_events 
                WHERE timestamp > ?
                GROUP BY severity
                ORDER BY count DESC
            """, (cutoff,))
            by_severity = dict(cursor.fetchall())
            
            # Recovery success rate
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN resolved = 1 THEN 1 END) as resolved,
                    COUNT(*) as total
                FROM error_events 
                WHERE timestamp > ? AND recovery_attempts > 0
            """, (cutoff,))
            recovery_data = cursor.fetchone()
            recovery_rate = (recovery_data[0] / recovery_data[1] * 100) if recovery_data[1] > 0 else 0
            
            conn.close()
            
            return {
                "total_errors": total_errors,
                "by_category": by_category,
                "by_severity": by_severity,
                "recovery_success_rate": round(recovery_rate, 2),
                "circuit_breakers_active": len([
                    code for code in self.circuit_breakers
                    if self.should_break_circuit(code)
                ])
            }
        
        except Exception as e:
            return {"error": f"Failed to get error stats: {e}"}

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 error_code: Optional[str] = None):
    """Decorator to automatically handle errors in functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance
                error_handler = getattr(wrapper, '_error_handler', None)
                if not error_handler:
                    error_handler = EnhancedErrorHandler()
                    wrapper._error_handler = error_handler
                
                # Generate error code if not provided
                code = error_code or f"{func.__name__.upper()}_ERROR"
                
                # Handle the error
                return error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    error_code=code,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
        
        return wrapper
    return decorator

@contextmanager
def error_recovery_context(handler: EnhancedErrorHandler,
                          category: ErrorCategory,
                          error_code: str,
                          context: Dict[str, Any]):
    """Context manager for error handling in code blocks"""
    try:
        yield
    except Exception as e:
        result = handler.handle_error(
            error=e,
            category=category,
            severity=ErrorSeverity.MEDIUM,
            error_code=error_code,
            context=context
        )
        
        if not result["success"]:
            raise RuntimeError(f"Error handling failed: {result}")

# Global error handler instance
global_error_handler = EnhancedErrorHandler()

# Convenience functions
def log_database_error(error: Exception, context: Dict[str, Any], user_id: Optional[str] = None):
    """Quick function to log database errors"""
    return global_error_handler.handle_error(
        error=error,
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        error_code="DB_OPERATION_FAILED",
        context=context,
        user_id=user_id
    )

def log_network_error(error: Exception, context: Dict[str, Any], user_id: Optional[str] = None):
    """Quick function to log network errors"""
    return global_error_handler.handle_error(
        error=error,
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        error_code="NETWORK_ERROR",
        context=context,
        user_id=user_id
    )

def log_telegram_error(error: Exception, context: Dict[str, Any], user_id: Optional[str] = None):
    """Quick function to log Telegram errors"""
    return global_error_handler.handle_error(
        error=error,
        category=ErrorCategory.TELEGRAM,
        severity=ErrorSeverity.MEDIUM,
        error_code="TELEGRAM_API_ERROR",
        context=context,
        user_id=user_id
    )

def get_system_health() -> Dict[str, Any]:
    """Get overall system health status"""
    stats = global_error_handler.get_error_stats(hours=1)
    
    # Health score calculation
    total_errors = stats.get("total_errors", 0)
    critical_errors = stats.get("by_severity", {}).get("critical", 0)
    recovery_rate = stats.get("recovery_success_rate", 0)
    
    if total_errors == 0:
        health_score = 100
    elif critical_errors > 0:
        health_score = max(0, 50 - (critical_errors * 10))
    else:
        health_score = max(0, 100 - (total_errors * 5) + (recovery_rate / 2))
    
    health_status = "healthy" if health_score >= 90 else \
                   "warning" if health_score >= 70 else \
                   "degraded" if health_score >= 50 else "critical"
    
    return {
        "health_score": round(health_score, 1),
        "status": health_status,
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test the error handling system
    handler = EnhancedErrorHandler()
    
    # Test error logging
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        result = handler.handle_error(
            error=e,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW,
            error_code="TEST_ERROR",
            context={"test": True}
        )
        print("Error handling result:", result)
    
    # Test system health
    health = get_system_health()
    print("System health:", health)