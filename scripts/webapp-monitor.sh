#!/bin/bash

# BITTEN WebApp Monitoring Script
# Monitors the webapp service and performs automatic recovery

set -e

# Configuration
SERVICE_NAME="bitten-webapp"
PM2_APP_NAME="bitten-webapp"
HEALTH_CHECK_URL="http://localhost:8888/health"
CHECK_INTERVAL=60
MAX_FAILURES=3
LOG_FILE="/var/log/bitten/webapp/monitor.log"
ALERT_EMAIL=""
WEBHOOK_URL=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

error() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

warn() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    
    # Send email alert if configured
    if [ ! -z "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # Send webhook alert if configured
    if [ ! -z "$WEBHOOK_URL" ]; then
        curl -X POST -H "Content-Type: application/json" \
             -d "{\"text\":\"$subject: $message\"}" \
             "$WEBHOOK_URL" 2>/dev/null || true
    fi
    
    log "Alert sent: $subject"
}

# Function to check service health
check_health() {
    local response
    local http_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 30 "$HEALTH_CHECK_URL" 2>/dev/null)
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$http_code" -eq 200 ]; then
        # Parse response for detailed health info
        local health_data=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
        local status=$(echo "$health_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
        
        if [ "$status" = "healthy" ]; then
            return 0
        else
            warn "Service reports unhealthy status: $status"
            return 1
        fi
    else
        error "Health check failed with HTTP code: $http_code"
        return 1
    fi
}

# Function to check system resources
check_resources() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    local memory_usage=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    # Check critical thresholds
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        warn "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        warn "High memory usage: ${memory_usage}%"
    fi
    
    if [ "$disk_usage" -gt 90 ]; then
        warn "High disk usage: ${disk_usage}%"
    fi
    
    log "System resources - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
}

# Function to attempt service recovery
attempt_recovery() {
    local recovery_method="$1"
    
    log "Attempting recovery using $recovery_method..."
    
    case "$recovery_method" in
        systemd)
            systemctl restart "$SERVICE_NAME"
            ;;
        pm2)
            pm2 restart "$PM2_APP_NAME"
            ;;
        *)
            error "Unknown recovery method: $recovery_method"
            return 1
            ;;
    esac
    
    # Wait for service to start
    sleep 10
    
    # Check if recovery was successful
    if check_health; then
        log "Recovery successful using $recovery_method"
        send_alert "Service Recovery Successful" "The $SERVICE_NAME service has been successfully recovered using $recovery_method"
        return 0
    else
        error "Recovery failed using $recovery_method"
        return 1
    fi
}

# Function to perform comprehensive recovery
perform_recovery() {
    log "Starting service recovery process..."
    
    # Try SystemD recovery first
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        if attempt_recovery "systemd"; then
            return 0
        fi
    fi
    
    # Try PM2 recovery
    if pm2 describe "$PM2_APP_NAME" &>/dev/null; then
        if attempt_recovery "pm2"; then
            return 0
        fi
    fi
    
    # If both fail, send critical alert
    error "All recovery attempts failed"
    send_alert "CRITICAL: Service Recovery Failed" "All recovery attempts for $SERVICE_NAME have failed. Manual intervention required."
    return 1
}

# Function to collect diagnostic information
collect_diagnostics() {
    local diag_file="/tmp/webapp_diagnostics_$(date +%Y%m%d_%H%M%S).txt"
    
    log "Collecting diagnostic information..."
    
    {
        echo "=== BITTEN WebApp Diagnostics ==="
        echo "Date: $(date)"
        echo ""
        
        echo "=== System Information ==="
        uname -a
        echo ""
        
        echo "=== SystemD Service Status ==="
        systemctl status "$SERVICE_NAME" --no-pager || echo "SystemD service not found"
        echo ""
        
        echo "=== PM2 Status ==="
        pm2 describe "$PM2_APP_NAME" || echo "PM2 service not found"
        echo ""
        
        echo "=== Process Information ==="
        ps aux | grep -E "(webapp_server|python)" | grep -v grep
        echo ""
        
        echo "=== Network Connections ==="
        netstat -tulpn | grep :8888
        echo ""
        
        echo "=== System Resources ==="
        free -h
        df -h
        echo ""
        
        echo "=== Recent Logs ==="
        journalctl -u "$SERVICE_NAME" --no-pager -n 50 || echo "No SystemD logs available"
        echo ""
        
        echo "=== Application Logs ==="
        tail -n 50 /var/log/bitten/webapp/*.log 2>/dev/null || echo "No application logs available"
        
    } > "$diag_file"
    
    log "Diagnostics saved to: $diag_file"
    echo "$diag_file"
}

# Main monitoring loop
monitor_loop() {
    local failure_count=0
    
    log "Starting webapp monitoring (check interval: ${CHECK_INTERVAL}s, max failures: $MAX_FAILURES)"
    
    while true; do
        if check_health; then
            if [ $failure_count -gt 0 ]; then
                log "Service recovered after $failure_count failures"
                failure_count=0
            fi
            
            # Check system resources
            check_resources
            
        else
            failure_count=$((failure_count + 1))
            error "Health check failed (failure $failure_count/$MAX_FAILURES)"
            
            if [ $failure_count -ge $MAX_FAILURES ]; then
                warn "Maximum failures reached, attempting recovery..."
                
                # Collect diagnostics before recovery
                diag_file=$(collect_diagnostics)
                
                if perform_recovery; then
                    failure_count=0
                else
                    # If recovery fails, wait longer before next check
                    log "Recovery failed, waiting 5 minutes before next check..."
                    sleep 300
                fi
            fi
        fi
        
        sleep $CHECK_INTERVAL
    done
}

# Function to run one-time check
run_check() {
    log "Performing one-time health check..."
    
    if check_health; then
        log "Service is healthy"
        check_resources
        exit 0
    else
        error "Service is unhealthy"
        collect_diagnostics
        exit 1
    fi
}

# Function to setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Install monitoring dependencies
    if ! command -v bc &> /dev/null; then
        apt-get update && apt-get install -y bc
    fi
    
    if ! command -v mail &> /dev/null; then
        apt-get update && apt-get install -y mailutils
    fi
    
    # Create systemd service for monitoring
    cat > /etc/systemd/system/bitten-webapp-monitor.service << EOF
[Unit]
Description=BITTEN WebApp Monitor
After=network.target bitten-webapp.service
Requires=bitten-webapp.service

[Service]
Type=simple
User=root
ExecStart=/root/HydraX-v2/scripts/webapp-monitor.sh monitor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable bitten-webapp-monitor
    
    log "Monitoring setup complete"
}

# Main function
main() {
    case "${1:-monitor}" in
        monitor)
            monitor_loop
            ;;
        check)
            run_check
            ;;
        setup)
            setup_monitoring
            ;;
        diagnostics)
            collect_diagnostics
            ;;
        *)
            echo "Usage: $0 {monitor|check|setup|diagnostics}"
            echo ""
            echo "Commands:"
            echo "  monitor      Start continuous monitoring (default)"
            echo "  check        Perform one-time health check"
            echo "  setup        Setup monitoring service"
            echo "  diagnostics  Collect diagnostic information"
            exit 1
            ;;
    esac
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Run main function
main "$@"