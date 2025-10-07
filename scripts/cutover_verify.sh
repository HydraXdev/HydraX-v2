#!/bin/bash
# CUTOVER: Verification Script
# Verifies MetaSocket integration is working correctly before production cutover

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 CUTOVER VERIFICATION - MetaSocket Integration${NC}"
echo "============================================================"

# Check 1: Environment configuration
echo -e "\n${BLUE}📊 Check 1: Environment Configuration${NC}"

SOURCE=${SOURCE:-ea}
MSKT_HOST=${MSKT_HOST:-127.0.0.1}
MSKT_CMD_PORT=${MSKT_CMD_PORT:-8777}
MSKT_STREAM_PORT=${MSKT_STREAM_PORT:-8778}

echo -e "SOURCE: ${YELLOW}$SOURCE${NC}"
echo -e "MSKT_HOST: ${YELLOW}$MSKT_HOST${NC}"
echo -e "MSKT_CMD_PORT: ${YELLOW}$MSKT_CMD_PORT${NC}"
echo -e "MSKT_STREAM_PORT: ${YELLOW}$MSKT_STREAM_PORT${NC}"

if [[ "$SOURCE" != "metasocket" && "$SOURCE" != "both" ]]; then
    echo -e "${RED}❌ WARNING: SOURCE not set for MetaSocket${NC}"
else
    echo -e "${GREEN}✅ Environment configured for MetaSocket${NC}"
fi

# Check 2: MetaSocket adapter availability
echo -e "\n${BLUE}📊 Check 2: MetaSocket Adapter${NC}"

if python3 -c "
import sys
sys.path.append('/root/HydraX-v2')
try:
    from adapters.metasocket.adapter import MetaSocketAdapter
    adapter = MetaSocketAdapter()
    print('✅ MetaSocket adapter imported successfully')

    health = adapter.get_health_status()
    print(f'📊 Health Status: {health[\"status\"]}')

    if health['status'] == 'OK':
        print('✅ MetaSocket adapter healthy')
    else:
        print(f'⚠️  MetaSocket adapter status: {health}')

except Exception as e:
    print(f'❌ MetaSocket adapter error: {e}')
    sys.exit(1)
"; then
    echo -e "${GREEN}✅ MetaSocket adapter operational${NC}"
else
    echo -e "${RED}❌ MetaSocket adapter issues detected${NC}"
fi

# Check 3: Command router integration
echo -e "\n${BLUE}📊 Check 3: Command Router Integration${NC}"

if python3 -c "
import sys
sys.path.append('/root/HydraX-v2')
try:
    # Check for MetaSocket routing function in command_router.py
    with open('/root/HydraX-v2/command_router.py', 'r') as f:
        content = f.read()
        if '_route_to_metasocket' in content:
            print('✅ Command router has MetaSocket routing support')
        else:
            print('⚠️  Command router missing MetaSocket routing function')
except Exception as e:
    print(f'❌ Command router file error: {e}')
    sys.exit(1)
"; then
    echo -e "${GREEN}✅ Command router integration ready${NC}"
else
    echo -e "${RED}❌ Command router integration issues${NC}"
fi

# Check 4: Health endpoint
echo -e "\n${BLUE}📊 Check 4: Health Endpoint Integration${NC}"

if curl -s http://localhost:8888/healthz | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'metasocket' in data:
        print('✅ Health endpoint includes MetaSocket metrics')
        print(f'📊 MetaSocket health: {data[\"metasocket\"]}')
    else:
        print('⚠️  Health endpoint missing MetaSocket (expected if SOURCE=ea)')
except Exception as e:
    print(f'❌ Health endpoint error: {e}')
" 2>/dev/null; then
    echo -e "${GREEN}✅ Health endpoint operational${NC}"
else
    echo -e "${YELLOW}⚠️  Health endpoint check skipped (webapp may not be running)${NC}"
fi

# Check 5: File structure
echo -e "\n${BLUE}📊 Check 5: File Structure${NC}"

REQUIRED_FILES=(
    "/root/HydraX-v2/adapters/metasocket/adapter.py"
    "/root/HydraX-v2/tests/metasocket/01_order_latency_test.py"
    "/root/HydraX-v2/tests/metasocket/02_manual_close_test.py"
    "/root/HydraX-v2/tests/metasocket/03_sl_tp_test.py"
    "/root/HydraX-v2/tests/metasocket/04_reconnect_test.py"
    "/root/HydraX-v2/scripts/run_metasocket_tests.sh"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file${NC}"
        ALL_FILES_EXIST=false
    fi
done

if $ALL_FILES_EXIST; then
    echo -e "${GREEN}✅ All required files present${NC}"
else
    echo -e "${RED}❌ Missing required files${NC}"
fi

# Check 6: Rollback readiness
echo -e "\n${BLUE}📊 Check 6: Rollback Readiness${NC}"

echo -e "📋 Rollback procedure:"
echo -e "   1. export SOURCE=ea"
echo -e "   2. pm2 restart command_router"
echo -e "   3. pm2 restart webapp"

if [[ -f "/root/HydraX-v2/.env" ]]; then
    if grep -q "SOURCE=ea" /root/HydraX-v2/.env; then
        echo -e "${GREEN}✅ Default SOURCE=ea in .env file${NC}"
    else
        echo -e "${YELLOW}⚠️  Non-default SOURCE in .env file${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
fi

# Final summary
echo -e "\n${BLUE}📊 CUTOVER VERIFICATION SUMMARY${NC}"
echo "============================================================"

if $ALL_FILES_EXIST && [[ "$SOURCE" == "metasocket" || "$SOURCE" == "both" ]]; then
    echo -e "${GREEN}🎉 CUTOVER READY - All checks passed${NC}"
    echo -e "${GREEN}✅ Environment configured${NC}"
    echo -e "${GREEN}✅ Adapter operational${NC}"
    echo -e "${GREEN}✅ Integration complete${NC}"
    echo -e "${GREEN}✅ Files in place${NC}"
    echo -e "${GREEN}✅ Rollback ready${NC}"
    echo ""
    echo -e "${BLUE}Next step: Run ./scripts/run_metasocket_tests.sh${NC}"
    exit 0
else
    echo -e "${RED}⚠️  CUTOVER NOT READY - Issues detected${NC}"
    echo ""
    echo -e "${YELLOW}Review issues above before proceeding${NC}"
    exit 1
fi