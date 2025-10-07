#!/usr/bin/env python3
"""
ZMQ Telemetry Bridge with Debug Logging
Receives telemetry on port 5556 and republishes on port 5560
Stores heartbeat data in database for position sizing
Publishes EA status to event bus for real-time monitoring
"""

import zmq
import json
import logging
import time
import sqlite3
from time import monotonic
from src.bitten_core.tiered_exit_integration import drive_exits_for_active_positions

# Event Bus integration
try:
    from event_bus.producer import EventProducer
    event_producer = EventProducer()
    EVENT_BUS_AVAILABLE = True
    logger_init = logging.getLogger('TelemetryBridge')
    logger_init.info("✅ Event Bus available for EA status publishing")
except ImportError:
    event_producer = None
    EVENT_BUS_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryBridge')

DB_PATH = "/root/HydraX-v2/bitten.db"

def update_ea_heartbeat(heartbeat_data):
    """Update EA instance with heartbeat data"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        uuid = heartbeat_data.get('uuid')
        balance = heartbeat_data.get('balance', 0.0)
        equity = heartbeat_data.get('equity', 0.0)
        positions = heartbeat_data.get('positions', 0)
        # ALWAYS use server time for last_seen (EA timestamp may be wrong timezone/clock)
        timestamp = int(time.time())  # Server receive time is source of truth

        # Update or insert EA instance with heartbeat data
        cursor.execute("""
            INSERT INTO ea_instances
            (target_uuid, last_balance, last_equity, last_seen, updated_at, open_positions)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(target_uuid) DO UPDATE SET
                last_balance = excluded.last_balance,
                last_equity = excluded.last_equity,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at,
                open_positions = excluded.open_positions
        """, (uuid, balance, equity, timestamp, timestamp, positions))

        conn.commit()
        conn.close()

        # Publish EA status to event bus for real-time monitoring
        if EVENT_BUS_AVAILABLE and event_producer:
            try:
                ea_status = {
                    'target_uuid': uuid,
                    'balance': balance,
                    'equity': equity,
                    'open_positions': positions,
                    'connected': True,
                    'last_seen': timestamp,
                    'timestamp': timestamp
                }
                event_producer.publish('ea.status.heartbeat', ea_status)
            except Exception as pub_error:
                logger.debug(f"Failed to publish EA status to event bus: {pub_error}")

        return True
    except Exception as e:
        logger.error(f"Failed to update EA heartbeat in database: {e}")
        return False

def main():
    context = zmq.Context()

    # PULL socket - receives telemetry from EA
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5556")
    logger.info("✅ Bound to port 5556 (PULL from EA)")

    # PUB socket - publishes to Elite Guard
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5560")
    logger.info("✅ Bound to port 5560 (PUB to subscribers)")

    # IPC PUB mirror - for tick monitoring/debugging
    mirror = context.socket(zmq.PUB)
    mirror.bind("ipc:///tmp/tick_mirror")
    logger.info("🔍 Bound IPC mirror: ipc:///tmp/tick_mirror")
    
    logger.info("📡 Bridging telemetry...")
    
    message_count = 0
    tick_count = 0
    ohlc_count = 0
    heartbeat_count = 0
    
    # Hook B: Track quotes and drive exit FSM
    quotes = {}  # symbol -> {"bid": x, "ask": y}
    last_drive_ts = 0.0
    DRIVE_MIN_GAP = 0.10  # 100ms debounce
    symbols_we_manage = {"USDJPY"}  # Canary symbol for testing
    
    while True:
        try:
            # Receive message
            message = receiver.recv_string()
            message_count += 1

            # Check for OHLC messages first
            if message.startswith("OHLC "):
                ohlc_count += 1
                # OHLC message format: "OHLC {json}"
                publisher.send_string(message)  # Republish as-is for Elite Guard
                mirror.send_string(message)  # Mirror to IPC
                
                # Log OHLC messages
                if message_count % 100 == 1:  # Log every 100th OHLC
                    try:
                        ohlc_data = json.loads(message[5:])
                        logger.info(f"📊 OHLC: {ohlc_data.get('symbol')} {ohlc_data.get('timeframe')}")
                    except:
                        pass
                        
            elif message.startswith("HEARTBEAT"):
                heartbeat_count += 1
                # Republish heartbeat
                publisher.send_string(message)
                mirror.send_string(message)  # Mirror to IPC
                if message_count % 30 == 0:
                    logger.info(f"💓 Heartbeat #{message_count} | Ticks: {tick_count}, OHLC: {ohlc_count}, HB: {heartbeat_count}")
                    
            else:
                # Try to parse as JSON (tick data or heartbeat)
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')

                    # Handle heartbeat messages
                    if msg_type == 'heartbeat':
                        heartbeat_count += 1

                        # Update database with heartbeat data
                        if update_ea_heartbeat(data):
                            # Log every 5th heartbeat
                            if heartbeat_count % 5 == 0:
                                uuid = data.get('uuid', 'UNKNOWN')
                                balance = data.get('balance', 0.0)
                                equity = data.get('equity', 0.0)
                                positions = data.get('positions', 0)
                                logger.info(
                                    f"💓 Heartbeat #{heartbeat_count} | "
                                    f"{uuid} | Bal: ${balance:.2f} | "
                                    f"Eq: ${equity:.2f} | Pos: {positions}"
                                )

                        # Republish heartbeat
                        publisher.send_json(data)
                        mirror.send_string(message)
                        continue

                    # Log first 5 messages in detail
                    if message_count <= 5:
                        logger.info(f"📊 Message {message_count}:")
                        logger.info(f"   Type: {msg_type}")
                        logger.info(f"   Keys: {list(data.keys())}")
                        if 'symbol' in data:
                            logger.info(f"   Symbol: {data['symbol']}")
                        if 'bid' in data and 'ask' in data:
                            logger.info(f"   Tick: {data['bid']}/{data['ask']}")

                    # Hook B: Accumulate quotes for exit FSM
                    if 'symbol' in data and 'bid' in data and 'ask' in data:
                        symbol = data['symbol']
                        quotes[symbol] = {
                            "bid": float(data['bid']),
                            "ask": float(data['ask'])
                        }
                        
                        # Drive exits if it's time and we have the canary symbol
                        now = monotonic()
                        if now - last_drive_ts >= DRIVE_MIN_GAP:
                            # Filter for managed symbols only
                            snapshot = {s: quotes[s] for s in quotes.keys() & symbols_we_manage
                                      if "bid" in quotes[s] and "ask" in quotes[s]}
                            
                            if snapshot:
                                # 🔥 Hook B: Drive the exit FSM
                                try:
                                    drive_exits_for_active_positions(snapshot)
                                    if message_count % 100 == 0:  # Log periodically
                                        logger.info(f"🎯 Hook B: Driving exits for {list(snapshot.keys())}")
                                except Exception as e:
                                    logger.error(f"Hook B error: {e}")
                                
                                last_drive_ts = now
                    
                    tick_count += 1
                    # Republish as JSON
                    publisher.send_json(data)
                    # Mirror to IPC as original string
                    mirror.send_string(message)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON message {message_count}: {message[:100]}...")
                    # Still republish as string
                    publisher.send_string(message)
                    mirror.send_string(message)  # Mirror non-JSON messages too
                
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()