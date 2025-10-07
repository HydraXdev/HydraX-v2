# 🚨 CRITICAL INFRASTRUCTURE CHANGE - JULY 27, 2025

## **IMMEDIATE ARCHITECTURE CHANGE - FOREXVPS MIGRATION**

**Date**: July 27, 2025
**Authority**: Project Owner
**Priority**: CRITICAL - Affects all MT5 operations
**Agent**: Claude

---

## 🛑 **MANDATORY CHANGES - EFFECTIVE IMMEDIATELY**

### **1. MT5 INFRASTRUCTURE MIGRATION**

**OLD ARCHITECTURE (DEPRECATED)**:

- ❌ Docker containers with Wine
- ❌ Local MT5 instances on Linux server
- ❌ Container cloning system
- ❌ Wine-based MT5 terminals
- ❌ Local file-based communication (fire.txt/trade_result.txt)

**NEW ARCHITECTURE (PRODUCTION)**:

- ✅ ForexVPS hosted MT5 terminals
- ✅ Pre-configured EA on VPS instances
- ✅ External VPS management
- ✅ Direct network communication
- ✅ VPS-based clone deployment

---

## 📋 **IMPLEMENTATION DIRECTIVES**

### **For All Developers and Agents**:

1. **DISREGARD ALL DOCKER/WINE REFERENCES**
   - Ignore any code related to Docker containers
   - Skip all Wine-based MT5 implementations
   - Do not use container cloning scripts
   - Bypass local MT5 terminal management

2. **NEW SIGNAL FLOW**

   ```
   VENOM Signal Generation (Local)
           ↓
   BittenCore Processing (Local)
           ↓
   Network Transmission to ForexVPS
           ↓
   EA Execution on VPS MT5 Terminal
           ↓
   Result Callback to BittenCore
   ```

3. **CODE MODIFICATIONS REQUIRED**
   - Remove all Docker exec commands
   - Remove Wine path references
   - Update fire execution to use network API
   - Change from file-based to network communication

4. **QUARANTINE OLD INFRASTRUCTURE**
   - Move all Docker/Wine code to `/archive/docker_wine_deprecated/`
   - Firewall ports previously used for containers
   - Lock down container-related endpoints
   - Preserve code for future reference only

---

## 🔒 **SECURITY MEASURES**

### **Firewall Rules**

```bash
# Block all container-related ports
iptables -A INPUT -p tcp --dport 5900:5999 -j DROP  # VNC ports
iptables -A INPUT -p tcp --dport 9000:9999 -j DROP  # Bridge ports
iptables -A INPUT -p tcp --dport 10090:10099 -j DROP # Test ports
```

### **Code Isolation**

- All Docker/Wine code moved to: `/archive/docker_wine_deprecated/`
- Production code must NOT reference:
  - `/root/.wine*`
  - `docker exec`
  - `mt5_user_*` containers
  - `fire.txt` or `trade_result.txt` local files

---

## 🎯 **PRODUCTION IMPLEMENTATION**

### **ForexVPS Integration Points**

1. **Signal Transmission**
   - Use HTTPS POST to VPS endpoints
   - Authenticate with API keys
   - Send encrypted signal payloads

2. **EA Communication**
   - EA polls ForexVPS API for signals
   - Executes trades on VPS MT5 terminal
   - Posts results back to BittenCore

3. **User Management**
   - Each user assigned VPS instance
   - Credentials managed by ForexVPS
   - Scaling handled externally

### **Code That Must Be Updated**

1. **`/src/mt5_bridge/mt5_bridge_adapter.py`**
   - Change from file-based to API-based
   - Remove Docker exec commands
   - Add VPS endpoint configuration

2. **`/bitten_production_bot.py`**
   - Remove container creation logic
   - Update `/connect` to register with VPS
   - Change credential injection method

3. **`/src/bitten_core/fire_router.py`**
   - Route signals to VPS API
   - Remove local file operations
   - Add network retry logic

---

## 📝 **DEVELOPER INSTRUCTIONS**

### **When You See Docker/Wine Code**:

```python
# OLD - DO NOT USE
docker_exec = f"docker exec mt5_user_{user_id} ..."
wine_path = "/root/.wine/drive_c/..."

# NEW - USE THIS PATTERN
vps_response = requests.post(
    f"{FOREXVPS_API_URL}/execute",
    json={"user_id": user_id, "signal": signal_data},
    headers={"Authorization": f"Bearer {VPS_API_KEY}"}
)
```

### **Environment Variables to Add**:

```bash
FOREXVPS_API_URL=https://api.forexvps.com/v1
VPS_API_KEY=your_api_key_here
VPS_WEBHOOK_URL=https://yourserver.com/vps/callback
```

---

## 🚫 **DEPRECATED COMPONENTS**

The following are NO LONGER IN USE:

- `hydrax-user-template:latest` Docker image
- `bitten-golden-master:v1` Docker image
- All MT5 Wine containers
- Container cloning scripts
- Local MT5 terminal management
- File-based EA communication
- Docker-based user isolation

---

## ✅ **WHAT REMAINS THE SAME**

- VENOM signal generation logic
- CITADEL Shield analysis
- BittenCore processing
- Telegram bot functionality
- WebApp interface
- User management system
- Database operations

---

## 🎯 **ACTION ITEMS**

1. **Immediate**: Stop all Docker/Wine related development
2. **Today**: Update fire execution to use VPS API
3. **This Week**: Migrate all active users to ForexVPS
4. **Archive**: Move deprecated code to archive folder
5. **Document**: Update all references in documentation

---

## 📌 **FINAL NOTES**

This change is **PERMANENT** for the current production phase. The Docker/Wine infrastructure is being preserved for potential future use but must be completely isolated from production code.

All new development must assume:

- MT5 terminals are hosted on ForexVPS
- EA is pre-configured on VPS instances
- Communication is via network API, not local files
- User scaling is handled by VPS provider

**Questions about this change should be directed to the project owner.**

---

**Document Authority**: Project Owner via Claude
**Effective Date**: July 27, 2025
**Status**: MANDATORY - IMMEDIATE IMPLEMENTATION
