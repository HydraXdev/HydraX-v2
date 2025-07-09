#!/bin/bash

# BITTEN WebApp Control Script
# Manages the webapp service using both SystemD and PM2

set -e

# Configuration
SERVICE_NAME="bitten-webapp"
PM2_APP_NAME="bitten-webapp"
WORKING_DIR="/root/HydraX-v2"
LOG_DIR="/var/log/bitten/webapp"
HEALTH_CHECK_URL="http://localhost:8888/health"
HEALTH_CHECK_TIMEOUT=30
MAX_RETRIES=3

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

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if service is running
is_systemd_running() {
    systemctl is-active --quiet $SERVICE_NAME 2>/dev/null
}

is_pm2_running() {
    pm2 describe $PM2_APP_NAME 2>/dev/null | grep -q "online"
}

# Function to perform health check
health_check() {
    local retries=0
    
    info "Performing health check..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log "Health check passed"
            return 0
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            warn "Health check failed, retrying in 5 seconds... ($retries/$MAX_RETRIES)"
            sleep 5
        fi
    done
    
    error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Function to wait for service to be ready
wait_for_service() {
    local max_wait=60
    local waited=0
    
    info "Waiting for service to be ready..."
    
    while [ $waited -lt $max_wait ]; do
        if health_check; then
            return 0
        fi
        
        sleep 2
        waited=$((waited + 2))
    done
    
    error "Service did not become ready within $max_wait seconds"
    return 1
}

# Function to create necessary directories
setup_directories() {
    info "Setting up directories..."
    mkdir -p $LOG_DIR
    mkdir -p /var/lib/bitten
    mkdir -p /etc/bitten
    chown -R root:root $LOG_DIR
    chown -R root:root /var/lib/bitten
    chown -R root:root /etc/bitten
}

# Function to install dependencies
install_dependencies() {
    info "Installing dependencies..."
    cd $WORKING_DIR
    pip3 install -r requirements.txt
    
    # Install PM2 if not already installed
    if ! command -v pm2 &> /dev/null; then
        npm install -g pm2
    fi
}

# SystemD management functions
systemd_start() {
    info "Starting $SERVICE_NAME with SystemD..."
    
    # Copy service file if needed
    if [ ! -f /etc/systemd/system/$SERVICE_NAME.service ]; then
        cp $WORKING_DIR/systemd/$SERVICE_NAME.service /etc/systemd/system/
        systemctl daemon-reload
    fi
    
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME
    
    if wait_for_service; then
        log "SystemD service started successfully"
    else
        error "Failed to start SystemD service"
        return 1
    fi
}

systemd_stop() {
    info "Stopping $SERVICE_NAME with SystemD..."
    systemctl stop $SERVICE_NAME
    log "SystemD service stopped"
}

systemd_restart() {
    info "Restarting $SERVICE_NAME with SystemD..."
    systemctl restart $SERVICE_NAME
    
    if wait_for_service; then
        log "SystemD service restarted successfully"
    else
        error "Failed to restart SystemD service"
        return 1
    fi
}

systemd_reload() {
    info "Reloading $SERVICE_NAME with SystemD..."
    systemctl reload $SERVICE_NAME
    log "SystemD service reloaded"
}

systemd_status() {
    systemctl status $SERVICE_NAME --no-pager
}

# PM2 management functions
pm2_start() {
    info "Starting $PM2_APP_NAME with PM2..."
    
    cd $WORKING_DIR
    pm2 start pm2.config.js --env production
    pm2 save
    
    if wait_for_service; then
        log "PM2 service started successfully"
    else
        error "Failed to start PM2 service"
        return 1
    fi
}

pm2_stop() {
    info "Stopping $PM2_APP_NAME with PM2..."
    pm2 stop $PM2_APP_NAME
    log "PM2 service stopped"
}

pm2_restart() {
    info "Restarting $PM2_APP_NAME with PM2..."
    pm2 restart $PM2_APP_NAME
    
    if wait_for_service; then
        log "PM2 service restarted successfully"
    else
        error "Failed to restart PM2 service"
        return 1
    fi
}

pm2_reload() {
    info "Reloading $PM2_APP_NAME with PM2..."
    pm2 reload $PM2_APP_NAME
    
    if wait_for_service; then
        log "PM2 service reloaded successfully"
    else
        error "Failed to reload PM2 service"
        return 1
    fi
}

pm2_status() {
    pm2 describe $PM2_APP_NAME
}

# Deployment functions
deploy() {
    info "Deploying webapp..."
    
    setup_directories
    install_dependencies
    
    # Choose deployment method
    case "${2:-systemd}" in
        systemd)
            systemd_start
            ;;
        pm2)
            pm2_start
            ;;
        *)
            error "Unknown deployment method: $2"
            return 1
            ;;
    esac
    
    log "Deployment completed successfully"
}

