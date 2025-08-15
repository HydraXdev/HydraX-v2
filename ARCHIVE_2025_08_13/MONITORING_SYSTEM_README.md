# BITTEN Production Monitoring System

## Overview

This comprehensive monitoring system provides real-time tracking and alerting for the BITTEN trading system, focusing on signal generation performance (65 signals/day target), win rate monitoring (85%+ target), and overall system health.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             BITTEN MONITORING SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Performance   │  │   Health Check  │  │   Alert System  │  │   Win Rate      │   │
│  │   Monitor       │  │   System        │  │                 │  │   Monitor       │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Log Manager   │  │   Dashboard     │  │   System        │  │   Notification  │   │
│  │   & Rotation    │  │   Web UI        │  │   Integrator    │  │   Channels      │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                              DATA STORAGE LAYER                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Performance   │  │   Health Check  │  │   Alert         │  │   Win Rate      │   │
│  │   Database      │  │   Database      │  │   Database      │  │   Database      │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Structured Logging System
- **JSON-formatted logs** with structured fields
- **Service-specific loggers** for different components
- **Performance logging** with context managers and decorators
- **Automatic log rotation** with configurable size and retention
- **Centralized log management** with search and analysis capabilities

### 2. Performance Monitoring
- **Signal generation tracking** with 65 signals/day target
- **TCS threshold optimization** with automatic adjustment
- **Trade execution monitoring** with timing metrics
- **Real-time performance dashboards** with charts and metrics
- **Historical performance analysis** with trend tracking

### 3. Health Check System
- **Multi-service health monitoring** (database, Redis, MT5 farm, webapp)
- **Automated health checks** with configurable intervals
- **RESTful health endpoints** for external monitoring
- **Service dependency tracking** with failure detection
- **Kubernetes-compatible** readiness and liveness probes

### 4. Alert System
- **Multi-channel notifications** (email, Slack, Telegram, webhook)
- **Configurable alert rules** with thresholds and cooldowns
- **Alert suppression** and acknowledgment features
- **Escalation policies** based on severity levels
- **Historical alert tracking** with resolution times

### 5. Win Rate Monitoring
- **Real-time win rate calculation** with 85%+ target
- **Symbol-specific tracking** for all trading pairs
- **Trend analysis** with improving/declining detection
- **Trading session analysis** (London, NY, Asian, Overlap)
- **Consecutive win/loss tracking** with statistics

### 6. Dashboard System
- **Real-time web dashboard** with auto-refresh
- **Interactive charts** using Plotly.js
- **System health overview** with status indicators
- **Performance metrics** with historical trends
- **Alert management** with acknowledgment capabilities

### 7. Log Management
- **Automated log rotation** with compression
- **Configurable retention policies** 
- **Log analysis** with metrics extraction
- **Daily report generation** with summaries
- **Archive management** with cleanup policies

## Installation

### Quick Installation
```bash
cd /root/HydraX-v2
sudo ./scripts/install_monitoring.sh
```

### Manual Installation
```bash
# Install dependencies
pip3 install -r requirements_monitoring.txt

# Create system user
sudo useradd -r -s /bin/false bitten

# Create directories
sudo mkdir -p /var/log/bitten /var/lib/bitten /etc/bitten
sudo chown -R bitten:bitten /var/log/bitten /var/lib/bitten

# Install service files
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable bitten-monitoring.service
sudo systemctl enable bitten-dashboard.service
sudo systemctl enable bitten-health-check.service
```

## Configuration

### Main Configuration (`/etc/bitten/monitoring.conf`)
```ini
[monitoring]
log_level = INFO
log_dir = /var/log/bitten
target_signals_per_day = 65
target_win_rate = 85.0
check_interval = 30

[database]
type = postgresql
host = localhost
port = 5432
user = bitten_user
password = your_password
database = bitten_db

[alerts]
email_enabled = true
email_smtp_server = localhost
email_from = alerts@bitten.local
email_to = admin@bitten.local

slack_enabled = true
slack_webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL

[mt5_farm]
url = http://129.212.185.102:8001
timeout = 10
```

