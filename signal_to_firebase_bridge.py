#!/usr/bin/env python3
"""
Signal to Firebase Bridge
Listens to ZMQ port 5557 for Elite Guard signals and writes them to Firebase Firestore
"""
import zmq
import json
import time
import signal
import sys
import os
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize Firebase
db = firestore.Client(project="bitten-0420")

print("🔥 Signal to Firebase Bridge Started")
print("=" * 60)
print("Project: bitten-0420")
print("Firestore: Connected")
print("Listening: ZMQ port 5557")
print("=" * 60)

# ZMQ setup
context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5557")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
print("✅ Subscribed to ZMQ port 5557")

# Graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutdown signal received, closing...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_historical_candles(symbol, timeframe='M30', count=12):
    """
    Load recent candles from candle_cache.json for chart display.

    Args:
        symbol: Trading pair (e.g., 'EURUSD', 'GBPJPY')
        timeframe: Candle timeframe (M1, M5, M15, M30)
        count: Number of candles to retrieve (default 12 for ~6 hours of M30)

    Returns:
        List of candle dictionaries with time, open, high, low, close, volume
    """
    try:
        cache_path = '/root/HydraX-v2/candle_cache.json'

        if not os.path.exists(cache_path):
            print(f"⚠️  Candle cache not found at {cache_path}")
            return []

        with open(cache_path, 'r') as f:
            cache = json.load(f)

        # Map timeframe to cache key
        timeframe_map = {
            'M1': 'm1_data',
            'M5': 'm5_data',
            'M15': 'm15_data',
            'M30': 'm30_data'
        }

        cache_key = timeframe_map.get(timeframe.upper())
        if not cache_key:
            print(f"⚠️  Unknown timeframe: {timeframe}")
            return []

        # Get candles for this symbol and timeframe
        if cache_key not in cache:
            print(f"⚠️  No {timeframe} data in cache")
            return []

        symbol_data = cache[cache_key].get(symbol, [])

        if not symbol_data:
            print(f"⚠️  No candles found for {symbol} in {timeframe}")
            return []

        # Get last N candles and format for Lightweight Charts
        recent_candles = symbol_data[-count:] if len(symbol_data) > count else symbol_data

        # Format candles for frontend (Lightweight Charts expects 'time' not 'timestamp')
        formatted_candles = []
        for candle in recent_candles:
            formatted_candles.append({
                'time': candle.get('timestamp', 0),
                'open': float(candle.get('open', 0)),
                'high': float(candle.get('high', 0)),
                'low': float(candle.get('low', 0)),
                'close': float(candle.get('close', 0)),
                'volume': int(candle.get('volume', 0))
            })

        print(f"✅ Loaded {len(formatted_candles)} {timeframe} candles for {symbol}")
        return formatted_candles

    except Exception as e:
        print(f"❌ Error loading candles: {e}")
        return []

def write_to_firestore(signal_data):
    """Write signal to Firebase Firestore /signals collection"""
    try:
        signal_id = signal_data.get('signal_id')
        if not signal_id:
            print("⚠️  No signal_id in data")
            return False

        # Build Firestore document matching schema from FIREBASE_HANDOVER.md
        doc = {
            # Core fields
            'pattern': signal_data.get('pattern_type', signal_data.get('pattern', '')),
            'pair': signal_data.get('symbol', ''),
            'timeframe': signal_data.get('timeframe', 'M15'),
            'session': signal_data.get('session', 'LONDON'),
            'timestamp': firestore.SERVER_TIMESTAMP,
            'confidence': float(signal_data.get('confidence', 0)),

            # Trade levels
            'entry': float(signal_data.get('entry_price', signal_data.get('entry', 0))),
            'tp': float(signal_data.get('take_profit', signal_data.get('tp', 0))),
            'sl': float(signal_data.get('stop_loss', signal_data.get('sl', 0))),

            # Metadata
            'status': 'new',
            'priority': 'high' if signal_data.get('confidence', 0) >= 85 else 'medium',
            'direction': signal_data.get('direction', ''),
            'signal_mode': 'SNIPER' if signal_data.get('confidence', 0) >= 85 else 'RAPID',
        }

        # Add historical candles for chart display
        symbol = signal_data.get('symbol', '')
        timeframe = signal_data.get('timeframe', 'M30')
        if symbol:
            candles = load_historical_candles(symbol, timeframe, count=12)
            if candles:
                doc['historical_candles'] = candles
                print(f"   📊 Added {len(candles)} {timeframe} candles to signal")

        # Remove empty values
        doc = {k: v for k, v in doc.items() if v not in [None, '', 0]}

        # Write to Firestore (use signal_id as document ID)
        db.collection('signals').document(signal_id).set(doc)

        print(f"✅ Written to Firestore: {signal_id} ({doc.get('pair')} {doc.get('direction')} @ {doc.get('confidence')}%)")
        return True

    except Exception as e:
        print(f"❌ Firestore write failed: {e}")
        return False

# Main loop
signal_count = 0
print("\n🎯 Listening for signals...\n")

while running:
    try:
        # Receive message from ZMQ (non-blocking with timeout)
        if subscriber.poll(1000):  # 1 second timeout
            message = subscriber.recv_string()

            # Parse Elite Guard signal format: "ELITE_GUARD_SIGNAL {json}"
            if message.startswith("ELITE_GUARD_SIGNAL "):
                json_str = message.replace("ELITE_GUARD_SIGNAL ", "", 1)
                signal_data = json.loads(json_str)

                # Write to Firebase
                if write_to_firestore(signal_data):
                    signal_count += 1

                    if signal_count % 10 == 0:
                        print(f"\n📊 Processed {signal_count} signals\n")
            else:
                # Handle other message formats
                try:
                    signal_data = json.loads(message)
                    if write_to_firestore(signal_data):
                        signal_count += 1
                except json.JSONDecodeError:
                    pass  # Ignore non-JSON messages

    except zmq.ZMQError as e:
        if e.errno == zmq.EAGAIN:
            continue  # Timeout, no message available
        else:
            print(f"❌ ZMQ Error: {e}")
            break
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        time.sleep(1)  # Prevent tight error loop

# Cleanup
print(f"\n✅ Shutting down... (processed {signal_count} signals)")
subscriber.close()
context.term()
print("👋 Signal to Firebase Bridge stopped")
