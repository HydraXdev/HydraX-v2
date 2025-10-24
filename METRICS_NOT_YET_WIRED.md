# ⚠️ METRICS NOT YET WIRED TO LIVE BACKEND - October 12, 2025

## 📊 FRONTEND DISPLAYS BUT BACKEND DOESN'T UPDATE

The following metrics are displayed in the frontend but are **NOT** being updated by the live backend systems:

---

## 🎮 GAMIFICATION METRICS (NOT WIRED)

### **XP System**
**Frontend Displays**: `xp`, `stx`, `xpAmmo`, `medals`
**Backend Status**: ❌ NOT wired to Firebase
**Where Expected**: `users/{uid}` document in Firebase

**What Exists But Not Connected**:
- XP calculation system: `/root/HydraX-v2/src/bitten_core/xp_economy.py`
- XP daemon: `/root/HydraX-v2/tools/xp_daemon.py`
- Achievement system: `/root/HydraX-v2/src/bitten_core/achievement_system.py`
- XP database: SQLite tables exist but not synced to Firebase

**Impact**:
- Users see XP = 0, medals = 0, stx = 0 (default values)
- No XP awarded for trades, streaks, challenges
- Shop system won't work (requires XP balance)
- Level progression not tracked

---

### **Achievements**
**Frontend Displays**: `achievements` array
**Backend Status**: ❌ NOT wired to Firebase
**Where Expected**: `users/{uid}.achievements`

**What Exists But Not Connected**:
- Achievement system: `/root/HydraX-v2/src/bitten_core/achievement_system.py`
- Achievement definitions in code
- No Firebase sync when achievements earned

**Impact**:
- Users see empty achievements list
- No achievement notifications
- No achievement-based unlocks

---

### **Longest Streak**
**Frontend Displays**: `longestStreak` (consecutive wins)
**Backend Status**: ❌ NOT calculated or written to Firebase
**Where Expected**: `users/{uid}.longestStreak`

**Current Behavior**:
- `close_active_trade()` updates wins/losses counters ✅
- But does NOT calculate or update longestStreak ❌

**What's Needed**:
- Calculate current streak on each win/loss
- Update longestStreak if current > longest
- Write to Firebase users/{uid}

---

## 👤 USER PROFILE METRICS (NOT WIRED)

### **Display Name**
**Frontend Displays**: `displayName`
**Backend Status**: ❌ NOT synced from backend to Firebase
**Where Expected**: `users/{uid}.displayName`

**Current Behavior**:
- Users can set displayName in frontend
- But backend doesn't update it from any source
- No sync from Telegram username or MT5 account name

---

### **Tier**
**Frontend Displays**: `tier` (RECRUIT, COMMANDER, FANG)
**Backend Status**: ❌ NOT synced from backend to Firebase
**Where Expected**: `users/{uid}.tier`

**Current Behavior**:
- Tier exists in backend SQLite (fire_mode_database.py)
- But NOT synced to Firebase on tier changes
- Frontend shows default or stale tier

**What's Needed**:
- When user upgrades tier in backend, write to Firebase
- Sync tier from payment/subscription system

---

### **Initial Capital**
**Frontend Displays**: Used for growth % calculation in WarChest
**Backend Status**: ❌ NOT written to Firebase
**Where Expected**: `users/{uid}.initialCapital`

**Current Behavior**:
- WarChest calculates growth as: `(equity - initialCapital) / initialCapital`
- But initialCapital is never set from backend
- Defaults to 0 or falls back to hardcoded values

**What's Needed**:
- Write initialCapital when user first created
- Or capture first balance from EA heartbeat

---

## 🤝 REFERRAL SYSTEM (NOT WIRED)

### **Referral Metrics**
**Frontend Displays**: `referralLink`, `referralCount`, `referralDiscountPct`
**Backend Status**: ❌ NOT synced to Firebase
**Where Expected**: `users/{uid}` document

**What Exists But Not Connected**:
- Referral system: `/root/HydraX-v2/standalone_referral_system.py`
- Referral SQLite database
- No Firebase sync when referrals occur

**Impact**:
- Users see referralCount = 0
- Referral discounts not reflected in UI
- Referral link exists but stats don't update

---

## 📈 TRADE STATISTICS (PARTIAL WIRING)

### **Currently Wired** ✅:
- `balance` - Updated on EA heartbeat
- `equity` - Updated on EA heartbeat
- `wins` - Updated on trade close (TP HIT)
- `losses` - Updated on trade close (SL HIT)

