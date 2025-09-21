# BITTEN Integration API Contracts

## Overview

This document defines the API contracts for integrating the BITTEN UI with backend services. All integrations use event-driven architecture with WebSocket feeds and REST endpoints.

## 1. Mission Snapshot (MT5 Renderer) — API Contract

### Request
```http
POST /render-mission
Content-Type: application/json

{
  "mission_id": "msn_20250920_1432",
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "entry": 2415.30,
  "sl": 2409.30,
  "tp": 2423.60,
  "pattern": "DIRECTION_BANDS",
  "tags": ["SNIPER","NY","Conf:75"],
  "template": "v207h_bands",
  "deadline_ms": 5000
}
```

### Response
```json
{
  "mission_id": "msn_20250920_1432",
  "status": "ok",
  "image_url": "https://cdn.bitten/missions/msn_20250920_1432.png",
  "sha256": "f9c7…b2a",
  "rendered_at": "2025-09-20T14:32:58Z",
  "renderer_id": "camera-04"
}
```

### Notes
- One snapshot per mission (mission-level, not per user)
- CDN URLs should be signed/expiring
- Watermark + short-hash embedded

## 2. Mission Feed (Server → Client) — WebSocket Events

### Connection
```javascript
wss://api.bitten/missions/stream
```

### Events

#### Mission Created
```json
{
  "type": "mission.created",
  "data": {
    "id": "msn_20250920_1432",
    "symbol": "XAUUSD",
    "timeframe": "M15",
    "entry": 2415.30,
    "sl": 2409.30,
    "tp": 2423.60,
    "pattern": "DIRECTION_BANDS",
    "confidence": 75,
    "snapshot_url": "https://cdn.../msn.png",
    "status": "NEW"
  }
}
```

#### Mission Updated
```json
{
  "type": "mission.updated",
  "data": {
    "id": "msn_20250920_1432",
    "status": "ACCEPTED"
  }
}
```

#### Mission Snapshot
```json
{
  "type": "mission.snapshot",
  "data": {
    "id": "msn_20250920_1432",
    "snapshot_url": "https://cdn.../msn.png",
    "sha256": "..."
  }
}
```

## 3. Price Stream (Server → Client) — WebSocket

### Connection
```javascript
wss://api.bitten/price?symbol=XAUUSD
```

### Message Format
```json
{
  "t": 1726839485123,
  "bid": 2415.22,
  "ask": 2415.34
}
```

Client computes mid/PL and updates live lines. Payload kept minimal for performance.

## 4. Execution Endpoints (Client → Bridge)

### Execute Order
```http
POST /orders/execute
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": "u_7176191872",
  "mission_id": "msn_20250920_1432",
  "symbol": "XAUUSD",
  "entry": 2415.30,
  "sl": 2409.30,
  "tp": 2423.60,
  "mode": "MARKET"
}
```

### Response
```json
{
  "status": "ok",
  "ticket": "84231197",
  "filled": 2415.28,
  "sl": 2409.30,
  "tp": 2423.60,
  "broker": "Coinexx-Demo",
  "at": "2025-09-20T14:35:10Z",
  "sig": "HMAC..."
}
```

### Close Order
```http
POST /orders/close
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": "u_7176191872",
  "ticket": "84231197"
}
```

### Response
```json
{
  "status": "ok",
  "ticket": "84231197",
  "closed": 2417.90,
  "pl": 26.2,
  "at": "2025-09-20T14:41:02Z",
  "sig": "HMAC..."
}
```

## 5. Receipts & Telemetry (Server → Client) — WebSocket

### Order Executed
```json
{
  "type": "order.executed",
  "data": {
    "ticket": "84231197",
    "mission_id": "msn_20250920_1432",
    "filled": 2415.28
  }
}
```

### Order Closed
```json
{
  "type": "order.closed",
  "data": {
    "ticket": "84231197",
    "pl": 26.2,
    "xp": 10
  }
}
```

### Client Actions
- Snap Entry/SL/TP lines to filled/sl/tp from receipt
- Push XP event to dashboard on order.closed

## 6. Pattern Templates

### Request
```http
GET /patterns
```

### Response
```json
[
  {
    "id": "DIRECTION_BANDS",
    "label": "Direction Bands",
    "template": "v207h_bands",
    "accent": "#00e0a4"
  },
  {
    "id": "ORDER_BLOCK",
    "label": "Order Block",
    "template": "v207h_ob",
    "accent": "#7df9ff"
  }
]
```

## 7. UI Integration Points

### War Room
- Subscribe to `mission.created/updated/snapshot`
- Display missions in queue
- Update status in real-time

### Mission Brief
- If `status !== LIVE`: show `snapshot_url` image
- On Execute success: set status `LIVE` and render live chart with price stream
- On `order.executed`: snap lines to true filled/sl/tp
- On `order.closed`: show toast, add XP, link to `/xp`

## 8. Security & Trust

### Authentication
- All client-server calls include user token in Authorization header
- All receipts return HMAC signature
- Client displays short hash for verification

### Snapshot URLs
- Signed URLs that expire quickly
- Only accessible from within the app

### Resilience
- Never block UI on snapshot rendering
- Missions render immediately, attach image when ready
- WebSocket reconnection with exponential backoff
- Message queuing when offline

## 9. QA Checklist (15 minutes)

- [ ] Create → Snapshot arrives within SLA (<5s P95)
- [ ] Accept → Execute → LIVE swap is instant
- [ ] Lines reflect actual fill prices from receipts
- [ ] Close → XP increments, event visible on /xp
- [ ] Network drop test: price WS reconnects, UI uses last price
- [ ] Mobile: buttons reachable, chart tap targets adequate
- [ ] Snapshot URLs expire after expected timeout
- [ ] HMAC signatures validate on receipts

## 10. Error Handling

### Connection Failures
- Automatic reconnection with exponential backoff
- Queue messages for retry when reconnected
- Show connection status indicator in UI

### API Errors
- Display user-friendly error messages
- Log detailed errors for debugging
- Fallback to cached data where appropriate

### Timeout Handling
- 10-second default timeout for API calls
- 5-second deadline for snapshot rendering
- Show loading states with timeout warnings