# EA PRODUCTION - OFFICIAL BITTEN EA

## 🎯 **THE LAW - AS OF OCTOBER 2, 2025**

**PRODUCTION EA**: `EA_BITTEN_v3.005_PRODUCTION.mq5`

This is the ONLY authorized production EA. All other versions are OBSOLETE and archived.

## **Features (v3.005)**

- ✅ Position Reconciliation (handshake with reconnect flag + open_positions array)
- ✅ Heartbeat system (every 1 second to port 5556)
- ✅ DEALER keepalive (every 5 seconds to port 5555)
- ✅ SafeNum protection (prevents NaN/Inf crashes)
- ✅ Deduplication (position update spam prevention)
- ✅ Multi-symbol monitoring (up to 200 symbols)
- ✅ Trade confirmations (port 5558)
- ✅ Position lifecycle events (opened/closed/tp/sl)

## **Server Integration**

This EA works with:
- `/root/HydraX-v2/zmq_telemetry_bridge_debug.py` (heartbeat storage)
- `/root/HydraX-v2/command_router.py` (position reconciliation)
- All server-side handlers are PRODUCTION READY

## **Compilation**

Compile in MT5 MetaEditor:
- 0 errors
- 0 warnings
- Production grade code

## **DO NOT USE ANYTHING FROM EA_ARCHIVE_OBSOLETE**

All archived versions are outdated and lack critical features like position reconciliation.
