#!/usr/bin/env python3
"""
MetaSocket Bootstrap System
Wires all components together and manages the complete data pipeline
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from typing import Optional

from .backfill import MetaSocketBackfill
from .normalizers.positions import PositionEventNormalizer
from .pollers.account import AccountSummaryPoller
from .signal_snapshots import SignalSnapshotProducer

# Import all MetaSocket components
from .subscriptions import MetaSocketSubscriptions
from .web.healthz import MetaSocketHealthCheck

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MetaSocketBootstrap:
    """Bootstrap system for MetaSocket integration"""

    def __init__(self, host: str = "185.244.67.11", ports: tuple = (8777, 8778)):
        self.host = host
        self.subscription_port = ports[0]
        self.polling_port = ports[1]

        # Component instances
        self.subscriptions: Optional[MetaSocketSubscriptions] = None
        self.backfill: Optional[MetaSocketBackfill] = None
        self.position_normalizer: Optional[PositionEventNormalizer] = None
        self.account_poller: Optional[AccountSummaryPoller] = None
        self.snapshot_producer: Optional[SignalSnapshotProducer] = None
        self.health_check: Optional[MetaSocketHealthCheck] = None

        # External callbacks (set by BITTEN system)
        self.tick_callback = None
        self.ohlc_callback = None
        self.position_callback = None
        self.account_callback = None
        self.snapshot_callback = None

        # Shutdown flag
        self.shutdown_requested = False
        self.health_server_thread = None

        # Statistics
        self.start_time = None
        self.events_processed = 0

    def set_callbacks(self, **callbacks):
        """Set external callback functions for BITTEN integration"""
        self.tick_callback = callbacks.get("tick_callback")
        self.ohlc_callback = callbacks.get("ohlc_callback")
        self.position_callback = callbacks.get("position_callback")
        self.account_callback = callbacks.get("account_callback")
        self.snapshot_callback = callbacks.get("snapshot_callback")

        logger.info(f"📡 External callbacks configured: {list(callbacks.keys())}")

    def initialize_components(self):
        """Initialize all MetaSocket components"""
        logger.info("🔧 Initializing MetaSocket components...")

        # Initialize subscription system
        self.subscriptions = MetaSocketSubscriptions(self.host, self.subscription_port)

        # Initialize backfill system
        self.backfill = MetaSocketBackfill(self.host, self.polling_port)

        # Initialize position normalizer
        self.position_normalizer = PositionEventNormalizer()

        # Initialize account poller
        self.account_poller = AccountSummaryPoller(self.host, self.polling_port)

        # Initialize snapshot producer
        self.snapshot_producer = SignalSnapshotProducer(self.backfill, self.subscriptions, self.account_poller)

        # Initialize health check system
        self.health_check = MetaSocketHealthCheck()
        self.health_check.set_components(
            subscriptions=self.subscriptions,
            backfill=self.backfill,
            position_normalizer=self.position_normalizer,
            account_poller=self.account_poller,
            snapshot_producer=self.snapshot_producer,
        )

        logger.info("✅ All components initialized")

    def wire_callbacks(self):
        """Wire internal callbacks between components"""
        logger.info("🔗 Wiring component callbacks...")

        # Wire tick data flow: subscriptions -> backfill -> external
        async def tick_handler(tick_data):
            try:
                # Update backfill with tick
                self.backfill.process_tick(tick_data)

                # Send to external callback
                if self.tick_callback:
                    await self.tick_callback(tick_data)

                self.events_processed += 1

            except Exception as e:
                logger.error(f"❌ Tick handler error: {e}")

        # Wire OHLC data flow: backfill -> external
        async def ohlc_handler(ohlc_data):
            try:
                # Send to external callback
                if self.ohlc_callback:
                    await self.ohlc_callback(ohlc_data)

                self.events_processed += 1

            except Exception as e:
                logger.error(f"❌ OHLC handler error: {e}")

        # Wire position events: subscriptions -> normalizer -> external
        async def position_handler(position_data):
            try:
                # Normalize position event
                normalized_event = await self.position_normalizer.process_position_event(position_data)

                # Send to external callback
                if normalized_event and self.position_callback:
                    await self.position_callback(normalized_event)

                self.events_processed += 1

            except Exception as e:
                logger.error(f"❌ Position handler error: {e}")

        # Wire account updates: poller -> external
        async def account_handler(account_data):
            try:
                # Send to external callback
                if self.account_callback:
                    await self.account_callback(account_data)

                self.events_processed += 1

            except Exception as e:
                logger.error(f"❌ Account handler error: {e}")

        # Wire snapshot updates: producer -> external
        async def snapshot_handler(snapshot_data):
            try:
                # Send to external callback
                if self.snapshot_callback:
                    await self.snapshot_callback(snapshot_data)

                self.events_processed += 1

            except Exception as e:
                logger.error(f"❌ Snapshot handler error: {e}")

        # Set callbacks on components
        self.subscriptions.set_callbacks(tick_cb=tick_handler, ohlc_cb=ohlc_handler, position_cb=position_handler)

        self.backfill.set_ohlc_callback(ohlc_handler)
        self.account_poller.set_account_callback(account_handler)
        self.snapshot_producer.set_snapshot_callback(snapshot_handler)

        logger.info("✅ All callbacks wired")

    def start_health_server(self):
        """Start health check server in separate thread"""

        def run_health_server():
            try:
                self.health_check.run(host="0.0.0.0", port=8890, debug=False)
            except Exception as e:
                logger.error(f"❌ Health server error: {e}")

        self.health_server_thread = threading.Thread(target=run_health_server, daemon=True)
        self.health_server_thread.start()
        logger.info("🏥 Health check server started on port 8890")

    async def start_backfill_process(self):
        """Start the backfill process"""
        logger.info("📊 Starting historical data backfill...")
        await self.backfill.start_backfill()
        logger.info("✅ Backfill completed")

    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""

        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def main_loop(self):
        """Main event loop coordinating all components"""
        logger.info("🚀 Starting MetaSocket main loop...")

        # Start all component tasks
        tasks = [
            # Subscription system (handles reconnections internally)
            self.subscriptions.start(),
            # Account polling
            self.account_poller.start(),
            # Position reconciliation
            self.position_normalizer.start(),
            # Snapshot service
            self.snapshot_producer.start(),
        ]

        # Start all tasks concurrently
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"❌ Main loop error: {e}")

    def print_startup_banner(self):
        """Print startup banner with system info"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                        METASOCKET → BITTEN                          ║