# Status and monitoring functions
status() {
    info "Checking service status..."
    
    echo "=== SystemD Status ==="
    if is_systemd_running; then
        echo -e "${GREEN}SystemD service is running${NC}"
        systemd_status
    else
        echo -e "${RED}SystemD service is not running${NC}"
    fi
    
    echo -e "\n=== PM2 Status ==="
    if is_pm2_running; then
        echo -e "${GREEN}PM2 service is running${NC}"
        pm2_status
    else
        echo -e "${RED}PM2 service is not running${NC}"
    fi
    
    echo -e "\n=== Health Check ==="
    if health_check; then
        echo -e "${GREEN}Service is healthy${NC}"
    else
        echo -e "${RED}Service is unhealthy${NC}"
    fi
}

logs() {
    local service_type="${2:-systemd}"
    local lines="${3:-100}"
    
    info "Showing logs for $service_type..."
    
    case $service_type in
        systemd)
            journalctl -u $SERVICE_NAME -n $lines -f
            ;;
        pm2)
            pm2 logs $PM2_APP_NAME --lines $lines
            ;;
        files)
            tail -f $LOG_DIR/*.log
            ;;
        *)
            error "Unknown log type: $service_type"
            return 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    info "Cleaning up..."
    
    # Stop services
    if is_systemd_running; then
        systemd_stop
    fi
    
    if is_pm2_running; then
        pm2_stop
    fi
    
    # Clean logs if requested
    if [ "$2" = "logs" ]; then
        rm -f $LOG_DIR/*.log
        log "Logs cleaned"
    fi
}

# Auto-recovery function
auto_recover() {
    info "Starting auto-recovery process..."
    
    # Check if service is running
    if ! health_check; then
        warn "Service is unhealthy, attempting recovery..."
        
        # Try to restart with SystemD first
        if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
            systemd_restart
            if health_check; then
                log "Auto-recovery successful with SystemD"
                return 0
            fi
        fi
        
        # Try to restart with PM2
        if pm2 describe $PM2_APP_NAME &>/dev/null; then
            pm2_restart
            if health_check; then
                log "Auto-recovery successful with PM2"
                return 0
            fi
        fi
        
        error "Auto-recovery failed"
        return 1
    else
        log "Service is healthy, no recovery needed"
    fi
}

# Main function
main() {
    case "$1" in
        # SystemD commands
        start)
            systemd_start
            ;;
        stop)
            systemd_stop
            ;;
        restart)
            systemd_restart
            ;;
        reload)
            systemd_reload
            ;;
        
        # PM2 commands
        pm2-start)
            pm2_start
            ;;
        pm2-stop)
            pm2_stop
            ;;
        pm2-restart)
            pm2_restart
            ;;
        pm2-reload)
            pm2_reload
            ;;
        
        # Deployment commands
        deploy)
            deploy "$@"
            ;;
        
        # Status and monitoring
        status)
            status
            ;;
        health)
            health_check
            ;;
        logs)
            logs "$@"
            ;;
        
        # Maintenance
        cleanup)
            cleanup "$@"
            ;;
        recover)
            auto_recover
            ;;
        
        # Help
        help|--help|-h)
            echo "Usage: $0 {start|stop|restart|reload|pm2-start|pm2-stop|pm2-restart|pm2-reload|deploy|status|health|logs|cleanup|recover|help}"
            echo ""
            echo "SystemD Commands:"
            echo "  start         Start the service with SystemD"
            echo "  stop          Stop the service with SystemD"
            echo "  restart       Restart the service with SystemD"
            echo "  reload        Reload the service with SystemD"
            echo ""
            echo "PM2 Commands:"
            echo "  pm2-start     Start the service with PM2"
            echo "  pm2-stop      Stop the service with PM2"
            echo "  pm2-restart   Restart the service with PM2"
            echo "  pm2-reload    Reload the service with PM2"
            echo ""
            echo "Deployment Commands:"
            echo "  deploy [systemd|pm2]  Deploy the service (default: systemd)"
            echo ""
            echo "Monitoring Commands:"
            echo "  status        Show service status"
            echo "  health        Perform health check"
            echo "  logs [systemd|pm2|files] [lines]  Show logs"
            echo ""
            echo "Maintenance Commands:"
            echo "  cleanup [logs]  Clean up services and optionally logs"
            echo "  recover       Auto-recover unhealthy service"
            echo ""
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"