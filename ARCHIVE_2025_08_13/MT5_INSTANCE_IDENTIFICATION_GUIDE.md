# 🎯 MT5 Instance Identification System

## Overview
With 245 MT5 instances (potentially scaling to 400+), we need clear identification methods. Here's how to tell them apart:

## 1. 🔢 By Magic Number Ranges

**Instant Identification:**
- **10001-10010**: Coinexx Live (paying users, offshore)
- **20001-20005**: Forex.com Live (paying users, regulated)
- **30001-30020**: Forex.com Demo (testing)
- **40001-40010**: Coinexx Demo (offshore testing)
- **50001-50200**: Generic Demo (Press Pass trials)

**Example**: Magic number 50147 = Generic Demo instance #147

## 2. 🌐 By Port Number

**Port Allocation:**
- **9001-9010**: Coinexx Live instances
- **9101-9105**: Forex.com Live instances
- **9201-9220**: Forex.com Demo instances
- **9301-9310**: Coinexx Demo instances
- **9401-9600**: Generic Demo instances (200 ports)

**Quick Check**: Port 9523 = Generic Demo instance

## 3. 📁 By Directory Structure

```
C:\MT5_Farm\
├── Masters\
│   └── BITTEN_MASTER\     (Single universal template)
└── Users\                (Dynamic user instances)
    ├── user_12345\        (Press Pass: BITTEN_MASTER clone + demo)
    ├── user_67890\        (Paid: BITTEN_MASTER clone + live credentials)
    ├── user_54321\        (Any tier: same master + appropriate credentials)
    └── user_xxxxx\        (Infinite scaling from one master)
```

### ACTUAL IMPLEMENTATION:
- **One Master Rules All**: BITTEN_MASTER template for everyone
- **Dynamic Credential Injection**: Demo/live credentials injected post-clone
- **Universal Scaling**: Same architecture for all user tiers

## 4. 🪟 By Window Title

Each MT5 window shows:
```
"MT5 Generic_Demo #147 M50147" 
      ↑           ↑    ↑
      Type        #    Magic
```

## 5. 🆔 By Instance ID (Database)

Each instance has a unique GUID in `instance_identity.json`:
```json
{
  "instance_id": "e0ef4050-1234-5678-9abc-def012345678",
  "master_type": "Generic_Demo",
  "clone_number": 147,
  "magic_number": 50147,
  "port": 9547,
  "broker": "MetaQuotes",
  "account_type": "DEMO_AUTO"
}
```

## 6. 👤 By User Assignment

**Press Pass Assignment System:**
```python
# When user gets Press Pass:
instance = get_available_generic_demo()
assign_to_user(user_id, instance_id, expires_in_7_days)

# Instance shows:
- user_id: "telegram_123456"
- assigned_date: "2025-01-15"
- expires: "2025-01-22"
- status: "active"
```

## 7. 📊 Quick Reference Dashboard

 < /dev/null |  Instance Type | Count | Magic Range | Port Range | Purpose |
|--------------|-------|-------------|------------|---------|
| Generic Demo | 200 | 50001-50200 | 9401-9600 | Press Pass (7-day) |
| Forex Demo | 20 | 30001-30020 | 9201-9220 | Regulated testing |
| Coinexx Demo | 10 | 40001-40010 | 9301-9310 | Offshore testing |
| Forex Live | 5 | 20001-20005 | 9101-9105 | Regulated trading |
| Coinexx Live | 10 | 10001-10010 | 9001-9010 | Offshore trading |

## 8. 🔍 Monitoring Commands

**PowerShell (on Windows):**
```powershell
# List all instances
powershell C:\MT5_Farm\instance_tracker.ps1 -Action list

# Check farm status
powershell C:\MT5_Farm\clone_realistic_farm.ps1 -Action status

# Monitor live instances
powershell C:\MT5_Farm\monitor_dashboard.ps1
```

**Python (from Linux):**
```python
# Get instance by user
from mt5_instance_manager import get_user_instance
instance = get_user_instance(user_id="telegram_123456")

# Check available Press Pass instances
available = get_available_instances("Generic_Demo")
print(f"{len(available)} Press Pass instances available")
```

## 9. 🎨 Visual Indicators

**Desktop Shortcuts:**
- Each instance has a named shortcut
- Format: `MT5_Generic_Demo_147_M50147.lnk`
- Icons show broker logo

**Status Files:**
- Green: `bitten_status_secure.txt` updated < 5 min
- Yellow: Updated 5-15 min ago  
- Red: No update > 15 min (likely inactive)

## 10. ♻️ Recycling System

**Press Pass Auto-Recycling:**
- Runs daily at 3 AM
- Checks instances assigned > 7 days
- Clears user data and configs
- Returns to available pool
- Logs all recycling actions

**Manual Recycling:**
```powershell
# Force recycle specific instance
Recycle-Instance -InstanceId "Generic_Demo_147"

# Bulk recycle expired
powershell C:\MT5_Farm\recycle_press_pass.ps1
```

## Summary

The system is designed for:
- **Automation**: Self-managing Press Pass rotation
- **Scalability**: Easy to add more instances
- **Tracking**: Every instance uniquely identifiable
- **Efficiency**: Quick user assignment and recycling

Most important identifiers:
1. **Magic Number** - Instant type identification
2. **Port Number** - Network routing
3. **Directory Name** - File system location
4. **Instance ID** - Database tracking