### **NOT Wired** ❌:
- `longestStreak` - Not calculated
- Total P&L tracking (sum of all trades)
- Win rate % (calculated in frontend from wins/losses)
- Average hold time
- Best/worst trades

---

## 🎯 PRIORITY RECOMMENDATIONS

### **HIGH PRIORITY** (Critical for User Experience):

1. **Longest Streak Calculation**
   - Add to `close_active_trade()` in firebase_backend.py
   - Calculate on each trade close
   - Write to Firebase users/{uid}

2. **Initial Capital Tracking**
   - Capture first balance from EA heartbeat
   - Write to Firebase on user creation
   - Required for accurate growth % in WarChest

3. **Tier Sync**
   - Hook into tier upgrade events
   - Sync tier changes to Firebase immediately

### **MEDIUM PRIORITY** (Enhances Experience):

4. **XP System Integration**
   - Wire XP awards to Firebase after each trade
   - Update medals, stx, xpAmmo from XP daemon
   - Enable XP shop functionality

5. **Achievement System**
   - Sync achievement unlocks to Firebase
   - Show achievement notifications in UI

6. **Display Name Sync**
   - Sync from Telegram username on first login
   - Allow users to customize in frontend

### **LOW PRIORITY** (Nice to Have):

7. **Referral System Sync**
   - Update referralCount when referrals join
   - Update referralDiscountPct when thresholds hit

---

## 🔧 WHERE TO ADD MISSING INTEGRATIONS

### **1. Longest Streak** (Add to confirm_listener.py):
```python
# In close_active_trade() function after updating wins/losses:

# Calculate and update streak
cur.execute("SELECT wins, losses FROM fires WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
recent_trades = cur.fetchall()

current_streak = 0
longest_streak = 0
for trade in recent_trades:
    if outcome == 'TP HIT':
        current_streak += 1
        longest_streak = max(longest_streak, current_streak)
    else:
        current_streak = 0

# Update Firebase
from firebase_backend import update_user_data
update_user_data(user_id, {'longestStreak': longest_streak})
```

### **2. Initial Capital** (Add to command_router.py):
```python
# In _handle_heartbeat() after updating balance:

# Check if this is first time seeing this user
cur.execute("SELECT initialCapital FROM user_stats WHERE user_id = ?", (user_id,))
if not cur.fetchone():
    from firebase_backend import update_user_data
    update_user_data(user_id, {'initialCapital': float(balance)})
```

### **3. XP System** (Wire xp_daemon.py to Firebase):
```python
# In xp_daemon.py after awarding XP:

from firebase_backend import update_user_data
update_user_data(user_id, {
    'xp': new_xp_total,
    'medals': medal_count,
    'stx': stx_balance,
    'xpAmmo': xp_ammo_count
})
```

### **4. Tier Sync** (Add to fire_mode_database.py):
```python
# In upgrade_tier() after tier change:

from firebase_backend import update_user_data
update_user_data(user_id, {'tier': new_tier})
```

---

## ✅ WHAT IS CURRENTLY WIRED

**Backend → Firebase Writes**:
- ✅ Signals generation
- ✅ Active trades on position_opened
- ✅ Trade history on position_closed
- ✅ Balance/equity updates on EA heartbeat
- ✅ Wins/losses counters on trade close
- ✅ Mission creation

**Frontend → Firebase Reads**:
- ✅ All pages read from Firebase collections
- ✅ Real-time listeners for live updates
- ✅ User controls (risk, autoFire, etc.) write to Firebase

---

## 📊 SUMMARY

**Wired Metrics**: 7 (signals, active trades, trade history, balance, equity, wins, losses)
**NOT Wired Metrics**: 13 (xp, stx, xpAmmo, medals, achievements, longestStreak, displayName, tier, initialCapital, referralLink, referralCount, referralDiscountPct, total P&L tracking)

**Frontend Shows but Backend Doesn't Update**:
- All gamification metrics (XP, medals, achievements)
- Longest streak calculation
- Initial capital for growth tracking
- Tier changes from backend
- Referral statistics

**These metrics will show default/zero values until backend integration is added.**

---

**Document Created**: October 12, 2025
**Status**: Identified gaps, ready for implementation
**Next Steps**: Prioritize HIGH PRIORITY items for next integration session
