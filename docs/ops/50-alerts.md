# HYDRASOCKET v1 Alert Response Guide

## Alert Severity Levels

### 🔴 CRITICAL (P0)
- **Response Time**: Immediate (< 5 minutes)
- **Impact**: Service down, trading halted
- **Escalation**: Automatic PagerDuty

### 🟡 WARNING (P1)
- **Response Time**: 15 minutes
- **Impact**: Performance degraded
- **Escalation**: Slack notification

### 🔵 INFO (P2)
- **Response Time**: 1 hour
- **Impact**: Monitoring/trending
- **Escalation**: Log aggregation

## Alert Response Procedures

### 🚨 HydraSocketDown
**Severity**: CRITICAL
**Description**: HydraSocket service not responding to health checks

#### Immediate Actions
```bash
# 1. Check service status
systemctl status hydrasocket
pm2 status hydrasocket-router

# 2. Check logs for crash reason
journalctl -u hydrasocket -n 50 --no-pager
pm2 logs hydrasocket-router --lines 50

# 3. Quick restart attempt
systemctl restart hydrasocket
# OR
pm2 restart hydrasocket-router

# 4. Verify recovery
curl http://localhost:8888/healthz
```

#### If restart fails
```bash
# Check port conflicts
sudo netstat -tulpn | grep :8888

# Check database access
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db ".tables"

# Check disk space
df -h /

# Emergency fallback
python3 /root/HydraX-v2/EMERGENCY_WEBAPP_NUCLEAR.py &
```

### ⚠️ HighOrderLatencyP95
**Severity**: WARNING
**Description**: Order processing latency p95 > 250ms

#### Investigation Steps
```bash
# 1. Check current latency
curl -s http://localhost:8888/metrics | grep order_to_open_ms_p95

# 2. Check system load
top -bn1 | head -10

# 3. Check database performance
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "PRAGMA optimize;"

# 4. Check WebSocket connections
curl -s http://localhost:8888/api/health | jq .ws_clients
```

#### Mitigation Actions
```bash
# Reduce WebSocket backpressure
curl -X POST http://localhost:8888/admin/reduce-backpressure

# Restart if latency persists > 10 minutes
pm2 reload hydrasocket-router
```

### 📉 BackpressureDrops
**Severity**: CRITICAL
**Description**: Messages being dropped due to backpressure

#### Immediate Actions
```bash
# 1. Check drop rate
curl -s http://localhost:8888/metrics | grep backpressure_drops_total

# 2. Check WebSocket client count
curl -s http://localhost:8888/api/health | jq .ws_clients

# 3. Enable drain mode to reduce load
curl -X POST http://localhost:8888/admin/drain

# 4. Monitor for stabilization
watch -n 5 'curl -s http://localhost:8888/metrics | grep backpressure_drops_total'
```

#### Recovery Actions
```bash
# If drops continue, restart with higher limits
export WS_ACK_WINDOW=512
pm2 restart hydrasocket-router

# Re-enable normal operations once stable
curl -X DELETE http://localhost:8888/admin/drain
```

### 🔌 RouterClientsDrop
**Severity**: CRITICAL
**Description**: No active WebSocket connections

#### Investigation Steps
```bash
# 1. Check WebSocket endpoint
curl -I http://localhost:8888/socket.io/

# 2. Test WebSocket connection manually
python3 -c "
import websockets
import asyncio

async def test():
    try:
        async with websockets.connect('ws://localhost:8888/socket.io/') as ws:
            print('✅ WebSocket connection successful')
            await ws.send('{\"type\":\"ping\"}')
            response = await ws.recv()
            print(f'Response: {response}')
    except Exception as e:
        print(f'❌ WebSocket error: {e}')

asyncio.run(test())
"

# 3. Check for network issues
netstat -an | grep :8888
```

#### Recovery Actions
```bash
# Restart WebSocket handler
pm2 restart hydrasocket-router

# Check firewall rules
sudo iptables -L | grep 8888

# Verify service binding
sudo netstat -tulpn | grep :8888
```

### 📊 EventLagHigh
**Severity**: WARNING
**Description**: Event processing lag p95 > 500ms

#### Investigation Steps
```bash
# 1. Check EA connectivity
curl -s http://localhost:8888/metrics | grep ea_events_received_total

# 2. Check ZMQ ports
sudo netstat -tulpn | grep -E ":(5558|5560)"

# 3. Check database write performance
time sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "INSERT INTO events (event_type, timestamp, source) VALUES ('test', $(date +%s), 'manual');"
```

