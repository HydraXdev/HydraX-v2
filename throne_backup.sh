#!/bin/bash
#
# BITTEN Commander Throne Backup Script
# Backs up throne database and configuration with rotation
#
# Usage: ./throne_backup.sh
# Can be added to cron for automated backups
#

# Configuration
BACKUP_ROOT="/root/HydraX-v2/backups/throne"
DB_PATH="/root/HydraX-v2/data/commander_throne.db"
CONFIG_FILE="/root/HydraX-v2/commander_throne.py"
LOG_FILE="/root/HydraX-v2/logs/throne_backup.log"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_STAMP=$(date +%Y-%m-%d)

# Ensure directories exist
mkdir -p "$BACKUP_ROOT"
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

# Start backup process
log "========================================="
log "Starting Commander Throne backup"
log "Backup timestamp: $TIMESTAMP"

# Create today's backup directory
BACKUP_DIR="$BACKUP_ROOT/$DATE_STAMP"
mkdir -p "$BACKUP_DIR"

# 1. Backup SQLite Database
log "Backing up commander_throne.db..."
if [ -f "$DB_PATH" ]; then
    # Check if sqlite3 is available
    if command -v sqlite3 >/dev/null 2>&1; then
        # Use SQLite backup command for consistency
        sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/commander_throne_${TIMESTAMP}.db'" 2>&1 | tee -a "$LOG_FILE"
        BACKUP_STATUS=${PIPESTATUS[0]}
    else
        # Fallback to Python sqlite3 module
        log "sqlite3 command not found, using Python fallback"
        python3 -c "
import sqlite3
import shutil
try:
    # Create a backup using Python
    src = sqlite3.connect('$DB_PATH')
    dst = sqlite3.connect('$BACKUP_DIR/commander_throne_${TIMESTAMP}.db')
    src.backup(dst)
    src.close()
    dst.close()
    print('Database backup successful via Python')
except Exception as e:
    print(f'Database backup failed: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG_FILE"
        BACKUP_STATUS=$?
    fi
    
    if [ $BACKUP_STATUS -eq 0 ]; then
        log "Database backup successful"
        
        # Compress the backup
        gzip -9 "$BACKUP_DIR/commander_throne_${TIMESTAMP}.db"
        log "Database backup compressed"
    else
        error_exit "Database backup failed"
    fi
else
    log "WARNING: Database file not found at $DB_PATH"
fi

# 2. Backup throne configuration
log "Backing up throne configuration..."
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$BACKUP_DIR/commander_throne_${TIMESTAMP}.py"
    if [ $? -eq 0 ]; then
        log "Configuration backup successful"
    else
        error_exit "Configuration backup failed"
    fi
else
    log "WARNING: Configuration file not found at $CONFIG_FILE"
fi

# 3. Backup related configuration files
log "Backing up related configuration..."
CONFIG_FILES=(
    "/root/HydraX-v2/templates/throne_dashboard.html"
    "/root/HydraX-v2/templates/throne_login.html"
    "/root/HydraX-v2/THRONE_CONFIG.md"
    "/root/HydraX-v2/systemd/throne.service"
)

for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        filename=$(basename "$config")
        cp "$config" "$BACKUP_DIR/${filename}_${TIMESTAMP}"
        log "Backed up: $filename"
    fi
done

# 4. Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${TIMESTAMP}.txt" << EOF
BITTEN Commander Throne Backup Manifest
=======================================
Timestamp: $TIMESTAMP
Hostname: $(hostname)
User: $(whoami)

Files Backed Up:
$(ls -la "$BACKUP_DIR" | grep -v "^total" | grep -v "manifest")

Database Information:
$(if [ -f "$DB_PATH" ]; then
    echo "Size: $(du -h "$DB_PATH" | cut -f1)"
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "Tables: $(sqlite3 "$DB_PATH" ".tables" 2>/dev/null)"
        echo "Row Counts:"
        for table in $(sqlite3 "$DB_PATH" ".tables" 2>/dev/null); do
            count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table" 2>/dev/null)
            echo "  $table: $count rows"
        done
    else
        # Use Python to get database info
        python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
    tables = cursor.fetchall()
    print('Tables:', ', '.join([t[0] for t in tables]))
    print('Row Counts:')
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
        count = cursor.fetchone()[0]
        print(f'  {table[0]}: {count} rows')
    conn.close()
except Exception as e:
    print(f'Error reading database: {e}')
" 2>/dev/null || echo "Unable to read database information"
    fi
else
    echo "Database not found"
fi)

System Information:
$(uname -a)
$(df -h "$BACKUP_ROOT" | tail -1)
EOF

# 5. Create verification checksum
log "Creating verification checksums..."
cd "$BACKUP_DIR"
sha256sum * > "checksums_${TIMESTAMP}.sha256"
cd - > /dev/null

# 6. Rotate old backups
log "Rotating old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_ROOT" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null
REMAINING_BACKUPS=$(find "$BACKUP_ROOT" -type d -name "20*" | wc -l)
log "Remaining backup sets: $REMAINING_BACKUPS"

# 7. Create latest symlink
log "Updating latest backup symlink..."
ln -sfn "$BACKUP_DIR" "$BACKUP_ROOT/latest"

# 8. Generate backup report
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
FILE_COUNT=$(find "$BACKUP_DIR" -type f | wc -l)

log "Backup completed successfully!"
log "Backup location: $BACKUP_DIR"
log "Backup size: $BACKUP_SIZE"
log "Files backed up: $FILE_COUNT"

# 9. Check backup integrity
log "Verifying backup integrity..."
cd "$BACKUP_DIR"
sha256sum -c "checksums_${TIMESTAMP}.sha256" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "Backup integrity verified - all checksums match"
else
    error_exit "Backup integrity check failed!"
fi
cd - > /dev/null

# 10. Optional: Send notification (uncomment if needed)
# if command -v mail >/dev/null 2>&1; then
#     echo "Commander Throne backup completed at $TIMESTAMP. Size: $BACKUP_SIZE" | \
#     mail -s "Throne Backup Success" admin@example.com
# fi

# Success exit
log "Throne backup process completed successfully"
log "========================================="
exit 0