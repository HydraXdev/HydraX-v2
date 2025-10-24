# BITTEN v2.0 Service Start Order & Dependencies

**Version**: 1.0
**Date**: October 8, 2025
**Purpose**: Define correct startup sequence for BITTEN v2.0 services

---

## 🎯 Critical Start Order

**Services MUST start in this exact order to prevent dependency failures:**

```
1. PostgreSQL (Database) - MUST be running first
    ↓
2. zmq_gateway (ZMQ Infrastructure) - Binds ports 5555, 5556, 5558, 5560
    ↓  (wait 3 seconds for port bindings)
    ↓
3. signal_engine (Pattern Detection) - Binds port 5557, connects to 5560
    ↓  (wait 5 seconds for pattern detector initialization)
    ↓
4. fire_service (Trade Execution) - Connects to database & ZMQ 5555
    ↓
5. api_server (HTTP API + Telegram) - Connects to database & ZMQ 5557, 5560
    ↓
6. analytics_worker (Background Jobs) - Connects to database & Firestore
```

---

## 📋 Startup Script (Automated)

**Use this for production deployments:**

```bash
#!/bin/bash
# /root/HydraX-v2/scripts/start_v2_services.sh

set -e  # Exit on error

echo "🚀 Starting BITTEN v2.0 Services in Correct Order"
echo "=================================================="

# Step 1: Verify PostgreSQL is running
echo "[1/7] Checking PostgreSQL..."
if ! pg_isready -h localhost -p 5433 -U bitten_admin > /dev/null 2>&1; then
    echo "❌ PostgreSQL not ready. Starting..."
    sudo systemctl start postgresql@15-main
    sleep 5
fi

if ! PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Cannot connect to bitten_v2 database. Aborting."
    exit 1
fi
echo "✅ PostgreSQL ready"

# Step 2: Start ZMQ Gateway (Core Infrastructure)
echo "[2/7] Starting zmq_gateway (ports 5555, 5556, 5558, 5560)..."
pm2 start /root/HydraX-v2/ecosystem.config.js --only zmq_gateway
sleep 3

# Verify port bindings
PORTS_OK=true
for port in 5555 5556 5558 5560; do
    if ! ss -tulpen | grep -q ":$port"; then
        echo "❌ Port $port not bound!"
        PORTS_OK=false
    fi
done

if [ "$PORTS_OK" = false ]; then
    echo "❌ ZMQ gateway failed to bind all ports. Check logs:"
    pm2 logs zmq_gateway --lines 20 --nostream
    exit 1
fi
echo "✅ zmq_gateway started and ports bound"

# Step 3: Start Signal Engine (Pattern Detection)
echo "[3/7] Starting signal_engine (port 5557)..."
pm2 start /root/HydraX-v2/ecosystem.config.js --only signal_engine
sleep 5

if ! ss -tulpen | grep -q ":5557"; then
    echo "❌ Signal engine failed to bind port 5557. Check logs:"
    pm2 logs signal_engine --lines 20 --nostream
    exit 1
fi
echo "✅ signal_engine started"

# Step 4: Start Fire Service (Trade Execution)
echo "[4/7] Starting fire_service..."
pm2 start /root/HydraX-v2/ecosystem.config.js --only fire_service
sleep 3
echo "✅ fire_service started"

# Step 5: Start API Server (HTTP + Telegram)
echo "[5/7] Starting api_server (port 8888, 2 instances)..."
pm2 start /root/HydraX-v2/ecosystem.config.js --only api_server
sleep 5

if ! curl -s http://localhost:8888/healthz > /dev/null 2>&1; then
    echo "⚠️  API server health check failed, but may be warming up..."
fi
echo "✅ api_server started"

# Step 6: Start Analytics Worker (Background Jobs)
echo "[6/7] Starting analytics_worker..."
pm2 start /root/HydraX-v2/ecosystem.config.js --only analytics_worker
sleep 3
echo "✅ analytics_worker started"

# Step 7: Final Verification
echo "[7/7] Final health check..."
pm2 list

# Verify all processes online
EXPECTED_PROCESSES=("zmq_gateway" "signal_engine" "fire_service" "api_server" "analytics_worker")
ALL_ONLINE=true

for process in "${EXPECTED_PROCESSES[@]}"; do
    if ! pm2 list | grep -q "$process.*online"; then
        echo "❌ Process $process not online"
        ALL_ONLINE=false
    fi
done

if [ "$ALL_ONLINE" = false ]; then
    echo "❌ Some processes failed to start. Check PM2 status."
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ All BITTEN v2.0 Services Started Successfully"
echo "=================================================="
echo ""
echo "Service URLs:"
echo "  - API: http://localhost:8888"
echo "  - Health: http://localhost:8888/healthz"
echo ""
echo "Next steps:"
echo "  1. Check logs: pm2 logs"
echo "  2. Monitor status: pm2 monit"
echo "  3. Save config: pm2 save"
```

**Make executable**: `chmod +x /root/HydraX-v2/scripts/start_v2_services.sh`

---

## 🛑 Shutdown Script (Reverse Order)

**Graceful shutdown in reverse dependency order:**

