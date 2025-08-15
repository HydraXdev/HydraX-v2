#!/usr/bin/env bash
set -euo pipefail
DB="${BITTEN_DB:-/root/HydraX-v2/bitten.db}"
echo "=== PROCESSES ==="; pm2 list || true
echo "=== PORTS ==="; ss -tulpen | grep -E ':(5555|5556|5557|5558|5560|8888|8899)' || true
echo "=== REDIS signals ==="; redis-cli XINFO STREAM signals 2>/dev/null | sed -n '1,80p' || echo "No Redis signals stream"
echo "=== REDIS groups ==="; redis-cli XINFO GROUPS signals 2>/dev/null || echo "No Redis groups"
echo "=== DB signals tail ==="; sqlite3 "$DB" "SELECT signal_id,symbol,datetime(created_at,'unixepoch','localtime') FROM signals ORDER BY created_at DESC LIMIT 5;"
echo "=== DB fires tail ===";   sqlite3 "$DB" "SELECT fire_id,status,ticket,datetime(created_at,'unixepoch','localtime') FROM fires ORDER BY created_at DESC LIMIT 5;"
echo "=== EA freshness ===";    sqlite3 "$DB" "SELECT target_uuid,user_id,(strftime('%s','now')-last_seen) AS age_s,last_balance,last_equity FROM ea_instances ORDER BY last_seen DESC LIMIT 5;"