#!/bin/bash
# Immortal wrapper for TCP Command Server
# Automatically restarts if it crashes

LOG_FILE="/var/log/tcp_command_server_immortal.log"

echo "$(date) | Starting Immortal TCP Command Server" | tee -a "$LOG_FILE"

while true; do
    echo "$(date) | [IMMORTAL] Starting TCP command server..." | tee -a "$LOG_FILE"

    python3 -u /root/HydraX-v2/tcp_command_server.py 2>&1 | tee -a "$LOG_FILE"

    EXIT_CODE=$?
    echo "$(date) | [IMMORTAL] Server exited with code $EXIT_CODE. Restarting in 3 seconds..." | tee -a "$LOG_FILE"
    sleep 3
done
