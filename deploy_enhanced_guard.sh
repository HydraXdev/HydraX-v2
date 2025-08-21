#!/bin/bash

# Elite Guard Enhanced Deployment Script
# Safe deployment with rollback capability

echo "=========================================="
echo "ELITE GUARD ENHANCED DEPLOYMENT"
echo "=========================================="

# Check if percent parameter provided
PERCENT=${1:-30}
echo "Deployment at $PERCENT% optimization"

# Function to check current processes
check_processes() {
    echo "Checking current processes..."
    pm2 list | grep -E "elite_guard|relay_to_telegram|command_router"
}

# Function to verify signal flow
verify_signal_flow() {
    echo "Verifying signal flow..."
    
    # Check if ZMQ ports are bound
    netstat -tuln | grep -E "5555|5556|5557|5558|5560" | head -5
    
    # Check recent signals
    if [ -f /root/HydraX-v2/truth_log.jsonl ]; then
        echo "Recent signals:"
        tail -2 /root/HydraX-v2/truth_log.jsonl | head -2
    fi
}

# Backup current state
echo "Creating deployment checkpoint..."
cp /root/HydraX-v2/truth_log.jsonl /root/HydraX-v2/truth_log.backup_$(date +%Y%m%d_%H%M%S).jsonl 2>/dev/null || true

# Stage 1: Stop relay temporarily (brief signal pause)
echo ""
echo "Stage 1: Pausing signal relay..."
pm2 stop relay_to_telegram 2>/dev/null || true
sleep 2

# Stage 2: Deploy enhanced Elite Guard
echo ""
echo "Stage 2: Deploying enhanced Elite Guard at $PERCENT% optimization..."

# Stop old Elite Guard
pm2 stop elite_guard 2>/dev/null || true
pm2 delete elite_guard 2>/dev/null || true
sleep 2

# Start enhanced Elite Guard
pm2 start /root/HydraX-v2/elite_guard_enhanced.py \
    --name elite_guard \
    --interpreter python3 \
    -- --percent $PERCENT

sleep 5

# Stage 3: Restart relay
echo ""
echo "Stage 3: Restarting signal relay..."
pm2 restart relay_to_telegram 2>/dev/null || pm2 start /root/HydraX-v2/elite_guard_zmq_relay.py --name relay_to_telegram --interpreter python3

# Stage 4: Start tracking components
echo ""
echo "Stage 4: Starting performance tracking..."

# Start comprehensive tracker if not running
pm2 list | grep -q "perf_tracker" || pm2 start /root/HydraX-v2/comprehensive_performance_tracker.py --name perf_tracker --interpreter python3

# Start optimizer if not running
pm2 list | grep -q "optimizer_v2" || pm2 start /root/HydraX-v2/pattern_optimizer_v2.py --name optimizer_v2 --interpreter python3

# Start dashboard if not running
pm2 list | grep -q "dashboard_v2" || pm2 start /root/HydraX-v2/performance_dashboard_v2.py --name dashboard_v2 --interpreter python3

# Stage 5: Verification
echo ""
echo "Stage 5: Verification..."
sleep 5

check_processes
echo ""
verify_signal_flow

# Stage 6: Create monitoring script
cat > /root/HydraX-v2/monitor_enhanced.sh << 'EOF'
#!/bin/bash
# Monitor enhanced Elite Guard performance

echo "=== ENHANCED ELITE GUARD MONITOR ==="
echo "Time: $(date)"
echo ""

# Check if running
if pm2 list | grep -q "elite_guard.*online"; then
    echo "✅ Elite Guard: RUNNING"
else
    echo "❌ Elite Guard: NOT RUNNING"
fi

# Check recent signals
echo ""
echo "Recent Signals (last 10 min):"
find /root/HydraX-v2/enhanced_signals.jsonl -mmin -10 2>/dev/null | xargs wc -l 2>/dev/null || echo "0"

# Check A/B test results
if [ -f /root/HydraX-v2/elite_guard_enhanced.log ]; then
    echo ""
    echo "A/B Test Summary:"
    grep "Rollout Level" /root/HydraX-v2/elite_guard_enhanced.log | tail -1
    grep "Original Signals:" /root/HydraX-v2/elite_guard_enhanced.log | tail -1
    grep "Optimized Signals:" /root/HydraX-v2/elite_guard_enhanced.log | tail -1
fi

# Check performance
echo ""
echo "Dashboard: http://localhost:8891"
echo ""
echo "To adjust rollout: ./adjust_rollout.sh [percent]"
echo "To rollback: ./rollback_enhanced.sh"
EOF

chmod +x /root/HydraX-v2/monitor_enhanced.sh

# Create rollback script
cat > /root/HydraX-v2/rollback_enhanced.sh << 'EOF'
#!/bin/bash
# Rollback to original Elite Guard

echo "⚠️  ROLLING BACK TO ORIGINAL ELITE GUARD..."

# Stop enhanced
pm2 stop elite_guard
pm2 delete elite_guard

# Restore original
pm2 start /root/HydraX-v2/elite_guard_with_citadel.py \
    --name elite_guard \
    --interpreter python3

pm2 restart relay_to_telegram

echo "✅ Rollback complete"
pm2 list | grep elite_guard
EOF

chmod +x /root/HydraX-v2/rollback_enhanced.sh

# Create adjustment script
cat > /root/HydraX-v2/adjust_rollout.sh << 'EOF'
#!/bin/bash
# Adjust rollout percentage

PERCENT=${1:-50}
echo "Adjusting rollout to $PERCENT%..."

pm2 delete elite_guard
pm2 start /root/HydraX-v2/elite_guard_enhanced.py \
    --name elite_guard \
    --interpreter python3 \
    -- --percent $PERCENT

echo "✅ Rollout adjusted to $PERCENT%"
EOF

chmod +x /root/HydraX-v2/adjust_rollout.sh

# Final summary
echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo "✅ Enhanced Elite Guard deployed at $PERCENT% optimization"
echo "✅ Performance tracking active"
echo "✅ Dashboard available at http://localhost:8891"
echo ""
echo "Commands:"
echo "  Monitor: ./monitor_enhanced.sh"
echo "  Adjust:  ./adjust_rollout.sh [percent]"
echo "  Rollback: ./rollback_enhanced.sh"
echo ""
echo "Next steps:"
echo "  - Monitor for 10 minutes"
echo "  - If win rate improving, increase to 50%"
echo "  - If win rate declining, rollback immediately"
echo "=========================================="