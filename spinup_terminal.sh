#!/bin/bash
#=================================================================
# HydraX MT5 Terminal Provisioning System
# 
# This script provides one-line deployment of MT5 terminals with
# automatic credential injection and Docker container management.
#
# Features:
# - Automatic Docker image building (if needed)
# - MT5 broker credential injection
# - Port allocation and management
# - Container lifecycle management
# - VNC access setup for remote debugging
# - Socket bridge configuration
#
# Usage:
#   ./spinup_terminal.sh --login 123456 --pass "password" --server "Demo-Server" --port 9009 --label USER1
#
# Requirements:
# - Docker installed and running
# - Sufficient system resources for MT5 + Wine
# - Network access for MT5 broker connections
#
# Output:
# - Running Docker container with MT5 terminal
# - Socket bridge listening on specified port
# - VNC server for remote access
# - Automatic EA attachment via templates
#=================================================================

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default values
LOGIN=""
PASS=""
SERVER=""
PORT="9013"
LABEL="USER_DEFAULT"

# Display usage
show_usage() {
    cat << EOF
Usage: $0 --login LOGIN --pass PASSWORD --server SERVER --port PORT --label LABEL

Required Arguments:
  --login LOGIN     MT5 login credentials
  --pass PASSWORD   MT5 password  
  --server SERVER   MT5 broker server
  --port PORT       Socket bridge port (default: 9013)
  --label LABEL     User label for container naming

Example:
  $0 --login 843859 --pass "Ao4@brz64erHaG" --server "Coinexx-Demo" --port 9013 --label USER_23

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --login)
                LOGIN="$2"
                shift 2
                ;;
            --pass)
                PASS="$2"
                shift 2
                ;;
            --server)
                SERVER="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --label)
                LABEL="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required parameters
    if [[ -z "$LOGIN" || -z "$PASS" || -z "$SERVER" ]]; then
        log_error "Missing required parameters!"
        show_usage
        exit 1
    fi
}

# Generate login.ini for this user
generate_login_config() {
    local config_file="$1"
    
    log_info "Generating login configuration..."
    
    cat > "$config_file" << EOF
[Server]
Name=$SERVER
Server=$SERVER

[Account]
Login=$LOGIN
Password=$PASS
SavePassword=1

[Common]
Login=$LOGIN
Password=$PASS
Server=$SERVER

[StartUp]
Login=$LOGIN
Password=$PASS
Server=$SERVER
AutoLogin=1
EOF
    
    log_success "Login configuration generated"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found! Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running! Please start Docker."
        exit 1
    fi
}

# Check if port is available
check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        log_error "Port $PORT already in use!"
        exit 1
    fi
}

# Build Docker image if it doesn't exist
build_image() {
    local image_name="hydrax-mt5:latest"
    
    if ! docker image inspect "$image_name" &> /dev/null; then
        log_info "Building HydraX MT5 Docker image..."
        
        if [[ ! -f "Dockerfile.mt5" ]]; then
            log_error "Dockerfile.mt5 not found in current directory!"
            exit 1
        fi
        
        docker build -f Dockerfile.mt5 -t "$image_name" . || {
            log_error "Failed to build Docker image"
            exit 1
        }
        
        log_success "Docker image built successfully"
    else
        log_info "Docker image already exists"
    fi
}

# Deploy the terminal container
deploy_terminal() {
    local container_name="hydrax-mt5-${LABEL,,}"  # Convert to lowercase
    local config_dir="$(pwd)/config-${LABEL}"
    
    log_info "Deploying terminal: $container_name"
    
    # Remove existing container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_warning "Removing existing container: $container_name"
        docker stop "$container_name" 2>/dev/null || true
        docker rm "$container_name" 2>/dev/null || true
    fi
    
    # Create user-specific config directory
    mkdir -p "$config_dir"
    
    # Generate login.ini for this user
    generate_login_config "$config_dir/login.ini"
    
    # Copy terminal.ini template
    if [[ -f "config/terminal.ini" ]]; then
        cp "config/terminal.ini" "$config_dir/terminal.ini"
    fi
    
    # Run container with user credentials
    docker run -d \
        --name "$container_name" \
        --restart unless-stopped \
        -p "${PORT}:9013" \
        -p "$((PORT + 1000)):5900" \
        -v "$config_dir:/wine/drive_c/MetaTrader5/config" \
        -v "$(pwd)/MQL5:/wine/drive_c/MetaTrader5/MQL5" \
        -e "MT5_LOGIN=$LOGIN" \
        -e "MT5_PASSWORD=$PASS" \
        -e "MT5_SERVER=$SERVER" \
        -e "BRIDGE_PORT=$PORT" \
        -e "USER_LABEL=$LABEL" \
        --label "hydrax.user_label=$LABEL" \
        --label "hydrax.port=$PORT" \
        --label "hydrax.server=$SERVER" \
        hydrax-mt5:latest
    
    # Wait for container to start
    sleep 5
    
    # Verify container is running
    if ! docker ps --filter "name=$container_name" --format '{{.Names}}' | grep -q "$container_name"; then
        log_error "Container failed to start!"
        docker logs "$container_name"
        exit 1
    fi
    
    log_success "Container deployed successfully"
}

