# 🏗️ BITTEN System Architecture

## System Overview

BITTEN (Bot-Integrated Tactical Trading Engine/Network) is a distributed automated trading system built on microservices architecture with ZMQ messaging, real-time ML optimization, and multi-tier user access control.

## Core Architecture Principles

- **Event-Driven**: All components communicate via ZMQ message passing
- **Microservices**: Each component runs as independent PM2 process
- **Real-Time Processing**: Sub-millisecond latency for market data
- **Fault Tolerance**: Auto-restart, heartbeat monitoring, circuit breakers
- **Horizontal Scalability**: Can handle 5000+ concurrent users

## Component Architecture

### 1. Market Data Pipeline

```
┌──────────────┐      ZMQ:5556      ┌─────────────────┐      ZMQ:5560      ┌──────────────┐
│  MT5 EA      │ ──────PUSH────────>│ Telemetry Bridge│ ──────PUB──────────>│ Subscribers  │
│ (Remote)     │                     │   (Bridge)      │                     │ (Patterns)   │
└──────────────┘                     └─────────────────┘                     └──────────────┘
```

**Components:**
- **MT5 EA**: MetaTrader 5 Expert Advisor pushing tick data
- **Telemetry Bridge**: Receives and redistributes market data
- **Subscribers**: Pattern detectors consuming market feed

**Data Format:**
```json
{
  "type": "TICK",
  "symbol": "EURUSD",
  "bid": 1.09875,
  "ask": 1.09895,
  "time": "2025.09.11 12:34:56.789"
}
```

### 2. Signal Generation Layer

```
┌─────────────────┐
│  Elite Guard    │───┐
│  (SMC Patterns) │   │
└─────────────────┘   │     ZMQ:5557
                      ├────────PUB──────────> Signal Relay ──> WebApp API
┌─────────────────┐   │                            │
│ Pattern Detector│───┤                            ├──> Telegram
│   (6 Patterns)  │   │                            │
└─────────────────┘   │                            └──> Database
                      │
┌─────────────────┐   │
│  ML Filter      │───┘
│  (XGBoost)      │
└─────────────────┘
```

**Pattern Detection Algorithms:**
1. **Liquidity Sweep Reversal**: Institutional stop hunts
2. **Order Block Bounce**: Accumulation zone reactions
3. **Fair Value Gap Fill**: Price inefficiency corrections
4. **VCB Breakout**: Volatility compression breakouts
5. **Momentum Burst**: Acceleration patterns
6. **BB Scalp**: Bollinger Band mean reversion

### 3. Execution Pipeline

```
User Request ──> WebApp ──> Validation ──> Fire Queue ──> Command Router ──> EA ──> MT5
     │              │            │             │              │             │        │
     └──────────────┴────────────┴─────────────┴──────────────┴─────────────┴────────┘
                                         Confirmation Path
```

**Fire Command Flow:**
1. User initiates trade (manual/auto)
2. WebApp validates permissions
3. BittenCore applies risk rules
4. Fire command enqueued to IPC
5. Command Router forwards to EA
6. EA executes on MT5
7. Confirmation sent back

### 4. Data Architecture

```sql
┌─────────────┐     ┌──────────┐     ┌─────────┐
│   signals   │────>│ missions │────>│  fires  │
└─────────────┘     └──────────┘     └─────────┘
       │                  │                │
       ├──────────────────┼────────────────┤
       │                  │                │
┌──────▼──────┐    ┌──────▼──────┐  ┌─────▼────┐
│ ml_training │    │ user_modes  │  │ outcomes │
└─────────────┘    └─────────────┘  └──────────┘
```

**Core Tables:**
- **signals**: Pattern detection results
- **missions**: User-specific trade opportunities
- **fires**: Executed trades
- **outcomes**: Trade results (WIN/LOSS)
- **ml_training**: Performance data for ML
- **user_modes**: User tier and permissions

### 5. Machine Learning Pipeline

```
Signal Generation ──> Outcome Tracking ──> Feature Engineering ──> Model Training
        │                    │                      │                    │
        └────────────────────┴──────────────────────┴────────────────────┘
                            Feedback Loop (24hr cycle)
```

**ML Components:**
- **XGBoost Model**: Pattern performance prediction
- **Feature Set**: Pattern, symbol, session, volatility, spread
- **Training Cycle**: Daily retraining with new outcomes
- **Threshold Adjustment**: Automatic confidence tuning

## Network Architecture

### ZMQ Port Allocation

| Port | Type | Direction | Purpose |
|------|------|-----------|---------|
| 5555 | ROUTER | Bidirectional | EA command routing |
| 5556 | PULL | EA → Server | Market data ingestion |
| 5557 | PUB | Patterns → System | Signal publishing |
| 5558 | PULL | EA → Server | Trade confirmations |
| 5560 | PUB | Bridge → Patterns | Market data relay |

### IPC Sockets

| Socket | Type | Purpose |
|--------|------|---------|
| /tmp/bitten_cmdqueue | PUSH/PULL | Fire command queue |

### HTTP Endpoints

| Port | Service | Purpose |
|------|---------|---------|
| 8888 | WebApp | Main API and dashboard |
| 8899 | Commander Throne | Admin interface |
| 8890 | Tracking Dashboard | Signal monitoring |
| 8891 | Confidence Analysis | Performance analytics |

## Process Management

### PM2 Ecosystem

