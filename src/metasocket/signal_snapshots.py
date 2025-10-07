#!/usr/bin/env python3
"""
MetaSocket Signal Snapshot Producer
Creates comprehensive market snapshots on demand or fire confirmation
"""

import asyncio
import json
import time
import logging
from typing import Dict, Optional, Callable, List
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class SignalSnapshotProducer:
    """Produces signal snapshots with OHLC, price, and overlays"""

    def __init__(self, backfill_manager, subscription_manager, account_poller):
        self.backfill = backfill_manager
        self.subscriptions = subscription_manager
        self.account_poller = account_poller

        # Snapshot callback
        self.snapshot_callback: Optional[Callable] = None

        # Cache snapshots for performance
        self.snapshot_cache: Dict[str, dict] = {}
        self.cache_ttl = 30  # Cache TTL in seconds
        self.cache_timestamps: Dict[str, float] = {}

        # Active symbols (same as other components)
        self.active_symbols = [
            # Major Forex Pairs (6)
            "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD",
            # Cross Pairs (10)
            "EURJPY", "GBPJPY", "EURGBP", "EURAUD", "GBPCAD", "AUDJPY", "NZDJPY",
            "CHFJPY", "CADJPY", "AUDCAD",
            # Additional Pairs (2)
            "USDCNH", "AUDNZD",
            # Precious Metals (2)
            "XAUUSD", "XAGUSD"
        ]

    def set_snapshot_callback(self, callback: Callable):
        """Set callback for snapshot events"""
        self.snapshot_callback = callback

    def calculate_technical_overlays(self, ohlc_data: List[dict], current_price: dict) -> dict:
        """Calculate technical overlays from OHLC data"""
        if len(ohlc_data) < 20:
            return {"spread": None, "rr_hint": None, "atr": None, "volatility": None}

        # Extract price arrays
        closes = [bar["close"] for bar in ohlc_data if bar["close"] is not None]
        highs = [bar["high"] for bar in ohlc_data if bar["high"] is not None]
        lows = [bar["low"] for bar in ohlc_data if bar["low"] is not None]

        if len(closes) < 20:
            return {"spread": None, "rr_hint": None, "atr": None, "volatility": None}

        # Calculate spread
        spread = current_price.get("ask", 0) - current_price.get("bid", 0) if current_price else None

        # Calculate ATR (Average True Range) - last 14 periods
        if len(ohlc_data) >= 14:
            atr_periods = []
            for i in range(1, min(15, len(ohlc_data))):
                high = ohlc_data[-i]["high"]
                low = ohlc_data[-i]["low"]
                prev_close = ohlc_data[-i-1]["close"]

                if high is not None and low is not None and prev_close is not None:
                    true_range = max(
                        high - low,
                        abs(high - prev_close),
                        abs(low - prev_close)
                    )
                    atr_periods.append(true_range)

            atr = np.mean(atr_periods) if atr_periods else None
        else:
            atr = None

        # Calculate volatility (std dev of last 20 closes)
        if len(closes) >= 20:
            recent_closes = closes[-20:]
            volatility = np.std(recent_closes)
        else:
            volatility = None

        # Risk/Reward hint based on ATR
        if atr:
            # Suggest 1.5x ATR for potential target, 0.5x ATR for stop
            rr_hint = {
                "suggested_tp": round(atr * 1.5, 5),
                "suggested_sl": round(atr * 0.5, 5),
                "ratio": 3.0  # 1.5 / 0.5 = 3:1 ratio
            }
        else:
            rr_hint = None

        # Support/Resistance levels (last 50 bars)
        if len(highs) >= 50 and len(lows) >= 50:
            recent_highs = sorted(highs[-50:], reverse=True)
            recent_lows = sorted(lows[-50:])

            # Key levels (top 3 highs, bottom 3 lows)
            resistance_levels = recent_highs[:3]
            support_levels = recent_lows[:3]
        else:
            resistance_levels = []
            support_levels = []

        return {
            "spread": round(spread, 6) if spread else None,
            "rr_hint": rr_hint,
            "atr": round(atr, 6) if atr else None,
            "volatility": round(volatility, 6) if volatility else None,
            "support_levels": support_levels[:3],  # Top 3
            "resistance_levels": resistance_levels[:3],  # Top 3
            "data_quality": len(closes)  # Number of bars used
        }

    async def create_snapshot(self, symbol: str, trigger: str = "on_demand") -> Optional[dict]:
        """Create comprehensive signal snapshot for symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{int(time.time() // self.cache_ttl)}"
            if cache_key in self.snapshot_cache:
                cached_snapshot = self.snapshot_cache[cache_key].copy()
                cached_snapshot["cache_hit"] = True
                cached_snapshot["trigger"] = trigger
                return cached_snapshot

            # Get OHLC data (last 100 bars)
            ohlc_data = self.backfill.get_ohlc_data(symbol, 100)
            if not ohlc_data:
                logger.warning(f"⚠️ {symbol}: No OHLC data available for snapshot")
                return None

            # Get current price
            current_price = self.backfill.get_latest_price(symbol)
            if not current_price:
                logger.warning(f"⚠️ {symbol}: No current price available for snapshot")
                return None

            # Calculate technical overlays
            overlays = self.calculate_technical_overlays(ohlc_data, current_price)

            # Get account data for context
            account_data = self.account_poller.get_latest_account_data()

            # Create comprehensive snapshot
            snapshot = {
                "type": "signal_snapshot",
                "symbol": symbol,
                "timeframe": "M1",
                "ohlc": ohlc_data,  # Last 100 bars
                "price": {
                    "bid": current_price["bid"],
                    "ask": current_price["ask"],
                    "mid": current_price["mid"]
                },
                "overlays": overlays,
                "account_context": {
                    "balance": account_data.get("balance") if account_data else None,
                    "equity": account_data.get("equity") if account_data else None,
                    "free_margin": account_data.get("free_margin") if account_data else None,
                    "currency": account_data.get("currency") if account_data else None
                },
                "metadata": {
                    "trigger": trigger,
                    "bars_count": len(ohlc_data),
                    "backfill_completed": self.backfill.backfill_completed.get(symbol, False),
                    "data_age_ms": int((time.time() - (ohlc_data[-1]["timestamp"] if ohlc_data else 0)) * 1000)
                },
                "ts_epoch_ms": int(time.time() * 1000),
                "src": "metasocket"
            }

            # Cache the snapshot
            self.snapshot_cache[cache_key] = snapshot.copy()
            self.cache_timestamps[cache_key] = time.time()

            # Clean old cache entries
            self.clean_cache()

            # Send to callback if set
            if self.snapshot_callback:
                await self.snapshot_callback(snapshot)

            logger.debug(f"📸 Snapshot created for {symbol}: {len(ohlc_data)} bars, "
                        f"price={current_price['mid']:.5f}, ATR={overlays.get('atr', 'N/A')}")

            return snapshot

        except Exception as e:
            logger.error(f"❌ Error creating snapshot for {symbol}: {e}")
            return None

    async def create_multi_symbol_snapshot(self, symbols: List[str], trigger: str = "bulk_request") -> Dict[str, dict]:
        """Create snapshots for multiple symbols"""
        snapshots = {}

        # Create snapshots in parallel for performance
        tasks = [self.create_snapshot(symbol, trigger) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                snapshots[symbol] = result
            elif isinstance(result, Exception):
                logger.error(f"❌ Snapshot error for {symbol}: {result}")
            else:
                logger.warning(f"⚠️ No snapshot created for {symbol}")

        return snapshots

    async def on_fire_confirmation(self, fire_data: dict):
        """Create snapshot when fire confirmation is received"""
        symbol = fire_data.get("symbol")
        if not symbol:
            return

        logger.info(f"🔥 Creating snapshot for fire confirmation: {symbol}")
        snapshot = await self.create_snapshot(symbol, "fire_confirmation")

        if snapshot:
            # Enhance snapshot with fire context
            snapshot["fire_context"] = {
                "fire_id": fire_data.get("fire_id"),
                "ticket": fire_data.get("ticket"),
                "direction": fire_data.get("direction"),
                "entry_price": fire_data.get("price"),
                "volume": fire_data.get("volume"),
                "sl": fire_data.get("sl"),
                "tp": fire_data.get("tp")
            }

            return snapshot

        return None

    def clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = []

        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl * 2:  # Keep for 2x TTL
                expired_keys.append(key)

        for key in expired_keys:
            self.snapshot_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)

        if expired_keys:
            logger.debug(f"🧹 Cleaned {len(expired_keys)} expired snapshot cache entries")

    async def snapshot_service_loop(self):
        """Service loop for periodic tasks"""
        while True:
            try:
                # Clean cache every 5 minutes
                self.clean_cache()
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"❌ Snapshot service loop error: {e}")
                await asyncio.sleep(60)

    def get_health_stats(self) -> dict:
        """Get health statistics for snapshot producer"""
        return {
            "cache_entries": len(self.snapshot_cache),
            "cache_hit_ratio": "N/A",  # Could implement hit/miss tracking
            "symbols_supported": len(self.active_symbols),
            "backfill_ready_symbols": sum(1 for symbol in self.active_symbols
                                        if self.backfill.backfill_completed.get(symbol, False)),
            "cache_ttl_seconds": self.cache_ttl
        }

    async def start(self):
        """Start the snapshot producer service"""
        logger.info("🚀 Starting signal snapshot producer")
        await self.snapshot_service_loop()

# Example usage
if __name__ == "__main__":
    # This would typically be used with real backfill and subscription managers

    class MockBackfill:
        def get_ohlc_data(self, symbol, count):
            # Mock OHLC data
            return [{"timestamp": int(time.time()) - i*60, "open": 1.1000 + i*0.0001,
                    "high": 1.1010 + i*0.0001, "low": 1.0990 + i*0.0001,
                    "close": 1.1005 + i*0.0001, "volume": 100} for i in range(count)]

        def get_latest_price(self, symbol):
            return {"symbol": symbol, "bid": 1.1000, "ask": 1.1002, "mid": 1.1001}

        backfill_completed = {"EURUSD": True}

    class MockAccount:
        def get_latest_account_data(self):
            return {"balance": 1000.0, "equity": 1050.0, "free_margin": 800.0, "currency": "USD"}

    async def snapshot_handler(snapshot):
        print(f"SNAPSHOT: {snapshot['symbol']} - {len(snapshot['ohlc'])} bars, "
              f"ATR={snapshot['overlays'].get('atr', 'N/A')}")

    producer = SignalSnapshotProducer(MockBackfill(), None, MockAccount())
    producer.set_snapshot_callback(snapshot_handler)

    # Test snapshot creation
    async def test_snapshot():
        snapshot = await producer.create_snapshot("EURUSD")
        if snapshot:
            print(f"Created snapshot with {len(snapshot['ohlc'])} bars")

    import asyncio
    asyncio.run(test_snapshot())