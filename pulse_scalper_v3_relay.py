#!/usr/bin/env python3
"""
Pulse Scalper v3.0 ZMQ-to-HTTP Relay
====================================
Version: 3.0 Optimized (October 19, 2025)
Purpose: Bridge PULSE v3.0 signals from ZMQ port 5562 to API server

Architecture:
- Subscribes: tcp://127.0.0.1:5562 (PULSE v3.0 optimized signals)
- POSTs to: http://localhost:8888/api/signals
- Source Tag: "pulse_v3_optimized"

Relay Pattern: Identical to Elite Guard / Apex relays for consistency

Author: Claude Code
Date: October 19, 2025
"""

import json
import zmq
import requests
import logging
import time
import signal as signal_handler
import sys
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/pulse_v3_relay.log"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("PulseV3Relay")


class PulseV3Relay:
    """ZMQ-to-HTTP relay for PULSE v3.0 Optimized signals"""

    def __init__(self):
        self.running = False
        self.context = zmq.Context()
        self.subscriber = None

        # Configuration
        self.zmq_endpoint = "tcp://127.0.0.1:5562"
        self.webapp_url = "http://localhost:8888/api/signals"
        self.http_timeout = 3
        self.reconnect_delay = 5

        # Statistics
        self.stats = {
            "signals_received": 0,
            "signals_relayed": 0,
            "http_errors": 0,
            "zmq_errors": 0,
            "started_at": None,
        }

    def start(self):
        """Start the ZMQ-to-HTTP relay"""
        self.running = True
        self.stats["started_at"] = time.time()

        logger.info("🚀 Starting PULSE v3.0 Optimized ZMQ-to-HTTP Relay")
        logger.info(f"📡 ZMQ Source: {self.zmq_endpoint}")
        logger.info(f"🌐 HTTP Target: {self.webapp_url}")
        logger.info("=" * 60)

        # Connect to ZMQ publisher
        if not self._connect_subscriber():
            logger.error("❌ Failed to connect to ZMQ source")
            return

        logger.info("✅ PULSE v3.0 Relay started successfully")
        logger.info("🔍 Listening for PULSE_SIGNAL messages...")

        # Main relay loop
        while self.running:
            try:
                # Wait for signal with timeout
                try:
                    message = self.subscriber.recv_string(flags=zmq.NOBLOCK)
                    self._process_signal(message)
                except zmq.Again:
                    # No message available, continue
                    time.sleep(0.1)
                    continue

            except KeyboardInterrupt:
                logger.info("⚠️ Received shutdown signal")
                self.stop()
                break
            except Exception as e:
                logger.error(f"❌ Relay loop error: {e}")
                self.stats["zmq_errors"] += 1
                time.sleep(self.reconnect_delay)

    def stop(self):
        """Stop the relay"""
        logger.info("🛑 Stopping PULSE v3.0 Relay...")
        self.running = False

        if self.subscriber:
            self.subscriber.close()

        self.context.term()
        logger.info("✅ PULSE v3.0 Relay stopped")

        # Log final stats
        self._log_stats()

    def _connect_subscriber(self):
        """Connect to ZMQ publisher"""
        try:
            if self.subscriber:
                self.subscriber.close()

            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect(self.zmq_endpoint)
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
            self.subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

            logger.info(f"✅ Connected to ZMQ: {self.zmq_endpoint}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to ZMQ: {e}")
            self.stats["zmq_errors"] += 1
            return False

    def _process_signal(self, message: str):
        """Process and relay a signal"""
        try:
            # Check for PULSE_SIGNAL prefix
            if not message.startswith("PULSE_SIGNAL"):
                logger.debug(f"Ignoring non-PULSE message: {message[:50]}...")
                return

            # Parse signal JSON
            signal_json = message.split(" ", 1)[1]
            signal_data = json.loads(signal_json)

            self.stats["signals_received"] += 1

            logger.info(
                f"📨 Received PULSE v3.0 signal: {signal_data.get('signal_id', 'UNKNOWN')} "
                f"for {signal_data.get('symbol', 'UNKNOWN')} @ {signal_data.get('confidence', 0)}% "
                f"(tier: {signal_data.get('tier', 'N/A')})"
            )

            # Relay to webapp
            self._post_to_webapp(signal_data)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid signal JSON: {e}")
            logger.debug(f"Raw message: {message}")
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")

    def _post_to_webapp(self, signal_data: Dict):
        """POST signal to webapp API"""
        try:
            # Add source tag for identification
            signal_data["source"] = "pulse_v3_optimized"

            response = requests.post(
                self.webapp_url,
                json=signal_data,
                timeout=self.http_timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                self.stats["signals_relayed"] += 1
                logger.info(
                    f"✅ Relayed signal {signal_data.get('signal_id')} "
                    f"for {signal_data.get('symbol')} successfully"
                )
            else:
                self.stats["http_errors"] += 1
                logger.error(
                    f"❌ HTTP {response.status_code}: {response.text[:100]}"
                )

        except requests.exceptions.Timeout:
            self.stats["http_errors"] += 1
            logger.error(f"⏱️ HTTP timeout posting to {self.webapp_url}")
        except requests.exceptions.ConnectionError:
            self.stats["http_errors"] += 1
            logger.error(f"🔌 Connection error: Cannot reach {self.webapp_url}")
        except Exception as e:
            self.stats["http_errors"] += 1
            logger.error(f"❌ HTTP POST error: {e}")

    def _log_stats(self):
        """Log relay statistics"""
        runtime = time.time() - self.stats["started_at"]
        logger.info("=" * 60)
        logger.info("📊 PULSE v3.0 Relay Statistics:")
        logger.info(f"   Signals Received: {self.stats['signals_received']}")
        logger.info(f"   Signals Relayed: {self.stats['signals_relayed']}")
        logger.info(f"   HTTP Errors: {self.stats['http_errors']}")
        logger.info(f"   ZMQ Errors: {self.stats['zmq_errors']}")
        logger.info(f"   Runtime: {runtime:.1f}s")
        logger.info("=" * 60)


def signal_handler_func(sig, frame):
    """Handle shutdown signals"""
    logger.info("⚠️ Shutdown signal received")
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handlers
    signal_handler.signal(signal_handler.SIGINT, signal_handler_func)
    signal_handler.signal(signal_handler.SIGTERM, signal_handler_func)

    # Start relay
    relay = PulseV3Relay()
    relay.start()
