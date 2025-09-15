# 🛡️ DATA FLOW PROTECTION DOCUMENTATION

**Created**: September 14, 2025  
**Purpose**: Prevent data flow breakages and ensure system resilience  
**Components**: Guardian, Dashboard, Alerts, Recovery

---

## 📊 CRITICAL DATA FLOWS

### **1. MARKET DATA FLOW**
```
MT5 EA → Port 5556 → Telemetry Bridge → Port 5560 → Elite Guard
```
**Critical Points**:
- EA must send ticks to port 5556
- Telemetry bridge must relay to port 5560
- Elite Guard must subscribe to port 5560

**Common Failures**:
- EA disconnected or not sending heartbeats
- Telemetry bridge process crashed
- Port binding conflicts

**Protection**:
- Auto-restart telemetry bridge if crashed
- Monitor EA heartbeat (<120s = healthy)
- Alert if no ticks for >5 minutes

---

### **2. SIGNAL GENERATION FLOW**
```
Elite Guard → Port 5557 → Relay → WebApp API → Database
```
**Critical Points**:
- Elite Guard publishes to port 5557
- Relay subscribes and forwards to WebApp
- WebApp stores in SQLite database

**Common Failures**:
- Elite Guard hanging on pattern detection
- Relay process not running
- WebApp API endpoint down

**Protection**:
- Auto-restart Elite Guard if no signals >1 hour
- Monitor signal count per hour
- Alert if signal rate drops below expected

---

### **3. FIRE EXECUTION FLOW**
```
WebApp → IPC Queue → Command Router → Port 5555 → EA → MT5
```
**Critical Points**:
- Fire command enqueued to IPC
- Command router pulls from queue
- Routes to EA via port 5555
- EA executes on MT5

**Common Failures**:
- IPC queue file permissions
- Command router not pulling
- EA not connected to port 5555

**Protection**:
- Monitor IPC queue size
- Auto-restart command router if stuck
- Check EA connection freshness

---

### **4. CONFIRMATION FLOW**
```
EA → Port 5558 → Confirmation Listener → Database Update
```
**Critical Points**:
- EA sends confirmation to port 5558
- Listener updates fires table
- Status changes from SENT to FILLED

**Common Failures**:
- Port 5558 not bound
- Confirmation listener crashed
- Database write failures

**Protection**:
- Monitor confirmation rate
- Auto-restart listener if needed
- Alert on low confirmation rate

---

## 🔧 MONITORING TOOLS

### **1. Data Flow Guardian** (`data_flow_guardian.py`)

**Purpose**: Real-time monitoring and automatic recovery

**Features**:
- Checks all critical processes every 30-60 seconds
- Auto-restarts failed processes (max 3 attempts)
- Monitors ZMQ port bindings
- Tracks data freshness (signals, trades, heartbeats)
- Writes health status to JSON file

**Usage**:
```bash
# Run as PM2 process for persistence
pm2 start data_flow_guardian.py --name guardian

# Or run directly for testing
python3 data_flow_guardian.py
```

**Health File**: `/root/HydraX-v2/data_flow_health.json`
- Updated every 30 seconds
- Contains all health metrics
- Used by dashboard and alerts

---

### **2. Data Flow Dashboard** (`data_flow_dashboard.html`)

**Purpose**: Visual monitoring interface

**Features**:
- Real-time status updates (30s refresh)
- Process health indicators
- Port binding status
- Data flow visualization
- 24-hour metrics
- Critical alerts display

**Access**:
```bash
# Serve via Python HTTP server
cd /root/HydraX-v2
python3 -m http.server 8890

# Access at: http://localhost:8890/data_flow_dashboard.html
```

**Indicators**:
- 🟢 Green = Healthy
- 🟡 Yellow = Warning
- 🔴 Red = Critical

---

### **3. Alert System** (`data_flow_alerts.py`)

**Purpose**: Proactive alerting on failures

**Alert Levels**:
- 🚨 **CRITICAL**: Immediate action needed
- ⚠️ **WARNING**: Degraded performance
- ℹ️ **INFO**: Informational

**Alert Conditions**:
- Process down >1 minute
- Port unbound >1 minute
- No signals >1 hour
- EA heartbeat >5 minutes
- No trades >2 hours
- Tracking files >2 hours old

**Alert Cooldown**: 1 hour (prevents spam)

**Log File**: `/root/HydraX-v2/data_flow_alerts.log`

---

## 🔄 AUTOMATIC RECOVERY

### **Process Auto-Restart**

