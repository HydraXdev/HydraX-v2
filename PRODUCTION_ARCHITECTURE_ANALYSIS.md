# HydraX-v2 Production Architecture Analysis

## Executive Summary

Based on the running processes and code analysis, here's what's actually running in production versus what's duplicate/test code:

## Active Production Components

### 1. Signal Generation System
- **ACTIVE**: `apex_v5_lean.py` (PID 427512)
- **NOT RUNNING**: `apex_v5_live_real.py` (referenced in configs but not running)
- **Purpose**: Generates trading signals from MT5 bridge data
- **Config**: Uses `apex_config.json` for signal generation parameters
- **Output**: Logs signals to `apex_v5_live_real.log` (monitored by telegram connector)

### 2. Telegram Integration
- **PRIMARY BOT**: `bitten_production_bot.py` (PID 424394)
  - Token: `7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w`
  - Commander ID: 7176191872
  - Handles actual trading commands and mission execution
  
- **SIGNAL RELAY**: `apex_telegram_connector.py` (PID 424397)
  - Monitors APEX log file for signals
  - Generates mission files in `/root/HydraX-v2/missions/`
  - Sends alerts to Telegram with WebApp links

### 3. Web Application
- **ACTIVE**: `webapp_server_optimized.py` (PID 424399)
  - Optimized Flask server with lazy loading
  - Serves the trading interface at `https://joinbitten.com/hud`
  - Integrates with signal storage and engagement database
  
- **NOT RUNNING**: Standard webapp servers (replaced by optimized version)

### 4. TOC (Tactical Operations Center)
- **DEFINED**: `/root/HydraX-v2/src/toc/unified_toc_server.py`
- **STATUS**: NOT RUNNING (not in process list)
- **Purpose**: Central brain for terminal assignment and fire routing
- **Note**: System is running WITHOUT the TOC, likely using direct bot integration

### 5. MT5 Bridge
- **RUNNING**: SSH tunnel to `3.145.84.187` (AWS instance)
- **Port**: 5555
- **Purpose**: Retrieves real-time market data from MT5 terminals

## Production Flow (Actual)

```
1. MT5 Bridge (3.145.84.187:5555)
   ↓
2. APEX v5 Lean (apex_v5_lean.py)
   ↓ (writes to apex_v5_live_real.log)
3. APEX Telegram Connector (apex_telegram_connector.py)
   ↓ (generates mission files + sends Telegram alerts)
4. Telegram Bot (bitten_production_bot.py)
   ↓ (handles /fire commands)
5. WebApp (webapp_server_optimized.py)
   ↓ (displays missions)
6. Direct MT5 Execution (bypassing TOC)
```

## Key Findings

### 1. TOC Not Running
The Tactical Operations Center (unified_toc_server.py) is NOT running in production. The system appears to be using a simplified flow where the Telegram bot directly handles trade execution.

### 2. Signal Generation Mismatch
- Config references `apex_v5_live_real.py` but actually runs `apex_v5_lean.py`
- Both write to the same log file (`apex_v5_live_real.log`)
- This suggests `apex_v5_lean.py` is the production-ready, optimized version

### 3. Dual Bot System
- `bitten_production_bot.py`: Main trading bot
- `apex_telegram_connector.py`: Signal notification bot
- Both work together but serve different purposes

### 4. Simplified Architecture
The actual production system is simpler than documented:
- No TOC server running
- No terminal assignment system active
- Direct bot-to-MT5 execution path

## Duplicate/Test Components

1. **Multiple webapp versions**: Only `webapp_server_optimized.py` is used
2. **Various bot versions**: Only `bitten_production_bot.py` is active
3. **TOC system**: Defined but not deployed
4. **Terminal assignment**: Code exists but not utilized
5. **Fire router**: Part of TOC, not in use

## Recommendations

1. **Clean up unused code**: Remove or clearly mark test/deprecated components
2. **Update documentation**: CLAUDE.md doesn't match actual architecture
3. **Consider TOC deployment**: The TOC system could add valuable features
4. **Consolidate signal generators**: Choose between lean and full versions
5. **Service management**: Implement proper systemd services for all components

## Security Concerns

1. **Hardcoded credentials**: Bot tokens in code
2. **Direct execution path**: No TOC validation layer
3. **Single commander**: Only one authorized user (7176191872)

## Next Steps

1. Decide if TOC should be deployed or removed
2. Clean up duplicate signal generation code
3. Update documentation to reflect actual architecture
4. Implement proper service management
5. Add monitoring and health checks