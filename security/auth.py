"""
BITTEN Security Module
JWT Authentication and Authorization System
"""
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from config.settings import SECURITY_CONFIG
from database.models import get_db, User, get_user_by_telegram_id

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token
security = HTTPBearer()

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = SECURITY_CONFIG["jwt_secret"]
        self.algorithm = SECURITY_CONFIG["jwt_algorithm"]
        self.expiration_hours = SECURITY_CONFIG["jwt_expiration"]
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

# Global auth manager
auth_manager = AuthManager()

# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    telegram_id = payload.get("telegram_id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

async def require_tier(required_tier: str):
    """Dependency factory for tier-based authorization"""
    async def tier_check(current_user: User = Depends(get_current_user)) -> User:
        tier_hierarchy = {
            "NIBBLER": 1,
            "SCOUT": 2, 
            "WARRIOR": 3,
            "COMMANDER": 4,
            "APEX": 5
        }
        
        user_tier_level = tier_hierarchy.get(current_user.tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 999)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient tier level. Required: {required_tier}, Current: {current_user.tier}"
            )
        
        return current_user
    
    return tier_check

# Specific tier requirements
require_scout = require_tier("SCOUT")
require_warrior = require_tier("WARRIOR") 
require_commander = require_tier("COMMANDER")
require_apex = require_tier("APEX")

class TelegramAuth:
    """Telegram-specific authentication"""
    
    @staticmethod
    def verify_telegram_hash(data: Dict[str, Any], bot_token: str) -> bool:
        """Verify Telegram webhook hash"""
        import hashlib
        import hmac
        
        received_hash = data.pop("hash", None)
        if not received_hash:
            return False
        
        # Create data string
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
        
        # Create secret key
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(received_hash, calculated_hash)
    
    @staticmethod
    def create_user_token(telegram_id: str, username: str = None) -> str:
        """Create token for Telegram user"""
        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "source": "telegram"
        }
        return auth_manager.create_access_token(user_data)

class APIKeyAuth:
    """API key authentication for external services"""
    
    def __init__(self):
        self.api_keys = {}  # In production, store in database
    
    def create_api_key(self, user_id: str, name: str) -> str:
        """Create API key for user"""
        api_key = auth_manager.generate_api_key()
        self.api_keys[api_key] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key"""
        key_data = self.api_keys.get(api_key)
        if key_data:
            key_data["last_used"] = datetime.utcnow()
            return key_data
        return None

# Global API key manager
api_key_manager = APIKeyAuth()

# Rate limiting
class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).seconds < window
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter()

def check_rate_limit(key: str, limit: int = 60, window: int = 60):
    """Rate limiting dependency"""
    if not rate_limiter.is_allowed(key, limit, window):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True

# Security utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def validate_input(data: str, max_length: int = 1000) -> str:
    """Basic input validation"""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input cannot be empty"
        )
    
    if len(data) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long. Maximum {max_length} characters"
        )
    
    # Basic XSS prevention
    dangerous_chars = ["<", ">", "script", "javascript:", "data:"]
    data_lower = data.lower()
    
    for char in dangerous_chars:
        if char in data_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters detected"
            )
    
    return data

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data (placeholder - implement proper encryption)"""
    # In production, use proper encryption library
    import base64
    return base64.b64encode(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data (placeholder - implement proper decryption)"""
    # In production, use proper decryption library
    import base64
    return base64.b64decode(encrypted_data.encode()).decode()