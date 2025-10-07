#!/usr/bin/env python3
"""
Direct TCP Command Client for HydraSocket EA

Sends commands directly to the remote EA via native TCP sockets.
The EA expects JSONL format (JSON + newline) on its command port.

EA Details:
- Location: 185.244.67.11
- Command Port: 5555 (InpCommandPort in EA)
- Protocol: Native TCP with JSONL
- Expected format: Single-line JSON terminated with \n

This client connects directly to the EA and sends commands,
bypassing the need for ZMQ translation.
"""

import json
import logging
import socket
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EACommandClient")


class DirectEACommandClient:
    """Direct TCP client for sending commands to HydraSocket EA"""

    def __init__(self, ea_host="185.244.67.11", ea_port=5555, timeout=10):
        self.ea_host = ea_host
        self.ea_port = ea_port
        self.timeout = timeout
        self.connection = None

    def connect(self):
        """Establish TCP connection to EA command port"""
        try:
            logger.info(f"🔌 Connecting to EA at {self.ea_host}:{self.ea_port}")
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.connect((self.ea_host, self.ea_port))
            logger.info(f"✅ Connected to EA")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    def send_command(self, command_dict):
        """
        Send command to EA as JSONL (JSON + newline)

        Args:
            command_dict: Command dictionary to send

        Returns:
            bool: Success status
        """
        if not self.connection:
            logger.error("❌ Not connected to EA")
            return False

        try:
            # Convert to JSON and add newline (JSONL format)
            command_json = json.dumps(command_dict, separators=(",", ":"))
            payload = (command_json + "\n").encode("utf-8")

            logger.info(f"📤 Sending command: {command_dict.get('type', 'unknown')}")
            logger.debug(f"   Payload: {command_json[:100]}...")

            self.connection.send(payload)
            logger.info(f"✅ Command sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Send failed: {e}")
            return False

    def send_feed_set(self, symbols=None, timeframes=None, lookback=200):
        """
        Send feed_set command to initialize EA watchlist

        Args:
            symbols: Comma-separated symbol list (default: 19 major pairs)
            timeframes: Comma-separated TF list (default: M1,M5,H1)
            lookback: Candle lookback count (default: 200)
        """
        if symbols is None:
            symbols = "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF"

        if timeframes is None:
            timeframes = "M1,M5,H1"

        command = {
            "type": "feed_set",
            "request_ref": f"init-feed-{int(time.time())}",
            "target_uuid": "COMMANDER_DEV_001",
            "symbols": symbols,
            "tfs": timeframes,
            "lookback": lookback,
            "midbar": 0,
            "midbar_sec": 10,
        }

        return self.send_command(command)

    def send_fire_command(self, fire_id, symbol, direction, entry, sl, tp, lot):
        """
        Send fire (trade execution) command to EA

        Args:
            fire_id: Unique fire command ID
            symbol: Trading symbol (e.g., "EURUSD")
            direction: "BUY" or "SELL"
            entry: Entry price (0 for market)
            sl: Stop loss price
            tp: Take profit price
            lot: Lot size
        """
        command = {
            "type": "fire",
            "fire_id": fire_id,
            "target_uuid": "COMMANDER_DEV_001",
            "symbol": symbol,
            "direction": direction.upper(),
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "lot": round(lot, 2),  # MT5 requires 2 decimal places
        }

        return self.send_command(command)

    def close(self):
        """Close connection to EA"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("🔌 Connection closed")
            except:
                pass
            self.connection = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def test_feed_set():
    """Test function to send feed_set command"""
    logger.info("=" * 70)
    logger.info("🧪 Testing Direct EA Command Client - feed_set")
    logger.info("=" * 70)

    with DirectEACommandClient() as client:
        if client.connection:
            success = client.send_feed_set()

            if success:
                logger.info("\n" + "=" * 70)
                logger.info("✅ SUCCESS - feed_set command sent to EA")
                logger.info("=" * 70)
                logger.info("\n📊 Expected EA behavior:")
                logger.info("   1. EA calls BuildWatchlist() with 19 symbols")
                logger.info("   2. EA calls EmitBootstrap() - sends historical bars")
                logger.info("   3. EA starts emitting custom_bar_closed every 15 seconds")
                logger.info("   4. Universal Bridge receives bars and forwards to port 5556")
                logger.info("   5. Elite Guard receives data and starts pattern scanning")
                logger.info("\n⏱️  Check logs in 30 seconds:")
                logger.info("   tail -f /var/log/hydrasocket_universal_bridge.log | grep 'bar_closed\\|custom_bar'")
                logger.info("=" * 70)
            else:
                logger.error("\n❌ FAILED - Could not send feed_set command")
        else:
            logger.error("\n❌ FAILED - Could not connect to EA")


if __name__ == "__main__":
    test_feed_set()
