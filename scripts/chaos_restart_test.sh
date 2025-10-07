#!/bin/bash
# Chaos engineering test - process restart simulation

echo "🔥 CHAOS TEST: Process Restart Simulation"
echo "Time: $(date)"

# Get current PID
PID=$(pgrep -f "standalone_docs_server")
echo "Current server PID: $PID"

if [ -z "$PID" ]; then
    echo "❌ No server process found"
    exit 1
fi

# Record start time
START_TIME=$(date +%s)

# Kill the process
echo "Killing process $PID"
kill -9 $PID

# Wait for restart (simulated)
sleep 2

# Restart server
python3 standalone_docs_server.py > /tmp/chaos_restart.log 2>&1 &
NEW_PID=$!

# Wait for service to be ready
sleep 3

# Test recovery
if curl -s http://localhost:8888/healthz > /dev/null; then
    END_TIME=$(date +%s)
    RECOVERY_TIME=$((END_TIME - START_TIME))
    echo "✅ Recovery successful in ${RECOVERY_TIME}s"
    echo "New PID: $NEW_PID"

    if [ $RECOVERY_TIME -lt 30 ]; then
        echo "✅ Recovery time under 30s threshold"
        exit 0
    else
        echo "⚠️ Recovery time over 30s threshold"
        exit 1
    fi
else
    echo "❌ Recovery failed"
    exit 1
fi