#### Mitigation Actions
```bash
# Optimize database
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "VACUUM; ANALYZE;"

# Restart EA event collector
pm2 restart ea_event_collector

# Check disk I/O
iostat -x 1 5
```

### 🔑 AuthenticationFailures
**Severity**: WARNING
**Description**: High rate of authentication failures

#### Investigation Steps
```bash
# 1. Check failed auth patterns
grep "auth.*failed" /var/log/hydrasocket/*.log | tail -20

# 2. Check API key validity
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "SELECT COUNT(*) FROM api_keys WHERE enabled=1;"

# 3. Look for brute force attempts
grep -E "401|403" /var/log/hydrasocket/*.log | cut -d' ' -f1 | sort | uniq -c | sort -nr
```

#### Mitigation Actions
```bash
# Rate limit suspicious IPs
sudo iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# Disable compromised keys
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "UPDATE api_keys SET enabled=0 WHERE key='SUSPICIOUS_KEY';"

# Force key rotation if needed
python3 tools/rotate_api_keys.py
```

### 💾 DatabaseErrors
**Severity**: WARNING
**Description**: Database operation failures

#### Investigation Steps
```bash
# 1. Check database integrity
sqlite3 /root/HydraX-v2/event_bus/bitten_events.db "PRAGMA integrity_check;"

# 2. Check disk space
df -h /root/HydraX-v2/

# 3. Check for locks
lsof /root/HydraX-v2/event_bus/bitten_events.db
```

#### Recovery Actions
```bash
# If corruption detected
systemctl stop hydrasocket

# Restore from backup
cp /opt/hydrasocket/backups/$(date +%Y%m%d)/bitten_events_*.db /root/HydraX-v2/event_bus/bitten_events.db

systemctl start hydrasocket
```

### 🧠 MemoryUsageHigh
**Severity**: WARNING
**Description**: Process memory usage > 2GB

#### Investigation Steps
```bash
# 1. Check memory usage breakdown
ps aux | grep hydrasocket
cat /proc/$(pgrep -f hydrasocket)/status | grep -E "VmRSS|VmSize"

# 2. Check for memory leaks
valgrind --tool=memcheck --leak-check=full python3 webapp_server_optimized.py &
```

#### Mitigation Actions
```bash
# Restart service to free memory
pm2 restart hydrasocket-router

# Monitor memory growth
watch -n 30 'ps aux | grep hydrasocket | grep -v grep'

# If leak persists, reduce worker count
# Edit ecosystem.config.js: args: "-w 2" (instead of -w 4)
pm2 restart hydrasocket-router
```

## Alert Escalation Matrix

### Level 1: Automated Response (0-5 minutes)
- Automatic restart attempts
- Health check validation
- Basic remediation scripts

### Level 2: On-Call Engineer (5-15 minutes)
- Manual diagnostics
- Service restarts
- Configuration adjustments

### Level 3: Senior Engineer (15-30 minutes)
- Code-level debugging
- Database recovery
- Architecture changes

### Level 4: Incident Commander (30+ minutes)
- Multi-service coordination
- Business impact assessment
- External communication

## Runbook Templates

### Investigation Checklist
```
□ Check service status
□ Review recent logs
□ Verify external dependencies
□ Check system resources
□ Test basic functionality
□ Identify root cause
□ Apply mitigation
□ Verify resolution
□ Document incident
```

### Communication Template
```
🚨 INCIDENT: [ALERT_NAME]
Status: [INVESTIGATING/MITIGATING/RESOLVED]
Start Time: [TIMESTAMP]
Impact: [DESCRIPTION]
Current Actions: [DESCRIPTION]
ETA: [TIMESTAMP]
Updates: #hydrasocket-incidents
```

## Prevention Strategies

### Monitoring Improvements
- Add predictive alerting for resource trends
- Implement anomaly detection for unusual patterns
- Set up dependency health monitoring

### Automation Enhancements
- Auto-scaling based on load
- Automated log analysis and root cause detection
- Self-healing restart policies

### Testing
- Regular chaos engineering exercises
- Load testing in production-like environments
- Disaster recovery drills

## Alert Tuning

### Threshold Adjustment
Review and adjust alert thresholds quarterly based on:
- Historical performance data
- Seasonal traffic patterns
- System capacity changes
- Business requirements

### False Positive Reduction
- Implement alert suppression during maintenance
- Add context-aware alerting logic
- Use composite alerts for complex conditions