# 🎯 Complete BITTEN Flow Documentation

## 🚀 System Overview
BITTEN is a military-themed forex trading system that guides users from onboarding through trade execution with gamification elements.

---

## 📊 Complete User Journey

### 1️⃣ **User Discovery & Onboarding**

#### A. User Finds BITTEN
- Discovers bot through Telegram search or invite link
- Joins main Telegram group: `-1002581996861`

#### B. First Contact
```
User: /start

Bot: 🎖️ **WELCOME TO B.I.T.T.E.N.**
     Bot-Integrated Tactical Trading Engine

     [📋 BEGIN BRIEFING]
```

#### C. Onboarding Flow
1. **Tier Selection**
   - Nibbler ($39) - Basic scalping
   - Fang ($89) - Advanced filters
   - Commander ($139) - Auto trading
   - APEX ($188) - Full automation

2. **MT5 Setup**
   - Guided MT5 installation
   - Account connection walkthrough
   - WebHook configuration

3. **Risk Profile Setup**
   - Daily loss limits (-7% max)
   - Position sizing rules
   - Emergency stop configuration

---

### 2️⃣ **Signal Detection & Distribution**

#### A. Signal Generation Flow
```
Market Data → Detection Modules → TCS Scoring → Fire Mode Router → Signal Alert
```

#### B. Signal Types
1. **Arcade Scalps** (All tiers)
   - Quick 5-30 pip trades
   - 70%+ TCS required
   - 30-min cooldown for Nibblers

2. **Sniper Shots** (Fang+)
   - High-confidence setups
   - 85%+ TCS required
   - Larger pip targets

3. **Special Events**
   - Midnight Hammer (5% risk)
   - Chaingun sequences
   - Unity bonuses

#### C. Signal Alert Format
```
⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes
[🎯 VIEW INTEL]
```

---

### 3️⃣ **WebApp Intelligence System**

#### A. User Clicks "VIEW INTEL"
- Opens https://joinbitten.com/hud
- Passes signal data via URL parameters
- Authenticates user tier

#### B. Tier-Based Intelligence Display

**Nibbler View:**
- Basic entry/exit points
- Simple risk calculation
- Countdown timer

**Fang View:**
- + Technical indicators
- + Market context
- + Historical performance

**Commander View:**
- + Advanced analytics
- + Multi-timeframe analysis
- + Auto-trade options

**APEX View:**
- + Full market depth
- + Algorithmic insights
- + Custom parameters

---

### 4️⃣ **Trade Execution**

#### A. Manual Execution (Nibbler/Fang)
1. User reviews intel in WebApp
2. Clicks "EXECUTE" button
3. Trade parameters sent to MT5
4. Confirmation returned to Telegram

#### B. Semi-Auto (Commander)
1. Pre-approved parameters
2. One-click execution
3. Automatic position management

#### C. Full Auto (APEX)
1. Signals auto-execute
2. Dynamic position sizing
3. Advanced risk management

---

### 5️⃣ **Post-Trade Flow**

#### A. Trade Confirmation
```
✅ **TRADE EXECUTED**
EUR/USD | BUY @ 1.0850
Position: 0.10 lots
Stop Loss: 1.0830
Take Profit: 1.0880
```

#### B. Position Monitoring
- Real-time P/L updates
- Trailing stop activation
- News event protection

#### C. Trade Closure
```
🎯 **TARGET HIT**
EUR/USD | +30 pips
Duration: 45 minutes
XP Earned: +150
```

---

### 6️⃣ **Gamification & Progress**

#### A. XP System
- Base XP per trade
- Multipliers for streaks
- Bonus for accuracy

#### B. Rank Progression
- Recruit → Soldier → Warrior → Elite → Legend
- Unlock perks and features
- Visual badge upgrades

#### C. Daily Missions
- Trade X times
- Achieve X% accuracy
- Capture X pips

---

## 🔧 Technical Implementation

### Component Architecture
```
Telegram Bot (7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ)
     ↓
BITTEN Core (signal_alerts.py, telegram_router.py)
     ↓
WebApp Server (https://joinbitten.com/hud)
     ↓
MT5 Bridge (trade execution)
     ↓
Database (user data, trades, XP)
```

### Key Files by Function

| Function | Primary File | Description |
|----------|-------------|-------------|
| Bot Commands | `telegram_router.py` | Handles /start, /stats, etc |
| Signal Alerts | `signal_alerts.py` | Creates brief alerts with WebApp buttons |
| WebApp Server | `webapp_server.py` | Serves mission briefing interface |
| Signal Detection | `fire_router.py` | Routes signals to appropriate handlers |
| Trade Execution | `mt5_bridge.py` | Executes trades on MT5 |
| User Management | `user_manager.py` | Tier access, XP, progression |
| Risk Management | `risk_manager.py` | Position sizing, daily limits |

---

## 🚨 Safety Systems

### Protective Mechanisms
1. **Daily Loss Limit**: -7% automatic cutoff
2. **Tilt Detection**: Forced break after 3 losses
3. **News Lockout**: No trades during high-impact events
4. **Position Limits**: Max exposure caps
5. **Emergency Stop**: Instant close all positions

### Cooldown System
- Nibbler: 30 min between trades
- Fang: 15 min cooldown
- Commander: 5 min cooldown
- APEX: No cooldown

---

## 📱 User Commands

### Essential Commands
- `/start` - Begin onboarding
- `/help` - Command list
- `/stats` - View performance
- `/positions` - Active trades
- `/upgrade` - Change tier
- `/stop` - Emergency stop

### Advanced Commands
- `/firetest` - Test signal
- `/missions` - Daily objectives
- `/squad` - Team features
- `/journal` - Trade diary

---

## 🔗 WebApp URLs

### Production
- Main HUD: `https://joinbitten.com/hud`
- Mission Brief: `https://joinbitten.com/mission`
- Stats Dashboard: `https://joinbitten.com/stats`
- Settings: `https://joinbitten.com/settings`

### Development
- Local: `http://localhost:5000/hud`
- Staging: `https://staging.joinbitten.com/hud`

---

## 🎮 Example User Session

```
1. User: /start
2. Bot: Shows tier options
3. User: Selects Fang tier
4. Bot: Payment processing
5. User: Completes MT5 setup
6. Bot: "⚡ SIGNAL DETECTED..."
7. User: Clicks [VIEW INTEL]
8. WebApp: Shows full analysis
9. User: Clicks [EXECUTE]
10. Bot: "✅ TRADE EXECUTED"
11. Time passes...
12. Bot: "🎯 TARGET HIT +30 pips"
13. Bot: "+150 XP earned!"
```

---

## ⚡ Quick Test Flow

```python
# 1. Send test signal
python send_test_signal.py

# 2. User clicks WebApp button
# 3. Views intel at https://joinbitten.com/hud
# 4. Executes trade
# 5. Receives confirmation
```

---

## 📞 Support & Troubleshooting

### Common Issues
1. **WebApp won't open**: Check HTTPS certificate
2. **Signal not received**: Verify bot permissions
3. **Trade failed**: Check MT5 connection
4. **Wrong tier access**: Verify subscription status

### Debug Commands
- `/debug` - System status
- `/modules` - Component health
- `/reconnect` - Reset connections