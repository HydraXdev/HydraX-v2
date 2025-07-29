"""
BITTEN Configuration Management
Environment-based settings replacing hardcoded values
ForexVPS-Aligned Architecture
"""
import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = {"extra": "allow", "env_file": ".env", "case_sensitive": True}
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://bitten:bitten_secure_2025@localhost/bitten_production"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    VOICE_BOT_TOKEN: str = os.getenv("VOICE_BOT_TOKEN", "")
    WEBHOOK_URL: Optional[str] = None
    
    # ForexVPS Integration (NEW - NO MORE DOCKER/WINE)
    FOREXVPS_API_URL: str = "https://api.forexvps.com/v1"
    VPS_API_KEY: str = os.getenv("VPS_API_KEY", "")
    VPS_WEBHOOK_URL: str = os.getenv("VPS_WEBHOOK_URL", "")
    VPS_TIMEOUT: int = 30
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "bitten_jwt_secret_2025")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "bitten_encryption_2025")
    
    # Application
    HOST: str = "0.0.0.0"
    PORT: int = 8888
    DEBUG: bool = False
    WORKERS: int = 4
    
    # External Services
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # DEPRECATED - NO LONGER USED (ForexVPS Migration)
    # BRIDGE_PORT: Removed - No bridge ports with ForexVPS
    # CONTAINER_REGISTRY: Removed - No containers with ForexVPS
    # WINE_PATH: Removed - No Wine with ForexVPS
    # DOCKER_SOCKET: Removed - No Docker with ForexVPS
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance
    CONNECTION_POOL_SIZE: int = 20
    CONNECTION_POOL_MAX_OVERFLOW: int = 30
    REDIS_CONNECTION_POOL_SIZE: int = 50
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Signal Generation
    VENOM_ENGINE_ENABLED: bool = True
    CITADEL_SHIELD_ENABLED: bool = True
    SIGNAL_EXPIRY_MINUTES: int = 35
    MAX_SIGNALS_PER_DAY: int = 25
    
    # Trading
    DEFAULT_RISK_PERCENT: float = 2.0
    MAX_CONCURRENT_TRADES: int = 5
    TRADE_TIMEOUT_SECONDS: int = 30
    

# Global settings instance
settings = Settings()

# ForexVPS API Configuration
FOREXVPS_CONFIG = {
    "base_url": settings.FOREXVPS_API_URL,
    "api_key": settings.VPS_API_KEY,
    "timeout": settings.VPS_TIMEOUT,
    "headers": {
        "Authorization": f"Bearer {settings.VPS_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "BITTEN-v6.1"
    }
}

# Database Configuration
DATABASE_CONFIG = {
    "url": settings.DATABASE_URL,
    "pool_size": settings.CONNECTION_POOL_SIZE,
    "max_overflow": settings.CONNECTION_POOL_MAX_OVERFLOW,
    "echo": settings.DEBUG
}

# Redis Configuration  
REDIS_CONFIG = {
    "url": settings.REDIS_URL,
    "connection_pool_kwargs": {
        "max_connections": settings.REDIS_CONNECTION_POOL_SIZE
    }
}

# Security Configuration
SECURITY_CONFIG = {
    "jwt_secret": settings.JWT_SECRET_KEY,
    "jwt_algorithm": settings.JWT_ALGORITHM,
    "jwt_expiration": settings.JWT_EXPIRATION_HOURS,
    "encryption_key": settings.ENCRYPTION_KEY
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": settings.LOG_FORMAT,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": "/var/log/bitten/application.log",
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["default", "file"],
    },
}

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def validate_settings() -> bool:
    """Validate required settings"""
    required_settings = [
        "BOT_TOKEN",
        "VPS_API_KEY",
        "JWT_SECRET_KEY"
    ]
    
    missing = []
    for setting in required_settings:
        if not getattr(settings, setting):
            missing.append(setting)
    
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")
    
    return True

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
elif os.getenv("ENVIRONMENT") == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"