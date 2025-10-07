# BITTEN UI - Backend Integration Guide

**For Backend & DevOps Teams**
**Date:** October 5, 2025
**Status:** Production Ready

---

## 🎯 Quick Start

The BITTEN UI needs **3 things** from the backend:

1. **Event Bus** (WebSocket) - Real-time data stream
2. **POST /api/fire** - Execute trade endpoint
3. **POST /api/trades/close-all** - Close all positions endpoint

---

## 1. Event Bus Gateway

### Connection

**Endpoint:** `/socket.io` or custom WebSocket path
**Protocol:** WebSocket (preferred) or Server-Sent Events
**Auth:** JWT token via query param or cookie

```javascript
// Client connects to:
ws://api.yourdomain.com/socket.io?token=<jwt>

// Or with cookie-based auth:
ws://api.yourdomain.com/socket.io
```

### Message Format

All messages follow this structure:

```json
{
  "topic": "user.profile",
  "data": { ... }
}
```

### Required Topics

#### 1. `user.profile` - User account data

**Frequency:** On connect + on balance change
**Payload:**

```json
{
  "id": "u_123",
  "codename": "ShadowWolf",
  "balance": 10000.0,
  "maxTrades": 6,
  "activeTrades": 3,
  "riskPerTrade": 100.0,
  "potentialReward": 148.0,
  "level": "FANG_III"
}
```

#### 2. `mission.alert` - New trading signal

**Frequency:** When pattern detected
**Payload:**

```json
{
  "pattern": "SWEEP_RETURN",
  "patternId": 1,
  "pair": "EURUSD",
  "timeframe": "5-MIN",
  "session": "NY SESSION",
  "timestamp": "2025-10-05T13:45:23Z",
  "confidence": 87.3,
  "entry": 1.05234,
  "takeProfit": 1.05382,
  "stopLoss": 1.05134,
  "pips": { "tp": 14.8, "sl": 10.0 },
  "riskReward": 1.48,
  "signalId": "ELITE_EURUSD_1728137123",
  "direction": "BUY"
}
```

#### 3. `trades.open` - Snapshot of all open trades

**Frequency:** On connect + on request
**Payload:**

```json
[
  {
    "id": "t_789",
    "pair": "XAUUSD",
    "entry": 2645.3,
    "current": 2658.9,
    "stopLoss": 2620.0,
    "takeProfit": 2680.0,
    "equity": 680.0,
    "lots": 0.2,
    "startTime": "2025-10-05T15:22:00Z",
    "direction": "BUY",
    "history": [0.2, 0.3, 0.25, 0.4, 0.6, 0.55, 0.7]
  }
]
```

#### 4. `trades.delta` - Individual trade update

**Frequency:** Every 1-5s per open trade
**Payload (full or partial):**

```json
{
  "id": "t_789",
  "current": 2660.2,
  "equity": 705.0
}
```

**Note:** Can send only changed fields to reduce bandwidth

#### 5. `system.status` - System health

**Frequency:** Every 15s + on connection events
**Payload:**

```json
{
  "secure": true,
  "latencyMs": 45,
  "hydraNode": "OK"
}
```

**hydraNode values:** `"OK"` | `"WARN"` | `"DOWN"`

### Heartbeat

**Server → Client:** Every 15s

```json
{
  "type": "ping",
  "serverTs": 1728137123456
}
```

**Client → Server:** Response

```json
{
  "type": "pong",
  "clientTs": 1728137123460
}
```

### Backpressure Strategy

- Drop oldest `trades.delta` per trade ID if client is slow
- Never drop lifecycle events (`position_opened`, `position_closed`)
- Buffer size: 256 messages per client

### Reconnection Behavior

- Client uses exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
- Max attempts: 10 before giving up
- Server should accept reconnects with same token

---

## 2. REST API Endpoints

### POST /api/fire - Execute Trade

**Purpose:** Execute a trading signal
**Auth:** Bearer token or session cookie
**Returns:** 202 Accepted (async operation)

**Request:**

```json
{
  "alertId": "ELITE_EURUSD_1728137123",
  "entry": 1.05234,
  "sl": 1.05134,
  "tp": 1.05382,
  "riskUsd": 100.0
}
```

**Success Response (202):**

```json
{
  "opId": "op_abc123",
  "message": "Trade execution initiated",
  "estimatedCompletionMs": 500
}
```

**Error Response (4xx/5xx):**

```json
{
  "error": "Insufficient balance",
  "code": "INSUFFICIENT_FUNDS",
  "details": {
    "required": 100.0,
    "available": 50.0
  }
}
```

