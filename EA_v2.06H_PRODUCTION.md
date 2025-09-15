# BITTEN EA v2.06H - PRODUCTION VERSION
**Last Updated**: September 14, 2025
**Status**: ACTIVE IN PRODUCTION
**Identity**: COMMANDER_DEV_001

## 🎯 OVERVIEW
This is the current production Expert Advisor (EA) running on MT5. Version 2.06H includes enhanced position tracking, slot management, and hedge prevention capabilities.

## 📊 KEY FEATURES

### 1. Enhanced Position Tracking
- **SendDealerHeartbeatMetrics()** - Sends complete position array with every heartbeat
- **Position Data**: Includes ticket, fire_id, symbol, direction, open_price, current_price, volume, PNL
- **Heartbeat Interval**: Every 30 seconds via OnTimer()

### 2. Slot Management (10 Position Limit)
- **CountBittenPositions()** - Enforces maximum 10 positions
- **Hard Limit**: Rejects new trades when 10 positions are open
- **Real-time Tracking**: Updates position count with each heartbeat

### 3. Hedge Prevention
- **HasPositionOnSymbol()** - Blocks opposite direction trades on same symbol
- **Protection**: Prevents BUY if SELL exists on symbol (and vice versa)
- **Symbol-specific**: Each symbol can only have one direction active

### 4. Position Close Detection
- **OnTrade()** Handler - Detects when positions close
- **Automatic Updates**: Removes closed positions from tracking
- **Slot Release**: Frees up slots immediately when trades close

## 🔧 TECHNICAL DETAILS

### ZMQ Communication
- **Socket Type**: DEALER (connects to ROUTER on server)
- **Connection**: tcp://134.199.204.67:5555
- **Identity**: COMMANDER_DEV_001
- **Protocol**: JSON messages with enhanced position data

### Message Format (Enhanced Heartbeat)
```json
{
  "type": "HEARTBEAT",
  "target_uuid": "COMMANDER_DEV_001",
  "user_id": "7176191872",
  "account_login": "60062731",
  "broker": "OANDA-v20 Live-1",
  "balance": 850.45,
  "equity": 835.20,
  "leverage": 100,
  "currency": "USD",
  "ts": 1726351234,
  "open_positions": 4,
  "positions": [
    {
      "ticket": 21604324,
      "fire_id": "ELITE_SNIPER_GBPJPY_1757886793",
      "symbol": "GBPJPY",
      "direction": "BUY",
      "open_price": 200.249,
      "current_price": 200.21,
      "volume": 1.78,
      "pnl": -47.0
    }
  ]
}
```

### Fire Command Handling
```json
{
  "type": "fire",
  "target_uuid": "COMMANDER_DEV_001",
  "fire_id": "ELITE_RAPID_EURUSD_1756773488",
  "symbol": "EURUSD",
  "direction": "BUY",
  "entry": 0,
  "sl": 1.09800,
  "tp": 1.10300,
  "lot": 0.10
}
```

## 📋 VERSION HISTORY

### v2.06H (Current Production) - Sept 14, 2025
- Added enhanced position tracking with full position array
- Implemented 10-position hard limit
- Added hedge prevention (no opposite direction on same symbol)
- Added OnTrade() handler for position close detection
- Fixed OnTimer() implementation for reliable heartbeats

### v2.02 (Previous) - August 2025
- Basic heartbeat functionality
- Simple trade execution
- No position tracking

## 🚀 DEPLOYMENT

### Installation
1. EA is compiled and loaded on MT5 terminal
2. Attached to a single chart (any symbol)
3. Monitors all symbols via OnTimer()
4. Connects to server via ZMQ DEALER socket

### Server-Side Integration
- **Command Router** (port 5555): Routes fire commands to EA
- **Confirmation Listener** (port 5558): Receives trade confirmations
- **Position Processor**: Monitors heartbeats for slot tracking
- **Database**: Stores position data in ea_instances table

## 🔍 MONITORING

### Check EA Status
```bash
# View current positions
sqlite3 /root/HydraX-v2/bitten.db "SELECT open_positions, substr(position_data,1,100) FROM ea_instances WHERE target_uuid='COMMANDER_DEV_001';"

# Check heartbeat freshness
sqlite3 /root/HydraX-v2/bitten.db "SELECT target_uuid, (strftime('%s','now') - last_seen) as age_seconds FROM ea_instances WHERE target_uuid='COMMANDER_DEV_001';"

# Monitor position processor
pm2 logs position_processor --lines 10
```

### Key Files
- **EA Source**: Not stored on server (compiled in MT5)
- **Command Router**: `/root/HydraX-v2/command_router.py`
- **Position Processor**: `/root/HydraX-v2/position_processor.py`
- **Position Manager**: `/root/HydraX-v2/position_slot_manager.py`

## ⚠️ IMPORTANT NOTES

1. **DO NOT** modify EA without testing position tracking
2. **DO NOT** run multiple instances (causes slot confusion)
3. **DO NOT** disable OnTimer() (breaks heartbeat system)
4. **ALWAYS** verify slot tracking after EA updates
5. **ALWAYS** ensure OnTrade() handler is active

## 📊 CURRENT STATUS (Live)
- **Version**: 2.06H
- **Status**: ACTIVE
- **Identity**: COMMANDER_DEV_001
- **User**: 7176191872
- **Slots**: Tracking 5/10 positions (as of last update)
- **Heartbeat**: Every 30 seconds
- **Last Known Good**: September 14, 2025 22:08 UTC

---

**This document serves as the authoritative reference for the production EA.**