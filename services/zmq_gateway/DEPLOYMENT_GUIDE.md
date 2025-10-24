# ZMQ Gateway v2.0 - Deployment Guide

## Pre-Deployment Checklist

### 1. Stop v1 Processes

**CRITICAL**: Stop all v1 processes before deploying v2 gateway:

```bash
# Stop old processes via PM2
pm2 stop zmq_telemetry_bridge_debug
pm2 stop command_router
pm2 stop confirm_listener_v207

# Or kill directly if not using PM2
pkill -f zmq_telemetry_bridge_debug
pkill -f command_router.py
pkill -f confirm_listener_v207
```

### 2. Verify Ports Are Free

```bash
# Check that critical ports are not in use
ss -tulpen | grep -E ":(5555|5556|5558|5560|9091)"

# Expected: No output (all ports free)
```

### 3. Verify Dependencies

```bash
cd /root/HydraX-v2/services/zmq_gateway
pip install -r requirements.txt

# Expected packages:
# - pyzmq>=25.0.0
# - aiohttp>=3.8.0
```

## Deployment Steps

### Option 1: Direct Python Execution

```bash
cd /root/HydraX-v2

# Start service
python3 -m services.zmq_gateway.main

# Service will display startup banner:
# ======================================================================
# 🚀 BITTEN ZMQ Gateway v2.0 - Starting
# ======================================================================
# ...
# ✅ ZMQ Gateway v2.0 - ALL SYSTEMS OPERATIONAL
```

### Option 2: PM2 Deployment (Recommended)

```bash
cd /root/HydraX-v2

# Start with PM2
pm2 start services/zmq_gateway/main.py \
  --name zmq_gateway \
  --interpreter python3 \
  --cwd /root/HydraX-v2 \
  --log /root/HydraX-v2/logs/zmq_gateway.log \
  --merge-logs

# Save PM2 config
pm2 save

# Enable startup on boot
pm2 startup
```

### Option 3: Systemd Service (Production)

Create `/etc/systemd/system/zmq-gateway.service`:

```ini
[Unit]
Description=BITTEN ZMQ Gateway v2.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment="PYTHONUNBUFFERED=1"
Environment="BITTEN_DB=/root/HydraX-v2/bitten.db"
Environment="LOG_LEVEL=INFO"
ExecStart=/usr/bin/python3 -m services.zmq_gateway.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
systemctl daemon-reload
systemctl enable zmq-gateway
systemctl start zmq-gateway
systemctl status zmq-gateway
```

## Post-Deployment Verification

### 1. Health Check

```bash
# Liveness (service running?)
curl http://localhost:9091/health/liveness

# Expected:
# {"status":"alive","uptime_seconds":30,"service":"zmq_gateway","version":"2.0.0"}

# Readiness (all components healthy?)
curl http://localhost:9091/health/readiness

# Expected:
# {"status":"ready","uptime_seconds":30,"components":{...}}
```

### 2. Port Bindings

```bash
ss -tulpen | grep -E ":(5555|5556|5558|5560|9091)"

# Expected output:
# tcp   LISTEN 0  100  0.0.0.0:5556   *:*  (port 5556 - market data in)
# tcp   LISTEN 0  100  0.0.0.0:5560   *:*  (port 5560 - market data out)
# tcp   LISTEN 0  100  0.0.0.0:5555   *:*  (port 5555 - command router)
# tcp   LISTEN 0  100  0.0.0.0:5558   *:*  (port 5558 - confirmations)
# tcp   LISTEN 0  128  0.0.0.0:9091   *:*  (port 9091 - health)
```

### 3. Component Metrics

```bash
curl -s http://localhost:9091/metrics | jq

# Expected output with component statistics:
# {
#   "uptime_seconds": 60,
#   "market_data": {
#     "message_count": 1500,
#     "tick_count": 1450,
#     "symbols_tracked": 16
#   },
#   "command_router": {
#     "connected_eas": 1,
#     "commands_routed": 0
#   },
#   "confirmations": {
#     "confirmations_received": 0
#   }
# }
```

### 4. EA Connection

Wait 30 seconds for EA heartbeat, then:

```bash
curl -s http://localhost:9091/metrics | jq '.command_router'

# Expected:
# {
#   "connected_eas": 1,  ← EA should be connected
#   "heartbeats_received": 6
# }
```

### 5. Database Updates

```bash
sqlite3 /root/HydraX-v2/bitten.db "
SELECT target_uuid,
       (strftime('%s','now') - last_seen) as age_seconds,
       last_balance,
       last_equity
FROM ea_instances
WHERE target_uuid = 'COMMANDER_DEV_001';
"

# Expected: age_seconds < 120 (EA is fresh)
```

## Monitoring

### Logs

```bash
# PM2 logs
pm2 logs zmq_gateway --lines 50

# Systemd logs
journalctl -u zmq-gateway -f

# Direct file
tail -f /root/HydraX-v2/logs/zmq_gateway.log
```

