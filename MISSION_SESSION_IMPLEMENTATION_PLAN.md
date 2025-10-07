# Mission Session Architecture - Implementation Plan

**Date**: October 5, 2025
**Purpose**: Secure, event-driven architecture for Telegram → Mission Brief → Execute flow
**Goal**: Same UX, better security with JWT tokens, WebSocket events, and replay protection

---

## 🎯 Architecture Overview

### Current Flow (Baseline)
```
Signal Generated → Telegram Alert → Mission Brief → Execute → MT5 EA → DB Confirm
```

### New Flow (Secure & Event-Driven)
```
Signal → MissionSession + JWT → Deep Link Alert → WS Auth → Event Subscriptions → Validated Execute → EA → Event Emissions → UI Updates
```

---

## 📋 Implementation Components

### 1. Database Schema Changes

#### New Table: mission_sessions
```sql
CREATE TABLE mission_sessions (
    mission_session_id TEXT PRIMARY KEY,          -- Format: ms_<ulid>
    user_id TEXT NOT NULL,
    alert_id INTEGER NOT NULL,                    -- References signals.id
    signal_id TEXT NOT NULL,                      -- References signals.signal_id
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING/EXECUTED/EXPIRED
    pair TEXT,
    timeframe TEXT,
    risk_max_usd REAL,
    token_nonce TEXT UNIQUE,                      -- One-time use nonce
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,                  -- 5-10 min TTL
    executed_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id)
);

CREATE INDEX idx_mission_sessions_user ON mission_sessions(user_id);
CREATE INDEX idx_mission_sessions_status ON mission_sessions(status);
CREATE INDEX idx_mission_sessions_expires ON mission_sessions(expires_at);
CREATE INDEX idx_mission_sessions_nonce ON mission_sessions(token_nonce);
```

#### New Table: idempotency_cache
```sql
CREATE TABLE idempotency_cache (
    cache_key TEXT PRIMARY KEY,                   -- {user_id}:{ms_id}:{client_request_id}
    user_id TEXT NOT NULL,
    mission_session_id TEXT NOT NULL,
    client_request_id TEXT NOT NULL,
    op_id TEXT NOT NULL,
    response_json TEXT NOT NULL,                  -- Cached response
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,                  -- 10 min TTL
    UNIQUE(user_id, mission_session_id, client_request_id)
);

CREATE INDEX idx_idempotency_expires ON idempotency_cache(expires_at);
```

#### New Table: api_tokens (for key management)
```sql
CREATE TABLE api_tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    key_id TEXT NOT NULL,                         -- kid for JWT rotation
    public_key TEXT NOT NULL,                     -- For RS256 verification
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    revoked_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

### 2. JWT Token System

#### Token Structure (JWS/JWT)
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-2025-10"
  },
  "payload": {
    "iss": "bitten-backend",
    "aud": "bitten-ui",
    "sub": "user_7176191872",
    "ms": "ms_01J7X5M2C3ABC",
    "aid": 12345,
    "scopes": ["mission:view", "order:execute"],
    "riskMaxUsd": 150,
    "pair": "EURUSD",
    "tf": "M5",
    "exp": 1728123456,
    "iat": 1728123156,
    "nonce": "8f3c1e9c..."
  }
}
```

#### Token Validation Rules
- `aud == "bitten-ui"` and `iss == "bitten-backend"`
- Signature verified by `kid`
- `exp` not expired
- `ms` exists and status == `PENDING`
- Nonce not already spent (one-time use)

#### Implementation Files
- `/root/HydraX-v2/src/security/jwt_manager.py` - Token generation/validation
- `/root/HydraX-v2/src/security/token_middleware.py` - Flask middleware for auth

---

### 3. Mission Session Lifecycle

#### State Machine
```
PENDING → EXECUTED (on successful execute)
PENDING → EXPIRED (on TTL expiration)
```

#### Lifecycle Events
1. **Creation**: When signal generated (in `/api/signals`)
2. **Validation**: On execute (in `/api/fire`)
3. **Execution**: Mark as EXECUTED, spend nonce
4. **Expiration**: Background job expires old sessions

