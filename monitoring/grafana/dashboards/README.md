# BITTEN v2.0 Grafana Dashboards

## Dashboard Files (JSON format - import via Grafana UI)

1. **phase1_cutover.json** - Real-time cutover monitoring
   - Service health indicators
   - Fire execution rate
   - Signal generation rate
   - Error rates by service
   
2. **service_health.json** - 5-service health dashboard
   - All service status (up/down)
   - P95/P99 latency metrics
   - Request rates
   - Error rates
   
3. **database_performance.json** - PostgreSQL metrics
   - Connection pool utilization
   - Query latency (P50/P95/P99)
   - Slow query log
   - Table sizes

## Import Instructions

```bash
# Import dashboards via Grafana API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @phase1_cutover.json
```

## Access

Grafana UI: http://localhost:3000
Default credentials: admin/admin (change on first login)
