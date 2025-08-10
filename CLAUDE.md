# BITTEN PRODUCTION SYSTEM - ACTUAL STATE

**Last Verified**: August 8, 2025 18:31 UTC  
**Method**: Direct process inspection (ps aux)

## WHAT'S ACTUALLY RUNNING RIGHT NOW

```bash
# Signal Generation
PID 2581568: elite_guard_with_citadel.py
PID 2577665: elite_guard_zmq_relay.py  
PID 2411770: zmq_telemetry_bridge_debug.py

# User Interface
PID 2588730: bitten_production_bot.py (Telegram)
PID 2582822: webapp_server_optimized.py (Port 8888)
PID 2454259: commander_throne.py (Port 8899)

# Infrastructure
PID 2455681: simple_truth_tracker.py
PID 2409025: position_tracker.py
PID 2586467: handshake_processor.py
```

## CRITICAL FACTS

1. **NO LOCAL MT5** - All MT5 operations via ForexVPS API
2. **NO VENOM** - Elite Guard is the ONLY signal generator running
3. **FOREXVPS ONLY** - Zero local terminal management

## DON'T ADD CODE - CHECK WHAT'S RUNNING

Before writing ANY code:
1. Run `ps aux | grep {process_name}`
2. Check if it's already running
3. Don't create duplicates
4. Don't trust old documentation

## STOP CREATING FILES

The system has 280+ Python files. STOP ADDING MORE.
- Fix what exists
- Delete what's broken
- Don't create new versions

That's it. Everything else is outdated bloat.