**Important:**

- UI expects 202 Accepted, NOT 200 OK
- Actual position confirmation arrives via event bus `trades.delta`
- Do NOT wait for MT5 confirmation before returning

### POST /api/trades/close-all - Close All Positions

**Purpose:** Close all open positions
**Auth:** Bearer token or session cookie
**Returns:** 202 Accepted (async operation)

**Request:**

```json
{
  "reason": "manual"
}
```

**Reason values:** `"manual"` | `"risk"` | `"weekend"`

**Success Response (202):**

```json
{
  "opId": "op_xyz789",
  "message": "Closing 3 positions",
  "estimatedCompletionMs": 2000
}
```

**Important:**

- Each closure streams via event bus as separate `trades.delta`
- UI removes trades from list when `equity` becomes final

---

## 3. CORS Configuration

```nginx
# Allow UI origin
Access-Control-Allow-Origin: https://ui.yourdomain.com
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

---

## 4. Error Codes

| Code                 | HTTP | Meaning               | UI Behavior                   |
| -------------------- | ---- | --------------------- | ----------------------------- |
| `INSUFFICIENT_FUNDS` | 402  | Not enough balance    | Show upgrade prompt           |
| `MAX_POSITIONS`      | 429  | Slot capacity reached | Show "Close a position first" |
| `SIGNAL_EXPIRED`     | 410  | Signal too old        | Remove from UI                |
| `INVALID_PARAMS`     | 400  | Bad request data      | Show validation error         |
| `UNAUTHORIZED`       | 401  | Auth failed           | Redirect to login             |
| `INTERNAL_ERROR`     | 500  | Server error          | Show retry button             |

---

## 5. Telemetry (Optional)

UI can send heartbeat metrics for observability:

**POST /api/telemetry/ui-heartbeat** (optional)

```json
{
  "userId": "u_123",
  "fps": 60,
  "memoryMb": 128,
  "latencyMs": 45,
  "timestamp": "2025-10-05T15:30:00Z"
}
```

Fire-and-forget, no response needed.

---

## 6. Integration Checklist

Backend team checklist:

- [ ] WebSocket endpoint ready at `/socket.io`
- [ ] Auth scheme decided (JWT or cookie)
- [ ] All 5 topics emit correct payloads
- [ ] Heartbeat every 15s with `serverTs`
- [ ] Backpressure: drop old deltas, keep lifecycle
- [ ] POST `/api/fire` returns 202 + opId
- [ ] POST `/api/trades/close-all` returns 202 + opId
- [ ] Emit `trades.delta` on position open/close
- [ ] CORS headers configured
- [ ] Error codes match table above

---

## 7. Testing

### WebSocket Test

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://api.yourdomain.com/socket.io

# Should receive system.status within 1s
```

### REST Test

```bash
# Fire endpoint
curl -i -X POST https://api.yourdomain.com/api/fire \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "alertId": "test_123",
    "entry": 1.05234,
    "sl": 1.05134,
    "tp": 1.05382,
    "riskUsd": 100
  }'

# Expected: HTTP 202 with opId

# Close all
curl -i -X POST https://api.yourdomain.com/api/trades/close-all \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{ "reason": "manual" }'

# Expected: HTTP 202 with opId
```

---

## 8. Deployment Sequence

1. **Stage 1:** Turn on event bus in staging
2. **Stage 2:** UI connects with `NEXT_PUBLIC_USE_MOCKS=0`
3. **Stage 3:** Test fire + close-all with 1 test account
4. **Stage 4:** Run event storm (100 deltas/min) for 10 min
5. **Stage 5:** Go live

**Rollback:** Set `NEXT_PUBLIC_USE_MOCKS=1` if issues detected

---

## 9. Performance SLA

| Metric           | Target  | Critical |
| ---------------- | ------- | -------- |
| WS Latency (p95) | < 100ms | < 250ms  |
| Fire API (p95)   | < 500ms | < 1s     |
| Delta frequency  | 1-5s    | 10s max  |
| Reconnect time   | < 5s    | < 15s    |

---

## 10. Contact

**Questions?** Reference this document and:

- UI repo: `/root/HydraX-v2/bitten-ui`
- Event bus adapter: `lib/eventBus/realAdapter.ts`
- API client: `lib/api/fireApi.ts`

**Need help?** Check logs for `[EventBus]` or `[Fire API]` tags.

---

**This guide is your source of truth for BITTEN UI integration.**
