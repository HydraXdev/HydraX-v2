# BITTEN v2.0 → v1.0 Rollback Instructions

## Quick Start

```bash
# Test first (recommended)
./rollback_to_v1.sh --dry-run

# Execute rollback
./rollback_to_v1.sh

# Automated rollback (no prompts)
./rollback_to_v1.sh --auto-confirm
```

## What the Script Does

1. **Stops all v2.0 PM2 processes** - Gracefully stops event bus architecture
2. **Creates emergency backup** - Snapshots current v2.0 state before changes
3. **Restores database** - Replaces bitten.db with v1.0 backup
4. **Restores code** - Overwrites critical files with v1.0 versions
5. **Recreates PM2 processes** - Starts v1.0 services (elite_guard, webapp, etc.)
6. **Verifies system health** - Checks processes, ports, database, endpoints

## Available Backups

Located in: `/root/HydraX-v2/backups/`

- `bitten_v1_complete_backup.tar.gz` (394M) - Complete v1.0 codebase
- `HydraX-v2_backup_20251008.tar.gz` (368M) - Earlier v1.0 snapshot
- `bitten_v1_backup_20251008.db` (148M) - v1.0 database

## Safety Features

### Dry-Run Mode
- Tests rollback without making changes
- Shows exactly what will happen
- Verifies backups exist and are accessible

### Emergency Backup
- Creates timestamped backup of v2.0 before rollback
- Saved to `/root/HydraX-v2/backups/emergency_v2_backup_[timestamp].tar.gz`
- Allows rolling forward if needed

### Confirmation Prompts
- Shows selected backups
- Shows rollback plan
- Requires explicit confirmation (unless --auto-confirm)

### Logging
- All actions logged to timestamped file
- Located at `/root/HydraX-v2/rollback_[timestamp].log`
- Includes success/failure status for each step

## Post-Rollback Verification

```bash
# Check PM2 processes
pm2 list

# Verify expected processes running:
# - elite_guard
# - relay_to_telegram
# - webapp
# - command_router
# - confirm_listener
# - outcome_daemon

# Check ZMQ ports
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)"

# Test webapp health
curl http://localhost:8888/healthz

# Check database
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals;"

# Monitor logs
pm2 logs
```

## If Rollback Fails

1. **Check the log file** - `/root/HydraX-v2/rollback_[timestamp].log`
2. **Emergency backup exists** - Can restore v2.0 from emergency backup
3. **PM2 status** - `pm2 list` shows which processes failed
4. **Manual recovery** - Can manually restore files from backups

## Expected Differences v1.0 vs v2.0

**v2.0 Processes (stopped):**
- event_bus, event_logger, unified_tracker, tracking_bridge

**v1.0 Processes (restored):**
- elite_guard (signal generation)
- relay_to_telegram (Telegram alerts)
- webapp (port 8888 API/UI)
- command_router (fire commands to EA)
- confirm_listener (trade confirmations)
- outcome_daemon (signal tracking)

## Troubleshooting

### "Backup directory not found"
```bash
mkdir -p /root/HydraX-v2/backups
# Move existing backups into this directory
```

### "No backup files found"
- Verify backups exist: `ls -lh /root/HydraX-v2/backups/`
- Script looks for: `*_backup_*.tar.gz` or `*_v1_*.tar.gz`

### "Process not found in PM2"
- This is normal if v2.0 processes aren't running
- Script will skip and continue

### "Database file missing"
- Emergency backup already created before this error
- Can manually restore from backup

## Command Reference

```bash
# Dry-run test
./rollback_to_v1.sh --dry-run

# Interactive rollback (recommended)
./rollback_to_v1.sh

# Automated rollback
./rollback_to_v1.sh --auto-confirm

# Check script location
which rollback_to_v1.sh
# Should output: /root/HydraX-v2/rollback_to_v1.sh

# Verify executable
ls -l /root/HydraX-v2/rollback_to_v1.sh
# Should show: -rwxr-xr-x (executable)
```

## Emergency Contact

If rollback fails and system is broken:

1. Review log file (timestamped in /root/HydraX-v2/)
2. Emergency backup available at `/root/HydraX-v2/backups/emergency_v2_backup_[timestamp].tar.gz`
3. Can manually extract and restore files
4. Database emergency backup: `/root/HydraX-v2/backups/bitten_v2_emergency_[timestamp].db`
