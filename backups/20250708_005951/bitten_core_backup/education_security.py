"""
BITTEN Education Platform Security Utilities
Comprehensive security module for education features including squad/mentor systems,
achievements, XP tracking, and anti-cheat mechanisms.
"""

import os
import re
import json
import time
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserRole(Enum):
    """User roles in the education platform"""
    STUDENT = "student"
    SQUAD_MEMBER = "squad_member"
    SQUAD_LEADER = "squad_leader"
    MENTOR = "mentor"
    ADMIN = "admin"
    SYSTEM = "system"

@dataclass
class SecurityConfig:
    """Security configuration for education platform"""
    # Input validation
    max_input_length: int = 1000
    max_username_length: int = 50
    max_squad_name_length: int = 100
    max_achievement_name_length: int = 200
    max_message_length: int = 500
    
    # Rate limiting
    default_rate_limit: int = 60  # requests per minute
    xp_rate_limit: int = 30  # XP gains per hour
    achievement_rate_limit: int = 10  # achievements per day
    message_rate_limit: int = 20  # messages per minute
    
    # Anti-cheat
    max_xp_per_action: int = 1000
    max_daily_xp: int = 10000
    suspicious_xp_threshold: int = 5000  # XP in 1 hour
    max_achievement_progress_jump: float = 0.5  # 50% progress in one update
    
    # Encryption
    encryption_key: Optional[bytes] = None
    token_expiry_hours: int = 24
    session_timeout_minutes: int = 30
    
    # Security headers
    enable_security_headers: bool = True
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    
    # Audit logging
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 90
    sensitive_fields: List[str] = field(default_factory=lambda: [
        'password', 'token', 'session_id', 'api_key', 'secret',
        'credit_card', 'ssn', 'email', 'phone'
    ])

# Global security configuration
_security_config = SecurityConfig()

def set_security_config(config: SecurityConfig):
    """Update global security configuration"""
    global _security_config
    _security_config = config

# ============================================================================
# INPUT SANITIZATION
# ============================================================================

