# ZMQ QUICK SETUP GUIDE

## MT5 EA Setup (Windows)

### 1. Get libzmq.dll
- Download: https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4-mingw.zip
- Extract: `bin/x64/libzmq.dll`
- Copy to: `C:\Program Files\MetaTrader 5\Libraries\` (create if needed)

### 2. Enable DLL Imports
⚠️ **CRITICAL: Must be enabled before attaching EA**
- Tools → Options → Expert Advisors
- ✅ Allow DLL imports
- Click OK

### 3. Compile & Attach EA
- Copy `BITTENBridge_TradeExecutor_ZMQ_v6.mq5` to Experts folder
- Open in MetaEditor (F4)
- Compile (F7) - must see "0 errors, 0 warnings"
- Attach to any chart
- Settings:
  - ZMQ Endpoint: `tcp://*:5555`
  - Stream all pairs: Yes
- Click OK

### 4. Verify Running
- Check Experts tab for:
  - "✅ ZMQ Publisher bound to: tcp://*:5555"
  - "📡 ZMQ Publisher: ACTIVE"

### 5. Windows Firewall
```cmd
netsh advfirewall firewall add rule name="MT5 ZMQ" dir=in action=allow protocol=TCP localport=5555
```

## Linux Setup

### 1. Install PyZMQ
```bash
pip install pyzmq
```

### 2. Test Connection
```bash
# Replace with your MT5 IP
export MT5_IP=192.168.1.100
python3 -c "import zmq; c=zmq.Context(); s=c.socket(zmq.SUB); s.setsockopt_string(zmq.SUBSCRIBE,''); s.connect('tcp://$MT5_IP:5555'); print(s.recv_string())"
```

### 3. Start ZMQ Receiver
```bash
cd /root/HydraX-v2
export ZMQ_ENDPOINT=tcp://$MT5_IP:5555
python3 zmq_market_data_receiver.py
```

### 4. Verify Data Flow
```bash
curl http://localhost:8001/market-data/health
```

## Troubleshooting

### EA Errors
- **DLL not found**: Ensure libzmq.dll is in Libraries folder
- **Failed to bind**: Check port 5555 not in use
- **No ZMQ messages**: Check Windows firewall

### Python Errors
- **Connection refused**: Check MT5 IP and port
- **No data**: Verify EA shows "ZMQ Publisher: ACTIVE"

### Common Issues
1. **DLL imports disabled**: Must enable BEFORE attaching EA
2. **Wrong IP**: Use actual MT5 machine IP, not localhost
3. **Firewall blocking**: Add exception for port 5555

## Success Indicators
- EA: Messages sent counter increasing
- Linux: `active_symbols: 15` in health check
- No errors in EA Experts tab

---

The EA maintains the file-based trading system while streaming all market data via ZMQ for maximum reliability and performance.