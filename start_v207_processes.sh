#!/bin/bash

echo "🚀 Starting v2.07H BITTEN processes..."
echo "======================================="

# Stop old versions first
echo "⏹️  Stopping old confirm_listener..."
pm2 stop confirm_listener 2>/dev/null

echo "⏹️  Stopping old telemetry_bridge..."
pm2 stop telemetry_bridge 2>/dev/null

# Start new v2.07H components
echo ""
echo "✅ Starting v2.07H confirm listener (handles all new message types)..."
pm2 start /root/HydraX-v2/confirm_listener_v207.py --name confirm_listener_v207 --interpreter python3

echo "✅ Starting v2.07H telemetry bridge (handles port 5560 metrics)..."
pm2 start /root/HydraX-v2/zmq_telemetry_bridge_v207.py --name telemetry_bridge_v207 --interpreter python3

# Restart webapp with v2.07H support
echo "🔄 Restarting webapp with v2.07H position tracking..."
pm2 restart webapp_main

echo ""
echo "📊 Checking process status..."
sleep 2
pm2 list | grep -E "confirm_listener|telemetry_bridge|webapp_main"

echo ""
echo "✅ v2.07H processes started!"
echo ""
echo "📋 Next steps:"
echo "1. Attach EA v2.07H to MT5"
echo "2. Verify all 4 sockets are connected (5555, 5556, 5558, 5560)"
echo "3. Check new API endpoints:"
echo "   - http://localhost:8888/api/v207/positions/COMMANDER_DEV_001"
echo "   - http://localhost:8888/api/v207/dashboard/COMMANDER_DEV_001"
echo "   - http://localhost:8888/api/v207/telemetry/COMMANDER_DEV_001"
echo ""
echo "📝 Monitor logs:"
echo "   pm2 logs confirm_listener_v207 --lines 20"
echo "   pm2 logs telemetry_bridge_v207 --lines 20"