**Configured Processes**:
```python
critical_processes = {
    "elite_guard": {
        "pm2_name": "elite_guard",
        "max_restarts": 3,
        "restart_on_fail": True
    },
    "command_router": {
        "pm2_name": "command_router",
        "max_restarts": 3,
        "restart_on_fail": True
    },
    "webapp": {
        "pm2_name": "webapp",
        "max_restarts": 3,
        "restart_on_fail": True
    },
    "telemetry_bridge": {
        "pm2_name": "zmq_telemetry_bridge",
        "max_restarts": 3,
        "restart_on_fail": True
    }
}
```

**Recovery Logic**:
1. Detect process failure
2. Wait 30 seconds
3. Attempt restart via PM2
4. Verify process started
5. Reset restart counter after 1 hour of stability

---

## 📋 MANUAL RECOVERY PROCEDURES

### **If Elite Guard Stops Generating Signals**

```bash
# 1. Check if process is running
pm2 list | grep elite_guard

# 2. Check logs for errors
pm2 logs elite_guard --lines 50

# 3. Restart the process
pm2 restart elite_guard

# 4. Verify signals flowing
tail -f /root/HydraX-v2/comprehensive_tracking.jsonl
```

### **If EA Connection Lost**

```bash
# 1. Check EA heartbeat age
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age FROM ea_instances;"

# 2. Check command router
pm2 logs command_router --lines 20

# 3. Verify port 5555 is bound
ss -tulpen | grep 5555

# 4. Check for zombie DEALER processes
ps aux | grep -i dealer
# Kill any test processes found
```

### **If No Market Data**

```bash
# 1. Check telemetry bridge
pm2 logs zmq_telemetry_bridge --lines 20

# 2. Verify port bindings
ss -tulpen | grep -E "5556|5560"

# 3. Restart telemetry bridge
pm2 restart zmq_telemetry_bridge

# 4. Check tick flow
# Should see tick messages in logs
```

### **If Fire Commands Not Executing**

```bash
# 1. Check IPC queue
ls -la /tmp/bitten_cmdqueue

# 2. Check command router
pm2 logs command_router --lines 20

# 3. Test fire pipeline
python3 -c "
import zmq
s = zmq.Context().socket(zmq.PUSH)
s.connect('ipc:///tmp/bitten_cmdqueue')
print('Sending test fire command...')
s.send_json({'type': 'test', 'message': 'Guardian test'})
print('Sent - check command_router logs')
"
```

---

## 🎯 BEST PRACTICES

### **1. Daily Checks**
- Review `bitten-report` output
- Check dashboard for any red indicators
- Review alert log for overnight issues

### **2. Weekly Maintenance**
- Clear old log files
- Archive tracking JSONL files >1GB
- Review and reset restart counters
- Update health thresholds if needed

### **3. Before Market Open**
- Run guardian health check
- Verify EA connection fresh
- Ensure all processes green
- Clear any pending alerts

### **4. Emergency Recovery**
```bash
# Full system restart sequence
pm2 restart all
sleep 10
python3 data_flow_guardian.py  # Run once to check
```

---

## 📊 HEALTH METRICS

### **Healthy System Indicators**
- ✅ All processes: RUNNING
- ✅ All ports: BOUND
- ✅ EA heartbeat: <120 seconds
- ✅ Signals: >1 per hour during market hours
- ✅ Tracking files: Updated <2 hours

### **Warning Signs**
- ⚠️ EA heartbeat: 120-300 seconds
- ⚠️ Signals: <1 per 2 hours
- ⚠️ Process restarts: >1 in past hour
- ⚠️ Tracking files: 2-4 hours old

### **Critical Issues**
- 🚨 Any process: DOWN
- 🚨 Critical port: UNBOUND
- 🚨 EA heartbeat: >300 seconds
- 🚨 No signals: >3 hours
- 🚨 No trades: >4 hours during market

---

## 🔒 DATA INTEGRITY

### **Backup Critical Files**
```bash
# Daily backup of database
cp /root/HydraX-v2/bitten.db /root/HydraX-v2/backups/bitten_$(date +%Y%m%d).db

# Archive tracking files weekly
tar -czf /root/HydraX-v2/backups/tracking_$(date +%Y%m%d).tar.gz *.jsonl
```

### **Prevent Corruption**
- Never modify database while processes running
- Use transactions for database updates
- Keep tracking files <1GB
- Rotate logs regularly

---

## 📞 ESCALATION PATH

### **Level 1: Automatic Recovery**
- Guardian auto-restarts failed processes
- Self-healing for transient issues

### **Level 2: Alert Notifications**
- Critical alerts logged
- Would send to Telegram if configured

### **Level 3: Manual Intervention**
- Check this documentation
- Follow recovery procedures
- Review ARCHITECTURE.md if needed

### **Level 4: System Reset**
- Full PM2 restart
- Clear IPC queues
- Reset database connections

---

**Remember**: The guardian watches the watchers. Keep it running for maximum protection.

**END OF DOCUMENT**