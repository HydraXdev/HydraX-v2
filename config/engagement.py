"""
Configuration settings for HydraX v2 Engagement System
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import timedelta

# Environment variables
ENGAGEMENT_DB_URL = os.getenv('ENGAGEMENT_DB_URL', 'sqlite:///data/engagement.db')
ENGAGEMENT_LOG_LEVEL = os.getenv('ENGAGEMENT_LOG_LEVEL', 'INFO')
ENGAGEMENT_DEBUG = os.getenv('ENGAGEMENT_DEBUG', 'false').lower() == 'true'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
FUSION_DASHBOARD_PORT = int(os.getenv('FUSION_DASHBOARD_PORT', '5000'))
FUSION_DASHBOARD_HOST = os.getenv('FUSION_DASHBOARD_HOST', '0.0.0.0')


@dataclass
class EngagementConfig:
    """Configuration for engagement system"""
    
    # Database settings
    database_url: str = ENGAGEMENT_DB_URL
    database_echo: bool = ENGAGEMENT_DEBUG
    
    # Logging settings
    log_level: str = ENGAGEMENT_LOG_LEVEL
    log_file: str = 'logs/engagement.log'
    
    # Login streak settings
    streak_milestones: Dict[int, List[Dict[str, Any]]] = None
    streak_grace_period_hours: int = 6  # Hours after midnight to still count as previous day
    
    # Daily mission settings
    max_daily_missions: int = 3
    mission_expiry_hours: int = 24
    mission_refresh_hour: int = 0  # UTC hour to refresh missions
    
    # Mystery box settings
    mystery_box_rates: Dict[str, float] = None
    mystery_box_max_contents: int = 5
    
    # Seasonal campaign settings
    campaign_xp_multiplier: float = 1.0
    campaign_max_milestones: int = 10
    
    # Performance settings
    cache_timeout_seconds: int = 300  # 5 minutes
    batch_size: int = 100
    cleanup_interval_hours: int = 24
    
    # Dashboard settings
    dashboard_update_interval: int = 5  # seconds
    dashboard_max_signals: int = 20
    dashboard_history_days: int = 7
    
    def __post_init__(self):
        """Initialize default values"""
        if self.streak_milestones is None:
            self.streak_milestones = {
                3: [
                    {'type': 'bits', 'amount': 500, 'metadata': {'bonus': 'first_milestone'}},
                    {'type': 'xp', 'amount': 100, 'metadata': {'source': 'streak_bonus'}}
                ],
                7: [
                    {'type': 'bits', 'amount': 1000, 'metadata': {'bonus': 'week_milestone'}},
                    {'type': 'mystery_box', 'amount': 1, 'metadata': {'rarity': 'common'}}
                ],
                14: [
                    {'type': 'bits', 'amount': 2000, 'metadata': {'bonus': 'fortnight_milestone'}},
                    {'type': 'rare_item', 'amount': 1, 'metadata': {'category': 'weapon_skin'}}
                ],
                30: [
                    {'type': 'bits', 'amount': 5000, 'metadata': {'bonus': 'month_milestone'}},
                    {'type': 'legendary_box', 'amount': 1, 'metadata': {'guaranteed_rare': True}}
                ],
                60: [
                    {'type': 'bits', 'amount': 10000, 'metadata': {'bonus': 'dedication_milestone'}},
                    {'type': 'exclusive_bot', 'amount': 1, 'metadata': {'rarity': 'legendary'}}
                ],
                100: [
                    {'type': 'bits', 'amount': 20000, 'metadata': {'bonus': 'centurion_milestone'}},
                    {'type': 'title', 'amount': 1, 'metadata': {'title': 'Dedicated Warrior'}}
                ]
            }
        
        if self.mystery_box_rates is None:
            self.mystery_box_rates = {
                'common': 0.50,
                'uncommon': 0.30,
                'rare': 0.15,
                'epic': 0.04,
                'legendary': 0.01
            }


@dataclass
class FusionDashboardConfig:
    """Configuration for fusion dashboard"""
    
    # Server settings
    host: str = FUSION_DASHBOARD_HOST
    port: int = FUSION_DASHBOARD_PORT
    debug: bool = ENGAGEMENT_DEBUG
    
    # SocketIO settings
    socketio_cors_origins: str = "*"
    socketio_async_mode: str = "threading"
    socketio_log_level: str = "INFO"
    
    # Update settings
    update_interval: int = 5  # seconds
    max_active_signals: int = 20
    history_retention_days: int = 7
    
    # Performance settings
    enable_caching: bool = True
    cache_timeout: int = 60  # seconds
    
    # UI settings
    theme: str = "dark"
    chart_update_interval: int = 10  # seconds
    notification_timeout: int = 5000  # milliseconds


@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    
    # Main database
    url: str = ENGAGEMENT_DB_URL
    echo: bool = ENGAGEMENT_DEBUG
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    
    # Connection settings
    connect_timeout: int = 30
    query_timeout: int = 60
    
    # Backup settings
    backup_interval_hours: int = 24
    backup_retention_days: int = 7
    backup_directory: str = "backups/engagement"


@dataclass
class CacheConfig:
    """Configuration for caching"""
    
    # Redis settings
    redis_url: str = REDIS_URL
    redis_db: int = 1  # Use separate DB for engagement cache
    redis_timeout: int = 5
    
    # Cache settings
    default_ttl: int = 300  # 5 minutes
    user_streak_ttl: int = 86400  # 24 hours
    campaign_ttl: int = 3600  # 1 hour
    mission_ttl: int = 1800  # 30 minutes
    
    # Performance settings
    max_connections: int = 10
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    
    # Log levels
    level: str = ENGAGEMENT_LOG_LEVEL
    file_level: str = "INFO"
    console_level: str = "INFO"
    
    # File settings
    log_dir: str = "logs"
    log_file: str = "engagement.log"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    backup_count: int = 5
    
    # Format settings
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Component-specific settings
    engagement_level: str = "INFO"
    dashboard_level: str = "INFO"
    database_level: str = "WARNING"
    cache_level: str = "WARNING"


# Create configuration instances
engagement_config = EngagementConfig()
dashboard_config = FusionDashboardConfig()
database_config = DatabaseConfig()
cache_config = CacheConfig()
logging_config = LoggingConfig()


# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate database URL
    if not database_config.url:
        errors.append("Database URL must be provided")
    
    # Validate streak milestones
    if not engagement_config.streak_milestones:
        errors.append("Streak milestones must be configured")
    
    # Validate mystery box rates
    if engagement_config.mystery_box_rates:
        total_rate = sum(engagement_config.mystery_box_rates.values())
        if abs(total_rate - 1.0) > 0.01:
            errors.append(f"Mystery box rates must sum to 1.0, got {total_rate}")
    
    # Validate dashboard settings
    if dashboard_config.port < 1 or dashboard_config.port > 65535:
        errors.append("Dashboard port must be between 1 and 65535")
    
    # Validate cache settings
    if cache_config.default_ttl < 1:
        errors.append("Cache TTL must be positive")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {errors}")
    
    return True


# Environment-specific configurations
def get_config_for_environment(env: str = "development") -> Dict[str, Any]:
    """Get configuration for specific environment"""
    
    base_config = {
        'engagement': engagement_config,
        'dashboard': dashboard_config,
        'database': database_config,
        'cache': cache_config,
        'logging': logging_config
    }
    
    if env == "production":
        # Production-specific overrides
        base_config['logging'].level = "WARNING"
        base_config['database'].echo = False
        base_config['dashboard'].debug = False
        base_config['cache'].default_ttl = 600  # 10 minutes
        
    elif env == "testing":
        # Testing-specific overrides
        base_config['database'].url = "sqlite:///:memory:"
        base_config['cache'].redis_url = "redis://localhost:6379/15"  # Test DB
        base_config['logging'].level = "DEBUG"
        base_config['engagement'].cache_timeout_seconds = 1  # Fast invalidation
        
    elif env == "development":
        # Development-specific overrides
        base_config['logging'].level = "DEBUG"
        base_config['database'].echo = True
        base_config['dashboard'].debug = True
        base_config['engagement'].cache_timeout_seconds = 10  # Quick refresh
    
    return base_config


# Feature flags
class FeatureFlags:
    """Feature flags for engagement system"""
    
    # Core features
    ENABLE_LOGIN_STREAKS = True
    ENABLE_DAILY_MISSIONS = True
    ENABLE_MYSTERY_BOXES = True
    ENABLE_SEASONAL_CAMPAIGNS = True
    ENABLE_PERSONAL_RECORDS = True
    
    # Dashboard features
    ENABLE_FUSION_DASHBOARD = True
    ENABLE_REAL_TIME_UPDATES = True
    ENABLE_PERFORMANCE_CHARTS = True
    
    # Advanced features
    ENABLE_CACHING = True
    ENABLE_BACKGROUND_TASKS = True
    ENABLE_ANALYTICS = True
    ENABLE_A_B_TESTING = False  # Disabled by default
    
    # Integration features
    ENABLE_TELEGRAM_INTEGRATION = True
    ENABLE_WEBAPP_INTEGRATION = True
    ENABLE_API_ENDPOINTS = True
    
    # Debug features
    ENABLE_DEBUG_ENDPOINTS = ENGAGEMENT_DEBUG
    ENABLE_MOCK_DATA = ENGAGEMENT_DEBUG
    ENABLE_PROFILING = False


# Export configuration
__all__ = [
    'EngagementConfig',
    'FusionDashboardConfig', 
    'DatabaseConfig',
    'CacheConfig',
    'LoggingConfig',
    'engagement_config',
    'dashboard_config',
    'database_config',
    'cache_config',
    'logging_config',
    'validate_config',
    'get_config_for_environment',
    'FeatureFlags'
]