#!/bin/bash
"""
SERVICE STOPPER v1.0
Stop all BITTEN infrastructure services

Author: BITTEN Trading System
Date: August 6, 2025
"""

echo "🛑 Stopping BITTEN Infrastructure Services..."

echo ""
echo "🔍 Finding service processes..."

# Function to stop a service
stop_service() {
    local service_name=$1
    local pids=$(pgrep -f "$service_name" | head -5)
    
    if [ -n "$pids" ]; then
        echo "Stopping $service_name (PIDs: $pids)..."
        echo "$pids" | xargs kill
        sleep 2
        
        # Force kill if still running
        local remaining=$(pgrep -f "$service_name")
        if [ -n "$remaining" ]; then
            echo "Force killing $service_name..."
            echo "$remaining" | xargs kill -9
        fi
        echo "✅ $service_name stopped"
    else
        echo "⚪ $service_name not running"
    fi
}

# Stop all services
stop_service "node_registry.py"
stop_service "heartbeat_monitor.py" 
stop_service "handshake_processor.py"
stop_service "confirmation_logger.py"
stop_service "position_tracker.py"
stop_service "citadel_protection_monitor.py"
stop_service "health_check.py"

echo ""
echo "📊 Checking for any remaining processes..."
remaining=$(ps aux | grep -E "(node_registry|heartbeat_monitor|handshake_processor|confirmation_logger|position_tracker|citadel_protection|health_check)" | grep -v grep | wc -l)

if [ "$remaining" -eq 0 ]; then
    echo "✅ All services stopped successfully"
else
    echo "⚠️ $remaining processes still running"
    ps aux | grep -E "(node_registry|heartbeat_monitor|handshake_processor|confirmation_logger|position_tracker|citadel_protection|health_check)" | grep -v grep
fi

echo ""
echo "🧹 Cleanup complete!"