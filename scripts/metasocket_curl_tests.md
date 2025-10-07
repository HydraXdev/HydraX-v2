# MetaSocket Direct cURL Tests

These are one-liner commands you can run directly to test MetaSocket without the adapter layer.

## 🔫 Fire a Trade (ORDER_SEND)

```bash
echo '{"cmd":"ORDER_SEND","symbol":"XAUUSD","type":"buy","volume":0.10,"sl":1932.00,"tp":1939.00,"comment":"MSKT","magic":900001,"idempotency_key":"test-'$(date +%s)'"}' | nc -w 5 127.0.0.1 8777
```

**Expected Response:**
```json
{"status":"ok","ticket":1234567,"price":1935.20}
```

## 💰 Get Account Status (ACCOUNT_STATUS)

```bash
echo '{"cmd":"ACCOUNT_STATUS"}' | nc -w 5 127.0.0.1 8777
```

**Expected Response:**
```json
{
  "cmd":"ACCOUNT_STATUS",
  "balance":10000.00,
  "equity":10025.40,
  "margin":120.00,
  "free_margin":9905.40,
  "leverage":500,
  "timestamp":1700000012000
}
```

## 📋 List Open Positions (POSITION_LIST)

```bash
echo '{"cmd":"POSITION_LIST"}' | nc -w 5 127.0.0.1 8777
```

**Expected Response:**
```json
{
  "positions": [
    {
      "ticket": 1234567,
      "symbol": "XAUUSD",
      "type": "buy",
      "volume": 0.10,
      "price": 1935.20,
      "sl": 1932.00,
      "tp": 1939.00,
      "profit": 25.40,
      "comment": "MSKT",
      "magic": 900001
    }
  ]
}
```

## 🧹 Close Position (ORDER_CLOSE)

```bash
echo '{"cmd":"ORDER_CLOSE","ticket":1234567,"comment":"MANUAL_CLOSE"}' | nc -w 5 127.0.0.1 8777
```

**Expected Response:**
```json
{"status":"ok","ticket":1234567,"close_price":1937.10,"profit":19.00}
```

## 📡 Listen to Event Stream

```bash
# Listen for 10 seconds to see live events
timeout 10 nc 127.0.0.1 8778
```

**Expected Events:**
```json
{"event":"ORDER_OPENED","ticket":1234567,"symbol":"XAUUSD","type":"buy","price":1935.20,"volume":0.10,"timestamp":1700000000000}
{"event":"ORDER_CLOSED","ticket":1234567,"reason":"manual","price":1937.10,"timestamp":1700000010000}
{"event":"ACCOUNT_UPDATE","balance":10000.00,"equity":10019.00,"timestamp":1700000011000}
```

## 🎯 Quick Health Check

Test if MetaSocket is responding:

```bash
echo '{"cmd":"PING"}' | nc -w 2 127.0.0.1 8777
```

**Expected Response:**
```json
{"status":"ok","message":"pong","timestamp":1700000000000}
```

## 📊 Verify Adapter Bus Messages

After running direct tests, check what your adapter published to the event bus:

```bash
# Check Redis for position events
redis-cli LRANGE bitten:events:positions -5 -1

# Check Redis for account updates
redis-cli LRANGE bitten:events:account -5 -1

# Check ZMQ messages (if using ZMQ bridge)
pm2 logs signals_zmq_to_redis --lines 10
```

## 🔄 Integration Test Flow

1. **Fire Trade**: `ORDER_SEND` → expect `ORDER_OPENED` event
2. **Check Position**: `POSITION_LIST` → verify position exists
3. **Get Account**: `ACCOUNT_STATUS` → verify margin usage
4. **Close Trade**: `ORDER_CLOSE` → expect `ORDER_CLOSED` event
5. **Verify Account**: `ACCOUNT_STATUS` → verify balance updated

This validates the complete fire → fill → close → account update cycle through MetaSocket.