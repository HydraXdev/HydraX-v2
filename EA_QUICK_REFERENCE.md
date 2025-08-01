# 🚀 EA DATA FLOW - QUICK REFERENCE CARD

## ✅ WORKING COMMANDS (Copy & Paste)

### 1. Check if telemetry bridge is running:
```bash
ps aux | grep zmq_telemetry_bridge_debug | grep -v grep
```

### 2. Start telemetry bridge if needed:
```bash
cd /root/HydraX-v2 && python3 zmq_telemetry_bridge_debug.py &
```

### 3. Check Elite Guard is running:
```bash
ps aux | grep elite_guard_with_citadel | grep -v grep
```

### 4. Monitor tick flow:
```bash
# See ticks arriving
tail -f /proc/$(pgrep -f elite_guard_with_citadel)/fd/1 | grep "Received tick"
```

### 5. Test complete flow:
```bash
python3 -c "import zmq; c=zmq.Context(); s=c.socket(zmq.SUB); s.connect('tcp://127.0.0.1:5560'); s.subscribe(b''); [print(f'✅ {s.recv_json()[\"symbol\"]}') for _ in range(5)]"
```

### 6. Check all ports:
```bash
ss -tlnp | grep -E '5556|5560|5557|8888' | column -t
```

## 🔴 IF BROKEN, RUN THIS:

```bash
# Kill everything and restart in order
pkill -f telemetry_pubbridge
pkill -f elite_guard_with_citadel
sleep 2

# Start bridge first
cd /root/HydraX-v2 && nohup python3 telemetry_pubbridge.py > /tmp/bridge.log 2>&1 &
sleep 2

# Start Elite Guard
cd /root/HydraX-v2 && nohup python3 elite_guard_with_citadel.py > /tmp/elite.log 2>&1 &
sleep 2

# Verify
ps aux | grep -E "telemetry|elite" | grep -v grep
```

## 📊 EXPECTED OUTPUT:

When working correctly, you should see:
```
INFO:__main__:📈 Received tick: symbol=EURUSD bid=1.15548 ask=1.15561
INFO:__main__:📈 Received tick: symbol=GBPUSD bid=1.3263 ask=1.32649
INFO:__main__:📈 Received tick: symbol=XAUUSD bid=3344.46 ask=3344.61
```

## ⚠️ NEVER DO THIS:
- ❌ Start Elite Guard before telemetry bridge
- ❌ Try to make EA bind to ports
- ❌ Change any port numbers
- ❌ Use recv_string() instead of recv_json()
- ❌ Skip the telemetry bridge