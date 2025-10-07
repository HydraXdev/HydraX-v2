# Audit Logger Integration Checklist

Quick checklist for integrating the security audit logger into BITTEN components.

## ✅ Pre-Integration Checklist

- [ ] Verify log directory exists: `/var/log/bitten/`
- [ ] Verify permissions: `drwx------` (700) on directory
- [ ] Test basic logging:
  ```bash
  python3 -c "from src.security.audit_logger import get_audit_logger; get_audit_logger().log_auth_success('test_user')"
  tail -1 /var/log/bitten/audit.log | jq
  ```
- [ ] Run test suite: `pytest tests/test_audit_logger.py -v`

## 📋 Integration Points

### 1. Mission Session Manager (`/root/HydraX-v2/src/mission_session/`)

**Files to modify:**
- `manager.py` - Session lifecycle management

**Events to log:**

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Session creation
audit.log_session_created(
    sub=user_id,
    ms=session_id,
    aid=alert_id,
    ttl=ttl_seconds
)

# ✅ Session validation
audit.log_session_validated(
    sub=user_id,
    ms=session_id,
    result=is_valid,
    reason="Session expired" if not is_valid else None
)

# ✅ Session execution
audit.log_session_executed(
    sub=user_id,
    ms=session_id,
    op_id=fire_id
)

# ✅ Session expiration
audit.log_session_expired(
    ms=session_id,
    expired_at=expiry_timestamp
)
```

**Integration steps:**
- [ ] Add import at top of `manager.py`
- [ ] Add `log_session_created()` after session creation
- [ ] Add `log_session_validated()` in validation method
- [ ] Add `log_session_executed()` when session is consumed
- [ ] Add `log_session_expired()` in cleanup/expiry handler

---

### 2. WebApp Server (`/root/HydraX-v2/webapp_server_optimized.py`)

**Events to log:**

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Fire API endpoint
@app.route('/api/fire', methods=['POST'])
def api_fire():
    # After session validation
    if not valid:
        audit.log_session_validated(
            sub=user_id,
            ms=session_id,
            result=False,
            reason="Invalid session"
        )
        return jsonify({'error': 'Invalid session'}), 401

    # After fire execution
    audit.log_fire_requested(
        sub=user_id,
        ms=session_id,
        aid=alert_id,
        op_id=fire_id
    )

# ✅ Risk check violations
if risk_pct > max_risk:
    audit.log_fire_risk_violation(
        sub=user_id,
        ms=session_id,
        requested_risk=risk_pct,
        max_risk=max_risk
    )

# ✅ Scope/permission violations
if required_scope not in user_scopes:
    audit.log_fire_scope_violation(
        sub=user_id,
        ms=session_id,
        required_scope=required_scope,
        had_scopes=user_scopes
    )
```

**Integration steps:**
- [ ] Add import at top of file
- [ ] Add logging in `/api/fire` endpoint
- [ ] Add logging in risk validation code
- [ ] Add logging in permission checks
- [ ] Test with manual API call

---

### 3. Idempotency Manager (`/root/HydraX-v2/src/idempotency/`)

**Events to log:**

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Idempotency cache hit
def check_idempotency(client_request_id: str):
    cached = get_from_cache(client_request_id)
    if cached:
        audit.log_fire_idempotent_hit(
            sub=user_id,
            ms=session_id,
            client_request_id=client_request_id,
            cached_op_id=cached['op_id']
        )
        return cached
```

**Integration steps:**
- [ ] Add import to idempotency manager
- [ ] Add logging when cache hit occurs
- [ ] Include user_id and session_id in cache metadata
- [ ] Test with duplicate requests

---

### 4. WebSocket Server (`/root/HydraX-v2/src/metasocket/`)

**Events to log:**

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Connection
@socketio.on('connect')
def on_connect():
    sid = request.sid
    audit.log_ws_connected(sid=sid)

# ✅ Authentication
@socketio.on('authenticate')
def on_authenticate(data):
    sid = request.sid
    token = data.get('token')

    try:
        user_id = validate_jwt(token)
        audit.log_auth_success(sub=user_id, method='jwt')
        audit.log_ws_connected(sid=sid, sub=user_id)
    except Exception as e:
        audit.log_ws_auth_failed(sid=sid, reason=str(e))

# ✅ Topic subscription
@socketio.on('subscribe')
def on_subscribe(data):
    audit.log_ws_subscribed(
        sid=request.sid,
        sub=user_id,
        topic=data['topic'],
        authorized=is_authorized
    )

# ✅ Disconnection
@socketio.on('disconnect')
def on_disconnect():
    audit.log_ws_disconnected(
        sid=request.sid,
        sub=user_id,
        duration=get_duration()
    )
```

**Integration steps:**
- [ ] Add import to WebSocket server file
- [ ] Add logging in `connect` handler
- [ ] Add logging in `authenticate` handler
- [ ] Add logging in `subscribe` handler
- [ ] Add logging in `disconnect` handler
- [ ] Test with WebSocket client

---