#### Implementation Files
- `/root/HydraX-v2/src/mission_session/session_manager.py` - CRUD operations
- `/root/HydraX-v2/src/mission_session/session_lifecycle.py` - State transitions
- `/root/HydraX-v2/src/mission_session/expiration_daemon.py` - Background cleanup

---

### 4. WebSocket Authentication

#### Connection Auth
```javascript
// Client connects with token
const socket = io('wss://api.bitten.io/ws/ui?t=<JWT>')
```

#### Server-Side Auth Flow
1. Extract JWT from query param `t` or cookie
2. Validate token (same rules as HTTP)
3. Map connection → `user_id` from token claims
4. Authorize topic subscriptions based on user scope

#### Topic Authorization
```python
# User can only subscribe to their own topics
user.profile              # Own profile
mission.alert/{alert_id}  # Own alert (validated against ms)
trades.open               # Own positions
trades.delta             # Own position updates
stats.*                   # Own stats
```

#### Implementation Files
- `/root/HydraX-v2/src/websocket/auth_middleware.py` - WS authentication
- `/root/HydraX-v2/src/websocket/topic_authorizer.py` - Topic-level authorization

---

### 5. Deep Link Generation

#### Telegram Button URL Format
```
https://www.joinbitten.com/mission?ms=<MISSION_SESSION_ID>&token=<JWT>
```

#### Example
```
https://www.joinbitten.com/mission?ms=ms_01J7X5M2C3ABC&token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0yMDI1LTEwIn0...
```

#### Telegram Bot Changes
- Modify alert posting to generate mission session
- Create JWT token with session claims
- Build deep link with ms + token
- Set button URL to deep link

#### Implementation Files
- Update `/root/HydraX-v2/bitten_production_bot.py` - Add deep link generation
- `/root/HydraX-v2/src/telegram/deep_link_generator.py` - Helper functions

---

### 6. Execute Action with Validation

#### HTTP Request Format
```http
POST /api/fire
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "clientRequestId": "crid_2d5b0a1f-uuid",
  "missionSessionId": "ms_01J7X5M2C3ABC",
  "alertId": 12345,
  "entry": 1.05234,
  "stopLoss": 1.05134,
  "takeProfit": 1.05382,
  "riskUsd": 100
}
```

#### Validation Flow
1. Validate JWT (scopes, TTL, signature)
2. Check mission session exists and status == PENDING
3. Check idempotency (clientRequestId)
4. Validate risk guardrails (riskUsd ≤ riskMaxUsd from token)
5. Enqueue to MT5 bridge
6. Mark session as EXECUTED
7. Spend nonce
8. Emit events

#### Response Codes
- `202 Accepted` - { "opId": "op_7qk...", "status": "ACCEPTED" }
- `409 Conflict` - Already executed or duplicate clientRequestId
- `401 Unauthorized` - Token invalid/expired
- `403 Forbidden` - Scopes missing
- `422 Unprocessable` - Risk guardrails violated

#### Implementation Files
- Update `/root/HydraX-v2/webapp_server_optimized.py` - `/api/fire` endpoint
- `/root/HydraX-v2/src/mission_session/execute_validator.py` - Validation logic
- `/root/HydraX-v2/src/idempotency/idempotency_manager.py` - Duplicate prevention

---

### 7. Event Bus Emissions

#### Event Types

**trades.delta** (Position updates)
```json
{
  "type": "trades.delta",
  "id": "temp_op_123",
  "pair": "EURUSD",
  "current": 1.05234,
  "equity": 0,
  "status": "ARMING"
}
```

**ops.confirmation** (EA confirmation)
```json
{
  "type": "ops.confirmation",
  "opId": "op_7qk...",
  "status": "FILLED",
  "filledPrice": 1.05234,
  "ticket": 123456,
  "ts": 1728123456
}
```

#### Emission Points
1. **Pre-position** - Immediately after enqueue (status: ARMING)
2. **EA Confirm** - When confirmation received (status: FILLED/REJECTED)
3. **Position Updates** - Live P&L deltas from EA

#### Implementation Files
- `/root/HydraX-v2/src/events/trade_event_emitter.py` - Event emission logic
- Update `/root/HydraX-v2/confirm_listener_v207.py` - Emit on confirmations

