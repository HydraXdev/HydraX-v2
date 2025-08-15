# 🔒 VERSION 6.4 - EA DATA FLOW CONTRACT LOCKED

**Date**: August 1, 2025
**Git Commit**: 032a9ea
**Git Tag**: v6.4-ea-data-flow-locked
**Status**: LOCKED AND PUSHED TO GITHUB

## Version Summary

This version establishes the **canonical EA → Core architecture** that MUST NOT be modified without consulting the binding contracts.

### Architecture Locked:
```
EA v7.01 (PUSH) → 134.199.204.67:5556 → Telemetry Bridge → 5560 → Elite Guard → WebApp → GROUP
```

### Key Components:
1. **EA v7.01**: ZMQ client sending tick data (NEVER binds)
2. **Telemetry Bridge**: MANDATORY for data flow (zmq_telemetry_bridge_debug.py)
3. **Elite Guard v6.0**: Pattern detection with CITADEL Shield
4. **Signal Delivery**: GROUP ONLY to @bitten_signals (no DMs)

### Documentation Suite:
- `EA_DATA_FLOW_CONTRACT.md` - Binding agreement
- `EA_QUICK_REFERENCE.md` - Troubleshooting commands
- `EA_DATA_FLOW_DIAGRAM.txt` - Visual architecture
- `start_elite_guard_system.sh` - Canonical startup script

### Current Configuration:
- Elite Guard threshold: 50% (temporary for 5-hour benchmarking)
- Truth system: Active and tracking all signals
- All components: Tested and operational

## GitHub Repository

**Repository**: https://github.com/HydraXdev/HydraX-v2
**Commit**: https://github.com/HydraXdev/HydraX-v2/commit/032a9ea
**Tag**: v6.4-ea-data-flow-locked

## Lock Declaration

This architecture is now **CANONICAL**. Any future agent or module attempting to modify:
- Port assignments (5556, 5560, 5557, 8888)
- Data flow direction
- Component dependencies
- Fire routes

MUST first consult `EA_DATA_FLOW_CONTRACT.md` and receive explicit authorization.

**Locked by**: Claude Code Agent
**Authority**: User directive for version lock
**Date**: August 1, 2025