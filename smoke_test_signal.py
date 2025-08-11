#!/usr/bin/env python3
import zmq, json, time

ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://127.0.0.1:5998")  # Bind to test port
time.sleep(0.5)

s = {
    "signal_id": "HUD_TEST_" + str(int(time.time())),
    "symbol": "XAUUSD",
    "direction": "BUY",
    "side": "BUY",
    "entry_price": 2417.2,
    "entry": 2417.2,
    "stop_loss": 2409.5,
    "sl": 2409.5,
    "take_profit": 2431.0,
    "tp": 2431.0,
    "risk_reward": "1:1.8",
    "rr": "1:1.8",
    "confidence": 86,
    "tcs": 86,
    "pattern_type": "LIQUIDITY_SWEEP",
    "signal_type": "PRECISION_STRIKE",
    "citadel_score": 8.6,
    "expires_at": "2030-01-01T00:00:00Z"
}

# Send as Elite Guard format
msg = f"ELITE_GUARD_SIGNAL {json.dumps(s)}"
pub.send_string(msg)
print(f"✅ Sent test signal: {s['signal_id']}")

# Also connect to relay port and send
pub2 = ctx.socket(zmq.PUB)
pub2.connect("tcp://127.0.0.1:5557")
time.sleep(0.5)
pub2.send_string(msg)
print("✅ Also sent to relay port 5557")

time.sleep(1)
pub.close()
pub2.close()
ctx.term()