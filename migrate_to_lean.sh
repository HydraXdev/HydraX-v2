#!/bin/bash
# Migrate to APEX Lean

echo "🔄 Migrating to APEX Lean..."

# Stop old processes
pkill -f apex_v5_live_real
pkill -f apex_engine_supervisor

# Backup old engine
mv apex_v5_live_real.py apex_v5_live_real.py.old 2>/dev/null

# Create symlink so existing scripts still work
ln -sf apex_v5_lean.py apex_v5_live_real.py

# Clean up lock files
rm -f .apex_engine.pid .apex_engine.lock

echo "✅ Migration complete!"
echo ""
echo "🎯 APEX Lean is ready!"
echo "   - Use 'python3 apex_control.py' to manage"
echo "   - Edit 'apex_config.json' to tune"
echo "   - Check 'apex_lean.log' for output"