#!/bin/bash
# HydraSocket v1 Automated Backup Script

set -e

DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%s)
BACKUP_DIR="/opt/hydrasocket/backups"
DB_PATH="/root/HydraX-v2/event_bus/bitten_events.db"
STATE_DIR="/root/HydraX-v2/state"

# Create directories
mkdir -p "$BACKUP_DIR/$DATE"
mkdir -p "$STATE_DIR"

echo "🗄️ Starting HydraSocket backup - $DATE"

# Backup database
echo "Backing up database..."
cp "$DB_PATH" "$BACKUP_DIR/$DATE/bitten_events_$DATE.db"

# Verify backup integrity
if sqlite3 "$BACKUP_DIR/$DATE/bitten_events_$DATE.db" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database backup verified"
else
    echo "❌ Database backup integrity check failed"
    exit 1
fi

# Export sequence index
echo "Exporting sequence index..."
python3 -c "
import sqlite3
import json
import time

conn = sqlite3.connect('$DB_PATH')
cursor = conn.execute('SELECT account_id, last_seq FROM account_sequences')
seq_data = {row[0]: row[1] for row in cursor.fetchall()}

backup_data = {
    'timestamp': time.time(),
    'date': '$DATE',
    'sequences': seq_data,
    'total_accounts': len(seq_data)
}

with open('$BACKUP_DIR/$DATE/seq_index_$DATE.json', 'w') as f:
    json.dump(backup_data, f, indent=2)

# Also save to state directory for hourly updates
with open('$STATE_DIR/seq_index.json', 'w') as f:
    json.dump(backup_data, f, indent=2)

conn.close()
print(f'✅ Sequence index exported: {len(seq_data)} accounts')
"

# Backup configuration files
echo "Backing up configuration..."
cp -r /root/HydraX-v2/openapi "$BACKUP_DIR/$DATE/"
cp /root/HydraX-v2/ecosystem.config.js "$BACKUP_DIR/$DATE/"
cp /root/HydraX-v2/.env "$BACKUP_DIR/$DATE/env_backup" 2>/dev/null || echo "No .env file found"

# Create backup manifest
cat > "$BACKUP_DIR/$DATE/manifest.json" << EOF
{
  "backup_date": "$DATE",
  "timestamp": $TIMESTAMP,
  "files": {
    "database": "bitten_events_$DATE.db",
    "sequences": "seq_index_$DATE.json",
    "config": ["openapi/", "ecosystem.config.js", "env_backup"]
  },
  "version": "hydrasocket-v1.0.0"
}
EOF

# Compress old backups (older than 7 days)
echo "Compressing old backups..."
find "$BACKUP_DIR" -name "*.db" -mtime +7 -exec gzip {} \;

# Remove old backups (older than 30 days)
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -type d -mtime +30 -empty -delete

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$DATE" | cut -f1)

echo "✅ Backup completed successfully"
echo "📁 Location: $BACKUP_DIR/$DATE"
echo "📊 Size: $BACKUP_SIZE"
echo "🗓️ Retention: 30 days"