# BITTEN PRESS PASS Onboarding Funnel - Full Specification

## 🧭 Overview
BITTEN's "Press Pass" onboarding system provides a frictionless, psychologically optimized entry point into the BITTEN trading platform. It allows users to experience real-time demo trading, accumulate temporary XP, and observe live trades — all without requiring upfront payment or account funding. The system is engineered to maximize user engagement, gather valuable signal data, and drive enlistment conversions.

---

## 🎫 PRESS PASS: Access Mode (Tier 0)

**What it is:**
- A 7-day limited-access trading preview
- Uses a real MT5 demo account (MetaQuotes-Demo)
- Trades are live and real, but XP resets nightly at 00:00 UTC
- XP and gamertag are locked behind ENLISTMENT

**User Flow:**
1. User lands on **joinBITTEN.com**
2. Sees offer: _"Grab Your 7-Day Press Pass – Watch the War Unfold"_
3. Enters **name + email** (stored in DB)
4. Presented with 3 options:
   - 🎫 **Try Now (Press Pass)** – auto-demo, no setup
   - 🧪 **Enlist with Demo Broker** – FOREX.com demo (requires card)
   - ⚔️ **Go Live** – funded live account (FOREX.com or other)
5. If they choose Press Pass:
   - MetaQuotes demo spun up
   - Assigned default user ID (name only)
   - No gamertag, no leaderboard
   - XP tracking **enabled**, but **XP resets every midnight**

---

## 💾 Logging & Data Capture
All PRESS PASS trades are captured and logged into full analytics:

**Tables:**
1. `trade_logs_all`
   - user_id
   - tier ("press_pass")
   - symbol, entry_time, exit_time
   - direction, lot size, result (pips, %)
2. `press_pass_shadow_stats`
   - XP_earned_today
   - win_rate
   - trades_executed
   - XP_burned_last_night
3. `conversion_signal_tracker`
   - press_pass_start_date
   - enlisted_after?
   - time_to_enlist (days)
   - XP_lost_prior_to_enlist

---

## ⚖️ XP System (PRESS PASS Mode)
- ✅ XP is earned like normal
- ❌ XP is not persistent
- At 11:59 PM:
   - Alert sent: _"Your XP expires in 1 minute unless you enlist…"
- At 00:00:
   - XP resets to 0
   - Stats remain in shadow log for future conversion messaging

---

## 🔁 If They Enlist (Demo or Live)
- All future XP becomes persistent
- They choose a gamertag
- Past PRESS PASS stats are optionally restored (as shadow XP bonus)
- Trades continue from same logic path with full feature access

---

## 📈 Marketing & Retargeting
**Email Cadence:**
- Day 1: "Welcome to the Warzone"
- Day 2–6: Daily updates on performance, XP lost, leaderboard teasers
- Day 7: Urgency push — final hours alert
- Post Day 7: Weekly emails — "REDEPLOY" campaign (_"You lost 1,034 XP. Ready to reclaim it?"_)

**Telegram / WebApp Alerts:**
- Live modal alerts: _"XP will reset in 2 hours"_
- RecruiterBot DMs: _"Observers don't earn medals. Enlist before midnight."_
- After reset: _"XP wiped. Data stored. Still watching, or ready to rank up?"_

---

## 🛠️ Technical Considerations
- MT5 terminals spun up on isolated bridge instances
- PRESS PASS users are sandboxed from Tier 1+ live users
- Trade execution behaves the same as any other account
- Database flags:
   - `tier = press_pass`
   - `xp_mode = ghost`

---

## 📊 Use Trade Count as Social Proof
- Landing page counter:
   > _"🎫 11,237 Press Passes granted since launch. Join the next wave."_

- Optional soft daily cap: _"Only 500 PRESS PASSES issued daily. 438 claimed so far today."_ (FOMO without hard block)

- Optional viral stat use:
   > _“In the past 48 hours:  
   - 2,142 trades executed  
   - 1,209 XP wiped  
   - 462 new enlistees  
   - 38 funded soldiers entered LIVE OPS”_

---

## ✅ Summary
The PRESS PASS system turns passive visitors into emotionally engaged prospects. It provides:
- Fast dopamine hits (real trades)
- A daily loss loop (XP decay)
- A strong identity hook (ENLISTING)
- Rich behavioral data (for both conversion + strategy refinement)

This funnel will outperform a generic 14-day trial by creating psychological friction, identity shaping, and long-term revenue alignment.

**XP is a mirror.  
Money is the path.  
BITTEN is the war.**