---

### 8. Idempotency System

#### Cache Key Format
```
{user_id}:{mission_session_id}:{client_request_id}
```

#### Duplicate Handling
```python
# First request
cache_key = f"{user_id}:{ms_id}:{client_request_id}"
if cache_key in idempotency_cache:
    return cached_response  # Same 202 response

# New request - execute and cache
response = execute_trade(...)
cache_response(cache_key, response, ttl=600)  # 10 min
return response
```

#### Cleanup
- Background job removes expired entries (expires_at < now())
- TTL: 10 minutes (covers typical user retry window)

#### Implementation Files
- `/root/HydraX-v2/src/idempotency/idempotency_manager.py` - Cache operations
- `/root/HydraX-v2/src/idempotency/cleanup_daemon.py` - Background cleanup

---

### 9. Mission Brief UI Changes

#### Current Behavior (Polling)
- UI polls `/api/signals` every few seconds
- Direct POST to `/api/fire` on execute

#### New Behavior (WebSocket Subscriptions)
```javascript
// On page load
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');
const msId = urlParams.get('ms');

// Connect with auth
const socket = io(`wss://www.joinbitten.com/socket.io?t=${token}`);

// Subscribe to topics
socket.on('connect', () => {
  socket.emit('subscribe', {
    topics: [
      'user.profile',
      `mission.alert/${alertId}`,
      'trades.open',
      'trades.delta',
      'system.status'
    ]
  });
});

// Listen for updates
socket.on('mission.alert', (data) => {
  updateDossier(data);
});

socket.on('trades.delta', (data) => {
  if (data.status === 'FILLED') {
    redirectToStatus();
  }
});

// Execute with idempotency
async function executeOrder() {
  const clientRequestId = generateUUID();

  const response = await fetch('/api/fire', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      clientRequestId,
      missionSessionId: msId,
      alertId,
      entry: signal.entry,
      stopLoss: signal.sl,
      takeProfit: signal.tp,
      riskUsd: calculatedRisk
    })
  });

  if (response.status === 202) {
    // Wait for trades.delta event
    showArmingStatus();
  }
}
```

#### Implementation Files
- Update `/root/HydraX-v2/bitten-ui/src/app/mission/page.tsx` - WebSocket integration
- `/root/HydraX-v2/bitten-ui/src/lib/websocket-client.ts` - WS client helper

---

## 🔐 Security Features

### 1. Token Security
- **Short-lived**: 5-10 min expiration
- **Scoped**: Only `mission:view` and `order:execute`
- **Bound**: Tied to user_id and mission_session_id
- **One-time**: Nonce prevents replay

### 2. Replay Protection
- Mission session status prevents re-execution
- Nonce marked as "spent" after first execute
- Subsequent attempts return 409 Conflict

### 3. Risk Guardrails
- `riskMaxUsd` encoded in token
- Server validates `riskUsd ≤ riskMaxUsd`
- Prevents client-side manipulation

### 4. Topic Authorization
- Users can only subscribe to their own topics
- Alert ID must match mission session
- Cross-user data leakage prevented

---

## 📦 Implementation Phases

### Phase 1: Foundation (Parallel)
- [ ] Create database schema (mission_sessions, idempotency_cache, api_tokens)
- [ ] Implement JWT manager (generation, validation)
- [ ] Implement mission session manager (CRUD, lifecycle)

### Phase 2: Integration (Parallel)
- [ ] Add WebSocket authentication middleware
- [ ] Update `/api/fire` with session validation
- [ ] Implement idempotency system
- [ ] Add event emissions (trades.delta, ops.confirmation)

### Phase 3: Client Updates (Parallel)
- [ ] Modify Telegram bot for deep links
- [ ] Update Mission Brief UI for WebSocket subscriptions
- [ ] Add clientRequestId generation

### Phase 4: Testing & Deployment
- [ ] End-to-end flow testing
- [ ] Security validation (token expiry, replay attacks)
- [ ] Performance testing (WebSocket scalability)
- [ ] Deploy to production

---

## 📊 Success Metrics

### Functional
- ✅ Same user experience (button → brief → execute → status)
- ✅ No duplicate orders (idempotency working)
- ✅ Expired sessions blocked (TTL enforcement)
- ✅ Real-time updates (WebSocket latency < 250ms)

### Security
- ✅ Token expiry enforced (no stale links work)
- ✅ Replay attacks blocked (nonce one-time use)
- ✅ Risk guardrails enforced (server-side validation)
- ✅ Topic isolation (no cross-user data leaks)

### Performance
- ✅ WebSocket connections stable (no disconnects under load)
- ✅ Event delivery < 250ms P95
- ✅ Database queries optimized (indexed lookups)

---

## 🎯 API Contracts

### Mission Session Creation
```python
def create_mission_session(signal_id: str, user_id: str, alert_id: int) -> dict:
    """
    Creates a new mission session with JWT token

    Returns:
        {
            'mission_session_id': 'ms_01J7X5M2C3ABC',
            'token': 'eyJhbGciOiJSUzI1NiIs...',
            'deep_link': 'https://www.joinbitten.com/mission?ms=...&token=...',
            'expires_at': 1728123456
        }
    """
