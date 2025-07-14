# 🎯 BITTEN - Bot-Integrated Tactical Trading Engine/Network

**Last Updated**: July 14, 2025  
**Version**: 2.1 (Production Ready with Bridge Integration)  
**Status**: LIVE PRODUCTION - Bridge Integration Complete

## 📋 Executive Summary

BITTEN is a sophisticated forex trading system that combines automated signal generation, tiered user access, and gamification to create a comprehensive trading platform. The system integrates with MT5 terminals via file-based bridge communication, Telegram for user interface, and includes extensive safety features.

### Quick Facts:
- **Purpose**: Tactical trading assistant with automated signal generation via bridge integration
- **Signal Types**: RAPID ASSAULT (35-65% TCS), SNIPER OPS (65-95% TCS)
- **Tiers**: PRESS PASS (free trial), NIBBLER ($39), FANG ($89), COMMANDER ($139), APEX ($188)
- **Infrastructure**: Python backend, MT5 file bridge, Telegram bot, WebApp HUD
- **Safety**: Daily loss limits, emergency stops, risk management

---

## 🏗️ System Architecture (Updated July 14, 2025)

### Core Components:
1. **APEX v5.0 Signal Engine** - Analyzes bridge market data and generates trading signals
2. **File-Based Bridge System** - Two-way communication with MT5 terminals via text files
3. **MT5 Clone Farm** - Single master template cloned to user instances in <3 seconds
4. **Telegram Interface** - Primary user interaction point with BIT COMMANDER bot
5. **WebApp HUD** - Mission briefs and trade execution interface
6. **Mission Briefing System** - Personalized trade analysis per user account
7. **XP & Gamification** - User progression and rewards system

### Bridge Architecture (CRITICAL):
```
MT5 Terminals → Signal Files → Bridge Directory → APEX Engine
                                                      ↓
APEX Engine → Signal Analysis → Telegram Connector → BIT COMMANDER Bot
                                                      ↓
User Clicks → Mission Briefing → WebApp HUD → Trade Execution → Bridge Files → MT5
```

### Bridge File Structure:
- **Input**: `C:\MT5_Farm\Bridge\Incoming\signal_SYMBOL_*.json`
- **Output**: `C:\MT5_Farm\Bridge\Outgoing\trade_*.json`
- **Status**: `C:\MT5_Farm\Bridge\Executed\result_*.json`

### Technology Stack:
- **Backend**: Python 3.10+
- **Trading**: MetaTrader 5 (MT5) via file bridge
- **Database**: SQLite (multiple specialized databases)
- **Frontend**: React WebApp
- **Messaging**: Telegram Bot API (BIT COMMANDER: 7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w)
- **Payments**: Stripe
- **Deployment**: AWS/Linux VPS + Windows MT5 Server

---

## 🔧 Critical APEX Engine Integration (Fixed July 14, 2025)

### Problem Solved:
The outsourced APEX v5.0 engine was trying to connect directly to MT5 (impossible on Linux). 
**Solution**: Connected APEX to existing bridge infrastructure.

### Fixed Implementation:
- **Before**: APEX → Direct MT5 Connection (FAILED)
- **After**: APEX → Bridge Files → Real Market Data ✅

