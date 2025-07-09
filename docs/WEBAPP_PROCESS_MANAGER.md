# BITTEN WebApp Process Manager

A comprehensive process management system for the BITTEN webapp server running on port 8888. This system provides robust monitoring, auto-restart capabilities, health checks, and multiple deployment options.

## Features

- **Multiple Process Managers**: SystemD and PM2 support
- **Health Monitoring**: Comprehensive health checks with detailed metrics
- **Auto-Recovery**: Automatic restart on failures with intelligent recovery
- **Log Management**: Automated log rotation and centralized logging
- **Security**: Hardened service configuration with proper permissions
- **Monitoring Integration**: Integration with existing BITTEN monitoring system
- **Alerting**: Email and webhook notifications for critical events
- **Resource Monitoring**: CPU, memory, and disk usage tracking

## Quick Start

### Installation

```bash
# Run as root
sudo /root/HydraX-v2/scripts/setup-webapp-process-manager.sh install
```

### Start Services

```bash
# Start with SystemD (recommended)
sudo /root/HydraX-v2/scripts/webapp-control.sh start

# Or start with PM2
sudo /root/HydraX-v2/scripts/webapp-control.sh pm2-start
```

### Check Status

```bash
sudo /root/HydraX-v2/scripts/webapp-control.sh status
```

## System Components

### 1. SystemD Services

#### bitten-webapp.service
Main webapp service with:
- Automatic restart on failure
- Security hardening
- Resource limits
- Health monitoring
- Dependency management

#### bitten-webapp-watchdog.service
Monitoring service that:
- Performs health checks every 60 seconds
- Attempts auto-recovery on failures
- Sends alerts on critical issues
- Collects diagnostic information

### 2. PM2 Configuration

Alternative process manager with:
- Cluster mode support
- Built-in monitoring
- Log management
- Zero-downtime restarts
- Process resurrection

### 3. Health Check Endpoints

The webapp provides several monitoring endpoints:

- `/health` - Comprehensive health check with system metrics
- `/metrics` - Prometheus-compatible metrics
- `/ready` - Readiness probe for orchestration
- `/live` - Liveness probe for orchestration

### 4. Log Management

- Automated log rotation via logrotate
- Centralized logging to `/var/log/bitten/webapp/`
- JSON-formatted logs for easy parsing
- Separate error and output logs

### 5. Monitoring Integration

Integrates with the existing BITTEN monitoring system:
- Performance metrics collection
- Win rate monitoring
- Alert management
- Emergency protocols

## Configuration

### Environment Variables

```bash
# Webapp Configuration
WEBAPP_PORT=8888
WEBAPP_HOST=0.0.0.0
WEBAPP_DEBUG=false
MONITORING_ENABLED=true

# Watchdog Configuration
ALERT_EMAIL=admin@bitten.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
WEBHOOK_URL=https://your-webhook-url.com
```

### Monitoring Thresholds

```bash
# Resource Thresholds
CPU_WARNING=80
CPU_CRITICAL=95
MEMORY_WARNING=80
MEMORY_CRITICAL=95
DISK_WARNING=80
DISK_CRITICAL=95

# Response Time Thresholds
RESPONSE_TIME_WARNING=5000  # milliseconds
RESPONSE_TIME_CRITICAL=10000  # milliseconds
```

## Usage

### Control Script

The main control script provides comprehensive service management:

```bash
# SystemD Commands
./scripts/webapp-control.sh start          # Start with SystemD
./scripts/webapp-control.sh stop           # Stop SystemD service
./scripts/webapp-control.sh restart        # Restart SystemD service
./scripts/webapp-control.sh reload         # Reload SystemD service

# PM2 Commands
./scripts/webapp-control.sh pm2-start      # Start with PM2
./scripts/webapp-control.sh pm2-stop       # Stop PM2 service
./scripts/webapp-control.sh pm2-restart    # Restart PM2 service
./scripts/webapp-control.sh pm2-reload     # Reload PM2 service

# Deployment
./scripts/webapp-control.sh deploy systemd # Deploy with SystemD
./scripts/webapp-control.sh deploy pm2     # Deploy with PM2

# Monitoring
./scripts/webapp-control.sh status         # Show service status
./scripts/webapp-control.sh health         # Perform health check
./scripts/webapp-control.sh logs systemd   # Show SystemD logs
./scripts/webapp-control.sh logs pm2       # Show PM2 logs
./scripts/webapp-control.sh logs files     # Show file logs

# Maintenance
./scripts/webapp-control.sh cleanup        # Clean up services
./scripts/webapp-control.sh recover        # Auto-recover service
```

### Watchdog Script

The watchdog provides advanced monitoring capabilities:

```bash
# Run continuous monitoring
python3 scripts/webapp-watchdog.py

# One-time health check
python3 scripts/webapp-watchdog.py check

# Collect diagnostics
python3 scripts/webapp-watchdog.py diagnostics

# Attempt recovery
python3 scripts/webapp-watchdog.py recover
```

### Monitoring Script

The monitoring script provides basic health checks:

```bash
# Start monitoring
./scripts/webapp-monitor.sh monitor

# One-time check
./scripts/webapp-monitor.sh check

# Setup monitoring service
./scripts/webapp-monitor.sh setup

# Collect diagnostics
./scripts/webapp-monitor.sh diagnostics
```

## Health Checks

### Manual Health Check

```bash
curl http://localhost:8888/health
```

