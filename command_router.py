#!/usr/bin/env python3
"""
BITTEN Command Router - Precise EA Targeting via DEALER/ROUTER Pattern
Binds ROUTER on tcp://*:5555 for EAs to connect as DEALER
Binds local IPC queue for webapp to submit fire commands
Routes commands to specific EA by target_uuid identity
"""
import os
import zmq
import json
import time
import threading
import sqlite3
import requests
from datetime import datetime

# Public ports (EAs connect here)
CMD_BIND = os.getenv("CMD_BIND", "tcp://*:5555")     # ROUTER (EA DEALER connects)
# Local queue for webapp -> router (not exposed to internet)
QUEUE_BIND = os.getenv("CMD_QUEUE", "ipc:///tmp/bitten_cmdqueue")  # PULL

EA_BOOK = {}  # target_uuid -> {"last_seen": ts}

def send_ea_linked_notification(user_id: str, ea_uuid: str, broker: str, account: str, equity: float, currency: str):
    """Send Athena DM to user about EA link"""
    try:
        # Get user tier for risk info
        conn = sqlite3.connect('/root/HydraX-v2/data/user_profiles.db')
        cursor = conn.cursor()
        cursor.execute("SELECT tier FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        tier = row[0] if row else "PRESS_PASS"
        conn.close()
        
        # Format notification message
        message = f"""✅ <b>EA LINKED SUCCESSFULLY</b>

<b>Broker:</b> {broker}
<b>Account:</b> {account}
<b>Equity:</b> ${equity:.2f} {currency}
<b>Risk Tier:</b> {tier}

Your EA is now connected and ready to receive trade signals.
Risk per trade: 2% (${equity * 0.02:.2f})

Stay tactical, Commander! 🎯"""

        # Send via Athena bot
        athena_token = os.environ.get("ATHENA_BOT_TOKEN")
        if athena_token:
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "HTML"
            }
            r = requests.post(
                f"https://api.telegram.org/bot{athena_token}/sendMessage",
                json=payload,
                timeout=5
            )
            if r.status_code == 200:
                print(f"[CMD] 📨 Sent EA link notification to user {user_id}")
            else:
                print(f"[CMD] Failed to send notification: {r.status_code}")
                
    except Exception as e:
        print(f"[CMD] Error sending notification: {e}")

