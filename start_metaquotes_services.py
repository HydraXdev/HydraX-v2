#!/usr/bin/env python3
"""
Start MetaQuotes Demo Account Services

Initializes and starts all MetaQuotes-related services including:
- Demo account pool manager
- Health monitoring
- Credential delivery processing
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from src.bitten_core.metaquotes import (
    get_demo_account_service,
    get_pool_manager,
    PoolConfig
)
from src.bitten_core.database.connection import test_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/metaquotes_services.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MetaQuotesServiceManager:
    """Manages all MetaQuotes-related services"""
    
    def __init__(self):
        self.pool_manager = None
        self.demo_service = None
        self.is_running = False
        self.tasks = []
        
    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing MetaQuotes services...")
        
        # Test database connection
        if not await test_db_connection():
            logger.error("Database connection failed!")
            raise Exception("Cannot start without database connection")
            
        # Initialize demo account service
        self.demo_service = await get_demo_account_service()
        logger.info("Demo account service initialized")
        
        # Initialize pool manager with custom config
        pool_config = PoolConfig(
            min_available_accounts=25,  # Start with smaller pool
            max_pool_size=100,
            target_buffer=40,
            provision_batch_size=5,
            health_check_interval_minutes=15,
            cleanup_interval_hours=4
        )
        
        self.pool_manager = await get_pool_manager()
        self.pool_manager.config = pool_config
        logger.info("Account pool manager initialized")
        
    async def start(self):
        """Start all services"""
        if self.is_running:
            logger.warning("Services already running")
            return
            
        self.is_running = True
        logger.info("Starting MetaQuotes services...")
        
        # Start pool manager
        await self.pool_manager.start()
        
        # Start monitoring task
        self.tasks.append(
            asyncio.create_task(self._monitor_services())
        )
        
        # Start credential delivery processor
        self.tasks.append(
            asyncio.create_task(self._process_credential_deliveries())
        )
        
        logger.info("All MetaQuotes services started successfully")
        
    async def stop(self):
        """Stop all services gracefully"""
        logger.info("Stopping MetaQuotes services...")
        self.is_running = False
        
        # Stop pool manager
        if self.pool_manager:
            await self.pool_manager.stop()
            
        # Cancel monitoring tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("All MetaQuotes services stopped")
        
    async def _monitor_services(self):
        """Monitor service health and statistics"""
        while self.is_running:
            try:
                # Get pool statistics
                pool_stats = await self.pool_manager.get_pool_statistics()
                
                logger.info(f"Pool Stats - Available: {pool_stats['healthy_available']}, "
                          f"Assigned: {pool_stats['assigned']}, "
                          f"Total: {pool_stats['total']}, "
                          f"Health: {pool_stats['pool_health']}")
                
                # Check if pool needs attention
                if pool_stats['pool_health'] != 'healthy':
                    logger.warning(f"Pool health degraded: {pool_stats}")
                    # Could trigger alerts here
                    
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
                
    async def _process_credential_deliveries(self):
        """Process pending credential deliveries"""
        while self.is_running:
            try:
                # TODO: Process credential delivery queue
                # This would integrate with Telegram bot, email service, etc.
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Delivery processing error: {e}")
                await asyncio.sleep(30)
                
    async def get_status(self) -> dict:
        """Get current service status"""
        try:
            pool_stats = await self.pool_manager.get_pool_statistics()
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'demo_service': 'active' if self.demo_service else 'inactive',
                    'pool_manager': 'active' if self.pool_manager else 'inactive'
                },
                'pool': pool_stats
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global service manager instance
service_manager = MetaQuotesServiceManager()


async def main():
    """Main entry point"""
    logger.info("MetaQuotes Service Manager starting...")
    
    try:
        # Initialize services
        await service_manager.initialize()
        
        # Start services
        await service_manager.start()
        
        # Log initial status
        status = await service_manager.get_status()
        logger.info(f"Initial status: {status}")
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            asyncio.create_task(shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep running until shutdown
        while service_manager.is_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await shutdown()
        sys.exit(1)


async def shutdown():
    """Graceful shutdown"""
    logger.info("Shutting down MetaQuotes services...")
    await service_manager.stop()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Run the service
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        sys.exit(1)