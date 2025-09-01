#!/bin/bash
# Archive obsolete tracking files
# Created: 2025-08-25T13:25:20.346972

echo "🗂️ Archiving obsolete tracking files..."

# Create archive directory
mkdir -p /root/HydraX-v2/archive_tracking_$(date +%Y%m%d)

# List of obsolete files to archive
FILES_TO_ARCHIVE=(
    "bitten_monitor.py"
    "citadel_protection_monitor.py"
    "clean_truth_writer.py"
    "convergence_tracker.py"
    "core_truth_integration.py"
    "dynamic_outcome_tracker.py"
    "elite_guard_signal_outcome.py"
    "monitor_candles.py"
    "monitor_signal_modes.py"
    "monitor_zmq_system.py"
    "mt5_instance_tracker.py"
    "network_latency_monitor.py"
    "outcome_tracker.py"
    "pattern_success_tracker.py"
    "position_tracker.py"
    "post_mortem_tracking_monitor.py"
    "production_monitor.py"
    "realtime_balance_tracker.py"
    "signal_outcome_monitor.py"
    "signal_truth_tracker.py"
    "simple_truth_tracker.py"
    "system_monitor.py"
    "trade_history_tracker.py"
    "truth_cli.py"
    "truth_dashboard_integration.py"
    "truth_log_query.py"
    "truth_position_integration.py"
    "truth_tracker.py"
    "webapp_truth_direct.py"
    "zmq_data_monitor.py"
    "zmq_market_data_truth_bridge.py"
    "zmq_trade_tracker.py"
    "zmq_truth_tracker_integration.py"
)

# Check for running processes before archiving
echo "⚠️ Checking for running processes..."
for file in "${FILES_TO_ARCHIVE[@]}"; do
    if pgrep -f "$file" > /dev/null; then
        echo "❌ WARNING: $file has running process. Skipping..."
    else
        if [ -f "/root/HydraX-v2/$file" ]; then
            mv "/root/HydraX-v2/$file" "/root/HydraX-v2/archive_tracking_$(date +%Y%m%d)/"
            echo "✅ Archived: $file"
        fi
    fi
done

echo "📊 Archive complete. Files moved to: /root/HydraX-v2/archive_tracking_$(date +%Y%m%d)/"
echo "⚠️ Remember to update any imports or dependencies in remaining files."
