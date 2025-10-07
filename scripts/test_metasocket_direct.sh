#!/bin/bash
# CUTOVER: Direct MetaSocket Testing with cURL
# Tests MetaSocket TCP endpoints directly without adapter layer

echo "🎯 METASOCKET DIRECT TESTING"
echo "============================================================"

# MetaSocket configuration
MSKT_HOST=${MSKT_HOST:-185.244.67.11}
MSKT_CMD_PORT=${MSKT_CMD_PORT:-8777}
MSKT_STREAM_PORT=${MSKT_STREAM_PORT:-8778}

echo "📊 Testing MetaSocket at $MSKT_HOST:$MSKT_CMD_PORT"

# Test 1: ORDER_SEND (Fire a Trade)
echo ""
echo "🔫 TEST 1: ORDER_SEND (Fire XAUUSD Trade)"
echo "------------------------------------------------------------"

ORDER_SEND_PAYLOAD='{
  "cmd": "ORDER_SEND",
  "symbol": "XAUUSD",
  "type": "buy",
  "volume": 0.10,
  "sl": 1932.00,
  "tp": 1939.00,
  "comment": "MSKT",
  "magic": 900001,
  "idempotency_key": "test-'$(date +%s)'-'$(shuf -i 1000-9999 -n 1)'"
}'

echo "📤 Sending ORDER_SEND payload:"
echo "$ORDER_SEND_PAYLOAD" | jq .

echo "📡 Response from MetaSocket:"
echo "$ORDER_SEND_PAYLOAD" | nc -w 5 $MSKT_HOST $MSKT_CMD_PORT | jq . || echo "❌ No response or connection failed"

# Test 2: ACCOUNT_STATUS
echo ""
echo "💰 TEST 2: ACCOUNT_STATUS (Get Account Info)"
echo "------------------------------------------------------------"

ACCOUNT_STATUS_PAYLOAD='{
  "cmd": "ACCOUNT_STATUS"
}'

echo "📤 Sending ACCOUNT_STATUS payload:"
echo "$ACCOUNT_STATUS_PAYLOAD" | jq .

echo "📡 Response from MetaSocket:"
echo "$ACCOUNT_STATUS_PAYLOAD" | nc -w 5 $MSKT_HOST $MSKT_CMD_PORT | jq . || echo "❌ No response or connection failed"

# Test 3: POSITION_LIST
echo ""
echo "📋 TEST 3: POSITION_LIST (Get Open Positions)"
echo "------------------------------------------------------------"

POSITION_LIST_PAYLOAD='{
  "cmd": "POSITION_LIST"
}'

echo "📤 Sending POSITION_LIST payload:"
echo "$POSITION_LIST_PAYLOAD" | jq .

echo "📡 Response from MetaSocket:"
echo "$POSITION_LIST_PAYLOAD" | nc -w 5 $MSKT_HOST $MSKT_CMD_PORT | jq . || echo "❌ No response or connection failed"

# Test 4: Stream Connection Test
echo ""
echo "📡 TEST 4: STREAM CONNECTION (Port $MSKT_STREAM_PORT)"
echo "------------------------------------------------------------"

echo "📤 Testing stream connection (5 second listen):"
echo "Connecting to stream port to listen for events..."

timeout 5 nc $MSKT_HOST $MSKT_STREAM_PORT || echo "❌ Stream connection failed or no events received"

echo ""
echo "============================================================"
echo "🎯 METASOCKET DIRECT TESTING COMPLETE"
echo ""
echo "📋 EXPECTED RESPONSES:"
echo ""
echo "✅ ORDER_SEND Success:"
echo '   {"status":"ok","ticket":1234567,"price":1935.20}'
echo ""
echo "✅ ACCOUNT_STATUS Success:"
echo '   {"cmd":"ACCOUNT_STATUS","balance":10000.00,"equity":10025.40,...}'
echo ""
echo "✅ POSITION_LIST Success:"
echo '   {"positions":[{"ticket":1234567,"symbol":"XAUUSD",...}]}'
echo ""
echo "✅ STREAM Events:"
echo '   {"event":"ORDER_OPENED","ticket":1234567,"symbol":"XAUUSD",...}'
echo '   {"event":"ORDER_CLOSED","ticket":1234567,"reason":"manual",...}'