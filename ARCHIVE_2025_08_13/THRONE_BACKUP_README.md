# BITTEN Commander Throne Backup System

## Overview

The Commander Throne backup system provides automated, production-ready backup and restore capabilities for the BITTEN throne control interface. This system ensures data integrity and business continuity with features including:

- **Automated daily backups** with configurable scheduling
- **7-day retention** with automatic rotation
- **Integrity verification** using SHA-256 checksums
- **Comprehensive logging** for audit trails
- **Health monitoring** with alerting capabilities
- **One-command restore** for disaster recovery

## Components

### 1. `throne_backup.sh` - Main Backup Script
The primary backup script that handles:
- SQLite database backup using proper `.backup` command
- Configuration file preservation
- Backup compression (gzip -9)
- Automatic rotation of old backups
- Integrity verification
- Detailed logging

### 2. `throne_restore.sh` - Restore Script
Disaster recovery script that:
- Restores from latest or specified backup
- Verifies backup integrity before restore
- Creates safety backup of current files
- Handles service restart automatically
- Provides detailed restore report

### 3. `throne_backup_monitor.sh` - Health Monitor
Monitoring script that checks:
- Backup age (alerts if >26 hours old)
- Backup size validation
- Integrity verification
- Disk space monitoring
- Generates health reports

## Quick Start

### Manual Backup
```bash
cd /root/HydraX-v2
./throne_backup.sh
```

### Automated Daily Backups
```bash
# Add to crontab
crontab -e

# Add this line for daily 3 AM backups:
0 3 * * * /root/HydraX-v2/throne_backup.sh >> /root/HydraX-v2/logs/throne_backup_cron.log 2>&1
```

### Restore from Backup
```bash
# Restore from latest backup
./throne_restore.sh

# Restore from specific backup
./throne_restore.sh /root/HydraX-v2/backups/throne/2025-07-15
```

### Monitor Backup Health
```bash
# Check backup health
./throne_backup_monitor.sh

# Add to cron for hourly health checks
0 * * * * /root/HydraX-v2/throne_backup_monitor.sh
```

## Backup Structure

```
/root/HydraX-v2/backups/throne/
├── 2025-07-15/
│   ├── commander_throne_20250715_030000.db.gz
│   ├── commander_throne_20250715_030000.py
│   ├── throne_dashboard.html_20250715_030000
│   ├── throne_login.html_20250715_030000
│   ├── manifest_20250715_030000.txt
│   └── checksums_20250715_030000.sha256
├── latest -> 2025-07-15/
└── health_report.txt
```

## What Gets Backed Up

1. **Database**: `commander_throne.db` - All command logs, sessions, rate limits
2. **Main Script**: `commander_throne.py` - Core throne application
3. **Templates**: HTML templates for dashboard and login
4. **Configuration**: Any throne-related config files
5. **Metadata**: Backup manifest with system information

## Monitoring and Alerts

The monitoring script checks:
- **Backup Age**: Warns if >26 hours, critical if >50 hours
- **Backup Size**: Ensures backups aren't empty
- **Integrity**: Verifies all checksums match
- **Disk Space**: Alerts if >80% full

Check alerts in: `/root/HydraX-v2/logs/throne_backup_alerts.log`

## Disaster Recovery Procedure

1. **Stop the throne service** (if running):
   ```bash
   systemctl stop throne.service
   ```

2. **Run restore script**:
   ```bash
   ./throne_restore.sh
   ```

3. **Verify restoration**:
   ```bash
   sqlite3 /root/HydraX-v2/data/commander_throne.db "PRAGMA integrity_check;"
   ```

4. **Restart service**:
   ```bash
   systemctl start throne.service
   ```

## Best Practices

1. **Test Restores**: Periodically test restore procedures in a non-production environment
2. **Monitor Logs**: Regularly check `/root/HydraX-v2/logs/throne_backup.log`
3. **Offsite Backup**: Consider syncing backups to remote storage
4. **Access Control**: Restrict access to backup directory (contains sensitive data)
5. **Retention Policy**: Adjust `RETENTION_DAYS` based on compliance requirements

## Troubleshooting

### Backup Fails
- Check disk space: `df -h /root/HydraX-v2/backups`
- Verify database accessibility: `sqlite3 /root/HydraX-v2/data/commander_throne.db ".tables"`
- Check permissions: `ls -la /root/HydraX-v2/data/`

### Restore Fails
- Verify backup integrity first: Run checksums manually
- Ensure throne service is stopped
- Check file permissions after restore

### Monitoring Alerts
- Review health report: `cat /root/HydraX-v2/backups/throne/health_report.txt`
- Check cron logs: `grep throne /var/log/cron`
- Verify backup directory: `ls -la /root/HydraX-v2/backups/throne/`

## Advanced Configuration

### Custom Retention Period
Edit `throne_backup.sh` and modify:
```bash
RETENTION_DAYS=14  # Keep 2 weeks instead of 7 days
```

### Email Notifications
Uncomment the mail section in `throne_backup.sh`:
```bash
if command -v mail >/dev/null 2>&1; then
    echo "Commander Throne backup completed at $TIMESTAMP. Size: $BACKUP_SIZE" | \
    mail -s "Throne Backup Success" admin@example.com
fi
```

### Remote Backup Sync
Add to backup script:
```bash
# Sync to remote server
rsync -avz "$BACKUP_DIR" user@backup-server:/backups/throne/
```

## Security Considerations

1. **Encryption**: Consider encrypting backups at rest
2. **Access Control**: Restrict backup directory to root only
3. **Audit Trail**: All backup operations are logged
4. **Integrity**: SHA-256 checksums prevent tampering

---

*Last Updated: 2025-07-15*
*Part of the BITTEN HydraX-v2 System*