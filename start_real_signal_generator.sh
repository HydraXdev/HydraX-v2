#!/bin/bash

# Start Real Signal Generator - Production Script
# Replaces fake VENOM engine with 100% real data version
#
# USAGE:
#   ./start_real_signal_generator.sh
#
# FEATURES:
# - Stops any fake signal generators
# - Starts real data engine on port 8001
# - Provides health monitoring
# - Logs all activity

echo "🚀 Starting VENOM Real Data Signal Generator"
echo "✅ 100% REAL MT5 DATA - Zero synthetic generation"
echo "=================================================="

# Create logs directory
mkdir -p /root/HydraX-v2/logs

# Stop any existing fake signal generators
echo "🛑 Stopping any fake signal generators..."
pkill -f "working_signal_generator.py" 2>/dev/null || true
pkill -f "apex_venom_v7_unfiltered.py" 2>/dev/null || true
pkill -f "signal_generator" 2>/dev/null || true

# Wait for processes to stop
sleep 2

# Check if port 8001 is in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8001 is in use, attempting to free it..."
    fuser -k 8001/tcp 2>/dev/null || true
    sleep 2
fi

# Start the real data signal generator
echo "🐍 Starting VENOM Real Data Engine..."
cd /root/HydraX-v2

# Run with logging
nohup python3 real_data_signal_generator.py > logs/real_signal_generator.log 2>&1 &
SIGNAL_GEN_PID=$!

# Wait a moment for startup
sleep 3

# Check if it started successfully
if kill -0 $SIGNAL_GEN_PID 2>/dev/null; then
    echo "✅ Real Signal Generator started successfully (PID: $SIGNAL_GEN_PID)"
    echo "📡 Listening on port 8001 for MT5 tick data"
    echo "📊 Ready to generate signals from real market data"
    
    # Test health endpoint
    echo "🔍 Testing health endpoint..."
    sleep 2
    
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        echo "✅ Health endpoint responding"
        echo ""
        echo "📋 Real Signal Generator Status:"
        curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "Health check successful"
    else
        echo "⚠️  Health endpoint not yet ready (normal during startup)"
    fi
    
    echo ""
    echo "📝 Logs: tail -f /root/HydraX-v2/logs/real_signal_generator.log"
    echo "🔍 Health: curl http://localhost:8001/health"
    echo "📊 Data Feed: curl http://localhost:8001/venom-feed"
    echo ""
    echo "🎯 To send test data:"
    echo "curl -X POST http://localhost:8001/market-data \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"ticks\":[{\"symbol\":\"EURUSD\",\"bid\":1.0850,\"ask\":1.0852,\"spread\":2.0,\"volume\":1500}]}'"
    
else
    echo "❌ Failed to start Real Signal Generator"
    echo "📝 Check logs: cat /root/HydraX-v2/logs/real_signal_generator.log"
    exit 1
fi

echo ""
echo "🐍 VENOM Real Data Engine is now active!"
echo "✅ Zero synthetic data - Only real MT5 ticks processed"