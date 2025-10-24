# Fire Service v2.0 - Deployment Guide

## Quick Start

```bash
# 1. Install dependencies
cd /root/HydraX-v2/services/fire_service
pip install -r requirements.txt

# 2. Run tests
python3 test_fire_service.py

# 3. Start service
python3 main.py
```

## Production Deployment with PM2

```bash
# Start fire service
pm2 start /root/HydraX-v2/services/fire_service/main.py \
  --name fire_service \
  --interpreter python3 \
  --log /root/HydraX-v2/logs/fire_service.log

# Save PM2 configuration
pm2 save

# Enable PM2 startup
pm2 startup
```

## Verification

### 1. Health Check

```bash
curl http://localhost:8890/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "fire_service",
  "version": "2.0.0"
}
```

### 2. Service Stats

```bash
curl http://localhost:8890/api/stats
```

### 3. API Documentation

Open in browser: `http://localhost:8890/docs`

### 4. Example Fire Execution

```bash
python3 example_fire.py
```

## Integration Checklist

- [ ] IPC queue connected: `ipc:///tmp/bitten_cmdqueue`
- [ ] Command router running on port 5555
- [ ] Confirmation listener running on port 5558
- [ ] Database accessible: `/root/HydraX-v2/bitten.db`
- [ ] Fire mode database: `/root/HydraX-v2/data/fire_modes.db`
- [ ] EA connected with fresh heartbeat (<120s)

## Port Requirements

- **8890**: Fire Service API (FastAPI)
- **5555**: Command Router (ZMQ ROUTER)
- **5558**: Confirmation Listener (ZMQ PULL)

## Database Schema

Fire Service requires these tables in `bitten.db`:

1. **fires** - Fire execution records
2. **ea_instances** - EA connections and balances
3. **positions_live** - Live position tracking

Fire mode database (`fire_modes.db`):

1. **user_fire_modes** - User fire mode settings
2. **active_slots** - Slot tracking

## Environment Variables

```bash
# Optional configuration
export LOG_LEVEL=INFO
export FIRE_SERVICE_PORT=8890
```

## Monitoring

### Check Service Status

```bash
pm2 status fire_service
```

### View Logs

```bash
# Real-time logs
pm2 logs fire_service

# Last 100 lines
pm2 logs fire_service --lines 100

# Error logs only
pm2 logs fire_service --err
```

### Service Metrics

```bash
# CPU/Memory usage
pm2 monit

# Service statistics
curl http://localhost:8890/api/stats
```

## Troubleshooting

### Service Won't Start

1. Check if port 8890 is available:
   ```bash
   netstat -tuln | grep 8890
   ```

2. Verify IPC queue exists:
   ```bash
   ls -la /tmp/bitten_cmdqueue
   ```

3. Check dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Fires Not Executing

1. Verify command router is running:
   ```bash
   ps aux | grep command_router
   ```

2. Check IPC queue connection:
   ```bash
   pm2 logs fire_service | grep "IPC queue"
   ```

3. Verify EA connection:
   ```bash
   sqlite3 /root/HydraX-v2/bitten.db \
     "SELECT target_uuid, (strftime('%s','now') - last_seen) AS age
      FROM ea_instances WHERE target_uuid = 'COMMANDER_DEV_001';"
   ```

### Confirmations Not Received

1. Check confirmation tracker is running:
   ```bash
   pm2 logs fire_service | grep "Confirmation listener"
   ```

2. Verify port 5558 is bound:
   ```bash
   netstat -tuln | grep 5558
   ```

3. Test confirmation flow:
   ```bash
   # Check fires table for status updates
   sqlite3 /root/HydraX-v2/bitten.db \
     "SELECT fire_id, status, ticket FROM fires
      ORDER BY created_at DESC LIMIT 5;"
   ```

## Performance Tuning

### Uvicorn Workers

For high-load scenarios, adjust workers in `main.py`:

```python
uvicorn.run(
    "api:app",
    host=config.API_HOST,
    port=config.API_PORT,
    workers=4,  # Increase for more concurrency
    log_level=config.LOG_LEVEL.lower()
)
```

⚠️ **Note**: Multiple workers may require Redis for shared state.

### Database Optimization

For high-frequency trading:

```sql
-- Add indexes
CREATE INDEX IF NOT EXISTS idx_fires_user_created
  ON fires(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fires_status
  ON fires(status);

CREATE INDEX IF NOT EXISTS idx_positions_user
  ON positions_live(user_id);
```

## Security Considerations

1. **API Access**: Consider adding authentication middleware
2. **Rate Limiting**: Implement request throttling for production
3. **Input Validation**: Already handled via Pydantic models
4. **Database Access**: Use connection pooling for production

## Backup and Recovery

### Backup Fire Records

```bash
# Backup fires table
sqlite3 /root/HydraX-v2/bitten.db \
  ".dump fires" > fires_backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
sqlite3 /root/HydraX-v2/bitten.db < fires_backup_20251008.sql
```

## Scaling Considerations

For multi-server deployments:

1. **Shared Database**: Use PostgreSQL instead of SQLite
2. **Message Queue**: Add RabbitMQ/Redis for distributed queues
3. **Load Balancer**: Use nginx for API load balancing
4. **State Management**: Implement Redis for shared state

## API Rate Limits

Current implementation has no rate limits. For production:

```python
# Add to api.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/fire")
@limiter.limit("10/minute")  # 10 fires per minute
async def execute_fire(request: FireRequest):
    ...
```

## Support

For issues:
1. Check logs: `pm2 logs fire_service`
2. Run tests: `python3 test_fire_service.py`
3. Verify integration: `python3 example_fire.py`
4. Review documentation: `/root/HydraX-v2/services/fire_service/README.md`

---

**Deployed**: October 8, 2025
**Version**: 2.0.0
**Status**: Production Ready ✅
