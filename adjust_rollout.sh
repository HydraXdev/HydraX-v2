#!/bin/bash
# Adjust rollout percentage

PERCENT=${1:-50}
echo "Adjusting rollout to $PERCENT%..."

pm2 delete elite_guard
pm2 start /root/HydraX-v2/elite_guard_enhanced.py \
    --name elite_guard \
    --interpreter python3 \
    -- --percent $PERCENT

echo "✅ Rollout adjusted to $PERCENT%"
