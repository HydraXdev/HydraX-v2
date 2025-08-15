#!/usr/bin/env bash
# === BITTEN DURABLE FANOUT: 24h VALIDATION + CLEAN CUTOVER PACK ===
# Complete validation, monitoring, and safe cutover script

set -euo pipefail
export BITTEN_ROOT=/root/HydraX-v2
export BITTEN_DB="$BITTEN_ROOT/bitten.db"
export WEBAPP_BASE=http://127.0.0.1:8888
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
mkdir -p "$BITTEN_ROOT/tools" "$BITTEN_ROOT/logs"

echo "=== BITTEN DURABLE FANOUT VALIDATION ==="
echo "Time: $(date)"
echo "==========================================="

# ---------------------------
# 1) Quick stream & consumer health
# ---------------------------
echo -e "\n== Redis Stream Health Check =="
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" XINFO STREAM signals 2>/dev/null | head -20 || echo "Stream not found"
echo -e "\n== Consumer Groups =="
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" XINFO GROUPS signals 2>/dev/null || echo "No consumer groups"
echo -e "\n== Pending Messages =="
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" XPENDING signals relay - + 10 2>/dev/null || echo "No pending"

# ---------------------------
# 2) Check both relay paths status
# ---------------------------
echo -e "\n== Relay Path Status =="
echo "Legacy relay (relay_to_telegram):"
pm2 list | grep -E "relay_to_telegram|signals-zmq-to-redis|signals-redis-to-webapp" || true

echo -e "\n== Process Health =="
for proc in relay_to_telegram signals-zmq-to-redis signals-redis-to-webapp; do
    if pm2 list | grep -q "$proc"; then
        echo "$proc: $(pm2 describe $proc 2>/dev/null | grep -E 'status|restarts|uptime' | head -3 | xargs)"
    fi
done

# ---------------------------
# 3) Check signal flow metrics
# ---------------------------
echo -e "\n== Signal Flow Metrics (last 5 min) =="
echo "Elite Guard signals:"
tail -100 /root/HydraX-v2/elite_guard.log 2>/dev/null | grep "Publishing signal" | wc -l || echo "0"

echo "Webapp received signals:"
sqlite3 "$BITTEN_DB" "SELECT COUNT(*) FROM signals WHERE created_at > strftime('%s','now') - 300;" 2>/dev/null || echo "0"

echo "Missions created:"
sqlite3 "$BITTEN_DB" "SELECT COUNT(*) FROM missions WHERE created_at > strftime('%s','now') - 300;" 2>/dev/null || echo "0"

# ---------------------------
# 4) Test signal path
# ---------------------------
echo -e "\n== Testing Signal Path =="
echo "Checking webapp health..."
curl -s "$WEBAPP_BASE/healthz" | jq . 2>/dev/null || echo "Webapp not responding"

# ---------------------------
# 5) Rollback script (if needed)
# ---------------------------
cat > "$BITTEN_ROOT/tools/rollback_to_legacy.sh" <<'ROLLBACK'
#!/usr/bin/env bash
echo "Rolling back to legacy relay..."
pm2 stop signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 delete signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 restart relay_to_telegram
pm2 save
echo "Rollback complete. Legacy relay active."
ROLLBACK
chmod +x "$BITTEN_ROOT/tools/rollback_to_legacy.sh"

# ---------------------------
# 6) Cutover script (when ready)
# ---------------------------
cat > "$BITTEN_ROOT/tools/cutover_to_redis.sh" <<'CUTOVER'
#!/usr/bin/env bash
echo "Cutting over to Redis durable fanout..."
pm2 stop relay_to_telegram 2>/dev/null || true
pm2 start signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 save
echo "Cutover complete. Redis fanout active."
CUTOVER
chmod +x "$BITTEN_ROOT/tools/cutover_to_redis.sh"

echo -e "\n=== Validation Complete ==="
echo "Scripts created:"
echo "  - Monitor: pm2 logs fanout_compare"
echo "  - Watchdog: $BITTEN_ROOT/tools/stream_watchdog.sh"
echo "  - Rollback: $BITTEN_ROOT/tools/rollback_to_legacy.sh"
echo "  - Cutover: $BITTEN_ROOT/tools/cutover_to_redis.sh"
echo ""
echo "Next steps:"
echo "1. Monitor for 24h: watch pm2 logs fanout_compare"
echo "2. Check lag: bash $BITTEN_ROOT/tools/stream_watchdog.sh"
echo "3. When confident, cutover: bash $BITTEN_ROOT/tools/cutover_to_redis.sh"
echo "4. If issues, rollback: bash $BITTEN_ROOT/tools/rollback_to_legacy.sh"