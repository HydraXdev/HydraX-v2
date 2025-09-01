#!/usr/bin/env python3
"""
ZMQ Telemetry Bridge with Debug Logging
Receives telemetry on port 5556 and republishes on port 5560
"""

import zmq
import json
import logging
import time
from time import monotonic
from src.bitten_core.tiered_exit_integration import drive_exits_for_active_positions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryBridge')

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
    
    logger.info("📡 Bridging telemetry...")
    
    message_count = 0
    
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
                # OHLC message format: "OHLC {json}"
                publisher.send_string(message)  # Republish as-is for Elite Guard
                
                # Log OHLC messages
                if message_count % 100 == 1:  # Log every 100th OHLC
                    try:
                        ohlc_data = json.loads(message[5:])
                        logger.info(f"📊 OHLC: {ohlc_data.get('symbol')} {ohlc_data.get('timeframe')}")
                    except:
                        pass
                        
            elif message.startswith("HEARTBEAT"):
                # Republish heartbeat
                publisher.send_string(message)
                if message_count % 30 == 0:
                    logger.info(f"💓 Heartbeat #{message_count}")
                    
            else:
                # Try to parse as JSON (tick data)
                try:
                    data = json.loads(message)
                    
                    # Log first 5 messages in detail
                    if message_count <= 5:
                        logger.info(f"📊 Message {message_count}:")
                        logger.info(f"   Type: {data.get('type', 'unknown')}")
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
                    
                    # Republish as JSON
                    publisher.send_json(data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON message {message_count}: {message[:100]}...")
                    # Still republish as string
                    publisher.send_string(message)
                
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()