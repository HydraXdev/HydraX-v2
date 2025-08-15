#!/usr/bin/env bash
set -euo pipefail
echo "[ROLLBACK] Returning /api/fire to direct IPC mode..."

# Disable shadow-only mode (webapp resumes direct IPC enqueue)
export FIRE_SHADOW_ONLY=0
pm2 restart webapp --update-env

# Disable bridge enqueue mode (bridge returns to log-only)
export FIRE_BRIDGE_ENQUEUE=0
pm2 restart fire_redis_bridge --update-env

pm2 save

echo "[ROLLBACK] Complete!"
echo "  - /api/fire back to direct IPC enqueue"
echo "  - fire_redis_bridge in log-only mode"
echo "  - Shadow publishing still active for observability"
echo ""
echo "To re-cutover: /root/HydraX-v2/tools/fire_cutover.sh"