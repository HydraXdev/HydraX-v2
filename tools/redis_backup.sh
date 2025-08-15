#!/usr/bin/env bash
set -euo pipefail

# Redis backup script for BITTEN system
TS=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/var/backups/bitten
OUT="$BACKUP_DIR/redis-aof-$TS.tar.gz"

echo "[BACKUP] Starting Redis backup at $(date)"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Force fsync of AOF & RDB
echo "[BACKUP] Forcing Redis save..."
redis-cli BGSAVE >/dev/null 2>&1 || true
sleep 2  # Give Redis time to complete background save

# Create backup archive
echo "[BACKUP] Creating archive..."
if [ -f /var/lib/redis/appendonly.aof ] && [ -f /var/lib/redis/dump.rdb ]; then
    tar -czf "$OUT" /var/lib/redis/appendonly.aof /var/lib/redis/dump.rdb 2>/dev/null
elif [ -f /var/lib/redis/appendonly.aof ]; then
    tar -czf "$OUT" /var/lib/redis/appendonly.aof 2>/dev/null
elif [ -f /var/lib/redis/dump.rdb ]; then
    tar -czf "$OUT" /var/lib/redis/dump.rdb 2>/dev/null
else
    # Try alternate locations
    if [ -f /var/lib/redis/6379/appendonly.aof ]; then
        tar -czf "$OUT" /var/lib/redis/6379/appendonly.aof 2>/dev/null
    elif [ -f /etc/redis/dump.rdb ]; then
        tar -czf "$OUT" /etc/redis/dump.rdb 2>/dev/null
    else
        echo "[BACKUP] Warning: No Redis data files found"
        exit 1
    fi
fi

# Check backup size
SIZE=$(du -h "$OUT" 2>/dev/null | cut -f1)
echo "[BACKUP] Complete: $OUT ($SIZE)"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "redis-aof-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
echo "[BACKUP] Cleaned up backups older than 7 days"