```javascript
module.exports = {
  apps: [
    {
      name: 'elite_guard',
      script: 'elite_guard_with_citadel.py',
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    },
    {
      name: 'command_router',
      script: 'command_router.py',
      instances: 1,
      autorestart: true
    },
    // ... other services
  ]
}
```

### Process Dependencies

```
zmq_telemetry_bridge (must start first)
    ├── elite_guard
    ├── pattern_detectors
    └── outcome_tracker

webapp_server
    ├── command_router
    ├── confirm_listener
    └── fire_executor
```

## Security Architecture

### Authentication Flow

```
User ──> Telegram Bot ──> User Registry ──> Tier Check ──> Access Grant
             │                  │                │              │
             └──────────────────┴────────────────┴──────────────┘
                              Verification Path
```

### Permission Tiers

| Tier | Access Level | Features |
|------|--------------|----------|
| PRESS | Read-only | View signals only |
| GLADIATOR | Basic | Manual fire, 1 slot |
| REAPER | Standard | Manual fire, 2 slots |
| COMMANDER | Advanced | Auto-fire, 3 slots |
| FANG | Premium | BITMODE, 3 slots |
| FANG+ | Elite | All features |

## Performance Optimizations

### Caching Strategy

- **Candle Cache**: 60-second persistence of market data
- **Signal Cache**: Mission files for 15-minute TTL
- **User Cache**: Registry with 5-minute refresh
- **ML Model Cache**: Loaded once, refreshed daily

### Resource Management

- **Connection Pooling**: ZMQ context sharing
- **Database Connection**: Single SQLite connection per process
- **Memory Management**: Circular buffers for tick data
- **CPU Optimization**: Numpy vectorization for calculations

## Monitoring & Observability

### Health Checks

```python
# System health endpoint
GET /healthz
{
  "status": "healthy",
  "uptime": 3600,
  "signals_24h": 127,
  "active_fires": 3,
  "ea_connected": true
}
```

### Logging Architecture

```
Application Logs ──> PM2 Logs ──> Log Rotation ──> Archive
       │                │              │              │
       └────────────────┴──────────────┴──────────────┘
                     Analysis Pipeline
```

### Performance Metrics

- **Signal Generation Rate**: 3-10 signals/hour
- **Fire Execution Latency**: <100ms
- **Pattern Detection Time**: <50ms per symbol
- **ML Inference Time**: <10ms per signal

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────┐
│         Production Server           │
│          134.199.204.67             │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      PM2 Process Manager     │   │
│  │  ┌────────┐  ┌────────┐     │   │
│  │  │Elite   │  │Command │     │   │
│  │  │Guard   │  │Router  │     │   │
│  │  └────────┘  └────────┘     │   │
│  │  ┌────────┐  ┌────────┐     │   │
│  │  │WebApp  │  │Tracker │     │   │
│  │  └────────┘  └────────┘     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │       SQLite Database        │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    ZMQ Message Broker        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
                    │
                    │ ZMQ
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐      ┌───────▼────────┐
│   MT5 Terminal │      │   MT5 Terminal │
│      (EA)      │      │      (EA)      │
└────────────────┘      └────────────────┘
```

### Backup & Recovery

- **Database Backup**: Daily SQLite backup
- **Configuration Backup**: Git repository
- **Process State**: PM2 dump/restore
- **Candle Cache**: JSON persistence

## Future Architecture Plans

### Planned Enhancements

1. **Redis Integration**: Replace IPC with Redis queues
2. **WebSocket Support**: Real-time signal streaming
3. **Kubernetes Migration**: Container orchestration
4. **Multi-Region Support**: Geographic distribution
5. **GraphQL API**: Advanced query capabilities

### Scalability Roadmap

- **Phase 1**: Current - Single server, 1000 users
- **Phase 2**: Q4 2025 - Load balancer, 5000 users
- **Phase 3**: Q1 2026 - Multi-region, 20000 users
- **Phase 4**: Q2 2026 - Full cloud native, unlimited scale

## Disaster Recovery

### Failure Scenarios

| Component | Impact | Recovery Time | Procedure |
|-----------|--------|---------------|-----------|
| Elite Guard | No signals | <30s | PM2 auto-restart |
| Command Router | No trades | <30s | PM2 auto-restart |
| Database | Data loss | <5min | Restore from backup |
| Network | Full outage | <10min | Failover server |

### Backup Procedures

```bash
# Daily backup script
#!/bin/bash
cp bitten.db bitten.db.backup_$(date +%Y%m%d)
pm2 save
git add -A && git commit -m "Daily backup"
git push origin main
```

## Development Guidelines

### Code Organization

```
/root/HydraX-v2/
├── src/
│   ├── bitten_core/       # Core trading logic
│   ├── patterns/           # Pattern detectors
│   └── ml/                 # ML components
├── tools/                  # Utility scripts
├── webapp/                 # Web interface
├── tests/                  # Test suite
└── docs/                   # Documentation
```

### Testing Strategy

- **Unit Tests**: Pattern detection logic
- **Integration Tests**: ZMQ message flow
- **End-to-End Tests**: Full trade cycle
- **Performance Tests**: Load testing

### Deployment Process

1. **Development**: Local testing
2. **Staging**: Test server validation
3. **Production**: Blue-green deployment
4. **Rollback**: PM2 version control

## Conclusion

The BITTEN architecture is designed for reliability, scalability, and performance. The modular design allows for independent component updates without system downtime, while the event-driven architecture ensures real-time responsiveness to market conditions.

For implementation details, refer to the specific component documentation in the `/docs` directory.