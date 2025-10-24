# 🧪 COMPREHENSIVE FRONTEND TEST PLAN - October 12, 2025

## 🎯 TEST OBJECTIVE
Verify EVERY button, timer, clock, and interactive element works correctly with Firebase real-time updates.

---

## 📱 PAGES TO TEST (9 Core Pages)

### 1. **AlertFeed** (`/signals`)

#### Buttons & Interactions:
- [ ] **"🎯 VIEW MISSION BRIEF" button** (each signal card)
  - Click → Opens MissionBrief page with signal details
  - URL: `/mission/{signal_id}`

#### Real-Time Elements:
- [ ] **Signal cards update live** (no refresh needed)
  - New signals appear automatically
  - Firebase listener: `collection(db, "signals")` with `onSnapshot`

- [ ] **Timestamp display** updates (e.g., "2 minutes ago")
  - Should update every minute without refresh

- [ ] **Status badges** change in real-time
  - "NEW" → "ACTIVE" → "EXPIRED"

#### Data Verification:
- [ ] Confidence % displays correctly (not 0%)
- [ ] Pattern names display (not "UNKNOWN")
- [ ] Pair/symbol displays correctly
- [ ] Session displays (LONDON, NY, etc.)

---

### 2. **MissionBrief** (`/mission/:id`)

#### Buttons & Interactions:
- [ ] **"🔫 AUTHORIZE STRIKE" button**
  - Click → Opens StrikeAuthorizationModal
  - Modal slides up with mission details

- [ ] **"← BACK TO SIGNALS" button**
  - Click → Navigates to /signals

#### Modal Testing (StrikeAuthorizationModal):
- [ ] **Modal opens** without cutting off right side (MOBILE FIX)
- [ ] **"PREFLIGHT CHECK" section** displays
  - Signal data shows correctly
  - Position sizing displays
  - Risk assessment visible

- [ ] **"🚀 EXECUTE STRIKE" button**
  - Click → Sends fire command
  - Shows "TRADE EXECUTED!" message
  - After 3 seconds → Redirects to /battlefield (NOT /signals)

- [ ] **Modal close prevention** during execution
  - Can't close by clicking outside during "executing" stage
  - Can't close by clicking outside during "success" stage

#### Real-Time Elements:
- [ ] **Mission status** updates live
  - "PENDING" → "EXECUTING" → "COMPLETED"

- [ ] **Countdown timer** (if mission has expiry)
  - Should tick down in real-time
  - Format: "Expires in 23:45"

---

### 3. **Battlefield** (`/battlefield`)

#### Buttons & Interactions:
- [ ] **"🎯 RETURN TO SIGNALS" button** (FIXED - single full-width button)
  - Click → Navigates to /signals
  - War Chest button REMOVED ✅

#### Real-Time Elements:
- [ ] **Active trade cards** update live
  - P&L updates without refresh
  - Current price updates
  - Equity line chart updates

- [ ] **Stats header** updates live
  - Balance updates from EA heartbeat
  - Equity updates
  - Wins/Losses counters update on trade close
  - Longest streak updates (NEW FIX) ✅

- [ ] **Trade sparklines** animate
  - History array grows as price updates come in

#### Data Verification:
- [ ] Wins/Losses display correctly (not hardcoded)
- [ ] Balance shows real MT5 balance (not 10000)
- [ ] Longest streak displays (not 0)
- [ ] Active trades show "No active positions" if empty

---

### 4. **CommandCenter** (`/command-center`)

#### Buttons & Interactions:
- [ ] **Risk slider** (0.25% - 5%)
  - Drag → Updates Firebase immediately
  - Value displays next to slider

- [ ] **Auto-fire toggle**
  - Click → Writes to Firebase `users/{uid}.autoFire`
  - Visual state changes (on/off)

- [ ] **Weekend close toggle**
  - Click → Writes to Firebase `users/{uid}.closeWeekends`

- [ ] **Notifications toggle**
  - Click → Writes to Firebase `users/{uid}.notifications`

#### Real-Time Elements:
- [ ] **User stats** update live
  - XP counter updates when XP awarded (NEW FIX) ✅
  - Balance updates from EA heartbeat
  - Accuracy % recalculates on trade close
  - Total shots updates

- [ ] **Recent trades** section updates
  - Last 5 trades display
  - Updates when new trade closes

#### Data Verification:
- [ ] XP displays (not 0) after trade
- [ ] Display name shows (not empty)
- [ ] Tier displays correctly
- [ ] Recent trades show outcomes (TP HIT/SL HIT)

---

### 5. **WarChest** (`/stats`)

#### Buttons & Interactions:
- [ ] **Tab buttons** (Overview, History, Statistics)
  - Click → Switches active tab
  - Content changes

