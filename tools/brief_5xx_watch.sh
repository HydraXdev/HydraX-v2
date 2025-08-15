#!/usr/bin/env bash
set -euo pipefail
BASE="${WEBAPP_PUBLIC_BASE:-http://127.0.0.1:8888}"
URL="$BASE/healthz"
CODES=()
for i in {1..12}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$URL" || echo "000")
  CODES+=("$CODE")
  sleep 5
done
FAILS=$(printf "%s\n" "${CODES[@]}" | egrep -c '^(5|000)')
if [ "$FAILS" -gt 1 ]; then
  echo "[WATCH:BRIEF-5XX] healthz error rate high: ${CODES[*]} base=$BASE"
fi