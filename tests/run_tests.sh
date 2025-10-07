#!/bin/bash
# Quick test runner script for BITTEN Mission Flow Dry-Run Tests

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🎯 BITTEN Mission Flow Dry-Run Tests"
echo -e "==================================================${NC}\n"

# Change to test directory
cd "$(dirname "$0")"

# Run tests
echo -e "${YELLOW}Running test suite...${NC}\n"
python3 dry_run_mission_flow.py

EXIT_CODE=$?

# Display results summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}Safe to proceed with deployment${NC}"
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}Review results before deployment${NC}"
fi

echo ""
echo -e "${BLUE}View detailed results:${NC}"
echo "  cat /root/HydraX-v2/tests/dry_run_results.json | python3 -m json.tool"

echo ""
echo -e "${BLUE}Quick reference:${NC}"
echo "  cat /root/HydraX-v2/tests/QUICK_START.md"

exit $EXIT_CODE