#### Real-Time Elements:
- [ ] **Trade history table** updates live
  - New completed trades appear automatically
  - Firebase listener: `collection(db, "trade_history")`

- [ ] **Statistics** recalculate live
  - Win rate %
  - Total profit
  - Max drawdown (NEW - real calculation) ✅
  - Profit factor
  - Risk/reward ratio

- [ ] **Growth percentage** displays correctly (NEW FIX) ✅
  - Formula: `((equity - initialCapital) / initialCapital) * 100`
  - initialCapital now tracked from first EA heartbeat

#### Data Verification:
- [ ] All trades show outcomes (TP HIT/SL HIT, not WIN/LOSS)
- [ ] Growth % not NaN or Infinity
- [ ] Max drawdown calculated (not hardcoded 12.5%)
- [ ] Total profit sums correctly

---

### 6. **Profile** (`/profile`)

#### Status: Secondary page (not critical for trading)

#### Buttons & Interactions:
- [ ] Profile editing works (if implemented)
- [ ] Save button writes to Firebase (if exists)

---

### 7. **Billing** (`/billing`)

#### Status: Secondary page (not critical for trading)

#### Buttons & Interactions:
- [ ] Subscription management (if implemented)

---

### 8. **Training** (`/training`)

#### Status: Content page

#### Verification:
- [ ] Educational content displays
- [ ] Navigation works

---

### 9. **Login/Auth** (`/auth/login`)

#### Buttons & Interactions:
- [ ] Login button works
- [ ] Redirects to appropriate page after login
- [ ] Firebase auth state changes

---

## ⏰ TIMER & CLOCK TESTING

### Mission Countdown Timers:
```typescript
// Should update every second
setInterval(() => {
  // Calculate time remaining
  const remaining = expiresAt - Date.now()
  // Format as MM:SS
  const minutes = Math.floor(remaining / 60000)
  const seconds = Math.floor((remaining % 60000) / 1000)
  display = `${minutes}:${seconds.toString().padStart(2, '0')}`
}, 1000)
```

**Test**:
- [ ] Timer counts down in real-time
- [ ] Format is correct (MM:SS)
- [ ] Timer doesn't freeze
- [ ] Timer reaches 0 and shows "EXPIRED"

### Timestamp Displays (Relative Time):
```typescript
// "2 minutes ago", "5 hours ago", etc.
// Should update every minute
```

**Test**:
- [ ] Timestamps update without refresh
- [ ] Format switches appropriately (minutes → hours → days)
- [ ] "Just now" for recent items

### Live Price Updates:
```typescript
// In Battlefield active trades
// Current price should update in real-time from Firebase
```

**Test**:
- [ ] Current price updates smoothly
- [ ] Equity line chart extends
- [ ] P&L recalculates live

---

## 🔥 FIREBASE REAL-TIME TESTING

### Signals Collection:
**Test Setup**: Generate new signal via Elite Guard

**Verification**:
- [ ] AlertFeed page shows new signal **without refresh**
- [ ] Signal appears within 1-2 seconds
- [ ] All fields populate correctly

**Console Test**:
```javascript
// Open browser console on /signals
// Watch for: "📊 Received X signals from Firebase"
```

### Active Trades Collection:
**Test Setup**: Execute trade via /api/fire

**Verification**:
- [ ] Battlefield page shows new trade **without refresh**
- [ ] Trade card appears immediately
- [ ] Real-time P&L updates start

### Trade History Collection:
**Test Setup**: Wait for trade to close (TP/SL hit)

**Verification**:
- [ ] Trade disappears from Battlefield **without refresh**
- [ ] Trade appears in WarChest history **without refresh**
- [ ] Wins/losses counter updates **without refresh**
- [ ] Longest streak updates **without refresh** (NEW) ✅

### User Document Updates:
**Test Setup**: EA sends heartbeat with new balance

**Verification**:
- [ ] Balance updates in CommandCenter **without refresh**
- [ ] Balance updates in Battlefield header **without refresh**
- [ ] Equity updates everywhere **without refresh**

---

## 🧪 INTEGRATION TESTING SCENARIOS

### Scenario 1: Complete Trade Flow
1. Start on AlertFeed (`/signals`)
2. Wait for new signal to appear (real-time)
3. Click "VIEW MISSION BRIEF"
4. Click "AUTHORIZE STRIKE"
5. Review preflight checks
6. Click "EXECUTE STRIKE"
7. Verify redirect to Battlefield (NOT signals)
8. See active trade appear
9. Watch P&L update in real-time
10. Wait for trade to close
11. Verify disappears from Battlefield
12. Navigate to WarChest
13. Verify appears in trade history
14. Verify wins counter incremented
15. Verify longest streak updated (if applicable)

