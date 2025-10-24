"""
Configuration for ZMQ Gateway Service
"""
import os

# ZMQ Ports
PORT_MARKET_DATA_IN = 5556  # PULL from EA (ticks, heartbeats)
PORT_METRICS_IN = 5560  # PULL from EA (position_update)
PORT_MARKET_DATA_OUT = 5570  # PUB to subscribers (broadcast)
PORT_COMMAND_ROUTER = 5555  # ROUTER for fire commands
PORT_CONFIRMATIONS = 5558  # PULL from EA
PORT_IPC_QUEUE = "ipc:///tmp/bitten_cmdqueue"  # PULL from webapp

# Health monitoring
HEALTH_PORT = 9091

# Database
DB_PATH = os.getenv("BITTEN_DB", "/root/HydraX-v2/bitten.db")  # Legacy SQLite (deprecated)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
)

# Timeouts
HEARTBEAT_SEC = int(os.getenv("BITTEN_EA_TTL_SEC", "120"))
COMMAND_TIMEOUT_SEC = 10
ROUTER_POLL_TIMEOUT_MS = 1000

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
