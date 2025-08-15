#!/usr/bin/env bash
set -euo pipefail
BASE="${WEBAPP_BASE:-http://127.0.0.1:8888}"
UUID="${1:-COMMANDER_DEV_001}"
SYMB="${2:-EURUSD}"
curl -s -X POST "$BASE/api/fire" \
  -H 'Content-Type: application/json' \
  --data "{\"type\":\"fire\",\"fire_id\":\"smoke_$(date +%s)\",\"target_uuid\":\"$UUID\",\"symbol\":\"$SYMB\",\"direction\":\"BUY\",\"entry\":1.1000,\"sl\":1.0900,\"tp\":1.1100,\"lot\":0.01,\"dry_run\":true}" \
  | jq .