║                      Unified Data Pipeline                          ║
╠══════════════════════════════════════════════════════════════════════╣
║ EA Host: {self.host:<20} Ports: {self.subscription_port}/{self.polling_port:<15} ║
║ Symbols: 22 active (including XAGUSD)                               ║
║ Health Check: http://localhost:8890/healthz                         ║
║ Components: Subscriptions, Backfill, Positions, Account, Snapshots  ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    async def start(self):
        """Start the complete MetaSocket system"""
        self.start_time = time.time()
        self.print_startup_banner()

        # Setup signal handlers
        self.setup_signal_handlers()

        # Initialize all components
        self.initialize_components()

        # Wire callbacks
        self.wire_callbacks()

        # Start health check server
        self.start_health_server()

        # Start backfill process
        await self.start_backfill_process()

        # Start main loop
        logger.info("🎯 MetaSocket system fully operational")

        try:
            await self.main_loop()
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("🔄 Shutting down MetaSocket system...")

        uptime = time.time() - (self.start_time or time.time())
        logger.info(f"📊 System stats - Uptime: {uptime:.1f}s, Events: {self.events_processed}")

        # Here you would clean up WebSocket connections, close files, etc.
        # The specific cleanup depends on each component's implementation

        logger.info("✅ MetaSocket system shutdown complete")

    # Convenience methods for external integration
    async def create_snapshot(self, symbol: str, trigger: str = "external_request"):
        """Create snapshot for external consumption"""
        if self.snapshot_producer:
            return await self.snapshot_producer.create_snapshot(symbol, trigger)
        return None

    async def on_fire_confirmation(self, fire_data: dict):
        """Handle fire confirmation from BITTEN system"""
        if self.snapshot_producer:
            return await self.snapshot_producer.on_fire_confirmation(fire_data)
        return None

    def get_health_status(self):
        """Get current health status"""
        if self.health_check:
            return self.health_check.collect_health_data()
        return {"status": "not_initialized"}


# Standalone execution
async def main():
    """Main function for standalone execution"""

    # Example callbacks for testing
    async def test_tick_callback(tick):
        logger.info(f"TICK: {tick['symbol']} {tick['mid']:.5f}")

    async def test_account_callback(account):
        logger.info(f"ACCOUNT: ${account['balance']:.2f} / ${account['equity']:.2f}")

    async def test_position_callback(position):
        logger.info(f"POSITION: {position['symbol']} {position['state']} " f"ticket={position['ticket']}")

    async def test_snapshot_callback(snapshot):
        logger.info(f"SNAPSHOT: {snapshot['symbol']} - {len(snapshot['ohlc'])} bars")

    # Create and configure bootstrap
    bootstrap = MetaSocketBootstrap()
    bootstrap.set_callbacks(
        tick_callback=test_tick_callback,
        account_callback=test_account_callback,
        position_callback=test_position_callback,
        snapshot_callback=test_snapshot_callback,
    )

    # Start system
    await bootstrap.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
        sys.exit(0)