### Key Files:
- `/root/HydraX-v2/apex_v5_live_real.py` - Fixed engine reading bridge files
- `/root/HydraX-v2/apex_telegram_connector.py` - Signal → Telegram integration
- `C:\MT5_Farm\Bridge\Incoming\` - Real market data source

---

## 🚀 Production Signal Flow

### Complete Working Flow:
1. **MT5 Terminals** → Generate market signals → Bridge files
2. **APEX Engine** → Reads bridge files → Analyzes market data → Generates TCS scores
3. **Telegram Connector** → Monitors APEX logs → Sends alerts to BIT COMMANDER bot
4. **User** → Clicks "🎯 VIEW INTEL" → Opens personalized mission briefing
5. **Mission Briefing** → Pulls user's MT5 account data → Calculates position sizing
6. **User** → Executes trade → Fire Router → JSON to bridge → MT5 execution

### Signal Format (APEX → Telegram):
```
🎯 SIGNAL #X: SYMBOL DIRECTION TCS:XX%
```

### Bridge File Format (Market Data):
```json
{
  "signal_num": 346,
  "symbol": "EURUSD", 
  "direction": "BUY",
  "tcs": 62,
  "timestamp": "2025-07-13T23:02:49.409688",
  "source": "APEX_v5.0",
  "entry_price": 1.47874,
  "spread": 2
}
```

---

## 💰 Tier System & Pricing

### 🆓 PRESS PASS (7-day Trial)
- **Price**: FREE
- **Signup**: Email-only (instant access)
- **Features**: View & execute RAPID ASSAULT signals (6 per day)
- **MT5**: Instant demo clone with $50k balance
- **Limitations**: XP resets nightly, demo account only
- **Purpose**: Let users experience the system
- **Upgrade Flow**: Pay → credentials injected → live trading instantly

### 🔰 NIBBLER ($39/month)
- **Signal Access**: View both RAPID ASSAULT & SNIPER OPS
- **Execution**: RAPID ASSAULT only (manual)
- **Fire Mode**: MANUAL only
- **Target**: Entry-level traders

### 🦷 FANG ($89/month)
- **Signal Access**: All signals (including future special events)
- **Execution**: All signals (manual)
- **Fire Mode**: MANUAL only
- **Target**: Active manual traders

### ⭐ COMMANDER ($139/month)
- **Signal Access**: All signals
- **Execution**: All signals
- **Fire Mode**: MANUAL + SEMI-AUTO + FULL AUTO
- **Special**: Autonomous slot-based execution
- **Target**: Serious traders wanting automation

### 🏔️ APEX ($188/month)
- **Signal Access**: All signals
- **Execution**: All signals
- **Fire Mode**: Same as COMMANDER
- **Special**: Future exclusive features
- **Target**: Premium users

---

## 🔫 Fire Modes Explained

### MANUAL Mode
- Click each trade to execute
- Full control over every decision
- Available to all paid tiers

### SEMI-AUTO Mode (COMMANDER/APEX)
- Assisted execution
- Manual selection with automated helpers
- Quick switching between manual/auto

### FULL AUTO Mode (COMMANDER/APEX)
- Autonomous slot-based execution
- Trades automatically fill open slots
- Set number of concurrent positions
- System handles execution when slots open

---

## 🚦 Signal System (APEX v5.0 with Bridge Integration)

### Signal Types:
1. **🔫 RAPID ASSAULT**
   - TCS Range: 35-65% (v5.0 aggressive)
   - Characteristics: High frequency, 20+ signals/day
   - Access: All tiers can view and execute (PRESS_PASS: 6/day, NIBBLER+: 6+/day)

2. **⚡ SNIPER OPS**
   - TCS Range: 65-95% (v5.0 precision)
   - Characteristics: Premium signals, higher profit targets
   - Access: All tiers can view, FANG+ can execute

3. **🔨 MIDNIGHT HAMMER** (Future)
   - Special event signals
   - APEX exclusive feature
   - Planned for major market events

### TCS (Trade Confidence Score) - APEX v5.0
- Algorithm-based confidence rating (0-100%)
- APEX v5.0 Range: 35-95% (Ultra-Aggressive Mode)
- **Data Source**: Bridge files from MT5 terminals (REAL market data)
- 15 Trading Pairs including volatility monsters
- Target: 40+ signals/day @ 89% win rate

---

## 🛡️ Safety Systems

### Risk Management:
- **Daily Loss Limits**: 7-10% maximum
- **Position Sizing**: Tier-based lot sizes
- **Emergency Stop**: Panic button for all positions
- **Tilt Detection**: Monitors emotional trading patterns
- **News Lockouts**: Prevents trading during high-impact events

### Security Features:
- Environment-based credentials (no hardcoding)
- Encrypted communications
- Rate limiting on APIs
- Audit trails for all trades
- File-based bridge isolation

---

## 🎮 XP & Gamification

### XP System:
- Earn XP for successful trades
- Achievement unlocks
- Seasonal Battle Pass
- Leaderboards

### Press Pass Special Rules (Psychological Design):
- **No Identity**: Anonymous user ID, no callsign or gamer tag
- **XP Resets Nightly**: All progress wiped at midnight UTC (maximum FOMO)
- **Referral Only**: Single social feature - can invite buddies to war room
- **Identity Envy**: See paid users with callsigns, ranks, permanent XP
- **Daily FOMO Cycle**: Build progress → warnings → midnight wipe → repeat
- **Conversion Triggers**: Identity desire, progress anxiety, social pressure

---

## 🔧 Current System Status (July 14, 2025)

### ✅ Operational:
- ✅ APEX v5.0 signal generation engine (bridge integrated)
- ✅ File-based MT5 bridge communication
- ✅ MT5 clone farm with BITTEN_MASTER template
- ✅ Telegram bot interface (BIT COMMANDER)
- ✅ WebApp at https://joinbitten.com
- ✅ Mission briefing system with individual account data
- ✅ XP and achievement systems
- ✅ Tier access control
- ✅ Risk management systems
- ✅ Stripe payment processing (live webhooks)
- ✅ SHEPHERD guardian system
- ✅ AI personality integration
- ✅ Bridge file monitoring and processing
- ✅ Signal flow: Bridge → APEX → Telegram → Users

### 🟡 Optional Enhancements:
- Voice synthesis (ElevenLabs API)
- Enhanced market data feeds
- Additional AI features

### 📝 Future Features:
- Chaingun Mode (rapid fire execution)
- Midnight Hammer (special events)
- Advanced APEX exclusives

---

## 🚀 Quick Start for Developers

### Key Directories:
```
/root/HydraX-v2/
├── src/bitten_core/     # Core trading logic
├── config/              # Configuration files
├── bitten/             # Additional modules
├── apex_v5_live_real.py # FIXED: Bridge-integrated signal engine
├── apex_telegram_connector.py # Signal → Telegram bridge
├── webapp_server.py    # WebApp backend
└── docs/               # Documentation
```

### Important Files:
- `apex_v5_live_real.py` - **FIXED ENGINE** reading bridge files
- `apex_telegram_connector.py` - Signal monitoring and Telegram integration
- `config/payment.py` - Tier pricing configuration
- `config/tier_mapping.py` - Tier name standardization
- `config/fire_mode_config.py` - Fire mode rules
- `src/bitten_core/mission_briefing_generator_v5.py` - Personalized mission briefings

### Bridge Integration Files:
- `C:\MT5_Farm\Bridge\Incoming\` - Market data from MT5 terminals
- `C:\MT5_Farm\Bridge\Outgoing\` - Trade commands to MT5
- `C:\MT5_Farm\Bridge\Executed\` - Trade results from MT5

### Running Services:
```bash
# Start APEX engine (reads bridge files)
python3 apex_v5_live_real.py &

