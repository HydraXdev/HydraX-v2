"""
BITTEN Security Utilities
Provides security functions and validators for the trading system
"""

import os
import re
import hmac
import hashlib
import json
import decimal
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
import secrets
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Constants for validation
VALID_SYMBOLS = re.compile(r'^[A-Z]{6,10}$')
VALID_DIRECTIONS = {'BUY', 'SELL'}
MIN_VOLUME = decimal.Decimal('0.01')
MAX_VOLUME = decimal.Decimal('100.0')
MIN_PRICE = decimal.Decimal('0.00001')
MAX_PRICE = decimal.Decimal('999999.99999')
MAX_RISK_PERCENT = decimal.Decimal('5.0')
MIN_BALANCE = decimal.Decimal('100.0')

# File security
ALLOWED_FILE_EXTENSIONS = {'.txt', '.json', '.log'}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

class SecurityError(Exception):
    """Base exception for security violations"""
    pass

class ValidationError(SecurityError):
    """Input validation error"""
    pass

class PathTraversalError(SecurityError):
    """Path traversal attempt detected"""
    pass

@dataclass
class SecureConfig:
    """Secure configuration with encryption keys"""
    file_hmac_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    max_trades_per_minute: int = 10
    max_concurrent_trades: int = 50
    enable_encryption: bool = True
    allowed_base_paths: List[str] = field(default_factory=list)

# Global secure config (should be loaded from secure storage)
_secure_config = SecureConfig()

def set_secure_config(config: SecureConfig):
    """Set the global secure configuration"""
    global _secure_config
    _secure_config = config

# Path Security Functions

def validate_safe_path(base_path: str, filename: str) -> str:
    """
    Validate that a file path is safe and within allowed directories
    
    Args:
        base_path: The base directory path
        filename: The filename to validate
        
    Returns:
        The validated full path
        
    Raises:
        PathTraversalError: If path traversal is detected
    """
    # Normalize and validate base path
    base = os.path.abspath(base_path)
    
    # Check if base path is in allowed paths
    if _secure_config.allowed_base_paths:
        allowed = False
        for allowed_path in _secure_config.allowed_base_paths:
            if base.startswith(os.path.abspath(allowed_path)):
                allowed = True
                break
        if not allowed:
            raise PathTraversalError(f"Base path not in allowed directories: {base}")
    
    # Validate filename
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise PathTraversalError(f"Invalid filename: {filename}")
    
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(f"File extension not allowed: {ext}")
    
    # Construct and validate full path
    full_path = os.path.abspath(os.path.join(base, filename))
    
    # Ensure the resolved path is still within base directory
    if not full_path.startswith(base):
        raise PathTraversalError("Path traversal attempt detected")
    
    return full_path

def secure_file_read(filepath: str, max_size: int = MAX_FILE_SIZE) -> str:
    """
    Securely read a file with size limits and validation
    
    Args:
        filepath: Path to file to read
        max_size: Maximum allowed file size
        
    Returns:
        File contents as string
        
    Raises:
        SecurityError: If file is too large or other security issue
    """
    # Check file size first
    if os.path.getsize(filepath) > max_size:
        raise SecurityError(f"File too large: {filepath}")
    
    # Read with explicit encoding
    with open(filepath, 'r', encoding='utf-8', errors='strict') as f:
        content = f.read(max_size + 1)
        
    # Double check size after read
    if len(content) > max_size:
        raise SecurityError(f"File content exceeds max size: {filepath}")
        
    return content

def secure_file_write(filepath: str, content: str, mode: int = 0o600):
    """
    Securely write a file with proper permissions
    
    Args:
        filepath: Path to write to
        content: Content to write
        mode: File permissions (default: 0o600 - owner read/write only)
    """
    # Create secure temporary file first
    import tempfile
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath))
    
    try:
        # Write content
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set permissions
        os.chmod(temp_path, mode)
        
        # Atomic rename
        os.replace(temp_path, filepath)
    except:
        # Clean up on error
        try:
            os.unlink(temp_path)
        except:
            pass
        raise

# Input Validation Functions

def validate_symbol(symbol: str) -> str:
    """Validate trading symbol format"""
    if not symbol or not VALID_SYMBOLS.match(symbol):
        raise ValidationError(f"Invalid symbol format: {symbol}")
    return symbol.upper()

