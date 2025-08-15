#!/usr/bin/env bash
# BITTEN System Full Status Check

echo "============================================"
echo "     BITTEN SYSTEM FULL STATUS CHECK"
echo "============================================"
echo "Time: $(date)"
echo ""

echo "📡 SIGNAL PATH (Elite Guard → WebApp)"
echo "────────────────────────────────────"
if pm2 list | grep -q "relay_to_telegram.*stopped"; then
    echo "Mode: ✅ REDIS-ONLY (production)"
    echo "  ZMQ→Redis: $(pm2 list | grep signals_zmq_to_redis | grep -q online && echo '✅' || echo '❌')"
    echo "  Redis→WebApp: $(pm2 list | grep signals_redis_to_webapp | grep -q online && echo '✅' || echo '❌')"
else
    echo "Mode: 🟡 DUAL (legacy + Redis)"
fi
STREAM_LEN=$(redis-cli XLEN signals 2>/dev/null || echo 0)
PENDING=$(redis-cli XPENDING signals relay 2>/dev/null | head -1 | awk '{print $1}' || echo 0)
echo "  Stream: $STREAM_LEN msgs, $PENDING pending"
echo ""

echo "🔥 FIRE PATH (WebApp → EA)"
echo "─────────────────────────"
if [ "${FIRE_SHADOW_ONLY:-0}" == "1" ]; then
    echo "Mode: ✅ REDIS-ONLY"
    echo "  Bridge forwarding: $([ "${FIRE_BRIDGE_ENQUEUE:-0}" == "1" ] && echo '✅' || echo '❌')"
else
    echo "Mode: 🟡 SHADOW (IPC + Redis mirror)"
    echo "  Direct IPC: ✅"
    echo "  Redis shadow: $([ "${FIRE_TO_REDIS:-1}" == "1" ] && echo '✅' || echo '❌')"
fi
echo "  Fire bridge: $(pm2 list | grep fire_redis_bridge | grep -q online && echo '✅ ONLINE' || echo '❌ DOWN')"
echo ""

echo "🤖 CORE PROCESSES"
echo "──────────────────"
for proc in elite_guard webapp command_router confirm_listener bitten-production-bot; do
    if pm2 list | grep -q "$proc.*online"; then
        uptime=$(pm2 describe $proc 2>/dev/null | grep uptime | awk -F'│' '{print $3}' | xargs)
        echo "✅ $proc (up: $uptime)"
    else
        echo "❌ $proc DOWN"
    fi
done
echo ""

echo "💾 EA INSTANCES (Fresh < 180s)"
echo "──────────────────────────────"
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) AS age_s FROM ea_instances WHERE (strftime('%s','now') - last_seen) < 180;" 2>/dev/null || echo "None fresh"
echo ""

echo "🔧 QUICK COMMANDS"
echo "────────────────"
echo "Test fire: /root/HydraX-v2/tools/safe_fire_smoke.sh"
echo "Signal status: /root/HydraX-v2/tools/signals_cutover_status.sh"
echo "Fire status: /root/HydraX-v2/tools/fire_shadow_status.sh"
echo "Rollback signals: pm2 start relay_to_telegram && pm2 save"
echo "Fire cutover: /root/HydraX-v2/tools/fire_cutover.sh"