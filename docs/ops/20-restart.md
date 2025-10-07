# HYDRASOCKET v1 Restart Playbook

## Emergency Restart (Service Down)

### 1. Immediate Actions

```bash
# Check service status
systemctl status hydrasocket
# OR
pm2 status hydrasocket-router

# Check logs for crash reason
journalctl -u hydrasocket -n 50
# OR
pm2 logs hydrasocket-router --lines 50
```

### 2. Quick Restart

```bash
# systemd
systemctl restart hydrasocket
systemctl status hydrasocket

# PM2
pm2 restart hydrasocket-router
pm2 status hydrasocket-router
```

### 3. Health Verification

```bash
# Wait for startup
sleep 15

# Check health
curl http://localhost:8888/healthz
if [ $? -eq 0 ]; then
  echo "✅ Service restored"
else
  echo "❌ Service still down - escalate"
fi
```

## Planned Restart (Zero-Downtime)

### 1. Pre-Restart Checks

```bash
# Check current health
curl http://localhost:8888/api/health

# Check active WebSocket connections
WS_COUNT=$(curl -s http://localhost:8888/api/health | jq .ws_clients)
echo "Active WebSocket connections: $WS_COUNT"
```

### 2. Graceful Drain

```bash
# Enable drain mode (stop accepting new connections)
curl -X POST http://localhost:8888/admin/drain

# Wait for connections to finish naturally (max 60s)
sleep 60

# Force close remaining connections if needed
curl -X POST http://localhost:8888/admin/force-close
```

### 3. Rolling Restart

```bash
# PM2 rolling restart (zero downtime)
pm2 reload hydrasocket-router

# Verify restart
pm2 status hydrasocket-router
```

### 4. Re-enable Traffic

```bash
# Disable drain mode
curl -X DELETE http://localhost:8888/admin/drain

# Verify health
curl http://localhost:8888/api/health
```

## Restart Triggers

### Automatic Restart Conditions

- Process crashes (handled by PM2/systemd)
- Memory usage > 2GB for 5 minutes
- Event lag > 2000ms for 10 minutes
- WebSocket connections stuck > 1000

### Manual Restart Reasons

- Configuration changes
- Memory leaks detected
- Performance degradation
- Deployment updates

## Restart Verification Checklist

- [ ] Service status: Running
- [ ] Health endpoint: 200 OK
- [ ] WebSocket connections: Accepting new
- [ ] Event processing: Lag < 500ms
- [ ] Database: Accessible
- [ ] ZMQ ports: Listening (5558, 5560)

## Troubleshooting Failed Restarts

### Common Issues

1. **Port already in use**

   ```bash
   sudo netstat -tulpn | grep :8888
   sudo kill -9 <PID>
   ```

2. **Database locked**

   ```bash
   lsof /root/HydraX-v2/event_bus/bitten_events.db
   sudo kill -9 <PID>
   ```

3. **ZMQ port conflicts**

   ```bash
   sudo netstat -tulpn | grep -E ":(5558|5560)"
   sudo kill -9 <PID>
   ```

4. **Permissions issues**
   ```bash
   sudo chown -R hydrasocket:hydrasocket /opt/hydrasocket
   sudo chmod +x /opt/hydrasocket/venv/bin/*
   ```

### Escalation Criteria

- Service fails to start after 3 restart attempts
- Health checks fail for > 5 minutes
- Database corruption detected
- Multiple ZMQ port conflicts

## Recovery Time Objectives

- **Emergency restart**: < 30 seconds
- **Planned restart**: < 60 seconds (zero downtime)
- **Failed restart recovery**: < 5 minutes

## Post-Restart Actions

1. Monitor metrics for 15 minutes
2. Check error rates in logs
3. Verify WebSocket client reconnections
4. Update incident tracking if applicable
