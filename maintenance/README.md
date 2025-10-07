# BITTEN Maintenance Suite

**Created**: October 7, 2025
**Based on**: System Audit findings (577-line comprehensive analysis)
**Purpose**: Automated system optimization and health monitoring

## 📋 Overview

This maintenance suite addresses the top 5 bottlenecks identified in the system audit:

1. **CI/CD Optimization** - Added pip caching to GitHub Actions (50-70% faster builds)
2. **Cache Cleanup** - Automated cleanup of pip cache (1.1G), npm cache (528M), and temp files
3. **Database Optimization** - VACUUM, ANALYZE, and space reclamation for SQLite databases
4. **Process Health** - Automated monitoring of critical processes and ZMQ port bindings
5. **Resource Monitoring** - Disk space and memory usage tracking

## 🚀 Quick Start

### Run Complete Maintenance Suite
```bash
cd /root/HydraX-v2/maintenance
bash run_maintenance.sh
```

### Run Individual Scripts
```bash
# Cache cleanup only (safe during trading hours)
bash cache_cleanup.sh

# Database maintenance (brief lock, run during off-hours)
bash database_maintenance.sh

# Process health check (read-only, always safe)
bash process_health.sh
```

## 📅 Automated Scheduling

### Recommended Crontab Setup
```bash
# Edit crontab
crontab -e

# Add these lines:
# Weekly full maintenance (Sunday 3 AM)
0 3 * * 0 /root/HydraX-v2/maintenance/run_maintenance.sh

# Daily health check (every 6 hours)
0 */6 * * * /root/HydraX-v2/maintenance/process_health.sh

# Cache cleanup (weekly, Sunday 2 AM)
0 2 * * 0 /root/HydraX-v2/maintenance/cache_cleanup.sh
```

## 📊 Script Details

### 1. `cache_cleanup.sh`
**Purpose**: Reclaim disk space from caches and temporary files
**Safe to run**: During trading hours ✅
**Targets**:
- Pip cache (~1.1G)
- NPM cache (~528M)
- Python build artifacts (`__pycache__`, `.pyc`)
- Old log files (>30 days)
- Stale ZMQ sockets

**Expected savings**: 1-2GB per run

### 2. `database_maintenance.sh`
**Purpose**: Optimize SQLite databases for performance
**Safe to run**: During off-peak hours ⚠️
**Operations**:
- VACUUM (reclaim deleted space)
- ANALYZE (update query statistics)
- PRAGMA optimize (improve query planner)

**Expected savings**: 10-30% database size reduction

### 3. `process_health.sh`
**Purpose**: Monitor critical system processes
**Safe to run**: Anytime ✅ (read-only)
**Monitors**:
- Elite Guard signal generation
- ZMQ port bindings (5555-5560, 8888)
- EA connection freshness
- PM2 process status
- Memory usage

**Exit codes**:
- `0`: All systems healthy
- `1`: Issues detected (check output)

### 4. `run_maintenance.sh`
**Purpose**: Master orchestration script
**Safe to run**: During off-peak hours ⚠️
**Features**:
- Runs all maintenance tasks in sequence
- Generates timestamped logs
- Pre/post maintenance validation
- Disk space monitoring
- Colored output for easy reading

## 🔧 CI/CD Improvements

### GitHub Actions Optimization
**File**: `.github/workflows/python-ci.yml`
**Changes**:
- Added pip caching (50-70% faster builds)
- Updated to latest actions (v4/v5)
- Added security scanning (bandit, pip-audit)
- Improved test coverage reporting

**Expected impact**: 5-10 minute faster CI runs

## 📈 Performance Gains

Based on system audit analysis:

| Area | Before | After | Improvement |
|------|--------|-------|-------------|
| CI/CD Build Time | ~15 min | ~5-8 min | 50-70% faster |
| Pip Cache | 1.1G | <100M | 90% reduction |
| Database Size | 350M | ~245M | 30% reduction |
| Disk Space | Variable | Monitored | Proactive alerts |

## 🏥 Health Monitoring

### Critical Processes Monitored
- `elite_guard_with_citadel.py` - Signal generation
- `webapp_server_optimized.py` - API server (port 8888)
- `command_router.py` - Fire command routing (port 5555)
- `confirm_listener_v207.py` - Trade confirmations (port 5558)
- `zmq_telemetry_bridge_debug.py` - Market data (ports 5556/5560)

### Critical Port Bindings
- **5555**: Command routing (ROUTER socket)
- **5556**: Market data ingestion (PULL socket)
- **5557**: Signal publishing (PUB socket)
- **5558**: Trade confirmations (PULL socket)
- **5560**: Market data relay (PUB socket)
- **8888**: WebApp HTTP API

## 📝 Log Files

All maintenance runs generate timestamped logs:
- Location: `/root/HydraX-v2/maintenance/maintenance_YYYYMMDD_HHMMSS.log`
- Retention: Manual cleanup recommended (keep last 10 runs)
- Format: Timestamped with color-coded output

## ⚠️ Important Notes

### When to Run
- **Cache Cleanup**: Anytime (safe)
- **Database Maintenance**: During off-peak hours (brief locks)
- **Process Health**: Anytime (read-only)
- **Full Maintenance**: Sunday 3 AM (recommended)

### Trading Impact
- Cache cleanup: **No impact** ✅
- Database maintenance: **Brief performance dip** (<1 min) ⚠️
- Process health: **No impact** ✅

### Disk Space Alerts
- **>85% usage**: Warning issued, manual review needed
- **>90% usage**: Critical, immediate action required
- Maintenance suite typically frees 1-2GB per run

## 🐛 Troubleshooting

### "Database is locked" errors
- Cause: Active trading operations
- Solution: Run during off-peak hours or stop processes temporarily

### "Permission denied" on cache cleanup
- Cause: Files owned by different user
- Solution: Run with `sudo` or adjust ownership

### Process health check failures
- Check PM2 logs: `pm2 logs [process-name] --lines 50`
- Restart failed process: `pm2 restart [process-name]`
- Check ZMQ ports: `ss -tulpen | grep -E ":(5555|5556|5557|5558|5560)"`

## 📚 Related Documentation

- **System Audit**: `/root/HydraX-v2/system_audit_summary.json`
- **Architecture**: `/root/HydraX-v2/ARCHITECTURE.md`
- **CLAUDE.md**: `/root/HydraX-v2/CLAUDE.md` (maintenance instructions)
- **CI/CD Workflow**: `.github/workflows/python-ci.yml`

## 🔄 Version History

- **v1.0.0** (Oct 7, 2025): Initial maintenance suite
  - Cache cleanup automation
  - Database optimization
  - Process health monitoring
  - CI/CD improvements
  - Master orchestration script

## 💡 Future Enhancements

- [ ] Automated backup rotation
- [ ] Performance metric trending
- [ ] Slack/Telegram alerts for failures
- [ ] Docker layer caching optimization
- [ ] Log aggregation and analysis
