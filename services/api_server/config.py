"""
BITTEN v2.0 API Server Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8888"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Database Configuration - SQLite (bitten.db is the source of truth)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////root/HydraX-v2/bitten.db")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "-1002581996861")

# Redis Configuration (for WebSocket pub/sub)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "bitten-secret-key-change-in-production")
API_KEY_HEADER = "X-Api-Key"

# Fire System
FIRE_QUEUE_IPC = "ipc:///tmp/bitten_cmdqueue"

# Templates
TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
