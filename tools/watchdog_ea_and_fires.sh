#!/usr/bin/env bash
set -euo pipefail
DB="${1:-/root/HydraX-v2/bitten.db}"
FRESH=${FRESH:-180}
STALE_FIRES=${STALE_FIRES:-120}   # seconds without confirmation
INTERVAL=${INTERVAL:-30}  # check interval

while true; do
  echo "== EA freshness (age_s > $FRESH => ALERT) =="
  sqlite3 "$DB" "SELECT target_uuid,user_id,(strftime('%s','now')-last_seen) AS age_s FROM ea_instances ORDER BY last_seen DESC;" | while read line; do
    age=$(echo "$line" | awk -F'|' '{print $3}')
    if [ -n "$age" ] && [ "$age" -gt "$FRESH" ]; then
      echo "[ALERT] EA stale: $line"; /root/HydraX-v2/tools/notifier.sh "EA stale: $line"
    else
      echo "OK $line"
    fi
  done
  echo "== Fires awaiting confirmation (> $STALE_FIRES s) =="
  sqlite3 "$DB" "
  SELECT fire_id, user_id, status, (strftime('%s','now')-created_at) AS age_s
  FROM fires
  WHERE status NOT IN ('FILLED','REJECTED','CANCELLED')
  ORDER BY created_at DESC LIMIT 50;
  " | while read line; do
    age=$(echo "$line" | awk -F'|' '{print $4}')
    st=$(echo "$line" | awk -F'|' '{print $3}')
    if [ "$st" = "" ] || [ "$st" = "PENDING" ] || [ "$st" = "ENQUEUED" ]; then
      if [ -n "$age" ] && [ "$age" -gt "$STALE_FIRES" ]; then
        echo "[ALERT] Fire stuck: $line"; /root/HydraX-v2/tools/notifier.sh "Fire stuck: $line"
      else
        echo "OK $line"
      fi
    else
      echo "OK $line"
    fi
  done
  sleep "$INTERVAL"
done