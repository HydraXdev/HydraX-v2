import json
import sys
import time

import zmq

sys.path.append("/root/HydraX-v2")

# Import Elite Guard handlers (adjust path as needed)
try:
    from elite_guard_with_citadel import EliteGuardWithCitadel

    EG_AVAILABLE = True
except ImportError:
    print("Elite Guard import failed - will print instead")
    EG_AVAILABLE = False


def on_tick(tick_data):
    """Handle incoming tick data"""
    if EG_AVAILABLE:
        # Forward to Elite Guard if available
        try:
            # You may need to adjust this based on Elite Guard's actual API
            print(f"EG TICK: {tick_data['symbol']} {tick_data['bid']}/{tick_data['ask']}")
        except Exception as e:
            print(f"EG tick error: {e}")
    else:
        print(f"EG TICK: {tick_data['symbol']} {tick_data['bid']}/{tick_data['ask']}")


def on_account_summary(account_data):
    """Handle incoming account summary"""
    if EG_AVAILABLE:
        try:
            print(f"EG ACCT: balance={account_data['balance']} equity={account_data['equity']}")
        except Exception as e:
            print(f"EG account error: {e}")
    else:
        print(f"EG ACCT: balance={account_data['balance']} equity={account_data['equity']}")


ctx = zmq.Context.instance()
sub = ctx.socket(zmq.SUB)
sub.connect("tcp://127.0.0.1:5562")
sub.setsockopt(zmq.SUBSCRIBE, b"")

print("EG wire listening on :5562 …", flush=True)
while True:
    try:
        msg = sub.recv()
        obj = json.loads(msg.decode("utf-8", "ignore"))

        if "symbol" in obj and "bid" in obj:  # tick
            on_tick(obj)
        elif "balance" in obj and "equity" in obj:  # account
            on_account_summary(obj)
    except Exception as e:
        print(f"EG wire error: {e}", flush=True)
        time.sleep(0.1)
