# BITTEN Mission Session - Wiring Points for Deployment

**Purpose**: Exact configuration points and deployment steps for mission session architecture
**Audience**: DevOps Engineers, System Administrators
**Status**: Production Ready
**Date**: October 5, 2025

---

## 🎯 Quick Deployment Checklist

```bash
# 1. Environment variables configured ✅
# 2. Database migration applied ✅
# 3. JWT keys generated ✅
# 4. Webapp code updated ✅
# 5. UI code updated ✅
# 6. Services restarted ✅
# 7. Tests passed ✅
```

---

## 🔌 Critical Wiring Points

### 1. WebSocket Adapter Configuration (Client)

**Location**: `/root/HydraX-v2/bitten-ui/src/lib/websocket-client.ts`

**Configuration**:

```typescript
const socket = io(
  process.env.NEXT_PUBLIC_BUS_URL || "https://www.joinbitten.com",
  {
    path: "/socket.io",
    transports: ["websocket", "polling"],
    auth: (cb) => {
      // Extract token from URL
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token") || urlParams.get("t");

      cb({
        token: token, // OR use query: { t: token }
      });
    },
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  },
);
```

**Environment Variables** (`.env.production`):

```bash
NEXT_PUBLIC_BUS_URL=wss://www.joinbitten.com
# OR for local dev:
# NEXT_PUBLIC_BUS_URL=ws://localhost:8888
```

**Topics to Subscribe**:

```typescript
socket.on("authenticated", () => {
  socket.emit("subscribe", {
    topics: [
      "user.profile", // User account data
      "mission.alert/123", // Specific alert (dynamic alertId)
      "trades.open", // Open positions snapshot
      "trades.delta", // Position updates
      "system.status", // System health beacons
      "stats.equity", // Stats page - equity updates
      "stats.kpis", // Stats page - KPI updates
      "stats.events", // Stats page - recent events
      "stats.dist.pair", // Stats page - pair distribution
      "stats.dist.session", // Stats page - session distribution
    ],
  });
});
```

---

### 2. Mission Deep Link Format

**Telegram Button URL**:

```
https://bitten.io/mission?ms=<MISSION_SESSION_ID>&token=<JWS>
```

**Components**:

- **ms**: Mission session ID (format: `ms_01JXXXXXXXXX`)
- **token**: Signed JWT with claims

**Example**:

```
https://www.joinbitten.com/mission?ms=ms_01J7X5M2C3ABC&token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0yMDI1LTEwIn0.eyJpc3MiOiJiaXR0ZW4tYmFja2VuZCIsImF1ZCI6ImJpdHRlbi11aSIsInN1YiI6InVzZXJfNzE3NjE5MTg3MiIsIm1zIjoibXNfMDFKN1g1TTJDM0FCQyIsImFpZCI6MTIzNDUsInNjb3BlcyI6WyJtaXNzaW9uOnZpZXciLCJvcmRlcjpleGVjdXRlIl0sInBhaXIiOiJFVVJVU0QiLCJ0ZiI6Ik01Iiwicmlza01heFVzZCI6MTUwLCJleHAiOjE3MjgxMjM0NTYsImlhdCI6MTcyODEyMzE1Niwibm9uY2UiOiI4ZjNjMWU5Yy4uLiJ9.signature...
```

**Implementation** (Telegram Bot):

```python
from src.telegram.deep_link_generator import get_link_generator

link_generator = get_link_generator()
link_data = link_generator.generate_mission_link(
    signal_id=signal['signal_id'],
    user_id=user_id,
    alert_id=alert_id,
    pair=signal['symbol'],
    timeframe=signal['timeframe'],
    risk_max_usd=calculate_user_risk_limit(user_id)
)

button_url = link_data['deep_link']
```

---

### 3. Execute Endpoint Contract

**Endpoint**: `POST /api/fire`

**Request Headers**:

```http
Authorization: Bearer <JWS>
Content-Type: application/json
```

**Request Body**:

```json
{
  "clientRequestId": "crid_a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "missionSessionId": "ms_01J7X5M2C3ABC",
  "alertId": 12345,
  "entry": 1.05234,
  "stopLoss": 1.05134,
  "takeProfit": 1.05382,
  "riskUsd": 100.0
}
```

