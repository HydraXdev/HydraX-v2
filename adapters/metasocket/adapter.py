#!/usr/bin/env python3
"""
MetaSocket Adapter for BITTEN Trading System
CUTOVER MODE: Minimal surgical changes only
"""
import os
import json
import time
import socket
import threading
import logging
import random
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Deque

# Event publishing
import redis
import zmq

logger = logging.getLogger(__name__)

class MetaSocketAdapter:
    """
    MetaSocket TCP adapter with circuit breaker and idempotency
    Maps MetaSocket events to BITTEN v1 frozen schemas
    """

    def __init__(self):
        # Config from env
        self.host = os.getenv('MSKT_HOST', '185.244.67.11')
        self.cmd_port = int(os.getenv('MSKT_CMD_PORT', '8777'))
        self.stream_port = int(os.getenv('MSKT_STREAM_PORT', '8778'))

        # Event bus connections
        self.redis_client = redis.Redis(decode_responses=True)
        self.zmq_context = zmq.Context()
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        self.zmq_publisher.bind("tcp://*:5562")  # MetaSocket events on separate port

        # Circuit breaker state
        self.circuit_open = False
        self.last_error_time = 0
        self.error_count = 0
        self.error_threshold = 5
        self.recovery_timeout = 30
        self.backoff_delays = [1, 2, 5, 10, 15, 30]
        self.backoff_index = 0

        # 22 active symbols
        self.symbols = ["EURUSD","GBPUSD","USDCHF","USDJPY","AUDUSD","NZDUSD",
                       "EURJPY","GBPJPY","EURGBP","EURAUD","GBPCAD","AUDJPY","NZDJPY","CHFJPY","CADJPY","AUDCAD",
                       "USDCNH","AUDNZD","XAUUSD","XAGUSD"]

        # Metrics for health logging
        self.tick_counts = defaultdict(int)
        self.last_tick_times = defaultdict(float)
        self.last_metrics_log = 0
        self.debug_event_count = 0  # For first 20 events logging

        # Command client state
        self.push_active = False
        self.last_push_ts = 0
        self.pending_requests = set()  # Track immediate requests
        self.symbol_index = 0  # For round-robin polling
        self.last_poll_time = 0
        self.last_account_poll = 0
        self.last_keepalive = 0

        # OHLC backfill store
        self.ohlc_store = defaultdict(list)  # symbol -> [ohlc_bars]
        self.backfill_completed = set()  # symbols with backfill done

        # Connection tracking
        self.cmd_socket: Optional[socket.socket] = None
        self.stream_socket: Optional[socket.socket] = None
        self.running = False

    def start(self):
        """Start adapter with spec-compliant command client"""
        print("🚀 Starting MetaSocket adapter", flush=True)
        self.running = True

        # Start command client loop
        threading.Thread(target=self._command_client_loop, daemon=True).start()
        threading.Thread(target=self._metrics_logger, daemon=True).start()

        print("✅ MetaSocket adapter started", flush=True)

    def stop(self):
        """Stop adapter gracefully"""
        self.running = False
        if self.cmd_socket:
            self.cmd_socket.close()
        if self.stream_socket:
            self.stream_socket.close()
        self.zmq_publisher.close()
        self.zmq_context.term()

    def jsend(self, sock: socket.socket, obj: dict):
        """Send JSON + newline"""
        line = json.dumps(obj, separators=(',',':')) + "\n"
        sock.sendall(line.encode('utf-8'))

    def publish(self, json_obj: dict):
        """Publish JSON object to ZMQ (no topic frame)"""
        try:
            msg = json.dumps(json_obj, separators=(',',':'))
            self.zmq_publisher.send_string(msg)
        except Exception as e:
            print(f"💥 ZMQ publish failed: {e}", flush=True)

    def _command_client_loop(self):
        """Spec-compliant command client on port 8777"""
        print("📡 Starting command client", flush=True)

        while self.running:
            try:
                print(f"[command] connecting to {self.host}:{self.cmd_port} ...", flush=True)
                with socket.create_connection((self.host, self.cmd_port), timeout=5) as s:
                    s.settimeout(1.0)  # For recv timeout
                    buffer = b""

                    print("COMMAND: connected 8777 (spec-compliant)", flush=True)

                    # Send initial commands
                    self.jsend(s, {"MSG":"HELP"})
                    self.jsend(s, {"MSG":"CONNECTION_STATUS"})
                    self.jsend(s, {"MSG":"ACCOUNT_STATUS"})

                    # Request price history backfill for each symbol
                    for sym in self.symbols:
                        if sym not in self.backfill_completed:
                            self.jsend(s, {"MSG":"PRICE_HISTORY","SYMBOL":sym,"TIMEFRAME":"PERIOD_M1","COUNT":300})

                    # Attempt push mode
                    self.jsend(s, {"MSG":"TRACK_TRADE_EVENTS","enabled":True})
                    for sym in self.symbols:
                        self.jsend(s, {"MSG":"TRACK_PRICES","SYMBOL":sym})
                        self.jsend(s, {"MSG":"TRACK_OHLC","SYMBOL":sym,"TIMEFRAME":"M1"})

                    # Reset state
                    self.push_active = False
                    self.last_push_ts = 0
                    self.pending_requests.clear()
                    self.symbol_index = 0
                    push_detection_start = time.time()
                    self.last_poll_time = 0
                    self.last_account_poll = 0
                    self.last_keepalive = time.time()

                    while self.running:
                        now = time.time()

                        # Read responses
                        try:
                            chunk = s.recv(4096)
                            if chunk:
                                buffer += chunk
                                while b"\n" in buffer:
                                    line, buffer = buffer.split(b"\n", 1)
                                    line = line.strip(b"\r\n ")
                                    if line:
                                        try:
                                            response = json.loads(line.decode('utf-8'))
                                            self._process_command_response(response)

                                            # Detect push mode
                                            msg_type = response.get('MSG', '')
                                            if msg_type in ['TICK_DATA', 'QUOTE'] and not self.push_active:
                                                # Check if this is unsolicited (not from our immediate request)
                                                req_key = f"{msg_type}_{response.get('SYMBOL', '')}"
                                                if req_key not in self.pending_requests:
                                                    self.push_active = True
                                                    self.last_push_ts = time.time()
                                                    print("COMMAND: PUSH active via TRACK_*", flush=True)
                                                else:
                                                    self.pending_requests.discard(req_key)

                                        except json.JSONDecodeError as e:
                                            print(f"[command] JSON parse error: {e}", flush=True)
                                        except Exception as e:
                                            print(f"[command] response error: {e}", flush=True)
                        except socket.timeout:
                            pass

                        # Check if we should enable polling (no push detected within 10s)
                        if not self.push_active and (now - push_detection_start) > 10:
                            self.push_active = False  # Explicitly disable push expectation
                            if not hasattr(self, '_poll_enabled'):
                                print("COMMAND: TICK_DATA polling active (≈ 5Hz)", flush=True)
                                self._poll_enabled = True

                        # TICK_DATA polling (if push not active)
                        if not self.push_active and (now - self.last_poll_time) > 0.2:  # 5Hz total
                            # Send 3-5 symbols per batch
                            batch_size = min(5, len(self.symbols) - self.symbol_index)
                            for i in range(batch_size):
                                sym = self.symbols[self.symbol_index]
                                req_key = f"TICK_DATA_{sym}"
                                self.pending_requests.add(req_key)
                                self.jsend(s, {"MSG":"TICK_DATA","SYMBOL":sym})
                                self.symbol_index = (self.symbol_index + 1) % len(self.symbols)
                            self.last_poll_time = now

                        # Account status polling
                        if (now - self.last_account_poll) > 3:
                            self.jsend(s, {"MSG":"ACCOUNT_STATUS"})
                            self.last_account_poll = now

                        # Keepalive
                        if (now - self.last_keepalive) > 15:
                            self.jsend(s, {"MSG":"CONNECTION_STATUS"})
                            self.last_keepalive = now

                        time.sleep(0.05)  # Small sleep to prevent busy loop

            except Exception as e:
                delay = self.backoff_delays[min(self.backoff_index, len(self.backoff_delays)-1)]
                jitter = delay * 0.1 * random.random()
                total_delay = delay + jitter
                print(f"[command] reconnect in {total_delay:.1f}s due to: {e}", flush=True)
                self.backoff_index = min(self.backoff_index + 1, len(self.backoff_delays)-1)
                time.sleep(total_delay)
            else:
                self.backoff_index = 0  # Reset on success

    def _process_command_response(self, response: dict):
        """Process MetaSocket command response and normalize to v1"""
        try:
            msg_type = response.get('MSG', '')

            if msg_type in ['TICK_DATA', 'QUOTE']:
                # Normalize price response to v1 tick
                symbol = response.get('SYMBOL', '')
                if not symbol:
                    return

                # Get price data defensively
                bid = response.get('BID', response.get('LAST', 0))
                ask = response.get('ASK', response.get('LAST', 0))

                # If only one price available, use it for both
                if not bid and ask:
                    bid = ask
                elif not ask and bid:
                    ask = bid

                try:
                    bid = float(bid) if bid else 0.0
                    ask = float(ask) if ask else 0.0
                    mid = (bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0
                except (ValueError, TypeError):
                    return

                # Get timestamp
                ts_raw = response.get('TIME', time.time())
                try:
                    ts_epoch_ms = int(float(ts_raw) * 1000) if isinstance(ts_raw, (int, float)) else int(time.time() * 1000)
                except:
                    ts_epoch_ms = int(time.time() * 1000)

                tick_event = {
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "ts_epoch_ms": ts_epoch_ms,
                    "src": "metasocket"
                }

                self.publish(tick_event)

                # Update metrics
                self.tick_counts[symbol] += 1
                self.last_tick_times[symbol] = time.time()

            elif msg_type == 'ACCOUNT_STATUS':
                # Normalize account status to v1
                account_event = {
                    "balance": float(response.get('BALANCE', response.get('Balance', 0.0))),
                    "equity": float(response.get('EQUITY', response.get('Equity', 0.0))),
                    "margin": float(response.get('MARGIN', response.get('Margin', 0.0))),
                    "free_margin": float(response.get('FREE_MARGIN', response.get('FreeMargin', 0.0))),
                    "leverage": int(response.get('LEVERAGE', response.get('Leverage', 500))),
                    "currency": str(response.get('CURRENCY', response.get('Currency', ''))),
                    "ts_epoch_ms": int(time.time() * 1000),
                    "src": "metasocket"
                }

                self.publish(account_event)

            elif msg_type == 'PRICE_HISTORY':
                # Process price history backfill
                symbol = response.get('SYMBOL', '')
                rates = response.get('RATES', [])

                if symbol and rates:
                    bars_loaded = 0
                    for rate in rates:
                        try:
                            # Parse timestamp: "YYYY.MM.DD HH:MM:SS" -> epoch ms
                            time_str = rate.get('TIME', '')
                            if time_str:
                                import datetime
                                dt = datetime.datetime.strptime(time_str, '%Y.%m.%d %H:%M:%S')
                                ts_open_ms = int(dt.timestamp() * 1000)
                            else:
                                continue

                            ohlc_bar = {
                                'ts_open_ms': ts_open_ms,
                                'open': float(rate.get('OPEN', 0)),
                                'high': float(rate.get('HIGH', 0)),
                                'low': float(rate.get('LOW', 0)),
                                'close': float(rate.get('CLOSE', 0)),
                                'volume': float(rate.get('TICK_VOLUME', rate.get('REAL_VOLUME', 0)))
                            }

                            self.ohlc_store[symbol].append(ohlc_bar)
                            bars_loaded += 1

                        except Exception:
                            continue

                    # Keep only latest 500 bars per symbol
                    if len(self.ohlc_store[symbol]) > 500:
                        self.ohlc_store[symbol] = self.ohlc_store[symbol][-500:]

                    self.backfill_completed.add(symbol)
                    print(f"BACKFILL: {symbol} M1 bars loaded={bars_loaded}", flush=True)

            elif msg_type.startswith('ORDER_') or 'TRADE' in msg_type:
                # Normalize trade/position events to v1
                ticket = response.get('TICKET', response.get('ORDER', ''))
                if ticket:
                    # Determine side
                    type_str = str(response.get('TYPE', '')).upper()
                    side = "BUY" if "BUY" in type_str else "SELL" if "SELL" in type_str else None

                    # Determine state and reason
                    state = "OPEN"
                    reason = "other"
                    if response.get('CLOSE_TIME') or response.get('STATE') == 'CLOSED':
                        state = "CLOSE"
                        if 'SL' in str(response.get('REASON', '')):
                            reason = "sl"
                        elif 'TP' in str(response.get('REASON', '')):
                            reason = "tp"
                        else:
                            reason = "manual"

                    position_event = {
                        "ticket": str(ticket),
                        "symbol": response.get('SYMBOL', ''),
                        "side": side,
                        "state": state,
                        "reason": reason,
                        "price": float(response.get('PRICE', response.get('OPEN_PRICE', response.get('CLOSE_PRICE', 0)))),
                        "volume": float(response.get('VOLUME', 0)),
                        "sl": float(response.get('SL')) if 'SL' in response else None,
                        "tp": float(response.get('TP')) if 'TP' in response else None,
                        "ts_epoch_ms": int((response.get('TIME', response.get('CLOSE_TIME', time.time())) or time.time()) * 1000),
                        "src": "metasocket"
                    }

                    self.publish(position_event)

        except Exception as e:
            # Skip errors, keep processing
            pass

    def get_ohlc_snapshot(self, symbol: str, n: int = 100) -> list:
        """Get last N OHLC bars for symbol plus latest price info"""
        bars = self.ohlc_store.get(symbol, [])
        return bars[-n:] if bars else []


    def _metrics_logger(self):
        """Log tick rates and event age every 5s"""
        while self.running:
            try:
                time.sleep(5)
                now = time.time()

                if now - self.last_metrics_log > 5:
                    # Log command client activity
                    if hasattr(self, 'tick_counts') and self.tick_counts:
                        total_ticks = sum(self.tick_counts.values())
                        if total_ticks > 0:
                            print(f"[command] total_ticks={total_ticks} symbols_active={len(self.tick_counts)}", flush=True)

                    # Calculate tick rates (EWMA 60s approximation)
                    rates = []
                    oldest_age = 0

                    for symbol in self.symbols:
                        count = self.tick_counts.get(symbol, 0)
                        last_time = self.last_tick_times.get(symbol, 0)

                        if last_time > 0:
                            age = now - last_time
                            oldest_age = max(oldest_age, age)

                            # Rough ticks/sec (reset counter each log)
                            rate = count / 5.0 if count > 0 else 0.0
                            if rate > 0:
                                rates.append(f"{symbol}:{rate:.1f}")

                    # Reset counters
                    self.tick_counts.clear()

                    rate_summary = ",".join(rates[:5])  # Show top 5
                    if rates:
                        print(f"[metrics] ticks/sec: {rate_summary} | oldest_age: {oldest_age:.1f}s", flush=True)

                    self.last_metrics_log = now

            except Exception as e:
                pass


    def fire_order(self, signal_id: str, symbol: str, direction: str, volume: float,
                  sl_pips: float = 0, tp_pips: float = 0, idempotency_key: str = None) -> dict:
        """WRITER: fire → ORDER_SEND with idempotency"""

        # Idempotency check
        if idempotency_key:
            if idempotency_key in self.fire_cache:
                logger.info(f"🔄 Duplicate fire blocked: {idempotency_key}")
                return {"success": False, "error": "Duplicate request", "idempotency_key": idempotency_key}

            # Cache for 24h
            self.fire_cache[idempotency_key] = time.time()

        if self.circuit_open:
            return {"success": False, "error": "Circuit breaker open"}

        try:
            sock = self._get_cmd_connection()
            if not sock:
                return {"success": False, "error": "Connection failed"}

            start_time = time.time()

            # ORDER_SEND command
            order_cmd = {
                "action": "ORDER_SEND",
                "symbol": symbol,
                "type": "ORDER_TYPE_BUY" if direction.upper() == "BUY" else "ORDER_TYPE_SELL",
                "volume": volume,
                "sl": sl_pips,
                "tp": tp_pips,
                "comment": "MSKT",
                "magic": 900001,
                "idempotency_key": idempotency_key or signal_id
            }

            cmd_json = json.dumps(order_cmd) + '\n'
            sock.send(cmd_json.encode())

            # Get response
            response = sock.recv(4096).decode().strip()
            result = json.loads(response) if response else {}

            # Record latency
            latency_ms = (time.time() - start_time) * 1000
            self.order_latencies.append(latency_ms)

            logger.info(f"🔫 ORDER_SEND: {symbol} {direction} {volume} → {result.get('ticket', 'FAILED')}")

            return {
                "success": result.get('retcode', -1) == 0,
                "ticket": result.get('ticket'),
                "latency_ms": latency_ms,
                "idempotency_key": idempotency_key
            }

        except Exception as e:
            self._handle_error(f"Fire order failed: {e}")
            return {"success": False, "error": str(e)}

    def close_ticket(self, ticket: int) -> dict:
        """WRITER: close_ticket → ORDER_CLOSE"""
        if self.circuit_open:
            return {"success": False, "error": "Circuit breaker open"}

        try:
            sock = self._get_cmd_connection()
            if not sock:
                return {"success": False, "error": "Connection failed"}

            close_cmd = {
                "action": "ORDER_CLOSE",
                "ticket": ticket,
                "comment": "MSKT",
                "magic": 900001
            }

            cmd_json = json.dumps(close_cmd) + '\n'
            sock.send(cmd_json.encode())

            response = sock.recv(4096).decode().strip()
            result = json.loads(response) if response else {}

            return {
                "success": result.get('retcode', -1) == 0,
                "ticket": ticket
            }

        except Exception as e:
            self._handle_error(f"Close ticket failed: {e}")
            return {"success": False, "error": str(e)}

    def get_health_status(self) -> dict:
        """Get adapter health metrics"""
        now = time.time()
        last_event_age_ms = int((now - self.last_event_time) * 1000)

        # Calculate p95 latencies
        event_lag_p95 = 0
        order_latency_p95 = 0

        if self.event_lag_samples:
            sorted_lags = sorted(self.event_lag_samples)
            event_lag_p95 = int(sorted_lags[int(len(sorted_lags) * 0.95)])

        if self.order_latencies:
            sorted_latencies = sorted(self.order_latencies)
            order_latency_p95 = int(sorted_latencies[int(len(sorted_latencies) * 0.95)])

        # Determine status
        status = "ok"
        if self.circuit_open:
            status = "paused"
        elif last_event_age_ms > 10000:  # 10s without events
            status = "degraded"

        return {
            "status": status,
            "source": "metasocket",
            "last_event_age_ms": last_event_age_ms,
            "event_lag_ms_p95": event_lag_p95,
            "order_latency_ms_p95": order_latency_p95,
            "circuit_open": self.circuit_open,
            "error_count": self.error_count
        }


# Global instance
adapter_instance = None

def get_adapter() -> MetaSocketAdapter:
    """Get singleton adapter instance"""
    global adapter_instance
    if not adapter_instance:
        adapter_instance = MetaSocketAdapter()
    return adapter_instance

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    adapter = MetaSocketAdapter()
    try:
        adapter.start()
        logger.info("🔥 MetaSocket adapter running")

        # Keep alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down adapter")
        adapter.stop()