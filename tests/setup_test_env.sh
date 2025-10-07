#!/bin/bash
# Setup script for BITTEN Mission Flow Dry-Run Tests

set -e

echo "=================================================="
echo "🔧 BITTEN Test Environment Setup"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Create test directory if not exists
echo -e "\n${YELLOW}Creating test directory...${NC}"
mkdir -p /root/HydraX-v2/tests
echo -e "${GREEN}✓ Directory created${NC}"

# Make test script executable
echo -e "\n${YELLOW}Making test script executable...${NC}"
chmod +x /root/HydraX-v2/tests/dry_run_mission_flow.py
echo -e "${GREEN}✓ Script is executable${NC}"

# Check required source directories
echo -e "\n${YELLOW}Checking source directories...${NC}"
REQUIRED_DIRS=(
    "/root/HydraX-v2/src"
    "/root/HydraX-v2/src/missions"
    "/root/HydraX-v2/src/bitten_core"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir exists${NC}"
    else
        echo -e "${YELLOW}⚠ $dir does not exist (will be created if needed)${NC}"
        mkdir -p "$dir"
    fi
done

# Create __init__.py files for Python modules
echo -e "\n${YELLOW}Setting up Python module structure...${NC}"
touch /root/HydraX-v2/src/__init__.py
touch /root/HydraX-v2/src/missions/__init__.py
touch /root/HydraX-v2/src/bitten_core/__init__.py
echo -e "${GREEN}✓ Module structure ready${NC}"

# Check if session_manager exists
echo -e "\n${YELLOW}Checking for session_manager module...${NC}"
if [ -f "/root/HydraX-v2/src/missions/session_manager.py" ]; then
    echo -e "${GREEN}✓ session_manager.py found${NC}"
else
    echo -e "${RED}✗ session_manager.py NOT found${NC}"
    echo -e "${YELLOW}Note: Test 1, 3, and 7 will fail until this module is implemented${NC}"
fi

# Verify test script exists
echo -e "\n${YELLOW}Verifying test script...${NC}"
if [ -f "/root/HydraX-v2/tests/dry_run_mission_flow.py" ]; then
    LINES=$(wc -l < /root/HydraX-v2/tests/dry_run_mission_flow.py)
    echo -e "${GREEN}✓ dry_run_mission_flow.py found ($LINES lines)${NC}"
else
    echo -e "${RED}✗ dry_run_mission_flow.py NOT found${NC}"
    exit 1
fi

# Test Python import
echo -e "\n${YELLOW}Testing Python import path...${NC}"
python3 -c "import sys; sys.path.insert(0, '/root/HydraX-v2'); print('✓ Import path OK')" 2>&1 | grep -q "✓" && echo -e "${GREEN}✓ Python imports working${NC}" || echo -e "${RED}✗ Import issues detected${NC}"

# Summary
echo -e "\n=================================================="
echo -e "${GREEN}✅ Test Environment Setup Complete${NC}"
echo "=================================================="

echo -e "\n${YELLOW}Quick Start Commands:${NC}"
echo "  Run tests: python3 /root/HydraX-v2/tests/dry_run_mission_flow.py"
echo "  View results: cat /root/HydraX-v2/tests/dry_run_results.json"
echo "  Read docs: cat /root/HydraX-v2/tests/README_DRY_RUN.md"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "  1. Implement session_manager.py (if not exists)"
echo "  2. Run dry-run tests"
echo "  3. Fix any failures"
echo "  4. Proceed with mission system deployment"

echo ""