### Metrics Dashboard

Create a simple monitoring script:

```bash
#!/bin/bash
# /root/HydraX-v2/monitor_gateway.sh

while true; do
  clear
  echo "=== ZMQ Gateway v2.0 Status ==="
  echo ""
  curl -s http://localhost:9091/metrics | jq -r '
    "Uptime: \(.uptime_seconds)s",
    "",
    "Market Data:",
    "  Messages: \(.market_data.message_count)",
    "  Ticks: \(.market_data.tick_count)",
    "  Symbols: \(.market_data.symbols_tracked)",
    "",
    "Command Router:",
    "  Connected EAs: \(.command_router.connected_eas)",
    "  Commands: \(.command_router.commands_routed)",
    "  Heartbeats: \(.command_router.heartbeats_received)",
    "",
    "Confirmations:",
    "  Received: \(.confirmations.confirmations_received)",
    "  Opened: \(.confirmations.positions_opened)",
    "  Closed: \(.confirmations.positions_closed)"
  '
  sleep 5
done
```

## Rollback Plan

If v2 gateway has issues:

### 1. Stop v2 Gateway

```bash
# PM2
pm2 stop zmq_gateway

# Systemd
systemctl stop zmq-gateway

# Direct
pkill -f "services.zmq_gateway.main"
```

### 2. Restart v1 Processes

```bash
pm2 restart zmq_telemetry_bridge_debug
pm2 restart command_router
pm2 restart confirm_listener_v207
```

### 3. Verify v1 Recovery

```bash
pm2 list | grep -E "telemetry|router|confirm"
ss -tulpen | grep -E ":(5555|5556|5558|5560)"
```

## Troubleshooting

### Issue: Port Already in Use

**Symptom**: `Address already in use (addr='tcp://*:5556')`

**Solution**:
```bash
# Find process using port
lsof -i :5556

# Kill process
kill -9 [PID]

# Or stop all v1 processes
pm2 stop zmq_telemetry_bridge_debug command_router confirm_listener_v207
```

### Issue: EA Not Connecting

**Symptom**: `connected_eas: 0` in metrics

**Solution**:
```bash
# 1. Check if EA is running on MT5
# 2. Verify EA settings (server IP, port 5555)
# 3. Check EA logs for connection errors
# 4. Verify firewall allows port 5555
```

### Issue: No Market Data

**Symptom**: `message_count: 0` in metrics

**Solution**:
```bash
# 1. Check if EA is sending data to port 5556
# 2. Verify telemetry is enabled in EA settings
# 3. Check logs for parsing errors
```

### Issue: Commands Not Routing

**Symptom**: `commands_routed: 0` but `commands_enqueued > 0`

**Solution**:
```bash
# Check queue size
curl -s http://localhost:9091/metrics | jq '.command_router.queue_size'

# If queue is growing:
# 1. EA may not be connected
# 2. UUID mismatch (firewall blocking)
# 3. Check logs for UUID_FIREWALL warnings
```

## Performance Tuning

### Database Connection Pool

For high-throughput environments:

```python
# In config.py, add:
DB_POOL_SIZE = 10
DB_TIMEOUT = 10
```

### ZMQ High Water Mark

For high-frequency trading:

```python
# In command_handler.py, increase:
self.ipc_pull.setsockopt(zmq.RCVHWM, 50000)  # From 10000
```

### Logging Level

For production (reduce I/O):

```bash
export LOG_LEVEL=WARNING
```

For debugging:

```bash
export LOG_LEVEL=DEBUG
```

## Security Considerations

### 1. Bind to Localhost Only

For single-server deployments:

```python
# In config.py, change:
# From: bind("tcp://*:5556")
# To:   bind("tcp://127.0.0.1:5556")
```

### 2. Firewall Rules

```bash
# Only allow EA connection from specific IP
iptables -A INPUT -p tcp --dport 5555 -s [EA_SERVER_IP] -j ACCEPT
iptables -A INPUT -p tcp --dport 5555 -j DROP
```

### 3. Health Endpoint Authentication

Add basic auth to health endpoints (future enhancement).

## Maintenance

### Log Rotation

```bash
# Add to /etc/logrotate.d/zmq-gateway
/root/HydraX-v2/logs/zmq_gateway.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Database Vacuum

```bash
# Weekly database optimization
sqlite3 /root/HydraX-v2/bitten.db "VACUUM;"
```

## Support

For issues or questions:
1. Check logs first: `pm2 logs zmq_gateway`
2. Verify health: `curl http://localhost:9091/health/readiness`
3. Review metrics: `curl http://localhost:9091/metrics`
4. Check this guide's troubleshooting section

## Version History

- **v2.0.0** (2025-10-08): Initial consolidated service
  - Replaced 3 v1 processes
  - Added health endpoints
  - Async/await architecture
  - 1,476 lines of code