# Start Telegram connector
python3 apex_telegram_connector.py &

# Check WebApp
systemctl status bitten-webapp
```

---

## 📞 Support & Documentation

### For Next AI Assistant:
1. **Bridge Integration is CRITICAL** - APEX reads market data from bridge files, not direct MT5
2. **Signal Flow**: Bridge Files → APEX → Telegram → Mission Briefings → Users
3. **No Direct MT5 Connection** - All MT5 communication via file bridge
4. Check `CURRENT_STATUS_SUMMARY.md` for latest status
5. Use SHEPHERD system to navigate codebase (`python3 bitten/interfaces/shepherd_cli.py`)
6. All credentials in environment variables
7. **BIT COMMANDER Bot Token**: 7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w

### Key Documentation:
- `/docs/bitten/RULES_OF_ENGAGEMENT.md` - Trading rules
- `/SHEPHERD_FULL_AUDIT_REPORT.md` - Code analysis
- `/TIER_FIRE_MODE_CLARIFICATION.md` - Access rules
- `APEX_TELEGRAM_INTEGRATION.md` - Signal flow documentation

### Bridge Architecture Documentation:
- `BULLETPROOF_INFRASTRUCTURE_SUMMARY.md` - Infrastructure details
- Bridge files at `C:\MT5_Farm\Bridge\` on Windows server 3.145.84.187

---

## ⚠️ Critical Architecture Notes

### APEX Engine Integration (FIXED July 14, 2025):
1. **NEVER** try direct MT5 connection from Linux
2. **ALWAYS** read market data from bridge files
3. **Bridge Path**: `C:\MT5_Farm\Bridge\Incoming\signal_SYMBOL_*.json`
4. **Signal Output**: Format must be `🎯 SIGNAL #X: SYMBOL DIRECTION TCS:XX%`
5. **No Fake Data**: System fails safely if no bridge data available

### System Dependencies:
1. **Windows MT5 Server**: 3.145.84.187 with bulletproof agents
2. **Bridge Files**: Real market data source
3. **BIT COMMANDER Bot**: Telegram signal delivery
4. **Mission Briefing System**: Individual account data integration

---

## 🏆 Production Readiness Checklist

- ✅ **APEX Engine**: Fixed and reading bridge files
- ✅ **Telegram Integration**: BIT COMMANDER bot operational
- ✅ **Bridge Communication**: File-based system working
- ✅ **Mission Briefings**: Personalized user data integration
- ✅ **WebApp**: Live at https://joinbitten.com
- ✅ **Payment System**: Stripe integration active
- ✅ **Tier System**: All access levels configured
- ✅ **Risk Management**: Safety systems active
- ✅ **MT5 Clone Farm**: Ready for user deployment

---

*BITTEN v2.1 - Tactical Trading Excellence with Bridge Integration*  
*Documentation updated July 14, 2025 - Production Ready*