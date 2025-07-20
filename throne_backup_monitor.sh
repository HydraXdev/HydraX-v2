#!/bin/bash
#
# BITTEN Commander Throne Backup Monitor
# Monitors backup health and sends alerts
#
# Usage: ./throne_backup_monitor.sh
# Can be added to cron for regular health checks
#

# Configuration
BACKUP_ROOT="/root/HydraX-v2/backups/throne"
LOG_FILE="/root/HydraX-v2/logs/throne_backup_monitor.log"
ALERT_FILE="/root/HydraX-v2/logs/throne_backup_alerts.log"
WARNING_AGE_HOURS=26  # Alert if no backup in 26 hours
CRITICAL_AGE_HOURS=50 # Critical alert if no backup in 50 hours
MIN_BACKUP_SIZE_MB=1  # Minimum expected backup size in MB

# Ensure directories exist
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $1" | tee -a "$ALERT_FILE" "$LOG_FILE"
}

# Start monitoring
log "========================================="
log "Starting backup health check"

# Check if backup directory exists
if [ ! -d "$BACKUP_ROOT" ]; then
    alert "Backup root directory does not exist: $BACKUP_ROOT"
    exit 1
fi

# Find latest backup
LATEST_BACKUP=$(find "$BACKUP_ROOT" -type d -name "20*" | sort -r | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    alert "No backups found in $BACKUP_ROOT"
    exit 1
fi

log "Latest backup: $LATEST_BACKUP"

# Check backup age
BACKUP_AGE_SECONDS=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")))
BACKUP_AGE_HOURS=$((BACKUP_AGE_SECONDS / 3600))

log "Backup age: $BACKUP_AGE_HOURS hours"

if [ $BACKUP_AGE_HOURS -gt $CRITICAL_AGE_HOURS ]; then
    alert "CRITICAL: Latest backup is $BACKUP_AGE_HOURS hours old (threshold: $CRITICAL_AGE_HOURS hours)"
    EXIT_CODE=2
elif [ $BACKUP_AGE_HOURS -gt $WARNING_AGE_HOURS ]; then
    alert "WARNING: Latest backup is $BACKUP_AGE_HOURS hours old (threshold: $WARNING_AGE_HOURS hours)"
    EXIT_CODE=1
else
    log "Backup age is within acceptable range"
    EXIT_CODE=0
fi

# Check backup size
BACKUP_SIZE_BYTES=$(du -sb "$LATEST_BACKUP" | cut -f1)
BACKUP_SIZE_KB=$((BACKUP_SIZE_BYTES / 1024))
BACKUP_SIZE_MB=$((BACKUP_SIZE_BYTES / 1024 / 1024))

# If less than 1MB, show in KB
if [ $BACKUP_SIZE_MB -eq 0 ] && [ $BACKUP_SIZE_KB -gt 0 ]; then
    BACKUP_SIZE_DISPLAY="${BACKUP_SIZE_KB}KB"
else
    BACKUP_SIZE_DISPLAY="${BACKUP_SIZE_MB}MB"
fi

log "Backup size: $BACKUP_SIZE_DISPLAY"

# For size check, accept if we have at least 50KB (reasonable for compressed DB + configs)
MIN_BACKUP_SIZE_KB=50
if [ $BACKUP_SIZE_KB -lt $MIN_BACKUP_SIZE_KB ]; then
    alert "Backup size too small: $BACKUP_SIZE_DISPLAY (minimum: ${MIN_BACKUP_SIZE_KB}KB)"
    EXIT_CODE=2
fi

# Check for database backup
DB_BACKUP=$(ls "$LATEST_BACKUP"/commander_throne_*.db.gz 2>/dev/null | head -1)
if [ -z "$DB_BACKUP" ]; then
    alert "No database backup found in latest backup"
    EXIT_CODE=2
else
    log "Database backup found: $(basename "$DB_BACKUP")"
fi

# Check backup integrity
if [ -f "$LATEST_BACKUP"/checksums_*.sha256 ]; then
    log "Verifying backup integrity..."
    cd "$LATEST_BACKUP"
    sha256sum -c checksums_*.sha256 > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        alert "Backup integrity check failed!"
        EXIT_CODE=2
    else
        log "Backup integrity verified"
    fi
    cd - > /dev/null
else
    alert "No checksum file found in latest backup"
    EXIT_CODE=1
fi

# Check disk space
DISK_USAGE=$(df -h "$BACKUP_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
log "Backup disk usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 90 ]; then
    alert "CRITICAL: Backup disk usage is ${DISK_USAGE}%"
    EXIT_CODE=2
elif [ $DISK_USAGE -gt 80 ]; then
    alert "WARNING: Backup disk usage is ${DISK_USAGE}%"
    [ $EXIT_CODE -eq 0 ] && EXIT_CODE=1
fi

# Count total backups
TOTAL_BACKUPS=$(find "$BACKUP_ROOT" -type d -name "20*" | wc -l)
log "Total backup sets: $TOTAL_BACKUPS"

# Generate summary report
cat > "$BACKUP_ROOT/health_report.txt" << EOF
BITTEN Commander Throne Backup Health Report
============================================
Generated: $(date)

Latest Backup: $(basename "$LATEST_BACKUP")
Backup Age: $BACKUP_AGE_HOURS hours
Backup Size: $BACKUP_SIZE_DISPLAY
Total Backups: $TOTAL_BACKUPS
Disk Usage: ${DISK_USAGE}%

Status: $([ $EXIT_CODE -eq 0 ] && echo "HEALTHY" || ([ $EXIT_CODE -eq 1 ] && echo "WARNING" || echo "CRITICAL"))

Recent Backup History:
$(find "$BACKUP_ROOT" -type d -name "20*" -printf "%f\t%s bytes\t%TY-%Tm-%Td %TH:%TM\n" | sort -r | head -10)

Recent Alerts:
$(tail -n 10 "$ALERT_FILE" 2>/dev/null || echo "No recent alerts")
EOF

log "Health report saved to: $BACKUP_ROOT/health_report.txt"

# Exit with appropriate code
if [ $EXIT_CODE -eq 0 ]; then
    log "Backup health check completed - ALL OK"
elif [ $EXIT_CODE -eq 1 ]; then
    log "Backup health check completed - WARNINGS"
else
    log "Backup health check completed - CRITICAL ISSUES"
fi

log "========================================="
exit $EXIT_CODE