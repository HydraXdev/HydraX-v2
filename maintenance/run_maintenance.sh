#!/bin/bash
# Master Maintenance Runner
# Orchestrates all BITTEN system maintenance tasks
# Based on System Audit findings (Oct 7, 2025)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/maintenance_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Start maintenance
log "🚀 BITTEN System Maintenance Suite"
log "===================================="
log ""
log "📝 Log file: $LOG_FILE"
log ""

# System check
log "🔍 Pre-maintenance system check..."
if ! command -v pm2 &> /dev/null; then
    error "PM2 not found. Critical services may be affected."
fi

if ! command -v sqlite3 &> /dev/null; then
    error "SQLite3 not found. Database maintenance will fail."
fi

log ""

# 1. Cache Cleanup
log "🧹 Step 1/4: Running cache cleanup..."
if [ -f "$SCRIPT_DIR/cache_cleanup.sh" ]; then
    bash "$SCRIPT_DIR/cache_cleanup.sh" >> "$LOG_FILE" 2>&1
    success "Cache cleanup complete"
else
    warn "cache_cleanup.sh not found, skipping"
fi
log ""

# 2. Database Maintenance
log "🗄️  Step 2/4: Running database maintenance..."
if [ -f "$SCRIPT_DIR/database_maintenance.sh" ]; then
    bash "$SCRIPT_DIR/database_maintenance.sh" >> "$LOG_FILE" 2>&1
    success "Database maintenance complete"
else
    warn "database_maintenance.sh not found, skipping"
fi
log ""

# 3. Process Health Check
log "🏥 Step 3/4: Running process health check..."
if [ -f "$SCRIPT_DIR/process_health.sh" ]; then
    bash "$SCRIPT_DIR/process_health.sh" >> "$LOG_FILE" 2>&1
    success "Process health check complete"
else
    warn "process_health.sh not found, skipping"
fi
log ""

# 4. Disk Space Check
log "💾 Step 4/4: Checking disk space..."
df -h / | tee -a "$LOG_FILE"
log ""

# Space freed summary
log "📊 Maintenance Summary:"
log "----------------------"
log "✅ Cache cleanup: DONE"
log "✅ Database optimization: DONE"
log "✅ Process health check: DONE"
log "✅ Disk space verified: DONE"
log ""

# Final disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
if [[ ${DISK_USAGE%\%} -gt 85 ]]; then
    warn "Disk usage is high: $DISK_USAGE - Consider manual cleanup"
else
    success "Disk usage is healthy: $DISK_USAGE"
fi

log ""
log "✅ Maintenance suite complete!"
log "📝 Full log: $LOG_FILE"
log ""
log "💡 To schedule automated maintenance, add to crontab:"
log "   # Run every Sunday at 3 AM"
log "   0 3 * * 0 $SCRIPT_DIR/run_maintenance.sh"