class InputSanitizer:
    """Comprehensive input sanitization for all user inputs"""
    
    # Regex patterns for validation
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    SQUAD_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_-]{3,100}$')
    ACHIEVEMENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Dangerous patterns to remove
    SQL_INJECTION_PATTERN = re.compile(
        r'(\b(union|select|insert|update|delete|drop|create|alter|exec|script)\b)',
        re.IGNORECASE
    )
    XSS_PATTERN = re.compile(
        r'(<script|<iframe|<object|<embed|<form|javascript:|onerror=|onload=|onclick=)',
        re.IGNORECASE
    )
    PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.[\\/]')
    
    @staticmethod
    def sanitize_string(
        value: Any,
        max_length: Optional[int] = None,
        allow_html: bool = False,
        allow_newlines: bool = True
    ) -> str:
        """
        Sanitize string input with comprehensive cleaning
        
        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            allow_newlines: Whether to allow newline characters
            
        Returns:
            Sanitized string
        """
        if value is None:
            return ""
        
        # Convert to string
        text = str(value)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Handle newlines
        if not allow_newlines:
            text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove SQL injection attempts
        text = InputSanitizer.SQL_INJECTION_PATTERN.sub('', text)
        
        # Remove XSS attempts
        if not allow_html:
            text = InputSanitizer.XSS_PATTERN.sub('', text)
            # Also escape HTML entities
            text = (text.replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;')
                       .replace('"', '&quot;')
                       .replace("'", '&#x27;'))
        
        # Remove path traversal attempts
        text = InputSanitizer.PATH_TRAVERSAL_PATTERN.sub('', text)
        
        # Limit length
        if max_length:
            text = text[:max_length]
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize and validate username"""
        username = InputSanitizer.sanitize_string(
            username,
            max_length=_security_config.max_username_length,
            allow_html=False,
            allow_newlines=False
        )
        
        if not InputSanitizer.USERNAME_PATTERN.match(username):
            raise ValueError(f"Invalid username format: {username}")
        
        return username
    
    @staticmethod
    def sanitize_squad_name(name: str) -> str:
        """Sanitize and validate squad name"""
        name = InputSanitizer.sanitize_string(
            name,
            max_length=_security_config.max_squad_name_length,
            allow_html=False,
            allow_newlines=False
        )
        
        if not InputSanitizer.SQUAD_NAME_PATTERN.match(name):
            raise ValueError(f"Invalid squad name format: {name}")
        
        return name
    
    @staticmethod
    def sanitize_achievement_id(achievement_id: str) -> str:
        """Sanitize and validate achievement ID"""
        achievement_id = InputSanitizer.sanitize_string(
            achievement_id,
            max_length=50,
            allow_html=False,
            allow_newlines=False
        )
        
        if not InputSanitizer.ACHIEVEMENT_ID_PATTERN.match(achievement_id):
            raise ValueError(f"Invalid achievement ID format: {achievement_id}")
        
        return achievement_id
    
    @staticmethod
    def sanitize_integer(value: Any, min_val: int = 0, max_val: int = 2147483647) -> int:
        """Sanitize and validate integer input"""
        try:
            num = int(value)
            if num < min_val or num > max_val:
                raise ValueError(f"Value {num} out of range [{min_val}, {max_val}]")
            return num
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid integer value: {value}") from e
    
    @staticmethod
    def sanitize_float(value: Any, min_val: float = 0.0, max_val: float = 1000000.0) -> float:
        """Sanitize and validate float input"""
        try:
            num = float(value)
            if num < min_val or num > max_val:
                raise ValueError(f"Value {num} out of range [{min_val}, {max_val}]")
            return num
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid float value: {value}") from e
    
    @staticmethod
    def sanitize_json(json_str: str, max_size: int = 10240) -> Dict[str, Any]:
        """Safely parse and validate JSON input"""
        if len(json_str) > max_size:
            raise ValueError(f"JSON input too large: {len(json_str)} > {max_size}")
        
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Thread-safe rate limiter with multiple strategies"""
    
    def __init__(self):
        self._buckets: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
        self._violation_counts: Dict[str, int] = defaultdict(int)
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_allowed: bool = False
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limits
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            burst_allowed: Allow burst traffic
            
        Returns:
            Tuple of (allowed, seconds_until_reset)
        """
        with self._lock:
            now = time.time()
            bucket = self._buckets[key]
            
            # Remove expired entries
            while bucket and bucket[0] < now - window_seconds:
                bucket.popleft()
            
            # Check limit
            if len(bucket) >= max_requests:
                # Calculate when the oldest request expires
                seconds_until_reset = int(bucket[0] + window_seconds - now)
                self._violation_counts[key] += 1
                
                # Log repeated violations
                if self._violation_counts[key] > 10:
                    logger.warning(f"Rate limit violations for {key}: {self._violation_counts[key]}")
                
                return False, seconds_until_reset
            
            # Add current request
            bucket.append(now)
            
            # Reset violation count on successful request
            if key in self._violation_counts:
                self._violation_counts[key] = 0
            
            return True, None
    
    def get_remaining_quota(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in current window"""
        with self._lock:
            now = time.time()
            bucket = self._buckets[key]
            
            # Count non-expired entries
            count = sum(1 for t in bucket if t > now - window_seconds)
            return max(0, max_requests - count)

# Rate limiter singleton
_rate_limiter = RateLimiter()