def validate_direction(direction: str) -> str:
    """Validate trade direction"""
    direction_upper = direction.upper()
    if direction_upper not in VALID_DIRECTIONS:
        raise ValidationError(f"Invalid direction: {direction}")
    return direction_upper

def validate_volume(volume: Union[float, str, decimal.Decimal]) -> decimal.Decimal:
    """Validate trade volume with decimal precision"""
    try:
        vol_decimal = decimal.Decimal(str(volume))
    except:
        raise ValidationError(f"Invalid volume format: {volume}")
    
    if not MIN_VOLUME <= vol_decimal <= MAX_VOLUME:
        raise ValidationError(f"Volume out of range: {volume}")
    
    # Round to 2 decimal places
    return vol_decimal.quantize(decimal.Decimal('0.01'))

def validate_price(price: Union[float, str, decimal.Decimal]) -> decimal.Decimal:
    """Validate price with decimal precision"""
    try:
        price_decimal = decimal.Decimal(str(price))
    except:
        raise ValidationError(f"Invalid price format: {price}")
    
    if price_decimal < 0:
        raise ValidationError(f"Price cannot be negative: {price}")
    
    if not MIN_PRICE <= price_decimal <= MAX_PRICE:
        raise ValidationError(f"Price out of range: {price}")
    
    # Round to 5 decimal places
    return price_decimal.quantize(decimal.Decimal('0.00001'))

def validate_risk_percent(risk: Union[float, str, decimal.Decimal]) -> decimal.Decimal:
    """Validate risk percentage"""
    try:
        risk_decimal = decimal.Decimal(str(risk))
    except:
        raise ValidationError(f"Invalid risk format: {risk}")
    
    if risk_decimal < 0:
        raise ValidationError("Risk cannot be negative")
    
    if risk_decimal > MAX_RISK_PERCENT:
        raise ValidationError(f"Risk exceeds maximum allowed: {risk}% > {MAX_RISK_PERCENT}%")
    
    return risk_decimal.quantize(decimal.Decimal('0.01'))

def validate_account_balance(balance: Union[float, str, decimal.Decimal]) -> decimal.Decimal:
    """Validate account balance"""
    try:
        balance_decimal = decimal.Decimal(str(balance))
    except:
        raise ValidationError(f"Invalid balance format: {balance}")
    
    if balance_decimal < MIN_BALANCE:
        raise ValidationError(f"Balance too low: {balance}")
    
    return balance_decimal.quantize(decimal.Decimal('0.01'))

# JSON Security Functions

def safe_json_loads(json_str: str, max_size: int = 1024 * 100) -> Dict[str, Any]:
    """
    Safely parse JSON with size limits
    
    Args:
        json_str: JSON string to parse
        max_size: Maximum allowed size
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        ValidationError: If JSON is invalid or too large
    """
    if len(json_str) > max_size:
        raise ValidationError("JSON string too large")
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")
    
    # Validate it's a dictionary
    if not isinstance(data, dict):
        raise ValidationError("JSON must be an object")
    
    return data

def safe_json_dumps(data: Dict[str, Any], max_size: int = 1024 * 100) -> str:
    """
    Safely serialize JSON with size limits
    
    Args:
        data: Dictionary to serialize
        max_size: Maximum allowed output size
        
    Returns:
        JSON string
        
    Raises:
        ValidationError: If output would be too large
    """
    try:
        json_str = json.dumps(data, separators=(',', ':'))
    except Exception as e:
        raise ValidationError(f"JSON serialization error: {e}")
    
    if len(json_str) > max_size:
        raise ValidationError("JSON output too large")
    
    return json_str

# File Integrity Functions

def calculate_file_hmac(filepath: str, key: Optional[bytes] = None) -> str:
    """Calculate HMAC for file integrity verification"""
    if key is None:
        key = _secure_config.file_hmac_key
    
    h = hmac.new(key, digestmod=hashlib.sha256)
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    
    return h.hexdigest()

def verify_file_hmac(filepath: str, expected_hmac: str, key: Optional[bytes] = None) -> bool:
    """Verify file integrity using HMAC"""
    if key is None:
        key = _secure_config.file_hmac_key
    
    actual_hmac = calculate_file_hmac(filepath, key)
    return hmac.compare_digest(actual_hmac, expected_hmac)