**Response Codes**:

| Code | Status        | Meaning                | Client Action                        |
| ---- | ------------- | ---------------------- | ------------------------------------ |
| 202  | Accepted      | Fire command queued    | Redirect to /status, wait for events |
| 400  | Bad Request   | Missing required field | Show error, allow retry              |
| 401  | Unauthorized  | Token expired/invalid  | Show "Session Expired" screen        |
| 403  | Forbidden     | Missing scope          | Show "Access Denied" screen          |
| 409  | Conflict      | Already executed       | Show "Already Executed" screen       |
| 410  | Gone          | Session expired        | Show "Session Expired" screen        |
| 422  | Unprocessable | Validation failed      | Show specific error, allow retry     |
| 500  | Server Error  | Internal error         | Show generic error, allow retry      |

**Success Response** (202):

```json
{
  "success": true,
  "opId": "op_xyz789",
  "status": "ACCEPTED"
}
```

**Error Response**:

```json
{
  "success": false,
  "error": "Session expired",
  "error_code": "SESSION_EXPIRED"
}
```

**Client Implementation**:

```typescript
async function executeOrder(token: string, data: ExecuteData) {
  const response = await fetch("/api/fire", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (response.status === 202) {
    // Success - wait for events
    return await response.json();
  } else if (response.status === 409) {
    // Already executed
    showAlreadyExecutedScreen();
  } else if (response.status === 410) {
    // Session expired
    showSessionExpiredScreen();
  } else if (response.status === 422) {
    // Validation error
    const error = await response.json();
    showValidationError(error.error);
  } else {
    // Other error
    const error = await response.json();
    showGenericError(error.error);
  }
}
```

---

### 4. Status/Stats Page Event Consumption

**Status Page** (`/status`):

**Topics to Listen**:

- `trades.open` - Snapshot of open positions
- `trades.delta` - Position updates (ARMING → FILLED → updates → CLOSED)

**Event Handling**:

```typescript
socket.on("trades.delta", (data) => {
  if (data.status === "ARMING") {
    // Show "Arming..." indicator
    showArmingIndicator(data.id);
  } else if (data.status === "FILLED") {
    // Add to positions list
    addPosition(data);
    removeArmingIndicator();
  } else if (data.status === "OPEN") {
    // Update P&L
    updatePosition(data.id, {
      current: data.current,
      pnl: data.pnl,
      equity: data.equity,
    });
  } else if (data.status === "CLOSED") {
    // Remove from list
    removePosition(data.id);
    showCloseNotification(data);
  }
});
```

**Stats Page** (`/stats`):

**Topics to Listen**:

- `stats.equity` - Equity time series updates
- `stats.kpis` - KPI updates (total trades, win rate, etc.)
- `stats.events` - Recent trading events
- `stats.dist.pair` - Pair distribution chart
- `stats.dist.session` - Session distribution chart

**Event Handling**:

```typescript
socket.on("stats.equity", (data) => {
  // Add point to equity chart
  equityChart.addPoint({
    x: data.timestamp * 1000,
    y: data.equity,
  });
});

socket.on("stats.kpis", (data) => {
  // Update KPI cards
  updateKPI("total_trades", data.total_trades);
  updateKPI("win_rate", data.win_rate);
  updateKPI("total_pnl", data.total_pnl);
});

socket.on("stats.events", (data) => {
  // Add to recent events feed
  addRecentEvent(data.event);
});
```

---

## 🔐 Security Configuration

### JWT Keys

**Generation** (one-time):

```bash
mkdir -p /root/HydraX-v2/keys
cd /root/HydraX-v2/keys
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
chmod 600 jwt_private.pem
chmod 644 jwt_public.pem
```

**File Permissions**:

```bash
-rw------- 1 root root 1704 Oct  5 17:14 jwt_private.pem  # 600 (private key)
-rw-r--r-- 1 root root  451 Oct  5 17:14 jwt_public.pem   # 644 (public key)
```

**Environment Variables**:

