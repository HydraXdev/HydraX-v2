# TELEGRAM BOTS PRODUCTION HARDENING REFERENCE

**Completed**: August 10, 2025  
**Agent**: Claude Code  
**Status**: ✅ PRODUCTION READY

## OVERVIEW

Successfully applied enterprise-grade hardening to 3 Telegram bots:
- `bitten_production_bot.py` - Main trading bot
- `bitten_voice_personality_bot.py` - Voice/personality system
- `athena_mission_bot.py` - Mission dispatch bot

All bots now run under PM2 process management with comprehensive error handling, monitoring, and auto-recovery.

## HARDENING FEATURES IMPLEMENTED

### 1. Non-Blocking I/O Operations
- **Implementation**: ThreadPoolExecutor with 8 worker threads
- **Location**: `hydrax_utils.py` line 9
- **Impact**: Prevents blocking on HTTP requests, file I/O, and API calls
```python
EXEC = ThreadPoolExecutor(max_workers=8)
```

### 2. FloodWait Protection
- **Implementation**: Exponential backoff for Telegram API rate limits (429 errors)
- **Location**: `hydrax_utils.py` `send_with_retry()` function
- **Retry Schedule**: 1s → 2s → 4s → 8s → 16s → 32s (max 6 attempts)
- **Impact**: Graceful handling of Telegram rate limits without crashes

### 3. Per-User Rate Limiting
- **Implementation**: Sliding window rate limiter (10 requests/minute per user)
- **Location**: `hydrax_utils.py` `rate_limited()` decorator
- **Impact**: Prevents abuse and ensures fair resource usage
- **Storage**: In-memory dictionary with timestamp cleanup

### 4. Atomic File Operations
- **Implementation**: Temp file + `os.replace()` pattern
- **Location**: `hydrax_utils.py` `atomic_write_json()` function
- **Impact**: Prevents corrupted files during concurrent writes
- **Pattern**: Write to `.tmp` → Atomic rename to final filename

### 5. Graceful Shutdown Handling
- **Implementation**: SIGINT/SIGTERM signal handlers
- **Location**: Each bot's main function
- **Impact**: Clean shutdown with resource cleanup
- **Features**: 
  - Stops Telegram polling gracefully
  - Shuts down ThreadPoolExecutor
  - Logs shutdown completion

### 6. Latency Monitoring
- **Implementation**: Decorator-based latency measurement with JSON logging
- **Location**: `hydrax_utils.py` `measure_latency()` decorator
- **Metrics**: p50, p90, p99 percentiles with rolling statistics
- **Output**: Structured JSON logs for monitoring integration

### 7. Automatic File Cleanup
- **Implementation**: Daily cleanup task for mission files
- **Location**: `bitten_production_bot.py` `setup_cleanup_task()`
- **Schedule**: Daily at startup, then every 24 hours
- **Rules**: Remove files >14 days old OR if >500 files total

### 8. Shared Utilities Module
- **File**: `/root/HydraX-v2/hydrax_utils.py`
- **Purpose**: DRY principle - avoid code duplication across bots
- **Functions**: All hardening helpers centralized in one location

## PM2 DEPLOYMENT CONFIGURATION

### Process Configuration
```javascript
// /root/HydraX-v2/pm2.config.js
{
  name: 'bitten-production-bot',
  script: 'bitten_production_bot.py',
  interpreter: 'python3',
  instances: 1,
  autorestart: true,
  max_memory_restart: '1G',
  max_restarts: 10,
  restart_delay: 4000,
  env: {
    BOT_TOKEN: os.getenv("BOT_TOKEN"),
    WEBAPP_BASE_URL: 'https://bitten.gold',
    CHAT_ID: '-1002581996861',
    ADMIN_IDS: '7176191872'
  }
}
```

### Environment Variables by Bot
- **Production Bot**: `BOT_TOKEN`, `WEBAPP_BASE_URL`, `CHAT_ID`, `ADMIN_IDS`
- **Voice Bot**: `VOICE_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN`, `CHAT_ID`, `ADMIN_IDS`
- **Athena Bot**: `BOT_TOKEN`, `CHAT_ID`, `ADMIN_IDS`

### SystemD Integration
- **Service**: `pm2-root.service` (auto-created by `pm2 startup`)
- **Auto-start**: Enabled on system boot
- **Persistence**: PM2 process list saved to `/root/.pm2/dump.pm2`

