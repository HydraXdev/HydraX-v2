#!/bin/bash
# Auto-update handover file with timestamp

cd /root/HydraX-v2/temp_work

# Add timestamp to handover
echo "" >> HANDOVER.md
echo "---" >> HANDOVER.md
echo "## Auto-save timestamp: $(date '+%Y-%m-%d %H:%M:%S')" >> HANDOVER.md

# Create backup
cp HANDOVER.md "HANDOVER_backup_$(date +%Y%m%d_%H%M%S).md"

# Keep only last 5 backups
ls -t HANDOVER_backup_*.md | tail -n +6 | xargs -r rm

echo "✅ Handover updated at $(date)"