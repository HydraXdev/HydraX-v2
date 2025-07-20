# Production vs Documented Architecture Comparison

## Key Differences Found

### 1. Signal Generation
**Documented (CLAUDE.md)**:
- References `apex_v5_live_real.py` as the main signal generator
- Complex multi-version system

**Actual Production**:
- `apex_v5_lean.py` is running (PID 427512)
- Writes to `apex_v5_live_real.log` file
- Simplified, optimized version focused on pip-grabbing

### 2. TOC (Tactical Operations Center)
**Documented**:
- TOC is the "central brain" at `/src/toc/unified_toc_server.py`
- Handles terminal assignment, fire routing, trade callbacks
- Complex terminal management system

**Actual Production**:
- TOC server is NOT running
- No terminal assignment system active
- Direct execution path from bot to MT5

### 3. Trade Execution Flow
**Documented**:
```
MT5 Bridge → APEX → TOC → Terminal Assignment → Fire Router → MT5 Terminal
```

**Actual Production**:
```
MT5 Bridge → APEX Lean → Log File → Telegram Connector → Direct MT5 Execution
```

### 4. Telegram Integration
**Documented**:
- Single unified bot system
- TOC integration for trade execution

**Actual Production**:
- Dual bot system:
  - `bitten_production_bot.py`: Main trading bot
  - `apex_telegram_connector.py`: Signal relay bot
- No TOC integration

### 5. Web Application
**Documented**:
- Standard webapp server
- Complex integration with all systems

**Actual Production**:
- `webapp_server_optimized.py` with lazy loading
- Simplified integration, mainly for display

### 6. Database Architecture
**Documented**:
- Centralized database management
- Complex user/trade tracking

**Actual Production**:
- Multiple separate .db files
- Mission files stored as JSON in filesystem
- Limited database usage

## Why These Differences Exist

1. **Performance Optimization**: The lean versions reduce memory/CPU usage
2. **Simplified Architecture**: Removed complexity that wasn't needed
3. **Direct Execution**: Faster trade execution without TOC overhead
4. **Evolutionary Development**: System evolved but docs weren't updated

## Risks of Current Architecture

1. **No Terminal Management**: Can't handle multiple MT5 terminals
2. **Limited Scalability**: Direct execution path limits concurrent users
3. **No Risk Management Layer**: TOC provided risk controls
4. **Single Point of Failure**: No redundancy in execution path

## Recommendations

1. **Update Documentation**: Reflect actual architecture
2. **Evaluate TOC**: Decide if benefits worth the complexity
3. **Add Monitoring**: Current system lacks observability
4. **Implement Failover**: Add redundancy to critical paths
5. **Version Control**: Clean up old/unused code versions

## Production Stability

Despite differences, the production system appears stable:
- APEX Lean generating consistent signals
- Telegram bots functioning
- WebApp accessible
- MT5 bridge connected

The simplified architecture may actually be MORE stable due to fewer moving parts.