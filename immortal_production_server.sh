#!/bin/bash
#
# Immortal Production TCP Command Server
# Automatically restarts on crash, logs everything
#

SERVER_SCRIPT="/root/HydraX-v2/production_tcp_command_server.py"
LOG_DIR="/var/log/hydrasocket"
LOG_FILE="$LOG_DIR/tcp_command_server.log"
PID_FILE="/var/run/tcp_command_server.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to rotate log if it gets too big (>100MB)
rotate_log() {
    if [ -f "$LOG_FILE" ]; then
        SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$SIZE" -gt 104857600 ]; then
            mv "$LOG_FILE" "$LOG_FILE.$(date +%Y%m%d_%H%M%S)"
            echo "$(date) | Log rotated due to size" > "$LOG_FILE"
        fi
    fi
}

echo "===============================================" | tee -a "$LOG_FILE"
echo "IMMORTAL TCP COMMAND SERVER STARTING" | tee -a "$LOG_FILE"
echo "$(date)" | tee -a "$LOG_FILE"
echo "===============================================" | tee -a "$LOG_FILE"

# Main immortal loop
while true; do
    rotate_log

    echo "$(date) | [IMMORTAL] Starting TCP Command Server..." | tee -a "$LOG_FILE"

    # Run the server and capture its PID
    python3 -u "$SERVER_SCRIPT" 2>&1 | tee -a "$LOG_FILE" &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"

    echo "$(date) | [IMMORTAL] Server started with PID $SERVER_PID" | tee -a "$LOG_FILE"

    # Wait for the server process to exit
    wait $SERVER_PID
    EXIT_CODE=$?

    rm -f "$PID_FILE"

    echo "$(date) | [IMMORTAL] Server exited with code $EXIT_CODE" | tee -a "$LOG_FILE"

    # Check if we should restart
    if [ "$EXIT_CODE" -eq 0 ]; then
        echo "$(date) | [IMMORTAL] Clean exit detected, checking for restart..." | tee -a "$LOG_FILE"
    else
        echo "$(date) | [IMMORTAL] Crash detected! Restarting in 3 seconds..." | tee -a "$LOG_FILE"
    fi

    sleep 3
done