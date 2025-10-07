#!/bin/bash
# CUTOVER: MetaSocket Golden Test Runner
# Executes all 4 golden tests in sequence and reports results

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 CUTOVER: MetaSocket Golden Test Suite${NC}"
echo "============================================================"

# Check SOURCE environment
SOURCE=${SOURCE:-ea}
echo -e "📊 SOURCE setting: ${YELLOW}$SOURCE${NC}"

if [[ "$SOURCE" != "metasocket" && "$SOURCE" != "both" ]]; then
    echo -e "${RED}❌ SKIP: SOURCE must be 'metasocket' or 'both' for MetaSocket tests${NC}"
    echo "   Set: export SOURCE=metasocket && ./run_metasocket_tests.sh"
    exit 1
fi

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

# Function to run a test
run_test() {
    local test_name="$1"
    local test_script="$2"
    local test_num="$3"

    echo -e "\n${BLUE}🚀 Running Test ${test_num}: ${test_name}${NC}"
    echo "=" * 40

    if python3 "$test_script"; then
        echo -e "${GREEN}✅ Test ${test_num} PASSED: ${test_name}${NC}"
        TEST_RESULTS+=("✅ Test ${test_num}: ${test_name} - PASSED")
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Test ${test_num} FAILED: ${test_name}${NC}"
        TEST_RESULTS+=("❌ Test ${test_num}: ${test_name} - FAILED")
        ((TESTS_FAILED++))
    fi
}

# Create test directory if it doesn't exist
mkdir -p /root/HydraX-v2/tests/metasocket

# Run all 4 golden tests
run_test "Order Latency (<500ms p95)" "/root/HydraX-v2/tests/metasocket/01_order_latency_test.py" "01"
run_test "Manual Close" "/root/HydraX-v2/tests/metasocket/02_manual_close_test.py" "02"
run_test "SL/TP Handling" "/root/HydraX-v2/tests/metasocket/03_sl_tp_test.py" "03"
run_test "Reconnect/Recovery" "/root/HydraX-v2/tests/metasocket/04_reconnect_test.py" "04"

# Final results
echo -e "\n${BLUE}📊 CUTOVER TEST SUMMARY${NC}"
echo "============================================================"

for result in "${TEST_RESULTS[@]}"; do
    echo -e "$result"
done

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$(( (TESTS_PASSED * 100) / TOTAL_TESTS ))

echo ""
echo -e "Total Tests: ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Success Rate: ${YELLOW}$SUCCESS_RATE%${NC}"

# Generate test report
REPORT_FILE="/root/HydraX-v2/logs/metasocket_test_results_$(date +%Y%m%d_%H%M%S).json"
mkdir -p "$(dirname "$REPORT_FILE")"

cat > "$REPORT_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "source": "$SOURCE",
    "total_tests": $TOTAL_TESTS,
    "passed": $TESTS_PASSED,
    "failed": $TESTS_FAILED,
    "success_rate": $SUCCESS_RATE,
    "results": [
$(IFS=$'\n'; echo "${TEST_RESULTS[*]}" | sed 's/.*Test \([0-9]*\): \(.*\) - \(.*\)/        {"test": "\1", "name": "\2", "result": "\3"}/' | paste -sd ',' -)
    ]
}
EOF

echo -e "📄 Test report saved: ${YELLOW}$REPORT_FILE${NC}"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED - MetaSocket CUTOVER Ready!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed - Review results before CUTOVER${NC}"
    exit 1
fi