#!/usr/bin/env bash
set -euo pipefail

# === BITTEN Redis System Health Check ===

echo "=== BITTEN REDIS SYSTEM STATUS ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo

# Check Redis connectivity
echo "[ Redis Server ]"
if redis-cli ping > /dev/null 2>&1; then
  echo "✓ Redis server: ONLINE"
  redis_info=$(redis-cli INFO server | grep -E "redis_version|uptime_in_seconds" | tr '\r' ' ')
  echo "  $redis_info"
else
  echo "✗ Redis server: OFFLINE"
  exit 1
fi
echo

# Check signal stream
echo "[ Signal Stream ]"
signal_len=$(redis-cli xlen signals 2>/dev/null || echo "0")
echo "  Length: $signal_len messages (maxlen=1000)"
last_signal=$(redis-cli xrevrange signals + - COUNT 1 2>/dev/null | head -1 || echo "none")
if [ "$last_signal" != "none" ] && [ -n "$last_signal" ]; then
  echo "  Last ID: $last_signal"
  last_ts=$(echo "$last_signal" | cut -d'-' -f1)
  age=$(($(date +%s)000 - last_ts))
  echo "  Age: $(($age / 1000))s ago"
else
  echo "  Last signal: No signals yet"
fi
echo

# Check fire streams
echo "[ Fire Streams ]"
fire_streams=$(redis-cli --raw keys "fire.*" 2>/dev/null | wc -l)
echo "  Active fire streams: $fire_streams"
if [ "$fire_streams" -gt 0 ]; then
  redis-cli --raw keys "fire.*" 2>/dev/null | head -5 | while read stream; do
    len=$(redis-cli xlen "$stream" 2>/dev/null || echo "0")
    echo "    $stream: $len messages"
  done
fi
echo

# Check consumer groups
echo "[ Consumer Groups ]"
if redis-cli xinfo groups signals >/dev/null 2>&1; then
  echo "  Signals consumer group 'relay':"
  pending=$(redis-cli xinfo groups signals 2>/dev/null | grep -A3 "name=relay" | grep "pending" | awk '{print $2}' || echo "0")
  echo "    Pending messages: $pending"
fi
echo

# Check bridge processes
echo "[ Bridge Processes ]"
pm2_list=$(pm2 list --no-color 2>/dev/null || echo "")
if echo "$pm2_list" | grep -q "signals_zmq_to_redis.*online"; then
  echo "✓ signals_zmq_to_redis: ONLINE"
else
  echo "✗ signals_zmq_to_redis: OFFLINE/ERROR"
fi

if echo "$pm2_list" | grep -q "signals_redis_to_webapp.*online"; then
  echo "✓ signals_redis_to_webapp: ONLINE"
else
  echo "✗ signals_redis_to_webapp: OFFLINE/ERROR"
fi

if echo "$pm2_list" | grep -q "fire_redis_bridge.*online"; then
  echo "✓ fire_redis_bridge: ONLINE"
else
  echo "✗ fire_redis_bridge: OFFLINE/ERROR"
fi
echo

# Check watchdogs
echo "[ Watchdog Processes ]"
if echo "$pm2_list" | grep -q "watchdog_ticks_vs_signals.*online"; then
  echo "✓ watchdog_ticks_vs_signals: ONLINE"
else
  echo "✗ watchdog_ticks_vs_signals: OFFLINE/ERROR"
fi

if echo "$pm2_list" | grep -q "watchdog_ea_and_fires.*online"; then
  echo "✓ watchdog_ea_and_fires: ONLINE"
else
  echo "✗ watchdog_ea_and_fires: OFFLINE/ERROR"
fi
echo

# Check pager alerts
echo "[ Pager Alerts ]"
if [ -f /root/HydraX-v2/logs/pager.log ]; then
  recent_alerts=$(tail -100 /root/HydraX-v2/logs/pager.log 2>/dev/null | grep "$(date -u '+%Y-%m-%d')" | wc -l || echo "0")
  echo "  Alerts today: $recent_alerts"
  last_alert=$(tail -1 /root/HydraX-v2/logs/pager.log 2>/dev/null | head -1)
  if [ -n "$last_alert" ]; then
    echo "  Last alert: $(echo "$last_alert" | cut -d']' -f2- | cut -c2-50)..."
  fi
else
  echo "  No pager log file yet"
fi

# Environment check
echo
echo "[ Notification Config ]"
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "✓ Telegram bot token: SET"
else
  echo "  Telegram bot token: NOT SET (alerts will log to file)"
fi
if [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "✓ Telegram chat ID: SET"
else
  echo "  Telegram chat ID: NOT SET"
fi
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  echo "✓ Slack webhook: SET"
else
  echo "  Slack webhook: NOT SET"
fi

echo
echo "=== END STATUS CHECK ==="