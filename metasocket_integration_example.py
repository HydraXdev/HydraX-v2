#!/usr/bin/env python3
"""
MetaSocket → Elite Guard Integration Example
Shows how to wire MetaSocket data streams to existing Elite Guard system
"""

import asyncio
import logging
import sys
from datetime import datetime

# Import MetaSocket components
from src.metasocket import MetaSocketBootstrap

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EliteGuardMetaSocketIntegration:
    """Integration layer between MetaSocket and Elite Guard"""

    def __init__(self):
        self.bootstrap = MetaSocketBootstrap()

        # Statistics
        self.ticks_received = 0
        self.positions_tracked = 0
        self.account_updates = 0
        self.snapshots_created = 0

        # Start time for uptime calculation
        self.start_time = datetime.now()

    async def handle_tick_data(self, tick_data):
        """Handle incoming tick data - wire to Elite Guard"""
        self.ticks_received += 1

        # This would replace the existing tick processing in Elite Guard
        symbol = tick_data.get("symbol")
        bid = tick_data.get("bid")
        ask = tick_data.get("ask")
        mid = tick_data.get("mid")

        logger.debug(f"📊 TICK: {symbol} = {mid:.5f} (bid={bid:.5f}, ask={ask:.5f})")

        # Wire to Elite Guard tick processing here:
        # elite_guard.process_market_tick(symbol, bid, ask, tick_data['ts_epoch_ms'])

    async def handle_ohlc_data(self, ohlc_data):
        """Handle OHLC bar completion - wire to Elite Guard"""
        symbol = ohlc_data.get("symbol")
        timeframe = ohlc_data.get("timeframe")
        close = ohlc_data.get("close")

        logger.info(f"📈 OHLC: {symbol} {timeframe} close={close:.5f}")

        # Wire to Elite Guard OHLC processing here:
        # elite_guard.process_completed_bar(symbol, ohlc_data)

    async def handle_position_event(self, position_data):
        """Handle position events - wire to existing tracking"""
        self.positions_tracked += 1

        ticket = position_data.get("ticket")
        symbol = position_data.get("symbol")
        state = position_data.get("state")
        side = position_data.get("side")

        logger.info(f"🔥 POSITION: {symbol} {side} {state} (ticket={ticket})")

        # Wire to existing position tracking here:
        # position_tracker.update_position(position_data)

    async def handle_account_update(self, account_data):
        """Handle account summary updates"""
        self.account_updates += 1

        balance = account_data.get("balance")
        equity = account_data.get("equity")
        free_margin = account_data.get("free_margin")

        logger.info(f"💰 ACCOUNT: Balance=${balance:.2f}, Equity=${equity:.2f}, Free=${free_margin:.2f}")

        # Wire to existing account tracking here:
        # account_monitor.update_account_data(account_data)

    async def handle_signal_snapshot(self, snapshot_data):
        """Handle signal snapshots - for fire confirmations"""
        self.snapshots_created += 1

        symbol = snapshot_data.get("symbol")
        bars_count = len(snapshot_data.get("ohlc", []))
        trigger = snapshot_data.get("metadata", {}).get("trigger", "unknown")

        logger.info(f"📸 SNAPSHOT: {symbol} ({bars_count} bars) trigger={trigger}")

        # Wire to existing snapshot handling here:
        # signal_processor.process_snapshot(snapshot_data)

    def print_stats(self):
        """Print integration statistics"""
        uptime = datetime.now() - self.start_time

        print("\n" + "=" * 60)
        print("📊 METASOCKET → ELITE GUARD INTEGRATION STATS")
        print("=" * 60)
        print(f"⏱️  Uptime: {uptime}")
        print(f"📈 Ticks Received: {self.ticks_received:,}")
        print(f"🔥 Positions Tracked: {self.positions_tracked}")
        print(f"💰 Account Updates: {self.account_updates}")
        print(f"📸 Snapshots Created: {self.snapshots_created}")
        print(f"🏥 Health: http://localhost:8890/healthz")
        print("=" * 60)

    async def start_integration(self):
        """Start the MetaSocket integration"""
        logger.info("🚀 Starting MetaSocket → Elite Guard Integration")

        # Set up callbacks to wire MetaSocket to Elite Guard
        self.bootstrap.set_callbacks(
            tick_callback=self.handle_tick_data,
            ohlc_callback=self.handle_ohlc_data,
            position_callback=self.handle_position_event,
            account_callback=self.handle_account_update,
            snapshot_callback=self.handle_signal_snapshot,
        )

        # Start the MetaSocket system
        await self.bootstrap.start()

    async def create_fire_snapshot(self, fire_data):
        """Create snapshot when fire is confirmed"""
        logger.info(f"🔥 Creating snapshot for fire: {fire_data.get('fire_id')}")

        snapshot = await self.bootstrap.on_fire_confirmation(fire_data)

        if snapshot:
            logger.info(f"✅ Fire snapshot created: {snapshot['symbol']} " f"({len(snapshot['ohlc'])} bars)")
            return snapshot
        else:
            logger.warning("⚠️ Failed to create fire snapshot")
            return None


# Example usage showing integration points
async def main():
    """Main function demonstrating the integration"""

    print("🎯 MetaSocket → BITTEN Integration Example")
    print("=" * 50)

    integration = EliteGuardMetaSocketIntegration()

    # In the real integration, you would:
    # 1. Replace existing Elite Guard tick sources with MetaSocket
    # 2. Wire callbacks to existing Elite Guard methods
    # 3. Use MetaSocket health checks for monitoring

    try:
        # Start the integration
        await integration.start_integration()

    except KeyboardInterrupt:
        logger.info("⏹️  Integration stopped by user")
        integration.print_stats()

    except Exception as e:
        logger.error(f"❌ Integration error: {e}")

    finally:
        logger.info("👋 Integration shutdown complete")


# Integration steps for Elite Guard
def integration_checklist():
    """Print integration checklist for Elite Guard"""

    print("\n🔧 ELITE GUARD INTEGRATION CHECKLIST:")
    print("-" * 40)
    print("1. ✅ XAGUSD added to trading pairs")
    print("2. 🔄 Replace tick sources:")
    print("   - Comment out zmq_telemetry_bridge")
    print("   - Wire MetaSocket tick_callback to process_tick()")
    print("3. 🔄 Replace OHLC sources:")
    print("   - Wire MetaSocket ohlc_callback to candle building")
    print("4. 🔄 Add position tracking:")
    print("   - Wire MetaSocket position_callback to tracking system")
    print("5. 🔄 Add account monitoring:")
    print("   - Wire MetaSocket account_callback to balance updates")
    print("6. 🔄 Add fire snapshots:")
    print("   - Call bootstrap.on_fire_confirmation() on fire events")
    print("7. 🔄 Add health monitoring:")
    print("   - Monitor http://localhost:8890/healthz")
    print("8. 🧪 Test integration:")
    print("   - Run python metasocket_integration_example.py")
    print("   - Verify all data streams working")
    print("-" * 40)


if __name__ == "__main__":
    # Print integration checklist
    integration_checklist()

    # Run integration example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