## OPERATIONAL COMMANDS

### Daily Operations
```bash
# Check all bot status
pm2 status

# View live logs
pm2 logs --lines 50

# Restart if needed
pm2 restart all

# Real-time monitoring dashboard
pm2 monit
```

### Troubleshooting Commands
```bash
# Check specific bot
pm2 describe bitten-production-bot

# Restart single bot
pm2 restart bitten-production-bot

# Stop and start
pm2 stop bitten-production-bot
pm2 start bitten-production-bot

# View detailed logs
pm2 logs bitten-production-bot --lines 200 --format

# Check memory usage
pm2 list --format table
```

### Log Locations
- **PM2 Logs**: `/root/.pm2/logs/`
- **Combined**: `{botname}-out-{id}.log`
- **Errors**: `{botname}-error-{id}.log`
- **PM2 System**: `/root/.pm2/pm2.log`

## VERIFICATION CHECKLIST

### ✅ Deployment Verification
- [x] All 3 bots running under PM2 management
- [x] Auto-restart enabled (max 10 restarts)
- [x] Environment variables correctly set
- [x] SystemD service enabled for boot persistence
- [x] PM2 configuration saved

### ✅ Hardening Verification
- [x] Non-blocking I/O: ThreadPoolExecutor active
- [x] Rate limiting: 10 req/min per user enforced
- [x] FloodWait: Exponential backoff on 429 errors
- [x] Atomic writes: All JSON operations use temp files
- [x] Graceful shutdown: Signal handlers registered
- [x] Latency monitoring: JSON logs with percentiles
- [x] Auto-cleanup: Daily mission file cleanup scheduled

### ✅ Smoke Tests Passed
- [x] Production bot responds to API calls
- [x] Voice bot responds to API calls
- [x] Athena bot initialized successfully
- [x] No webhook conflicts resolved
- [x] No duplicate process conflicts

## ERROR PATTERNS RESOLVED

### Before Hardening
- **Bot crashes** on network timeouts
- **File corruption** during concurrent writes
- **Rate limit violations** causing 429 errors
- **Memory leaks** from blocking operations
- **Process conflicts** between multiple instances
- **No monitoring** of performance metrics

### After Hardening
- **Resilient networking** with retry logic
- **Atomic file operations** prevent corruption
- **Rate limiting** prevents API abuse
- **Non-blocking I/O** prevents memory issues
- **PM2 management** handles conflicts automatically
- **Comprehensive monitoring** with structured logs

## PERFORMANCE IMPROVEMENTS

### Resource Usage
- **Memory**: Stable usage, no leaks from blocking operations
- **CPU**: Reduced blocking, better thread utilization
- **Network**: Retry logic prevents cascading failures
- **Disk I/O**: Atomic writes prevent corruption

### Reliability
- **Uptime**: Auto-restart on crashes (max 10 attempts)
- **Error Recovery**: Exponential backoff prevents rapid failures
- **Monitoring**: Latency metrics for performance tracking
- **Maintenance**: Automated cleanup prevents disk bloat

## MAINTENANCE NOTES

### Daily Tasks
- Check `pm2 status` for any restart alerts
- Monitor memory usage via `pm2 monit`
- Review error logs if restart count increases

### Weekly Tasks
- Review latency metrics in logs
- Check disk usage in `/missions/` directory
- Verify cleanup task is running (should keep <500 files)

### Monthly Tasks
- Update bot tokens if rotated
- Review PM2 configuration for optimization
- Archive old log files if disk usage high

## FILE REFERENCES

### Core Files Modified
- `/root/HydraX-v2/hydrax_utils.py` - Shared utilities (NEW)
- `/root/HydraX-v2/bitten_production_bot.py` - Hardened production bot
- `/root/HydraX-v2/bitten_voice_personality_bot.py` - Hardened voice bot
- `/root/HydraX-v2/athena_mission_bot.py` - Hardened mission bot
- `/root/HydraX-v2/pm2.config.js` - PM2 configuration

### Configuration Files
- `/root/.pm2/dump.pm2` - Saved PM2 process list
- `/etc/systemd/system/pm2-root.service` - SystemD service
- `/root/HydraX-v2/.env` - Environment variables

---

**This hardening implementation ensures enterprise-grade reliability, monitoring, and maintainability for all Telegram bot operations.**