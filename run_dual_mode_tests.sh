#!/bin/bash

# BITTEN Dual-Mode Signal Testing Execution Script
# Author: Testing & Validation Lead (Agent 4)
# Purpose: Execute comprehensive dual-mode signal validation

echo "🚀 BITTEN Dual-Mode Signal Testing Framework"
echo "=============================================="
echo "Starting validation at $(date)"
echo ""

# Set up environment
export ENABLE_MOMENTUM_BURST=true
export ENABLE_SESSION_OPEN_FADE=true
export ENABLE_MICRO_BREAKOUT_RETEST=true
export DUAL_MODE_ENABLED=true
export OPTIMIZED_TP_SL_ENABLED=true

# Run the comprehensive test suite
echo "📊 Executing comprehensive test suite..."
echo "Testing new momentum patterns: momentum_burst, session_open_fade, micro_breakout_retest"
echo "Validating RAPID vs SNIPER classification logic"
echo "Verifying TP/SL calculations and R:R ratios"
echo "Checking backward compatibility and integration"
echo ""

cd /root/HydraX-v2

# Execute the test framework
python3 test_dual_mode_signals.py

# Capture exit code
EXIT_CODE=$?

echo ""
echo "=============================================="
echo "Test execution completed at $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed! System ready for deployment."
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review detailed report: dual_mode_test_report.json"
    echo "2. Deploy dual-mode system to production"
    echo "3. Monitor signal performance in live trading"
else
    echo "❌ Tests failed! System requires fixes before deployment."
    echo ""
    echo "📋 Required Actions:"
    echo "1. Review test failures in dual_mode_test_report.json"
    echo "2. Fix critical issues identified"
    echo "3. Re-run tests until all pass"
fi

echo ""
echo "📄 Log files generated:"
echo "- test_dual_mode_signals.log (execution log)"
echo "- dual_mode_test_report.json (detailed results)"

exit $EXIT_CODE