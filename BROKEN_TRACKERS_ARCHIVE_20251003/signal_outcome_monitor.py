#!/usr/bin/env python3
"""
Signal Outcome Monitor - Reliable Event Bus Edition
Monitors EVERY signal against live price to determine actual WIN/LOSS
Reports to event bus and updates comprehensive_tracking.jsonl
"""

import sys

sys.path.append("/root/HydraX-v2")

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

import zmq

from event_bus.consumer import EventConsumer
from event_bus.producer import EventProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SignalOutcomeMonitor:
    """Monitor all signals against live price data"""

    def __init__(self):
        # Event bus
        self.consumer = EventConsumer()
        self.producer = EventProducer()

        # ZMQ for live ticks
        self.context = zmq.Context()
        self.tick_subscriber = self.context.socket(zmq.SUB)
        self.tick_subscriber.connect("tcp://localhost:5560")
        self.tick_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

        # Tracking file
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"

        # Active signals being monitored {signal_id: signal_data}
        self.active_signals = {}

        # Current prices {symbol: {'bid': price, 'ask': price}}
        self.current_prices = {}

        logger.info("🎯 Signal Outcome Monitor initialized")

    def handle_signal_generated(self, event_data):
        """Handle new signal from event bus"""
        try:
            signal_id = event_data.get("signal_id")
            symbol = event_data.get("symbol")
            direction = event_data.get("direction")
            entry = float(event_data.get("entry_price", 0))
            sl = float(event_data.get("stop_loss", 0))
            tp = float(event_data.get("take_profit", 0))
            confidence = float(event_data.get("confidence", 0))
            pattern = event_data.get("pattern_type", "UNKNOWN")
            session = event_data.get("session", "UNKNOWN")

            if not all([signal_id, symbol, direction, entry, sl, tp]):
                logger.warning(f"Incomplete signal data: {signal_id}")
                return

            # Store signal for monitoring
            self.active_signals[signal_id] = {
                "signal_id": signal_id,
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "confidence": confidence,
                "pattern_type": pattern,
                "session": session,
                "generated_at": int(time.time()),
                "outcome": "PENDING",
                "max_favorable": 0.0,
                "max_adverse": 0.0,
            }

            logger.info(f"📊 Monitoring: {signal_id} - {symbol} {direction} @ {confidence}%")

        except Exception as e:
            logger.error(f"Error handling signal generated: {e}")

    def process_tick(self, tick_data):
        """Process incoming tick and check against active signals"""
        try:
            symbol = tick_data.get("symbol")
            bid = float(tick_data.get("bid", 0))
            ask = float(tick_data.get("ask", 0))

            if not symbol or not bid or not ask:
                return

            # Update current price
            self.current_prices[symbol] = {"bid": bid, "ask": ask}

            # Check all active signals for this symbol
            to_remove = []

            for signal_id, signal in list(self.active_signals.items()):
                if signal["symbol"] != symbol:
                    continue

                # Get execution price based on direction
                if signal["direction"] == "BUY":
                    current_price = ask  # Buy at ask
                    price_diff = current_price - signal["entry_price"]
                else:  # SELL
                    current_price = bid  # Sell at bid
                    price_diff = signal["entry_price"] - current_price

                # Update max favorable/adverse
                if price_diff > signal["max_favorable"]:
                    signal["max_favorable"] = price_diff
                if price_diff < 0 and abs(price_diff) > signal["max_adverse"]:
                    signal["max_adverse"] = abs(price_diff)

                # Check TP hit
                tp_distance = abs(signal["tp"] - signal["entry_price"])
                if price_diff >= tp_distance:
                    signal["outcome"] = "WIN"
                    signal["exit_price"] = current_price
                    signal["pips_result"] = price_diff
                    self.record_outcome(signal)
                    to_remove.append(signal_id)
                    logger.info(f"✅ WIN: {signal_id} - {symbol} TP hit @ {current_price}")
                    continue

                # Check SL hit
                sl_distance = abs(signal["sl"] - signal["entry_price"])
                if price_diff <= -sl_distance:
                    signal["outcome"] = "LOSS"
                    signal["exit_price"] = current_price
                    signal["pips_result"] = price_diff
                    self.record_outcome(signal)
                    to_remove.append(signal_id)
                    logger.info(f"❌ LOSS: {signal_id} - {symbol} SL hit @ {current_price}")
                    continue

            # Remove completed signals
            for signal_id in to_remove:
                del self.active_signals[signal_id]

        except Exception as e:
            logger.error(f"Error processing tick: {e}")

    def record_outcome(self, signal):
        """Record signal outcome to file and event bus"""
        try:
            # Add metadata
            signal["resolved_at"] = int(time.time())
            signal["duration_minutes"] = (signal["resolved_at"] - signal["generated_at"]) / 60

            # Write to tracking file
            with open(self.tracking_file, "a") as f:
                f.write(json.dumps(signal) + "\n")

            # Publish to event bus
            outcome_event = {
                "signal_id": signal["signal_id"],
                "symbol": signal["symbol"],
                "direction": signal["direction"],
                "pattern_type": signal["pattern_type"],
                "session": signal.get("session", "UNKNOWN"),
                "confidence": signal["confidence"],
                "outcome": signal["outcome"],
                "pips_result": signal.get("pips_result", 0),
                "duration_minutes": signal["duration_minutes"],
                "max_favorable": signal["max_favorable"],
                "max_adverse": signal["max_adverse"],
                "resolved_at": signal["resolved_at"],
            }

            self.producer.publish("signal.outcome", outcome_event)

            # Log outcome
            emoji = "✅" if signal["outcome"] == "WIN" else "❌" if signal["outcome"] == "LOSS" else "⏱️"
            pips = signal.get("pips_result", 0)
            logger.info(f"{emoji} {signal['outcome']}: {signal['signal_id']} - {pips:+.1f} pips")

        except Exception as e:
            logger.error(f"Error recording outcome: {e}")

    def print_status(self):
        """Print monitoring status"""
        logger.info("=" * 70)
        logger.info(f"📊 Active Signals: {len(self.active_signals)}")
        logger.info(f"💹 Symbols Tracked: {len(self.current_prices)}")

        if self.active_signals:
            logger.info("Currently monitoring:")
            for signal_id, signal in list(self.active_signals.items())[:5]:
                age = int(time.time()) - signal["generated_at"]
                age_str = f"{age//60}m" if age < 3600 else f"{age//3600}h{(age%3600)//60}m"
                logger.info(f"  {signal['symbol']} {signal['direction']} @ {signal['confidence']}% ({age_str})")

        logger.info("=" * 70)

    def run(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting Signal Outcome Monitor...")

        # Subscribe to signal generation
        self.consumer.subscribe("signal.generated", self.handle_signal_generated)

        # Start event consumer in background
        import threading

        consumer_thread = threading.Thread(target=self.consumer.start, daemon=True)
        consumer_thread.start()

        logger.info("✅ Subscribed to signal.generated events")
        logger.info("✅ Connected to tick stream (port 5560)")
        logger.info("✅ Monitoring EVERY signal to WIN/LOSS outcome")

        # Main tick monitoring loop
        last_status = 0

        try:
            while True:
                # Check for ticks (non-blocking with timeout)
                try:
                    if self.tick_subscriber.poll(timeout=100):  # 100ms timeout
                        message = self.tick_subscriber.recv_string(zmq.NOBLOCK)

                        # Parse tick data
                        if message.startswith("TICK "):
                            tick_json = message[5:]
                            tick_data = json.loads(tick_json)
                            self.process_tick(tick_data)
                except zmq.Again:
                    pass  # No message available
                except Exception as e:
                    logger.error(f"Error receiving tick: {e}")

                # Print status every 5 minutes
                if int(time.time()) - last_status >= 300:
                    self.print_status()
                    last_status = int(time.time())

        except KeyboardInterrupt:
            logger.info("🛑 Signal Outcome Monitor shutting down...")

            # Record all pending signals as TIMEOUT
            for signal in self.active_signals.values():
                signal["outcome"] = "TIMEOUT"
                self.record_outcome(signal)


if __name__ == "__main__":
    monitor = SignalOutcomeMonitor()
    monitor.run()
