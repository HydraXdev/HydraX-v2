#!/usr/bin/env python3
"""
Convert Elite Guard to use Finnhub hybrid data instead of EA ticks
Preserves signal publishing and ML subscription
"""

import re

# Read the file
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'r') as f:
    content = f.read()

print("📝 Converting Elite Guard to Finnhub hybrid data...")

# 1. Add Finnhub import after existing imports
import_addition = """
# Finnhub hybrid data adapter (Phase 1 - Finnhub integration)
sys.path.insert(0, "/root/HydraX-v2")
from services.finnhub_data_adapter import FinnhubDataAdapter
"""

# Find the line after "sys.path.insert(0, "/root/HydraX-v2")" and add import
content = content.replace(
    'sys.path.insert(0, "/root/HydraX-v2")\n\n# Import Memory-Lite',
    f'sys.path.insert(0, "/root/HydraX-v2")\n{import_addition}\n# Import Memory-Lite'
)

# 2. Remove ZMQ tick consumer subscription in setup_zmq()
old_setup = '''    def setup_zmq(self):
        """Setup ZMQ connections"""
        try:
            # SUB to the zmq_gateway v2.0 PUB stream on port 5570
            # EA pushes to 5556 → zmq_gateway pulls and publishes to 5570
            self.tick_consumer = self.context.socket(zmq.SUB)
            self.tick_consumer.connect("tcp://127.0.0.1:5570")
            self.tick_consumer.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
            self.tick_consumer.setsockopt(zmq.RCVTIMEO, 100)  # 100ms timeout for non-blocking
            print(f"🔌 Tick/OHLC SUB consumer connected to 5570 - zmq_gateway v2.0 relay")

            # Publisher for signals
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            print(f"🔌 Signal PUB bound to 5557")

            # Subscribe to Grokkeeper ML adjustments on port 5565
            self.ml_subscriber = self.context.socket(zmq.SUB)
            self.ml_subscriber.connect("tcp://127.0.0.1:5565")
            self.ml_subscriber.setsockopt_string(zmq.SUBSCRIBE, "PATTERN_ADJUSTMENT")
            self.ml_subscriber.setsockopt(zmq.RCVTIMEO, 100)  # Non-blocking
            print("🤖 Connected to Grokkeeper ML feedback on port 5565")

            logger.info(
                "✅ ZMQ connections established (5570 SUB for ticks/OHLC, 5557 PUB for signals, 5565 SUB for ML)"
            )
            return True
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            return False'''

new_setup = '''    def setup_zmq(self):
        """Setup ZMQ connections (SIGNALS ONLY - no tick consumption)"""
        try:
            # ✅ Publisher for signals (KEEP - generators still publish signals!)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            print(f"🔌 Signal PUB bound to 5557")

            # ✅ Subscribe to Grokkeeper ML adjustments on port 5565 (KEEP - ML feedback)
            self.ml_subscriber = self.context.socket(zmq.SUB)
            self.ml_subscriber.connect("tcp://127.0.0.1:5565")
            self.ml_subscriber.setsockopt_string(zmq.SUBSCRIBE, "PATTERN_ADJUSTMENT")
            self.ml_subscriber.setsockopt(zmq.RCVTIMEO, 100)  # Non-blocking
            print("🤖 Connected to Grokkeeper ML feedback on port 5565")

            logger.info(
                "✅ ZMQ connections established (5557 PUB for signals, 5565 SUB for ML)"
            )
            logger.info("📡 Market data: Using Finnhub hybrid candles (not EA ticks)")
            return True
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            return False'''

content = content.replace(old_setup, new_setup)

# 3. Initialize Finnhub adapter in __init__ (find where ZMQ context is created)
old_init_zmq = "        self.context = zmq.Context()"
new_init_zmq = '''        self.context = zmq.Context()

        # Initialize Finnhub hybrid data adapter (replaces EA tick consumption)
        print("🌐 Initializing Finnhub Data Adapter...")
        self.finnhub_adapter = FinnhubDataAdapter()
        print("✅ Finnhub adapter ready - hybrid candles + ticks")'''

content = content.replace(old_init_zmq, new_init_zmq)

# 4. Replace data_listener with Finnhub candle poller
old_listener = '''    def data_listener(self):
        """Listen for market data from EA tick stream"""
        print("📡 Data listener started, connecting to EA tick stream (port 5556)...")

        while self.running:
            try:
                # Use PULL socket to consume from EA tick/OHLC stream
                if self.tick_consumer.poll(timeout=100):
                    message = self.tick_consumer.recv_string()

                    # Process EA market messages (TICK or OHLC packets)
                    self.process_market_message(message)

            except Exception as e:
                logger.debug(f"Listener error: {e}")
                time.sleep(0.1)'''

new_listener = '''    def data_listener(self):
        """Poll Finnhub hybrid candles (replaces EA tick stream)"""
        print("📡 Finnhub candle poller started (polling every 5 seconds)...")

        last_poll = {}  # Track last poll time per symbol

        while self.running:
            try:
                current_time = time.time()

                for symbol in self.trading_pairs:
                    # Poll every 5 seconds per symbol
                    if symbol not in last_poll or (current_time - last_poll[symbol]) >= 5:
                        # Get latest candle from Finnhub
                        candles = self.finnhub_adapter.get_candles(symbol, count=100)

                        if candles:
                            # Process candles into internal format
                            for candle in candles[-10:]:  # Process last 10 candles
                                # Build internal M1 buffer from Finnhub candles
                                if symbol not in self.M1:
                                    self.M1[symbol] = deque(maxlen=500)

                                self.M1[symbol].append({
                                    "open": candle['open'],
                                    "high": candle['high'],
                                    "low": candle['low'],
                                    "close": candle['close'],
                                    "volume": candle.get('volume', 0),
                                    "timestamp": candle['time'],
                                    "complete": True,
                                    "source": "finnhub"
                                })

                            last_poll[symbol] = current_time

                # Sleep to avoid tight loop
                time.sleep(1)

            except Exception as e:
                logger.debug(f"Finnhub poll error: {e}")
                time.sleep(5)'''

content = content.replace(old_listener, new_listener)

# 5. Remove tick_consumer cleanup in shutdown
old_cleanup = '''        if hasattr(self, "tick_consumer") and self.tick_consumer:
            self.tick_consumer.close()'''

new_cleanup = '''        # Finnhub adapter cleanup (if needed)
        if hasattr(self, "finnhub_adapter"):
            logger.info("🌐 Closing Finnhub adapter...")'''

content = content.replace(old_cleanup, new_cleanup)

# Write modified file
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'w') as f:
    f.write(content)

print("✅ Elite Guard converted to Finnhub hybrid data!")
print("")
print("Changes made:")
print("  1. ✅ Removed ZMQ tick consumer (port 5570)")
print("  2. ✅ Added Finnhub Data Adapter import")
print("  3. ✅ Initialized adapter in __init__")
print("  4. ✅ Replaced data_listener with Finnhub candle poller")
print("  5. ✅ Kept signal publisher (port 5557)")
print("  6. ✅ Kept ML subscriber (port 5565)")
print("")
print("Ready to restart Elite Guard!")
