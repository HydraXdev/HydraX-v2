# HYDRASOCKET v1 Chaos Engineering Tests

## Overview

Chaos engineering tests validate system resilience under failure conditions. Run these tests regularly to ensure robust operation.

## Test Schedule

- **Weekly**: Basic chaos tests (router kill, network partition)
- **Monthly**: Advanced chaos tests (database corruption, resource exhaustion)
- **Quarterly**: Full disaster recovery simulation

## Test Categories

### 1. Process Failures

#### Test: Router Process Kill

**Objective**: Verify automatic restart and state recovery

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Router Process Kill"

# Get current metrics
INITIAL_WS=$(curl -s http://localhost:8888/api/health | jq .ws_clients)
echo "Initial WebSocket clients: $INITIAL_WS"

# Kill router process
PID=$(pgrep -f "hydrasocket-router")
echo "Killing process $PID"
kill -9 $PID

# Wait for PM2 restart
sleep 15

# Verify recovery
if curl -s http://localhost:8888/healthz > /dev/null; then
    echo "✅ Process restart successful"

    # Check WebSocket recovery
    sleep 10
    RECOVERED_WS=$(curl -s http://localhost:8888/api/health | jq .ws_clients)
    echo "Recovered WebSocket clients: $RECOVERED_WS"

    if [ "$RECOVERED_WS" -ge "$((INITIAL_WS * 80 / 100))" ]; then
        echo "✅ WebSocket recovery successful (80%+ retained)"
    else
        echo "⚠️ WebSocket recovery partial"
    fi
else
    echo "❌ Process restart failed"
    exit 1
fi
```

#### Test: Database Lock Simulation

**Objective**: Test database recovery under lock conditions

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Database Lock Simulation"

DB_PATH="/root/HydraX-v2/event_bus/bitten_events.db"

# Create long-running transaction to lock database
sqlite3 "$DB_PATH" "BEGIN EXCLUSIVE; SELECT COUNT(*) FROM events;" &
LOCK_PID=$!

sleep 5

# Test API during lock
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/v1/events?account_id=TEST)

if [ "$HTTP_CODE" = "500" ] || [ "$HTTP_CODE" = "503" ]; then
    echo "✅ Service correctly handles database lock"
else
    echo "⚠️ Unexpected response during lock: $HTTP_CODE"
fi

# Release lock
kill $LOCK_PID
sleep 2

# Verify recovery
if curl -s http://localhost:8888/healthz > /dev/null; then
    echo "✅ Database lock recovery successful"
else
    echo "❌ Database lock recovery failed"
    exit 1
fi
```

### 2. Network Failures

#### Test: Port Blocking

**Objective**: Test resilience to ZMQ port failures

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: ZMQ Port Blocking"

# Block ZMQ ports with iptables
sudo iptables -A INPUT -p tcp --dport 5558 -j DROP
sudo iptables -A INPUT -p tcp --dport 5560 -j DROP

echo "Blocked ZMQ ports 5558, 5560"

# Monitor service behavior
sleep 30

# Check if service handles gracefully
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/healthz)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Service survives ZMQ port blocking"
else
    echo "❌ Service affected by ZMQ port blocking: $HTTP_CODE"
fi

# Restore network
sudo iptables -D INPUT -p tcp --dport 5558 -j DROP
sudo iptables -D INPUT -p tcp --dport 5560 -j DROP

echo "Restored ZMQ ports"

# Verify full recovery
sleep 10
if curl -s http://localhost:8888/api/health | jq .ws_clients > /dev/null; then
    echo "✅ Full network recovery successful"
else
    echo "⚠️ Network recovery incomplete"
fi
```

#### Test: WebSocket Connection Flood

**Objective**: Test WebSocket handling under load

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: WebSocket Connection Flood"

# Launch 100 concurrent WebSocket connections
for i in {1..100}; do
    (
        python3 -c "
import websockets
import asyncio
import json

async def flood_connection():
    try:
        uri = 'ws://localhost:8888/socket.io/?account_id=CHAOS_$i'
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({'type': 'subscribe', 'topic': 'events'}))
            # Keep connection open
            await asyncio.sleep(60)
    except Exception as e:
        print(f'Connection $i failed: {e}')

asyncio.run(flood_connection())
        " &
    )
done

sleep 10

# Check service health under load
WS_COUNT=$(curl -s http://localhost:8888/api/health | jq .ws_clients)
echo "WebSocket connections under flood: $WS_COUNT"

# Check response times
RESPONSE_TIME=$(curl -w "@-" -o /dev/null -s "http://localhost:8888/healthz" <<< 'time_total')
echo "Response time under load: ${RESPONSE_TIME}s"

# Cleanup - kill background processes
jobs -p | xargs kill 2>/dev/null

sleep 5

# Verify recovery
FINAL_WS=$(curl -s http://localhost:8888/api/health | jq .ws_clients)
echo "WebSocket connections after cleanup: $FINAL_WS"

if [ "$FINAL_WS" -lt 10 ]; then
    echo "✅ WebSocket cleanup successful"
else
    echo "⚠️ WebSocket connections may be leaking"
fi
```

### 3. Resource Exhaustion

#### Test: Memory Pressure

**Objective**: Test behavior under memory pressure

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Memory Pressure"

# Create memory pressure
stress --vm 1 --vm-bytes 1G --timeout 60s &
STRESS_PID=$!

# Monitor service during pressure
for i in {1..12}; do
    sleep 5
    MEM_USAGE=$(ps -o rss= -p $(pgrep -f hydrasocket-router) | awk '{print $1/1024}')
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/healthz)
    echo "Memory: ${MEM_USAGE}MB, HTTP: $HTTP_CODE"

    if [ "$HTTP_CODE" != "200" ]; then
        echo "⚠️ Service degraded under memory pressure"
        break
    fi
