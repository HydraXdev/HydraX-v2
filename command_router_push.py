#!/usr/bin/env python3
"""
Simple PUSH-based command router matching original working architecture
Port 5555: PUSH socket for commands (EA PULL connects)
Port 5556: PULL socket for market data (EA PUSH sends)
"""
import os, json, time, zmq, logging, threading
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
LOG = logging.getLogger("CMD")

PUSH_BIND = "tcp://*:5555"  # Commands to EA
PULL_BIND = "tcp://*:5556"  # Market data from EA
QUEUE_PULL = "ipc:///tmp/bitten_cmdqueue"  # Commands from webapp
HEARTBEAT_SEC = 120

ctx = zmq.Context.instance()

# Sockets
push = ctx.socket(zmq.PUSH)
push.bind(PUSH_BIND)
LOG.info(f"[CMD] PUSH bound {PUSH_BIND}")

pull = ctx.socket(zmq.PULL)
pull.bind(PULL_BIND)
LOG.info(f"[CMD] PULL bound {PULL_BIND}")

queue = ctx.socket(zmq.PULL)
queue.bind(QUEUE_PULL)
LOG.info(f"[CMD] Queue bound {QUEUE_PULL}")

# EA registry
ea_last_seen = {}

def recv_market_data_forever():
    """Receive market data and heartbeats from EA on 5556"""
    while True:
        try:
            msg = pull.recv_json()
            typ = (msg.get("type") or "").upper()
            uuid = msg.get("target_uuid") or msg.get("uuid") or "UNKNOWN"
            
            if typ in ("HELLO", "HEARTBEAT", "PING"):
                ea_last_seen[uuid] = time.time()
                LOG.info(f"[EA] {typ} {uuid}")
            elif typ == "TICK":
                # Just track that EA is alive
                ea_last_seen[uuid] = time.time()
        except Exception as e:
            LOG.warning(f"Market data recv error: {e}")

def queue_to_push_forever():
    """Forward commands from IPC queue to EA via PUSH"""
    while True:
        cmd = queue.recv_json()
        fire_id = cmd.get("fire_id")
        LOG.info(f"[CMD] DEQ {fire_id} | {cmd.get('type')} | {cmd.get('symbol')}")
        
        uuid = cmd.get("target_uuid")
        if not uuid:
            LOG.warning(f"DROP cmd without target_uuid: {cmd}")
            continue

        # TTL check
        last = ea_last_seen.get(uuid, 0)
        if last == 0 or (time.time() - last) > HEARTBEAT_SEC:
            LOG.warning(f"[CMD] ❌ EA {uuid} not fresh (ttl {HEARTBEAT_SEC}s). Rejecting {fire_id}")
            continue

        # PUSH socket - just send the JSON
        push.send_json(cmd)
        LOG.info(f"[CMD] → {uuid} | {fire_id} | {cmd.get('type')} | {cmd.get('symbol')}")

def main():
    t1 = threading.Thread(target=recv_market_data_forever, daemon=True)
    t2 = threading.Thread(target=queue_to_push_forever, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()