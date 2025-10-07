# Mission Session Architecture - Quick Start Guide

**Goal**: Get the secure mission session flow operational in production

---

## ✅ What's Already Complete

1. ✅ Database schema applied
2. ✅ JWT keys generated
3. ✅ All foundation modules created
4. ✅ Integration code documented

---

## 🚀 Activation Steps (30 Minutes)

### Step 1: Add Environment Variables (2 min)

Add to `/root/HydraX-v2/.env` or `/root/HydraX-v2/bitten-ui/.env.production`:

```bash
# JWT Configuration
JWT_PRIVATE_KEY_PATH=/root/HydraX-v2/keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/root/HydraX-v2/keys/jwt_public.pem
JWT_KEY_ID=key-2025-10
JWT_ALGORITHM=RS256
JWT_ISSUER=bitten-backend
JWT_AUDIENCE=bitten-ui

# Mission Session Configuration
MISSION_SESSION_TTL=600
IDEMPOTENCY_TTL=600

# UI URL for deep links
BITTEN_UI_URL=https://www.joinbitten.com
```

### Step 2: Test Foundation Components (5 min)

```bash
# Test JWT manager
cd /root/HydraX-v2
python3 src/security/jwt_manager.py

# Test mission session manager
python3 src/mission_session/session_manager.py

# Test idempotency manager
python3 src/idempotency/idempotency_manager.py

# Test deep link generator
python3 src/telegram/deep_link_generator.py

# All should complete without errors
```

### Step 3: Integrate WebSocket Auth (10 min)

**File**: `/root/HydraX-v2/webapp_server_optimized.py`

**Add imports** (after existing imports, around line 40):

```python
# Mission Session Architecture
try:
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

    MISSION_SESSION_ENABLED = True
    logger.info("✅ Mission Session Architecture loaded")
except Exception as e:
    logger.warning(f"⚠️ Mission Session Architecture not available: {e}")
    MISSION_SESSION_ENABLED = False
```

**Configure event emitter** (after `socketio = SocketIO(...)` around line 200):

```python
# Configure event emitter (after socketio initialization)
if MISSION_SESSION_ENABLED:
    event_emitter.set_socketio(socketio)
```

**Update WebSocket connect handler** (replace existing `@socketio.on('connect')` around line 2241):

```python
@socketio.on('connect')
def handle_connect():
    """Handle client connections with optional authentication"""
    logger.info(f"Client connected: {request.sid}")

    # Try to authenticate if token provided
    if MISSION_SESSION_ENABLED:
        token = request.args.get('t') or request.args.get('token')

        if token:
            from flask_socketio import join_room, emit
            result = ws_auth.authenticate_connection(request.sid, token)

            if result['authenticated']:
                # Join user room
                user_id = result['user_id']
                join_room(f"user_{user_id}")
                logger.info(f"✅ Authenticated WS connection for user {user_id}")

                emit('authenticated', {
                    'success': True,
                    'user_id': user_id,
                    'scopes': result['scopes']
                })
                return

    # Fallback: allow unauthenticated (legacy mode)
    socketio.emit('status', {'connected': True, 'server': 'BITTEN-OPTIMIZED'})

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up on disconnect"""
    if MISSION_SESSION_ENABLED:
        ws_auth.disconnect_session(request.sid)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle topic subscriptions with authorization"""
    if not MISSION_SESSION_ENABLED:
        return

    from flask_socketio import join_room, emit

    topics = data.get('topics', [])

    for topic in topics:
        if ws_auth.authorize_topic(request.sid, topic):
            join_room(topic)
            emit('subscribed', {'topic': topic})
            logger.info(f"✅ Subscribed {request.sid} to {topic}")
        else:
            emit('subscription_denied', {'topic': topic, 'reason': 'Unauthorized'})
```

### Step 4: Add Deep Link to Signal API (5 min)

**File**: `/root/HydraX-v2/webapp_server_optimized.py`

**Find `/api/signals` POST handler** (around line 1450-1500) and add:

