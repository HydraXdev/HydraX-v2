#!/bin/bash

# Frontend Real-Time Verification Script
# Tests all timers, clocks, and Firebase listeners

echo "======================================"
echo "🧪 FRONTEND REAL-TIME VERIFICATION"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test Firebase connectivity
echo "1️⃣ Testing Firebase Connectivity..."
python3 << 'EOF'
try:
    from firebase_backend import initialize_firebase
    db = initialize_firebase()
    if db:
        print("✅ Firebase Admin SDK connected")
        # Test read access
        users_ref = db.collection('users').limit(1)
        docs = users_ref.stream()
        doc_count = sum(1 for _ in docs)
        print(f"✅ Firebase read access working ({doc_count} docs found)")
    else:
        print("❌ Firebase initialization failed")
except Exception as e:
    print(f"❌ Firebase error: {e}")
EOF

echo ""

# Test frontend build
echo "2️⃣ Checking Frontend Build..."
if [ -d "/root/throne/out" ] || [ -d "/root/throne/firebase_deploy" ]; then
    echo -e "${GREEN}✅ Frontend build directory exists${NC}"

    # Check for critical files
    if [ -f "/root/throne/firebase_deploy/index.html" ] || [ -f "/root/throne/out/index.html" ]; then
        echo -e "${GREEN}✅ index.html found${NC}"
    else
        echo -e "${RED}❌ index.html missing${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Build directory not found - run 'npm run build'${NC}"
fi

echo ""

# Check Firebase hosting config
echo "3️⃣ Checking Firebase Hosting Config..."
if [ -f "/root/throne/firebase.json" ]; then
    echo -e "${GREEN}✅ firebase.json found${NC}"

    # Check public directory setting
    PUBLIC_DIR=$(grep -o '"public"[^,]*' /root/throne/firebase.json | cut -d'"' -f4)
    echo "   Public directory: $PUBLIC_DIR"
else
    echo -e "${RED}❌ firebase.json missing${NC}"
fi

echo ""

# Test timer implementations
echo "4️⃣ Checking Timer Implementations..."

# Check AlertFeed timestamps
if grep -q "setInterval.*formatTimeAgo" /root/throne/src/pages/AlertFeed.tsx; then
    echo -e "${GREEN}✅ AlertFeed timestamps update (10s interval)${NC}"
else
    echo -e "${YELLOW}⚠️  AlertFeed timestamp updates not found${NC}"
fi

# Check MissionCard countdown
if grep -q "useEffect.*countdown\|timeRemaining" /root/throne/src/pages/AlertFeed.tsx; then
    echo -e "${GREEN}✅ Mission countdown timers present${NC}"
else
    echo -e "${YELLOW}⚠️  Mission countdown timers not found${NC}"
fi

# Check modal redirect timeout
if grep -q "setTimeout.*battlefield.*3000" /root/throne/src/components/mission/StrikeAuthorizationModal.tsx; then
    echo -e "${GREEN}✅ Post-execution redirect (3s timeout)${NC}"
else
    echo -e "${YELLOW}⚠️  Post-execution redirect timeout not found${NC}"
fi

echo ""

# Check Firebase listeners
echo "5️⃣ Checking Firebase Real-Time Listeners..."

# AlertFeed signals listener
if grep -q "onSnapshot.*signals" /root/throne/src/pages/AlertFeed.tsx; then
    echo -e "${GREEN}✅ AlertFeed signals listener (onSnapshot)${NC}"
else
    echo -e "${RED}❌ AlertFeed signals listener missing${NC}"
fi

# Battlefield active_trades listener
if grep -q "onSnapshot.*active_trades" /root/throne/src/pages/Battlefield.tsx; then
    echo -e "${GREEN}✅ Battlefield active_trades listener${NC}"
else
    echo -e "${RED}❌ Battlefield active_trades listener missing${NC}"
fi