def update_ea_instance(target_uuid: str, metrics: dict):
    """Update EA instance in database with latest metrics"""
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        now = int(time.time())
        
        # Extract metrics with defaults
        user_id = metrics.get('user_id')
        account_login = metrics.get('account_login', metrics.get('account'))
        broker = metrics.get('broker')
        currency = metrics.get('currency')
        leverage = metrics.get('leverage')
        balance = metrics.get('balance')
        equity = metrics.get('equity')
        
        # Upsert EA instance
        cursor.execute('''
            INSERT INTO ea_instances (
                target_uuid, user_id, account_login, broker, currency,
                leverage, last_balance, last_equity, last_seen, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(target_uuid) DO UPDATE SET
                user_id = COALESCE(excluded.user_id, user_id),
                account_login = COALESCE(excluded.account_login, account_login),
                broker = COALESCE(excluded.broker, broker),
                currency = COALESCE(excluded.currency, currency),
                leverage = COALESCE(excluded.leverage, leverage),
                last_balance = COALESCE(excluded.last_balance, last_balance),
                last_equity = COALESCE(excluded.last_equity, last_equity),
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            target_uuid, user_id, account_login, broker, currency,
            leverage, balance, equity, now, now, now
        ))
        
        conn.commit()
        conn.close()
        
        # Log metrics update
        if balance and equity:
            print(f"[CMD] 💰 EA Metrics: {target_uuid} | Balance: {balance} | Equity: {equity} | Currency: {currency}")
        
    except Exception as e:
        print(f"[CMD] ❌ Failed to update EA instance: {e}")

def router_loop():
    ctx = zmq.Context.instance()
    router = ctx.socket(zmq.ROUTER)
    router.setsockopt(zmq.LINGER, 0)
    router.bind(CMD_BIND)

    qpull = ctx.socket(zmq.PULL)
    qpull.bind(QUEUE_BIND)

    poller = zmq.Poller()
    poller.register(router, zmq.POLLIN)
    poller.register(qpull,  zmq.POLLIN)

    print(f"[CMD] ROUTER bound {CMD_BIND}")
    print(f"[CMD] Queue   bound {QUEUE_BIND}")
    print(f"[CMD] Command Router started at {datetime.now()}")

    while True:
        try:
            events = dict(poller.poll(1000))

            # A) Webapp enqueued a command → forward to specific EA identity
            if qpull in events:
                msg = qpull.recv_json()  # {"target_uuid": "...", "payload": {...}}
                tu = msg.get("target_uuid")
                payload = msg.get("payload", {})
                if not tu or not isinstance(payload, dict):
                    print(f"[CMD] ❌ Bad queue message: {msg}")
                    continue
                
                # Send to EA: [identity, payload] (2-part format)
                try:
                    router.send_multipart([tu.encode(), json.dumps(payload).encode()])
                    fire_id = payload.get('fire_id', '')
                    cmd_type = payload.get('type', '')
                    symbol = payload.get('symbol', '')
                    print(f"[CMD] → {tu} | {fire_id} | {cmd_type} | {symbol}")
                except Exception as e:
                    print(f"[CMD] ❌ Failed to route to {tu}: {e}")

            # B) EA traffic (HELLO / HEARTBEAT / replies)
            if router in events:
                try:
                    frames = router.recv_multipart()
                    
                    # Normalize incoming frames (accept 2-part or 3-part)
                    if len(frames) == 2:
                        ident, data = frames
                    elif len(frames) == 3 and frames[1] == b"":
                        ident, data = frames[0], frames[2]
                    else:
                        print(f"[CMD] ❌ Invalid frame count: {len(frames)} from {frames[0] if frames else b'?'}")
                        continue
                    
                    tu = ident.decode(errors="ignore")
                    
                    try:
                        obj = json.loads(data.decode())
                    except Exception as e:
                        print(f"[CMD] {tu} ❌ Bad JSON: {e}")
                        continue

                    typ = obj.get("type", "").upper()
                    
                    if typ in ("HELLO", "HEARTBEAT"):
                        # Rate limiting check
                        now = int(time.time())
                        if tu in EA_BOOK:
                            last_msg = EA_BOOK[tu].get("last_seen", 0)
                            if now - last_msg < 1:  # Limit to 1 message per second
                                print(f"[CMD] ⚠️ Rate limit exceeded for {tu}")
                                continue
                        
                        # Validate user exists (security check)
                        user_id = obj.get('user_id')
                        if typ == "HELLO" and user_id:
                            conn = sqlite3.connect('/root/HydraX-v2/data/user_profiles.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT 1 FROM user_profiles WHERE user_id = ?", (user_id,))
                            if not cursor.fetchone():
                                print(f"[CMD] ❌ Rejected HELLO from {tu} - unknown user {user_id}")
                                conn.close()
                                continue
                            conn.close()
                        
                        EA_BOOK[tu] = {
                            "last_seen": now,
                            "type": typ,
                            "metrics": obj,
                            "msg_count": EA_BOOK.get(tu, {}).get("msg_count", 0) + 1
                        }
                        
                        # Log connection IP for audit
                        print(f"[CMD] 📍 {typ} from {tu} | Messages: {EA_BOOK[tu]['msg_count']}")
                        
                        # Update EA metrics in database
                        update_ea_instance(tu, obj)
                        
                        if typ == "HELLO":
                            # Extract and log metrics
                            balance = obj.get('balance', 'N/A')
                            equity = obj.get('equity', 'N/A')
                            currency = obj.get('currency', 'N/A')
                            leverage = obj.get('leverage', 'N/A')
                            broker = obj.get('broker', 'Unknown')
                            account = obj.get('account_login', obj.get('account', 'N/A'))
                            user_id = obj.get('user_id')
                            
                            print(f"[CMD] ✅ HELLO from {tu} | Balance: {balance} | Equity: {equity} | Currency: {currency} | Leverage: {leverage}")
                            
                            # Send WELCOME back with confirmation of metrics received (2-part format)
                            welcome = {
                                "type": "WELCOME",
                                "status": "registered",
                                "target_uuid": tu,
                                "message": f"EA linked successfully. Equity: {equity} {currency}",
                                "timestamp": int(time.time())
                            }
                            # Send 2-part response: [identity, payload]
                            router.send_multipart([ident, json.dumps(welcome).encode()])
                            
                            # Send Athena DM to user about EA link
                            if user_id:
                                try:
                                    send_ea_linked_notification(user_id, tu, broker, account, equity, currency)
                                except Exception as e:
                                    print(f"[CMD] Failed to send link notification: {e}")
                    
                    elif typ == "CONFIRM":
                        # EA confirmation of trade execution
                        ticket = obj.get("ticket", "NO_TICKET")
                        fire_id = obj.get("fire_id", "")
                        print(f"[CMD] ✅ CONFIRM from {tu} | Ticket: {ticket} | Fire: {fire_id}")
                    
                    else:
                        # Other message types
                        print(f"[CMD] {tu} | Type: {typ}")
                        
                except Exception as e:
                    print(f"[CMD] ❌ Error processing EA message: {e}")
                    
        except KeyboardInterrupt:
            print("[CMD] Shutting down...")
            break
        except Exception as e:
            print(f"[CMD] ❌ Main loop error: {e}")
            time.sleep(1)
    
    router.close()
    qpull.close()
    ctx.term()

def cleanup_stale_eas():
    """Remove EAs that haven't sent heartbeat in 60 seconds"""
    while True:
        time.sleep(30)
        now = int(time.time())
        stale = []
        for uuid, info in EA_BOOK.items():
            if now - info["last_seen"] > 60:
                stale.append(uuid)
        for uuid in stale:
            print(f"[CMD] ⚠️ Removing stale EA: {uuid}")
            del EA_BOOK[uuid]

if __name__ == "__main__":
    # Start cleanup thread
    cleanup = threading.Thread(target=cleanup_stale_eas, daemon=True)
    cleanup.start()
    
    # Run main router loop
    router_loop()