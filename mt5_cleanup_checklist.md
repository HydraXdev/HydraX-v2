# 🚨 MT5 MASTER TERMINAL CLEANUP CHECKLIST

## CRITICAL CONTAMINATION EMERGENCY RESPONSE

**Target Server:** 3.145.84.187
**Terminal ID:** 173477FF1060D99CE79296FC73108719
**Priority:** PRODUCTION EMERGENCY

---

## 📋 EXECUTION CHECKLIST

### ✅ PRE-EXECUTION VERIFICATION

- [ ] Confirmed access to Windows server 3.145.84.187
- [ ] Verified administrator privileges
- [ ] Backup of current master terminal state created
- [ ] All users notified of maintenance window
- [ ] Emergency rollback plan prepared

### 🚨 PHASE 1: IMMEDIATE SHUTDOWN

- [ ] Connected to server 3.145.84.187
- [ ] Checked for running MT5 processes (`tasklist | findstr terminal64`)
- [ ] Terminated all MT5 processes if found (`taskkill /IM terminal64.exe /F`)
- [ ] Verified process termination (no terminal64.exe in task list)
- [ ] Located master terminal directory:
  - [ ] Path: `C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719`
  - [ ] Alternative path checked if needed
  - [ ] Directory permissions verified

### 🧹 PHASE 2: DECONTAMINATION

- [ ] Navigated to `MQL5\Files\` directory
- [ ] Counted contaminated files:
  - [ ] `.json` files: **\_** found
  - [ ] `.txt` files: **\_** found
  - [ ] `.log` files: **\_** found
- [ ] Created backup directory with timestamp
- [ ] Moved contaminated files to backup (not deleted)
- [ ] Verified `MQL5\Files\` is clean
- [ ] Cleaned `Logs\` directory of EA-generated files
- [ ] Verified no active bridge files remain

### 🛡️ PHASE 3: STERILIZATION (MANUAL)

- [ ] Started master MT5 terminal
- [ ] Opened Tools > Options > Expert Advisors
- [ ] **DISABLED** Algo Trading globally:
  - [ ] ❌ "Allow algorithmic trading" UNCHECKED
  - [ ] ❌ "Allow DLL imports" UNCHECKED
  - [ ] ❌ "Allow WebRequest for listed URL" UNCHECKED
- [ ] Applied settings (clicked OK)
- [ ] Verified EA attached to charts shows 😞 (disabled face)
- [ ] Saved profile as "BITTEN_MASTER_TEMPLATE"
- [ ] Closed MT5 terminal completely
- [ ] Verified terminal stays closed (not auto-restarting)

### 📦 PHASE 4: ARCHIVAL

- [ ] Created timestamp: MT5_MASTER_COLD_YYYYMMDD_HHMMSS.zip
- [ ] Archived clean master template directory
- [ ] Verified archive integrity (file size reasonable)
- [ ] Documented archive location
- [ ] Tested archive extraction (optional but recommended)

### 🔍 FINAL VERIFICATION

- [ ] No MT5 processes running (`tasklist | findstr terminal64` returns empty)
- [ ] MQL5\Files\ directory contains no .json/.txt/.log files
- [ ] Logs\ directory cleaned of EA files
- [ ] Master template archived successfully
- [ ] Archive stored in secure location
- [ ] Clean master ready for cloning

---

## 🚨 EMERGENCY CONTACTS

**If Issues Arise:**

- Bridge Troll Agent: Ports 5555-5557
- Production Support: [Contact Info]
- Server Admin: [Contact Info]

## 📝 EXECUTION LOG

**Executed by:** **\*\***\_\_\_\_**\*\***
**Start Time:** **\*\***\_\_\_\_**\*\***
**Completion Time:** **\*\***\_\_\_\_**\*\***
**Issues Encountered:** **\*\***\_\_\_\_**\*\***
**Resolution Notes:** **\*\***\_\_\_\_**\*\***

## ✅ SIGN-OFF

**Production Lead:** **\*\***\_\_\_\_**\*\*** Date: **\_\_\_\_**
**Technical Lead:** **\*\***\_\_\_\_**\*\*** Date: **\_\_\_\_**
**QA Verification:** **\*\***\_\_\_\_**\*\*** Date: **\_\_\_\_**

---

## 🔥 POST-CLEANUP VERIFICATION

After cleanup, test cloning process:

1. Clone master template to new directory
2. Start cloned terminal
3. Verify Algo Trading is disabled
4. Verify no bridge files are present
5. Confirm clean state propagates to clones

**Status:** [ ] VERIFIED CLEAN [ ] NEEDS REMEDIATION

---

_This cleanup addresses the contamination causing trade execution failures. Clean master = clean clones = working trades._
