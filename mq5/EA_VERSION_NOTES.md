# EA Version Notes

## BITTENBridge_TradeExecutor_ZMQ_v7_PRODUCTION_CLEAN.mq5

**Date**: August 1, 2025  
**Status**: PRODUCTION READY - CLEAN VERSION

### Features:
- ✅ ZMQ Client connecting to 134.199.204.67:5555 (commands) and :5556 (heartbeat)
- ✅ Tick streaming on every tick via port 5556
- ✅ OHLC candle streaming every 5 seconds (M1, M5, M15 timeframes)
- ✅ Extended watchdog timer (120 seconds)
- ✅ Debug logging for received ZMQ messages
- ✅ Empty msg_type detection
- ✅ Heartbeat message handling (no warnings)
- ❌ Dummy test loop REMOVED
- ✅ Trade execution via ZMQ commands
- ✅ Position management and reporting

### Candle Data Format:
```json
{
  "type": "candle_batch",
  "symbol": "EURUSD",
  "timestamp": 1754083399,
  "M1": [{"time":1754083340,"open":1.15283,"high":1.15301,"low":1.15275,"close":1.1529,"volume":125},...],
  "M5": [{"time":1754083100,"open":1.15216,"high":1.15221,"low":1.15161,"close":1.15197,"volume":562},...],
  "M15": [{"time":1754082400,"open":1.15538,"high":1.15588,"low":1.15478,"close":1.15572,"volume":1827},...]
}
```

### Usage:
This is the clean production version with all debug features properly configured and no test loops. Use this as the base for any future modifications.