done

# Stop memory pressure
kill $STRESS_PID 2>/dev/null

sleep 10

# Verify recovery
if curl -s http://localhost:8888/healthz > /dev/null; then
    echo "✅ Memory pressure recovery successful"
else
    echo "❌ Service did not recover from memory pressure"
    exit 1
fi
```

#### Test: Disk Space Exhaustion

**Objective**: Test behavior when disk space is low

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Disk Space Exhaustion"

# Fill disk to 95% capacity
df -h /
AVAILABLE=$(df / | awk 'NR==2{print $4}' | sed 's/[^0-9]*//g')
FILL_SIZE=$((AVAILABLE - 100))  # Leave 100MB

if [ $FILL_SIZE -gt 0 ]; then
    echo "Creating ${FILL_SIZE}MB file to consume disk space"
    dd if=/dev/zero of=/tmp/chaos_fill bs=1M count=$FILL_SIZE 2>/dev/null

    sleep 5

    # Test service behavior
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/healthz)
    echo "Service response with low disk: $HTTP_CODE"

    # Check if logs still work
    if tail -1 /var/log/hydrasocket/out.log > /dev/null 2>&1; then
        echo "✅ Logging continues with low disk space"
    else
        echo "⚠️ Logging affected by low disk space"
    fi

    # Cleanup
    rm -f /tmp/chaos_fill

    sleep 5

    # Verify recovery
    if curl -s http://localhost:8888/healthz > /dev/null; then
        echo "✅ Disk space recovery successful"
    else
        echo "❌ Service did not recover from disk exhaustion"
        exit 1
    fi
else
    echo "Skipping disk exhaustion test - insufficient free space"
fi
```

### 4. Data Corruption

#### Test: Database Corruption Simulation

**Objective**: Test recovery from database corruption

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Database Corruption Simulation"

DB_PATH="/root/HydraX-v2/event_bus/bitten_events.db"
BACKUP_PATH="/tmp/chaos_backup_$(date +%s).db"

# Create backup
cp "$DB_PATH" "$BACKUP_PATH"

# Stop service
systemctl stop hydrasocket

# Simulate corruption by truncating database
truncate -s 50% "$DB_PATH"

# Try to start service with corrupted database
systemctl start hydrasocket

sleep 10

# Check if service detects corruption
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/healthz)

if [ "$HTTP_CODE" != "200" ]; then
    echo "✅ Service correctly detects database corruption"

    # Test recovery procedure
    systemctl stop hydrasocket
    cp "$BACKUP_PATH" "$DB_PATH"
    systemctl start hydrasocket

    sleep 15

    if curl -s http://localhost:8888/healthz > /dev/null; then
        echo "✅ Database corruption recovery successful"
    else
        echo "❌ Database corruption recovery failed"
        exit 1
    fi