def rate_limit(
    max_requests: int = None,
    window_seconds: int = 60,
    key_func: Optional[Callable] = None,
    error_message: str = "Rate limit exceeded"
):
    """
    Decorator for rate limiting functions
    
    Args:
        max_requests: Maximum requests (defaults to config)
        window_seconds: Time window
        key_func: Function to extract rate limit key from arguments
        error_message: Error message on rate limit
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default: use first argument as key
                key = str(args[0]) if args else "anonymous"
            
            # Apply rate limit
            requests = max_requests or _security_config.default_rate_limit
            allowed, retry_after = _rate_limiter.check_rate_limit(
                key, requests, window_seconds
            )
            
            if not allowed:
                raise PermissionError(f"{error_message}. Retry after {retry_after} seconds.")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# ============================================================================
# AUTHORIZATION MIDDLEWARE
# ============================================================================

@dataclass
class UserContext:
    """User context for authorization"""
    user_id: int
    username: str
    role: UserRole
    squad_id: Optional[int] = None
    permissions: Set[str] = field(default_factory=set)
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

class AuthorizationMiddleware:
    """Authorization middleware for squad/mentor features"""
    
    # Permission definitions
    PERMISSIONS = {
        UserRole.STUDENT: {
            'view_own_profile', 'edit_own_profile', 'view_achievements',
            'join_squad', 'leave_squad', 'view_leaderboard'
        },
        UserRole.SQUAD_MEMBER: {
            'view_own_profile', 'edit_own_profile', 'view_achievements',
            'view_squad_info', 'participate_squad_challenges',
            'leave_squad', 'view_leaderboard', 'send_squad_message'
        },
        UserRole.SQUAD_LEADER: {
            'view_own_profile', 'edit_own_profile', 'view_achievements',
            'view_squad_info', 'edit_squad_info', 'manage_squad_members',
            'create_squad_challenges', 'view_squad_analytics',
            'send_squad_message', 'moderate_squad_chat', 'view_leaderboard'
        },
        UserRole.MENTOR: {
            'view_own_profile', 'edit_own_profile', 'view_achievements',
            'view_student_profiles', 'assign_challenges', 'track_progress',
            'send_mentor_message', 'create_learning_paths', 'view_analytics',
            'moderate_content', 'view_leaderboard'
        },
        UserRole.ADMIN: {
            'all'  # Admin has all permissions
        }
    }
    
    def __init__(self):
        self._sessions: Dict[str, UserContext] = {}
        self._session_lock = threading.Lock()
    
    def create_session(self, user_context: UserContext) -> str:
        """Create a new session for user"""
        session_id = secrets.token_urlsafe(32)
        user_context.session_id = session_id
        
        # Assign role-based permissions
        if user_context.role == UserRole.ADMIN:
            user_context.permissions = {'all'}
        else:
            user_context.permissions = self.PERMISSIONS.get(
                user_context.role, set()
            )
        
        with self._session_lock:
            self._sessions[session_id] = user_context
        
        logger.info(f"Session created for user {user_context.username} with role {user_context.role.value}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserContext]:
        """Get user context from session"""
        with self._session_lock:
            context = self._sessions.get(session_id)
            
            if context:
                # Check session timeout
                if datetime.now() - context.created_at > timedelta(
                    minutes=_security_config.session_timeout_minutes
                ):
                    del self._sessions[session_id]
                    return None
            
            return context
    
    def destroy_session(self, session_id: str):
        """Destroy a session"""
        with self._session_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    def check_permission(self, user_context: UserContext, permission: str) -> bool:
        """Check if user has specific permission"""
        if 'all' in user_context.permissions:
            return True
        return permission in user_context.permissions
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user context from arguments
                user_context = None
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
                
                if not user_context:
                    raise PermissionError("No user context provided")
                
                if not self.check_permission(user_context, permission):
                    raise PermissionError(
                        f"User {user_context.username} lacks permission: {permission}"
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_role(self, *allowed_roles: UserRole):
        """Decorator to require specific roles"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user context from arguments
                user_context = None
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
                
                if not user_context:
                    raise PermissionError("No user context provided")
                
                if user_context.role not in allowed_roles:
                    raise PermissionError(
                        f"User role {user_context.role.value} not in allowed roles: "
                        f"{[r.value for r in allowed_roles]}"
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator

# Authorization middleware singleton
_auth_middleware = AuthorizationMiddleware()

def get_auth_middleware() -> AuthorizationMiddleware:
    """Get global authorization middleware instance"""
    return _auth_middleware

# ============================================================================
# ENCRYPTION UTILITIES
# ============================================================================

class EncryptionManager:
    """Encryption utilities for sensitive data"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self._master_key = master_key
        else:
            # Generate or load master key
            self._master_key = self._get_or_create_master_key()
        
        self._fernet = Fernet(self._derive_key(self._master_key))
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = Path("data/.encryption_key")
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            
            # Ensure directory exists
            key_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with restricted permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set file permissions (Unix only)
            try:
                os.chmod(key_file, 0o600)
            except AttributeError:
                pass  # Windows doesn't support chmod
            
            return key
    
    def _derive_key(self, password: bytes, salt: bytes = b'bitten-education-salt') -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt_string(self, plaintext: str) -> str:
        """Encrypt a string"""
        return self._fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt_string(self, ciphertext: str) -> str:
        """Decrypt a string"""
        return self._fernet.decrypt(ciphertext.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary"""
        json_str = json.dumps(data)
        return self.encrypt_string(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> Dict[str, Any]:
        """Decrypt to dictionary"""
        json_str = self.decrypt_string(ciphertext)
        return json.loads(json_str)
    
    def hash_sensitive_data(self, data: str, salt: Optional[bytes] = None) -> str:
        """One-way hash for sensitive data like passwords"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        hash_bytes = kdf.derive(data.encode())
        
        # Return salt + hash as base64
        return base64.b64encode(salt + hash_bytes).decode()
    
    def verify_hash(self, data: str, hash_str: str) -> bool:
        """Verify data against hash"""
        try:
            # Decode salt + hash
            combined = base64.b64decode(hash_str)
            salt = combined[:32]
            stored_hash = combined[32:]
            
            # Recompute hash
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            computed_hash = kdf.derive(data.encode())
            
            # Constant-time comparison
            return hmac.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

# Encryption manager singleton
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager(_security_config.encryption_key)
    return _encryption_manager

# ============================================================================
# SECURITY HEADERS
# ============================================================================

def apply_security_headers(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply security headers to web responses
    
    Args:
        response: Response dictionary to modify
        
    Returns:
        Modified response with security headers
    """
    if not _security_config.enable_security_headers:
        return response
    
    headers = response.get('headers', {})
    
    # Content Security Policy
    headers['Content-Security-Policy'] = _security_config.csp_policy
    
    # Other security headers
    headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    })
    
    response['headers'] = headers
    return response

