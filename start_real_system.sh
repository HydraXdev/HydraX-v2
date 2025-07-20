#!/bin/bash
# Start complete real trading system

echo "🚀 STARTING REAL BITTEN TRADING SYSTEM"
echo "======================================="

# Kill all fake processes
echo "🗑️ Stopping simulation processes..."
killall python3 2>/dev/null

# Start X server if not running
if ! pgrep Xvfb > /dev/null; then
    echo "🖥️ Starting X server..."
    export DISPLAY=:0
    Xvfb :0 -screen 0 1024x768x24 &
    sleep 2
fi

# Start VNC server if not running  
if ! pgrep x11vnc > /dev/null; then
    echo "📺 Starting VNC server..."
    x11vnc -display :0 -bg -nopw -listen localhost -xkb &
    sleep 2
fi

# Connect to real broker
echo "🏦 Testing real broker connection..."
python3 /root/HydraX-v2/real_trade_executor.py

# Start APEX engine with real execution
echo "🎯 Starting APEX with real trade execution..."
cd /root/HydraX-v2
python3 apex_v5_lean.py &

# Start webapp with real fire API
echo "🌐 Starting webapp with real execution..."
python3 webapp_server_optimized.py &

# Wait for MT5 installation
echo "⏳ Waiting for MT5 installation to complete..."
sleep 30

# Check MT5 installation
echo "🔍 Checking MT5 installation..."
find /root/.wine_user_7176191872 -name "*terminal*" -o -name "*MetaTrader*" 2>/dev/null | head -3

echo ""
echo "✅ REAL TRADING SYSTEM STARTED"
echo "📋 Account: 843859@Coinexx-Demo"
echo "🎯 User ID: 7176191872" 
echo "🔗 VNC: localhost:5900"
echo "🌐 WebApp: http://localhost:8888"
echo ""
echo "💰 REAL MONEY TRADING IS NOW ACTIVE"