### Dashboard Configuration (`/etc/bitten/dashboard.conf`)
```ini
[dashboard]
host = 0.0.0.0
port = 8080
debug = false

[security]
secret_key = your_secret_key
session_timeout = 3600
```

## Usage

### Starting Services
```bash
# Start all monitoring services
sudo systemctl start bitten-monitoring.service
sudo systemctl start bitten-dashboard.service
sudo systemctl start bitten-health-check.service

# Check status
sudo systemctl status bitten-monitoring.service
```

### Accessing Dashboard
- **Web Dashboard**: http://localhost:8080
- **Health Check API**: http://localhost:8888/health
- **Detailed Health**: http://localhost:8888/health/detailed
- **Metrics API**: http://localhost:8080/api/metrics/current

### Monitoring Commands
```bash
# Check system status
./scripts/monitoring_status.sh

# Restart services
./scripts/restart_monitoring.sh

# View logs
journalctl -u bitten-monitoring.service -f
tail -f /var/log/bitten/bitten-monitoring.log

# Check health
curl http://localhost:8888/health | jq
```

## Integration with BITTEN Core

### Automatic Integration
```python
from src.monitoring.system_integrator import setup_bitten_monitoring

# In your main BITTEN startup
bitten_core = BittenCore()
monitoring = setup_bitten_monitoring(bitten_core)
```

### Manual Integration
```python
from src.monitoring import (
    get_performance_monitor, 
    get_win_rate_monitor,
    get_alert_manager
)

# Record signal generation
performance_monitor = get_performance_monitor()
performance_monitor.signal_monitor.record_signal_generation(
    signal_count=3,
    pairs_active=5,
    generation_time_ms=150.0,
    tcs_threshold=72.0,
    market_conditions="volatile",
    success_rate=0.85,
    avg_confidence=0.78
)

# Record trade execution
performance_monitor.trade_monitor.record_trade_execution(
    trade_id="TRADE001",
    symbol="GBPUSD",
    direction="BUY",
    entry_price=1.2650,
    lot_size=0.1,
    execution_time_ms=45.0,
    success=True
)

# Record completed trade for win rate
win_rate_monitor = get_win_rate_monitor()
win_rate_monitor.record_trade(
    trade_id="TRADE001",
    symbol="GBPUSD",
    direction="BUY",
    entry_price=1.2650,
    exit_price=1.2680,
    entry_time=datetime(2025, 7, 9, 10, 0, 0),
    exit_time=datetime(2025, 7, 9, 10, 30, 0),
    lot_size=0.1,
    pnl=30.0,
    strategy="london_breakout"
)
```

## Monitoring Targets

### Signal Generation
- **Target**: 65 signals per day across 10 pairs
- **Warning**: Below 52 signals (80% of target)
- **Critical**: Below 39 signals (60% of target)
- **TCS Threshold**: Auto-adjusted between 65-85%

### Win Rate
- **Target**: 85%+ win rate
- **Warning**: Below 80% win rate
- **Critical**: Below 75% win rate
- **Minimum Trades**: 10 trades for reliable analysis

### System Health
- **CPU Warning**: Above 80% usage
- **Memory Warning**: Above 85% usage
- **Response Time Warning**: Above 1000ms
- **Error Rate Critical**: Above 5%

## Alert Rules

### Default Alert Rules
1. **Signal Generation Below Target** (Medium)
2. **Win Rate Below Target** (High)
3. **System Resource High Usage** (Medium)
4. **Service Down** (Critical)
5. **High Error Rate** (High)
6. **MT5 Farm Connection Issues** (Critical)

### Custom Alert Rules
```python
from src.monitoring.alert_system import AlertRule, AlertSeverity

# Create custom alert rule
rule = AlertRule(
    id="custom_metric_alert",
    name="Custom Metric Alert",
    description="Alert when custom metric exceeds threshold",
    service="my-service",
    metric="custom_metric",
    condition=">",
    threshold=100.0,
    severity=AlertSeverity.HIGH,
    duration_seconds=300,
    cooldown_seconds=1800
)

alert_manager = get_alert_manager()
alert_manager.add_alert_rule(rule)
```

## API Endpoints

