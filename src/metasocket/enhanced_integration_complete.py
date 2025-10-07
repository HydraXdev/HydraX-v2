#!/usr/bin/env python3
"""
enhanced_integration_complete.py - Complete MetaSocket integration
Combines enhanced subscriptions and backfill systems with TypeScript-mirrored logic
"""

import asyncio
import logging
import time
from typing import Dict, Optional

from symbols import SYMBOLS
from subscriptions_v2 import EnhancedSubscriptionManager
from backfill_v2 import EnhancedBackfillManager, Bar

logger = logging.getLogger(__name__)

class CompleteMetaSocketIntegration:
    """Complete MetaSocket integration with TypeScript-mirrored components"""

    def __init__(self, host: str = "185.244.67.11", ports: tuple = (8777, 8778)):
        self.host = host
        self.subscription_port = ports[0]
        self.backfill_port = ports[1]

        # Enhanced components
        self.subscription_manager = EnhancedSubscriptionManager(
            f"ws://{host}:{self.subscription_port}"
        )
        self.backfill_manager = EnhancedBackfillManager(
            f"ws://{host}:{self.backfill_port}"
        )

        # Integration statistics
        self.stats = {
            "ticks_processed": 0,
            "bars_completed": 0,
            "snapshots_created": 0,
            "start_time": None
        }

        # External callbacks
        self.external_tick_callback = None
        self.external_ohlc_callback = None
        self.external_snapshot_callback = None

    def set_callbacks(self, **callbacks):
        """Set external callbacks for Elite Guard integration"""
        self.external_tick_callback = callbacks.get('tick_callback')
        self.external_ohlc_callback = callbacks.get('ohlc_callback')
        self.external_snapshot_callback = callbacks.get('snapshot_callback')

    async def handle_tick(self, tick_data: dict):
        """Handle incoming tick data from subscriptions"""
        self.stats["ticks_processed"] += 1

        # Process through backfill system for OHLC building
        self.backfill_manager.process_tick(tick_data)

        # Send to external callback if set
        if self.external_tick_callback:
            await self.external_tick_callback(tick_data)

        logger.debug(f"📊 TICK: {tick_data['symbol']} = {tick_data.get('mid', 'N/A'):.5f}")

    async def handle_ohlc(self, ohlc_data: dict):
        """Handle OHLC bar completion"""
        self.stats["bars_completed"] += 1

        # Convert to our Bar format and update store
        symbol = ohlc_data.get("symbol")
        if symbol:
            bar = Bar(
                ts_open_ms=ohlc_data.get("ts_epoch_ms", int(time.time() * 1000)),
                o=ohlc_data.get("open", 0),
                h=ohlc_data.get("high", 0),
                l=ohlc_data.get("low", 0),
                c=ohlc_data.get("close", 0),
                v=ohlc_data.get("volume")
            )

            # Add to store (this would normally happen through tick processing)
            # self.backfill_manager.store.put(symbol, [bar])

        # Send to external callback if set
        if self.external_ohlc_callback:
            await self.external_ohlc_callback(ohlc_data)

        logger.info(f"📈 OHLC: {symbol} {ohlc_data.get('timeframe', 'M1')} = {ohlc_data.get('close', 'N/A'):.5f}")

    async def create_snapshot(self, symbol: str, trigger: str = "on_demand") -> Optional[dict]:
        """Create signal snapshot using backfill data"""
        snapshot = self.backfill_manager.create_snapshot(symbol)

        if snapshot:
            snapshot["trigger"] = trigger
            self.stats["snapshots_created"] += 1

            # Send to external callback if set
            if self.external_snapshot_callback:
                await self.external_snapshot_callback(snapshot)

            logger.info(f"📸 SNAPSHOT: {symbol} - {len(snapshot.get('bars', []))} bars (trigger: {trigger})")

        return snapshot

    async def start_backfill_process(self):
        """Start the backfill process for historical data"""
        logger.info("📊 Starting backfill process...")

        try:
            result = await self.backfill_manager.perform_backfill()
            logger.info(f"✅ Backfill completed: {result['success']}/{len(SYMBOLS)} symbols successful")

            if result['failed']:
                logger.warning(f"⚠️ Failed symbols: {result['failed']}")

        except Exception as e:
            logger.error(f"❌ Backfill process failed: {e}")

    async def start(self):
        """Start the complete integration"""
        self.stats["start_time"] = time.time()

        logger.info("🚀 Starting complete MetaSocket integration")
        logger.info(f"📡 Symbols: {len(SYMBOLS)}")
        logger.info(f"🔗 Subscription endpoint: ws://{self.host}:{self.subscription_port}")
        logger.info(f"📊 Backfill endpoint: ws://{self.host}:{self.backfill_port}")

        # Set up subscription callbacks
        self.subscription_manager.set_callbacks(
            tick_cb=self.handle_tick,
            ohlc_cb=self.handle_ohlc
        )

        # Start backfill first
        await self.start_backfill_process()

        # Start subscription system
        logger.info("📡 Starting subscription system...")

        # Start subscription manager (this will run indefinitely)
        await self.subscription_manager.start()

    async def stop(self):
        """Stop the complete integration"""
        logger.info("🛑 Stopping complete MetaSocket integration")

        await self.subscription_manager.stop()

        uptime = time.time() - (self.stats["start_time"] or time.time())
        logger.info(f"📊 Final stats - Uptime: {uptime:.1f}s, Ticks: {self.stats['ticks_processed']:,}, "
                   f"Bars: {self.stats['bars_completed']}, Snapshots: {self.stats['snapshots_created']}")

    def get_health_status(self) -> dict:
        """Get comprehensive health status"""
        subscription_health = self.subscription_manager.get_health_status()
        backfill_health = self.backfill_manager.get_health_stats()

        current_time = time.time()
        uptime = current_time - (self.stats["start_time"] or current_time)

        return {
            "overall_status": "healthy" if subscription_health["connected"] and backfill_health["backfill_completed"] else "degraded",
            "uptime_seconds": uptime,
            "symbols_configured": len(SYMBOLS),
            "subscriptions": subscription_health,
            "backfill": backfill_health,
            "stats": self.stats
        }

    def print_status_banner(self):
        """Print current status banner"""
        health = self.get_health_status()

        print("\n" + "="*70)
        print("📊 COMPLETE METASOCKET INTEGRATION STATUS")
        print("="*70)
        print(f"🔗 Status: {health['overall_status'].upper()}")
        print(f"⏱️  Uptime: {health['uptime_seconds']:.1f}s")
        print(f"📈 Symbols: {health['symbols_configured']}")
        print(f"📡 Subscription Connected: {health['subscriptions']['connected']}")
        print(f"📊 Backfill Completed: {health['backfill']['backfill_completed']}")
        print(f"🎯 Ticks Processed: {health['stats']['ticks_processed']:,}")
        print(f"📈 Bars Completed: {health['stats']['bars_completed']}")
        print(f"📸 Snapshots Created: {health['stats']['snapshots_created']}")

        # Show stale symbols if any
        stale_symbols = health['subscriptions']['metrics']['stale_symbols']
        if stale_symbols:
            print(f"⚠️  Stale Symbols: {len(stale_symbols)} ({stale_symbols[:3]}{'...' if len(stale_symbols) > 3 else ''})")

        print("="*70)