# ============================================================================
# ANTI-CHEAT MECHANISMS
# ============================================================================

class AntiCheatSystem:
    """Anti-cheat system for XP and achievements"""
    
    def __init__(self):
        self._xp_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self._achievement_history: Dict[int, Dict[str, datetime]] = defaultdict(dict)
        self._suspicious_users: Set[int] = set()
        self._lock = threading.Lock()
    
    def validate_xp_gain(
        self,
        user_id: int,
        xp_amount: int,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate XP gain for suspicious patterns
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        with self._lock:
            # Check single gain limit
            if xp_amount > _security_config.max_xp_per_action:
                return False, f"XP gain exceeds maximum: {xp_amount} > {_security_config.max_xp_per_action}"
            
            # Check daily limit
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            daily_xp = sum(
                gain['amount'] for gain in self._xp_history[user_id]
                if datetime.fromisoformat(gain['timestamp']) >= today_start
            )
            
            if daily_xp + xp_amount > _security_config.max_daily_xp:
                return False, f"Daily XP limit exceeded: {daily_xp + xp_amount} > {_security_config.max_daily_xp}"
            
            # Check for suspicious patterns
            recent_gains = [
                g for g in self._xp_history[user_id]
                if datetime.fromisoformat(g['timestamp']) >= now - timedelta(hours=1)
            ]
            
            hourly_xp = sum(g['amount'] for g in recent_gains)
            if hourly_xp + xp_amount > _security_config.suspicious_xp_threshold:
                self._suspicious_users.add(user_id)
                logger.warning(f"Suspicious XP pattern for user {user_id}: {hourly_xp + xp_amount} XP/hour")
            
            # Record the gain
            self._xp_history[user_id].append({
                'amount': xp_amount,
                'source': source,
                'timestamp': now.isoformat(),
                'metadata': metadata or {}
            })
            
            return True, None
    
    def validate_achievement_unlock(
        self,
        user_id: int,
        achievement_id: str,
        progress: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate achievement unlock/progress
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        with self._lock:
            # Check progress bounds
            if not 0 <= progress <= 1:
                return False, f"Invalid progress value: {progress}"
            
            # Check for instant completion of complex achievements
            last_update = self._achievement_history[user_id].get(achievement_id)
            
            if last_update:
                time_diff = datetime.now() - last_update
                
                # Suspicious if large progress jump in short time
                if progress > _security_config.max_achievement_progress_jump and \
                   time_diff < timedelta(minutes=1):
                    self._suspicious_users.add(user_id)
                    return False, "Achievement progress increased too quickly"
            
            # Record update
            self._achievement_history[user_id][achievement_id] = datetime.now()
            
            return True, None
    
    def is_user_suspicious(self, user_id: int) -> bool:
        """Check if user has been flagged as suspicious"""
        return user_id in self._suspicious_users
    
    def get_user_risk_score(self, user_id: int) -> float:
        """
        Calculate risk score for user (0-1)
        
        Higher score indicates more suspicious behavior
        """
        with self._lock:
            score = 0.0
            
            # Check if flagged
            if user_id in self._suspicious_users:
                score += 0.5
            
            # Check XP patterns
            now = datetime.now()
            recent_gains = [
                g for g in self._xp_history[user_id]
                if datetime.fromisoformat(g['timestamp']) >= now - timedelta(hours=24)
            ]
            
            if recent_gains:
                # Check for repetitive amounts (bot-like behavior)
                amounts = [g['amount'] for g in recent_gains]
                unique_amounts = len(set(amounts))
                if unique_amounts < len(amounts) * 0.3:  # Less than 30% unique
                    score += 0.2
                
                # Check for time patterns
                timestamps = [datetime.fromisoformat(g['timestamp']) for g in recent_gains]
                if len(timestamps) > 10:
                    # Calculate time deltas
                    deltas = [
                        (timestamps[i+1] - timestamps[i]).total_seconds()
                        for i in range(len(timestamps)-1)
                    ]
                    
                    # Check for consistent intervals (bot-like)
                    avg_delta = sum(deltas) / len(deltas)
                    variance = sum((d - avg_delta) ** 2 for d in deltas) / len(deltas)
                    
                    if variance < 10:  # Very consistent timing
                        score += 0.3
            
            return min(score, 1.0)

# Anti-cheat system singleton
_anti_cheat = AntiCheatSystem()

def get_anti_cheat_system() -> AntiCheatSystem:
    """Get global anti-cheat system instance"""
    return _anti_cheat

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Comprehensive audit logging for security events"""
    
    def __init__(self, log_dir: str = "data/audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._current_log_file = None
        self._log_date = None
    
    def _get_log_file(self) -> Path:
        """Get current log file, rotating daily"""
        today = datetime.now().date()
        
        if self._log_date != today:
            self._log_date = today
            self._current_log_file = self.log_dir / f"audit_{today}.json"
        
        return self._current_log_file
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[int],
        details: Dict[str, Any],
        severity: SecurityLevel = SecurityLevel.MEDIUM
    ):
        """Log a security event"""
        if not _security_config.enable_audit_logging:
            return
        
        with self._lock:
            # Sanitize sensitive data
            sanitized_details = self._sanitize_details(details)
            
            # Create event record
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'severity': severity.value,
                'details': sanitized_details,
                'session_id': sanitized_details.get('session_id', 'N/A')
            }
            
            # Write to log file
            log_file = self._get_log_file()
            
            try:
                # Append to JSON lines format
                with open(log_file, 'a', encoding='utf-8') as f:
                    json.dump(event, f)
                    f.write('\n')
                
                # Set file permissions (Unix only)
                try:
                    os.chmod(log_file, 0o600)
                except AttributeError:
                    pass
                
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
            
            # Alert on critical events
            if severity == SecurityLevel.CRITICAL:
                self._alert_critical_event(event)
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from details"""
        sanitized = {}
        
        for key, value in details.items():
            # Check if field is sensitive
            if any(sensitive in key.lower() for sensitive in _security_config.sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _alert_critical_event(self, event: Dict[str, Any]):
        """Send alert for critical security events"""
        logger.critical(f"CRITICAL SECURITY EVENT: {event['event_type']} - {event['details']}")
        # In production, this would send notifications to administrators
    
    def search_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        severity: Optional[SecurityLevel] = None
    ) -> List[Dict[str, Any]]:
        """Search audit logs"""
        results = []
        
        # Iterate through log files in date range
        current_date = start_date.date()
        while current_date <= end_date.date():
            log_file = self.log_dir / f"audit_{current_date}.json"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            
                            # Apply filters
                            if event_type and event['event_type'] != event_type:
                                continue
                            if user_id and event['user_id'] != user_id:
                                continue
                            if severity and event['severity'] != severity.value:
                                continue
                            
                            # Check timestamp
                            event_time = datetime.fromisoformat(event['timestamp'])
                            if start_date <= event_time <= end_date:
                                results.append(event)
                        
                        except json.JSONDecodeError:
                            continue
            
            current_date += timedelta(days=1)
        
        return results
    
    def cleanup_old_logs(self):
        """Remove logs older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=_security_config.audit_log_retention_days)
        
        for log_file in self.log_dir.glob("audit_*.json"):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Removed old audit log: {log_file}")
            
            except Exception as e:
                logger.error(f"Error cleaning up log file {log_file}: {e}")

# Audit logger singleton
_audit_logger = AuditLogger()

def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    return _audit_logger

# ============================================================================
# CSRF PROTECTION
# ============================================================================

class CSRFProtection:
    """CSRF protection for state-changing operations"""
    
    def __init__(self):
        self._tokens: Dict[str, Tuple[str, datetime]] = {}
        self._lock = threading.Lock()
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_urlsafe(32)
        
        with self._lock:
            self._tokens[token] = (session_id, datetime.now())
        
        return token
    
    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        with self._lock:
            if token not in self._tokens:
                return False
            
            stored_session_id, created_at = self._tokens[token]
            
            # Check session match
            if stored_session_id != session_id:
                return False
            
            # Check token age (24 hours)
            if datetime.now() - created_at > timedelta(hours=24):
                del self._tokens[token]
                return False
            
            # Token is valid - remove it (one-time use)
            del self._tokens[token]
            return True
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        with self._lock:
            now = datetime.now()
            expired = [
                token for token, (_, created_at) in self._tokens.items()
                if now - created_at > timedelta(hours=24)
            ]
            
            for token in expired:
                del self._tokens[token]
    
    def require_csrf_token(self, func: Callable) -> Callable:
        """Decorator to require CSRF token"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token and session from kwargs
            token = kwargs.get('csrf_token')
            session_id = kwargs.get('session_id')
            
            if not token or not session_id:
                raise PermissionError("CSRF token required")
            
            if not self.validate_token(token, session_id):
                raise PermissionError("Invalid CSRF token")
            
            # Remove token from kwargs before calling function
            kwargs.pop('csrf_token', None)
            
            return func(*args, **kwargs)
        
        return wrapper

# CSRF protection singleton
_csrf_protection = CSRFProtection()

def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance"""
    return _csrf_protection

# ============================================================================
# COMPREHENSIVE SECURITY VALIDATOR
# ============================================================================

class SecurityValidator:
    """Main security validator combining all security features"""
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.rate_limiter = _rate_limiter
        self.auth = _auth_middleware
        self.encryption = get_encryption_manager()
        self.anti_cheat = _anti_cheat
        self.audit = _audit_logger
        self.csrf = _csrf_protection
    
    def validate_and_log_request(
        self,
        user_context: UserContext,
        action: str,
        data: Dict[str, Any],
        required_permission: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive request validation and logging
        
        Args:
            user_context: User making the request
            action: Action being performed
            data: Request data
            required_permission: Required permission for action
            
        Returns:
            Sanitized data
            
        Raises:
            PermissionError: If validation fails
        """
        # Check permission
        if required_permission and not self.auth.check_permission(user_context, required_permission):
            self.audit.log_event(
                'permission_denied',
                user_context.user_id,
                {
                    'action': action,
                    'required_permission': required_permission,
                    'user_role': user_context.role.value
                },
                SecurityLevel.HIGH
            )
            raise PermissionError(f"Permission denied: {required_permission}")
        
        # Sanitize input data
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitizer.sanitize_string(value)
            elif isinstance(value, (int, float)):
                sanitized_data[key] = value
            elif isinstance(value, dict):
                sanitized_data[key] = self.validate_and_log_request(
                    user_context, f"{action}.{key}", value
                )
            else:
                sanitized_data[key] = value
        
        # Log the action
        self.audit.log_event(
            'user_action',
            user_context.user_id,
            {
                'action': action,
                'data_keys': list(sanitized_data.keys()),
                'session_id': user_context.session_id
            },
            SecurityLevel.LOW
        )
        
        return sanitized_data

# Global security validator
_security_validator = SecurityValidator()

def get_security_validator() -> SecurityValidator:
    """Get global security validator instance"""
    return _security_validator

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def secure_random_string(length: int = 32) -> str:
    """Generate cryptographically secure random string"""
    return secrets.token_urlsafe(length)

def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks"""
    return hmac.compare_digest(a, b)

def hash_user_identifier(identifier: Union[str, int], salt: str = "bitten-edu") -> str:
    """Hash user identifier for privacy"""
    combined = f"{salt}:{identifier}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def validate_file_upload(
    file_data: bytes,
    allowed_types: List[str],
    max_size: int = 5 * 1024 * 1024  # 5MB
) -> Tuple[bool, Optional[str]]:
    """
    Validate file upload for security
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    if len(file_data) > max_size:
        return False, f"File too large: {len(file_data)} > {max_size}"
    
    # Check file type (basic check - in production use python-magic)
    # This is a simplified check based on file headers
    file_signatures = {
        'pdf': b'%PDF',
        'png': b'\x89PNG',
        'jpg': b'\xff\xd8\xff',
        'gif': b'GIF8',
    }
    
    file_type = None
    for ftype, signature in file_signatures.items():
        if file_data.startswith(signature):
            file_type = ftype
            break
    
    if file_type not in allowed_types:
        return False, f"File type not allowed: {file_type}"
    
    return True, None

# ============================================================================
# CLEANUP TASKS
# ============================================================================

def run_security_cleanup():
    """Run periodic security cleanup tasks"""
    try:
        # Clean up expired CSRF tokens
        _csrf_protection.cleanup_expired_tokens()
        
        # Clean up old audit logs
        _audit_logger.cleanup_old_logs()
        
        # Clean up expired sessions
        with _auth_middleware._session_lock:
            now = datetime.now()
            expired_sessions = [
                sid for sid, ctx in _auth_middleware._sessions.items()
                if now - ctx.created_at > timedelta(minutes=_security_config.session_timeout_minutes)
            ]
            
            for sid in expired_sessions:
                del _auth_middleware._sessions[sid]
        
        logger.info("Security cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during security cleanup: {e}")

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
Example usage of the security utilities:

# 1. Input Sanitization
from bitten_core.education_security import InputSanitizer, get_security_validator

# Sanitize user input
username = InputSanitizer.sanitize_username(user_input)
squad_name = InputSanitizer.sanitize_squad_name(squad_input)
message = InputSanitizer.sanitize_string(message_input, max_length=500)

# 2. Rate Limiting
from bitten_core.education_security import rate_limit, get_audit_logger

@rate_limit(max_requests=10, window_seconds=60)
def submit_challenge(user_id: int, challenge_data: dict):
    # Process challenge submission
    pass

# 3. Authorization
from bitten_core.education_security import get_auth_middleware, UserContext, UserRole

auth = get_auth_middleware()

# Create user session
user_context = UserContext(
    user_id=12345,
    username="student123",
    role=UserRole.SQUAD_LEADER,
    squad_id=42
)
session_id = auth.create_session(user_context)

# Check permissions
@auth.require_permission('manage_squad_members')
def remove_squad_member(context: UserContext, member_id: int):
    # Remove member from squad
    pass

# 4. Encryption
from bitten_core.education_security import get_encryption_manager

crypto = get_encryption_manager()

# Encrypt sensitive data
encrypted = crypto.encrypt_dict({
    'api_key': 'secret_key_123',
    'user_data': {'id': 123, 'email': 'user@example.com'}
})

# Decrypt
decrypted = crypto.decrypt_dict(encrypted)

# 5. Anti-Cheat
from bitten_core.education_security import get_anti_cheat_system

anti_cheat = get_anti_cheat_system()

# Validate XP gain
valid, reason = anti_cheat.validate_xp_gain(
    user_id=12345,
    xp_amount=500,
    source='challenge_completed'
)

if not valid:
    raise ValueError(f"Invalid XP gain: {reason}")

# 6. Audit Logging
from bitten_core.education_security import get_audit_logger, SecurityLevel

audit = get_audit_logger()

# Log security event
audit.log_event(
    event_type='squad_created',
    user_id=12345,
    details={
        'squad_name': 'Elite Traders',
        'initial_members': 5
    },
    severity=SecurityLevel.LOW
)

# 7. CSRF Protection
from bitten_core.education_security import get_csrf_protection

csrf = get_csrf_protection()

# Generate token
token = csrf.generate_token(session_id)

# Use in decorator
@csrf.require_csrf_token
def delete_squad(session_id: str, squad_id: int):
    # Delete squad
    pass

# 8. Complete Request Validation
from bitten_core.education_security import get_security_validator

validator = get_security_validator()

# Validate and log complete request
sanitized_data = validator.validate_and_log_request(
    user_context=user_context,
    action='update_profile',
    data={
        'bio': user_bio,
        'display_name': display_name
    },
    required_permission='edit_own_profile'
)
"""