### Scenario 2: Multi-Tab Real-Time Sync
1. Open Battlefield in Tab 1
2. Open CommandCenter in Tab 2
3. Execute trade in Tab 1
4. Verify balance updates in BOTH tabs without refresh
5. Wait for trade close
6. Verify stats update in BOTH tabs

### Scenario 3: Mobile Responsive Testing
1. Resize browser to 375px width (iPhone)
2. Open MissionBrief and click "AUTHORIZE STRIKE"
3. Verify modal doesn't cut off right side (FIXED) ✅
4. Verify buttons fit properly
5. Test Battlefield footer button fits full width (FIXED) ✅

---

## 🐛 BUG VERIFICATION (Previously Fixed)

### Bug 1: Modal Cutting Off on Mobile
**Status**: ✅ FIXED (added `!w-[calc(100vw-1rem)]` with !important)

**Test**:
- [ ] Open MissionBrief on mobile viewport
- [ ] Click "AUTHORIZE STRIKE"
- [ ] Verify right side is visible
- [ ] Verify all content fits in viewport

### Bug 2: Wrong Redirect After Fire
**Status**: ✅ FIXED (changed to `/battlefield` with `replace: true`)

**Test**:
- [ ] Execute trade from MissionBrief
- [ ] After "TRADE EXECUTED!" message
- [ ] Verify redirects to `/battlefield` (not `/signals`)
- [ ] Verify can't go back to execution screen

### Bug 3: Battlefield Button Layout
**Status**: ✅ FIXED (removed War Chest button, single full-width button)

**Test**:
- [ ] Open Battlefield on mobile
- [ ] Verify only ONE button at bottom
- [ ] Verify button is full width
- [ ] Verify says "RETURN TO SIGNALS"

---

## 📊 DATA VERIFICATION CHECKLIST

### NOT Hardcoded (Must Be Live Data):
- [ ] ❌ Balance = 10000 (must show real MT5 balance)
- [ ] ❌ Wins = 4, Losses = 1 (must be real counters)
- [ ] ❌ Longest Streak = 3 (must be calculated)
- [ ] ❌ Max Drawdown = 12.5% (must be calculated)
- [ ] ❌ XP = 0 (must update after trades)
- [ ] ❌ Growth % = NaN (must calculate from initialCapital)
- [ ] ❌ Confidence = 0% (must show real confidence)

### Must Be Real-Time (Firebase onSnapshot):
- [ ] Signals appearing on AlertFeed
- [ ] Active trades on Battlefield
- [ ] Balance/equity updates
- [ ] Trade history additions
- [ ] Wins/losses counters

---

## 🚀 TESTING COMMANDS

### Start Frontend:
```bash
cd /root/throne
npm run dev
# Visit: http://134.199.204.67:3000
```

### Start Backend Services:
```bash
pm2 restart command_router
pm2 restart confirm_listener
pm2 restart webapp
```

### Monitor Logs:
```bash
# Watch for Firebase writes
tail -f /root/HydraX-v2/*.log | grep "Firebase"

# Watch for trade executions
pm2 logs confirm_listener | grep "Position opened\|Position closed"

# Watch for EA heartbeats
pm2 logs command_router | grep "User data synced"
```

### Browser Console Tests:
```javascript
// On any page with Firebase
console.log('Firebase listeners active:',
  document.querySelectorAll('[data-firebase-listener]').length
);

// Check for real-time updates
// Should see: "📊 Received X signals from Firebase"
```

---

## ✅ TEST COMPLETION CRITERIA

**All tests pass when**:
1. ✅ Every button clickable and performs correct action
2. ✅ Every navigation works (no broken links)
3. ✅ Every timer counts down in real-time
4. ✅ Every timestamp updates without refresh
5. ✅ All Firebase listeners receive updates in <2 seconds
6. ✅ No hardcoded values (all from Firebase)
7. ✅ Mobile responsive (no cutoffs or layout breaks)
8. ✅ Multi-tab sync works (updates propagate)
9. ✅ No console errors related to Firebase or data
10. ✅ All modals open/close properly

---

## 📝 TESTING LOG TEMPLATE

**Date**: 2025-10-12
**Tester**: Claude Code
**Environment**: Production (https://bitten-0420.web.app)

### Results:
| Page | Buttons | Timers | Real-Time | Status |
|------|---------|--------|-----------|--------|
| AlertFeed | ⏳ | ⏳ | ⏳ | Testing |
| MissionBrief | ⏳ | ⏳ | ⏳ | Testing |
| Battlefield | ⏳ | ⏳ | ⏳ | Testing |
| CommandCenter | ⏳ | ⏳ | ⏳ | Testing |
| WarChest | ⏳ | ⏳ | ⏳ | Testing |

**Legend**: ✅ Pass | ❌ Fail | ⏳ Testing | 🔄 In Progress

---

**Testing will verify complete system integration is working end-to-end.**
