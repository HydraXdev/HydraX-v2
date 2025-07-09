"""
Configuration manager for the intelligence system
Handles API keys, settings, and environment-specific configurations
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import asyncio
from datetime import datetime


@dataclass
class APIConfig:
    """Configuration for external APIs"""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 100
    timeout: int = 30
    retry_count: int = 3
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class DataSourceConfig:
    """Configuration for data sources"""
    name: str
    type: str
    enabled: bool = True
    priority: int = 1
    batch_size: int = 100
    update_interval: int = 60
    connection_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connection_params is None:
            self.connection_params = {}


@dataclass
class CacheConfig:
    """Configuration for caching system"""
    enabled: bool = True
    backend: str = "redis"
    ttl_default: int = 300
    ttl_signals: int = 600
    ttl_market_data: int = 60
    max_size: int = 10000
    connection_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connection_params is None:
            self.connection_params = {}


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and logging"""
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    metrics_enabled: bool = True
    metrics_port: int = 9090
    alert_webhooks: List[str] = None
    performance_tracking: bool = True
    
    def __post_init__(self):
        if self.alert_webhooks is None:
            self.alert_webhooks = []


class ConfigManager:
    """Manages all configuration for the intelligence system"""
    
    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/intelligence")
        self.env_file = env_file or ".env"
        self._config: Dict[str, Any] = {}
        self._api_configs: Dict[str, APIConfig] = {}
        self._data_source_configs: Dict[str, DataSourceConfig] = {}
        self._cache_config: Optional[CacheConfig] = None
        self._monitoring_config: Optional[MonitoringConfig] = None
        self._encryption_key: Optional[bytes] = None
        self.logger = logging.getLogger("intelligence.config")
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Initialize encryption
        self._init_encryption()
        
    def _init_encryption(self) -> None:
        """Initialize encryption for sensitive data"""
        key = os.getenv("INTELLIGENCE_ENCRYPTION_KEY")
        if not key:
            # Generate new key if not exists
            key = Fernet.generate_key()
            self.logger.warning("No encryption key found, generating new one")
        else:
            key = key.encode() if isinstance(key, str) else key
        self._encryption_key = key
        self._cipher = Fernet(self._encryption_key)
        
    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value"""
        return self._cipher.encrypt(value.encode()).decode()
        
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value"""
        return self._cipher.decrypt(encrypted_value.encode()).decode()
        
    async def load_config(self) -> None:
        """Load all configuration files"""
        try:
            # Create config directory if not exists
            self.config_path.mkdir(parents=True, exist_ok=True)
            
            # Load main config
            main_config_file = self.config_path / "config.yaml"
            if main_config_file.exists():
                with open(main_config_file, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self.logger.warning(f"Main config file not found: {main_config_file}")
                self._config = self._get_default_config()
                
            # Load API configs
            api_config_file = self.config_path / "apis.yaml"
            if api_config_file.exists():
                with open(api_config_file, 'r') as f:
                    api_data = yaml.safe_load(f) or {}
                    for name, config in api_data.items():
                        self._api_configs[name] = APIConfig(name=name, **config)
                        
            # Load data source configs
            sources_config_file = self.config_path / "data_sources.yaml"
            if sources_config_file.exists():
                with open(sources_config_file, 'r') as f:
                    sources_data = yaml.safe_load(f) or {}
                    for name, config in sources_data.items():
                        self._data_source_configs[name] = DataSourceConfig(name=name, **config)
                        
            # Load cache config
            cache_config = self._config.get('cache', {})
            self._cache_config = CacheConfig(**cache_config)
            
            # Load monitoring config
            monitoring_config = self._config.get('monitoring', {})
            self._monitoring_config = MonitoringConfig(**monitoring_config)
            
            # Override with environment variables
            self._apply_env_overrides()
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'name': 'HydraX Intelligence System',
                'version': '2.0.0',
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true'
            },
            'cache': {
                'enabled': True,
                'backend': 'redis',
                'ttl_default': 300
            },
            'monitoring': {
                'log_level': 'INFO',
                'metrics_enabled': True
            },
            'processing': {
                'max_workers': 10,
                'batch_size': 100,
                'timeout': 300
            }
        }
        
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # API keys from environment
        for key, value in os.environ.items():
            if key.startswith('API_KEY_'):
                api_name = key.replace('API_KEY_', '').lower()
                if api_name not in self._api_configs:
                    self._api_configs[api_name] = APIConfig(name=api_name)
                self._api_configs[api_name].api_key = value
                
            elif key.startswith('API_SECRET_'):
                api_name = key.replace('API_SECRET_', '').lower()
                if api_name not in self._api_configs:
                    self._api_configs[api_name] = APIConfig(name=api_name)
                self._api_configs[api_name].api_secret = value
                
    async def save_config(self) -> None:
        """Save current configuration to files"""
        try:
            # Save main config
            main_config_file = self.config_path / "config.yaml"
            with open(main_config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
                
            # Save API configs (encrypt sensitive data)
            api_config_file = self.config_path / "apis.yaml"
            api_data = {}
            for name, config in self._api_configs.items():
                config_dict = asdict(config)
                # Encrypt sensitive fields
                if config.api_key:
                    config_dict['api_key'] = self.encrypt_value(config.api_key)
                if config.api_secret:
                    config_dict['api_secret'] = self.encrypt_value(config.api_secret)
                api_data[name] = config_dict
            with open(api_config_file, 'w') as f:
                yaml.dump(api_data, f, default_flow_style=False)
                
            # Save data source configs
            sources_config_file = self.config_path / "data_sources.yaml"
            sources_data = {name: asdict(config) for name, config in self._data_source_configs.items()}
            with open(sources_config_file, 'w') as f:
                yaml.dump(sources_data, f, default_flow_style=False)
                
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def get_api_config(self, name: str) -> Optional[APIConfig]:
        """Get API configuration by name"""
        return self._api_configs.get(name)
        
    def add_api_config(self, config: APIConfig) -> None:
        """Add or update API configuration"""
        self._api_configs[config.name] = config
        
    def get_data_source_config(self, name: str) -> Optional[DataSourceConfig]:
        """Get data source configuration by name"""
        return self._data_source_configs.get(name)
        
    def add_data_source_config(self, config: DataSourceConfig) -> None:
        """Add or update data source configuration"""
        self._data_source_configs[config.name] = config
        
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self._cache_config
        
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self._monitoring_config
        
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations as dictionary"""
        return {
            'main': self._config,
            'apis': {name: asdict(config) for name, config in self._api_configs.items()},
            'data_sources': {name: asdict(config) for name, config in self._data_source_configs.items()},
            'cache': asdict(self._cache_config) if self._cache_config else {},
            'monitoring': asdict(self._monitoring_config) if self._monitoring_config else {}
        }
        
    async def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required API keys
        required_apis = self.get('required_apis', [])
        for api_name in required_apis:
            if api_name not in self._api_configs:
                issues.append(f"Required API config missing: {api_name}")
            elif not self._api_configs[api_name].api_key:
                issues.append(f"API key missing for: {api_name}")
                
        # Check data sources
        if not self._data_source_configs:
            issues.append("No data sources configured")
            
        # Check cache backend
        if self._cache_config.enabled and self._cache_config.backend == 'redis':
            # Check if Redis connection params are provided
            if not self._cache_config.connection_params:
                issues.append("Redis connection parameters not configured")
                
        return issues
        
    def to_env_file(self, filepath: Optional[str] = None) -> None:
        """Export configuration to .env file format"""
        filepath = filepath or '.env.intelligence'
        lines = []
        
        # System config
        lines.append("# Intelligence System Configuration")
        lines.append(f"INTELLIGENCE_ENV={self.get('system.environment', 'development')}")
        lines.append(f"INTELLIGENCE_DEBUG={self.get('system.debug', False)}")
        lines.append("")
        
        # API Keys
        lines.append("# API Keys")
        for name, config in self._api_configs.items():
            if config.api_key:
                lines.append(f"API_KEY_{name.upper()}={config.api_key}")
            if config.api_secret:
                lines.append(f"API_SECRET_{name.upper()}={config.api_secret}")
        lines.append("")
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
            
        self.logger.info(f"Configuration exported to {filepath}")