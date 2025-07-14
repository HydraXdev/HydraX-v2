"""
MetaQuotes Demo Account Provisioning Module

Production-ready integration with MetaQuotes for instant demo account creation,
secure credential delivery, and lifecycle management.
"""

from .demo_account_service import (
    DemoAccountService,
    DemoAccountConfig,
    AccountStatus,
    HealthStatus,
    get_demo_account_service
)

from .account_pool_manager import (
    AccountPoolManager,
    PoolConfig,
    get_pool_manager
)

from .credential_delivery import (
    SecureCredentialDelivery,
    DeliveryMethod,
    DeliveryStatus,
    CredentialPackage
)

__all__ = [
    # Services
    'DemoAccountService',
    'AccountPoolManager', 
    'SecureCredentialDelivery',
    
    # Configs
    'DemoAccountConfig',
    'PoolConfig',
    
    # Enums
    'AccountStatus',
    'HealthStatus',
    'DeliveryMethod',
    'DeliveryStatus',
    
    # Types
    'CredentialPackage',
    
    # Singletons
    'get_demo_account_service',
    'get_pool_manager'
]