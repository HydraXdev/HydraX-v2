#!/usr/bin/env python3
"""
EA v2.07 Signal Engine - FLAT Architecture Implementation
Complete ZMQ signal engine following EA v2.07 contract

Socket Architecture:
- ROUTER on :5555 - Bidirectional fire command channel (learns EA routing_id from HELLO)
- PULL on :5556 - Receives TICK messages from EA
- PULL on :5558 - Receives CONFIRM messages from EA
- PULL on :5560 - Receives additional EA data streams

Signal Flow:
EA DEALER -> HELLO -> Engine learns routing_id
EA PUSH -> TICK -> Engine builds candles
Engine analysis -> Fire command -> ROUTER -> EA DEALER
EA PUSH -> CONFIRM -> Engine receives trade results

Based on user's exact code structure requirements.
"""

import json
import logging
import signal
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import zmq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/root/HydraX-v2/logs/ea_v207_signal_engine.log"), logging.StreamHandler()],
)
logger = logging.getLogger("EA_V207_SignalEngine")


class CandleBook:
    """
    Manages OHLC candle building from tick data
    Supports multiple timeframes: M1, M5, M15, H1
    """

    def __init__(self):
        # symbol -> timeframe -> candles list
        self.candles = defaultdict(lambda: defaultdict(list))
        # symbol -> current incomplete candle
        self.current_candles = defaultdict(dict)

        # Timeframe definitions in seconds
        self.timeframes = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}

    def add_tick(self, symbol: str, price: float, timestamp: int):
        """Process a tick and update candles for all timeframes"""
        try:
            for tf_name, tf_seconds in self.timeframes.items():
                self._update_candle(symbol, tf_name, price, timestamp, tf_seconds)
        except Exception as e:
            logger.error(f"Error adding tick for {symbol}: {e}")

    def _update_candle(self, symbol: str, timeframe: str, price: float, timestamp: int, tf_seconds: int):
        """Update or create candle for specific timeframe"""
        # Calculate candle start time (aligned to timeframe boundary)
        candle_start = (timestamp // tf_seconds) * tf_seconds

        # Get current incomplete candle
        current_key = f"{timeframe}_{candle_start}"

        if current_key not in self.current_candles[symbol]:
            # Create new candle
            self.current_candles[symbol][current_key] = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": candle_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1,
                "tick_count": 1,
            }
        else:
            # Update existing candle
            candle = self.current_candles[symbol][current_key]
            candle["high"] = max(candle["high"], price)
            candle["low"] = min(candle["low"], price)
            candle["close"] = price
            candle["volume"] += 1
            candle["tick_count"] += 1

        # Check if we need to finalize the previous candle
        self._finalize_old_candles(symbol, timeframe, candle_start, tf_seconds)

    def _finalize_old_candles(self, symbol: str, timeframe: str, current_start: int, tf_seconds: int):
        """Move completed candles to permanent storage"""
        to_remove = []

        for key, candle in self.current_candles[symbol].items():
            if not key.startswith(f"{timeframe}_"):
                continue

            candle_start = candle["timestamp"]
            if candle_start < current_start:
                # This candle is complete, move to permanent storage
                self.candles[symbol][timeframe].append(candle.copy())
                to_remove.append(key)

        # Remove finalized candles from current_candles
        for key in to_remove:
            del self.current_candles[symbol][key]

        # Keep only last 500 candles per timeframe to manage memory
        if len(self.candles[symbol][timeframe]) > 500:
            self.candles[symbol][timeframe] = self.candles[symbol][timeframe][-500:]

    def get_candles(self, symbol: str, timeframe: str, count: int = 50) -> List[Dict]:
        """Get recent candles for analysis"""
        return self.candles[symbol][timeframe][-count:] if self.candles[symbol][timeframe] else []

    def get_current_candle(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get the current incomplete candle"""
        for key, candle in self.current_candles[symbol].items():
            if key.startswith(f"{timeframe}_"):
                return candle
        return None


class EAV207SignalEngine:
    """
    Complete EA v2.07 Signal Engine Implementation
    Follows FLAT architecture with proper ZMQ socket management
    """

    def __init__(self, use_alternative_ports=False):
        self.context = zmq.Context()
        self.running = False
        self.uuid_route = {}  # EA routing_id mapping
        self.candle_book = CandleBook()

        # Configuration
        self.use_alternative_ports = use_alternative_ports
        self.setup_ports()

        # Signal generation state
        self.signal_cooldowns = defaultdict(float)  # symbol -> last_signal_time
        self.min_signal_interval = 300  # 5 minutes between signals per symbol

        # Trading pairs to monitor
        self.trading_pairs = [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCHF",
            "USDCAD",
            "AUDUSD",
            "NZDUSD",
            "EURJPY",
            "GBPJPY",
            "EURGBP",
            "EURAUD",
            "EURCAD",
            "GBPAUD",
            "GBPCAD",
            "XAUUSD",
            "XAGUSD",
        ]

        # Performance tracking
        self.stats = {
            "ticks_processed": 0,
            "signals_generated": 0,
            "fire_commands_sent": 0,
            "confirmations_received": 0,
            "start_time": time.time(),
        }

    def setup_ports(self):
        """Setup ZMQ port configuration"""
        if self.use_alternative_ports:
            # Alternative ports (if conflicts exist)
            self.ports = {
                "router": 5565,  # Fire commands (alternative to 5555)
                "pull_market": 5566,  # Market data (alternative to 5556)
                "pull_confirm": 5568,  # Confirmations (alternative to 5558)
                "pull_secondary": 5570,  # Secondary data (alternative to 5560)
            }
            logger.info("Using alternative ports to avoid conflicts")
        else:
            # Standard EA v2.07 ports
            self.ports = {
                "router": 5555,  # Fire commands
                "pull_market": 5556,  # Market data from EA
                "pull_confirm": 5558,  # Trade confirmations from EA
                "pull_secondary": 5560,  # Additional EA data streams
            }
            logger.info("Using standard EA v2.07 ports")

    def setup_sockets(self):
        """Initialize and bind ZMQ sockets"""
        try:
            # ROUTER socket for bidirectional fire commands
            self.router = self.context.socket(zmq.ROUTER)
            self.router.setsockopt(zmq.LINGER, 0)
            self.router.bind(f"tcp://*:{self.ports['router']}")
            logger.info(f"✅ ROUTER bound to port {self.ports['router']} (fire commands)")

            # PULL sockets for incoming data
            self.pull_market = self.context.socket(zmq.PULL)
            self.pull_market.setsockopt(zmq.LINGER, 0)
            self.pull_market.bind(f"tcp://*:{self.ports['pull_market']}")
            logger.info(f"✅ PULL bound to port {self.ports['pull_market']} (market data)")

            self.pull_confirm = self.context.socket(zmq.PULL)
            self.pull_confirm.setsockopt(zmq.LINGER, 0)
            self.pull_confirm.bind(f"tcp://*:{self.ports['pull_confirm']}")
            logger.info(f"✅ PULL bound to port {self.ports['pull_confirm']} (confirmations)")

            self.pull_secondary = self.context.socket(zmq.PULL)
            self.pull_secondary.setsockopt(zmq.LINGER, 0)
            self.pull_secondary.bind(f"tcp://*:{self.ports['pull_secondary']}")
            logger.info(f"✅ PULL bound to port {self.ports['pull_secondary']} (secondary)")

            # Setup poller for non-blocking message handling
            self.poller = zmq.Poller()
            self.poller.register(self.router, zmq.POLLIN)
            self.poller.register(self.pull_market, zmq.POLLIN)
            self.poller.register(self.pull_confirm, zmq.POLLIN)
            self.poller.register(self.pull_secondary, zmq.POLLIN)

            logger.info("🎯 All ZMQ sockets configured and ready")

        except zmq.ZMQError as e:
            logger.error(f"❌ ZMQ socket setup failed: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected socket setup error: {e}")
            raise

    def handle_hello_message(self, routing_id: bytes, message: Dict):
        """Handle HELLO handshake from EA to learn routing identity"""
        try:
            ea_uuid = message.get("uuid", "UNKNOWN")
            ea_version = message.get("version", "UNKNOWN")

            # Store routing identity for this EA
            self.uuid_route[ea_uuid] = routing_id

            logger.info(f"🤝 HELLO from EA {ea_uuid} v{ea_version}")
            logger.info(f"   Routing ID: {routing_id.hex()}")

            # Send acknowledgment back to EA
            ack_response = {
                "type": "hello_ack",
                "server_version": "EA_V207_SIGNAL_ENGINE_1.0",
                "timestamp": int(time.time()),
                "status": "ready",
            }

            self.send_router_json(routing_id, ack_response)
            logger.info(f"✅ Sent HELLO_ACK to {ea_uuid}")

        except Exception as e:
            logger.error(f"❌ Error handling HELLO: {e}")

    def handle_tick_message(self, message: Dict):
        """Process TICK message from EA and update candles"""
        try:
            symbol = message.get("symbol")
            bid = message.get("bid")
            ask = message.get("ask")
            timestamp = message.get("timestamp", int(time.time()))

            if not symbol or bid is None or ask is None:
                logger.warning(f"Invalid TICK data: {message}")
                return

            # Use mid-price for candle building
            mid_price = (bid + ask) / 2.0

            # Add tick to candle book
            self.candle_book.add_tick(symbol, mid_price, timestamp)

            self.stats["ticks_processed"] += 1

            # Check for signal generation (every 100 ticks to avoid spam)
            if self.stats["ticks_processed"] % 100 == 0:
                self.maybe_signal(symbol)

        except Exception as e:
            logger.error(f"❌ Error processing TICK: {e}")

    def handle_confirm_message(self, message: Dict):
        """Process trade confirmation from EA"""
        try:
            fire_id = message.get("fire_id")
            status = message.get("status")
            ticket = message.get("ticket")
            price = message.get("price")

            logger.info(f"📋 CONFIRM: {fire_id} -> {status}")
            if ticket:
                logger.info(f"   Ticket: {ticket}, Price: {price}")

            self.stats["confirmations_received"] += 1

            # Here you could update database or notify other systems
            # For now, just log the confirmation

        except Exception as e:
            logger.error(f"❌ Error processing CONFIRM: {e}")

    def maybe_signal(self, symbol: str):
        """
        Check if we should generate a signal for the given symbol
        This is where the actual trading strategy logic goes
        """
        try:
            # Check cooldown to avoid spam
            now = time.time()
            if now - self.signal_cooldowns[symbol] < self.min_signal_interval:
                return

            # Get recent candles for analysis
            m5_candles = self.candle_book.get_candles(symbol, "M5", 20)
            m15_candles = self.candle_book.get_candles(symbol, "M15", 20)

            if len(m5_candles) < 10 or len(m15_candles) < 5:
                return  # Not enough data

            # Simple strategy: Look for volatility compression breakout
            signal = self.detect_vcb_breakout(symbol, m5_candles, m15_candles)

            if signal:
                self.queue_fire(signal)
                self.signal_cooldowns[symbol] = now

        except Exception as e:
            logger.error(f"❌ Error in signal detection for {symbol}: {e}")

    def detect_vcb_breakout(self, symbol: str, m5_candles: List[Dict], m15_candles: List[Dict]) -> Optional[Dict]:
        """
        Detect Volatility Compression Breakout pattern
        Simple implementation for demonstration
        """
        try:
            if len(m5_candles) < 10:
                return None

            # Calculate recent volatility (simplified)
            recent_ranges = []
            for candle in m5_candles[-10:]:
                range_pips = (candle["high"] - candle["low"]) * 10000  # Rough pip calculation
                recent_ranges.append(range_pips)

            avg_range = sum(recent_ranges) / len(recent_ranges)
            current_range = recent_ranges[-1]

            # Look for compression followed by expansion
            if avg_range < 5.0 and current_range > avg_range * 1.5:
                # Potential breakout
                last_candle = m5_candles[-1]
                prev_candle = m5_candles[-2] if len(m5_candles) > 1 else last_candle

                # Determine direction
                direction = "BUY" if last_candle["close"] > prev_candle["close"] else "SELL"

                # Calculate entry, SL, TP
                entry = last_candle["close"]

                if direction == "BUY":
                    sl = last_candle["low"] - (20 * 0.0001)  # 20 pip SL
                    tp = entry + (30 * 0.0001)  # 30 pip TP
                else:
                    sl = last_candle["high"] + (20 * 0.0001)  # 20 pip SL
                    tp = entry - (30 * 0.0001)  # 30 pip TP

                signal = {
                    "signal_id": f"VCB_{symbol}_{int(time.time())}",
                    "symbol": symbol,
                    "direction": direction,
                    "entry": round(entry, 5),
                    "sl": round(sl, 5),
                    "tp": round(tp, 5),
                    "confidence": 75.0,
                    "pattern_type": "VCB_BREAKOUT",
                    "timestamp": int(time.time()),
                }

                logger.info(f"🎯 VCB Signal detected: {symbol} {direction} @ {entry}")
                return signal

        except Exception as e:
            logger.error(f"❌ Error in VCB detection: {e}")

        return None

    def queue_fire(self, signal: Dict):
        """
        Generate and queue a fire command for the signal
        This creates the actual trade execution command
        """
        try:
            # Create fire command matching EA v2.07 format
            fire_command = {
                "type": "fire",
                "fire_id": signal["signal_id"],
                "target_uuid": "COMMANDER_DEV_001",  # Default EA target
                "symbol": signal["symbol"],
                "direction": signal["direction"],
                "entry": signal["entry"],
                "sl": signal["sl"],
                "tp": signal["tp"],
                "lot": 0.01,  # Default lot size
                "timestamp": signal["timestamp"],
            }

            # Find the appropriate EA routing ID
            target_uuid = fire_command["target_uuid"]
            if target_uuid in self.uuid_route:
                routing_id = self.uuid_route[target_uuid]
                self.send_router_json(routing_id, fire_command)

                self.stats["fire_commands_sent"] += 1
                self.stats["signals_generated"] += 1

                logger.info(f"🔥 FIRE command sent: {fire_command['fire_id']}")
                logger.info(f"   {fire_command['symbol']} {fire_command['direction']} @ {fire_command['entry']}")

            else:
                logger.warning(f"⚠️ No routing ID found for EA {target_uuid}")

        except Exception as e:
            logger.error(f"❌ Error queuing fire command: {e}")

    def send_router_json(self, routing_id: bytes, data: Dict):
        """Send JSON message via ROUTER socket to specific EA"""
        try:
            json_str = json.dumps(data)
            self.router.send_multipart([routing_id, json_str.encode("utf-8")])
        except Exception as e:
            logger.error(f"❌ Error sending router message: {e}")

    def main_loop(self):
        """Main message processing loop"""
        logger.info("🚀 Starting main loop...")

        last_stats_time = time.time()

        while self.running:
            try:
                # Poll for messages with timeout
                events = dict(self.poller.poll(timeout=1000))  # 1 second timeout

                # Handle ROUTER messages (HELLO, other bidirectional)
                if self.router in events:
                    try:
                        routing_id, message_bytes = self.router.recv_multipart(zmq.NOBLOCK)
                        message = json.loads(message_bytes.decode("utf-8"))

                        msg_type = message.get("type", "unknown")
                        if msg_type == "hello":
                            self.handle_hello_message(routing_id, message)
                        else:
                            logger.info(f"📨 Router message: {msg_type} from {routing_id.hex()}")

                    except zmq.Again:
                        pass
                    except Exception as e:
                        logger.error(f"❌ Error handling router message: {e}")

                # Handle market data messages
                if self.pull_market in events:
                    try:
                        message_bytes = self.pull_market.recv(zmq.NOBLOCK)
                        message = json.loads(message_bytes.decode("utf-8"))

                        msg_type = message.get("type", "unknown")
                        if msg_type == "tick":
                            self.handle_tick_message(message)
                        else:
                            logger.debug(f"📈 Market message: {msg_type}")

                    except zmq.Again:
                        pass
                    except Exception as e:
                        logger.error(f"❌ Error handling market message: {e}")

                # Handle confirmation messages
                if self.pull_confirm in events:
                    try:
                        message_bytes = self.pull_confirm.recv(zmq.NOBLOCK)
                        message = json.loads(message_bytes.decode("utf-8"))

                        msg_type = message.get("type", "unknown")
                        if msg_type == "confirm":
                            self.handle_confirm_message(message)
                        else:
                            logger.info(f"📋 Confirm message: {msg_type}")

                    except zmq.Again:
                        pass
                    except Exception as e:
                        logger.error(f"❌ Error handling confirm message: {e}")

                # Handle secondary data messages
                if self.pull_secondary in events:
                    try:
                        message_bytes = self.pull_secondary.recv(zmq.NOBLOCK)
                        message = json.loads(message_bytes.decode("utf-8"))

                        logger.debug(f"📡 Secondary message: {message.get('type', 'unknown')}")

                    except zmq.Again:
                        pass
                    except Exception as e:
                        logger.error(f"❌ Error handling secondary message: {e}")

                # Print stats every 60 seconds
                now = time.time()
                if now - last_stats_time > 60:
                    self.print_stats()
                    last_stats_time = now

            except KeyboardInterrupt:
                logger.info("🛑 Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"💥 Main loop error: {e}")
                logger.error(traceback.format_exc())
                time.sleep(1)  # Brief pause before retry

    def print_stats(self):
        """Print current engine statistics"""
        uptime = time.time() - self.stats["start_time"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        logger.info("📊 Engine Statistics:")
        logger.info(f"   Uptime: {hours:02d}:{minutes:02d}")
        logger.info(f"   Ticks processed: {self.stats['ticks_processed']}")
        logger.info(f"   Signals generated: {self.stats['signals_generated']}")
        logger.info(f"   Fire commands sent: {self.stats['fire_commands_sent']}")
        logger.info(f"   Confirmations received: {self.stats['confirmations_received']}")
        logger.info(f"   Connected EAs: {len(self.uuid_route)}")

        # Candle book stats
        total_symbols = len([s for s in self.trading_pairs if self.candle_book.candles[s]])
        logger.info(f"   Symbols with candles: {total_symbols}")

    def start(self):
        """Start the signal engine"""
        try:
            logger.info("🚀 Starting EA v2.07 Signal Engine...")

            self.setup_sockets()
            self.running = True

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            logger.info("✅ EA v2.07 Signal Engine started successfully")
            logger.info(f"   Router port: {self.ports['router']} (fire commands)")
            logger.info(f"   Market port: {self.ports['pull_market']} (ticks)")
            logger.info(f"   Confirm port: {self.ports['pull_confirm']} (confirmations)")
            logger.info(f"   Secondary port: {self.ports['pull_secondary']} (additional)")

            # Start main processing loop
            self.main_loop()

        except Exception as e:
            logger.error(f"💥 Failed to start signal engine: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            self.cleanup()

    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {sig}, shutting down...")
        self.running = False

    def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up resources...")

        self.running = False

        # Close sockets
        for attr_name in ["router", "pull_market", "pull_confirm", "pull_secondary"]:
            if hasattr(self, attr_name):
                socket = getattr(self, attr_name)
                socket.close()
                logger.info(f"   Closed {attr_name}")

        # Terminate context
        self.context.term()
        logger.info("✅ Cleanup complete")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--alternative-ports":
        use_alternative = True
        logger.info("🔄 Using alternative ports to avoid conflicts")
    else:
        use_alternative = False
        logger.info("📡 Using standard EA v2.07 ports")

    engine = EAV207SignalEngine(use_alternative_ports=use_alternative)

    try:
        engine.start()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"💥 Engine failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
