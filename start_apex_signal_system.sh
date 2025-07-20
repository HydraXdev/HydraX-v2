#!/bin/bash
# Start APEX Signal Delivery System

echo "🚀 Starting APEX Signal Delivery System..."

# Set working directory
cd /root/HydraX-v2

# Check if APEX is running
if ! pgrep -f "apex_v5_live_real.py" > /dev/null; then
    echo "⚠️  APEX engine not running. Starting..."
    python3 apex_v5_live_real.py > apex_v5_live_real.log 2>&1 &
    sleep 5
else
    echo "✅ APEX engine already running"
fi

# Check if telegram connector is running
if ! pgrep -f "apex_telegram_connector.py" > /dev/null; then
    echo "⚠️  Telegram connector not running. Starting..."
    python3 apex_telegram_connector.py > apex_telegram_connector.log 2>&1 &
    sleep 2
else
    echo "✅ Telegram connector already running"
fi

# Stop any existing signal delivery
pkill -f "apex_signal_delivery.py" 2>/dev/null

# Start signal delivery system
echo "🔥 Starting Signal Delivery System..."
python3 apex_signal_delivery.py > apex_signal_delivery.log 2>&1 &

echo "✅ APEX Signal System started!"
echo ""
echo "📊 Monitor logs with:"
echo "  tail -f apex_v5_live_real.log      # APEX engine"
echo "  tail -f apex_signal_delivery.log   # Signal routing"
echo "  tail -f apex_telegram_connector.log # Telegram alerts"
echo ""
echo "🛑 Stop all with: pkill -f apex"