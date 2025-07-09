#!/usr/bin/env python3
"""
Press Pass Scheduler Service
Runs the nightly XP reset system for Press Pass users
"""

import os
import sys
import asyncio
import logging
import signal
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitten_core.xp_integration import XPIntegrationManager
from bitten_core.telegram_messenger import TelegramMessenger
from bitten_core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/press_pass_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class PressPassSchedulerService:
    """Service to run Press Pass reset scheduler"""
    
    def __init__(self):
        self.running = False
        self.xp_manager = None
        self.loop = None
        
    async def initialize(self):
        """Initialize the service"""
        try:
            # Load config
            config_manager = ConfigManager()
            config = config_manager.config
            
            # Initialize Telegram messenger
            telegram = TelegramMessenger(
                bot_token=config['telegram']['bot_token'],
                admin_chat_id=config['telegram']['admin_chat_id']
            )
            
            # Initialize XP manager with telegram
            self.xp_manager = XPIntegrationManager(
                telegram_messenger=telegram
            )
            
            logger.info("Press Pass scheduler service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize service: {e}")
            raise
    
    async def start(self):
        """Start the scheduler service"""
        self.running = True
        
        # Start the scheduler
        self.xp_manager.start_press_pass_scheduler()
        
        logger.info("Press Pass scheduler service started")
        
        # Keep the service running
        while self.running:
            await asyncio.sleep(60)  # Check every minute
            
            # Log heartbeat every hour
            if datetime.now().minute == 0:
                logger.info(f"Press Pass scheduler heartbeat at {datetime.now(timezone.utc)}")
    
    def stop(self):
        """Stop the scheduler service"""
        logger.info("Stopping Press Pass scheduler service...")
        
        self.running = False
        
        if self.xp_manager:
            self.xp_manager.stop_press_pass_scheduler()
        
        logger.info("Press Pass scheduler service stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()
        if self.loop:
            self.loop.stop()

async def main():
    """Main entry point"""
    service = PressPassSchedulerService()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, service.handle_signal)
    signal.signal(signal.SIGTERM, service.handle_signal)
    
    try:
        # Initialize service
        await service.initialize()
        
        # Store loop reference
        service.loop = asyncio.get_event_loop()
        
        # Start service
        await service.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
    finally:
        service.stop()

if __name__ == "__main__":
    asyncio.run(main())