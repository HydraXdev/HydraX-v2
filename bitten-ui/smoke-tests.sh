#!/bin/bash

# BITTEN UI - Smoke Tests
# Quick verification that deployed app is working

set -e

# Configuration
BASE_URL="${1:-http://localhost:3000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 BITTEN UI - Smoke Tests"
echo "  Testing: $BASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    echo ""
    echo "Testing: $name"
    echo "  URL: $url"

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo "  ✅ PASS (HTTP $response)"
        ((PASSED++))
    else
        echo "  ❌ FAIL (HTTP $response, expected $expected_code)"
        ((FAILED++))
    fi
}

# Run tests
echo ""
echo "Running endpoint tests..."

test_endpoint "Homepage" "$BASE_URL/" "200"
test_endpoint "Mission Brief" "$BASE_URL/mission" "200"
test_endpoint "Status Board" "$BASE_URL/status" "200"

# Test WebSocket (if backend is available)
echo ""
echo "Testing WebSocket connection..."
if command -v wscat &> /dev/null; then
    timeout 5 wscat -c "${BASE_URL/http/ws}/socket.io" &> /dev/null && \
        echo "  ✅ WebSocket connectable" || \
        echo "  ⚠️  WebSocket not responding (backend may not be ready)"
else
    echo "  ℹ️  wscat not installed, skipping WebSocket test"
    echo "     Install with: npm install -g wscat"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "  🎉 All tests passed!"
    echo ""
    exit 0
else
    echo "  ⚠️  Some tests failed"
    echo ""
    exit 1
fi
