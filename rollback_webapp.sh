#!/bin/bash
# Emergency rollback script for webapp refactoring
# Usage: ./rollback_webapp.sh

echo "🔄 Rolling back webapp to last backup..."

# Find most recent backup
LATEST_BACKUP=$(ls -t /root/HydraX-v2/webapp_server_optimized.py.backup.* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found!"
    exit 1
fi

echo "📋 Using backup: $LATEST_BACKUP"
cp "$LATEST_BACKUP" /root/HydraX-v2/webapp_server_optimized.py

echo "🔄 Restarting webapp..."
pm2 restart webapp

echo "✅ Rollback complete!"
pm2 status webapp
