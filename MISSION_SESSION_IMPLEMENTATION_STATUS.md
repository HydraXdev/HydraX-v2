# Mission Session Implementation Status

**Date**: October 5, 2025
**Status**: ✅ Foundation Complete - Ready for Integration

---

## ✅ Completed Components

### 1. Database Schema (✅ Applied)
**File**: `/root/HydraX-v2/migrations/002_mission_sessions.sql`
**Status**: ✅ Applied to production database

**Tables Created**:
- `mission_sessions` - Core session management
- `idempotency_cache` - Duplicate request prevention
- `api_tokens` - JWT key management

**Indexes Created**:
- User lookups
- Status filtering
- Expiration queries
- Nonce validation

### 2. JWT Token System (✅ Complete)
**File**: `/root/HydraX-v2/src/security/jwt_manager.py`
**Keys**: `/root/HydraX-v2/keys/jwt_private.pem` & `jwt_public.pem`

**Features**:
- RS256 signing with key rotation support
- Token generation with mission session claims
- Validation with expiry and signature checks
- Scope management
- Nonce extraction

**Usage**:
```python
from src.security.jwt_manager import get_jwt_manager

jwt_mgr = get_jwt_manager()
token = jwt_mgr.generate_mission_token(
    user_id="user_123",
    mission_session_id="ms_abc",
    alert_id=999,
    scopes=["mission:view", "order:execute"],
    pair="EURUSD",
    risk_max_usd=150.0
)

claims = jwt_mgr.validate_token(token)
```

### 3. Mission Session Manager (✅ Complete)
**File**: `/root/HydraX-v2/src/mission_session/session_manager.py`

**Features**:
- Session creation with ULID IDs
- Status lifecycle (PENDING → EXECUTED/EXPIRED)
- Nonce validation
- Expiration management

**Usage**:
```python
from src.mission_session.session_manager import get_session_manager

session_mgr = get_session_manager()

# Create session
session = session_mgr.create_session(
    user_id="user_123",
    signal_id="signal_abc",
    alert_id=999,
    pair="EURUSD",
    ttl_seconds=600
)

# Validate before execute
validation = session_mgr.validate_session(
    mission_session_id="ms_abc",
    expected_nonce="nonce_from_token"
)

if validation['valid']:
    # Execute trade
    session_mgr.mark_executed("ms_abc")
```

### 4. Idempotency Manager (✅ Complete)
**File**: `/root/HydraX-v2/src/idempotency/idempotency_manager.py`

**Features**:
- Duplicate request detection
- Response caching (10 min TTL)
- Automatic cleanup of expired entries

**Usage**:
```python
from src.idempotency.idempotency_manager import get_idempotency_manager

idem_mgr = get_idempotency_manager()

# Check for duplicate
duplicate = idem_mgr.check_duplicate(
    user_id="user_123",
    mission_session_id="ms_abc",
    client_request_id="crid_xyz"
)

if duplicate:
    return duplicate['cached_response']  # Return same response

# Cache new response
idem_mgr.cache_response(
    user_id="user_123",
    mission_session_id="ms_abc",
    client_request_id="crid_xyz",
    op_id="op_789",
    response={'success': True, 'opId': 'op_789'}
)
```

### 5. WebSocket Authentication (✅ Complete)
**File**: `/root/HydraX-v2/src/websocket/auth_middleware.py`

**Features**:
- JWT-based connection authentication
- Session management
- Topic authorization
- Scope validation
- Decorators for protected handlers

**Usage**:
```python
from src.websocket.auth_middleware import get_ws_auth, require_ws_auth

ws_auth = get_ws_auth()

# Authenticate connection
result = ws_auth.authenticate_connection(sid, token)

# Check authorization
if ws_auth.authorize_topic(sid, 'mission.alert/123'):
    # Subscribe to topic
    pass

# Use decorators
@socketio.on('execute_order')
@require_ws_auth
def handle_execute(data):
    user_id = ws_auth.get_user_id(request.sid)
    # Process order
```

### 6. Deep Link Generator (✅ Complete)
**File**: `/root/HydraX-v2/src/telegram/deep_link_generator.py`

**Features**:
- Mission session creation
- JWT token generation
- Deep link formatting
- Short link support (legacy)

**Usage**:
```python
from src.telegram.deep_link_generator import get_link_generator

link_gen = get_link_generator()

link_data = link_gen.generate_mission_link(
    signal_id="signal_abc",
    user_id="user_123",
    alert_id=999,
    pair="EURUSD",
    risk_max_usd=150.0
)

# link_data contains:
# - deep_link: https://www.joinbitten.com/mission?ms=...&token=...
# - mission_session_id
# - token
# - expires_at
```

