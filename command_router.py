#!/usr/bin/env python3
import os, json, time, zmq, logging, threading
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
LOG = logging.getLogger("CMD")

PUSH_BIND     = os.getenv("BITTEN_PUSH_ADDR",      "tcp://*:5555")         # EA PULL connects here
QUEUE_PULL    = os.getenv("BITTEN_QUEUE_ADDR",    "ipc:///tmp/bitten_cmdqueue")  # webapp PUSHes here
HEARTBEAT_SEC = int(os.getenv("BITTEN_EA_TTL_SEC","120"))

ctx = zmq.Context.instance()

# DB update functions
import sqlite3
def _ea_db():
    db=os.environ.get("BITTEN_DB","/root/HydraX-v2/bitten.db")
    conn=sqlite3.connect(db, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

_last_upd_cache = {}  # uuid -> ts

def _normalize(val):
    """Convert empty strings to None"""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def _upsert_ea_instance(payload):
    # Rate-limit to 1/sec per UUID
    uuid = str(payload.get("target_uuid","")).strip()
    if not uuid: 
        return
    now = int(time.time())
    ts = _last_upd_cache.get(uuid, 0)
    if now - ts < 1:
        return
    _last_upd_cache[uuid] = now

    # Normalize values - empty strings become None
    user_id       = _normalize(payload.get("user_id"))
    acct_login    = _normalize(payload.get("account_login") or payload.get("account"))
    broker        = _normalize(payload.get("broker"))
    currency      = _normalize(payload.get("currency") or payload.get("account_currency"))
    leverage      = int(payload.get("leverage", 0) or 0)
    balance       = float(payload.get("balance", payload.get("account_balance", 0)) or 0)
    equity        = float(payload.get("equity",  payload.get("account_equity",  0)) or 0)
    last_seen     = int(payload.get("ts", now) or now)
    created_at    = now
    updated_at    = now

    try:
        conn=_ea_db()
        cur=conn.cursor()
        
        # Create table if needed
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ea_instances (
            target_uuid     TEXT PRIMARY KEY,
            user_id         TEXT,
            account_login   TEXT,
            broker          TEXT,
            currency        TEXT,
            leverage        INTEGER,
            last_balance    REAL,
            last_equity     REAL,
            last_seen       INTEGER,
            created_at      INTEGER,
            updated_at      INTEGER
        );
        """)
        
        # UPSERT with user_id preservation using COALESCE
        cur.execute("""
            INSERT INTO ea_instances(
              target_uuid,user_id,account_login,broker,currency,leverage,
              last_balance,last_equity,last_seen,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(target_uuid) DO UPDATE SET
              user_id=COALESCE(excluded.user_id, ea_instances.user_id),
              account_login=COALESCE(excluded.account_login, ea_instances.account_login),
              broker=COALESCE(excluded.broker, ea_instances.broker),
              currency=COALESCE(excluded.currency, ea_instances.currency),
              leverage=COALESCE(excluded.leverage, ea_instances.leverage),
              last_balance=excluded.last_balance,
              last_equity=excluded.last_equity,
              last_seen=excluded.last_seen,
              updated_at=excluded.updated_at
        """,(uuid,user_id,acct_login,broker,currency,leverage,balance,equity,last_seen,created_at,updated_at))
        
        # Log if user_id changed
        if user_id is not None:
            cur.execute("SELECT user_id FROM ea_instances WHERE target_uuid=?", (uuid,))
            row = cur.fetchone()
            if row and row[0] != user_id:
                LOG.info(f"[CMD] EA {uuid} user_id changed: {row[0]} → {user_id}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        LOG.warning("DB update failed: %s", e)

def _insert_fire_record(cmd):
    """Insert fire command into database for tracking"""
    try:
        fire_id = cmd.get("fire_id")
        if not fire_id:
            return
            
        # Extract user_id from the EA instance that will execute this
        target_uuid = cmd.get("target_uuid")
        if not target_uuid:
            return
            
        # Get user_id from ea_instances table
        conn = _ea_db()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM ea_instances WHERE target_uuid = ?", (target_uuid,))
        row = cur.fetchone()
        user_id = row[0] if row and row[0] else "unknown"
        
        # Create fires table if needed
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fires (
            fire_id TEXT PRIMARY KEY,
            mission_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT,
            ticket INTEGER,
            price REAL,
            idem TEXT UNIQUE,
            created_at INTEGER,
            updated_at INTEGER,
            equity_used REAL,
            risk_pct_used REAL
        )
        """)
        
        # Insert fire record with SENT status
        now = int(time.time())
        cur.execute("""
            INSERT OR IGNORE INTO fires 
            (fire_id, mission_id, user_id, status, created_at, updated_at)
            VALUES (?, ?, ?, 'SENT', ?, ?)
        """, (fire_id, fire_id, user_id, now, now))
        
        conn.commit()
        conn.close()
        LOG.info(f"[CMD] 📝 Fire record created: {fire_id} for user {user_id}")
        
    except Exception as e:
        LOG.warning(f"[CMD] Fire record insert error: {e}")


router = ctx.socket(zmq.ROUTER); router.bind(PUSH_BIND)
pull   = ctx.socket(zmq.PULL)
pull.setsockopt(zmq.RCVHWM, 10000)
pull.bind(QUEUE_PULL)
LOG.info(f"[CMD] Queue bound {QUEUE_PULL}")

# EA registry: uuid -> last_seen
ea_last_seen = {}
# Map UUID to socket identity for routing back
uuid_to_identity = {}

def recv_router_forever():
    while True:
        # ROUTER frames: [identity, empty, payload] OR [identity, payload]
        parts = router.recv_multipart()
        if len(parts) == 3:
            ident, empty, payload = parts
        elif len(parts) == 2:
            ident, payload = parts
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
            # Only update identity mapping if it's new or changed
            old_ident = uuid_to_identity.get(uuid)
            if old_ident != ident:
                if old_ident:
                    LOG.warning(f"[EA] Identity changed for {uuid}: {old_ident} → {ident}")
                uuid_to_identity[uuid] = ident  # Map UUID to actual socket identity
            _upsert_ea_instance(msg)  # Update DB

        if typ in ("HELLO","HEARTBEAT","PING"):
            LOG.info("[EA] %s %s", typ, uuid)
        else:
            # EAs generally shouldn't send other types here; ignore
            pass

def queue_to_router_forever():
    while True:
        cmd = pull.recv_json()
        fire_id = cmd.get("fire_id")
        LOG.info(f"[CMD] DEQ {fire_id} | {cmd.get('type')} | {cmd.get('symbol')}")
        
        uuid = cmd.get("target_uuid")
        if not uuid:
            LOG.warning("DROP cmd without target_uuid: %s", cmd); continue

        # TTL check
        last = ea_last_seen.get(uuid, 0)
        if last == 0 or (time.time() - last) > HEARTBEAT_SEC:
            LOG.warning("[CMD] ❌ EA %s not fresh (ttl %ss). Rejecting %s", uuid, HEARTBEAT_SEC, cmd.get("fire_id"))
            continue

        # Get the actual socket identity for this UUID
        identity = uuid_to_identity.get(uuid)
        if not identity:
            LOG.warning("[CMD] ❌ No socket identity for UUID %s", uuid)
            continue

        # Insert fire record into database for tracking
        if cmd.get("type") == "fire":
            _insert_fire_record(cmd)
        
        payload = json.dumps(cmd).encode()
        # ROUTER to DEALER: send [identity, payload] - DEALER strips identity automatically  
        router.send_multipart([identity, payload])
        LOG.info("[CMD] → %s | %s | %s | %s", uuid, cmd.get("fire_id"), cmd.get("type"), cmd.get("symbol"))

def main():
    LOG.info("[CMD] ROUTER bound %s", PUSH_BIND)
    LOG.info("[CMD] Queue bound %s", QUEUE_PULL)
    t1 = threading.Thread(target=recv_router_forever, daemon=True)
    t2 = threading.Thread(target=queue_to_router_forever, daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()

if __name__ == "__main__":
    main()