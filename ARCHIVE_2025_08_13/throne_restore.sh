#!/bin/bash
#
# BITTEN Commander Throne Restore Script
# Restores throne database and configuration from backup
#
# Usage: ./throne_restore.sh [backup_directory]
# If no directory specified, uses latest backup
#

# Configuration
BACKUP_ROOT="/root/HydraX-v2/backups/throne"
DB_PATH="/root/HydraX-v2/data/commander_throne.db"
CONFIG_FILE="/root/HydraX-v2/commander_throne.py"
LOG_FILE="/root/HydraX-v2/logs/throne_restore.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Start restore process
log "========================================="
log "Starting Commander Throne restore"

# Determine backup to restore from
if [ -n "$1" ]; then
    RESTORE_DIR="$1"
else
    RESTORE_DIR="$BACKUP_ROOT/latest"
    log "No backup specified, using latest backup"
fi

# Verify backup directory exists
if [ ! -d "$RESTORE_DIR" ]; then
    error_exit "Backup directory not found: $RESTORE_DIR"
fi

log "Restoring from: $RESTORE_DIR"

# Verify checksums first
log "Verifying backup integrity..."
if [ -f "$RESTORE_DIR"/checksums_*.sha256 ]; then
    cd "$RESTORE_DIR"
    sha256sum -c checksums_*.sha256 > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        error_exit "Backup integrity check failed! Backup may be corrupted."
    fi
    cd - > /dev/null
    log "Backup integrity verified"
else
    log "WARNING: No checksum file found, cannot verify integrity"
fi

# Create safety backup of current files
log "Creating safety backup of current files..."
SAFETY_DIR="/root/HydraX-v2/backups/throne/pre-restore-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAFETY_DIR"

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$SAFETY_DIR/"
    log "Current database backed up to safety directory"
fi

if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$SAFETY_DIR/"
    log "Current configuration backed up to safety directory"
fi

# Stop throne service if running
if systemctl is-active --quiet throne.service 2>/dev/null; then
    log "Stopping throne service..."
    systemctl stop throne.service
    RESTART_SERVICE=true
fi

# Restore database
log "Restoring database..."
DB_BACKUP=$(ls -t "$RESTORE_DIR"/commander_throne_*.db.gz 2>/dev/null | head -1)
if [ -n "$DB_BACKUP" ]; then
    # Decompress and restore
    gunzip -c "$DB_BACKUP" > "${DB_PATH}.tmp"
    if [ $? -eq 0 ]; then
        mv "${DB_PATH}.tmp" "$DB_PATH"
        log "Database restored successfully"
    else
        rm -f "${DB_PATH}.tmp"
        error_exit "Database restoration failed"
    fi
else
    log "WARNING: No database backup found in restore directory"
fi

# Restore configuration
log "Restoring configuration..."
CONFIG_BACKUP=$(ls -t "$RESTORE_DIR"/commander_throne_*.py 2>/dev/null | head -1)
if [ -n "$CONFIG_BACKUP" ]; then
    cp "$CONFIG_BACKUP" "$CONFIG_FILE"
    if [ $? -eq 0 ]; then
        log "Configuration restored successfully"
    else
        error_exit "Configuration restoration failed"
    fi
else
    log "WARNING: No configuration backup found in restore directory"
fi

# Restore additional files
log "Restoring additional configuration files..."
for file in "$RESTORE_DIR"/*.html_* "$RESTORE_DIR"/*.md_* "$RESTORE_DIR"/*.service_*; do
    if [ -f "$file" ]; then
        # Extract original filename
        original_name=$(basename "$file" | sed 's/_[0-9]\{8\}_[0-9]\{6\}$//')
        
        # Determine destination based on file type
        case "$original_name" in
            *.html)
                dest="/root/HydraX-v2/templates/$original_name"
                ;;
            *.service)
                dest="/root/HydraX-v2/systemd/$original_name"
                ;;
            *)
                dest="/root/HydraX-v2/$original_name"
                ;;
        esac
        
        if [ -n "$dest" ]; then
            mkdir -p "$(dirname "$dest")"
            cp "$file" "$dest"
            log "Restored: $original_name"
        fi
    fi
done

# Set proper permissions
log "Setting file permissions..."
chmod 644 "$DB_PATH" 2>/dev/null
chmod 755 "$CONFIG_FILE" 2>/dev/null

# Restart service if it was running
if [ "$RESTART_SERVICE" = true ]; then
    log "Restarting throne service..."
    systemctl start throne.service
    sleep 2
    if systemctl is-active --quiet throne.service; then
        log "Throne service restarted successfully"
    else
        log "WARNING: Throne service failed to restart"
    fi
fi

# Verify restoration
log "Verifying restoration..."
if [ -f "$DB_PATH" ]; then
    # Check database integrity
    sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log "Database integrity check passed"
        
        # Show restored data summary
        log "Restored database summary:"
        for table in $(sqlite3 "$DB_PATH" ".tables" 2>/dev/null); do
            count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table" 2>/dev/null)
            log "  $table: $count rows"
        done
    else
        error_exit "Database integrity check failed!"
    fi
else
    log "WARNING: Database file not found after restore"
fi

# Display manifest if available
MANIFEST=$(ls -t "$RESTORE_DIR"/manifest_*.txt 2>/dev/null | head -1)
if [ -f "$MANIFEST" ]; then
    log "Backup manifest:"
    cat "$MANIFEST" | tee -a "$LOG_FILE"
fi

log "Restore completed successfully!"
log "Safety backup available at: $SAFETY_DIR"
log "========================================="

exit 0