#!/bin/bash
# 🚀 Elite Guard System Startup Script
# Ensures correct startup order for EA → Elite Guard data flow

echo "🚀 Starting Elite Guard System..."
echo "================================"

# Kill any existing processes
echo "🔄 Cleaning up existing processes..."
pkill -f zmq_telemetry_bridge_debug
pkill -f elite_guard_with_citadel
sleep 2

# Start telemetry bridge FIRST (critical!)
echo "📡 Starting telemetry bridge..."
cd /root/HydraX-v2
nohup python3 zmq_telemetry_bridge_debug.py > /tmp/telemetry_bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 3

# Verify bridge is running
if ps -p $BRIDGE_PID > /dev/null; then
    echo "✅ Telemetry bridge started (PID: $BRIDGE_PID)"
else
    echo "❌ Failed to start telemetry bridge!"
    exit 1
fi

# Start Elite Guard
echo "🛡️ Starting Elite Guard..."
nohup python3 elite_guard_with_citadel.py > /tmp/elite_guard.log 2>&1 &
GUARD_PID=$!
sleep 3

# Verify Elite Guard is running
if ps -p $GUARD_PID > /dev/null; then
    echo "✅ Elite Guard started (PID: $GUARD_PID)"
else
    echo "❌ Failed to start Elite Guard!"
    exit 1
fi

# Check if WebApp is running
if ps aux | grep -q "[w]ebapp_server_optimized"; then
    echo "✅ WebApp already running"
else
    echo "⚠️ WebApp not running - start manually if needed"
fi

# Test data flow
echo ""
echo "🔍 Testing data flow..."
python3 -c "
import zmq
import sys
try:
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect('tcp://127.0.0.1:5560')
    subscriber.subscribe(b'')
    subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
    
    print('⏳ Waiting for tick data...')
    msg = subscriber.recv_json()
    print(f'✅ Data flowing! Received: {msg.get(\"symbol\")} @ {msg.get(\"bid\")}')
    sys.exit(0)
except zmq.error.Again:
    print('❌ No data received in 5 seconds - check EA is running')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

echo ""
echo "================================"
echo "📊 System Status:"
echo "- Telemetry Bridge: PID $BRIDGE_PID"
echo "- Elite Guard: PID $GUARD_PID"
echo "- Logs: /tmp/telemetry_bridge.log, /tmp/elite_guard.log"
echo ""
echo "📋 Next steps:"
echo "1. Ensure EA is running and connected"
echo "2. Monitor Elite Guard for pattern detection"
echo "3. Signals will appear in @bitten_signals group"
echo ""
echo "See /EA_DATA_FLOW_CONTRACT.md for troubleshooting"