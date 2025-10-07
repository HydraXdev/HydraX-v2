#!/bin/bash
# Process Health Monitor
# Checks critical BITTEN system processes and ZMQ port bindings
# Auto-restarts failed processes if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🏥 BITTEN Process Health Check"
echo "==============================="
echo ""

# Critical processes to monitor
CRITICAL_PROCESSES=(
    "elite_guard_with_citadel.py"
    "webapp_server_optimized.py"
    "command_router.py"
    "confirm_listener_v207.py"
    "zmq_telemetry_bridge_debug.py"
)

# Critical ZMQ ports
CRITICAL_PORTS=(
    "5555"  # Command routing
    "5556"  # Market data ingestion
    "5557"  # Signal publishing
    "5558"  # Trade confirmations
    "5560"  # Market data relay
    "8888"  # WebApp API
)

# Check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null 2>&1; then
        local pid=$(pgrep -f "$process_name")
        local uptime=$(ps -p "$pid" -o etime= | xargs)
        echo "✅ $process_name (PID: $pid, Uptime: $uptime)"
        return 0
    else
        echo "❌ $process_name - NOT RUNNING"
        return 1
    fi
}

# Check if port is bound
check_port() {
    local port=$1
    if ss -tuln | grep -q ":$port "; then
        local process=$(ss -tulpen | grep ":$port " | awk '{print $NF}' | head -1)
        echo "✅ Port $port - BOUND ($process)"
        return 0
    else
        echo "❌ Port $port - NOT BOUND"
        return 1
    fi
}

# Check PM2 processes
check_pm2() {
    if command -v pm2 &> /dev/null; then
        echo "📊 PM2 Process Status:"
        echo "---------------------"
        pm2 jlist 2>/dev/null | jq -r '.[] | "  \(.name): \(.pm2_env.status) (PID: \(.pid // "N/A"))"' 2>/dev/null || pm2 list --no-color | head -20
        echo ""
    else
        echo "⚠️  PM2 not available"
    fi
}

# Process checks
echo "🔍 Critical Process Status:"
echo "---------------------------"
FAILED_PROCESSES=()
for process in "${CRITICAL_PROCESSES[@]}"; do
    if ! check_process "$process"; then
        FAILED_PROCESSES+=("$process")
    fi
done
echo ""

# Port checks
echo "🔌 Critical Port Bindings:"
echo "-------------------------"
FAILED_PORTS=()
for port in "${CRITICAL_PORTS[@]}"; do
    if ! check_port "$port"; then
        FAILED_PORTS+=("$port")
    fi
done
echo ""

# PM2 status
check_pm2

# Memory usage
echo "💾 System Resource Usage:"
echo "------------------------"
free -h | grep -E "^Mem|^Swap"
echo ""

# Elite Guard specific check
echo "🎯 Elite Guard Signal Status:"
echo "-----------------------------"
if [ -f "$PROJECT_ROOT/comprehensive_tracking.jsonl" ]; then
    RECENT_SIGNALS=$(tail -10 "$PROJECT_ROOT/comprehensive_tracking.jsonl" 2>/dev/null | wc -l)
    LAST_SIGNAL=$(tail -1 "$PROJECT_ROOT/comprehensive_tracking.jsonl" 2>/dev/null | jq -r '.signal_id // "N/A"' 2>/dev/null || echo "N/A")
    echo "Recent signals (last 10): $RECENT_SIGNALS"
    echo "Latest signal: $LAST_SIGNAL"
else
    echo "⚠️  Signal tracking file not found"
fi
echo ""

# EA Connection check
echo "🤖 EA Connection Status:"
echo "-----------------------"
if [ -f "$PROJECT_ROOT/bitten.db" ]; then
    sqlite3 "$PROJECT_ROOT/bitten.db" "SELECT target_uuid, user_id, (strftime('%s','now') - last_seen) AS age_seconds FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';" 2>/dev/null | while IFS='|' read -r uuid user age; do
        if [ "$age" -lt 120 ]; then
            echo "✅ $uuid connected (age: ${age}s)"
        else
            echo "⚠️  $uuid stale (age: ${age}s)"
        fi
    done
else
    echo "⚠️  Database not found"
fi
echo ""

# Summary
echo "📋 Health Summary:"
echo "-----------------"
if [ ${#FAILED_PROCESSES[@]} -eq 0 ] && [ ${#FAILED_PORTS[@]} -eq 0 ]; then
    echo "✅ All critical systems operational"
    exit 0
else
    echo "⚠️  Issues detected:"
    if [ ${#FAILED_PROCESSES[@]} -gt 0 ]; then
        echo "   Failed processes: ${FAILED_PROCESSES[*]}"
    fi
    if [ ${#FAILED_PORTS[@]} -gt 0 ]; then
        echo "   Unbound ports: ${FAILED_PORTS[*]}"
    fi
    echo ""
    echo "💡 TIP: Check logs for failed processes:"
    echo "   pm2 logs [process-name] --lines 50"
    exit 1
fi
