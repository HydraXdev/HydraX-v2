#!/bin/bash

echo "========================================================================"
echo "BITTEN v2.0 Analytics Worker - Deployment Verification"
echo "========================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$PYTHON_VERSION >= 3.8" | bc -l) )); then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python $PYTHON_VERSION (requires 3.8+)${NC}"
fi

# Check 2: Dependencies
echo -n "Checking dependencies... "
MISSING_DEPS=0
for pkg in apscheduler psycopg2 zmq firebase_admin; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        echo -e "${RED}✗ Missing: $pkg${NC}"
        MISSING_DEPS=1
    fi
done
if [ $MISSING_DEPS -eq 0 ]; then
    echo -e "${GREEN}✓ All dependencies installed${NC}"
fi

# Check 3: Database connection
echo -n "Checking PostgreSQL connection... "
if psql -h localhost -U postgres -d bitten_v2 -c "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✓ Database connected${NC}"
else
    echo -e "${RED}✗ Cannot connect to database${NC}"
fi

# Check 4: ZMQ port 5560
echo -n "Checking ZMQ port 5560... "
if netstat -tuln 2>/dev/null | grep -q ":5560"; then
    echo -e "${GREEN}✓ Port 5560 bound${NC}"
else
    echo -e "${YELLOW}⚠ Port 5560 not bound (telemetry bridge may not be running)${NC}"
fi

# Check 5: Firebase credentials
echo -n "Checking Firebase credentials... "
if [ -f "/root/bitten-firebase-sa.json" ]; then
    echo -e "${GREEN}✓ Credentials file exists${NC}"
else
    echo -e "${RED}✗ Credentials file missing${NC}"
fi

# Check 6: Files exist
echo -n "Checking service files... "
FILES_MISSING=0
for file in main.py config.py jobs/outcome_tracker.py jobs/stats_aggregator.py jobs/firestore_mirror.py jobs/reconciliation.py jobs/reports.py; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        FILES_MISSING=1
    fi
done
if [ $FILES_MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ All service files present${NC}"
fi

# Check 7: Line count verification
echo -n "Verifying code integrity... "
TOTAL_LINES=$(find . -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')
if [ "$TOTAL_LINES" -ge 1800 ]; then
    echo -e "${GREEN}✓ $TOTAL_LINES lines of code${NC}"
else
    echo -e "${RED}✗ Only $TOTAL_LINES lines (expected 1837+)${NC}"
fi

echo ""
echo "========================================================================"
echo "Verification Complete"
echo "========================================================================"
echo ""
echo "To start the service:"
echo "  pm2 start main.py --name analytics_worker --interpreter python3"
echo ""
echo "To monitor logs:"
echo "  pm2 logs analytics_worker"
echo ""
