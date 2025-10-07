# 🛡️ BITTEN Ops Runbook

> **Purpose**: Verify end-to-end health of BITTEN (EA → Router → Guard → Redis → Athena → Telegram) in under 60s.

---

## 1. Tick Feed Health

```bash
# Check tick mirror (ipc:///tmp/tick_mirror) for 10s
python3 - <<'PY'
import zmq,json,time,collections
ctx=zmq.Context(); s=ctx.socket(zmq.SUB); s.setsockopt(zmq.SUBSCRIBE,b'')
s.connect("ipc:///tmp/tick_mirror"); s.setsockopt(zmq.RCVTIMEO,2000)
counts=collections.Counter(); start=time.time()
while time.time()-start<10:
    try: pkt=json.loads(s.recv().decode()); counts[pkt.get("symbol")]+=1
    except: pass
dur=time.time()-start; total=sum(counts.values())
print("Tick rate:", round(total/dur,2),"msg/s; top symbols:",counts.most_common(5))
PY
```

✅ **Expect**: >5 msg/s across majors (EURUSD, XAUUSD, etc).

---

## 2. Command Plane

```bash
# Ping → expect Pong in confirm logs
python3 - <<'PY'
import zmq,json,time; ctx=zmq.Context(); p=ctx.socket(zmq.PUSH)
p.connect("ipc:///tmp/bitten_cmdqueue"); pid=f"OPS-PING-{int(time.time())}"
p.send_json({"type":"ping","target_uuid":"COMMANDER_DEV_001","ping_id":pid}); print("SENT",pid)
PY
tail -n 20 /root/.pm2/logs/confirm-listener-v207-error.log | grep OPS-PING
```

✅ **Expect**: a 🏓 PONG entry within ~5s.

---

## 3. Router / Ports

```bash
ss -ltnp | egrep ':5555|:5556|:5558|:5560'
```

✅ **Expect**: One owner per sacred port.

---

## 4. Elite Guard

```bash
tail -n 50 /root/.pm2/logs/elite-guard-error.log
```

✅ **Expect**: "15-second scan trigger" and pattern scores.
⚠️ **Look for**: "ago=<5s" on ticks, not 64k+ seconds.

---

## 5. Redis Alert Bus

```bash
# Show stream + consumer group
redis-cli XINFO STREAM alerts:v1
redis-cli XINFO GROUPS alerts:v1
```

✅ **Expect**: Length small (queue drains), group `athena:g1` exists.

---

## 6. Telegram Sender (Athena)

```bash
tail -n 50 /root/.pm2/logs/athena-broadcaster-secure-error.log
tail -n 20 /root/.pm2/logs/athena-broadcaster-secure-out.log
```

✅ **Expect**: `[TG OK]` lines.
⚠️ **If you see** repeated `[TG TIMEOUT]` → check VPS network / rate-limits.
❌ **If** `[TG FINAL_FAIL]` → check DLQ.

---

## 7. DLQ (Dead Letter Queue)

```bash
redis-cli XINFO STREAM alerts:v1:dead
```

✅ **Expect**: Should be empty (0 length). Non-zero → investigate Telegram sender errors.

---

## 8. End-to-End Test (manual trigger)

```bash
# Inject a synthetic alert into Redis
redis-cli XADD alerts:v1 * type signal_alert alert_id OPS-TEST text "[OPS TEST]" ts $(date +%s)
```

✅ **Expect**: Athena log `[TG OK] alert_id=OPS-TEST`.

---

## 9. Pager Guards (cron/watchdog)

- **Ticks**: alert if mirror count = 0 for 2 runs in market hours.
- **Pong**: alert if missing for >60s.
- **DLQ**: alert if stream length >5.

---

## ✅ Green State

- ✅ Tick rate >5 msg/s
- ✅ PONG received
- ✅ Guard scans every 15s
- ✅ Redis queue draining, DLQ empty
- ✅ Athena logs `[TG OK]` regularly

---

## 🚨 Critical Process Dependencies

**Required for Signal Generation:**
```bash
pm2 list | grep -E "elite_guard|zmq_telemetry_bridge"
```

**Required for Fire Execution:**
```bash
pm2 list | grep -E "command_router|confirm_listener"
```

**Required for Alert Delivery:**
```bash
pm2 list | grep -E "athena_broadcaster_secure"
```

---

## 🔧 Quick Health Check Script

```bash
#!/bin/bash
# Quick system health verification
echo "🛡️ BITTEN SYSTEM HEALTH CHECK"
echo "================================"

echo "1. Critical Processes:"
pm2 list | grep -E "(elite_guard|command_router|confirm_listener|athena_broadcaster_secure)" | awk '{print $2 " - " $9}'

echo -e "\n2. Port Bindings:"
ss -ltnp | egrep ':5555|:5558' | awk '{print $4 " → " $7}'

echo -e "\n3. Recent Elite Guard Activity:"
tail -n 3 /root/.pm2/logs/elite-guard-error.log | grep -E "(scan trigger|ticks.*ago)"

echo -e "\n4. Recent Athena Activity:"
tail -n 3 /root/.pm2/logs/athena-broadcaster-secure-out.log | grep -E "\[TG"

echo -e "\n5. DLQ Status:"
redis-cli XLEN alerts:v1:dead 2>/dev/null || echo "DLQ stream not found"

echo -e "\n✅ Health check complete"
```

---

## 📞 Emergency Contacts & Escalation

**L1 - System Restart:**
```bash
pm2 restart elite_guard command_router confirm_listener athena_broadcaster_secure
```

**L2 - Full System Reset:**
```bash
pm2 restart all
```

**L3 - EA Connection Issues:**
- Check EA heartbeat: `sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances;"`
- If age >120s, restart EA or check ForexVPS connection