```bash
JWT_PRIVATE_KEY_PATH=/root/HydraX-v2/keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/root/HydraX-v2/keys/jwt_public.pem
JWT_KEY_ID=key-2025-10
JWT_ALGORITHM=RS256
JWT_ISSUER=bitten-backend
JWT_AUDIENCE=bitten-ui
```

**Key Rotation Plan**:

1. Generate new key pair with new kid (e.g., `key-2025-11`)
2. Update `JWT_KEY_ID` to new kid
3. Keep old keys valid until all TTLs drain (~10 minutes)
4. Remove old keys after 24 hours

---

### Mission Session Configuration

**Environment Variables**:

```bash
MISSION_SESSION_TTL=600        # 10 minutes (5-10 min range)
IDEMPOTENCY_TTL=600            # 10 minutes cache
BITTEN_UI_URL=https://www.joinbitten.com
```

**Database Migration**:

```bash
# Apply mission session schema
sqlite3 /root/HydraX-v2/bitten.db < /root/HydraX-v2/migrations/002_mission_sessions.sql

# Verify
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT * FROM schema_versions WHERE version = '002_mission_sessions';"
```

---

## 📦 Deployment Steps

### Pre-Deployment Checklist

```bash
# 1. Verify database backup
cp /root/HydraX-v2/bitten.db /root/HydraX-v2/bitten.db.backup.$(date +%Y%m%d)

# 2. Verify JWT keys exist
ls -la /root/HydraX-v2/keys/jwt_*.pem

# 3. Run Go/No-Go validation
python3 /root/HydraX-v2/tests/go_no_go_validation.py
# Should show: 27/28 tests passed

# 4. Verify environment variables
grep -E "JWT_|MISSION_|BITTEN_UI" /root/HydraX-v2/.env

# 5. Build UI (if changes made)
cd /root/HydraX-v2/bitten-ui
npm run build
```

### Deployment Sequence

**1. Apply Database Migration**:

```bash
sqlite3 /root/HydraX-v2/bitten.db < /root/HydraX-v2/migrations/002_mission_sessions.sql
```

**2. Restart Webapp**:

```bash
pm2 restart webapp
```

**3. Verify Webapp Started**:

```bash
pm2 logs webapp --lines 20

# Should see:
# ✅ Mission Session Architecture loaded
# ✅ Loaded JWT private key
# ✅ Loaded JWT public key
```

**4. Restart UI** (if updated):

```bash
pm2 restart bitten-ui
```

**5. Run Integration Tests**:

```bash
python3 /root/HydraX-v2/tests/dry_run_mission_flow.py
```

**6. Manual Smoke Test**:

```bash
# Generate test session
python3 << 'EOF'
import sys
sys.path.append('/root/HydraX-v2')
from src.telegram.deep_link_generator import get_link_generator

link_gen = get_link_generator()
link_data = link_gen.generate_mission_link(
    signal_id='SMOKE_TEST',
    user_id='7176191872',
    alert_id=999,
    pair='EURUSD'
)
print(f"\n🔗 Test Link:\n{link_data['deep_link']}\n")
EOF
```

**7. Open test link in browser and verify**:

- [ ] Page loads
- [ ] WebSocket connects
- [ ] Beacons show operational
- [ ] Mission data displays

---

### Post-Deployment Verification

**Check Logs**:

```bash
# Webapp logs
pm2 logs webapp --lines 50 | grep -E "✅|❌|Mission Session"

# Audit logs
tail -20 /var/log/bitten/audit.log | jq

# Error logs
pm2 logs webapp --err --lines 20
```

**Check Database**:

```bash
# Verify tables exist
sqlite3 /root/HydraX-v2/bitten.db \
  ".tables" | grep -E "mission_sessions|idempotency_cache"

# Check for test sessions
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) FROM mission_sessions;"
```

**Check WebSocket**:

```bash
# Test WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: $(openssl rand -base64 16)" \
  http://localhost:8888/socket.io/
```

**Monitor Performance**:

```bash
# Watch for errors
watch -n 5 "pm2 list | grep -E 'webapp|bitten-ui'"

# Monitor latency
pm2 monit
```

---

## 🚨 Rollback Procedure

**If deployment fails**:

**1. Stop Services**:

```bash
pm2 stop webapp bitten-ui
```

