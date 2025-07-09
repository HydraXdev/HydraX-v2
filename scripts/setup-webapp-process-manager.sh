#!/bin/bash

# BITTEN WebApp Process Manager Setup Script
# Sets up comprehensive process management for the webapp service

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="bitten-webapp"
WATCHDOG_SERVICE="bitten-webapp-watchdog"
MONITORING_SERVICE="bitten-monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Function to create directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p /var/log/bitten/webapp
    mkdir -p /var/lib/bitten
    mkdir -p /etc/bitten
    mkdir -p "$PROJECT_DIR/logs"
    
    # Set proper permissions
    chown -R root:root /var/log/bitten
    chown -R root:root /var/lib/bitten
    chown -R root:root /etc/bitten
    
    log "Directories created successfully"
}

# Function to install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        curl \
        bc \
        mailutils \
        logrotate \
        netstat-nat \
        htop \
        nginx \
        supervisor
    
    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    fi
    
    log "System dependencies installed"
}

# Function to install Python dependencies
install_python_dependencies() {
    log "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    pip3 install -r requirements.txt
    
    log "Python dependencies installed"
}

# Function to install PM2
install_pm2() {
    log "Installing PM2..."
    
    if ! command -v pm2 &> /dev/null; then
        npm install -g pm2
        
        # Setup PM2 startup
        pm2 startup systemd -u root --hp /root
        
        log "PM2 installed and configured"
    else
        log "PM2 already installed"
    fi
}

# Function to setup SystemD services
setup_systemd_services() {
    log "Setting up SystemD services..."
    
    # Copy service files
    cp "$PROJECT_DIR/systemd/$SERVICE_NAME.service" /etc/systemd/system/
    cp "$PROJECT_DIR/systemd/$WATCHDOG_SERVICE.service" /etc/systemd/system/
    
    # Copy existing monitoring service if it exists
    if [ -f "$PROJECT_DIR/systemd/$MONITORING_SERVICE.service" ]; then
        cp "$PROJECT_DIR/systemd/$MONITORING_SERVICE.service" /etc/systemd/system/
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    log "SystemD services configured"
}

# Function to setup logrotate
setup_logrotate() {
    log "Setting up log rotation..."
    
    # Copy logrotate configuration
    cp /etc/logrotate.d/bitten-webapp /etc/logrotate.d/bitten-webapp.bak 2>/dev/null || true
    
    # Test logrotate configuration
    if logrotate -d /etc/logrotate.d/bitten-webapp; then
        log "Log rotation configured successfully"
    else
        error "Log rotation configuration failed"
        return 1
    fi
}

# Function to setup nginx reverse proxy
setup_nginx() {
    log "Setting up nginx reverse proxy..."
    
    # Create nginx configuration
    cat > /etc/nginx/sites-available/bitten-webapp << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check specific settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8888/health;
        access_log off;
    }
    
    # Metrics endpoint
    location /metrics {
        proxy_pass http://127.0.0.1:8888/metrics;
        access_log off;
    }
}
EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/bitten-webapp /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if nginx -t; then
        systemctl reload nginx
        log "Nginx configured successfully"
    else
        error "Nginx configuration failed"
        return 1
    fi
}

# Function to setup monitoring integration
setup_monitoring_integration() {
    log "Setting up monitoring integration..."
    
    # Create monitoring configuration
    cat > /etc/bitten/monitoring.conf << 'EOF'
[webapp]
service_name = bitten-webapp
health_check_url = http://localhost:8888/health
check_interval = 60
max_failures = 3
recovery_timeout = 300

[alerts]
email_enabled = true
webhook_enabled = false
alert_cooldown = 900

[thresholds]
cpu_warning = 80
cpu_critical = 95
memory_warning = 80
memory_critical = 95
disk_warning = 80
disk_critical = 95
response_time_warning = 5000
response_time_critical = 10000
EOF
    
    log "Monitoring integration configured"
}

# Function to test the setup
test_setup() {
    log "Testing the setup..."
    
    # Test webapp control script
    if "$PROJECT_DIR/scripts/webapp-control.sh" status; then
        log "Webapp control script test passed"
    else
        warn "Webapp control script test failed"
    fi
    
    # Test health check
    if "$PROJECT_DIR/scripts/webapp-watchdog.py" check; then
        log "Health check test passed"
    else
        warn "Health check test failed (service may not be running)"
    fi
    
    # Test logrotate
    if logrotate -d /etc/logrotate.d/bitten-webapp > /dev/null 2>&1; then
        log "Logrotate test passed"
    else
        warn "Logrotate test failed"
    fi
    
    log "Setup testing completed"
}

