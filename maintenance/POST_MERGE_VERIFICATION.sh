#!/bin/bash
# Post-Merge Verification Script for chore/maintenance-suite
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Purpose: Verify maintenance suite deployment after merge

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 BITTEN MAINTENANCE SUITE - POST-MERGE VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing: $test_name... "

    if eval "$test_command" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Verify maintenance directory exists
echo "📁 Directory Structure Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Maintenance directory exists" "[ -d /root/HydraX-v2/maintenance ]"
run_test "Logs directory exists" "[ -d /root/HydraX-v2/maintenance/logs ]"
run_test "Reports directory exists" "[ -d /root/HydraX-v2/maintenance/reports ]"
run_test "Cache directory exists" "[ -d /root/HydraX-v2/maintenance/cache ]"

echo ""

# 2. Verify Python files exist
echo "🐍 Python Module Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Health check module" "[ -f /root/HydraX-v2/maintenance/health_check.py ]"
run_test "Database health module" "[ -f /root/HydraX-v2/maintenance/database_health.py ]"
run_test "Log analyzer module" "[ -f /root/HydraX-v2/maintenance/log_analyzer.py ]"
run_test "Report generator module" "[ -f /root/HydraX-v2/maintenance/report_generator.py ]"
run_test "Main maintenance module" "[ -f /root/HydraX-v2/maintenance/run_maintenance.py ]"

echo ""

# 3. Verify Python syntax
echo "📝 Python Syntax Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Health check syntax" "python3 -m py_compile /root/HydraX-v2/maintenance/health_check.py"
run_test "Database health syntax" "python3 -m py_compile /root/HydraX-v2/maintenance/database_health.py"
run_test "Log analyzer syntax" "python3 -m py_compile /root/HydraX-v2/maintenance/log_analyzer.py"
run_test "Report generator syntax" "python3 -m py_compile /root/HydraX-v2/maintenance/report_generator.py"
run_test "Main maintenance syntax" "python3 -m py_compile /root/HydraX-v2/maintenance/run_maintenance.py"

echo ""

# 4. Test imports (no execution)
echo "📦 Module Import Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Health check imports" "python3 -c 'import sys; sys.path.insert(0, \"/root/HydraX-v2/maintenance\"); import health_check'"
run_test "Database health imports" "python3 -c 'import sys; sys.path.insert(0, \"/root/HydraX-v2/maintenance\"); import database_health'"
run_test "Log analyzer imports" "python3 -c 'import sys; sys.path.insert(0, \"/root/HydraX-v2/maintenance\"); import log_analyzer'"
run_test "Report generator imports" "python3 -c 'import sys; sys.path.insert(0, \"/root/HydraX-v2/maintenance\"); import report_generator'"

echo ""

# 5. Check cron entries
echo "⏰ Cron Job Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Weekly maintenance cron exists" "crontab -l | grep -q 'run_maintenance.py --weekly'"
run_test "Daily health check cron exists" "crontab -l | grep -q 'health_check.py --quick'"
run_test "Weekly cache cleanup cron exists" "crontab -l | grep -q 'run_maintenance.py --cleanup-only'"

echo ""

# 6. Verify CI cache (optional - may not exist on first run)
echo "💾 CI Cache Verification (Optional)"
echo "────────────────────────────────────────────────────────────────────────────────"

if [ -f /root/HydraX-v2/maintenance/cache/flake8_results.json ]; then
    echo -e "${GREEN}✓${NC} CI cache exists (from previous run)"
else
    echo -e "${YELLOW}⚠${NC} CI cache not found (normal for first deployment)"
fi

echo ""

# 7. Run quick health check
echo "🏥 Quick Health Check Test"
echo "────────────────────────────────────────────────────────────────────────────────"

cd /root/HydraX-v2/maintenance
if python3 health_check.py --quick > /tmp/health_check_test.log 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Health check executed successfully"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Health check execution failed"
    echo "Check /tmp/health_check_test.log for details"
    ((TESTS_FAILED++))
fi

echo ""

# 8. Verify permissions
echo "🔐 Permission Verification"
echo "────────────────────────────────────────────────────────────────────────────────"

run_test "Maintenance scripts executable" "[ -x /root/HydraX-v2/maintenance/run_maintenance.py ]"
run_test "Health check executable" "[ -x /root/HydraX-v2/maintenance/health_check.py ]"
run_test "Log directory writable" "[ -w /root/HydraX-v2/maintenance/logs ]"
run_test "Reports directory writable" "[ -w /root/HydraX-v2/maintenance/reports ]"
run_test "Cache directory writable" "[ -w /root/HydraX-v2/maintenance/cache ]"

echo ""

# 9. Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VERIFICATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo "Total Tests Run: $TOTAL_TESTS"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL VERIFICATION CHECKS PASSED${NC}"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Monitor first maintenance run: tail -f /root/HydraX-v2/maintenance/logs/maintenance.log"
    echo "2. Check reports: ls -lh /root/HydraX-v2/maintenance/reports/"
    echo "3. Review health dashboard: python3 /root/HydraX-v2/maintenance/health_check.py"
    echo ""
    exit 0
else
    echo -e "${RED}✗ VERIFICATION FAILED - $TESTS_FAILED test(s) failed${NC}"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Check /tmp/health_check_test.log for health check errors"
    echo "2. Verify all files were merged correctly"
    echo "3. Ensure Python dependencies are installed"
    echo ""
    exit 1
fi