# CommandCenter user listener
if grep -q "onSnapshot.*users" /root/throne/src/pages/CommandCenter.tsx; then
    echo -e "${GREEN}✅ CommandCenter user listener${NC}"
else
    echo -e "${YELLOW}⚠️  CommandCenter user listener not found${NC}"
fi

# WarChest trade_history listener
if grep -q "onSnapshot.*trade_history" /root/throne/src/pages/WarChest.tsx; then
    echo -e "${GREEN}✅ WarChest trade_history listener${NC}"
else
    echo -e "${RED}❌ WarChest trade_history listener missing${NC}"
fi

echo ""

# Check cleanup handlers
echo "6️⃣ Checking Cleanup Handlers..."

CLEANUP_COUNT=$(grep -r "return () => clearInterval\|return () => unsubscribe" /root/throne/src/pages/ | wc -l)
echo -e "${GREEN}✅ Found ${CLEANUP_COUNT} cleanup handlers${NC}"

if [ "$CLEANUP_COUNT" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Expected more cleanup handlers (potential memory leaks)${NC}"
fi

echo ""

# Check mobile fixes
echo "7️⃣ Checking Mobile Responsive Fixes..."

# Modal width fix
if grep -q "!w-\[calc(100vw" /root/throne/src/components/mission/StrikeAuthorizationModal.tsx; then
    echo -e "${GREEN}✅ Modal mobile width fix applied${NC}"
else
    echo -e "${YELLOW}⚠️  Modal mobile width fix not found${NC}"
fi

# Battlefield button fix
if grep -q "w-full.*RETURN TO SIGNALS" /root/throne/src/pages/Battlefield.tsx; then
    echo -e "${GREEN}✅ Battlefield single button layout${NC}"
else
    echo -e "${YELLOW}⚠️  Battlefield button layout not verified${NC}"
fi

echo ""

# Check redirect fix
echo "8️⃣ Checking Navigation Fixes..."

if grep -q "navigate('/battlefield'.*replace.*true" /root/throne/src/components/mission/StrikeAuthorizationModal.tsx; then
    echo -e "${GREEN}✅ Battlefield redirect after fire (replace: true)${NC}"
else
    echo -e "${YELLOW}⚠️  Battlefield redirect not found${NC}"
fi

echo ""

# Test backend processes
echo "9️⃣ Checking Backend Processes..."

if pm2 list > /dev/null 2>&1; then
    # Check critical processes
    if pm2 list | grep -q "command_router.*online"; then
        echo -e "${GREEN}✅ command_router running${NC}"
    else
        echo -e "${RED}❌ command_router not running${NC}"
    fi

    if pm2 list | grep -q "confirm_listener.*online"; then
        echo -e "${GREEN}✅ confirm_listener running${NC}"
    else
        echo -e "${RED}❌ confirm_listener not running${NC}"
    fi

    if pm2 list | grep -q "webapp.*online"; then
        echo -e "${GREEN}✅ webapp running${NC}"
    else
        echo -e "${YELLOW}⚠️  webapp not in PM2 (may run differently)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  PM2 not available${NC}"
fi

echo ""

# Summary
echo "======================================"
echo "📊 VERIFICATION SUMMARY"
echo "======================================"
echo ""
echo "✅ = Working"
echo "⚠️  = Warning or not critical"
echo "❌ = Issue found"
echo ""
echo "Next Steps:"
echo "1. If build directory missing: cd /root/throne && npm run build"
echo "2. Deploy: firebase deploy --only hosting"
echo "3. Test in browser: https://bitten-0420.web.app"
echo "4. Monitor logs: pm2 logs"
echo ""
echo "Manual Testing Checklist:"
echo "□ Open /signals - new signals appear without refresh"
echo "□ Timestamps update every 10 seconds"
echo "□ Click mission brief - modal opens without cutoff"
echo "□ Execute trade - redirects to /battlefield"
echo "□ Active trade appears - P&L updates live"
echo "□ Trade closes - moves to history without refresh"
echo "□ All counters update (wins, streak, balance)"
echo ""
