#!/usr/bin/env python3
"""
Direct fire sender to Redis for BITTEN system
Sends complete fire packets with all trade parameters to EA
"""

import redis
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_fire_to_ea(signal_id, symbol, direction, entry, sl, tp, lot=0.01, user_id="7176191872", target_uuid="COMMANDER_DEV_001"):
    """Send complete fire packet directly to Redis for EA execution"""
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Build complete fire packet with ALL parameters
    fire_packet = {
        "type": "fire",
        "fire_id": f"DIRECT_{signal_id}_{int(time.time())}",
        "signal_id": signal_id,
        "symbol": symbol,
        "direction": direction.upper(),
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "lot": float(lot),
        "user_id": str(user_id),
        "target_uuid": target_uuid,
        "timestamp": time.time()
    }
    
    # Add to Redis stream for EA
    stream_key = f"fire.{target_uuid}"
    msg_id = r.xadd(stream_key, {
        "event": json.dumps(fire_packet),
        "fire_id": fire_packet["fire_id"],
        "symbol": symbol,
        "user_id": user_id,
        "target_uuid": target_uuid,
        "idem": f"direct:{user_id}:{int(time.time())}"
    })
    
    logger.info(f"✅ Fire packet sent to Redis: {fire_packet['fire_id']}")
    logger.info(f"   Symbol: {symbol} {direction} @ {entry}")
    logger.info(f"   SL: {sl} | TP: {tp} | Lot: {lot}")
    logger.info(f"   Redis ID: {msg_id}")
    
    return fire_packet

if __name__ == "__main__":
    # Test with last GBPUSD signal
    send_fire_to_ea(
        signal_id="ELITE_GUARD_GBPUSD_1755107616",
        symbol="GBPUSD",
        direction="BUY",
        entry=1.35694,
        sl=1.35634,
        tp=1.35784,
        lot=0.01
    )