```python
@app.route('/api/signals', methods=['POST'])
def api_signals_post():
    """Receive signal and create mission session"""
    try:
        signal_data = request.get_json()
        signal_id = signal_data.get('signal_id')

        # Store signal (existing logic)
        # ... your existing code ...

        # Generate deep link if mission session enabled
        deep_link = None
        if MISSION_SESSION_ENABLED:
            try:
                user_id = request.headers.get('X-User-ID', '7176191872')

                link_data = link_generator.generate_mission_link(
                    signal_id=signal_id,
                    user_id=user_id,
                    alert_id=signal_data.get('id', 0),
                    pair=signal_data.get('symbol'),
                    timeframe=signal_data.get('timeframe'),
                    risk_max_usd=150.0
                )

                deep_link = link_data['deep_link']
                logger.info(f"✅ Generated deep link for signal {signal_id}")

            except Exception as e:
                logger.warning(f"⚠️ Could not generate deep link: {e}")

        return jsonify({
            'success': True,
            'signal_id': signal_id,
            'deep_link': deep_link  # Will be None if feature disabled
        })

    except Exception as e:
        logger.error(f"Error in api_signals_post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Step 5: Test the System (5 min)

```bash
# Restart webapp
pm2 restart webapp

# Check logs
pm2 logs webapp --lines 50

# Should see:
# ✅ Mission Session Architecture loaded
# ✅ Loaded JWT private key from ...
# ✅ Loaded JWT public key from ...
```

**Test API**:

```bash
# Test signal creation with deep link
curl -X POST http://localhost:8888/api/signals \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 7176191872" \
  -d '{
    "signal_id": "TEST_SIGNAL_123",
    "symbol": "EURUSD",
    "timeframe": "M5",
    "direction": "BUY",
    "confidence": 85
  }'

# Should return deep_link in response
```

**Test WebSocket Auth**:

```bash
# Generate a test token
python3 -c "
from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager

# Create test session
sm = get_session_manager()
session = sm.create_session(
    user_id='user_test',
    signal_id='test_123',
    alert_id=999,
    pair='EURUSD'
)

# Generate token
jm = get_jwt_manager()
token = jm.generate_mission_token(
    user_id='user_test',
    mission_session_id=session['mission_session_id'],
    alert_id=999,
    scopes=['mission:view', 'order:execute']
)

print(f'Test URL:')
print(f'https://www.joinbitten.com/mission?ms={session[\"mission_session_id\"]}&token={token}')
"
```

### Step 6: Verify Database (2 min)

```bash
# Check mission sessions table
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT mission_session_id, user_id, status, created_at FROM mission_sessions LIMIT 5;"

# Check idempotency cache
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) FROM idempotency_cache;"

# Should see your test sessions
```

---

## 🎯 Phase 2: Full Integration (Later)

Once Step 5 tests pass, you can proceed with:

1. Update `/api/fire` endpoint with full validation (see MISSION_SESSION_IMPLEMENTATION_STATUS.md)
2. Modify Telegram bot to use deep links
3. Update Mission Brief UI for WebSocket subscriptions
4. Add cleanup daemons

---

## 🔍 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Check Python path

```bash
export PYTHONPATH=/root/HydraX-v2:$PYTHONPATH
python3 src/security/jwt_manager.py
```

### Issue: "Key file not found"

**Solution**: Verify keys exist

```bash
ls -la /root/HydraX-v2/keys/
# Should show jwt_private.pem and jwt_public.pem
```

### Issue: WebSocket authentication fails

**Solution**: Check token in browser console

```javascript
const urlParams = new URLSearchParams(window.location.search);
console.log("Token:", urlParams.get("token"));
```

### Issue: Database errors

**Solution**: Verify migration applied

```bash
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT * FROM schema_versions WHERE version = '002_mission_sessions';"
```

---

## 📊 Success Indicators

After completing steps 1-6:

- [ ] Webapp starts without errors
- [ ] Logs show "Mission Session Architecture loaded"
- [ ] `/api/signals` returns deep_link field
- [ ] WebSocket connects with ?t=token parameter
- [ ] Test session created in database
- [ ] Test token validates successfully

---

## 🚀 Next Steps After Quickstart

1. **Enable in Production**: Set `MISSION_SESSION_ENABLED=true` globally
2. **Update Telegram Bot**: Use deep links in alerts (see MISSION_SESSION_IMPLEMENTATION_STATUS.md)
3. **Full /api/fire Integration**: Add session validation and idempotency
4. **UI Update**: Add WebSocket subscriptions to Mission Brief page
5. **Monitoring**: Add dashboards for session stats

---

**This quickstart gets the foundation running without breaking existing functionality. Legacy flow still works while new mission session flow is being tested.**
