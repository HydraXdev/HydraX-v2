#!/bin/bash
# Event Bus Validation Suite Deployment Script
# Sets up 24-48h validation monitoring

set -e

echo "🚀 Deploying Event Bus Validation Suite"
echo "======================================="

# Make scripts executable
chmod +x /root/HydraX-v2/event_bus_validation_harness.py
chmod +x /root/HydraX-v2/hourly_validation_monitor.py
chmod +x /root/HydraX-v2/fallback_drill_test.py
chmod +x /root/HydraX-v2/validation_dashboard.py

echo "✅ Made validation scripts executable"

# Test that outcome mirrorer is running
if pgrep -f "outcome_mirrorer" > /dev/null; then
    echo "✅ Outcome Mirrorer is running"
else
    echo "⚠️ Outcome Mirrorer not found - starting it..."
    cd /root/HydraX-v2
    nohup python3 outcome_mirrorer.py > outcome_mirrorer.log 2>&1 &
    sleep 2
    if pgrep -f "outcome_mirrorer" > /dev/null; then
        echo "✅ Outcome Mirrorer started successfully"
    else
        echo "❌ Failed to start Outcome Mirrorer"
        exit 1
    fi
fi

# Run initial validation test
echo "🧪 Running initial validation test..."
cd /root/HydraX-v2
python3 event_bus_validation_harness.py
if [ $? -eq 0 ]; then
    echo "✅ Initial validation PASSED"
else
    echo "❌ Initial validation FAILED - check logs"
    exit 1
fi

# Set up cron job for hourly monitoring
echo "⏰ Setting up hourly validation monitoring..."

# Remove existing cron job if present
crontab -l 2>/dev/null | grep -v "hourly_validation_monitor" | crontab -

# Add new cron job
(crontab -l 2>/dev/null; echo "0 * * * * cd /root/HydraX-v2 && python3 hourly_validation_monitor.py >> /root/HydraX-v2/cron_validation.log 2>&1") | crontab -

echo "✅ Hourly monitoring cron job installed"

# Start validation dashboard
echo "📊 Starting validation dashboard..."
cd /root/HydraX-v2

# Kill existing dashboard if running
pkill -f "validation_dashboard.py" || true
sleep 1

# Start new dashboard
nohup python3 validation_dashboard.py > validation_dashboard.log 2>&1 &
sleep 3

if pgrep -f "validation_dashboard.py" > /dev/null; then
    echo "✅ Validation dashboard started on http://localhost:8892"
else
    echo "❌ Failed to start validation dashboard"
fi

# Run fallback drill test
echo "🔧 Running fallback drill test..."
python3 fallback_drill_test.py
if [ $? -eq 0 ]; then
    echo "✅ Fallback drill test PASSED"
else
    echo "⚠️ Fallback drill test had issues - check logs"
fi

# Create monitoring script for easy status checks
cat > /root/HydraX-v2/check_validation_status.sh << 'EOF'
#!/bin/bash
# Quick validation status check

echo "🔍 Event Bus Validation Status"
echo "=============================="

# Check processes
echo "📊 Processes:"
if pgrep -f "outcome_mirrorer" > /dev/null; then
    echo "  ✅ Outcome Mirrorer: RUNNING"
else
    echo "  ❌ Outcome Mirrorer: STOPPED"
fi

if pgrep -f "validation_dashboard" > /dev/null; then
    echo "  ✅ Validation Dashboard: RUNNING (http://localhost:8892)"
else
    echo "  ❌ Validation Dashboard: STOPPED"
fi

# Check latest results
echo ""
echo "📈 Latest Validation Results:"
latest_result=$(ls -t /root/HydraX-v2/validation_results_*.json 2>/dev/null | head -1)
if [ -n "$latest_result" ]; then
    status=$(python3 -c "import json; print(json.load(open('$latest_result'))['overall']['status'])" 2>/dev/null || echo "UNKNOWN")
    timestamp=$(python3 -c "import json; print(json.load(open('$latest_result'))['overall']['timestamp'])" 2>/dev/null || echo "UNKNOWN")
    echo "  Status: $status"
    echo "  Time: $timestamp"
else
    echo "  No validation results found"
fi

# Check hourly monitoring
echo ""
echo "⏰ Hourly Monitoring:"
latest_hourly=$(ls -t /root/HydraX-v2/hourly_validation_*.json 2>/dev/null | head -1)
if [ -n "$latest_hourly" ]; then
    status=$(python3 -c "import json; print(json.load(open('$latest_hourly'))['overall_status'])" 2>/dev/null || echo "UNKNOWN")
    echo "  Last Check: $status"
else
    echo "  No hourly results found"
fi

# Check data sources
echo ""
echo "💾 Data Sources:"
if [ -f "/root/HydraX-v2/event_bus/bitten_events.db" ]; then
    bus_size=$(du -h /root/HydraX-v2/event_bus/bitten_events.db | cut -f1)
    echo "  ✅ Event Bus DB: $bus_size"
else
    echo "  ❌ Event Bus DB: MISSING"
fi

if [ -f "/root/HydraX-v2/dynamic_tracking.jsonl" ]; then
    jsonl_size=$(du -h /root/HydraX-v2/dynamic_tracking.jsonl | cut -f1)
    echo "  ✅ Dynamic Tracking JSONL: $jsonl_size"
else
    echo "  ❌ Dynamic Tracking JSONL: MISSING"
fi

echo ""
echo "🌐 Dashboard: http://localhost:8892"
echo "📊 Run full validation: python3 /root/HydraX-v2/event_bus_validation_harness.py"
echo "🔧 Test fallback: python3 /root/HydraX-v2/fallback_drill_test.py"
EOF

chmod +x /root/HydraX-v2/check_validation_status.sh

echo ""
echo "🎉 Event Bus Validation Suite Deployed Successfully!"
echo "=================================================="
echo ""
echo "📊 Validation Dashboard: http://localhost:8892"
echo "⏰ Hourly monitoring: Active (cron job installed)"
echo "🔍 Quick status check: ./check_validation_status.sh"
echo ""
echo "📋 Next Steps:"
echo "1. Monitor dashboard for 24-48 hours"
echo "2. Watch for any validation failures"
echo "3. After validation period, run Phase C cutover"
echo ""
echo "📁 Log Files:"
echo "  - /root/HydraX-v2/validation_harness.log"
echo "  - /root/HydraX-v2/hourly_validation.log"
echo "  - /root/HydraX-v2/fallback_drill.log"
echo "  - /root/HydraX-v2/validation_dashboard.log"
echo ""
echo "🚨 Alert Thresholds:"
echo "  - 3 consecutive hourly failures triggers alert"
echo "  - >0.5% delta in counts/sums triggers warning"
echo "  - >5% latency regression triggers warning"