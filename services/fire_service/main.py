#!/usr/bin/env python3
"""
Fire Service Main Entry Point
Starts FastAPI server with uvicorn
"""

import logging
import sys
import os
from pathlib import Path

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.fire_service.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/root/HydraX-v2/logs/fire_service.log")
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    import uvicorn

    logger.info("=" * 70)
    logger.info("BITTEN FIRE SERVICE v2.0 - STARTING")
    logger.info("=" * 70)
    logger.info(f"Service: {config.SERVICE_NAME}")
    logger.info(f"Version: {config.VERSION}")
    logger.info(f"Host: {config.API_HOST}")
    logger.info(f"Port: {config.API_PORT}")
    logger.info(f"Workers: {config.API_WORKERS}")
    logger.info(f"IPC Queue: {config.IPC_QUEUE}")
    logger.info(f"Confirmation Port: {config.CONFIRM_LISTENER_PORT}")
    logger.info(f"Manual Risk: {config.MANUAL_RISK_PCT}%")
    logger.info(f"AUTO Risk: {config.AUTO_RISK_PCT}%")
    logger.info("=" * 70)

    # Start uvicorn server
    uvicorn.run(
        "api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        workers=1,  # Single worker for ZMQ socket management
        log_level=config.LOG_LEVEL.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