### Health Check Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health status
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/metrics` - Prometheus-style metrics

### Dashboard API Endpoints
- `GET /api/status` - API status
- `GET /api/metrics/current` - Current metrics
- `GET /api/metrics/historical` - Historical data
- `GET /api/charts/signal_generation` - Signal generation chart
- `GET /api/charts/win_rate` - Win rate chart
- `GET /api/alerts/active` - Active alerts
- `POST /api/alerts/acknowledge/<alert_id>` - Acknowledge alert

## File Structure

```
/root/HydraX-v2/src/monitoring/
├── __init__.py                 # Package initialization
├── logging_config.py           # Structured logging system
├── performance_monitor.py      # Performance monitoring
├── health_check.py             # Health check system
├── alert_system.py             # Alert management
├── win_rate_monitor.py         # Win rate monitoring
├── log_manager.py              # Log rotation and management
├── dashboard.py                # Web dashboard
├── system_integrator.py        # BITTEN core integration
├── main_monitor.py             # Main monitoring server
├── dashboard_server.py         # Dashboard server
└── health_check_server.py      # Health check server

/etc/bitten/
├── monitoring.conf             # Main configuration
├── dashboard.conf              # Dashboard configuration
└── health.conf                 # Health check configuration

/var/log/bitten/
├── bitten-monitoring.log       # Main monitoring logs
├── bitten-dashboard.log        # Dashboard logs
├── bitten-health-check.log     # Health check logs
├── signals.log                 # Signal generation logs
├── trades.log                  # Trade execution logs
├── health.log                  # Health monitoring logs
├── performance.log             # Performance metrics
└── archive/                    # Archived logs

/var/lib/bitten/
├── performance.db              # Performance metrics database
├── win_rate.db                 # Win rate database
├── alerts.db                   # Alert history database
└── backups/                    # Database backups
```

## Maintenance

### Daily Tasks
- Review dashboard for anomalies
- Check active alerts
- Verify signal generation targets
- Monitor win rate performance

### Weekly Tasks
- Review log summaries
- Check system resource usage
- Verify backup integrity
- Update alert thresholds if needed

### Monthly Tasks
- Analyze performance trends
- Review alert effectiveness
- Clean up old logs and databases
- Update monitoring configurations

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   ```bash
   # Check logs
   journalctl -u bitten-monitoring.service -n 50
   
   # Check configuration
   sudo -u bitten python3 -c "import src.monitoring; print('OK')"
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   sudo -u bitten python3 -c "
   from src.monitoring.performance_monitor import PerformanceDatabase;
   db = PerformanceDatabase();
   print('Database OK')
   "
   ```

3. **Dashboard Not Loading**
   ```bash
   # Check dashboard service
   systemctl status bitten-dashboard.service
   
   # Check port binding
   netstat -tlnp | grep 8080
   ```

4. **Alerts Not Sending**
   ```bash
   # Check alert configuration
   grep -A 10 "\[alerts\]" /etc/bitten/monitoring.conf
   
   # Test alert manager
   sudo -u bitten python3 -c "
   from src.monitoring.alert_system import get_alert_manager;
   am = get_alert_manager();
   print('Alert manager OK')
   "
   ```

### Performance Issues
- Check CPU and memory usage
- Review log file sizes
- Verify database performance
- Monitor network connections

## Security Considerations

- **Service User**: Runs as dedicated `bitten` user
- **File Permissions**: Restricted access to logs and databases
- **Network Security**: Firewall rules for dashboard access
- **Log Sanitization**: Sensitive data filtering
- **Authentication**: Basic auth for log access

## Backup and Recovery

### Automated Backups
- Daily database backups
- Weekly log archives
- Monthly full system backups

### Recovery Procedures
1. Stop monitoring services
2. Restore database from backup
3. Restore configuration files
4. Restart services
5. Verify functionality

## License

This monitoring system is part of the BITTEN trading platform. All rights reserved.

## Support

For issues or questions:
1. Check logs: `/var/log/bitten/`
2. Review configuration: `/etc/bitten/`
3. Run status check: `./scripts/monitoring_status.sh`
4. Contact system administrator

---

**Last Updated**: July 9, 2025
**Version**: 1.0.0
**Author**: BITTEN Development Team