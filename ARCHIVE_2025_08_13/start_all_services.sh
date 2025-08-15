#!/bin/bash
"""
SERVICE LAUNCHER v1.0
Start all BITTEN infrastructure services

Author: BITTEN Trading System
Date: August 6, 2025
"""

echo "🚀 Starting BITTEN Infrastructure Services..."

# Change to the correct directory
cd /root/HydraX-v2

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to start a service in background
start_service() {
    local service_name=$1
    local script_name=$2
    
    echo "Starting $service_name..."
    nohup python3 $script_name > logs/${service_name}_startup.log 2>&1 &
    local pid=$!
    echo "✅ $service_name started (PID: $pid)"
    sleep 2
}

# Start all services
echo ""
echo "🔧 Starting core infrastructure services..."

start_service "node_registry" "node_registry.py"
start_service "heartbeat_monitor" "heartbeat_monitor.py"
start_service "handshake_processor" "handshake_processor.py"
start_service "confirmation_logger" "confirmation_logger.py"
start_service "position_tracker" "position_tracker.py"
start_service "citadel_monitor" "citadel_protection_monitor.py"
start_service "health_dashboard" "health_check.py"

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

echo ""
echo "📊 Checking service status..."

# Check which services are running
check_service() {
    local service_name=$1
    if pgrep -f "$service_name" > /dev/null; then
        echo "✅ $service_name: Running"
    else
        echo "❌ $service_name: Stopped"
    fi
}

check_service "node_registry.py"
check_service "heartbeat_monitor.py"
check_service "handshake_processor.py"
check_service "confirmation_logger.py"
check_service "position_tracker.py"
check_service "citadel_protection_monitor.py"
check_service "health_check.py"

echo ""
echo "🌐 Service URLs:"
echo "  - Health Dashboard: http://localhost:5567"
echo "  - Health API: http://localhost:5567/health"
echo ""

echo "📝 Log files:"
echo "  - Service logs: /root/HydraX-v2/logs/"
echo "  - Startup logs: /root/HydraX-v2/logs/*_startup.log"
echo ""

echo "🎯 Testing basic connectivity..."

# Test Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Not accessible"
fi

# Test Health Dashboard
echo -n "Health Dashboard: "
sleep 2
if curl -s http://localhost:5567/health > /dev/null 2>&1; then
    echo "✅ Accessible"
else
    echo "❌ Not accessible"
fi

echo ""
echo "🎉 Service startup complete!"
echo ""
echo "To stop all services, run:"
echo "  pkill -f 'python3.*\\.py'"
echo ""
echo "To view logs:"
echo "  tail -f logs/*.log"