### 5. JWT Manager (`/root/HydraX-v2/src/security/jwt_manager.py`)

**Events to log:**

```python
from audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Token validation
def validate_token(token: str):
    try:
        payload = decode_jwt(token)
        user_id = payload['sub']
        audit.log_auth_success(sub=user_id, method='jwt')
        return payload
    except Exception as e:
        audit.log_auth_failed(reason=str(e))
        raise

# ✅ Authorization check
def check_authorization(user_id: str, resource: str, action: str):
    if not has_permission(user_id, resource, action):
        audit.log_authorization_denied(
            sub=user_id,
            resource=resource,
            action=action
        )
        raise PermissionError()
```

**Integration steps:**
- [ ] Add import to jwt_manager.py
- [ ] Add logging in token validation
- [ ] Add logging in authorization checks
- [ ] Test with valid/invalid tokens

---

### 6. Rate Limiter (`/root/HydraX-v2/src/rate_limiter.py`)

**Events to log:**

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()

# ✅ Rate limit exceeded
def check_rate_limit(user_id: str, endpoint: str):
    if is_rate_limited(user_id, endpoint):
        audit.log_rate_limit_exceeded(
            sub=user_id,
            endpoint=endpoint,
            limit=get_limit(endpoint)
        )
        raise RateLimitError()
```

**Integration steps:**
- [ ] Add import to rate_limiter.py
- [ ] Add logging when rate limit exceeded
- [ ] Test with rapid requests

---

## 🧪 Testing Integration

After integrating each component, verify logging:

```bash
# 1. Clear existing logs
sudo rm /var/log/bitten/audit.log

# 2. Trigger event in component
# (e.g., create session, make fire request, connect WebSocket)

# 3. Verify log entry
tail -1 /var/log/bitten/audit.log | jq

# 4. Check for required fields
tail -1 /var/log/bitten/audit.log | jq 'keys'

# 5. Verify no PII leaked
grep -E "(balance|password|token|email|phone)" /var/log/bitten/audit.log
# Should return nothing or only "[REDACTED]"
```

## 📊 Post-Integration Monitoring

### Daily Log Analysis

```bash
# Count events by type
cat /var/log/bitten/audit.log | jq -r '.event_type' | sort | uniq -c

# Find all WARNING/ERROR events
cat /var/log/bitten/audit.log | jq 'select(.level == "WARNING" or .level == "ERROR")'

# Check log rotation
ls -lh /var/log/bitten/
```

### Weekly Security Review

```bash
# Find failed authentications
cat /var/log/bitten/audit.log* | jq 'select(.event_type == "auth.failed")'

# Find risk violations
cat /var/log/bitten/audit.log* | jq 'select(.event_type == "fire.risk_violation")'

# Find rate limit violations
cat /var/log/bitten/audit.log* | jq 'select(.event_type == "rate_limit.exceeded")'

# Count fire requests per user
cat /var/log/bitten/audit.log* | \
  jq -r 'select(.event_type == "fire.requested") | .sub' | \
  sort | uniq -c | sort -rn
```

## 🚨 Common Issues

### Issue: Logs not created

**Solution:**
```bash
sudo mkdir -p /var/log/bitten
sudo chmod 700 /var/log/bitten
sudo chown $USER:$USER /var/log/bitten
```

### Issue: Permission denied

**Solution:**
```bash
sudo chown -R $USER:$USER /var/log/bitten
```

### Issue: PII appearing in logs

**Solution:**
1. Review code - ensure using audit logger methods, not raw logging
2. Add field to `SENSITIVE_KEYS` in `SanitizedJSONFormatter`
3. Use `sanitize_data()` before logging arbitrary data

### Issue: Events not appearing

**Check:**
```python
# Verify logger is working
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()
audit.log_auth_success('test_user')

# Check log file
import subprocess
subprocess.run(['tail', '-1', '/var/log/bitten/audit.log'])
```

## ✅ Final Checklist

Before deploying to production:

- [ ] All integration points implemented
- [ ] All tests passing: `pytest tests/test_audit_logger.py -v`
- [ ] No PII in logs: `grep -i "balance\|password\|email" /var/log/bitten/audit.log`
- [ ] Log rotation working: `ls -lh /var/log/bitten/`
- [ ] Permissions correct: `ls -ld /var/log/bitten/`
- [ ] Log analysis tools tested: `cat /var/log/bitten/audit.log | jq`
- [ ] Documentation reviewed: `cat src/security/AUDIT_LOGGER_README.md`
- [ ] Integration examples tested: `python src/security/audit_logger_examples.py`

## 📚 Resources

- **Main Documentation**: `/root/HydraX-v2/src/security/AUDIT_LOGGER_README.md`
- **Usage Examples**: `/root/HydraX-v2/src/security/audit_logger_examples.py`
- **Test Suite**: `/root/HydraX-v2/tests/test_audit_logger.py`
- **Source Code**: `/root/HydraX-v2/src/security/audit_logger.py`

---

**Questions?** Review the examples file or run the test suite for verification.