```bash
#!/bin/bash
# /root/HydraX-v2/scripts/stop_v2_services.sh

set -e

echo "🛑 Stopping BITTEN v2.0 Services in Reverse Order"
echo "=================================================="

# Stop in reverse order
echo "[1/5] Stopping analytics_worker..."
pm2 stop analytics_worker
sleep 1

echo "[2/5] Stopping api_server..."
pm2 stop api_server
sleep 2  # Allow HTTP connections to drain

echo "[3/5] Stopping fire_service..."
pm2 stop fire_service
sleep 1

echo "[4/5] Stopping signal_engine..."
pm2 stop signal_engine
sleep 1

echo "[5/5] Stopping zmq_gateway..."
pm2 stop zmq_gateway
sleep 2

# Verify all stopped
echo ""
echo "Final status:"
pm2 list

echo ""
echo "✅ All BITTEN v2.0 Services Stopped"
```

**Make executable**: `chmod +x /root/HydraX-v2/scripts/stop_v2_services.sh`

---

## ⚡ Quick Commands

**Start all services (automated)**:
```bash
/root/HydraX-v2/scripts/start_v2_services.sh
```

**Stop all services (automated)**:
```bash
/root/HydraX-v2/scripts/stop_v2_services.sh
```

**Restart all services (with dependency order)**:
```bash
/root/HydraX-v2/scripts/stop_v2_services.sh && sleep 5 && /root/HydraX-v2/scripts/start_v2_services.sh
```

**Start using PM2 ecosystem (all at once - NOT RECOMMENDED)**:
```bash
# This starts all services simultaneously (may cause dependency issues)
pm2 start /root/HydraX-v2/ecosystem.config.js
```

**Restart single service (safe)**:
```bash
pm2 restart <service_name>
```

---

## 🔍 Dependency Matrix

| Service | Depends On | Port Bindings | Wait Time |
|---------|-----------|---------------|-----------|
| zmq_gateway | PostgreSQL | 5555, 5556, 5558, 5560 | 3s after start |
| signal_engine | zmq_gateway (port 5560) | 5557 | 5s after start |
| fire_service | zmq_gateway, PostgreSQL | None (connects only) | 3s after start |
| api_server | All ZMQ services, PostgreSQL | 8888 | 5s after start |
| analytics_worker | PostgreSQL, Firestore | None | 3s after start |

**Why the wait times?**
- ZMQ sockets need time to bind and become ready
- Pattern detectors in signal_engine load configuration (2-3 seconds)
- HTTP server in api_server needs time to initialize routes
- Database connection pools need warm-up time

---

## 🚨 Common Startup Issues

### Issue 1: "Address Already in Use"

**Symptom**: zmq_gateway fails to start with port binding error

**Cause**: Old processes still holding ZMQ ports

**Fix**:
```bash
# Kill processes on ZMQ ports
for port in 5555 5556 5557 5558 5560; do
    lsof -ti:$port | xargs -r kill -9
done

# Restart services
/root/HydraX-v2/scripts/start_v2_services.sh
```

---

### Issue 2: Service Starts Then Immediately Crashes

**Symptom**: PM2 shows service restarting constantly

**Cause**: Dependency not ready (database, ZMQ port)

**Fix**:
```bash
# Check logs for specific error
pm2 logs <service_name> --lines 50 --nostream

# Common fixes:
# - PostgreSQL not running: sudo systemctl start postgresql@15-main
# - ZMQ port not bound: Restart zmq_gateway first
# - Missing dependencies: pip3 install -r requirements_v2.txt
```

---

### Issue 3: api_server Health Check Fails

**Symptom**: `curl http://localhost:8888/healthz` returns connection refused

**Cause**: Service still warming up or crashed

**Fix**:
```bash
# Wait 10 seconds for full initialization
sleep 10
curl -s http://localhost:8888/healthz | jq

# If still fails, check logs
pm2 logs api_server --lines 50 --nostream

# Check if port is bound
ss -tulpen | grep :8888
```

---

## 🔄 Automated Startup on System Boot

**Configure PM2 to start on server reboot:**

```bash
# Generate startup script
pm2 startup systemd

# Follow the command output and run the generated command
# Example output:
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root

# Save current PM2 process list
pm2 save

# Verify startup configuration
systemctl status pm2-root
```

**Test auto-start**:
```bash
# Reboot server
sudo reboot

# After reboot, verify services started automatically
pm2 list
```

---

## 📊 Health Monitoring

**Verify all services are healthy:**

```bash
# Quick check
pm2 list | grep -E "online|stopped|errored"

# Detailed check
pm2 monit

# Service-specific health
curl -s http://localhost:8888/api/health/detailed | jq

# Database connectivity
PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT COUNT(*) as active_services FROM pg_stat_activity WHERE datname = 'bitten_v2';"

# ZMQ port bindings
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"
```

---

## 📞 Support

**If startup issues persist:**

1. **Collect diagnostic data**:
   ```bash
   pm2 logs --lines 200 > pm2_logs_all.txt
   ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)" > port_bindings.txt
   PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT * FROM pg_stat_activity WHERE datname = 'bitten_v2';" > db_connections.txt
   ```

2. **Create support package**:
   ```bash
   tar -czf startup_diagnostics_$(date +%Y%m%d_%H%M%S).tar.gz \
       pm2_logs_all.txt \
       port_bindings.txt \
       db_connections.txt \
       /etc/logrotate.d/bitten_v2 \
       /root/HydraX-v2/ecosystem.config.js
   ```

3. **Escalate to DevOps team** with diagnostic package

---

**Last Updated**: October 8, 2025
**Maintained By**: DevOps Team
**Review Frequency**: Monthly
