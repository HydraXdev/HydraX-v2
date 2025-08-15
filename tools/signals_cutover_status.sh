#!/usr/bin/env bash
# Signals Redis Cutover Status & Commands

echo "=== SIGNALS REDIS CUTOVER STATUS ==="
echo "Time: $(date)"
echo "====================================="

echo -e "\n== Signal Path Status =="
if pm2 list | grep -q "relay_to_telegram.*stopped"; then
    echo "✅ REDIS-ONLY MODE (cutover complete)"
    echo "   - Legacy relay: STOPPED"
    echo "   - signals_zmq_to_redis: $(pm2 list | grep signals_zmq_to_redis | grep -q online && echo 'ONLINE' || echo 'DOWN')"
    echo "   - signals_redis_to_webapp: $(pm2 list | grep signals_redis_to_webapp | grep -q online && echo 'ONLINE' || echo 'DOWN')"
elif pm2 list | grep -q "relay_to_telegram.*online"; then
    echo "⚠️  DUAL MODE (both paths active)"
    echo "   - Legacy relay: ONLINE"
    echo "   - Redis path: ALSO ONLINE"
else
    echo "❌ UNKNOWN STATE"
fi

echo -e "\n== Redis Stream Health =="
LENGTH=$(redis-cli XLEN signals 2>/dev/null || echo 0)
PENDING=$(redis-cli XPENDING signals relay 2>/dev/null | head -1 | awk '{print $1}' || echo 0)
echo "Stream length: $LENGTH messages"
echo "Pending: $PENDING messages"
if [ "$PENDING" -gt 100 ]; then
    echo "⚠️  WARNING: High pending count!"
fi

echo -e "\n== Process Uptime =="
for proc in signals_zmq_to_redis signals_redis_to_webapp; do
    uptime=$(pm2 describe $proc 2>/dev/null | grep uptime | awk -F'│' '{print $3}' | xargs)
    restarts=$(pm2 describe $proc 2>/dev/null | grep restarts | awk -F'│' '{print $3}' | xargs)
    echo "$proc: uptime=$uptime, restarts=$restarts"
done

echo -e "\n== Commands =="
echo "Monitor logs:"
echo "  pm2 logs signals_zmq_to_redis --lines 50"
echo "  pm2 logs signals_redis_to_webapp --lines 50"
echo ""
echo "Check stream:"
echo "  redis-cli XINFO STREAM signals"
echo "  redis-cli XPENDING signals relay"
echo ""
echo "ROLLBACK to legacy relay:"
echo "  pm2 start relay_to_telegram && pm2 save"
echo ""
echo "RE-CUTOVER to Redis-only:"
echo "  pm2 stop relay_to_telegram && pm2 save"
echo ""
echo "Fire path cutover (optional):"
echo "  /root/HydraX-v2/tools/fire_cutover.sh"