else
    echo "⚠️ Service did not detect database corruption"
    # Restore anyway
    systemctl stop hydrasocket
    cp "$BACKUP_PATH" "$DB_PATH"
    systemctl start hydrasocket
fi

# Cleanup
rm -f "$BACKUP_PATH"
```

### 5. Configuration Chaos

#### Test: Invalid Configuration

**Objective**: Test handling of invalid configuration

```bash
#!/bin/bash
echo "🔥 CHAOS TEST: Invalid Configuration"

CONFIG_PATH="/root/HydraX-v2/.env"
BACKUP_CONFIG="/tmp/chaos_config_backup"

# Backup original config
cp "$CONFIG_PATH" "$BACKUP_CONFIG"

# Introduce invalid configuration
echo "INVALID_CONFIG_VALUE=this_will_break_things" >> "$CONFIG_PATH"
echo "DB_PATH=/nonexistent/path/database.db" >> "$CONFIG_PATH"

# Restart service with invalid config
pm2 restart hydrasocket-router

sleep 10

# Check if service handles gracefully
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/healthz)

if [ "$HTTP_CODE" != "200" ]; then
    echo "✅ Service correctly rejects invalid configuration"
else
    echo "⚠️ Service accepted invalid configuration"
fi

# Restore configuration
cp "$BACKUP_CONFIG" "$CONFIG_PATH"
pm2 restart hydrasocket-router

sleep 15

# Verify recovery
if curl -s http://localhost:8888/healthz > /dev/null; then
    echo "✅ Configuration recovery successful"
else
    echo "❌ Configuration recovery failed"
    exit 1
fi

# Cleanup
rm -f "$BACKUP_CONFIG"
```

## Chaos Test Suite

### Run All Tests

```bash
#!/bin/bash
echo "🎯 HYDRASOCKET CHAOS TEST SUITE"
echo "==============================="

TESTS=(
    "process_kill_test.sh"
    "database_lock_test.sh"
    "network_partition_test.sh"
    "websocket_flood_test.sh"
    "memory_pressure_test.sh"
    "disk_exhaustion_test.sh"
    "database_corruption_test.sh"
    "invalid_config_test.sh"
)

PASSED=0
FAILED=0

for test in "${TESTS[@]}"; do
    echo ""
    echo "Running: $test"
    echo "----------------------------------------"

    if bash "/root/HydraX-v2/docs/ops/chaos/$test"; then
        echo "✅ $test PASSED"
        ((PASSED++))
    else
        echo "❌ $test FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "==============================="
echo "CHAOS TEST RESULTS:"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "==============================="

if [ $FAILED -eq 0 ]; then
    echo "🎉 All chaos tests passed!"
    exit 0
else
    echo "⚠️ Some chaos tests failed - investigate failures"
    exit 1
fi
```

### Automated Chaos Testing

```bash
# Crontab entry for weekly chaos testing
# Run chaos tests every Sunday at 2 AM
0 2 * * 0 /root/HydraX-v2/scripts/chaos_test_suite.sh >> /var/log/hydrasocket/chaos_tests.log 2>&1
```

## Chaos Metrics

### Test Success Criteria

- **Recovery Time**: Service should recover within 60 seconds
- **Data Integrity**: No data loss during failures
- **Client Impact**: <10% of WebSocket clients should disconnect
- **Error Handling**: Graceful degradation, no crashes

### Monitoring During Chaos

```bash
# Monitor script to run during chaos tests
#!/bin/bash
while true; do
    echo "$(date): Health=$(curl -s -w "%{http_code}" http://localhost:8888/healthz -o /dev/null), WS=$(curl -s http://localhost:8888/api/health | jq .ws_clients), Mem=$(ps -o rss= -p $(pgrep hydrasocket) | awk '{print $1/1024}')MB"
    sleep 5
done
```

## Post-Chaos Analysis

### Metrics to Review

- Service downtime duration
- Error rates during and after chaos
- Resource usage patterns
- Alert triggering accuracy
- Recovery time measurements

### Improvement Actions

- Update restart thresholds
- Improve error handling
- Enhance monitoring coverage
- Strengthen graceful degradation
- Update runbooks based on findings
