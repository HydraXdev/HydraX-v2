#!/usr/bin/env python3
"""
ZMQ Gateway Service - BITTEN v2.0

Consolidates 3 v1 processes into a single unified service:
- Market data bridge (port 5556 → 5560)
- Command router (port 5555 + IPC queue)
- Confirmation listener (port 5558)

Usage:
    python3 main.py

Environment Variables:
    BITTEN_DB - Database path (default: /root/HydraX-v2/bitten.db)
    LOG_LEVEL - Logging level (default: INFO)
"""
import asyncio
import logging
import signal
import sys
import os

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import zmq.asyncio

from services.zmq_gateway.command_handler import CommandHandler
from services.zmq_gateway.confirmation_handler import ConfirmationHandler
from services.zmq_gateway.config import LOG_LEVEL
from services.zmq_gateway.health_server import HealthServer
from services.zmq_gateway.market_data_handler import MarketDataHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class ZMQGateway:
    """Main ZMQ Gateway service orchestrator"""

    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.shutdown_event = asyncio.Event()

        # Component handlers
        self.market_data = MarketDataHandler(self.context)
        self.command_router = CommandHandler(self.context)
        self.confirmations = ConfirmationHandler(self.context)
        self.health_server = HealthServer()

        # Background tasks
        self.tasks = []

    async def start(self):
        """Initialize and start all components"""
        logger.info("=" * 70)
        logger.info("🚀 BITTEN ZMQ Gateway v2.0 - Starting")
        logger.info("=" * 70)

        # Initialize all handlers
        logger.info("📡 Initializing market data handler...")
        await self.market_data.start()

        logger.info("🎯 Initializing command router...")
        await self.command_router.start()

        logger.info("🎧 Initializing confirmation listener...")
        await self.confirmations.start()

        logger.info("💊 Initializing health server...")
        self.health_server.set_components(
            self.market_data,
            self.command_router,
            self.confirmations
        )
        await self.health_server.start()

        # Start background tasks
        logger.info("⚡ Starting background tasks...")
        self.tasks = [
            # Market data processing
            asyncio.create_task(self.market_data.process_messages()),

            # Command routing tasks
            asyncio.create_task(self.command_router.process_router_messages()),
            asyncio.create_task(self.command_router.process_ipc_commands()),
            asyncio.create_task(self.command_router.route_commands()),

            # Confirmation processing
            asyncio.create_task(self.confirmations.process_messages()),
        ]

        logger.info("=" * 70)
        logger.info("✅ ZMQ Gateway v2.0 - ALL SYSTEMS OPERATIONAL")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📊 Port Bindings:")
        logger.info("   - 5556 (PULL)   : Market data from EA")
        logger.info("   - 5560 (PUB)    : Market data to subscribers")
        logger.info("   - 5555 (ROUTER) : Fire commands to/from EA")
        logger.info("   - 5558 (PULL)   : Trade confirmations from EA")
        logger.info("   - IPC Queue     : Commands from webapp")
        logger.info("   - 9091 (HTTP)   : Health monitoring")
        logger.info("")
        logger.info("🏥 Health Endpoints:")
        logger.info("   - Liveness:  http://localhost:9091/health/liveness")
        logger.info("   - Readiness: http://localhost:9091/health/readiness")
        logger.info("   - Metrics:   http://localhost:9091/metrics")
        logger.info("")
        logger.info("Press Ctrl+C to shutdown")
        logger.info("=" * 70)

    async def stop(self):
        """Clean shutdown of all components"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("🛑 Shutting down ZMQ Gateway...")
        logger.info("=" * 70)

        # Cancel all background tasks
        logger.info("⏹️  Cancelling background tasks...")
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Stop all handlers
        logger.info("📡 Stopping market data handler...")
        await self.market_data.stop()

        logger.info("🎯 Stopping command router...")
        await self.command_router.stop()

        logger.info("🎧 Stopping confirmation listener...")
        await self.confirmations.stop()

        logger.info("💊 Stopping health server...")
        await self.health_server.stop()

        # Terminate ZMQ context
        logger.info("🔌 Terminating ZMQ context...")
        self.context.term()

        logger.info("=" * 70)
        logger.info("✅ ZMQ Gateway shutdown complete")
        logger.info("=" * 70)

    async def run(self):
        """Main run loop with signal handling"""
        # Setup signal handlers
        loop = asyncio.get_event_loop()

        def signal_handler(sig):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            self.shutdown_event.set()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

        # Start service
        await self.start()

        # Wait for shutdown signal
        await self.shutdown_event.wait()

        # Clean shutdown
        await self.stop()


async def main():
    """Entry point"""
    gateway = ZMQGateway()
    try:
        await gateway.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
