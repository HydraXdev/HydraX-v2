# HYDRASOCKET v1 Deployment Playbook

## Pre-Deployment Checklist

- [ ] Database migration tested (`test_hydrasocket_migration.py` passes)
- [ ] Schema hash verified (`/api/health` returns expected `schema_sha256`)
- [ ] Load tests passed (K6 results archived)
- [ ] Security tests passed (RBAC + idempotency validated)
- [ ] Backup created (see [40-dr.md](./40-dr.md))

## Blue/Green Deployment Steps

### 1. Preparation

```bash
# Stop accepting new WebSocket connections
curl -X POST http://localhost:8888/admin/drain

# Wait for active connections to finish (max 60s)
sleep 60
```

### 2. Database Migration (if required)

```bash
# Apply migrations
cd /root/HydraX-v2
sqlite3 event_bus/bitten_events.db < migrations/001_add_sequencing.sql

# Verify migration
python3 test_hydrasocket_migration.py
```

### 3. Code Deployment

```bash
# Pull latest code
git fetch origin
git checkout router-v1.0.0

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Service Restart (Zero-Downtime)

```bash
# Option A: PM2 rolling restart
pm2 reload hydrasocket-router

# Option B: systemd restart
systemctl restart hydrasocket
```

### 5. Health Check

```bash
# Wait for service to be ready
sleep 10

# Verify health
curl http://localhost:8888/healthz
curl http://localhost:8888/api/health

# Check schema hash matches deployment
EXPECTED_HASH=$(sha256sum /root/HydraX-v2/openapi/openapi.yaml | cut -d' ' -f1)
ACTUAL_HASH=$(curl -s http://localhost:8888/api/health | jq -r .schema_sha256)

if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
  echo "❌ Schema hash mismatch! Rolling back..."
  exit 1
fi

echo "✅ Deployment successful"
```

### 6. Post-Deployment Validation

```bash
# Test WebSocket connection
python3 tests/smoke/test_ws_connection.py

# Test API endpoints
python3 tests/smoke/test_api_endpoints.py

# Monitor for 5 minutes
watch -n 30 'curl -s http://localhost:8888/api/health | jq'
```

## Rollback Trigger Conditions

- Health check fails after 60 seconds
- Schema hash mismatch
- WebSocket connections drop > 50%
- API error rate > 1%
- Event lag > 1000ms for 2 minutes

## Post-Deployment Monitoring

Monitor these metrics for 30 minutes post-deployment:

- `order_to_open_ms_p95 < 250ms`
- `event_lag_ms_p95 < 500ms`
- `ws_clients >= baseline`
- `http_requests_total{status!~"2.."} rate < 1%`

## Deployment Notes

- Always deploy during low-traffic hours
- Keep previous version available for 24h
- Update Grafana deployment annotations
- Notify trading operations team