```

### Execute Validation
```python
def validate_execute_request(token: str, request_data: dict) -> dict:
    """
    Validates execute request with all guardrails

    Returns:
        {
            'valid': True,
            'user_id': 'user_123',
            'mission_session': {...},
            'error': None
        }
    """
```

### Event Emission
```python
def emit_trade_delta(user_id: str, position_data: dict):
    """
    Emits position delta to user's WebSocket channel
    """
    socketio.emit('trades.delta', position_data, room=f'user_{user_id}')
```

---

## 🔧 Configuration

### Environment Variables
```bash
# JWT Configuration
JWT_PRIVATE_KEY_PATH=/root/HydraX-v2/keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/root/HydraX-v2/keys/jwt_public.pem
JWT_KEY_ID=key-2025-10
JWT_ALGORITHM=RS256
JWT_ISSUER=bitten-backend
JWT_AUDIENCE=bitten-ui

# Mission Session Configuration
MISSION_SESSION_TTL=600  # 10 minutes
IDEMPOTENCY_TTL=600      # 10 minutes

# WebSocket Configuration
WS_AUTH_ENABLED=true
WS_TOKEN_PARAM=t
```

### Key Generation
```bash
# Generate RSA key pair for JWT signing
openssl genrsa -out /root/HydraX-v2/keys/jwt_private.pem 2048
openssl rsa -in /root/HydraX-v2/keys/jwt_private.pem -pubout -out /root/HydraX-v2/keys/jwt_public.pem
```

---

## 📝 Testing Checklist

### Unit Tests
- [ ] JWT generation and validation
- [ ] Mission session lifecycle transitions
- [ ] Idempotency cache operations
- [ ] Token nonce spending

### Integration Tests
- [ ] End-to-end flow (alert → execute → confirm)
- [ ] WebSocket authentication
- [ ] Topic authorization
- [ ] Event emissions

### Security Tests
- [ ] Token expiry enforcement
- [ ] Replay attack prevention
- [ ] Risk guardrail validation
- [ ] Cross-user isolation

### Performance Tests
- [ ] WebSocket connection scaling (100+ concurrent)
- [ ] Event delivery latency (P95 < 250ms)
- [ ] Database query performance (indexed lookups)

---

## 🚀 Deployment Strategy

### Pre-Deployment
1. Generate JWT key pair
2. Apply database migrations
3. Configure environment variables
4. Deploy new code (webapp + bot)

### Deployment
1. Enable mission session creation (feature flag)
2. Monitor logs for errors
3. Test with single user (Commander Dev 001)
4. Gradually roll out to all users

### Rollback Plan
1. Disable mission session creation (feature flag)
2. Revert to legacy mission flow
3. Investigate issues
4. Fix and re-deploy

---

## 📚 References

- **JWT Spec**: RFC 7519 (JSON Web Tokens)
- **WebSocket Auth**: Socket.IO Authentication Guide
- **Idempotency**: Stripe API Idempotency Best Practices
- **Event Bus**: Redis Pub/Sub Pattern

---

**This plan provides the complete blueprint for implementing the secure mission session architecture while maintaining the exact same user experience.**
