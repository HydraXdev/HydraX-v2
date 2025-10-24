"""
Analytics Worker Configuration
"""
import os
from typing import Dict, Any

# PostgreSQL Connection
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/bitten_v2'
)

# ZMQ Market Data
ZMQ_MARKET_DATA_PORT = 5560
ZMQ_MARKET_DATA_ENDPOINT = f"tcp://127.0.0.1:{ZMQ_MARKET_DATA_PORT}"

# Firebase Admin SDK
FIREBASE_CREDENTIALS_PATH = os.getenv(
    'FIREBASE_CREDENTIALS',
    '/root/bitten-firebase-sa.json'
)

# Job Schedules (cron-style)
JOB_SCHEDULES: Dict[str, Dict[str, Any]] = {
    'outcome_tracker': {
        'trigger': 'interval',
        'minutes': 5,
        'description': 'Track signals to TP/SL completion'
    },
    'stats_aggregator': {
        'trigger': 'interval',
        'minutes': 15,
        'description': 'Calculate user statistics'
    },
    'firestore_mirror': {
        'trigger': 'interval',
        'hours': 1,
        'description': 'Mirror PostgreSQL to Firestore'
    },
    'reconciliation': {
        'trigger': 'cron',
        'hour': 2,
        'minute': 0,
        'description': 'Nightly drift check (2 AM UTC)'
    },
    'reports': {
        'trigger': 'cron',
        'hour': 3,
        'minute': 0,
        'description': 'Nightly performance reports (3 AM UTC)'
    }
}

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Outcome Tracking Configuration
OUTCOME_TRACKING_CONFIG = {
    'max_signal_age_hours': 24,  # Stop tracking signals older than 24h
    'tick_buffer_size': 1000,     # Keep last 1000 ticks in memory
    'batch_update_size': 50       # Update DB in batches of 50
}

# Firestore Mirror Configuration
FIRESTORE_CONFIG = {
    'batch_size': 500,           # Write in batches of 500 docs
    'collections': {
        'users': 'users',
        'signals': 'signals',
        'positions': 'positions'
    }
}

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
