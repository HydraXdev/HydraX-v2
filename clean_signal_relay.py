#!/usr/bin/env python3
"""
Clean Signal Relay - NO MODIFICATIONS
Direct pass-through from generator_merger (5564) to API server
STORM-FREE - Preserves original generator R:R ratios
"""

import zmq
import requests
import json
import time
import signal as signal_handler
import sys

# Configuration
ZMQ_PORT = 5564  # generator_merger output
API_URL = "http://127.0.0.1:8888/api/signals"
RELAY_NAME = "CLEAN_RELAY"

def signal_exit_handler(signum, frame):
    print(f"\n🛑 {RELAY_NAME}: Shutting down...")
    sys.exit(0)

signal_handler.signal(signal_handler.SIGINT, signal_exit_handler)
signal_handler.signal(signal_handler.SIGTERM, signal_exit_handler)

def main():
    print(f"🚀 {RELAY_NAME}: Starting CLEAN signal relay")
    print(f"📡 Subscribing to ZMQ port {ZMQ_PORT} (generator_merger)")
    print(f"🎯 Posting to API: {API_URL}")
    print(f"✅ STORM-FREE: Preserving original R:R ratios")
    print("=" * 80)
    
    # Setup ZMQ subscriber
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f"tcp://127.0.0.1:{ZMQ_PORT}")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    
    signal_count = 0
    
    while True:
        try:
            # Receive signal
            message = subscriber.recv_string()

            # Debug: Show what we received
            if len(message) > 0:
                print(f"🔍 RAW MESSAGE: {message[:100]}")

            # Strip prefix if present (generators send "PREFIX {json}")
            # Examples: "ELITE_GUARD_SIGNAL {json}", "ELITE_RAPID_GBPUSD_xxx {json}"
            if ' ' in message:
                message = message.split(' ', 1)[1]
                print(f"🔍 AFTER STRIP: {message[:100]}")

            signal_data = json.loads(message)
            
            signal_id = signal_data.get('signal_id', 'UNKNOWN')
            symbol = signal_data.get('symbol', 'UNKNOWN')
            confidence = signal_data.get('confidence', 0)
            
            # Extract original R:R data
            sl_pips = signal_data.get('stop_pips', 0)
            tp_pips = signal_data.get('target_pips', 0)
            rr_ratio = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
            
            signal_count += 1
            
            print(f"\n📨 Signal #{signal_count}: {signal_id}")
            print(f"   Symbol: {symbol} | Confidence: {confidence}%")
            print(f"   SL: {sl_pips:.1f}p | TP: {tp_pips:.1f}p | R:R: 1:{rr_ratio}")
            
            # Post to API WITHOUT MODIFICATIONS
            response = requests.post(
                API_URL,
                json=signal_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   ✅ Posted to API (UNMODIFIED)")
            else:
                print(f"   ❌ API error: {response.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except requests.RequestException as e:
            print(f"❌ API request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
