#!/bin/bash
# Create safety backup of critical modules

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lockbox_core_modules_$TIMESTAMP.zip"

echo "🔐 Creating safety backup: $BACKUP_NAME"

# List of critical files/dirs to backup
CRITICAL_MODULES=(
    "apex_venom_v7_unfiltered.py"          # VENOM signal engine
    "working_signal_generator.py"          # Signal generator
    "src/bitten_core/fire_router.py"       # Fire router with ZMQ
    "webapp_server_optimized.py"           # Web interface
    "bitten_production_bot.py"             # Main bot
    "zmq_bitten_controller.py"             # ZMQ controller
    "zmq_telemetry_service.py"             # Telemetry
    "zmq_xp_integration.py"                # XP logic
    "zmq_risk_integration.py"              # Risk logic
    ".env"                                 # Environment config
)

# Check which files exist
EXISTING_FILES=""
for file in "${CRITICAL_MODULES[@]}"; do
    if [ -f "$file" ]; then
        EXISTING_FILES="$EXISTING_FILES $file"
    fi
done

# Create backup
if [ -n "$EXISTING_FILES" ]; then
    zip -r "$BACKUP_NAME" $EXISTING_FILES
    echo "✅ Backup created: $BACKUP_NAME"
    ls -lh "$BACKUP_NAME"
else
    echo "❌ No critical files found to backup"
fi