### 7. Trade Event Emitter (✅ Complete)
**File**: `/root/HydraX-v2/src/events/trade_event_emitter.py`

**Features**:
- User-scoped event emission
- Trade lifecycle events (arming, filled, closed)
- Operation confirmations
- Position updates

**Usage**:
```python
from src.events.trade_event_emitter import get_event_emitter

emitter = get_event_emitter()
emitter.set_socketio(socketio)  # Configure Socket.IO instance

# Emit arming event
emitter.emit_trade_arming(
    user_id="user_123",
    op_id="op_789",
    pair="EURUSD",
    direction="BUY",
    entry=1.05234,
    sl=1.05134,
    tp=1.05382,
    lot=0.10
)

# Emit confirmation
emitter.emit_operation_confirmation(
    user_id="user_123",
    op_id="op_789",
    status="FILLED",
    ticket=123456,
    filled_price=1.05236
)
```

---

## 🔧 Integration Steps (Next Phase)

### Step 1: WebApp Integration

**File to Modify**: `/root/HydraX-v2/webapp_server_optimized.py`

**Changes Needed**:

#### A. Add Imports (top of file)
```python
# Mission Session Architecture
from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager
from src.idempotency.idempotency_manager import get_idempotency_manager
from src.websocket.auth_middleware import get_ws_auth, require_ws_auth
from src.telegram.deep_link_generator import get_link_generator
from src.events.trade_event_emitter import get_event_emitter

# Initialize managers
jwt_manager = get_jwt_manager()
session_manager = get_session_manager()
idempotency_manager = get_idempotency_manager()
ws_auth = get_ws_auth()
link_generator = get_link_generator()
event_emitter = get_event_emitter()
```

#### B. Configure Event Emitter (after socketio initialization)
```python
# After: socketio = SocketIO(app, ...)
event_emitter.set_socketio(socketio)
```

#### C. Update WebSocket Connection Handler
```python
@socketio.on('connect')
def handle_connect():
    """Handle client connections with authentication"""
    # Extract token from query params
    token = request.args.get('t') or request.args.get('token')

    if not token:
        logger.warning(f"⚠️ WebSocket connection without token from {request.sid}")
        disconnect()
        return

    # Authenticate
    result = ws_auth.authenticate_connection(request.sid, token)

    if not result['authenticated']:
        logger.warning(f"⚠️ WebSocket authentication failed: {result.get('error')}")
        disconnect()
        return

    # Join user room
    user_id = result['user_id']
    join_room(f"user_{user_id}")

    logger.info(f"✅ WebSocket connected and authenticated: {request.sid} (user: {user_id})")

    # Send connection confirmation
    emit('authenticated', {
        'success': True,
        'user_id': user_id,
        'scopes': result['scopes']
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up on disconnect"""
    ws_auth.disconnect_session(request.sid)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
@require_ws_auth
def handle_subscribe(data):
    """Handle topic subscriptions"""
    topics = data.get('topics', [])

    for topic in topics:
        if ws_auth.authorize_topic(request.sid, topic):
            join_room(topic)
            emit('subscribed', {'topic': topic})
        else:
            emit('subscription_denied', {'topic': topic, 'reason': 'Unauthorized'})
```