Sample response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-09T10:30:00Z",
  "uptime": 3600,
  "service": "bitten-webapp",
  "version": "1.0.0",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available": 8589934592,
    "disk_percent": 35.7,
    "disk_free": 50000000000
  },
  "process": {
    "pid": 1234,
    "memory_rss": 104857600,
    "memory_vms": 209715200,
    "threads": 4,
    "connections": 2
  },
  "dependencies": {
    "status": "ok",
    "errors": []
  }
}
```

### Metrics Endpoint

```bash
curl http://localhost:8888/metrics
```

Returns Prometheus-compatible metrics for monitoring systems.

## Deployment

### SystemD Deployment (Recommended)

```bash
# Install and configure
sudo ./scripts/setup-webapp-process-manager.sh install

# Start services
sudo ./scripts/webapp-control.sh start

# Enable auto-start on boot
sudo systemctl enable bitten-webapp
sudo systemctl enable bitten-webapp-watchdog
```

### PM2 Deployment

```bash
# Install PM2
npm install -g pm2

# Start with PM2
sudo ./scripts/webapp-control.sh pm2-start

# Save PM2 configuration
pm2 save

# Setup PM2 startup
pm2 startup
```

### Docker Deployment (Future)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8888/health || exit 1

CMD ["python", "webapp_server.py"]
```

## Monitoring and Alerting

### Email Alerts

Configure email alerts by setting environment variables:

```bash
export ALERT_EMAIL=admin@bitten.com
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

### Webhook Alerts

Configure webhook alerts for integration with Slack, Discord, etc.:

```bash
export WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Monitoring Dashboard

Access monitoring information via:

- SystemD: `journalctl -u bitten-webapp -f`
- PM2: `pm2 monit`
- Health endpoint: `curl http://localhost:8888/health`
- Metrics: `curl http://localhost:8888/metrics`

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   journalctl -u bitten-webapp -n 50
   
   # Check dependencies
   python3 -c "from signal_storage import get_latest_signal; print('OK')"
   
   # Check port availability
   netstat -tulpn | grep 8888
   ```

2. **High resource usage**
   ```bash
   # Check process status
   ps aux | grep webapp_server
   
   # Monitor resources
   htop
   
   # Check logs for errors
   tail -f /var/log/bitten/webapp/error.log
   ```

3. **Health check failing**
   ```bash
   # Test health endpoint
   curl -v http://localhost:8888/health
   
   # Check dependencies
   python3 scripts/webapp-watchdog.py diagnostics
   
   # Manual recovery
   python3 scripts/webapp-watchdog.py recover
   ```

### Log Locations

- SystemD logs: `journalctl -u bitten-webapp`
- Application logs: `/var/log/bitten/webapp/`
- PM2 logs: `~/.pm2/logs/`
- Watchdog logs: `/var/log/bitten/webapp/watchdog.log`
- Monitor logs: `/var/log/bitten/webapp/monitor.log`

### Performance Tuning

1. **Increase resource limits**
   ```bash
   # Edit service file
   sudo systemctl edit bitten-webapp
   
   # Add overrides
   [Service]
   MemoryLimit=4G
   CPUQuota=400%
   ```

2. **Optimize PM2 configuration**
   ```javascript
   // In pm2.config.js
   {
     instances: 2,  // Use multiple instances
     exec_mode: 'cluster',  // Enable cluster mode
     max_memory_restart: '1G'  // Restart on memory limit
   }
   ```

## Security

### Service Security

- Non-privileged user execution (where possible)
- Restricted file system access
- Network restrictions
- No new privileges
- Private temporary directories

### Access Control

- Health endpoints are restricted to localhost by default
- Nginx reverse proxy with proper headers
- Log file permissions properly configured
- Service files protected from modification

## Integration

### Existing Monitoring System

The process manager integrates with the existing BITTEN monitoring system:

```python
from src.monitoring.system_integrator import get_monitoring_integrator

# Get monitoring integrator
integrator = get_monitoring_integrator()

# Start monitoring
integrator.start_monitoring()

# Record trade
integrator.record_trade_close(...)
```

### Custom Monitoring

Add custom monitoring hooks:

```python
# In webapp_server.py
from src.monitoring.system_integrator import get_monitoring_integrator

integrator = get_monitoring_integrator()

@app.before_request
def before_request():
    # Record request metrics
    integrator.record_request_start()

@app.after_request
def after_request(response):
    # Record response metrics
    integrator.record_request_end(response.status_code)
    return response
```

## Maintenance

### Regular Tasks

1. **Check logs weekly**
   ```bash
   # Check for errors
   grep -i error /var/log/bitten/webapp/*.log
   
   # Check disk usage
   du -h /var/log/bitten/
   ```

2. **Update dependencies monthly**
   ```bash
   pip3 install -r requirements.txt --upgrade
   npm update -g pm2
   ```

3. **Test recovery procedures**
   ```bash
   # Test automatic recovery
   sudo killall -9 python3
   # Wait for recovery
   sleep 60
   # Check status
   ./scripts/webapp-control.sh status
   ```

### Backup Procedures

1. **Configuration backup**
   ```bash
   tar -czf bitten-webapp-config-$(date +%Y%m%d).tar.gz \
     /etc/systemd/system/bitten-webapp* \
     /etc/logrotate.d/bitten-webapp \
     /etc/bitten/ \
     /root/HydraX-v2/pm2.config.js
   ```

2. **Log backup**
   ```bash
   tar -czf bitten-webapp-logs-$(date +%Y%m%d).tar.gz \
     /var/log/bitten/webapp/
   ```

## Support

For issues and questions:

1. Check the logs first
2. Run diagnostics: `python3 scripts/webapp-watchdog.py diagnostics`
3. Check system status: `./scripts/webapp-control.sh status`
4. Review this documentation
5. Contact the BITTEN development team

## Version History

- v1.0.0 - Initial release with SystemD and PM2 support
- v1.1.0 - Added advanced monitoring and alerting
- v1.2.0 - Integrated with existing monitoring system
- v1.3.0 - Added comprehensive health checks and metrics