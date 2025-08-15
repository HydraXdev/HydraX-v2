#!/usr/bin/env bash
set -euo pipefail
echo "[CUTOVER] Switching /api/fire to Redis-only mode..."

# Enable shadow-only mode (webapp stops direct IPC enqueue)
export FIRE_SHADOW_ONLY=1
pm2 restart webapp --update-env

# Enable bridge enqueue mode (bridge forwards to IPC)
export FIRE_BRIDGE_ENQUEUE=1
pm2 restart fire_redis_bridge --update-env

pm2 save

echo "[CUTOVER] Complete!"
echo "  - /api/fire now publishes to Redis only"
echo "  - fire_redis_bridge forwarding to IPC"
echo "  - Idempotency protected via fires.idem"
echo ""
echo "To monitor: pm2 logs fire_redis_bridge"
echo "To rollback: /root/HydraX-v2/tools/fire_rollback.sh"