# 🚨 DUPLICATE TELEGRAM ALERTS - PERMANENT FIX DOCUMENTATION

**Date**: September 7, 2025  
**Issue**: Duplicate Telegram signal alerts being sent to users  
**Root Cause**: Multiple processes sending the same signals  
**Status**: ✅ FIXED - DO NOT RESTART THE STOPPED PROCESS

---

## ⚠️ CRITICAL - FOR ALL FUTURE AGENTS ⚠️

### **THE PROBLEM**
Users receive **DUPLICATE** Telegram alerts for the same trading signal:
- One alert from `athena_broadcaster` (correct format: ⚡ RAPID, 🎯 SNIPER)  
- One alert from `elite_guard_zmq_relay` (duplicate format: different styling)

### **THE PERMANENT SOLUTION**

**✅ KEEP RUNNING:**
- `athena_broadcaster` (PM2 ID 122) - This is the CORRECT signal source
- `signals_redis_to_webapp` (PM2 ID 20) - Required for auto-fire functionality

**❌ MUST STAY STOPPED:**  
- `relay_to_telegram` (PM2 ID 10) - Runs elite_guard_zmq_relay.py, causes duplicates if both instances run
- Never run multiple instances of `elite_guard_zmq_relay.py` simultaneously

**✅ ONE OF THESE MUST RUN (NOT BOTH):**
- Either `relay_to_telegram` (PM2) OR standalone `elite_guard_zmq_relay.py` process
- This is the essential link: Elite Guard (ZMQ) → Relay → WebApp → Telegram

### **IF DUPLICATES RETURN, RUN THESE COMMANDS:**

```bash
# 1. Check for the duplicate process
ps aux | grep elite_guard_zmq_relay | grep -v grep

# 2. If found, kill it immediately  
kill [PID_NUMBER]

# 3. Verify PM2 processes are correct
pm2 list | grep -E "relay_to_telegram|athena_broadcaster|signals_redis_to_webapp"

# Expected result:
# relay_to_telegram: STOPPED ✅
# athena_broadcaster: ONLINE ✅  
# signals_redis_to_webapp: ONLINE ✅

# 4. If relay_to_telegram is online, stop it:
pm2 stop relay_to_telegram
```

### **WHY THIS HAPPENS**
1. **Signal Flow**: Elite Guard → Redis → ATHENA → Telegram (correct path)
2. **Duplicate Flow**: Elite Guard → ZMQ Relay → Telegram (wrong path)
3. **Both paths active** = User gets same signal twice in different formats

### **AUTO-FIRE DEPENDENCY**  
- `signals_redis_to_webapp` MUST stay running for auto-fire to work
- If you stop this to fix duplicates, auto-fire breaks
- Only stop the telegram broadcasting duplicates, not the webapp feed

### **VERIFICATION CHECKLIST**
After fixing duplicates:
- [ ] Users receive only ONE telegram alert per signal
- [ ] Auto-fire still works for 80%+ confidence signals  
- [ ] `athena_broadcaster` shows active in logs
- [ ] `elite_guard_zmq_relay` is NOT running as standalone process
- [ ] `relay_to_telegram` is STOPPED in PM2

### **INCIDENT HISTORY**
- **Fixed by Agent 1**: September 7, 2025 22:30 - Stopped relay_to_telegram
- **Broken by Agent 2**: September 7, 2025 23:12 - Restarted elite_guard_zmq_relay  
- **Fixed by Agent 1**: September 7, 2025 23:25 - Killed duplicate process + documented

---

## 🔒 FOR FUTURE AGENTS: FOLLOW THIS RULE

**NEVER restart `elite_guard_zmq_relay.py` or `relay_to_telegram` without checking this document first!**

If you see signal/telegram issues:
1. ✅ Read this document FIRST
2. ✅ Check the process list against the "correct configuration" above  
3. ✅ Kill duplicates, don't create new ones
4. ✅ Test that users get single alerts AND auto-fire works
5. ✅ Update this document if you discover new issues

**This prevents the duplicate alert issue from recurring every time a new agent works on the system.**