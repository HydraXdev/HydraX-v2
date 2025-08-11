#!/usr/bin/env python3
"""Send signal directly like Elite Guard does"""

import zmq
import json
import time
from datetime import datetime, timezone, timedelta

# Connect as publisher like Elite Guard
ctx = zmq.Context()
sock = ctx.socket(zmq.PUB)
sock.bind("tcp://127.0.0.1:5998")
time.sleep(1)  # Let subscribers connect

# Create realistic signal
signal = {
    "signal_id": f"ELITE_GUARD_EURUSD_{int(time.time())}",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.08500,
    "stop_loss": 1.08300,
    "take_profit": 1.08900,
    "confidence": 85,
    "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
    "signal_type": "PRECISION_STRIKE",
    "citadel_score": 8.5,
    "risk_reward": "1:2",
    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2, minutes=5)).isoformat()
}

# Send as Elite Guard format
message = f"ELITE_GUARD_SIGNAL {json.dumps(signal)}"
sock.send_string(message)
print(f"✅ Sent signal: {signal['signal_id']}")
print("Check Telegram group for button...")

sock.close()
ctx.term()