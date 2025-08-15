#!/usr/bin/env bash
set -euo pipefail
MSG="$*"
STAMP="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"
PAYLOAD="[$STAMP] $MSG"
ok=0

# Telegram notification
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${PAYLOAD}" >/dev/null && ok=1 || true
fi

# Slack notification
if [ $ok -eq 0 ] && [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  curl -fsS -X POST -H 'Content-type: application/json' \
    --data "{\"text\":$(printf '%s' "$PAYLOAD" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
    "$SLACK_WEBHOOK_URL" >/dev/null && ok=1 || true
fi

# Log fallback
if [ $ok -eq 0 ]; then
  echo "[NOTIFY-LOG] $PAYLOAD" >> /root/HydraX-v2/logs/pager.log
fi