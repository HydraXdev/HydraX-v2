#!/bin/bash
# Setup script for Press Pass Monitoring System

set -e

echo "Setting up Press Pass Monitoring System..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r /root/HydraX-v2/requirements_monitoring.txt

# Create monitoring user
echo "Creating monitoring user..."
if ! id -u bitten > /dev/null 2>&1; then
    useradd -r -s /bin/false bitten
fi

# Create directories
echo "Creating required directories..."
mkdir -p /var/www/html/analytics
mkdir -p /var/log
chown -R bitten:bitten /var/www/html/analytics
chown bitten:bitten /var/log/press_pass_monitoring*.log 2>/dev/null || true

# Copy systemd service file
echo "Installing systemd service..."
cp /root/HydraX-v2/scripts/press_pass_monitoring.service /etc/systemd/system/

# Create environment file for sensitive configurations
echo "Creating environment configuration..."
cat > /etc/press_pass_monitoring.env << EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=bitten_user
DB_PASSWORD=your_password_here
DB_NAME=bitten_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Output Configuration
OUTPUT_DIR=/var/www/html/analytics
ANOMALY_SENSITIVITY=2.5

# Alert Configuration (uncomment and configure as needed)
# ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# EMAIL_ALERTS_ENABLED=true
# ALERT_EMAIL_RECIPIENTS=team@example.com
EOF

chmod 600 /etc/press_pass_monitoring.env
chown bitten:bitten /etc/press_pass_monitoring.env

# Update systemd service to use environment file
sed -i '/\[Service\]/a EnvironmentFile=/etc/press_pass_monitoring.env' /etc/systemd/system/press_pass_monitoring.service

# Create log rotation configuration
echo "Setting up log rotation..."
cat > /etc/logrotate.d/press_pass_monitoring << EOF
/var/log/press_pass_monitoring*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 bitten bitten
    sharedscripts
    postrotate
        systemctl reload press_pass_monitoring.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Create monitoring cron jobs
echo "Setting up cron jobs..."
cat > /etc/cron.d/press_pass_monitoring << EOF
# Press Pass Monitoring System Cron Jobs

# Daily XP reset at midnight GMT
0 0 * * * postgres psql -d bitten_db -c "SELECT reset_daily_shadow_xp();" >> /var/log/xp_reset.log 2>&1

# Weekly cleanup of old Press Pass data (Sundays at 3 AM GMT)
0 3 * * 0 postgres psql -d bitten_db -c "SELECT cleanup_old_press_pass_data(90);" >> /var/log/press_pass_cleanup.log 2>&1

# Generate hourly performance snapshot
0 * * * * bitten /usr/bin/curl -s http://localhost/analytics/api/snapshot >> /var/log/analytics_snapshot.log 2>&1
EOF

# Create nginx configuration for analytics dashboard
echo "Setting up nginx configuration..."
cat > /etc/nginx/sites-available/analytics << EOF
server {
    listen 80;
    server_name analytics.yourdomain.com;

    root /var/www/html/analytics;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
        
        # Enable CORS for dashboard access
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept";
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/analytics /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start the service
echo "Starting Press Pass Monitoring Service..."
systemctl enable press_pass_monitoring.service
systemctl start press_pass_monitoring.service

# Check service status
sleep 2
if systemctl is-active --quiet press_pass_monitoring.service; then
    echo "Press Pass Monitoring System started successfully!"
    echo ""
    echo "Service Status:"
    systemctl status press_pass_monitoring.service --no-pager
    echo ""
    echo "Next steps:"
    echo "1. Update database credentials in /etc/press_pass_monitoring.env"
    echo "2. Configure alert webhooks if needed"
    echo "3. Access the analytics dashboard at http://analytics.yourdomain.com"
    echo "4. Monitor logs at /var/log/press_pass_monitoring.log"
else
    echo "Error: Service failed to start. Check logs at /var/log/press_pass_monitoring_error.log"
    exit 1
fi