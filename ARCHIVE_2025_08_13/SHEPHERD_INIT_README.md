# SHEPHERD Initialization System

This directory contains production-ready initialization scripts for the SHEPHERD intelligent code analysis system.

## Components

### 1. shepherd_init.sh
Main initialization script that:
- Checks Python version (requires 3.8+)
- Installs dependencies
- Creates required directories
- Builds initial index
- Starts watch mode for real-time updates
- Runs health checks

**Usage:**
```bash
# Basic initialization
./shepherd_init.sh

# With continuous monitoring
./shepherd_init.sh --monitor
```

### 2. shepherd.service
Systemd service file for automatic startup with:
- Auto-restart on failure
- Resource limits (2GB memory, 50% CPU)
- Security hardening
- Proper logging to journald
- Health check integration

**Installation:**
```bash
# Install service
sudo ./install_shepherd_service.sh

# Start service
sudo systemctl start shepherd

# Enable auto-start on boot
sudo systemctl enable shepherd

# Check status
sudo systemctl status shepherd

# View logs
sudo journalctl -u shepherd -f
```

### 3. shepherd_healthcheck.py
Comprehensive health monitoring that checks:
- Process status
- Index freshness and integrity
- System resources (CPU, memory, disk)
- Log file sizes
- File permissions
- Network connectivity

**Usage:**
```bash
# Single health check
./shepherd_healthcheck.py

# JSON output
./shepherd_healthcheck.py --json

# Continuous monitoring
./shepherd_healthcheck.py --continuous --interval 60

# Startup check (used by systemd)
./shepherd_healthcheck.py --startup
```

## Directory Structure

```
/root/HydraX-v2/
├── bitten/
│   ├── core/
│   │   └── shepherd/         # SHEPHERD core modules
│   └── data/
│       └── shepherd/         # Index and state files
│           ├── shepherd_index.json
│           ├── shepherd_watch.pid
│           ├── health_state.json
│           ├── file_hashes.json
│           ├── indexes/     # Index versions
│           ├── cache/       # Cached data
│           └── backups/     # Index backups
└── logs/
    └── shepherd/            # Log files
        ├── indexer/        # Indexing logs
        ├── query/          # Query logs
        ├── health/         # Health check logs
        └── watch.log       # Watch mode logs
```

## Configuration

### Environment Variables
- `PYTHON_BIN`: Python executable path (default: python3)
- `SHEPHERD_ALERT_EMAIL`: Email for critical alerts
- `SMTP_HOST`: SMTP server for alerts
- `SMTP_PORT`: SMTP port (default: 25)
- `SMTP_USER`: SMTP username
- `SMTP_PASS`: SMTP password

### Thresholds (in shepherd_healthcheck.py)
- `MAX_INDEX_AGE_HOURS`: 24 hours
- `MAX_MEMORY_PERCENT`: 80%
- `MAX_CPU_PERCENT`: 90%
- `MAX_DISK_PERCENT`: 90%
- `MIN_FREE_DISK_GB`: 1 GB
- `MAX_LOG_SIZE_MB`: 100 MB

## Health Status

The health check system uses three status levels:
- **healthy**: Everything is working correctly
- **warning**: Non-critical issues that should be addressed
- **critical**: Serious issues requiring immediate attention

Critical issues trigger email alerts if configured.

## Monitoring

### Systemd Integration
When running as a systemd service:
- Watchdog timer ensures the service is responsive
- Automatic restart on failure (max 5 times in 5 minutes)
- Resource limits prevent runaway processes

### Metrics
The health check tracks:
- Component count in index
- Index age and size
- Process CPU and memory usage
- Disk space availability
- Log file sizes
- Response times

## Troubleshooting

### SHEPHERD won't start
1. Check Python version: `python3 --version` (needs 3.8+)
2. Check permissions: `ls -la /root/HydraX-v2/bitten/data/shepherd`
3. Check logs: `journalctl -u shepherd -n 100`

### High resource usage
1. Check index size: `du -h /root/HydraX-v2/bitten/data/shepherd/shepherd_index.json`
2. Reduce watch frequency in shepherd_watch.py
3. Increase resource limits in shepherd.service

### Index not updating
1. Check watch process: `ps aux | grep shepherd_watch`
2. Check file permissions in data directory
3. Manually rebuild: `python3 /root/HydraX-v2/bitten/core/shepherd/indexer.py`

### Health check failures
1. Run manual check: `./shepherd_healthcheck.py`
2. Check specific component: `./shepherd_healthcheck.py --json | jq '.results[]'`
3. Review health state: `cat /root/HydraX-v2/bitten/data/shepherd/health_state.json`

## Maintenance

### Daily Tasks
- Monitor health check alerts
- Review log sizes

### Weekly Tasks
- Check index backup count
- Review resource usage trends
- Update thresholds if needed

### Monthly Tasks
- Full index rebuild
- Clean old log files
- Review and optimize queries

## Security Notes

1. The service runs with restricted permissions
2. Write access limited to data and log directories
3. Network access restricted to necessary protocols
4. Consider running as non-root user in production
5. Rotate logs regularly
6. Keep Python dependencies updated

## Support

For issues or questions:
1. Check health status first
2. Review recent logs
3. Verify configuration
4. Check system resources

The SHEPHERD system is designed to be self-monitoring and self-healing, but manual intervention may be required for critical issues.