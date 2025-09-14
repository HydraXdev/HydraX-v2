#!/bin/bash
# Daily WINLOSS report runner for PM2 cron scheduling

REPORT_DIR="/root/HydraX-v2/reports/daily"
REPORT_SCRIPT="/root/HydraX-v2/tools/winloss_report.py"

# Create report directory if it doesn't exist
mkdir -p "$REPORT_DIR"

# Generate filename with date
DATE=$(date +%Y-%m-%d)
REPORT_FILE="$REPORT_DIR/winloss_${DATE}.txt"

# Run the report for yesterday (since this runs at midnight)
echo "Running WINLOSS report for $DATE..." > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
python3 "$REPORT_SCRIPT" yesterday >> "$REPORT_FILE" 2>&1

# Also generate a "latest" symlink for easy access
ln -sf "$REPORT_FILE" "$REPORT_DIR/latest.txt"

echo "Daily WINLOSS report saved to $REPORT_FILE"