"""
Health Server - HTTP endpoints for monitoring
Provides /health/liveness and /health/readiness endpoints
"""
import asyncio
import json
import logging
from typing import Dict, Optional

from aiohttp import web

from .config import HEALTH_PORT

logger = logging.getLogger(__name__)


class HealthServer:
    """HTTP server for health checks and metrics"""

    def __init__(self):
        self.app = None
        self.runner = None
        self.site = None

        # Component health status
        self.market_data_handler = None
        self.command_handler = None
        self.confirmation_handler = None

        # Start time
        self.start_time = asyncio.get_event_loop().time()

    def set_components(self, market_data, command, confirmation):
        """Set component references for health checks"""
        self.market_data_handler = market_data
        self.command_handler = command
        self.confirmation_handler = confirmation

    async def start(self):
        """Start HTTP server"""
        self.app = web.Application()

        # Add routes
        self.app.router.add_get("/health/liveness", self.liveness)
        self.app.router.add_get("/health/readiness", self.readiness)
        self.app.router.add_get("/metrics", self.metrics)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, "0.0.0.0", HEALTH_PORT)
        await self.site.start()

        logger.info(f"✅ Health server listening on port {HEALTH_PORT}")
        logger.info(f"   - Liveness:  http://localhost:{HEALTH_PORT}/health/liveness")
        logger.info(f"   - Readiness: http://localhost:{HEALTH_PORT}/health/readiness")
        logger.info(f"   - Metrics:   http://localhost:{HEALTH_PORT}/metrics")

    async def liveness(self, request):
        """
        Liveness probe - indicates if service is running

        Returns 200 if service is alive (even if components have issues)
        """
        uptime = asyncio.get_event_loop().time() - self.start_time

        response = {
            "status": "alive",
            "uptime_seconds": int(uptime),
            "service": "zmq_gateway",
            "version": "2.0.0"
        }

        return web.json_response(response, status=200)

    async def readiness(self, request):
        """
        Readiness probe - indicates if service is ready to handle traffic

        Returns 200 if all components are healthy
        Returns 503 if any component is unhealthy
        """
        uptime = asyncio.get_event_loop().time() - self.start_time
        components = {}
        all_ready = True

        # Check market data handler
        if self.market_data_handler:
            stats = self.market_data_handler.get_stats()
            components["market_data"] = {
                "status": "healthy",
                "message_count": stats["message_count"],
                "symbols_tracked": stats["symbols_tracked"]
            }
        else:
            components["market_data"] = {
                "status": "unhealthy",
                "error": "not initialized"
            }
            all_ready = False

        # Check command handler
        if self.command_handler:
            stats = self.command_handler.get_stats()
            components["command_router"] = {
                "status": "healthy",
                "connected_eas": stats["connected_eas"],
                "commands_routed": stats["commands_routed"]
            }
        else:
            components["command_router"] = {
                "status": "unhealthy",
                "error": "not initialized"
            }
            all_ready = False

        # Check confirmation handler
        if self.confirmation_handler:
            stats = self.confirmation_handler.get_stats()
            components["confirmations"] = {
                "status": "healthy",
                "confirmations_received": stats["confirmations_received"],
                "positions_opened": stats["positions_opened"]
            }
        else:
            components["confirmations"] = {
                "status": "unhealthy",
                "error": "not initialized"
            }
            all_ready = False

        response = {
            "status": "ready" if all_ready else "not_ready",
            "uptime_seconds": int(uptime),
            "components": components
        }

        status_code = 200 if all_ready else 503
        return web.json_response(response, status=status_code)

    async def metrics(self, request):
        """
        Metrics endpoint - provides operational metrics

        Returns current statistics from all components
        """
        metrics = {
            "uptime_seconds": int(asyncio.get_event_loop().time() - self.start_time)
        }

        # Gather stats from all components
        if self.market_data_handler:
            metrics["market_data"] = self.market_data_handler.get_stats()

        if self.command_handler:
            metrics["command_router"] = self.command_handler.get_stats()

        if self.confirmation_handler:
            metrics["confirmations"] = self.confirmation_handler.get_stats()

        return web.json_response(metrics, status=200)

    async def stop(self):
        """Clean shutdown"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Health server stopped")
