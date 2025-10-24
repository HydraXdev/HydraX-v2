#!/usr/bin/env python3
"""
Fire Service Configuration
Central configuration for fire execution service
"""

import os
from pathlib import Path


class FireServiceConfig:
    """Fire service configuration"""

    # Service identity
    SERVICE_NAME = "fire_service"
    VERSION = "2.0.0"

    # Database paths
    BASE_DIR = Path("/root/HydraX-v2")
    BITTEN_DB = BASE_DIR / "bitten.db"  # Legacy SQLite (deprecated)
    FIRE_MODE_DB = BASE_DIR / "data" / "fire_modes.db"

    # PostgreSQL v2 database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
    )

    # ZMQ configuration
    IPC_QUEUE = "ipc:///tmp/bitten_cmdqueue"
    COMMAND_ROUTER_PORT = 5555
    CONFIRM_LISTENER_PORT = 5558

    # Risk management
    MANUAL_RISK_PCT = 2.0  # 2% risk for manual fires
    AUTO_RISK_PCT = 5.0    # 5% risk for AUTO fires (testing mode)
    MAX_RISK_PCT = 10.0    # Maximum allowed risk

    # BITMODE v2 configuration
    BITMODE_PARTIAL1_TRIGGER = 8.0   # First partial close at +8 pips
    BITMODE_PARTIAL1_PERCENT = 25.0  # Close 25% of position
    BITMODE_PARTIAL2_TRIGGER = 12.0  # Second partial close at +12 pips
    BITMODE_PARTIAL2_PERCENT = 25.0  # Close 25% of position
    BITMODE_TRAIL_DISTANCE = 8.0     # Trailing stop distance

    # Symbol specifications
    SYMBOL_SPECS = {
        "EURUSD": {"digits": 5, "pip_size": 0.0001, "pip_value": 10.0},
        "GBPUSD": {"digits": 5, "pip_size": 0.0001, "pip_value": 10.0},
        "USDJPY": {"digits": 3, "pip_size": 0.01, "pip_value": 9.09},
        "EURJPY": {"digits": 3, "pip_size": 0.01, "pip_value": 9.09},
        "GBPJPY": {"digits": 3, "pip_size": 0.01, "pip_value": 9.09},
        "XAUUSD": {"digits": 2, "pip_size": 0.01, "pip_value": 10.0},
        "XAGUSD": {"digits": 3, "pip_size": 0.001, "pip_value": 5.0},
    }

    # Default symbol spec for unlisted pairs
    DEFAULT_SPEC = {"digits": 5, "pip_size": 0.0001, "pip_value": 10.0}

    # Execution timeouts
    FIRE_TIMEOUT_SECONDS = 30
    CONFIRMATION_TIMEOUT_SECONDS = 60

    # API configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8890
    API_WORKERS = 2

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Tier limits
    TIER_LIMITS = {
        "NIBBLER": {"manual": 1, "auto": 0, "total": 1},
        "FANG": {"manual": 2, "auto": 0, "total": 2},
        "COMMANDER": {"manual": 10, "auto": 10, "total": 10},
    }

    @classmethod
    def get_symbol_spec(cls, symbol: str) -> dict:
        """Get symbol specification"""
        return cls.SYMBOL_SPECS.get(symbol, cls.DEFAULT_SPEC)

    @classmethod
    def get_pip_size(cls, symbol: str) -> float:
        """Get pip size for symbol"""
        return cls.get_symbol_spec(symbol)["pip_size"]

    @classmethod
    def get_pip_value(cls, symbol: str) -> float:
        """Get pip value for symbol"""
        return cls.get_symbol_spec(symbol)["pip_value"]

    @classmethod
    def calculate_pips(cls, symbol: str, price1: float, price2: float) -> float:
        """Calculate pip difference between two prices"""
        pip_size = cls.get_pip_size(symbol)
        return abs(price1 - price2) / pip_size


# Create singleton instance
config = FireServiceConfig()
