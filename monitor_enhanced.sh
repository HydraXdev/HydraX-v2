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
