#!/usr/bin/env bash
# BITTEN System Status Check

echo "=== BITTEN SYSTEM STATUS CHECK ==="
echo "Time: $(date)"
echo "==========================================="

echo -e "\n== Process Health =="
echo "Critical processes:"
for proc in elite_guard relay_to_telegram signals_zmq_to_redis signals_redis_to_webapp webapp command_router confirm_listener; do
    if pm2 list | grep -q "$proc.*online"; then
        echo "✅ $proc: ONLINE"
    else
        echo "❌ $proc: DOWN/ERROR"
    fi
done

echo -e "\n== Redis Stream Status =="
echo "Stream length: $(redis-cli XLEN signals 2>/dev/null || echo 0)"
echo "Consumer groups: $(redis-cli XINFO GROUPS signals 2>/dev/null | grep -c 'name' || echo 0)"
echo "Pending messages: $(redis-cli XPENDING signals relay 2>/dev/null | head -1 | awk '{print $1}' || echo 0)"

echo -e "\n== EA Instances (Fresh < 180s) =="
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) AS age_s FROM ea_instances WHERE (strftime('%s','now') - last_seen) < 180;" 2>/dev/null || echo "None fresh"

echo -e "\n== Recent Signals (last 5 min) =="
echo "Signals in DB: $(sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s','now') - 300;" 2>/dev/null || echo 0)"
echo "Missions created: $(sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM missions WHERE created_at > strftime('%s','now') - 300;" 2>/dev/null || echo 0)"

echo -e "\n== Fire Test (dry_run) =="
/root/HydraX-v2/tools/safe_fire_smoke.sh COMMANDER_DEV_001 EURUSD 2>/dev/null | jq -c . || echo "Fire test failed"

echo -e "\n== Cutover Commands =="
echo "To switch to Redis-only: pm2 stop relay_to_telegram && pm2 save"
echo "To rollback to legacy: pm2 start relay_to_telegram && pm2 save"
echo "Current mode: $(pm2 list | grep -q 'relay_to_telegram.*online' && echo 'DUAL (legacy + Redis)' || echo 'Redis-only')"