# HYDRASOCKET v1 Operations Overview

## System Architecture
- **Router**: HydraSocket v1 WebSocket + REST API (port 8888)
- **Database**: SQLite with sequencing + idempotency tables
- **ZMQ**: EA lifecycle events (5558), telemetry (5560)
- **Process Management**: PM2 or systemd
- **Monitoring**: Prometheus metrics + Grafana alerts

## Service Dependencies
```
HydraSocket Router (port 8888)
├── Database (bitten_events.db)
├── ZMQ Lifecycle (port 5558)
├── ZMQ Telemetry (port 5560)
└── Metrics Export (Prometheus)
```

## Critical Endpoints
- `/healthz` - Liveness probe
- `/api/health` - Detailed health + schema hash
- `/docs` - API documentation
- `/metrics` - Prometheus metrics
- WebSocket: `ws://host:8888/socket.io/`

## Key Metrics
- `order_to_open_ms_p95` - Order processing latency
- `event_lag_ms_p95` - Event ingestion lag
- `ws_clients` - Active WebSocket connections
- `backpressure_drops_total` - Dropped messages due to backpressure

## Emergency Contacts
- **On-call Engineer**: See deployment notes
- **Escalation**: System Administrator
- **Business Owner**: Trading Operations Team

## Runbook Navigation
- [10-deploy.md](./10-deploy.md) - Deployment procedures
- [20-restart.md](./20-restart.md) - Service restart procedures
- [30-rollback.md](./30-rollback.md) - Rollback procedures
- [40-dr.md](./40-dr.md) - Disaster recovery
- [50-alerts.md](./50-alerts.md) - Alert response guide
- [60-chaos-tests.md](./60-chaos-tests.md) - Chaos engineering tests