**2. Restore Database** (if needed):

```bash
cp /root/HydraX-v2/bitten.db.backup.YYYYMMDD /root/HydraX-v2/bitten.db
```

**3. Revert Code**:

```bash
cd /root/HydraX-v2
git checkout HEAD~1 webapp_server_optimized.py

cd /root/HydraX-v2/bitten-ui
git checkout HEAD~1 app/mission/page.tsx
```

**4. Rebuild UI**:

```bash
cd /root/HydraX-v2/bitten-ui
npm run build
```

**5. Restart Services**:

```bash
pm2 restart webapp bitten-ui
```

**6. Verify Legacy Flow**:

```bash
curl http://localhost:8888/healthz
```

**7. Document Incident**:

```bash
echo "Rollback: $(date) - Reason: <describe>" >> /var/log/bitten/incidents.log
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

**Performance**:

- WebSocket connection latency (target: < 100ms)
- Event delivery time (target: < 250ms P95)
- Page load time (target: < 2000ms)

**Security**:

- Failed authentication attempts (audit log)
- Risk violations (fire.risk_violation events)
- Token expiry rate

**Reliability**:

- WebSocket disconnection rate
- Idempotency cache hit rate
- Session expiration rate

**Monitoring Commands**:

```bash
# WebSocket connections
netstat -an | grep 8888 | grep ESTABLISHED | wc -l

# Recent audit events
tail -100 /var/log/bitten/audit.log | jq -r '.event_type' | sort | uniq -c

# Mission session stats
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT status, COUNT(*) FROM mission_sessions GROUP BY status;"

# Idempotency cache stats
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT COUNT(*) as total,
          COUNT(CASE WHEN expires_at > strftime('%s', 'now') THEN 1 END) as active,
          COUNT(CASE WHEN expires_at <= strftime('%s', 'now') THEN 1 END) as expired
   FROM idempotency_cache;"
```

---

## 🔧 Troubleshooting

### Issue: WebSocket Authentication Fails

**Symptoms**: 401 errors, `ws.auth_failed` events in audit log

**Check**:

```bash
# 1. Verify JWT keys loaded
pm2 logs webapp | grep "JWT"

# 2. Test token generation
python3 -c "
from src.security.jwt_manager import get_jwt_manager
jm = get_jwt_manager()
token = jm.generate_mission_token('test', 'ms_test', 999, ['mission:view'])
print('Token:', token[:50])
"

# 3. Check key permissions
ls -la /root/HydraX-v2/keys/
```

**Solution**: Verify JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH are correct

---

### Issue: Session Always Expired

**Symptoms**: All sessions return 410 Gone

**Check**:

```bash
# Check system time
date

# Check session TTL
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT mission_session_id, created_at, expires_at,
          (expires_at - created_at) as ttl_seconds,
          (expires_at - strftime('%s', 'now')) as remaining_seconds
   FROM mission_sessions ORDER BY created_at DESC LIMIT 5;"
```

**Solution**:

- Verify MISSION_SESSION_TTL is set correctly (600 = 10 minutes)
- Check system clock is synchronized

---

### Issue: Idempotency Not Working

**Symptoms**: Duplicate orders created

**Check**:

```bash
# Check cache entries
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT * FROM idempotency_cache ORDER BY created_at DESC LIMIT 5;"

# Check for duplicate fires
sqlite3 /root/HydraX-v2/bitten.db \
  "SELECT mission_id, COUNT(*) as count FROM fires
   GROUP BY mission_id HAVING count > 1;"
```

**Solution**:

- Verify idempotency_cache table exists
- Check clientRequestId is being generated consistently
- Review /api/fire logs for idempotency check execution

---

## 📞 Support & Escalation

**Production Issues**:

1. Check `/var/log/bitten/audit.log` for security events
2. Check `pm2 logs webapp` for application errors
3. Run `/root/HydraX-v2/tests/go_no_go_validation.py` for diagnostics
4. Collect: logs + database snapshot + error screenshots
5. Escalate to development team

**Emergency Contacts**:

- DevOps: [escalation procedure]
- Development: [escalation procedure]

---

**This document provides complete wiring configuration for deploying the mission session architecture to production.**
