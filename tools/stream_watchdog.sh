#!/usr/bin/env bash
set -euo pipefail
R="${R:-redis-cli}"

# Check stream lag and consumer health
while true; do
    # Get stream length
    STREAM_LEN=$($R XLEN signals 2>/dev/null || echo 0)
    
    # Get pending messages count
    PENDING=$($R XPENDING signals relay 2>/dev/null | head -1 | awk '{print $1}' || echo 0)
    
    # Get last delivery timestamp for consumer
    LAST_DELIVERY=$($R XINFO CONSUMERS signals relay 2>/dev/null | grep -o 'idle [0-9]*' | awk '{print $2}' || echo 999999)
    
    # Alert if issues
    if [ "$STREAM_LEN" -gt 10000 ]; then
        echo "[ALERT] Stream length high: $STREAM_LEN messages"
    fi
    
    if [ "$PENDING" -gt 100 ]; then
        echo "[ALERT] High pending messages: $PENDING"
    fi
    
    if [ "$LAST_DELIVERY" -gt 120000 ]; then
        echo "[ALERT] Consumer idle for $(($LAST_DELIVERY/1000))s"
    fi
    
    echo "[WATCHDOG] Stream: $STREAM_LEN msgs | Pending: $PENDING | Idle: $(($LAST_DELIVERY/1000))s"
    sleep 30
done