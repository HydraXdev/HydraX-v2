#!/bin/bash
# Database Maintenance Script
# Addresses System Audit Bottleneck #3: Database consolidation and optimization
# Vacuums, analyzes, and optimizes SQLite databases

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🗄️  BITTEN Database Maintenance"
echo "==============================="
echo ""

# Function to optimize a database
optimize_db() {
    local db_path=$1
    local db_name=$(basename "$db_path")

    if [ ! -f "$db_path" ]; then
        echo "⚠️  $db_name: Not found, skipping"
        return
    fi

    local size_before=$(du -h "$db_path" | cut -f1)
    echo "📊 $db_name: $size_before"

    # Run VACUUM to reclaim space
    echo "   🔧 Running VACUUM..."
    sqlite3 "$db_path" "VACUUM;" 2>/dev/null || echo "   ⚠️  VACUUM failed (may be in use)"

    # Run ANALYZE to update statistics
    echo "   🔧 Running ANALYZE..."
    sqlite3 "$db_path" "ANALYZE;" 2>/dev/null || echo "   ⚠️  ANALYZE failed"

    # Optimize query planner
    echo "   🔧 Optimizing query planner..."
    sqlite3 "$db_path" "PRAGMA optimize;" 2>/dev/null || true

    local size_after=$(du -h "$db_path" | cut -f1)
    echo "   ✅ Complete: $size_before → $size_after"
    echo ""
}

# Find and optimize all SQLite databases
echo "🔍 Finding SQLite databases..."
echo ""

# Main databases
optimize_db "$PROJECT_ROOT/bitten.db"
optimize_db "$PROJECT_ROOT/event_bus/bitten_events.db"
optimize_db "$PROJECT_ROOT/src/bitten_core/fire_mode.db"

# Find additional databases
find "$PROJECT_ROOT" -type f -name "*.db" -not -path "*/node_modules/*" -not -path "*/.git/*" | while read -r db; do
    optimize_db "$db"
done

echo "📈 Database Statistics:"
echo "----------------------"
echo ""

# Show table counts for main database
if [ -f "$PROJECT_ROOT/bitten.db" ]; then
    echo "📊 bitten.db tables:"
    sqlite3 "$PROJECT_ROOT/bitten.db" "SELECT name, (SELECT COUNT(*) FROM sqlite_master sm WHERE sm.name = m.name) as tables FROM sqlite_master m WHERE type='table' ORDER BY name;" 2>/dev/null | head -10 || true
    echo ""
fi

# Show disk usage
echo "💾 Total database disk usage:"
find "$PROJECT_ROOT" -type f -name "*.db" -not -path "*/node_modules/*" -not -path "*/.git/*" -exec du -ch {} + | tail -1

echo ""
echo "✅ Database maintenance complete!"
echo ""
echo "💡 TIP: Run this script weekly via cron:"
echo "   0 3 * * 0 $SCRIPT_DIR/database_maintenance.sh"
