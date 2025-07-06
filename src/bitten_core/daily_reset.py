#!/usr/bin/env python3
"""
Daily Reset Script for BITTEN Risk Controller

This script should be run at 00:00 UTC daily via cron job.
It resets daily counters for all users.

Cron example:
0 0 * * * /usr/bin/python3 /root/HydraX-v2/src/bitten_core/daily_reset.py
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitten_core.risk_controller import get_risk_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/daily_reset.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run daily reset"""
    try:
        logger.info("Starting daily reset at %s", datetime.now(timezone.utc))
        
        # Get risk controller instance
        risk_controller = get_risk_controller()
        
        # Reset all daily counters
        risk_controller.reset_all_daily_counters()
        
        logger.info("Daily reset completed successfully")
        
    except Exception as e:
        logger.error(f"Daily reset failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()