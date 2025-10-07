#!/bin/bash
# CUTOVER ROLLBACK: Safely return to EA source
# This script reverts the system from MetaSocket back to EA mode

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 CUTOVER ROLLBACK: Returning to EA Source${NC}"
echo "============================================================"

# Check current SOURCE setting
CURRENT_SOURCE=${SOURCE:-ea}
echo -e "📊 Current SOURCE: ${YELLOW}$CURRENT_SOURCE${NC}"

if [[ "$CURRENT_SOURCE" == "ea" ]]; then
    echo -e "${GREEN}✅ System already using EA source${NC}"
    echo -e "${YELLOW}⚠️  Continuing rollback to ensure clean state${NC}"
fi

# Step 1: Update environment to EA
echo -e "\n${BLUE}🔄 Step 1: Setting SOURCE=ea in environment${NC}"

export SOURCE=ea
echo -e "✅ Runtime SOURCE set to: ${GREEN}ea${NC}"

# Update .env file if it exists
if [[ -f "/root/HydraX-v2/.env" ]]; then
    # Create backup
    cp /root/HydraX-v2/.env "/root/HydraX-v2/.env.backup.$(date +%Y%m%d_%H%M%S)"

    # Update SOURCE in .env
    if grep -q "^SOURCE=" /root/HydraX-v2/.env; then
        sed -i 's/^SOURCE=.*/SOURCE=ea/' /root/HydraX-v2/.env
        echo -e "✅ Updated SOURCE=ea in .env file"
    else
        echo "SOURCE=ea" >> /root/HydraX-v2/.env
        echo -e "✅ Added SOURCE=ea to .env file"
    fi
else
    echo -e "${YELLOW}⚠️  No .env file found - creating with SOURCE=ea${NC}"
    echo "SOURCE=ea" > /root/HydraX-v2/.env
fi

# Step 2: Restart command router
echo -e "\n${BLUE}🔄 Step 2: Restarting command router${NC}"

if pm2 list | grep -q "command_router"; then
    pm2 restart command_router
    echo -e "✅ Command router restarted"
    sleep 2
else
    echo -e "${YELLOW}⚠️  Command router not running in PM2${NC}"
fi

# Step 3: Restart webapp
echo -e "\n${BLUE}🔄 Step 3: Restarting webapp${NC}"

if pm2 list | grep -q "webapp"; then
    pm2 restart webapp
    echo -e "✅ Webapp restarted"
    sleep 2
else
    echo -e "${YELLOW}⚠️  Webapp not running in PM2${NC}"
fi

# Step 4: Verify rollback
echo -e "\n${BLUE}🔍 Step 4: Verifying rollback${NC}"

# Check environment
NEW_SOURCE=${SOURCE:-ea}
if [[ "$NEW_SOURCE" == "ea" ]]; then
    echo -e "✅ Runtime SOURCE confirmed: ${GREEN}ea${NC}"
else
    echo -e "❌ Runtime SOURCE still: ${RED}$NEW_SOURCE${NC}"
fi

# Check .env file
if grep -q "^SOURCE=ea" /root/HydraX-v2/.env 2>/dev/null; then
    echo -e "✅ .env file SOURCE confirmed: ${GREEN}ea${NC}"
else
    echo -e "❌ .env file SOURCE not set to ea"
fi

# Check health endpoint (if webapp is running)
sleep 3  # Give webapp time to start

if curl -s http://localhost:8888/healthz | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'metasocket' not in data:
        print('✅ Health endpoint clean - no MetaSocket metrics')
    else:
        print('⚠️  Health endpoint still shows MetaSocket metrics (may take time to clear)')
except Exception as e:
    print('⚠️  Could not check health endpoint')
" 2>/dev/null; then
    echo -e "✅ Health endpoint checked"
else
    echo -e "${YELLOW}⚠️  Health endpoint check skipped${NC}"
fi

# Step 5: Verification summary
echo -e "\n${BLUE}📊 ROLLBACK VERIFICATION${NC}"
echo "============================================================"

ROLLBACK_SUCCESS=true

if [[ "$NEW_SOURCE" != "ea" ]]; then
    echo -e "❌ Runtime SOURCE not reverted"
    ROLLBACK_SUCCESS=false
fi

if ! grep -q "^SOURCE=ea" /root/HydraX-v2/.env 2>/dev/null; then
    echo -e "❌ .env file SOURCE not reverted"
    ROLLBACK_SUCCESS=false
fi

if $ROLLBACK_SUCCESS; then
    echo -e "${GREEN}🎉 ROLLBACK SUCCESSFUL${NC}"
    echo -e "${GREEN}✅ System reverted to EA source${NC}"
    echo -e "${GREEN}✅ All configurations updated${NC}"
    echo -e "${GREEN}✅ Services restarted${NC}"

    echo -e "\n${BLUE}📋 POST-ROLLBACK CHECKLIST:${NC}"
    echo -e "   1. Monitor PM2 logs for any issues"
    echo -e "   2. Verify fire commands work normally"
    echo -e "   3. Check EA connectivity"
    echo -e "   4. Confirm no MetaSocket references in logs"

    exit 0
else
    echo -e "${RED}❌ ROLLBACK INCOMPLETE${NC}"
    echo -e "${YELLOW}Manual intervention may be required${NC}"
    exit 1
fi
