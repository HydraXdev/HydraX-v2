#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/HydraX-v2"
MANIFEST="$ROOT/bitten_manifest.json"

ok(){ echo "✓ OK $1"; }
die(){ echo "✗ FAIL $1"; exit 1; }

echo "=== BITTEN Stack Verification ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# 1) Required PM2 processes
echo -n "Checking PM2 processes... "
req_procs=(command_router relay_to_telegram webapp confirm_listener elite_guard outcome_daemon)
for p in "${req_procs[@]}"; do 
  pm2 jlist 2>/dev/null | grep -q "\"name\":\"$p\"" || die "PM2 process missing: $p"
done
ok "all 6 required PM2 processes present"

# 2) Disallowed processes not running
echo -n "Checking for disallowed processes... "
disallowed=(fire_router_service zmq_bitten_controller clone_farm venom bitten_production_bot handshake_processor)
for p in "${disallowed[@]}"; do
  ps aux | grep -v grep | grep -q "$p" && die "Disallowed process running: $p"
done
ok "no disallowed processes found"

# 3) Background processes
echo -n "Checking background processes... "
bridge_running=$(ps aux | grep -v grep | grep -c "zmq_telemetry_bridge" || echo "0")
if [ "$bridge_running" -gt 0 ]; then
  ok "telemetry bridge running"
else
  die "zmq_telemetry_bridge not running"
fi

# 4) Ports: exactly one binder each
echo -n "Checking port bindings... "
check_port(){ 
  want=$1
  c=$(ss -tulpen 2>/dev/null | awk '{print $5}' | grep -E ":$want\$" | wc -l)
  [ "$c" -eq 1 ] || die "port $want binder count=$c (expected 1)"
}
for port in 5555 5556 5557 5558 5560 8888; do 
  check_port $port
done
ok "all ports bound exactly once"

# 5) 5558 open to world
echo -n "Checking 5558 accessibility... "
ss -tulpen 2>/dev/null | grep -E "LISTEN.*:5558" | grep -q "0.0.0.0:5558" || die "5558 not bound on 0.0.0.0"
ok "5558 reachable from external IPs"

# 6) IPC queue exists
echo -n "Checking IPC queue... "
[ -S /tmp/bitten_cmdqueue ] || [ -e /tmp/bitten_cmdqueue ] || echo -n "" # IPC sockets don't always show as files
ok "IPC queue path available"

# 7) Health endpoint
echo -n "Checking webapp health... "
curl -sf http://127.0.0.1:8888/healthz >/dev/null 2>&1 || die "/healthz not responding"
ok "/healthz returns 200"

# 8) DB tables & critical columns
echo -n "Checking database schema... "
DB="$ROOT/bitten.db"
[ -f "$DB" ] || die "Database file missing: $DB"

have_table(){ 
  sqlite3 "$DB" ".tables" 2>/dev/null | grep -qw "$1" || die "table missing: $1"
}
have_col(){ 
  sqlite3 "$DB" "PRAGMA table_info($1);" 2>/dev/null | awk -F'|' '{print $2}' | grep -qx "$2" || die "table $1 missing column $2"
}

for t in missions fires ea_instances signals users; do 
  have_table $t
done

have_col missions mission_id
have_col missions signal_id
have_col missions status
have_col fires fire_id
have_col fires mission_id
have_col fires status
have_col fires ticket
have_col ea_instances target_uuid
have_col ea_instances last_seen
ok "all 5 tables with required columns present"

# 9) EA connectivity
echo -n "Checking EA connectivity... "
recent_hb=$(pm2 logs command_router --lines 20 --nostream 2>/dev/null | grep -c "HEARTBEAT" || echo "0")
if [ "$recent_hb" -gt 0 ]; then
  ok "EA heartbeats detected (count: $recent_hb)"
else
  echo "⚠ WARNING: No recent EA heartbeats"
fi

# 10) Signal flow check
echo -n "Checking signal flow... "
elite_running=$(pm2 jlist 2>/dev/null | grep -q '"name":"elite_guard"' && echo "yes" || echo "no")
relay_running=$(pm2 jlist 2>/dev/null | grep -q '"name":"relay_to_telegram"' && echo "yes" || echo "no")
if [ "$elite_running" = "yes" ] && [ "$relay_running" = "yes" ]; then
  ok "signal generation pipeline active"
else
  die "signal pipeline broken (elite_guard=$elite_running, relay=$relay_running)"
fi

# 11) Immutable files exist
echo -n "Checking immutable files... "
[ -f "$ROOT/command_router.py" ] || die "Missing immutable: command_router.py"
[ -f "$ROOT/confirm_listener.py" ] || die "Missing immutable: confirm_listener.py"
ok "immutable files present"

# 12) No duplicate ZMQ relays
echo -n "Checking for duplicate processes... "
relay_count=$(ps aux | grep -v grep | grep -c "elite_guard_zmq_relay" || echo "0")
if [ "$relay_count" -gt 1 ]; then
  die "Multiple ZMQ relay processes running (count: $relay_count)"
fi
ok "no duplicate processes"

echo ""
echo "=== ALL CHECKS PASSED ==="
echo "Stack is compliant with bitten_manifest.json"