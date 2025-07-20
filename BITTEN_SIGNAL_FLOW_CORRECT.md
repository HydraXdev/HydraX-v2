# 🎯 BITTEN Correct Signal Flow

**Last Updated**: July 15, 2025  
**Status**: User-Driven Execution Model

## 📋 The Actual Flow (NOT Automated!)

### 1️⃣ **Signal Generation**
```
MT5 EA → Bridge Files → APEX Engine → TCS Scoring
```
- APEX reads market data from bridge files
- Calculates TCS score (now minimum 65%)
- Logs signals: `🎯 SIGNAL #X: SYMBOL DIRECTION TCS:XX%`

### 2️⃣ **User Notification** (Alert Only!)
```
APEX Log → Telegram Connector → Bot Message
```
- Telegram connector monitors APEX logs
- Sends **ALERT ONLY** to users
- **NO AUTOMATIC EXECUTION**

Example Telegram Alert:
```
🟢 MODERATE APEX SIGNAL

📊 EURAUD BUY
🎯 TCS: 66%
⏰ Time: 09:15:00

[🎯 VIEW INTEL]
```

### 3️⃣ **User Decision**
- User sees alert in Telegram
- User clicks "VIEW INTEL" button
- Opens personalized mission briefing in WebApp

### 4️⃣ **Mission Briefing**
```
User → /mission/<signal_id> → Personalized Intel
```
- Shows user's MT5 account data
- Calculates position sizing
- Shows entry/SL/TP levels
- **User decides whether to execute**

### 5️⃣ **Manual Execution** (User Initiated!)
```
User Clicks FIRE → /api/fire → MT5 Bridge → Trade
```
- Only executes if user clicks FIRE button
- Validates user tier permissions
- Sends to MT5 bridge for execution

## ❌ What We Are NOT Doing

1. **NOT** automatically executing trades when signals appear
2. **NOT** bypassing user decision making
3. **NOT** sending trades directly from APEX to MT5
4. **NOT** auto-trading without user consent

## ✅ What We ARE Doing

1. **Alerting** users to opportunities
2. **Providing** detailed mission briefings
3. **Enabling** user-initiated execution
4. **Respecting** tier-based permissions

## 🔧 Components

### Required Running Services:
1. **APEX Engine** - Generates and scores signals
2. **Telegram Connector** - Sends alerts to users
3. **WebApp** - Serves mission briefings and fire endpoint
4. **Fire Execution Handler** - Executes user-initiated trades

### Key Files:
- `apex_v5_live_real.py` - Signal generation
- `apex_telegram_connector.py` - User alerts (ALREADY WORKING!)
- `src/bitten_core/web_app.py` - Mission briefings and fire endpoint
- `fire_execution_handler.py` - MT5 bridge execution

## 🚫 Security & Permissions

### Tier Restrictions:
- **PRESS_PASS**: RAPID ASSAULT only (demo)
- **NIBBLER**: RAPID ASSAULT only (manual)
- **FANG**: All signals (manual)
- **COMMANDER**: All signals + auto modes
- **APEX**: All features

### Fire Validation:
- User can only fire once per signal
- Must have appropriate tier for signal type
- Must have sufficient balance

## 📊 Data Flow

```
Market Data → APEX → Signal
                ↓
         Telegram Alert
                ↓
         User Sees Alert
                ↓
         Clicks VIEW INTEL
                ↓
         Mission Briefing
                ↓
         User Decides
                ↓
      (IF YES) Click FIRE
                ↓
          MT5 Execution
```

## 🎮 User Experience

1. User subscribes to @HydraXCommanderBot
2. Receives signal alerts throughout the day
3. Each alert has "VIEW INTEL" button
4. Clicking opens personalized mission briefing
5. User analyzes and decides to trade or pass
6. If trading, clicks FIRE button
7. Trade executes through MT5 bridge
8. User receives confirmation

This is a **decision support system**, not an auto-trader!