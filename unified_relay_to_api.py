#!/usr/bin/env python3
"""
Unified Generator Relay - Forwards all generator signals from merger to API
- Subscribes to tcp://127.0.0.1:5564 (generator_merger output)
- POSTs all signals to http://localhost:8888/api/signals
- Handles ELITE_GUARD_SIGNAL, PULSE_SIGNAL, and APEX_SIGNAL
"""

import json
import logging
import requests
import zmq
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("UnifiedRelay")

def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5564")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
    subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout
    
    webapp_url = "http://localhost:8888/api/signals"
    count = 0
    
    logger.info("🚀 Unified Generator Relay started")
    logger.info("📡 Listening on port 5564 (generator_merger output)")
    logger.info("🌐 Forwarding to: " + webapp_url)
    
    while True:
        try:
            message = subscriber.recv_string()
            
            # Parse message format: "PREFIX {json}"
            if " " not in message:
                continue
                
            prefix, signal_json = message.split(" ", 1)
            signal_data = json.loads(signal_json)
            
            count += 1
            generator = prefix.replace("_SIGNAL", "").replace("_", " ")
            
            logger.info(f"📨 [{count}] Received {generator}: {signal_data.get('signal_id', 'UNKNOWN')}")
            
            # Forward to API
            response = requests.post(webapp_url, json=signal_data, timeout=3)
            
            if response.status_code == 200:
                logger.info(f"✅ [{count}] Relayed {generator} signal successfully")
            else:
                logger.error(f"❌ [{count}] HTTP {response.status_code}: {response.text[:100]}")
                
        except zmq.Again:
            # Timeout - continue
            continue
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
