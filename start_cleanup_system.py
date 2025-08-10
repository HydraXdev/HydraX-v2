#!/usr/bin/env python3
"""
🧹 START AUTO-CLEANUP SYSTEM
Runs the automatic cleanup system for Telegram messages and mission files
"""

import sys
import logging
import time
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

from src.bitten_core.auto_cleanup_system import cleanup_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/cleanup_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Start the auto-cleanup system
    """
    logger.info("=" * 60)
    logger.info("🧹 BITTEN AUTO-CLEANUP SYSTEM")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Configuration:")
    logger.info("  • Telegram messages: Auto-delete after 8 hours")
    logger.info("  • Mission files: Auto-delete after 8 hours")
    logger.info("  • Signal files: Auto-delete after 24 hours")
    logger.info("  • Check interval: Every 5 minutes")
    logger.info("")
    logger.info("Starting cleanup system...")
    
    # Start the cleanup system
    cleanup_system.start()
    
    logger.info("✅ Auto-cleanup system is running")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            # Log stats every hour
            if int(time.time()) % 3600 < 60:
                cleanup_system.log_cleanup_stats()
                
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping cleanup system...")
        cleanup_system.stop()
        logger.info("Cleanup system stopped")

if __name__ == "__main__":
    main()