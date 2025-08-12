#!/usr/bin/env python3
import os, json, time, zmq, logging, threading
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
LOG = logging.getLogger("CMD")

ROUTER_BIND   = os.getenv("BITTEN_ROUTER_ADDR",   "tcp://*:5555")         # EA DEALER connects here
QUEUE_PULL    = os.getenv("BITTEN_QUEUE_ADDR",    "ipc:///tmp/bitten_cmdqueue")  # webapp PUSHes here
HEARTBEAT_SEC = int(os.getenv("BITTEN_EA_TTL_SEC","120"))

ctx = zmq.Context.instance()
router = ctx.socket(zmq.ROUTER); router.bind(ROUTER_BIND)
pull   = ctx.socket(zmq.PULL);   pull.bind(QUEUE_PULL)

# EA registry: uuid -> last_seen
ea_last_seen = {}

def recv_router_forever():
    while True:
        # ROUTER frames: [identity, empty, payload]
        parts = router.recv_multipart()
        if len(parts) == 3:
            ident, empty, payload = parts
        elif len(parts) == 2:
            ident, payload = parts; empty = b""
        else:
            LOG.warning("ROUTER invalid frame parts=%d", len(parts)); continue

        try:
            msg = json.loads(payload.decode("utf-8", "ignore"))
        except Exception:
            LOG.warning("ROUTER non-json payload from %s", ident); continue

        # HELLO / HEARTBEAT from EA
        typ = (msg.get("type") or "").upper()
        uuid = msg.get("target_uuid") or msg.get("user_uuid") or msg.get("uuid") or ident.decode()
        if uuid:
            ea_last_seen[uuid] = time.time()

        if typ in ("HELLO","HEARTBEAT","PING"):
            LOG.info("[EA] %s %s", typ, uuid)
            # optional pong
            if typ=="PING":
                router.send_multipart([ident, b"", json.dumps({"type":"PONG"}).encode()])
        else:
            # EAs generally shouldn't send other types here; ignore
            pass

def queue_to_router_forever():
    while True:
        cmd = pull.recv_json()
        uuid = cmd.get("target_uuid")
        if not uuid:
            LOG.warning("DROP cmd without target_uuid: %s", cmd); continue

        # TTL check
        last = ea_last_seen.get(uuid, 0)
        if last == 0 or (time.time() - last) > HEARTBEAT_SEC:
            LOG.warning("[CMD] ❌ EA %s not fresh (ttl %ss). Rejecting %s", uuid, HEARTBEAT_SEC, cmd.get("fire_id"))
            continue

        payload = json.dumps(cmd).encode()
        router.send_multipart([uuid.encode(), b"", payload])
        LOG.info("[CMD] → %s | %s | %s | %s", uuid, cmd.get("fire_id"), cmd.get("type"), cmd.get("symbol"))

def main():
    LOG.info("[CMD] ROUTER bound %s", ROUTER_BIND)
    LOG.info("[CMD] Queue  bound %s", QUEUE_PULL)
    t1 = threading.Thread(target=recv_router_forever, daemon=True)
    t2 = threading.Thread(target=queue_to_router_forever, daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()

if __name__ == "__main__":
    main()