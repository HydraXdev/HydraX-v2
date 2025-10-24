#!/bin/bash
# ZMQ Bridge Monitor & Auto-Restart
# Ensures zmq_gateway is always running and alerts if it goes down

# Add PM2 to PATH for cron environment
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

GATEWAY_PROCESS="zmq_gateway"
GATEWAY_SCRIPT="/root/HydraX-v2/services/zmq_gateway/main.py"
LOG_FILE="/root/HydraX-v2/logs/bridge_monitor.log"
ALERT_FILE="/root/HydraX-v2/BRIDGE_DOWN_ALERT.txt"

# Check if zmq_gateway PM2 process is running
if ! pm2 list | grep -q "$GATEWAY_PROCESS.*online"; then
    echo "$(date) - ❌ ZMQ Gateway DOWN! Attempting restart..." | tee -a "$LOG_FILE"

    # Create alert file for system status page
    echo "ZMQ Gateway went down at $(date)" > "$ALERT_FILE"
    echo "Market data flow interrupted - no new signals possible" >> "$ALERT_FILE"
    echo "Automatic restart attempted" >> "$ALERT_FILE"

    # Restart the gateway
    pm2 restart "$GATEWAY_PROCESS" 2>&1 | tee -a "$LOG_FILE"

    # Wait 3 seconds and verify
    sleep 3

    if pm2 list | grep -q "$GATEWAY_PROCESS.*online"; then
        echo "$(date) - ✅ ZMQ Gateway restarted successfully" | tee -a "$LOG_FILE"
        rm -f "$ALERT_FILE"  # Clear alert
    else
        echo "$(date) - 🚨 FAILED to restart ZMQ Gateway! Manual intervention required!" | tee -a "$LOG_FILE"
    fi
else
    # Gateway is running - check if alert file exists and clear it
    if [ -f "$ALERT_FILE" ]; then
        echo "$(date) - ✅ ZMQ Gateway back online, clearing alert" >> "$LOG_FILE"
        rm -f "$ALERT_FILE"
    fi
fi

# Also check Elite Guard connection to gateway
ELITE_GUARD_PID=$(pm2 list | grep elite_guard | grep online | awk '{print $10}')
if [ -n "$ELITE_GUARD_PID" ]; then
    # Check if Elite Guard has recent market data (last 60 seconds)
    LAST_TICK=$(pm2 logs elite_guard --lines 50 --nostream 2>/dev/null | grep "TICK:" | tail -1)
    if [ -z "$LAST_TICK" ]; then
        echo "$(date) - ⚠️  Elite Guard not receiving ticks, restarting..." | tee -a "$LOG_FILE"
        pm2 restart elite_guard 2>&1 | tee -a "$LOG_FILE"
    fi
fi
