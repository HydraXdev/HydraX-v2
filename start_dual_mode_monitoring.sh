#!/bin/bash
"""
BITTEN Dual Mode Monitoring Startup Script
Starts enhanced signal outcome monitor and dashboard
"""

echo "🚀 Starting BITTEN Dual Mode Monitoring System..."
echo "=================================="

# Set working directory
cd /root/HydraX-v2

echo "📊 Starting Enhanced Signal Outcome Monitor..."
python3 signal_outcome_monitor.py &
MONITOR_PID=$!
echo "   Signal Outcome Monitor started (PID: $MONITOR_PID)"

# Give monitor time to initialize
sleep 3

echo ""
echo "🎯 Starting Dual Mode Dashboard..."
echo "   Press Ctrl+C to stop both processes"
echo "=================================="
echo ""

# Start dashboard in foreground (so Ctrl+C works)
python3 dual_mode_dashboard.py

# When dashboard exits, kill the monitor too
echo ""
echo "🛑 Stopping Signal Outcome Monitor..."
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

echo "✅ Dual Mode Monitoring System stopped"