# Function to start services
start_services() {
    local method="${1:-systemd}"
    
    log "Starting services with method: $method"
    
    case $method in
        systemd)
            # Enable and start services
            systemctl enable $SERVICE_NAME
            systemctl enable $WATCHDOG_SERVICE
            
            systemctl start $SERVICE_NAME
            sleep 5
            systemctl start $WATCHDOG_SERVICE
            
            # Check status
            if systemctl is-active --quiet $SERVICE_NAME; then
                log "SystemD webapp service started successfully"
            else
                error "Failed to start SystemD webapp service"
                return 1
            fi
            
            if systemctl is-active --quiet $WATCHDOG_SERVICE; then
                log "SystemD watchdog service started successfully"
            else
                warn "Watchdog service failed to start"
            fi
            ;;
            
        pm2)
            # Start with PM2
            cd "$PROJECT_DIR"
            pm2 start pm2.config.js --env production
            pm2 save
            
            # Start watchdog manually
            nohup "$PROJECT_DIR/scripts/webapp-watchdog.py" > /var/log/bitten/webapp/watchdog.log 2>&1 &
            
            log "PM2 services started successfully"
            ;;
            
        *)
            error "Unknown startup method: $method"
            return 1
            ;;
    esac
}

# Function to show status
show_status() {
    log "Current system status:"
    
    echo ""
    echo "=== SystemD Services ==="
    systemctl status $SERVICE_NAME --no-pager || echo "Service not found"
    echo ""
    systemctl status $WATCHDOG_SERVICE --no-pager || echo "Watchdog not found"
    
    echo ""
    echo "=== PM2 Services ==="
    pm2 list || echo "PM2 not running"
    
    echo ""
    echo "=== Health Check ==="
    if curl -f -s http://localhost:8888/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ WebApp is healthy${NC}"
    else
        echo -e "${RED}✗ WebApp is not responding${NC}"
    fi
    
    echo ""
    echo "=== Resource Usage ==="
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "Disk: $(df / | tail -1 | awk '{print $5}')"
}

# Function to cleanup (for testing/reinstall)
cleanup() {
    log "Cleaning up existing installation..."
    
    # Stop services
    systemctl stop $SERVICE_NAME 2>/dev/null || true
    systemctl stop $WATCHDOG_SERVICE 2>/dev/null || true
    pm2 stop all 2>/dev/null || true
    
    # Disable services
    systemctl disable $SERVICE_NAME 2>/dev/null || true
    systemctl disable $WATCHDOG_SERVICE 2>/dev/null || true
    
    # Remove service files
    rm -f /etc/systemd/system/$SERVICE_NAME.service
    rm -f /etc/systemd/system/$WATCHDOG_SERVICE.service
    
    # Remove nginx configuration
    rm -f /etc/nginx/sites-enabled/bitten-webapp
    rm -f /etc/nginx/sites-available/bitten-webapp
    
    systemctl daemon-reload
    
    log "Cleanup completed"
}

# Main function
main() {
    check_root
    
    case "${1:-install}" in
        install)
            log "Installing BITTEN WebApp Process Manager..."
            create_directories
            install_dependencies
            install_python_dependencies
            install_pm2
            setup_systemd_services
            setup_logrotate
            setup_nginx
            setup_monitoring_integration
            test_setup
            log "Installation completed successfully"
            ;;
            
        start)
            start_services "${2:-systemd}"
            ;;
            
        stop)
            systemctl stop $SERVICE_NAME 2>/dev/null || true
            systemctl stop $WATCHDOG_SERVICE 2>/dev/null || true
            pm2 stop all 2>/dev/null || true
            log "Services stopped"
            ;;
            
        status)
            show_status
            ;;
            
        cleanup)
            cleanup
            ;;
            
        test)
            test_setup
            ;;
            
        *)
            echo "Usage: $0 {install|start|stop|status|cleanup|test}"
            echo ""
            echo "Commands:"
            echo "  install    Install and configure process manager"
            echo "  start      Start services (systemd|pm2)"
            echo "  stop       Stop all services"
            echo "  status     Show system status"
            echo "  cleanup    Remove installation"
            echo "  test       Test the setup"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function
main "$@"