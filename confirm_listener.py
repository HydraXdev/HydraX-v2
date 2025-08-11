#!/usr/bin/env python3
"""
Confirm Listener - SUB 5558 → update DB + Athena replies under mission
Athena bot owns all group confirmation messages
"""
import os
import json
import time
import sqlite3
import requests
import zmq
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AthenaConfirm')

DB = os.environ.get("BITTEN_DB", "bitten.db")
ATHENA_TOKEN = os.environ["ATHENA_BOT_TOKEN"]
ATHENA_CHAT_ID = int(os.environ["ATHENA_CHAT_ID"])
CONFIRM_SUB = os.environ.get("ZMQ_CONFIRM_SUB", "tcp://127.0.0.1:5558")

def db():
    return sqlite3.connect(DB)

def athena_reply(message_id: int, text: str):
    """Reply to a specific message via Athena bot"""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{ATHENA_TOKEN}/sendMessage",
            json={
                "chat_id": ATHENA_CHAT_ID,
                "text": text,
                "reply_to_message_id": message_id,
                "parse_mode": "HTML"
            },
            timeout=10
        )
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to reply via Athena: {e}")
        return False

def main():
    logger.info("🚀 Starting Athena Confirmation Listener")
    logger.info(f"📡 Subscribing to: {CONFIRM_SUB}")
    logger.info(f"🤖 Using Athena bot for group: {ATHENA_CHAT_ID}")
    
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVTIMEO, 0)  # Non-blocking
    sub.connect(CONFIRM_SUB)
    sub.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
    
    conn = db()
    poller = zmq.Poller()
    poller.register(sub, zmq.POLLIN)
    
    confirm_count = 0
    
    logger.info("✅ Athena confirm listener ready...")
    
    while True:
        try:
            socks = dict(poller.poll(500))
            if sub not in socks:
                continue
            
            try:
                msg = sub.recv_string(flags=zmq.NOBLOCK)
            except zmq.Again:
                continue
            
            # Parse confirmation {fire_id, status, ticket, price, reason?}
            c = json.loads(msg)
            confirm_count += 1
            
            fire_id = c.get("fire_id")
            status = c.get("status", "UNKNOWN")
            ticket = c.get("ticket")
            price = c.get("price")
            
            logger.info(f"📨 Confirmation #{confirm_count}: fire_id={fire_id}, status={status}")
            
            if not fire_id:
                logger.warning("Confirmation missing fire_id")
                continue
            
            # Update fires table
            conn.execute("""
                UPDATE fires 
                SET status=?, ticket=?, price=?, updated_at=? 
                WHERE fire_id=?
            """, (status, ticket, price, int(time.time()), fire_id))
            conn.commit()
            
            # Get mission ID from fires
            row = conn.execute("""
                SELECT mission_id 
                FROM fires 
                WHERE fire_id=?
            """, (fire_id,)).fetchone()
            
            if not row:
                logger.warning(f"No fire record found for: {fire_id}")
                continue
            
            mission_id = row[0]
            
            # Get mission details
            m = conn.execute("""
                SELECT tg_message_id, payload_json 
                FROM missions 
                WHERE mission_id=?
            """, (mission_id,)).fetchone()
            
            if not m:
                logger.warning(f"No mission found for: {mission_id}")
                continue
            
            tg_msg_id, payload_json = m
            
            # Parse payload for symbol/side
            try:
                p = json.loads(payload_json)
                symbol = p.get('symbol', 'UNKNOWN')
                side = p.get('direction', p.get('side', 'BUY')).upper()
            except Exception:
                symbol = 'UNKNOWN'
                side = 'UNKNOWN'
            
            # Send appropriate reply via Athena
            if status == "FILLED":
                reply_text = (f"✅ EXECUTED — <b>{symbol}</b> {side} @ <b>{price}</b> • "
                            f"ticket <code>{ticket}</code>")
                if athena_reply(tg_msg_id, reply_text):
                    logger.info(f"✅ Athena confirmed execution for {mission_id}")
                
                # Update mission status
                conn.execute("""
                    UPDATE missions 
                    SET status=? 
                    WHERE mission_id=?
                """, ("FILLED", mission_id))
                conn.commit()
                
            elif status in ("REJECTED", "FAILED", "TIMEOUT"):
                reason = c.get("reason", "Unknown error")
                reply_text = (f"❌ FAILED — {symbol} {side} • "
                            f"reason: <code>{reason}</code>")
                if athena_reply(tg_msg_id, reply_text):
                    logger.info(f"❌ Athena reported failure for {mission_id}")
                
                # Update mission status
                conn.execute("""
                    UPDATE missions 
                    SET status=? 
                    WHERE mission_id=?
                """, (status, mission_id))
                conn.commit()
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(1)
    
    sub.close()
    ctx.term()
    conn.close()
    logger.info("👋 Athena confirm listener stopped")

if __name__ == "__main__":
    main()