#!/usr/bin/env python3
"""
BITTEN Firebase Projector Service Runner

Starts the Firebase projector to mirror Postgres trading truth to Firestore.

Usage:
    python run_firebase_projector.py

Environment:
    GOOGLE_APPLICATION_CREDENTIALS - Path to Firebase service account JSON
    REDIS_URL - Redis connection string (optional, for pub/sub)

Author: BITTEN System
Date: 2025-10-08
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from firebase_admin import credentials, firestore, initialize_app
except ImportError:
    print("ERROR: firebase-admin not installed")
    print("Install with: pip install firebase-admin")
    sys.exit(1)

try:
    import redis
except ImportError:
    redis = None
    print("WARNING: redis not installed, pub/sub will not work")

from src.bitten_core.firebase_projector import FirebaseProjector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/firebase_projector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global shutdown flag
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global shutdown_flag
    logger.info(f"[MAIN] Received signal {signum}, shutting down...")
    shutdown_flag = True


async def main():
    """Main entry point"""
    logger.info("[MAIN] Starting Firebase Projector Service")

    # 1. Initialize Firebase
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not cred_path:
        logger.error("[MAIN] GOOGLE_APPLICATION_CREDENTIALS not set")
        return 1

    if not os.path.exists(cred_path):
        logger.error(f"[MAIN] Credentials file not found: {cred_path}")
        return 1

    try:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
        db = firestore.client()
        logger.info("[MAIN] Firebase initialized")
    except Exception as e:
        logger.error(f"[MAIN] Failed to initialize Firebase: {e}")
        return 1

    # 2. Initialize Redis (optional)
    redis_client = None
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    if redis:
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info(f"[MAIN] Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(f"[MAIN] Redis not available: {e}")
            redis_client = None

    # 3. Create projector
    projector = FirebaseProjector(db, redis_client=redis_client)

    # 4. Subscribe to events
    if redis_client:
        logger.info("[MAIN] Subscribing to Redis channels...")

        # Subscribe to domain event channels
        channels = [
            'bitten:signals',
            'bitten:exec',
            'bitten:trades',
            'bitten:presence',
        ]

        # Run subscription in background
        subscription_task = asyncio.create_task(
            projector.subscribe_redis(channels)
        )

        # Wait for shutdown signal
        while not shutdown_flag:
            await asyncio.sleep(1)

        # Cancel subscription
        subscription_task.cancel()

    else:
        logger.warning("[MAIN] Redis not available, running in direct-call mode")
        logger.info("[MAIN] Use projector.route_event(event) to project events manually")

        # In direct-call mode, just keep running
        while not shutdown_flag:
            await asyncio.sleep(1)

    logger.info("[MAIN] Projector service stopped")
    return 0


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run async main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
