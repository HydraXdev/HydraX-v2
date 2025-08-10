#!/bin/bash
# BITTEN Core System Startup Script
# Auto-starts and monitors all critical processes

echo "🚀 BITTEN CORE SYSTEM STARTUP"
echo "================================"
date

cd /root/HydraX-v2

# Function to check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        echo "✅ $process_name is already running"
        return 0
    else
        echo "❌ $process_name is NOT running"
        return 1
    fi
}

# Function to start process if not running
start_if_needed() {
    local process_name=$1
    local start_command=$2
    local log_file=$3
    
    if ! check_process "$process_name"; then
        echo "🔄 Starting $process_name..."
        eval "$start_command > $log_file 2>&1 &"
        sleep 2
        if check_process "$process_name"; then
            echo "✅ $process_name started successfully"
        else
            echo "❌ Failed to start $process_name"
        fi
    fi
}

echo ""
echo "📡 Checking ZMQ Infrastructure..."
echo "--------------------------------"

# Check and start telemetry bridge
start_if_needed "zmq_telemetry_bridge" \
    "python3 zmq_telemetry_bridge_debug.py" \
    "telemetry_bridge.log"

# Check and start complete circuit
start_if_needed "complete_bitten_circuit" \
    "python3 /root/complete_bitten_circuit.py" \
    "complete_circuit.log"

echo ""
echo "🛡️ Checking Signal Processing Chain..."
echo "--------------------------------------"

# Elite Guard with immortality
start_if_needed "elite_guard_with_citadel" \
    "python3 elite_guard_with_citadel.py" \
    "elite_guard_immortal.log"

# ZMQ Relay
start_if_needed "elite_guard_zmq_relay" \
    "python3 elite_guard_zmq_relay.py" \
    "zmq_relay.log"

# Final Fire Publisher
start_if_needed "final_fire_publisher" \
    "python3 final_fire_publisher.py" \
    "fire_publisher.log"

echo ""
echo "🌐 Checking User Interfaces..."
echo "------------------------------"

# Telegram Bot
start_if_needed "bitten_production_bot" \
    "python3 /root/HydraX-v2/bitten_production_bot.py" \
    "telegram_bot.log"

# WebApp Server
start_if_needed "webapp_server_optimized" \
    "python3 webapp_server_optimized.py" \
    "webapp.log"

# Commander Throne
start_if_needed "commander_throne" \
    "python3 commander_throne.py" \
    "throne.log"

echo ""
echo "📊 System Status Check..."
echo "------------------------"

# Count running processes
PROCESS_COUNT=$(ps aux | grep -E "bitten|webapp|zmq|telemetry|throne|elite|fire" | grep -v grep | wc -l)
echo "Total BITTEN processes running: $PROCESS_COUNT"

# Check ZMQ ports
PORT_COUNT=$(netstat -tuln | grep -E "5555|5556|5557|5558|5560|8888|8899" | wc -l)
echo "Active ZMQ/Web ports: $PORT_COUNT"

# Check EA connection
if netstat -an | grep -q "185.244.67.11"; then
    echo "✅ EA Connected from 185.244.67.11"
else
    echo "⚠️ EA not connected - waiting for connection..."
fi

echo ""
echo "🎯 BITTEN Core System Startup Complete"
echo "======================================"

# Optional: Monitor mode
if [ "$1" == "--monitor" ]; then
    echo ""
    echo "📊 Entering monitoring mode (Ctrl+C to exit)..."
    while true; do
        sleep 30
        echo -n "."
        # Check if Elite Guard is still alive
        if ! pgrep -f "elite_guard_with_citadel" > /dev/null; then
            echo ""
            echo "⚠️ Elite Guard died - restarting..."
            python3 elite_guard_with_citadel.py > elite_guard_immortal.log 2>&1 &
        fi
    done
fi