# Test the bridge connection
test_bridge() {
    local container_name="hydrax-mt5-${LABEL,,}"
    
    log_info "Testing bridge connectivity..."
    
    # Wait for services to start
    sleep 10
    
    # Test socket connection
    if timeout 5 bash -c "</dev/tcp/localhost/$PORT" 2>/dev/null; then
        log_success "Socket bridge is accessible on port $PORT"
    else
        log_warning "Socket bridge connection test failed"
        log_info "Container may still be starting up..."
    fi
    
    # Test with sample signal
    log_info "Sending test signal..."
    
    echo '{"symbol":"EURUSD","side":"buy","tp":30,"sl":15,"test":true}' | timeout 5 nc localhost "$PORT" 2>/dev/null && {
        log_success "Test signal sent successfully"
    } || {
        log_warning "Test signal failed - check container logs"
    }
}

# Display connection information
show_connection_info() {
    local container_name="hydrax-mt5-${LABEL,,}"
    
    echo
    log_success "🧠 HydraX MT5 Terminal deployed successfully!"
    echo
    echo -e "${CYAN}=== TERMINAL INFORMATION ===${NC}"
    echo -e "${BLUE}Container Name:${NC}    $container_name"
    echo -e "${BLUE}User Label:${NC}       $LABEL"
    echo -e "${BLUE}MT5 Server:${NC}       $SERVER"
    echo -e "${BLUE}MT5 Login:${NC}        $LOGIN"
    echo -e "${BLUE}Socket Port:${NC}      $PORT"
    echo -e "${BLUE}VNC Port:${NC}         $((PORT + 1000))"
    echo
    echo -e "${CYAN}=== READY FOR FIRE COMMANDS ===${NC}"
    echo -e "${BLUE}Socket Bridge:${NC}    localhost:$PORT"
    echo -e "${BLUE}Test Command:${NC}     echo '{\"symbol\":\"EURUSD\",\"side\":\"buy\",\"tp\":30,\"sl\":15}' | nc localhost $PORT"
    echo -e "${BLUE}Fire File:${NC}        MQL5/Files/fire.txt (monitored by BITTENBridge EA)"
    echo
    echo -e "${CYAN}=== MANAGEMENT COMMANDS ===${NC}"
    echo -e "${BLUE}View Logs:${NC}        docker logs $container_name -f"
    echo -e "${BLUE}Container Shell:${NC}  docker exec -it $container_name /bin/bash"
    echo -e "${BLUE}Stop Terminal:${NC}    docker stop $container_name"
    echo -e "${BLUE}Remove Terminal:${NC}  docker rm $container_name"
    echo
    echo -e "${GREEN}✅ Terminal is ready for HydraX Engine signals!${NC}"
}

# Main execution
main() {
    echo -e "${PURPLE}"
    echo "======================================================"
    echo "  🧠 HydraX MT5 Terminal Provisioning System"
    echo "  Dynamic broker credential injection + EA auto-load"
    echo "======================================================"
    echo -e "${NC}"
    
    parse_arguments "$@"
    
    log_info "Starting terminal provisioning for $LABEL..."
    log_info "Credentials: $LOGIN @ $SERVER"
    log_info "Port: $PORT"
    
    check_docker
    check_port
    build_image
    deploy_terminal
    test_bridge
    show_connection_info
    
    log_success "🔥 HydraX terminal provisioning complete!"
}

# Handle script termination
cleanup() {
    log_warning "Script interrupted"
    exit 1
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@"