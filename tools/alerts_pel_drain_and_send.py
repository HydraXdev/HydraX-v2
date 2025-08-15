import os, time, json, redis, requests, urllib.parse
R = redis.Redis(host=os.getenv("REDIS_HOST","127.0.0.1"), port=int(os.getenv("REDIS_PORT","6379")), decode_responses=True)
STREAM = os.getenv("STREAM","alerts"); GROUP=os.getenv("GROUP","telegram"); CONSUMER=os.getenv("CONSUMER","athena")
TG_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN"); CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")  # must be set in env already
assert TG_TOKEN and CHAT_ID, "Missing TELEGRAM_BOT_TOKEN/CHAT_ID env"

def send(msg):
    u=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r=requests.post(u, json={"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True})
    r.raise_for_status(); return r.json().get("result",{}).get("message_id")

claimed = 0
start_id = "0-0"
while True:
    # XAUTOCLAIM returns pending older than 0 ms; we'll batch 50
    resp = R.xautoclaim(STREAM, GROUP, CONSUMER, 0, start_id, count=50)
    next_start = resp[0]
    items = resp[1]
    if not items:
        break
    for mid, fields in items:
        try:
            # fields is dict-like already (decode_responses=True)
            # Build minimal 3-line alert (already used in broadcaster)
            pc = fields.get("pattern_class","RAPID")
            sym = fields.get("symbol","?")
            dirn= fields.get("direction","?")
            conf= fields.get("confidence","?")
            rr  = fields.get("target_rr","?")
            url = fields.get("mission_url","")
            if pc == "SNIPER":
                line1 = "🎯 SNIPER"
            else:
                line1 = "⚡ RAPID"
            msg = f"{line1}\n{sym} {dirn} • TCS {conf}% • RR {rr}\n{url}".strip()
            msg_id = send(msg)
            # ACK after successful send
            R.xack(STREAM, GROUP, mid)
            claimed += 1
            print(f"[PEL-DRAIN] SENT {mid} → msg_id={msg_id}")
        except Exception as e:
            print(f"[PEL-DRAIN][ERR] {mid} {e}")
    start_id = next_start
print(f"[PEL-DRAIN] Done. Sent {claimed} messages.")