# Sanitization Functions

def sanitize_log_output(message: str, sensitive_fields: Optional[List[str]] = None) -> str:
    """
    Sanitize log messages to remove sensitive information
    
    Args:
        message: Log message to sanitize
        sensitive_fields: List of field names to redact
        
    Returns:
        Sanitized message
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'key', 'secret', 'balance', 'equity']
    
    sanitized = message
    
    # Redact sensitive fields
    for field in sensitive_fields:
        # Pattern to match field:value or "field":"value"
        patterns = [
            rf'{field}\s*:\s*"[^"]*"',
            rf'{field}\s*:\s*\'[^\']*\'',
            rf'{field}\s*:\s*[^\s,}}]+',
            rf'"{field}"\s*:\s*"[^"]*"',
            rf'"{field}"\s*:\s*[^\s,}}]+'
        ]
        
        for pattern in patterns:
            sanitized = re.sub(pattern, f'{field}:***REDACTED***', sanitized, flags=re.IGNORECASE)
    
    # Redact numbers that look like balances (4+ digits)
    sanitized = re.sub(r'\b\d{4,}\.\d{2}\b', '***REDACTED***', sanitized)
    
    return sanitized

def sanitize_trade_comment(comment: str, max_length: int = 100) -> str:
    """
    Sanitize trade comment to prevent injection
    
    Args:
        comment: Trade comment to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized comment
    """
    if not comment:
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', comment)[:max_length]
    
    # Remove potential injection patterns
    injection_patterns = [
        r'<[^>]*>',  # HTML tags
        r'\$\{[^}]*\}',  # Template injection
        r'{{[^}]*}}',  # Template injection
        r'%\{[^}]*\}',  # Template injection
    ]
    
    for pattern in injection_patterns:
        sanitized = re.sub(pattern, '', sanitized)
    
    return sanitized.strip()

# Rate Limiting

class RateLimiter:
    """Simple rate limiter for trade operations"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user is within rate limits
        
        Args:
            user_id: User identifier
            
        Returns:
            True if within limits, False if exceeded
        """
        import time
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            uid: times for uid, times in self.requests.items()
            if times and times[-1] > current_time - self.window_seconds
        }
        
        # Check user's requests
        user_requests = self.requests.get(user_id, [])
        recent_requests = [t for t in user_requests if t > current_time - self.window_seconds]
        
        if len(recent_requests) >= self.max_requests:
            return False
        
        # Add current request
        if user_id not in self.requests:
            self.requests[user_id] = []
        self.requests[user_id].append(current_time)
        
        return True

# Secure Communication

def generate_secure_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
    """
    Hash a password securely
    
    Args:
        password: Password to hash
        salt: Optional salt (will be generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    
    # Use PBKDF2 with SHA256
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    return hashed.hex(), salt

def verify_password(password: str, hashed: str, salt: bytes) -> bool:
    """Verify a password against its hash"""
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, hashed)

# Example usage in other modules:
"""
from .security_utils import (
    validate_symbol, validate_direction, validate_volume,
    validate_safe_path, secure_file_write, secure_file_read,
    safe_json_loads, sanitize_log_output, RateLimiter
)

# In mt5_bridge_adapter.py:
def execute_trade(self, symbol: str, direction: str, volume: float, ...):
    # Validate inputs
    symbol = validate_symbol(symbol)
    direction = validate_direction(direction)
    volume = validate_volume(volume)
    
    # Rate limiting
    if not self.rate_limiter.check_rate_limit(str(user_id)):
        raise SecurityError("Rate limit exceeded")
    
    # Secure file operations
    safe_path = validate_safe_path(self.mt5_files_path, self.instruction_file)
    secure_file_write(safe_path, instruction.to_csv())

# In risk_management.py:
def calculate_position_size(self, account: AccountInfo, ...):
    # Validate account info
    balance = validate_account_balance(account.balance)
    
    # Prevent division by zero
    if pip_value == 0:
        raise ValidationError("Invalid pip value: 0")
    
    # Use decimal for financial calculations
    risk_amount = balance * (risk_percent / decimal.Decimal('100'))
"""