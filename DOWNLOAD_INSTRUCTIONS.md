# 📥 Enhanced MT5 Bridge - Complete Download Instructions

**Status**: ✅ **BOTH FILES READY FOR DOWNLOAD**  
**Server**: Active on port 9999  
**Date**: July 16, 2025 14:32 UTC

---

## 🚀 **Complete Setup Commands**

### **Step 1: Download Both Scripts**
```powershell
# Download the enhanced MT5 bridge agent
iwr http://134.199.204.67:9999/primary_agent_mt5_enhanced.py -OutFile primary_agent_mt5_enhanced.py

# Download the bridge rescue agent
iwr http://134.199.204.67:9999/bridge_rescue_agent.py -OutFile bridge_rescue_agent.py
```

### **Step 2: Run the Rescue Agent**
```powershell
# This will automatically configure everything
python bridge_rescue_agent.py
```

---

## 📋 **What You Get**

### **✅ primary_agent_mt5_enhanced.py** (15.4 KB)
- **Socket listener** on port 9000
- **Ping command** returns MT5 account status
- **Fire command** executes real MT5 trades
- **Enhanced console logging** with [BRIDGE] format
- **Auto-reconnect** MT5 functionality
- **HTTP API** maintains existing functionality on port 5555

### **✅ bridge_rescue_agent.py** (11.6 KB)
- **Windows firewall** configuration (port 9000)
- **MT5 auto-launch** from standard installation path
- **Enhanced agent** startup and monitoring
- **Connectivity testing** and verification
- **Comprehensive logging** to bridge_status.log

---

## 🔧 **Automated Setup Sequence**

When you run `python bridge_rescue_agent.py`, it will:

1. **🔒 Configure Firewall** - Opens port 9000 in Windows Defender
2. **🎯 Start MT5** - Launches MT5 if not already running
3. **🚀 Start Enhanced Agent** - Launches the socket bridge
4. **🧪 Test Connection** - Verifies everything is working

**Final Output:**
```
[BRIDGE] Rescue complete — listening on port 9000 and MT5 is active.
```

---

## 🎯 **File Server Status**

### **✅ Currently Serving:**
- **primary_agent_mt5_enhanced.py**: `http://134.199.204.67:9999/primary_agent_mt5_enhanced.py`
- **bridge_rescue_agent.py**: `http://134.199.204.67:9999/bridge_rescue_agent.py`

### **📊 File Details:**
- **Enhanced Agent**: 15,436 bytes (Full MT5 socket integration)
- **Rescue Agent**: 11,605 bytes (Windows automation script)
- **Server Status**: Active and responsive
- **Content-Type**: text/plain; charset=utf-8

---

## 🧪 **Testing Commands**

### **After Setup, Test Socket Functionality:**
```powershell
# Test ping command
python -c "
import socket, json
s = socket.socket()
s.connect(('localhost', 9000))
s.send(json.dumps({'command': 'ping'}).encode())
response = s.recv(1024)
print(json.loads(response.decode()))
s.close()
"
```

### **Expected Response:**
```json
{
  "status": "online",
  "account": 843859,
  "broker": "Coinexx-Demo",
  "balance": 1023.50,
  "symbols": ["XAUUSD", "GBPJPY", "USDJPY", "EURUSD"],
  "ping": "OK"
}
```

---

## 🚨 **Requirements**

### **System Requirements:**
- ✅ Windows 10/11
- ✅ Python 3.11+
- ✅ Administrator privileges (for firewall)
- ✅ MT5 installed at: `C:\Program Files\MetaTrader 5\terminal64.exe`

### **Python Dependencies:**
```powershell
pip install psutil
pip install MetaTrader5
```

---

## 🎯 **Complete Deployment Instructions**

### **Run These Commands in Order:**
```powershell
# 1. Download both scripts
iwr http://134.199.204.67:9999/primary_agent_mt5_enhanced.py -OutFile primary_agent_mt5_enhanced.py
iwr http://134.199.204.67:9999/bridge_rescue_agent.py -OutFile bridge_rescue_agent.py

# 2. Install dependencies
pip install psutil MetaTrader5

# 3. Run rescue agent (as Administrator)
python bridge_rescue_agent.py

# 4. Verify success (should show final message)
# [BRIDGE] Rescue complete — listening on port 9000 and MT5 is active.
```

### **Troubleshooting:**
- **"Enhanced agent not found"** → Ensure both files are in the same directory
- **"Firewall rule failed"** → Run PowerShell as Administrator
- **"MT5 not found"** → Verify MT5 installation path

---

**🎉 BOTH FILES READY FOR IMMEDIATE DOWNLOAD!**

*Your enhanced MT5 bridge with socket functionality is ready for deployment to Windows.*