# Example integration with Elite Guard simulation
async def elite_guard_integration_example():
    """Example showing integration with Elite Guard-style callbacks"""

    print("🎯 Complete MetaSocket → Elite Guard Integration Example")
    print("="*60)

    # Elite Guard simulation callbacks
    async def elite_guard_tick_handler(tick):
        """Simulated Elite Guard tick processing"""
        symbol = tick.get("symbol")
        mid = tick.get("mid")

        # This would be: elite_guard.process_market_tick(symbol, tick)
        print(f"EG_TICK: {symbol} = {mid:.5f} (processed by Elite Guard)")

    async def elite_guard_ohlc_handler(ohlc):
        """Simulated Elite Guard OHLC processing"""
        symbol = ohlc.get("symbol")
        close = ohlc.get("close")

        # This would be: elite_guard.process_completed_bar(symbol, ohlc)
        print(f"EG_OHLC: {symbol} M1 close = {close:.5f} (processed by Elite Guard)")

    async def elite_guard_snapshot_handler(snapshot):
        """Simulated Elite Guard snapshot processing"""
        symbol = snapshot.get("symbol")
        bars_count = len(snapshot.get("bars", []))
        trigger = snapshot.get("trigger")

        # This would be: elite_guard.process_signal_snapshot(symbol, snapshot)
        print(f"EG_SNAPSHOT: {symbol} ({bars_count} bars) trigger={trigger} (processed by Elite Guard)")

    # Create complete integration
    integration = CompleteMetaSocketIntegration()

    # Set Elite Guard callbacks
    integration.set_callbacks(
        tick_callback=elite_guard_tick_handler,
        ohlc_callback=elite_guard_ohlc_handler,
        snapshot_callback=elite_guard_snapshot_handler
    )

    print(f"✅ Integration configured with {len(SYMBOLS)} symbols")
    print("🔗 Elite Guard callbacks wired")

    # In a real scenario, you would call:
    # await integration.start()

    # For demonstration, let's simulate some operations
    print("\n🧪 Simulating integration operations...")

    # Simulate tick processing
    test_tick = {
        "symbol": "EURUSD",
        "bid": 1.10500,
        "ask": 1.10502,
        "mid": 1.10501,
        "ts_epoch_ms": int(time.time() * 1000),
        "src": "metasocket"
    }

    await integration.handle_tick(test_tick)

    # Simulate OHLC bar
    test_ohlc = {
        "symbol": "EURUSD",
        "timeframe": "M1",
        "open": 1.10500,
        "high": 1.10520,
        "low": 1.10480,
        "close": 1.10510,
        "volume": 1000,
        "ts_epoch_ms": int(time.time() * 1000),
        "src": "metasocket"
    }

    await integration.handle_ohlc(test_ohlc)

    # Create snapshot
    # First add some test data to backfill
    from backfill_v2 import Bar
    test_bars = [
        Bar(int(time.time() * 1000) - i * 60000, 1.10500 + i * 0.0001,
            1.10520 + i * 0.0001, 1.10480 + i * 0.0001, 1.10510 + i * 0.0001)
        for i in range(50)
    ]
    integration.backfill_manager.store.put("EURUSD", test_bars)
    integration.backfill_manager.backfill_completed = True

    await integration.create_snapshot("EURUSD", "fire_confirmation")

    # Show status
    integration.print_status_banner()

    print("\n🎉 Integration example completed successfully!")
    print("🔗 Ready for production deployment with Elite Guard")

# Main execution
async def main():
    """Main function for testing complete integration"""

    # Run Elite Guard integration example
    await elite_guard_integration_example()

    print(f"\n📋 Production deployment steps:")
    print(f"1. Replace existing MetaSocket components with enhanced versions")
    print(f"2. Wire integration.set_callbacks() to Elite Guard methods")
    print(f"3. Start with: await integration.start()")
    print(f"4. Monitor health with: integration.get_health_status()")
    print(f"5. Create snapshots with: await integration.create_snapshot(symbol)")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🚀 Complete Enhanced MetaSocket Integration")
    print("=" * 50)
    print("Features: TypeScript-mirrored logic, enhanced resilience, comprehensive monitoring")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Integration test stopped by user")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise