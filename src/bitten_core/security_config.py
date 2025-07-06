"""
BITTEN Security Configuration
Centralized security settings and validation rules
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    
    # File system security
    MAX_FILE_SIZE: int = 1024 * 1024  # 1MB
    ALLOWED_DATA_DIRECTORIES: List[str] = None
    FILE_PERMISSIONS: int = 0o750
    
    # Input validation
    MAX_STRING_LENGTH: int = 500
    MAX_REASON_LENGTH: int = 200
    MAX_LOG_ENTRIES: int = 10000
    
    # Rate limiting
    EMERGENCY_RATE_LIMITS: Dict[str, int] = None
    RATE_LIMIT_WINDOW: int = 300  # 5 minutes
    
    # Emergency system
    MAX_EMERGENCY_DURATION: int = 86400  # 24 hours
    MAX_CONCURRENT_EMERGENCIES: int = 1
    EMERGENCY_TIMEOUT: int = 86400
    
    # Authentication
    EMERGENCY_PERMISSIONS: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.ALLOWED_DATA_DIRECTORIES is None:
            self.ALLOWED_DATA_DIRECTORIES = ['data', 'logs', 'backups', 'test_data']
        
        if self.EMERGENCY_RATE_LIMITS is None:
            self.EMERGENCY_RATE_LIMITS = {
                'emergency_stop': 5,
                'panic': 2,
                'halt_all': 1,
                'recover': 10,
                'emergency_status': 20
            }
        
        if self.EMERGENCY_PERMISSIONS is None:
            self.EMERGENCY_PERMISSIONS = {
                'emergency_stop': ['AUTHORIZED', 'ELITE', 'ADMIN'],
                'panic': ['AUTHORIZED', 'ELITE', 'ADMIN'],
                'halt_all': ['ELITE', 'ADMIN'],
                'recover': ['AUTHORIZED', 'ELITE', 'ADMIN'],
                'emergency_status': ['USER', 'AUTHORIZED', 'ELITE', 'ADMIN']
            }

class SecurityValidator:
    """Security validation utilities"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        
        # Dangerous character patterns
        self.DANGEROUS_CHARS = re.compile(r'[<>"\'{}\[\]\\]')
        self.PATH_TRAVERSAL = re.compile(r'\.\.[\\/]')
        
    def validate_string_input(self, value: Any, max_length: int = None) -> str:
        """Validate and sanitize string input"""
        if not isinstance(value, str):
            value = str(value) if value is not None else ""
        
        # Remove dangerous characters
        value = self.DANGEROUS_CHARS.sub('', value)
        
        # Remove path traversal attempts
        value = self.PATH_TRAVERSAL.sub('', value)
        
        # Limit length
        max_len = max_length or self.config.MAX_STRING_LENGTH
        value = value[:max_len]
        
        return value.strip()
    
    def validate_file_path(self, path: str) -> bool:
        """Validate file path for security"""
        if not path or not isinstance(path, str):
            return False
        
        # Check for path traversal
        if '..' in path or path.startswith('/') or '\\' in path:
            return False
        
        # Check against allowed directories
        path_parts = path.split('/')
        if path_parts[0] not in self.config.ALLOWED_DATA_DIRECTORIES:
            return False
        
        return True
    
    def validate_user_id(self, user_id: Any) -> Optional[int]:
        """Validate user ID"""
        try:
            uid = int(user_id)
            # Basic sanity check for user ID range
            if 1 <= uid <= 999999999:  # Telegram user ID range
                return uid
        except (ValueError, TypeError):
            pass
        return None
    
    def validate_emergency_reason(self, args: List[str]) -> str:
        """Validate and sanitize emergency reason"""
        if not args or not isinstance(args, list):
            return "Manual emergency stop"
        
        # Join and sanitize
        reason = " ".join(str(arg) for arg in args)
        reason = self.validate_string_input(reason, self.config.MAX_REASON_LENGTH)
        
        return reason if reason else "Manual emergency stop"
    
    def validate_json_size(self, file_path: str) -> bool:
        """Check if JSON file size is within limits"""
        try:
            import os
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                return size <= self.config.MAX_FILE_SIZE
        except Exception:
            pass
        return False
    
    def validate_trigger_type(self, trigger: str) -> bool:
        """Validate emergency trigger type"""
        valid_triggers = [
            'manual', 'panic', 'drawdown', 'news', 'system_error',
            'market_volatility', 'broker_connection', 'admin_override',
            'scheduled_maintenance'
        ]
        return trigger in valid_triggers
    
    def validate_emergency_level(self, level: str) -> bool:
        """Validate emergency level"""
        valid_levels = ['soft', 'hard', 'panic', 'maintenance']
        return level in valid_levels
    
    def check_permissions(self, user_rank: str, command: str) -> bool:
        """Check if user has permission for command"""
        allowed_ranks = self.config.EMERGENCY_PERMISSIONS.get(command, ['ADMIN'])
        return user_rank in allowed_ranks
    
    def sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for safe logging"""
        sanitized = {}
        
        for key, value in data.items():
            if key == 'user_id' and isinstance(value, int):
                # Hash user ID for privacy
                import hashlib
                sanitized[key] = hashlib.sha256(str(value).encode()).hexdigest()[:8]
            elif isinstance(value, str):
                sanitized[key] = self.validate_string_input(value, 100)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_log_data(value)
            else:
                sanitized[key] = str(value)[:50]
        
        return sanitized

class SecurityMonitor:
    """Security monitoring and alerting"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.security_events = []
        self.suspicious_activities = []
    
    def log_security_event(self, event_type: str, user_id: int, details: Dict[str, Any]):
        """Log security-related events"""
        from datetime import datetime
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'user_id_hash': self._hash_user_id(user_id),
            'details': self._sanitize_details(details),
            'severity': self._calculate_severity(event_type)
        }
        
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > self.config.MAX_LOG_ENTRIES:
            self.security_events = self.security_events[-1000:]
        
        # Alert on high severity events
        if event['severity'] >= 8:
            self._trigger_security_alert(event)
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect suspicious patterns"""
        anomalies = []
        
        # Check for rapid emergency calls
        from datetime import datetime, timedelta
        recent_threshold = datetime.now() - timedelta(hours=1)
        
        recent_emergencies = [
            e for e in self.security_events
            if e['type'] == 'emergency_command' and
            datetime.fromisoformat(e['timestamp']) > recent_threshold
        ]
        
        if len(recent_emergencies) > 10:
            anomalies.append({
                'type': 'rapid_emergency_calls',
                'count': len(recent_emergencies),
                'severity': 9,
                'description': 'Unusually high number of emergency commands'
            })
        
        # Check for failed authentication attempts
        failed_auths = [
            e for e in self.security_events
            if e['type'] == 'authentication_failure' and
            datetime.fromisoformat(e['timestamp']) > recent_threshold
        ]
        
        if len(failed_auths) > 20:
            anomalies.append({
                'type': 'authentication_failures',
                'count': len(failed_auths),
                'severity': 7,
                'description': 'High number of authentication failures'
            })
        
        return anomalies
    
    def _hash_user_id(self, user_id: int) -> str:
        """Hash user ID for privacy"""
        import hashlib
        return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize event details"""
        validator = SecurityValidator(self.config)
        return validator.sanitize_log_data(details)
    
    def _calculate_severity(self, event_type: str) -> int:
        """Calculate event severity (1-10)"""
        severity_map = {
            'emergency_command': 6,
            'authentication_failure': 4,
            'permission_violation': 7,
            'path_traversal_attempt': 9,
            'injection_attempt': 10,
            'rate_limit_violation': 5,
            'system_error': 6
        }
        return severity_map.get(event_type, 5)
    
    def _trigger_security_alert(self, event: Dict[str, Any]):
        """Trigger security alert for high severity events"""
        # In production, this would send alerts to administrators
        import logging
        logger = logging.getLogger(__name__)
        logger.critical(f"SECURITY ALERT: {event['type']} - Severity {event['severity']}")

# Global security instances
_security_config = SecurityConfig()
_security_validator = SecurityValidator(_security_config)
_security_monitor = SecurityMonitor(_security_config)

def get_security_config() -> SecurityConfig:
    """Get global security configuration"""
    return _security_config

def get_security_validator() -> SecurityValidator:
    """Get global security validator"""
    return _security_validator

def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor"""
    return _security_monitor