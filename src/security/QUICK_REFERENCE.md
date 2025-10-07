# Audit Logger - Quick Reference Card

**One-page cheat sheet for security audit logging in BITTEN**

---

## 🚀 Quick Start (Copy & Paste)

```python
from src.security.audit_logger import get_audit_logger
audit = get_audit_logger()
```

---

## 📋 Common Events (Copy & Paste)

### Mission Session Events

```python
# Session created
audit.log_session_created(
    sub=user_id,      # User ID
    ms=session_id,    # Mission session ID
    aid=alert_id,     # Alert ID
    ttl=300           # TTL in seconds
)

# Session validated
audit.log_session_validated(
    sub=user_id,
    ms=session_id,
    result=True,      # or False
    reason=None       # or "Session expired"
)

# Session executed
audit.log_session_executed(
    sub=user_id,
    ms=session_id,
    op_id=fire_id     # Fire ID
)

# Session expired
audit.log_session_expired(
    ms=session_id,
    expired_at="2025-10-05T17:30:00Z"
)
```

### Fire Events

```python
# Fire requested
audit.log_fire_requested(
    sub=user_id,
    ms=session_id,
    aid=alert_id,
    op_id=fire_id
)

# Idempotency hit
audit.log_fire_idempotent_hit(
    sub=user_id,
    ms=session_id,
    client_request_id=request_id,
    cached_op_id=cached_fire_id
)

# Risk violation
audit.log_fire_risk_violation(
    sub=user_id,
    ms=session_id,
    requested_risk=10.0,
    max_risk=5.0
)

# Scope violation
audit.log_fire_scope_violation(
    sub=user_id,
    ms=session_id,
    required_scope="fire:execute",
    had_scopes=["fire:view"]
)
```

### WebSocket Events

```python
# Connected
audit.log_ws_connected(
    sid=socket_id,
    sub=user_id  # Optional, after auth
)

# Auth failed
audit.log_ws_auth_failed(
    sid=socket_id,
    reason="Invalid token"
)

# Subscribed
audit.log_ws_subscribed(
    sid=socket_id,
    sub=user_id,
    topic="signals:EURUSD",
    authorized=True
)

# Disconnected
audit.log_ws_disconnected(
    sid=socket_id,
    sub=user_id,
    duration=123.45  # seconds
)
```

### General Security

```python
# Auth success
audit.log_auth_success(
    sub=user_id,
    method="jwt"  # or "password"
)

# Auth failed
audit.log_auth_failed(
    reason="Invalid credentials",
    sub=user_id  # Optional
)

# Authorization denied
audit.log_authorization_denied(
    sub=user_id,
    resource="premium_signals",
    action="access"
)

# Rate limit exceeded
audit.log_rate_limit_exceeded(
    sub=user_id,
    endpoint="/api/fire",
    limit=10
)
```

---

## 🔍 Quick Log Queries

### View Live Logs
```bash
tail -f /var/log/bitten/audit.log | jq
```

### Last 10 Events
```bash
tail -10 /var/log/bitten/audit.log | jq
```

### Find Failed Auths
```bash
cat /var/log/bitten/audit.log | jq 'select(.event_type == "auth.failed")'
```

### Count Events by Type
```bash
cat /var/log/bitten/audit.log | jq -r '.event_type' | sort | uniq -c
```

### Find User Activity
```bash
cat /var/log/bitten/audit.log | jq 'select(.sub == "7176191872")'
```

### Find WARNING Events
```bash
cat /var/log/bitten/audit.log | jq 'select(.level == "WARNING")'
```

### Fire Requests Last Hour
```bash
cat /var/log/bitten/audit.log | \
  jq 'select(.event_type == "fire.requested" and .timestamp > "'$(date -u -d '1 hour ago' -Iseconds)'")'
```

---

## 🔒 Security Reminders

### ✅ DO Log
- User IDs (`sub`)
- Session IDs (`ms`)
- Alert IDs (`aid`)
- Operation IDs (`op_id`)
- Event outcomes (success/fail)
- Timestamps (UTC)

### ❌ NEVER Log
- Balances
- Account numbers
- Passwords
- Tokens/keys
- Email addresses
- Phone numbers
- Trade amounts

### Auto-Sanitized Fields
These are **automatically redacted** to `[REDACTED]`:
- `balance`, `equity`, `profit`, `loss`, `amount`
- `password`, `token`, `secret`, `key`, `nonce`
- `account_number`, `email`, `phone`

---

## 📊 Event Types Reference

| Code | Event Type | Level |
|------|-----------|-------|
| `session.created` | Session created | INFO |
| `session.validated` | Session validated | INFO/WARN |
| `session.executed` | Session executed | INFO |
| `session.expired` | Session expired | WARN |
| `fire.requested` | Fire requested | INFO |
| `fire.idempotent_hit` | Duplicate request | INFO |
| `fire.risk_violation` | Risk exceeded | WARN |
| `fire.scope_violation` | Missing scope | WARN |
| `ws.connected` | WS connected | INFO |
| `ws.auth_failed` | WS auth failed | WARN |
| `ws.subscribed` | WS subscribed | INFO/WARN |
| `ws.disconnected` | WS disconnected | INFO |
| `auth.success` | Auth success | INFO |
| `auth.failed` | Auth failed | WARN |
| `authz.denied` | Authorization denied | WARN |
| `rate_limit.exceeded` | Rate limit hit | WARN |

---

## 🛠️ Troubleshooting

### Logs Not Appearing?
```bash
# Check directory exists
ls -ld /var/log/bitten

# Check permissions (should be 700)
sudo chmod 700 /var/log/bitten

# Test manually
python3 -c "from src.security.audit_logger import get_audit_logger; get_audit_logger().log_auth_success('test')"
tail -1 /var/log/bitten/audit.log | jq
```

### PII Leaking?
```bash
# Search for sensitive data
grep -E "(balance|password|token|email)" /var/log/bitten/audit.log

# Should only see "[REDACTED]"
```

### Need to Clear Logs?
```bash
# Backup first!
sudo cp /var/log/bitten/audit.log /var/log/bitten/audit.log.backup

# Clear
sudo rm /var/log/bitten/audit.log

# Logs will auto-recreate
```

---

## 📁 File Locations

| File | Location |
|------|----------|
| **Logs** | `/var/log/bitten/audit.log` |
| **Module** | `/root/HydraX-v2/src/security/audit_logger.py` |
| **Tests** | `/root/HydraX-v2/tests/test_audit_logger.py` |
| **README** | `/root/HydraX-v2/src/security/AUDIT_LOGGER_README.md` |
| **Examples** | `/root/HydraX-v2/src/security/audit_logger_examples.py` |
| **Checklist** | `/root/HydraX-v2/src/security/INTEGRATION_CHECKLIST.md` |

---

## 🧪 Quick Test

```bash
# Run all tests
cd /root/HydraX-v2
pytest tests/test_audit_logger.py -v

# Should see: 22 passed in ~2s
```

---

## 📞 Need Help?

1. **Full Docs**: `cat /root/HydraX-v2/src/security/AUDIT_LOGGER_README.md`
2. **Examples**: `cat /root/HydraX-v2/src/security/audit_logger_examples.py`
3. **Integration**: `cat /root/HydraX-v2/src/security/INTEGRATION_CHECKLIST.md`

---

**Print this card and keep it at your desk! 📄**
