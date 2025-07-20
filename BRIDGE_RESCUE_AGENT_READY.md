# 🚨 Bridge Rescue Agent - Ready for Deployment

**Created**: July 16, 2025 14:15 UTC  
**Status**: ✅ **READY FOR DOWNLOAD**

---

## 📥 **Download Instructions**

### **✅ Step 1: Download the Script**
```powershell
iwr http://134.199.204.67:9999/bridge_rescue_agent.py -OutFile bridge_rescue_agent.py
```

### **✅ Step 2: Run the Rescue Agent**
```powershell
python bridge_rescue_agent.py
```

**Optional port specification:**
```powershell
python bridge_rescue_agent.py --port 9000
```

---

## 🛠️ **What the Rescue Agent Does**

### **🔥 Automatic Setup Sequence:**

1. **🔒 Firewall Configuration**
   - Opens TCP port 9000 in Windows Defender Firewall
   - Creates inbound rule: "BITTEN Bridge Port 9000"
   - Logs success/failure status

2. **🎯 MT5 Status Check**
   - Checks if `terminal64.exe` is running
   - If not found, launches MT5 from: `C:\Program Files\MetaTrader 5\terminal64.exe`
   - Waits up to 30 seconds for MT5 to start
   - Logs process ID when successful

3. **🚀 Enhanced Agent Launch**
   - Checks if `primary_agent_mt5_enhanced.py` is running
   - If not found, launches it via `subprocess.Popen`
   - Runs silently in background (no blocking UI)
   - Waits up to 15 seconds for agent to initialize

4. **🧪 Connectivity Test**
   - Tests socket connection to port 9000
   - Sends ping command to verify bridge response
   - Confirms MT5 bridge is responding correctly

### **📝 Logging**
- All output logged to: `bridge_status.log`
- Console output includes status updates
- Error details captured for troubleshooting

---

## 🎯 **Expected Output**

### **✅ Successful Completion:**
```
[BRIDGE] Checking Windows Firewall for port 9000...
[BRIDGE] ✅ Firewall rule already exists for port 9000
[BRIDGE] Checking MT5 status...
[BRIDGE] ✅ MT5 already running (PID: 1234)
[BRIDGE] Checking enhanced bridge agent...
[BRIDGE] 🚀 Starting enhanced bridge agent...
[BRIDGE] ✅ Enhanced agent started successfully (PID: 5678)
[BRIDGE] Testing bridge connectivity on port 9000...
[BRIDGE] ✅ Bridge responding: online
[BRIDGE] ✅ BRIDGE RESCUE COMPLETE (4/4 checks passed)
[BRIDGE] Rescue complete — listening on port 9000 and MT5 is active.
```

### **⚠️ Partial Success:**
If 3 out of 4 checks pass, the script still reports success but logs which check failed.

### **❌ Failure Scenarios:**
- MT5 not found at expected path
- `primary_agent_mt5_enhanced.py` missing from current directory
- Permission issues with firewall configuration
- Port already in use by another application

---

## 🔧 **Script Features**

### **✅ Windows Compatibility**
- **Python 3.11** compatible
- Uses Windows-specific firewall commands (`netsh`)
- Process detection via `psutil`
- Silent background process launching

### **✅ Robust Error Handling**
- 30-second timeout for command execution
- Process monitoring with PID tracking
- Comprehensive logging to file and console
- Graceful failure handling

### **✅ Non-Blocking Operation**
- No UI dialogs or blocking prompts
- Background process creation
- Silent unless errors occur
- Quick execution (typically under 30 seconds)

### **✅ Smart Detection**
- Checks existing processes before starting new ones
- Verifies firewall rules before creating duplicates
- Tests actual connectivity, not just process existence
- Handles edge cases (file not found, permission denied, etc.)

---

## 📋 **Prerequisites**

### **Required Files:**
- ✅ `primary_agent_mt5_enhanced.py` (in same directory)
- ✅ Python 3.11+ installed
- ✅ `psutil` package: `pip install psutil`

### **Required Permissions:**
- ✅ Administrator privileges (for firewall configuration)
- ✅ MT5 installation at: `C:\Program Files\MetaTrader 5\terminal64.exe`

### **Network Requirements:**
- ✅ Port 9000 available (script will configure firewall)
- ✅ No conflicting applications on port 9000

---

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **"Enhanced agent not found"**
   - Ensure `primary_agent_mt5_enhanced.py` is in the current directory
   - Check file permissions

2. **"MT5 not found"**
   - Verify MT5 installation path: `C:\Program Files\MetaTrader 5\terminal64.exe`
   - Check if MT5 is installed in a different location

3. **"Firewall rule creation failed"**
   - Run PowerShell as Administrator
   - Check Windows Defender Firewall service is running

4. **"Bridge connectivity test failed"**
   - Wait a few seconds and try again
   - Check if another application is using port 9000
   - Verify enhanced agent started successfully

### **Manual Verification:**
```powershell
# Check if processes are running
Get-Process | Where-Object {$_.Name -like "*terminal64*"}
Get-Process | Where-Object {$_.CommandLine -like "*primary_agent_mt5_enhanced*"}

# Check if port is listening
netstat -an | findstr :9000

# Check firewall rule
netsh advfirewall firewall show rule name="BITTEN Bridge Port 9000" dir=in
```

---

## 🎯 **File Server Status**

### **✅ Currently Hosted At:**
- **URL**: `http://134.199.204.67:9999/bridge_rescue_agent.py`
- **Status**: Active and serving file
- **Size**: 11.6 KB
- **Last Modified**: July 16, 2025 14:10:27 GMT

### **Download Command Ready:**
```powershell
iwr http://134.199.204.67:9999/bridge_rescue_agent.py -OutFile bridge_rescue_agent.py
python bridge_rescue_agent.py
```

---

**🚀 BRIDGE RESCUE AGENT IS READY FOR DEPLOYMENT!**

*The script will automatically configure everything needed for the enhanced MT5 bridge to work properly on Windows.*