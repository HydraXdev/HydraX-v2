# ZMQ DEPLOYMENT GUIDE FOR HYDRAX

## Overview

This guide covers the deployment of ZeroMQ-based real-time data streaming from MT5 to the Linux VENOM engine, replacing the fragile HTTP polling system.

## Architecture

```
MT5 (Windows VPS)                     Linux VPS
┌─────────────────┐                  ┌──────────────────────┐
│   EA v6.0 ZMQ   │                  │  ZMQ Market Receiver │
│                 │                  │                      │
│ [ZMQ Publisher] │───tcp:5555────>  │  [ZMQ Subscriber]    │
│                 │                  │         ↓            │
│ [File Trading]  │                  │   Flask API :8001    │
│  fire.txt       │                  │         ↓            │
│  trade_result   │                  │   VENOM Pipeline     │
└─────────────────┘                  └──────────────────────┘
```

## Prerequisites

### On MT5 Windows VPS

1. **Download ZMQ Library**
   ```
   Download: https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4.zip
   Extract: libzmq.dll (64-bit version)
   Place in: C:\Windows\System32\ or MT5 terminal folder
   ```

2. **Enable DLL Imports in MT5**
   - Tools → Options → Expert Advisors
   - ✅ Allow DLL imports
   - ✅ Allow WebRequest (keep existing URLs)

3. **Firewall Configuration**
   ```cmd
   netsh advfirewall firewall add rule name="ZMQ Publisher" dir=in action=allow protocol=TCP localport=5555
   ```

### On Linux VPS

1. **Install Dependencies**
   ```bash
   pip install pyzmq flask cachetools
   ```

2. **Network Configuration**
   ```bash
   # Check connectivity to MT5
   nc -zv MT5_IP_ADDRESS 5555
   ```

## Deployment Steps

### Step 1: Deploy EA on MT5

1. **Copy EA to MT5**
   ```
   Copy: BITTENBridge_TradeExecutor_ZMQ_v6.mq5
   To: C:\Program Files\MetaTrader 5\MQL5\Experts\
   ```

2. **Compile EA**
   - Open MetaEditor (F4 in MT5)
   - Open the EA file
   - Compile (F7)
   - Must see: "0 errors, 0 warnings"

3. **Attach to Chart**
   - Open any chart (EA will stream all 15 pairs)
   - Drag EA to chart
   - Configure settings:
     - ZMQ_BIND_ADDRESS: tcp://*:5555
     - StreamIntervalMS: 100 (for high frequency)
   - Click OK

4. **Verify EA Running**
   - Check Experts tab for "ZMQ Publisher initialized"
   - Should see "Publishing on: tcp://*:5555"

### Step 2: Deploy ZMQ Receiver on Linux

1. **Stop Old Services**
   ```bash
   # Stop HTTP-based receivers
   systemctl stop market-data-receiver
   pkill -f market_data_receiver
   ```

2. **Configure Environment**
   ```bash
   # Edit the service file
   nano /root/HydraX-v2/zmq-market-receiver.service
   
   # Update ZMQ_ENDPOINT with your MT5 IP
   Environment="ZMQ_ENDPOINT=tcp://YOUR_MT5_IP:5555"
   ```

3. **Install Service**
   ```bash
   # Copy service file
   cp /root/HydraX-v2/zmq-market-receiver.service /etc/systemd/system/
   
   # Reload systemd
   systemctl daemon-reload
   
   # Enable service
   systemctl enable zmq-market-receiver
   
   # Start service
   systemctl start zmq-market-receiver
   ```

4. **Verify Service**
   ```bash
   # Check status
   systemctl status zmq-market-receiver
   
   # Check logs
   journalctl -u zmq-market-receiver -f
   
   # Test API
   curl http://localhost:8001/market-data/health
   ```

### Step 3: Restart VENOM Pipeline

1. **Kill Old VENOM Stream**
   ```bash
   pkill -f venom_stream_pipeline
   ```

2. **Start VENOM with ZMQ Data**
   ```bash
   cd /root/HydraX-v2
   python3 venom_stream_pipeline.py > /tmp/venom_stream.log 2>&1 &
   ```

3. **Verify Data Flow**
   ```bash
   # Check VENOM logs
   tail -f /tmp/venom_stream.log
   
   # Should see "Processing 16 symbols" without "No live market data" errors
   ```

## Quick Start Script

Run this for automated deployment:

```bash
cd /root/HydraX-v2
export ZMQ_ENDPOINT=tcp://YOUR_MT5_IP:5555
python3 start_zmq_infrastructure.py
```

## Monitoring

### Check Data Flow
```bash
# Real-time symbol count
watch -n 1 'curl -s http://localhost:8001/market-data/health | jq .'

# Check specific symbol
curl -s http://localhost:8001/market-data/venom-feed?symbol=EURUSD | jq .
```

### Performance Metrics
```bash
# ZMQ receiver stats
journalctl -u zmq-market-receiver | grep "Messages received"

# Network latency
ping -c 10 MT5_IP_ADDRESS
```

## Troubleshooting

### EA Not Sending Data
1. Check DLL imports enabled
2. Verify libzmq.dll is accessible
3. Check Windows firewall
4. Look for errors in MT5 Experts tab

### No Data on Linux
1. Check connectivity: `nc -zv MT5_IP 5555`
2. Verify service running: `systemctl status zmq-market-receiver`
3. Check logs: `journalctl -u zmq-market-receiver -n 100`
4. Test direct connection: `python3 -c "import zmq; ctx=zmq.Context(); s=ctx.socket(zmq.SUB); s.setsockopt_string(zmq.SUBSCRIBE,''); s.connect('tcp://MT5_IP:5555'); print(s.recv_string())"`

### VENOM Not Generating Signals
1. Verify data reception: `curl http://localhost:8001/market-data/all`
2. Check TCS threshold in citadel_state.json
3. Ensure truth tracker is running
4. Check for throttle states

## Performance Tuning

### Linux Kernel
```bash
# Add to /etc/sysctl.conf
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_low_latency = 1

# Apply
sysctl -p
```

### Process Priority
```bash
# Set high priority for receiver
renice -n -10 -p $(pgrep -f zmq_market_data_receiver)
```

## Security Considerations

1. **Firewall Rules**
   - Only allow ZMQ port from MT5 IP
   - Keep Flask API (8001) local only

2. **VPN Option**
   - Consider VPN between MT5 and Linux VPS
   - Reduces latency and improves security

3. **Monitoring**
   - Set up alerts for connection drops
   - Monitor message rates for anomalies

## Expected Results

- **Latency**: <1ms on same network, <50ms across internet
- **Message Rate**: 150+ messages/second (15 pairs × 10 ticks/sec)
- **Reliability**: Auto-reconnect on network issues
- **CPU Usage**: <5% on receiver, <10% on EA
- **Memory**: <200MB for receiver with 50k message buffer

## Next Steps

1. Monitor for 24 hours to ensure stability
2. Tune buffer sizes based on actual volume
3. Add compression if bandwidth is limited
4. Consider topic-based filtering for specific pairs
5. Implement heartbeat monitoring

---

The ZMQ implementation provides industrial-grade reliability with minimal latency, solving all issues with the HTTP polling approach.