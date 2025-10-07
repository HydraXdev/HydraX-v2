#!/bin/bash
# MetaSocket Integration Validation Runner
# Executes comprehensive validation suite with proper environment setup

echo "🚀 METASOCKET INTEGRATION VALIDATION RUNNER"
echo "=============================================="

# Set working directory
cd /root/HydraX-v2/src/metasocket

# Check Python environment
echo "📋 Environment Check:"
echo "  Python: $(python3 --version)"
echo "  Working directory: $(pwd)"
echo "  Available symbols: $(python3 -c "from symbols import SYMBOLS; print(len(SYMBOLS))")"

# Create logs directory
mkdir -p /tmp/metasocket_logs

# Run validation with proper error handling
echo ""
echo "🧪 Starting validation suite..."
echo "Logs will be saved to: /tmp/metasocket_validation.log"
echo ""

# Execute validation script
python3 metasocket_validation.py 2>&1 | tee /tmp/metasocket_validation.log

# Check exit code
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "📊 Validation Complete!"
echo "Exit code: $EXIT_CODE"
echo "Full logs available at: /tmp/metasocket_validation.log"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed - Ready for production deployment"
else
    echo "❌ Some tests failed - Review logs and fix issues before merging"
fi

exit $EXIT_CODE