#### D. Update /api/signals Endpoint (Signal Generation)
```python
@app.route('/api/signals', methods=['POST'])
def api_signals_post():
    """Receive signal and create mission session"""
    try:
        signal_data = request.get_json()
        signal_id = signal_data.get('signal_id')
        user_id = request.headers.get('X-User-ID') or '7176191872'  # Default for testing

        # Create mission session + deep link for each user who should see this signal
        # (In production, iterate over users who should receive this alert based on tier/filters)

        link_data = link_generator.generate_mission_link(
            signal_id=signal_id,
            user_id=user_id,
            alert_id=signal_data.get('id', 0),
            pair=signal_data.get('symbol'),
            timeframe=signal_data.get('timeframe'),
            risk_max_usd=150.0  # Calculate based on user's settings
        )

        # Store signal in database (existing logic)
        # ... your existing signal storage code ...

        # Return deep link for Telegram bot
        return jsonify({
            'success': True,
            'signal_id': signal_id,
            'deep_link': link_data['deep_link'],
            'mission_session_id': link_data['mission_session_id'],
            'expires_at': link_data['expires_at']
        })

    except Exception as e:
        logger.error(f"Error processing signal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### E. Update /api/fire Endpoint (Execute with Validation)
```python
@app.route('/api/fire', methods=['POST'])
def fire_mission():
    """Idempotent fire API with mission session validation"""
    try:
        # Extract JWT token
        auth_header = request.headers.get('Authorization')
        token_str = jwt_manager.extract_token_from_header(auth_header)

        if not token_str:
            return jsonify({'error': 'Missing authorization token', 'success': False}), 401

        # Validate token
        try:
            claims = jwt_manager.validate_token(token_str)
        except Exception as e:
            return jsonify({'error': f'Invalid token: {str(e)}', 'success': False}), 401

        # Extract request data
        data = request.get_json()
        client_request_id = data.get('clientRequestId')
        mission_session_id = data.get('missionSessionId')
        alert_id = data.get('alertId')
        risk_usd = data.get('riskUsd')

        # Validate required fields
        if not client_request_id:
            return jsonify({'error': 'Missing clientRequestId', 'success': False}), 400
        if not mission_session_id:
            return jsonify({'error': 'Missing missionSessionId', 'success': False}), 400

        # Verify mission session ID matches token
        if claims['ms'] != mission_session_id:
            return jsonify({'error': 'Mission session mismatch', 'success': False}), 403

        # Check idempotency
        user_id = claims['sub']
        duplicate = idempotency_manager.check_duplicate(user_id, mission_session_id, client_request_id)

        if duplicate:
            logger.info(f"⚠️ Duplicate request detected: {client_request_id}")
            return jsonify(duplicate['cached_response']), 202  # Return cached response

        # Validate mission session
        nonce = jwt_manager.get_nonce(claims)
        validation = session_manager.validate_session(mission_session_id, nonce)

        if not validation['valid']:
            error_code = validation.get('error_code', 'VALIDATION_FAILED')
            if error_code == 'SESSION_EXPIRED':
                return jsonify({'error': validation['error'], 'success': False}), 410  # Gone
            elif error_code == 'SESSION_ALREADY_PROCESSED':
                return jsonify({'error': validation['error'], 'success': False}), 409  # Conflict
            else:
                return jsonify({'error': validation['error'], 'success': False}), 422

        # Validate risk guardrails
        risk_max_usd = claims.get('riskMaxUsd')
        if risk_max_usd and risk_usd > risk_max_usd:
            return jsonify({
                'error': f'Risk exceeds maximum ({risk_max_usd} USD)',
                'success': False
            }), 422

        # Check scopes
        if not jwt_manager.has_scope(claims, 'order:execute'):
            return jsonify({'error': 'Insufficient permissions', 'success': False}), 403

        # Generate operation ID
        op_id = f"op_{ULID()}"

        # Emit arming event
        event_emitter.emit_trade_arming(
            user_id=user_id,
            op_id=op_id,
            pair=data.get('pair', claims.get('pair')),
            direction=data.get('direction', 'BUY'),
            entry=data.get('entry', 0),
            sl=data.get('stopLoss', 0),
            tp=data.get('takeProfit', 0),
            lot=data.get('lot', 0.01)
        )

        # *** YOUR EXISTING FIRE LOGIC HERE ***
        # Enqueue to MT5 bridge, create fire record, etc.
        # ... (keep your existing fire execution code)

        # Mark session as executed
        session_manager.mark_executed(mission_session_id)

        # Build response
        response = {
            'success': True,
            'opId': op_id,
            'status': 'ACCEPTED'
        }

        # Cache response for idempotency
        idempotency_manager.cache_response(user_id, mission_session_id, client_request_id, op_id, response)

        return jsonify(response), 202

    except Exception as e:
        logger.error(f"Error in fire_mission: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
```

#### F. Update Confirmation Listener Integration

**File to Modify**: `/root/HydraX-v2/confirm_listener_v207.py`

**Add after confirmation received**:
```python
# After processing confirmation from EA
event_emitter.emit_operation_confirmation(
    user_id=user_id,
    op_id=op_id,
    status="FILLED" if success else "REJECTED",
    ticket=ticket if success else None,
    filled_price=fill_price if success else None,
    reason=reason if not success else None
)

# If filled, emit trade delta
if success:
    event_emitter.emit_trade_filled(
        user_id=user_id,
        fire_id=fire_id,
        ticket=ticket,
        pair=pair,
        direction=direction,
        entry=entry_price,
        filled_price=fill_price,
        sl=sl,
        tp=tp,
        lot=lot_size
    )
```

---

### Step 2: Telegram Bot Integration

**File to Modify**: `/root/HydraX-v2/bitten_production_bot.py`

**Changes Needed**:

#### A. Add Deep Link Import
```python
from src.telegram.deep_link_generator import get_link_generator

link_generator = get_link_generator()
```

#### B. Modify Alert Posting Function
```python
def post_signal_alert(signal_data):
    """Post signal alert with deep link"""
    try:
        # Generate deep link for each user
        user_id = signal_data.get('user_id', '7176191872')

        link_data = link_generator.generate_mission_link(
            signal_id=signal_data['signal_id'],
            user_id=user_id,
            alert_id=signal_data.get('id', 0),
            pair=signal_data.get('symbol'),
            timeframe=signal_data.get('timeframe'),
            risk_max_usd=150.0  # From user settings
        )

        # Format alert message
        alert_text = f"""
🎯 {signal_data['pattern']} Signal

Pair: {signal_data['symbol']}
Direction: {signal_data['direction']}
Confidence: {signal_data['confidence']}%

Session expires in 10 minutes
        """

        # Create inline button with deep link
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(
            text="📋 View Mission Brief",
            url=link_data['deep_link']
        )
        markup.add(button)

        # Send to Telegram group
        bot.send_message(
            chat_id=TELEGRAM_GROUP_ID,
            text=alert_text,
            reply_markup=markup
        )

        logger.info(f"✅ Posted alert with deep link for {signal_data['signal_id']}")

    except Exception as e:
        logger.error(f"❌ Error posting alert: {e}")
```

---

### Step 3: Mission Brief UI Update

**File to Modify**: `/root/HydraX-v2/bitten-ui/src/app/mission/page.tsx`

**Changes Needed**: (Next.js/React implementation)

```typescript
// Extract token and mission session from URL
const searchParams = useSearchParams();
const token = searchParams.get('token');
const msId = searchParams.get('ms');

// WebSocket connection with auth
useEffect(() => {
  if (!token) {
    // Show session expired message
    return;
  }

  // Connect to WebSocket with token
  const socket = io(`wss://www.joinbitten.com/socket.io?t=${token}`);

  socket.on('authenticated', (data) => {
    console.log('✅ Authenticated', data);

    // Subscribe to topics
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

  socket.on('mission.alert', (data) => {
    // Update mission dossier with alert data
    setMissionData(data);
  });

  socket.on('trades.delta', (data) => {
    if (data.status === 'FILLED') {
      // Redirect to status page
      router.push('/status');
    } else if (data.status === 'ARMING') {
      // Show arming status
      setOrderStatus('arming');
    }
  });

  return () => socket.disconnect();
}, [token, msId]);

// Execute order with idempotency
async function executeOrder() {
  const clientRequestId = crypto.randomUUID();

  try {
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
        entry: missionData.entry,
        stopLoss: missionData.sl,
        takeProfit: missionData.tp,
        riskUsd: calculatedRisk
      })
    });

    if (response.status === 202) {
      // Wait for WebSocket events
      setOrderStatus('pending');
    } else if (response.status === 409) {
      alert('Order already executed');
    } else if (response.status === 410) {
      alert('Session expired');
    } else {
      const error = await response.json();
      alert(`Error: ${error.error}`);
    }
  } catch (error) {
    console.error('Execute error:', error);
  }
}
```

---

## 🧪 Testing Checklist

### Unit Tests
- [  ] JWT token generation/validation
- [  ] Mission session lifecycle
- [  ] Idempotency cache
- [  ] WebSocket authentication
- [  ] Topic authorization

### Integration Tests
- [  ] End-to-end flow (signal → deep link → execute → confirm)
- [  ] WebSocket event delivery
- [  ] Duplicate request prevention
- [  ] Session expiration handling

### Security Tests
- [  ] Token expiry enforcement
- [  ] Replay attack prevention (nonce)
- [  ] Risk guardrail validation
- [  ] Cross-user isolation

---

## 📊 Deployment Checklist

### Pre-Deployment
- [✅] Database migration applied
- [✅] JWT keys generated
- [  ] Environment variables configured
- [  ] Code integrated into webapp
- [  ] Telegram bot updated
- [  ] UI updated

### Deployment
- [  ] Restart webapp with new code
- [  ] Restart Telegram bot
- [  ] Deploy UI changes
- [  ] Monitor logs for errors

### Post-Deployment
- [  ] Test with single user
- [  ] Verify deep links working
- [  ] Check WebSocket connections
- [  ] Monitor idempotency cache
- [  ] Verify event emissions

---

## 🎯 Next Steps

**Immediate** (Required for operation):
1. Integrate WebSocket handlers into webapp_server_optimized.py
2. Update /api/fire endpoint with session validation
3. Modify Telegram bot alert posting
4. Update Mission Brief UI component

**Secondary** (Enhancements):
1. Add session expiration cleanup daemon
2. Add idempotency cache cleanup daemon
3. Add monitoring dashboards for session stats
4. Add admin endpoints for session management

**Documentation**:
1. Update API documentation with new endpoints
2. Document WebSocket event schema
3. Create developer guide for deep link generation
4. Add troubleshooting guide

---

**All foundation components are complete and ready for integration! Follow the integration steps above to activate the secure mission session flow.**
