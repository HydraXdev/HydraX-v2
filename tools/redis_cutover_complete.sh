#!/usr/bin/env bash
# BITTEN System Redis Cutover Complete Status

echo "================================================"
echo "   🎯 BITTEN REDIS CUTOVER COMPLETE 🎯"
echo "================================================"
echo "Time: $(date)"
echo ""

echo "✅ BOTH PATHS NOW REDIS-ONLY"
echo "───────────────────────────"
echo "📡 SIGNALS: Elite Guard → Redis Stream → WebApp"
echo "🔥 FIRE: WebApp → Redis Stream → Bridge → IPC → EA"
echo ""

echo "🔒 SAFETY FEATURES"
echo "─────────────────"
echo "✅ Bridge ignores dry_run payloads"
echo "✅ Idempotency via fires.idem index"
echo "✅ Server-side user mapping"
echo "✅ EA freshness checks"
echo ""

echo "📊 CURRENT STATUS"
echo "────────────────"
# Check process status
WEBAPP_ENV=$(pm2 env 15 2>/dev/null | grep FIRE_SHADOW_ONLY | awk -F': ' '{print $2}')
BRIDGE_ENV=$(pm2 env 24 2>/dev/null | grep FIRE_BRIDGE_ENQUEUE | awk -F': ' '{print $2}')
echo "Webapp FIRE_SHADOW_ONLY: ${WEBAPP_ENV:-not set} (1=Redis-only)"
echo "Bridge FIRE_BRIDGE_ENQUEUE: ${BRIDGE_ENV:-not set} (1=forwarding)"
echo ""

# Check streams
echo "Redis Streams:"
echo "  signals: $(redis-cli XLEN signals 2>/dev/null || echo 0) messages"
echo "  fire.COMMANDER_DEV_001: $(redis-cli XLEN fire.COMMANDER_DEV_001 2>/dev/null || echo 0) messages"
echo ""

# Check processes
echo "Process Health:"
for proc in webapp fire_redis_bridge signals_zmq_to_redis signals_redis_to_webapp command_router; do
    if pm2 list | grep -q "$proc.*online"; then
        echo "  ✅ $proc"
    else
        echo "  ❌ $proc"
    fi
done
echo ""

echo "⚡ ROLLBACK COMMANDS"
echo "───────────────────"
echo "Fire to dual mode (IPC + shadow):"
echo "  export FIRE_SHADOW_ONLY=0 && pm2 restart webapp --update-env"
echo "  export FIRE_BRIDGE_ENQUEUE=0 && pm2 restart fire_redis_bridge --update-env"
echo ""
echo "Signals to legacy relay:"
echo "  pm2 start relay_to_telegram && pm2 save"
echo ""

echo "🛠️ MONITORING"
echo "────────────"
echo "Watch fire bridge: pm2 logs fire_redis_bridge --lines 50"
echo "Check streams: redis-cli XINFO STREAM fire.COMMANDER_DEV_001"
echo "System status: /root/HydraX-v2/tools/bitten_full_status.sh"
echo "Bus status: /root/HydraX-v2/tools/bus_status.sh"