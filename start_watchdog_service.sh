#!/bin/bash
# Start Clone Farm Watchdog as System Service

echo "🐕 DEPLOYING CLONE FARM WATCHDOG SERVICE"
echo "========================================"

# Create systemd service file
cat > /etc/systemd/system/clone-farm-watchdog.service << EOF
[Unit]
Description=Clone Farm Watchdog Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
WorkingDirectory=/root/HydraX-v2
ExecStart=/usr/bin/python3 /root/HydraX-v2/clone_farm_watchdog.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=clone-farm-watchdog

# Resource limits
MemoryMax=1G
CPUQuota=50%

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/root /var/log /tmp

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service file created"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd configuration reloaded"

# Enable service
systemctl enable clone-farm-watchdog.service
echo "✅ Watchdog service enabled for auto-start"

# Start service
systemctl start clone-farm-watchdog.service
echo "✅ Watchdog service started"

# Check status
sleep 2
if systemctl is-active --quiet clone-farm-watchdog.service; then
    echo "🎯 WATCHDOG SERVICE SUCCESSFULLY DEPLOYED"
    echo ""
    echo "📊 Service Status:"
    systemctl status clone-farm-watchdog.service --no-pager -l
    echo ""
    echo "📋 Management Commands:"
    echo "  Status:  systemctl status clone-farm-watchdog"
    echo "  Stop:    systemctl stop clone-farm-watchdog"
    echo "  Start:   systemctl start clone-farm-watchdog"
    echo "  Restart: systemctl restart clone-farm-watchdog"
    echo "  Logs:    journalctl -u clone-farm-watchdog -f"
    echo ""
    echo "📁 Log Files:"
    echo "  System:   journalctl -u clone-farm-watchdog"
    echo "  App:      tail -f /var/log/clone_farm_watchdog.log"
    echo "  Status:   ls /var/log/clone_farm_status_*.json"
    echo ""
else
    echo "❌ WATCHDOG SERVICE FAILED TO START"
    echo "🔍 Checking logs..."
    journalctl -u clone-farm-watchdog.service --no-pager -l
    exit 1
fi

# Create log rotation
cat > /etc/logrotate.d/clone-farm-watchdog << EOF
/var/log/clone_farm_watchdog.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}

/var/log/clone_farm_status_*.json {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
}
EOF

echo "✅ Log rotation configured"

# Create monitoring cron jobs
cat > /etc/cron.d/clone-farm-monitoring << EOF
# Clone Farm Monitoring Cron Jobs

# Run integrity check every 15 minutes
*/15 * * * * root /root/HydraX-v2/check_master_integrity.sh >> /var/log/master_clone_integrity.log 2>&1

# Generate daily status report
0 6 * * * root /usr/bin/python3 /root/HydraX-v2/clone_farm_watchdog.py --once && echo "Daily watchdog check completed at \$(date)" >> /var/log/daily_checks.log

# Clean old status reports weekly
0 2 * * 0 root find /var/log -name "clone_farm_status_*.json" -mtime +30 -delete
EOF

echo "✅ Monitoring cron jobs installed"

echo ""
echo "🎯 WATCHDOG DEPLOYMENT COMPLETE"
echo "================================"
echo ""
echo "✅ Service running and monitoring:"
echo "  - Master clone integrity"
echo "  - Required processes"
echo "  - System resources"
echo "  - User clone health"
echo "  - Webapp endpoints"
echo ""
echo "✅ Automatic features:"
echo "  - Process restart on failure"
echo "  - Resource monitoring"
echo "  - Log rotation"
echo "  - Daily health checks"
echo ""
echo "🐕 Clone Farm Watchdog is now providing uninterrupted service monitoring!"
echo ""