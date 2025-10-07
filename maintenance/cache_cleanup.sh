#!/bin/bash
# Cache Cleanup Maintenance Script
# Addresses System Audit Bottleneck #2: Storage optimization
# Safely cleans pip cache, npm cache, and temporary files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧹 BITTEN System Cache Cleanup"
echo "=============================="
echo ""

# Function to show size before/after
show_size() {
    local path=$1
    local name=$2
    if [ -d "$path" ]; then
        local size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo "$name: $size"
    else
        echo "$name: Not found"
    fi
}

# Show initial sizes
echo "📊 Current Cache Sizes:"
echo "----------------------"
show_size "/root/.cache/pip" "Pip cache"
show_size "$PROJECT_ROOT/node_modules" "Node modules"
show_size "/root/.npm" "NPM cache"
show_size "/tmp" "Temp files"
echo ""

# Pip cache cleanup (keep last 30 days)
echo "🔧 Cleaning pip cache (keeping last 30 days)..."
if command -v pip &> /dev/null; then
    pip cache purge --quiet 2>/dev/null || true
    pip cache remove '*' --quiet 2>/dev/null || true
fi
echo "✅ Pip cache cleaned"

# NPM cache cleanup
echo "🔧 Cleaning NPM cache..."
if command -v npm &> /dev/null; then
    npm cache clean --force 2>/dev/null || true
fi
echo "✅ NPM cache cleaned"

# Clean temporary build files
echo "🔧 Cleaning temporary build files..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Python build artifacts cleaned"

# Clean old log files (>30 days)
echo "🔧 Cleaning old log files (>30 days)..."
find "$PROJECT_ROOT" -type f -name "*.log" -mtime +30 -delete 2>/dev/null || true
find "/tmp" -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
echo "✅ Old logs cleaned"

# Clean old ZMQ socket files
echo "🔧 Cleaning stale ZMQ sockets..."
find /tmp -type s -name "bitten_*" -mtime +1 -delete 2>/dev/null || true
echo "✅ ZMQ sockets cleaned"

echo ""
echo "📊 Final Cache Sizes:"
echo "--------------------"
show_size "/root/.cache/pip" "Pip cache"
show_size "$PROJECT_ROOT/node_modules" "Node modules"
show_size "/root/.npm" "NPM cache"
show_size "/tmp" "Temp files"
echo ""
echo "✅ Cache cleanup complete!"
echo ""
echo "💡 TIP: Run this script weekly via cron:"
echo "   0 2 * * 0 $SCRIPT_DIR/cache_cleanup.sh"
