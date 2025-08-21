#!/bin/bash
# Rollback to original Elite Guard

echo "⚠️  ROLLING BACK TO ORIGINAL ELITE GUARD..."

# Stop enhanced
pm2 stop elite_guard
pm2 delete elite_guard

# Restore original
pm2 start /root/HydraX-v2/elite_guard_with_citadel.py \
    --name elite_guard \
    --interpreter python3

pm2 restart relay_to_telegram

echo "✅ Rollback complete"
pm2 list | grep elite_guard
