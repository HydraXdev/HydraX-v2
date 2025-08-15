# 🚨 EMERGENCY MT5 MASTER CLEANUP - DEPLOYMENT PACKAGE

## MISSION OVERVIEW
**Target:** Windows Server 3.145.84.187  
**Terminal ID:** 173477FF1060D99CE79296FC73108719  
**Crisis:** Contaminated master MT5 template causing trade execution failures  

## 📦 DEPLOYMENT PACKAGE CONTENTS

| File | Purpose | Usage |
|------|---------|-------|
| `emergency_mt5_cleanup.ps1` | **Main PowerShell cleanup script** | Primary automated cleanup |
| `emergency_mt5_cleanup.bat` | **Batch script alternative** | Fallback for PowerShell issues |
| `verify_cleanup_success.ps1` | **Post-cleanup verification** | Confirms decontamination success |
| `mt5_cleanup_checklist.md` | **Manual execution checklist** | Step-by-step verification |
| `remote_execution_guide.md` | **Connection methods guide** | How to access the server |

## 🚀 QUICK DEPLOYMENT

### Option 1: Automated PowerShell (Recommended)
```powershell
# 1. Connect to server 3.145.84.187
# 2. Copy emergency_mt5_cleanup.ps1 to C:\temp\
# 3. Execute with admin privileges:
powershell -ExecutionPolicy Bypass -File C:\temp\emergency_mt5_cleanup.ps1
```

### Option 2: Batch Script Fallback
```cmd
# 1. Connect to server 3.145.84.187
# 2. Copy emergency_mt5_cleanup.bat to C:\temp\
# 3. Run as administrator:
C:\temp\emergency_mt5_cleanup.bat
```

### Option 3: Manual Execution
```
Follow the step-by-step checklist in mt5_cleanup_checklist.md
```

## 🔍 VERIFICATION PROCESS

After cleanup execution:
```powershell
# Run verification script
powershell -ExecutionPolicy Bypass -File C:\temp\verify_cleanup_success.ps1
```

**Success Criteria:**
- ✅ No MT5 processes running
- ✅ MQL5\Files directory clean of .json/.txt/.log files  
- ✅ EA logs removed from Logs directory
- ✅ Contaminated files backed up (not deleted)
- ✅ Clean master template archived
- ✅ Algo Trading disabled in MT5 configuration

## 🎯 EXPECTED RESULTS

**Before Cleanup:**
- ❌ Master MT5 running with live/demo account
- ❌ EA actively writing bridge files
- ❌ Algo Trading enabled
- ❌ All cloned accounts contaminated
- ❌ Trade execution failures

**After Cleanup:**  
- ✅ Master MT5 stopped and sterilized
- ✅ No bridge files in template
- ✅ Algo Trading disabled globally
- ✅ Clean template ready for cloning
- ✅ Future clones will be sterile

## 🛠️ MANUAL CONFIGURATION REQUIRED

After automated cleanup, manually:
1. Start MT5 terminal
2. Tools > Options > Expert Advisors
3. **UNCHECK** "Allow algorithmic trading"
4. **UNCHECK** "Allow DLL imports"  
5. **UNCHECK** "Allow WebRequest for listed URL"
6. Save profile as "BITTEN_MASTER_TEMPLATE"
7. Close terminal

## 🚨 CRITICAL NOTES

- **PRODUCTION EMERGENCY:** This fixes contamination causing trade failures
- **DATA SAFETY:** Scripts backup contaminated files (don't delete)
- **REVERSIBLE:** Archive created for rollback if needed
- **TESTED:** Scripts include comprehensive error handling
- **VERIFICATION:** Success can be confirmed with verification script

## 📞 EMERGENCY CONTACTS

**If Issues Arise:**
- Bridge Troll Agent: Ports 5555-5557
- Terminal ID: 173477FF1060D99CE79296FC73108719
- Server: 3.145.84.187

## 🏆 SUCCESS METRICS

**Resolution Time:** < 30 minutes  
**Downtime:** Minimal (only during cleanup)  
**Risk Level:** Low (backup/archive strategy)  
**Impact:** High (fixes all future account clones)

---

**Execute immediately to restore clean trading environment.**  
**Clean master = clean clones = working trades.**