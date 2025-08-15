#!/usr/bin/env bash
set -euo pipefail

echo "======================================"
echo "    BITTEN BUS STATUS (Redis Streams)"
echo "======================================"
echo "Time: $(date)"
echo ""

echo "== Redis signals stream info =="
redis-cli XINFO STREAM signals 2>/dev/null | head -20 || echo "Stream not found"

echo -e "\n== Consumer Groups =="
redis-cli XINFO GROUPS signals 2>/dev/null || echo "No groups"

echo -e "\n== Pending messages (relay group) =="
PENDING=$(redis-cli XPENDING signals relay 2>/dev/null | head -1 | awk '{print $1}' || echo 0)
echo "Total pending: $PENDING"
if [ "$PENDING" != "0" ] && [ "$PENDING" != "" ]; then
    echo "Details (first 10):"
    redis-cli XPENDING signals relay - + 10 2>/dev/null
fi

echo -e "\n== Stream Length =="
LEN=$(redis-cli XLEN signals 2>/dev/null || echo 0)
echo "Signals stream: $LEN messages"
if [ "$LEN" -gt 200000 ]; then
    echo "⚠️  WARNING: Approaching retention limit (250k)"
fi

echo -e "\n== Last 2 entries =="
redis-cli XREVRANGE signals + - COUNT 2 2>/dev/null || echo "No entries"

echo -e "\n== Fire Streams =="
FIRE_COUNT=$(redis-cli --scan --pattern "fire.*" 2>/dev/null | wc -l || echo 0)
echo "Active fire streams: $FIRE_COUNT"
if [ "$FIRE_COUNT" -gt 0 ]; then
    echo "Fire stream details:"
    redis-cli --scan --pattern "fire.*" 2>/dev/null | while read stream; do
        len=$(redis-cli XLEN "$stream" 2>/dev/null || echo 0)
        echo "  $stream: $len messages"
    done
fi

echo -e "\n== Process Health =="
for proc in signals_zmq_to_redis signals_redis_to_webapp fire_redis_bridge; do
    if pm2 list | grep -q "$proc.*online"; then
        echo "✅ $proc: ONLINE"
    else
        echo "❌ $proc: DOWN/MISSING"
    fi
done

echo -e "\n== Backup Status =="
LATEST_BACKUP=$(ls -t /var/backups/bitten/redis-aof-*.tar.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    echo "Latest: $(basename $LATEST_BACKUP) ($SIZE)"
else
    echo "No backups found"
fi
BACKUP_COUNT=$(ls /var/backups/bitten/redis-aof-*.tar.gz 2>/dev/null | wc -l || echo 0)
echo "Total backups: $BACKUP_COUNT"