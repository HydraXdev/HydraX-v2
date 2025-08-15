#!/usr/bin/env bash
# Fire Shadow System Status Check

echo "=== FIRE SHADOW SYSTEM STATUS ==="
echo "Time: $(date)"
echo "=================================="

echo -e "\n== Shadow Mode Configuration =="
echo "FIRE_TO_REDIS: ${FIRE_TO_REDIS:-1} (1=shadow enabled)"
echo "FIRE_SHADOW_ONLY: ${FIRE_SHADOW_ONLY:-0} (1=Redis-only, 0=dual)"
echo "FIRE_BRIDGE_ENQUEUE: ${FIRE_BRIDGE_ENQUEUE:-0} (1=forwarding, 0=log-only)"

echo -e "\n== Process Status =="
echo "webapp: $(pm2 list | grep -q 'webapp.*online' && echo '✅ ONLINE' || echo '❌ DOWN')"
echo "fire_redis_bridge: $(pm2 list | grep -q 'fire_redis_bridge.*online' && echo '✅ ONLINE' || echo '❌ DOWN')"
echo "command_router: $(pm2 list | grep -q 'command_router.*online' && echo '✅ ONLINE' || echo '❌ DOWN')"

echo -e "\n== Per-EA Fire Streams =="
redis-cli --scan --pattern "fire.*" 2>/dev/null | while read stream; do
    len=$(redis-cli XLEN "$stream" 2>/dev/null || echo 0)
    groups=$(redis-cli XINFO GROUPS "$stream" 2>/dev/null | grep -c "name" || echo 0)
    echo "$stream: $len messages, $groups consumer groups"
done || echo "No fire streams found"

echo -e "\n== Current Operation Mode =="
if [ "${FIRE_SHADOW_ONLY:-0}" == "1" ] && [ "${FIRE_BRIDGE_ENQUEUE:-0}" == "1" ]; then
    echo "🔴 REDIS-ONLY MODE (production)"
    echo "   - Webapp publishes to Redis only"
    echo "   - Bridge forwards to IPC queue"
elif [ "${FIRE_TO_REDIS:-1}" == "1" ] && [ "${FIRE_SHADOW_ONLY:-0}" == "0" ]; then
    echo "🟡 SHADOW MODE (dual path)"
    echo "   - Webapp sends to IPC directly"
    echo "   - Also mirrors to Redis for observability"
    echo "   - Bridge in ${FIRE_BRIDGE_ENQUEUE:-0}==1 ? 'forward' : 'log-only' mode"
else
    echo "⚪ LEGACY MODE (IPC only)"
    echo "   - No Redis shadow publishing"
fi

echo -e "\n== Available Commands =="
echo "Test (dry-run): /root/HydraX-v2/tools/safe_fire_smoke.sh COMMANDER_DEV_001 EURUSD"
echo "Cutover to Redis: /root/HydraX-v2/tools/fire_cutover.sh"
echo "Rollback to dual: /root/HydraX-v2/tools/fire_rollback.sh"
echo "Monitor bridge: pm2 logs fire_redis_bridge --lines 50"