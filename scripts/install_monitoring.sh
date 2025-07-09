#!/bin/bash
# BITTEN Monitoring System Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BITTEN_USER="bitten"
BITTEN_GROUP="bitten"
INSTALL_DIR="/root/HydraX-v2"
LOG_DIR="/var/log/bitten"
LIB_DIR="/var/lib/bitten"
CONFIG_DIR="/etc/bitten"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BITTEN Monitoring System Installation${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Create system user and group
echo -e "${YELLOW}Creating system user and group...${NC}"
if ! id -u "$BITTEN_USER" > /dev/null 2>&1; then
    useradd -r -s /bin/false -d "$LIB_DIR" "$BITTEN_USER"
    echo -e "${GREEN}Created user: $BITTEN_USER${NC}"
else
    echo -e "${YELLOW}User $BITTEN_USER already exists${NC}"
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$LOG_DIR" "$LIB_DIR" "$CONFIG_DIR"
mkdir -p "$LOG_DIR/archive"
mkdir -p "$LIB_DIR/backups"
mkdir -p "$CONFIG_DIR/ssl"

# Set permissions
chown -R "$BITTEN_USER:$BITTEN_GROUP" "$LOG_DIR" "$LIB_DIR"
chmod 755 "$LOG_DIR" "$LIB_DIR" "$CONFIG_DIR"
chmod 750 "$CONFIG_DIR/ssl"

echo -e "${GREEN}Directories created successfully${NC}"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r "$INSTALL_DIR/requirements.txt"
pip3 install -r "$INSTALL_DIR/requirements_monitoring.txt"

# Install additional monitoring dependencies
pip3 install psutil plotly pandas gunicorn

echo -e "${GREEN}Dependencies installed successfully${NC}"

# Create configuration files
echo -e "${YELLOW}Creating configuration files...${NC}"

# Main monitoring configuration
cat > "$CONFIG_DIR/monitoring.conf" << EOF
[monitoring]
log_level = INFO
log_dir = $LOG_DIR
db_path = $LIB_DIR/monitoring.db
target_signals_per_day = 65
target_win_rate = 85.0
check_interval = 30

[database]
type = postgresql
host = localhost
port = 5432
user = bitten_user
password = change_me
database = bitten_db

[redis]
host = localhost
port = 6379
db = 0

[alerts]
email_enabled = true
email_smtp_server = localhost
email_smtp_port = 587
email_from = alerts@bitten.local
email_to = admin@bitten.local

slack_enabled = false
slack_webhook_url = 

telegram_enabled = false
telegram_bot_token = 
telegram_chat_id = 

[mt5_farm]
url = http://129.212.185.102:8001
timeout = 10
retry_count = 3

[health_checks]
check_interval = 30
timeout = 5
enabled_checks = database,redis,mt5_farm,webapp,telegram
EOF

# Dashboard configuration
cat > "$CONFIG_DIR/dashboard.conf" << EOF
[dashboard]
host = 0.0.0.0
port = 8080
debug = false
template_dir = $INSTALL_DIR/src/monitoring/templates
static_dir = $INSTALL_DIR/src/monitoring/static

[security]
secret_key = $(openssl rand -hex 32)
session_timeout = 3600
max_connections = 100

[performance]
cache_timeout = 300
max_chart_points = 1000
refresh_interval = 30
EOF

# Health check configuration
cat > "$CONFIG_DIR/health.conf" << EOF
[health]
api_port = 8888
check_interval = 30
timeout = 5
max_retries = 3

[endpoints]
webapp = http://localhost:9001/health
telegram = http://localhost:9001/status
mt5_farm = http://129.212.185.102:8001/status

[thresholds]
cpu_warning = 80
cpu_critical = 90
memory_warning = 85
memory_critical = 95
disk_warning = 85
disk_critical = 95
response_time_warning = 1000
response_time_critical = 5000
EOF

# Set configuration permissions
chown -R "$BITTEN_USER:$BITTEN_GROUP" "$CONFIG_DIR"
chmod 600 "$CONFIG_DIR"/*.conf

echo -e "${GREEN}Configuration files created${NC}"

# Create server entry points
echo -e "${YELLOW}Creating server entry points...${NC}"

# Main monitoring server
cat > "$INSTALL_DIR/src/monitoring/main_monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
BITTEN Monitoring System Main Server
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitoring.performance_monitor import get_performance_monitor
from src.monitoring.health_check import create_health_check_system, get_default_config
from src.monitoring.alert_system import get_alert_manager
from src.monitoring.win_rate_monitor import get_win_rate_monitor
from src.monitoring.log_manager import get_log_manager
from src.monitoring.logging_config import setup_service_logging

class MonitoringServer:
    """Main monitoring server"""
    
    def __init__(self):
        self.logger = setup_service_logging("bitten-monitoring")
        self.running = False
        
        # Initialize components
        self.performance_monitor = get_performance_monitor()
        self.health_manager, _ = create_health_check_system(get_default_config())
        self.alert_manager = get_alert_manager()
        self.win_rate_monitor = get_win_rate_monitor(self.alert_manager)
        self.log_manager = get_log_manager()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self):
        """Start monitoring server"""
        self.logger.info("Starting BITTEN Monitoring System...")
        self.running = True
        
        try:
            # Start all components
            self.performance_monitor.start()
            self.health_manager.start_monitoring()
            self.win_rate_monitor.start()
            self.log_manager.start()
            
            self.logger.info("All monitoring components started successfully")
            
            # Keep running until shutdown
            while self.running:
                import time
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in monitoring server: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop monitoring server"""
        self.logger.info("Stopping BITTEN Monitoring System...")
        
        # Stop all components
        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.stop()
        if hasattr(self, 'health_manager'):
            self.health_manager.stop_monitoring()
        if hasattr(self, 'win_rate_monitor'):
            self.win_rate_monitor.stop()
        if hasattr(self, 'log_manager'):
            self.log_manager.stop()
        
        self.logger.info("Monitoring system stopped")

if __name__ == "__main__":
    server = MonitoringServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
EOF

# Dashboard server
cat > "$INSTALL_DIR/src/monitoring/dashboard_server.py" << 'EOF'
#!/usr/bin/env python3
"""
BITTEN Dashboard Server
"""

import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitoring.dashboard import create_dashboard_app, get_default_dashboard_config
from src.monitoring.logging_config import setup_service_logging

class DashboardServer:
    """Dashboard server wrapper"""
    
    def __init__(self):
        self.logger = setup_service_logging("bitten-dashboard")
        self.dashboard = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    def start(self):
        """Start dashboard server"""
        self.logger.info("Starting BITTEN Dashboard Server...")
        
        try:
            # Create dashboard app
            config = get_default_dashboard_config()
            self.dashboard = create_dashboard_app(config)
            
            # Run dashboard
            self.dashboard.run(
                host=config.get('host', '0.0.0.0'),
                port=config.get('port', 8080),
                debug=config.get('debug', False)
            )
            
        except Exception as e:
            self.logger.error(f"Error starting dashboard: {e}")
            raise

if __name__ == "__main__":
    server = DashboardServer()
    server.start()
EOF

# Health check server
cat > "$INSTALL_DIR/src/monitoring/health_check_server.py" << 'EOF'
#!/usr/bin/env python3
"""
BITTEN Health Check Server
"""

import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitoring.health_check import create_health_check_system, get_default_config
from src.monitoring.logging_config import setup_service_logging

class HealthCheckServer:
    """Health check server wrapper"""
    
    def __init__(self):
        self.logger = setup_service_logging("bitten-health-check")
        self.health_manager = None
        self.health_api = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        if self.health_manager:
            self.health_manager.stop_monitoring()
        sys.exit(0)
    
    def start(self):
        """Start health check server"""
        self.logger.info("Starting BITTEN Health Check Server...")
        
        try:
            # Create health check system
            config = get_default_config()
            config['api_port'] = 8888
            
            self.health_manager, self.health_api = create_health_check_system(config)
            
            # Start monitoring
            self.health_manager.start_monitoring()
            
            # Run API server
            self.health_api.run()
            
        except Exception as e:
            self.logger.error(f"Error starting health check server: {e}")
            raise

if __name__ == "__main__":
    server = HealthCheckServer()
    server.start()
EOF

# Make scripts executable
chmod +x "$INSTALL_DIR/src/monitoring/main_monitor.py"
chmod +x "$INSTALL_DIR/src/monitoring/dashboard_server.py"
chmod +x "$INSTALL_DIR/src/monitoring/health_check_server.py"

echo -e "${GREEN}Server entry points created${NC}"

# Install systemd service files
echo -e "${YELLOW}Installing systemd service files...${NC}"

cp "$INSTALL_DIR/systemd/bitten-monitoring.service" /etc/systemd/system/
cp "$INSTALL_DIR/systemd/bitten-dashboard.service" /etc/systemd/system/
cp "$INSTALL_DIR/systemd/bitten-health-check.service" /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}Service files installed${NC}"

# Create log rotation configuration
echo -e "${YELLOW}Setting up log rotation...${NC}"

cat > /etc/logrotate.d/bitten-monitoring << EOF
$LOG_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $BITTEN_USER $BITTEN_GROUP
    sharedscripts
    postrotate
        systemctl reload bitten-monitoring.service > /dev/null 2>&1 || true
        systemctl reload bitten-dashboard.service > /dev/null 2>&1 || true
        systemctl reload bitten-health-check.service > /dev/null 2>&1 || true
    endscript
}

$LOG_DIR/archive/*.log.gz {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 644 $BITTEN_USER $BITTEN_GROUP
}
EOF

echo -e "${GREEN}Log rotation configured${NC}"

# Create monitoring cron jobs
echo -e "${YELLOW}Setting up cron jobs...${NC}"

cat > /etc/cron.d/bitten-monitoring << EOF
# BITTEN Monitoring System Cron Jobs

# Daily performance report generation
0 1 * * * $BITTEN_USER /usr/bin/python3 -c "
import sys; sys.path.insert(0, '$INSTALL_DIR/src');
from monitoring.performance_monitor import get_performance_monitor;
from datetime import datetime, timedelta;
monitor = get_performance_monitor();
monitor.start();
report = monitor.report_generator.generate_daily_report(datetime.now() - timedelta(days=1));
print('Daily report generated:', report.performance_score);
monitor.stop()
" >> $LOG_DIR/daily_reports.log 2>&1

# Weekly log cleanup
0 2 * * 0 $BITTEN_USER find $LOG_DIR -name "*.log" -mtime +7 -exec gzip {} \; >> $LOG_DIR/cleanup.log 2>&1

# Monthly archive cleanup
0 3 1 * * $BITTEN_USER find $LOG_DIR/archive -name "*.gz" -mtime +90 -delete >> $LOG_DIR/cleanup.log 2>&1

# Health check every 5 minutes
*/5 * * * * $BITTEN_USER /usr/bin/curl -s http://localhost:8888/health > /dev/null || echo "Health check failed at \$(date)" >> $LOG_DIR/health_check_failures.log
EOF

echo -e "${GREEN}Cron jobs configured${NC}"

# Create nginx configuration for dashboard
echo -e "${YELLOW}Creating nginx configuration...${NC}"

cat > /etc/nginx/sites-available/bitten-monitoring << EOF
server {
    listen 80;
    server_name monitoring.bitten.local;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Main dashboard
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8888/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Static files
    location /static/ {
        alias $INSTALL_DIR/src/monitoring/static/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Logs (restricted access)
    location /logs/ {
        alias $LOG_DIR/;
        allow 127.0.0.1;
        allow ::1;
        deny all;
        autoindex on;
        auth_basic "BITTEN Monitoring Logs";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

# Create SSL version if certificates exist
if [ -f /etc/ssl/certs/bitten.crt ] && [ -f /etc/ssl/private/bitten.key ]; then
    cat > /etc/nginx/sites-available/bitten-monitoring-ssl << EOF
server {
    listen 443 ssl http2;
    server_name monitoring.bitten.local;

    ssl_certificate /etc/ssl/certs/bitten.crt;
    ssl_certificate_key /etc/ssl/private/bitten.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Main dashboard
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8888/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Static files
    location /static/ {
        alias $INSTALL_DIR/src/monitoring/static/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Logs (restricted access)
    location /logs/ {
        alias $LOG_DIR/;
        allow 127.0.0.1;
        allow ::1;
        deny all;
        autoindex on;
        auth_basic "BITTEN Monitoring Logs";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name monitoring.bitten.local;
    return 301 https://\$server_name\$request_uri;
}
EOF

    ln -sf /etc/nginx/sites-available/bitten-monitoring-ssl /etc/nginx/sites-enabled/
    echo -e "${GREEN}SSL configuration created${NC}"
else
    ln -sf /etc/nginx/sites-available/bitten-monitoring /etc/nginx/sites-enabled/
    echo -e "${YELLOW}SSL certificates not found, using HTTP configuration${NC}"
fi

# Test nginx configuration
if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}Nginx configuration updated${NC}"
else
    echo -e "${RED}Nginx configuration error${NC}"
fi

# Create monitoring utilities
echo -e "${YELLOW}Creating monitoring utilities...${NC}"

# Monitoring status script
cat > "$INSTALL_DIR/scripts/monitoring_status.sh" << 'EOF'
#!/bin/bash
# BITTEN Monitoring System Status

echo "=== BITTEN Monitoring System Status ==="
echo

# Check service status
echo "Service Status:"
echo "  Monitoring Service: $(systemctl is-active bitten-monitoring.service)"
echo "  Dashboard Service:  $(systemctl is-active bitten-dashboard.service)"
echo "  Health Check API:   $(systemctl is-active bitten-health-check.service)"
echo

# Check ports
echo "Port Status:"
echo "  Dashboard (8080):   $(netstat -ln | grep :8080 | wc -l) listeners"
echo "  Health API (8888):  $(netstat -ln | grep :8888 | wc -l) listeners"
echo

# Check log files
echo "Log Files:"
echo "  Monitoring logs:    $(find /var/log/bitten -name "*.log" | wc -l) files"
echo "  Total log size:     $(du -sh /var/log/bitten | cut -f1)"
echo "  Latest entries:     $(tail -n 1 /var/log/bitten/bitten-monitoring.log 2>/dev/null || echo "No entries")"
echo

# Check database
echo "Database Status:"
if [ -f /var/lib/bitten/monitoring.db ]; then
    echo "  Performance DB:     $(stat -c%s /var/lib/bitten/monitoring.db) bytes"
else
    echo "  Performance DB:     Not found"
fi
echo

# Check health endpoints
echo "Health Endpoints:"
echo "  Local Health Check: $(curl -s http://localhost:8888/health | jq -r .status 2>/dev/null || echo "Failed")"
echo "  Dashboard Health:   $(curl -s http://localhost:8080/api/status | jq -r .status 2>/dev/null || echo "Failed")"
echo

# Check recent alerts
echo "Recent Activity:"
echo "  Recent errors:      $(grep -c ERROR /var/log/bitten/*.log 2>/dev/null || echo "0")"
echo "  Recent warnings:    $(grep -c WARNING /var/log/bitten/*.log 2>/dev/null || echo "0")"
echo
EOF

chmod +x "$INSTALL_DIR/scripts/monitoring_status.sh"

# Restart services script
cat > "$INSTALL_DIR/scripts/restart_monitoring.sh" << 'EOF'
#!/bin/bash
# BITTEN Monitoring System Restart

echo "Restarting BITTEN Monitoring Services..."

# Stop services
systemctl stop bitten-dashboard.service
systemctl stop bitten-health-check.service
systemctl stop bitten-monitoring.service

# Wait a moment
sleep 2

# Start services
systemctl start bitten-monitoring.service
systemctl start bitten-health-check.service
systemctl start bitten-dashboard.service

# Check status
echo "Service Status:"
systemctl is-active bitten-monitoring.service
systemctl is-active bitten-health-check.service
systemctl is-active bitten-dashboard.service

echo "Monitoring services restarted"
EOF

chmod +x "$INSTALL_DIR/scripts/restart_monitoring.sh"

echo -e "${GREEN}Monitoring utilities created${NC}"

# Enable services
echo -e "${YELLOW}Enabling services...${NC}"

systemctl enable bitten-monitoring.service
systemctl enable bitten-dashboard.service
systemctl enable bitten-health-check.service

echo -e "${GREEN}Services enabled${NC}"

# Final setup
echo -e "${YELLOW}Performing final setup...${NC}"

# Create monitoring user home directory
mkdir -p /home/"$BITTEN_USER"
chown "$BITTEN_USER:$BITTEN_GROUP" /home/"$BITTEN_USER"

# Create initial database
sudo -u "$BITTEN_USER" python3 -c "
import sys; sys.path.insert(0, '$INSTALL_DIR/src');
from monitoring.performance_monitor import PerformanceMonitor;
from monitoring.win_rate_monitor import WinRateDatabase;
from monitoring.alert_system import AlertDatabase;
print('Initializing databases...');
pm = PerformanceMonitor();
wr = WinRateDatabase();
ad = AlertDatabase();
print('Databases initialized');
"

echo -e "${GREEN}Final setup completed${NC}"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}BITTEN Monitoring System Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update database credentials in $CONFIG_DIR/monitoring.conf"
echo "2. Configure alert notifications in $CONFIG_DIR/monitoring.conf"
echo "3. Start services: systemctl start bitten-monitoring.service"
echo "4. Check status: $INSTALL_DIR/scripts/monitoring_status.sh"
echo "5. Access dashboard: http://localhost:8080"
echo "6. Health check API: http://localhost:8888/health"
echo
echo -e "${YELLOW}Service Commands:${NC}"
echo "  Start:   systemctl start bitten-monitoring.service"
echo "  Stop:    systemctl stop bitten-monitoring.service"
echo "  Status:  systemctl status bitten-monitoring.service"
echo "  Logs:    journalctl -u bitten-monitoring.service -f"
echo "  Restart: $INSTALL_DIR/scripts/restart_monitoring.sh"
echo
echo -e "${YELLOW}Configuration Files:${NC}"
echo "  Main:      $CONFIG_DIR/monitoring.conf"
echo "  Dashboard: $CONFIG_DIR/dashboard.conf"
echo "  Health:    $CONFIG_DIR/health.conf"
echo
echo -e "${YELLOW}Log Files:${NC}"
echo "  Location:  $LOG_DIR"
echo "  Archive:   $LOG_DIR/archive"
echo "  Cleanup:   /etc/logrotate.d/bitten-monitoring"
echo
echo -e "${GREEN}Installation completed successfully!${NC}"