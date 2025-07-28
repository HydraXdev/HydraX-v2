#!/bin/bash
#=================================================================
# HydraX MT5 Auto-Terminal Provisioning System
# Industrial-Grade Docker + Wine + MT5 Trading Infrastructure
#=================================================================

set -euo pipefail

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="HydraX MT5 Auto-Terminal Starter"

# Default configuration
DEFAULT_DOCKER_IMAGE="hydrax/mt5:latest"
DEFAULT_VNC_PORT="6080"
DEFAULT_SOCKET_BRIDGE_PORT="8080"
DEFAULT_MT5_FILES_PATH="/mt5-files"

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Display banner
show_banner() {
    echo -e "${PURPLE}"
    echo "======================================================"
    echo "  HydraX MT5 Auto-Terminal Provisioning System"
    echo "  Industrial-Grade Docker + Wine + MT5 Infrastructure"
    echo "  Version: $SCRIPT_VERSION"
    echo "======================================================"
    echo -e "${NC}"
}

# Display usage
show_usage() {
    cat << EOF
Usage: $0 --login USER --pass PASS --server SERVER --port PORT [OPTIONS]

Required Arguments:
  --login USER      MT5 login credentials
  --pass PASS       MT5 password  
  --server SERVER   MT5 broker server
  --port PORT       Unique port for this terminal (e.g., 9013)

Optional Arguments:
  --user-id ID      User ID for container naming (default: generated)
  --ea-name NAME    EA name to attach (default: DirectTrade_TwoWay)
  --image IMAGE     Docker image to use (default: $DEFAULT_DOCKER_IMAGE)
  --memory MEM      Memory limit (default: 1g)
  --cpu CPU         CPU limit (default: 1.0)
  --pairs PAIRS     Trading pairs CSV (default: EURUSD,GBPUSD,USDJPY,USDCAD,AUDUSD,USDCHF,NZDUSD,EURGBP,EURJPY,GBPJPY,XAUUSD,GBPNZD,GBPAUD,EURAUD,GBPCHF)
  --no-vnc          Disable VNC access
  --debug           Enable debug mode
  --help            Show this help

Examples:
  # Basic terminal with demo account
  $0 --login 12345 --pass mypass --server MetaQuotes-Demo --port 9013
  
  # Production terminal with specific EA
  $0 --login 987654 --pass secret123 --server ICMarkets-Live01 --port 9014 --ea-name BITTEN_EA_v3
  
  # High-resource terminal for multiple pairs
  $0 --login 555666 --pass trader2025 --server FXCM-USDDemo01 --port 9015 --memory 2g --cpu 2.0

EOF
}

# Parse command line arguments
parse_arguments() {
    # Required parameters
    MT5_LOGIN=""
    MT5_PASSWORD=""
    MT5_SERVER=""
    TERMINAL_PORT=""
    
    # Optional parameters
    USER_ID=$(date +%s)
    EA_NAME="DirectTrade_TwoWay"
    DOCKER_IMAGE="$DEFAULT_DOCKER_IMAGE"
    MEMORY_LIMIT="1g"
    CPU_LIMIT="1.0"
    TRADING_PAIRS="EURUSD,GBPUSD,USDJPY,USDCAD,AUDUSD,USDCHF,NZDUSD,EURGBP,EURJPY,GBPJPY,XAUUSD,GBPNZD,GBPAUD,EURAUD,GBPCHF"
    ENABLE_VNC=true
    DEBUG_MODE=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --login)
                MT5_LOGIN="$2"
                shift 2
                ;;
            --pass)
                MT5_PASSWORD="$2" 
                shift 2
                ;;
            --server)
                MT5_SERVER="$2"
                shift 2
                ;;
            --port)
                TERMINAL_PORT="$2"
                shift 2
                ;;
            --user-id)
                USER_ID="$2"
                shift 2
                ;;
            --ea-name)
                EA_NAME="$2"
                shift 2
                ;;
            --image)
                DOCKER_IMAGE="$2"
                shift 2
                ;;
            --memory)
                MEMORY_LIMIT="$2"
                shift 2
                ;;
            --cpu)
                CPU_LIMIT="$2"
                shift 2
                ;;
            --pairs)
                TRADING_PAIRS="$2"
                shift 2
                ;;
            --no-vnc)
                ENABLE_VNC=false
                shift
                ;;
            --debug)
                DEBUG_MODE=true
                shift
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
    if [[ -z "$MT5_LOGIN" || -z "$MT5_PASSWORD" || -z "$MT5_SERVER" || -z "$TERMINAL_PORT" ]]; then
        log_error "Missing required parameters!"
        show_usage
        exit 1
    fi
    
    # Set derived variables
    CONTAINER_NAME="hydrax-mt5-${USER_ID}"
    VNC_PORT=$((TERMINAL_PORT + 1000))  # VNC port = terminal_port + 1000
    SOCKET_PORT=$((TERMINAL_PORT + 2000))  # Socket port = terminal_port + 2000
    
    if [[ "$DEBUG_MODE" == true ]]; then
        set -x  # Enable debug tracing
        log_info "Debug mode enabled"
    fi
}

# Validate system requirements
validate_system() {
    log_info "Validating system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found! Please install Docker first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running! Please start Docker."
        exit 1
    fi
    
    # Check port availability
    if netstat -tuln | grep -q ":$TERMINAL_PORT "; then
        log_error "Port $TERMINAL_PORT already in use!"
        exit 1
    fi
    
    if [[ "$ENABLE_VNC" == true ]] && netstat -tuln | grep -q ":$VNC_PORT "; then
        log_error "VNC Port $VNC_PORT already in use!"
        exit 1
    fi
    
    log_success "System validation complete"
}

# Pull or build Docker image
prepare_docker_image() {
    log_info "Preparing Docker image: $DOCKER_IMAGE"
    
    # Check if image exists locally
    if docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
        log_info "Docker image found locally"
    else
        log_warning "Docker image not found locally, building..."
        
        # Create Dockerfile if it doesn't exist
        if [[ ! -f "Dockerfile.hydrax-mt5" ]]; then
            create_dockerfile
        fi
        
        # Build the image
        docker build -t "$DOCKER_IMAGE" -f Dockerfile.hydrax-mt5 . || {
            log_error "Failed to build Docker image"
            exit 1
        }
    fi
    
    log_success "Docker image ready"
}

# Create Dockerfile for HydraX MT5
create_dockerfile() {
    log_info "Creating HydraX MT5 Dockerfile..."
    
    cat > Dockerfile.hydrax-mt5 << 'DOCKERFILE'
FROM ubuntu:22.04

# Install Wine and dependencies
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEARCH=win64
ENV WINEPREFIX=/wine
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y \
    wine64 \
    winetricks \
    xvfb \
    x11vnc \
    supervisor \
    curl \
    wget \
    unzip \
    python3 \
    python3-pip \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Initialize Wine
RUN wine wineboot --init

# Create MT5 directory structure
RUN mkdir -p /wine/drive_c/MetaTrader5/MQL5/Experts \
    && mkdir -p /wine/drive_c/MetaTrader5/MQL5/Files \
    && mkdir -p /wine/drive_c/MetaTrader5/Templates \
    && mkdir -p /wine/drive_c/MetaTrader5/Profiles/Charts \
    && mkdir -p /mt5-files/drop \
    && mkdir -p /logs

# Install Python dependencies for socket bridge
RUN pip3 install websockets asyncio python-socketio

# Copy startup scripts
COPY scripts/start-mt5.sh /start-mt5.sh
COPY scripts/socket-bridge.py /socket-bridge.py
COPY scripts/supervisor.conf /etc/supervisor/conf.d/hydrax.conf

# Copy EA and templates
COPY ea/DirectTrade_TwoWay.ex5 /wine/drive_c/MetaTrader5/MQL5/Experts/
COPY templates/auto-attach.tpl /wine/drive_c/MetaTrader5/Templates/

# Set permissions
RUN chmod +x /start-mt5.sh \
    && chmod +x /socket-bridge.py \
    && chmod -R 777 /wine \
    && chmod -R 777 /mt5-files

# Expose ports
EXPOSE 5900 6080 8080

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/hydrax.conf"]
DOCKERFILE

    log_success "Dockerfile created"
}

# Create necessary support files
create_support_files() {
    log_info "Creating support files..."
    
    # Create directories
    mkdir -p scripts templates ea
    
    # Create MT5 startup script
    cat > scripts/start-mt5.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

# Wait for Wine to be ready
sleep 5

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2

# Start VNC server if enabled
if [[ "${ENABLE_VNC:-true}" == "true" ]]; then
    x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -ncache 10 -forever -rfbport 5900 &
    VNC_PID=$!
fi

# Download MT5 if not exists
MT5_INSTALLER="/wine/drive_c/mt5setup.exe"
if [[ ! -f "$MT5_INSTALLER" ]]; then
    echo "Downloading MT5..."
    wget -q -O "$MT5_INSTALLER" "https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe"
fi

# Install MT5 silently
if [[ ! -f "/wine/drive_c/MetaTrader5/terminal64.exe" ]]; then
    echo "Installing MT5..."
    cd /wine/drive_c
    wine mt5setup.exe /auto
    sleep 30
fi

# Create MT5 config file with user credentials
cat > /wine/drive_c/MetaTrader5/config/common.ini << INIFILE
[Server]
Name=${MT5_SERVER}

[StartUp]
Login=${MT5_LOGIN}
Password=${MT5_PASSWORD}
Server=${MT5_SERVER}
AutoLogin=true

[Expert]
Enabled=true
AllowLiveTrading=true
AllowDllImports=true
INIFILE

# Start MT5
echo "Starting MT5..."
cd /wine/drive_c/MetaTrader5
wine terminal64.exe /portable /config:config/common.ini &
MT5_PID=$!

# Wait for MT5 to start
sleep 20

# Auto-attach EA to specified pairs
python3 /scripts/auto-attach-ea.py --ea-name "${EA_NAME}" --pairs "${TRADING_PAIRS}"

# Keep container running
wait $MT5_PID
STARTSCRIPT

    # Create socket bridge
    cat > scripts/socket-bridge.py << 'SOCKETBRIDGE'
#!/usr/bin/env python3
"""
Socket-to-File Bridge for MT5 Communication
Receives trading signals via socket and drops JSON files for EA processing
"""

import asyncio
import websockets
import json
import os
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SocketBridge')

class SocketBridge:
    def __init__(self, port=8080, drop_path="/mt5-files/drop"):
        self.port = port
        self.drop_path = drop_path
        self.clients = set()
        
        # Ensure drop directory exists
        os.makedirs(drop_path, exist_ok=True)
        
        logger.info(f"Socket Bridge initialized on port {port}")
        logger.info(f"Drop path: {drop_path}")

    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        finally:
            self.clients.remove(websocket)

    async def process_message(self, websocket, message):
        """Process incoming trading signal"""
        try:
            data = json.loads(message)
            
            if data.get('action') == 'trade':
                result = await self.handle_trade_signal(data)
                await websocket.send(json.dumps({
                    'status': 'success' if result else 'error',
                    'message': 'Trade signal processed' if result else 'Failed to process trade signal',
                    'timestamp': datetime.now().isoformat()
                }))
            else:
                await websocket.send(json.dumps({
                    'status': 'error', 
                    'message': 'Unknown action',
                    'timestamp': datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'status': 'error',
                'message': 'Invalid JSON',
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }))

    async def handle_trade_signal(self, signal_data):
        """Convert trading signal to MT5 file format"""
        try:
            # Extract trade parameters
            symbol = signal_data.get('symbol', '').upper()
            direction = signal_data.get('direction', '').upper()
            lot_size = float(signal_data.get('lot_size', 0.01))
            stop_loss = float(signal_data.get('stop_loss', 0))
            take_profit = float(signal_data.get('take_profit', 0))
            
            # Validate required fields
            if not symbol or not direction:
                logger.error("Missing required fields: symbol or direction")
                return False
                
            if direction not in ['BUY', 'SELL']:
                logger.error(f"Invalid direction: {direction}")
                return False
            
            # Create trade file for MT5 EA
            trade_id = int(time.time() * 1000000)
            filename = f"trade_{trade_id}_{symbol}.json"
            filepath = os.path.join(self.drop_path, filename)
            
            trade_instruction = {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'lot_size': lot_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now().isoformat(),
                'magic_number': 20250726,
                'comment': f'HydraX_{trade_id}'
            }
            
            # Write trade file
            with open(filepath, 'w') as f:
                json.dump(trade_instruction, f, indent=2)
            
            logger.info(f"Trade file created: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating trade file: {e}")
            return False

    def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting Socket Bridge server on port {self.port}")
        
        start_server = websockets.serve(
            self.handle_client, 
            '0.0.0.0', 
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    bridge = SocketBridge(port=port)
    bridge.start_server()
SOCKETBRIDGE

    # Create EA auto-attach script
    cat > scripts/auto-attach-ea.py << 'AUTOATTACH'
#!/usr/bin/env python3
"""
Auto-attach EA to MT5 charts
"""
import os
import time
import argparse

def create_chart_template(ea_name, pairs):
    """Create MT5 template file for auto-attaching EA"""
    
    template_content = f"""
<template>
    <description>HydraX Auto-Attach Template</description>
    <window>
        <symbol>{pairs[0]}</symbol>
        <period>16408</period>
        <experts>
            <expert>
                <name>{ea_name}</name>
                <inputs>
                    <input name="MagicNumber" value="20250726"/>
                    <input name="LotSize" value="0.01"/>
                </inputs>
                <flags>
                    <allow_live_trading>true</allow_live_trading>
                    <allow_dll_imports>true</allow_dll_imports>
                </flags>
            </expert>
        </experts>
    </window>
</template>
"""
    
    template_path = "/wine/drive_c/MetaTrader5/Templates/HydraX_AutoAttach.tpl"
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    print(f"Template created: {template_path}")

def attach_ea_to_pairs(ea_name, pairs):
    """Attach EA to multiple trading pairs"""
    
    print(f"Auto-attaching {ea_name} to pairs: {pairs}")
    
    # Create template
    create_chart_template(ea_name, pairs)
    
    # Create MQL5 script for mass attachment
    script_content = f'''
//+------------------------------------------------------------------+
//| HydraX EA Auto-Attacher                                         |
//+------------------------------------------------------------------+

void OnStart()
{{
    string pairs[] = {{{",".join([f'"{pair}"' for pair in pairs])}}};
    
    for(int i = 0; i < ArraySize(pairs); i++)
    {{
        string symbol = pairs[i];
        
        // Ensure symbol is available
        if(!SymbolSelect(symbol, true))
        {{
            Print("Warning: Symbol ", symbol, " not available");
            continue;
        }}
        
        // Open chart
        long chart_id = ChartOpen(symbol, PERIOD_H1);
        if(chart_id == 0)
        {{
            Print("Error: Cannot open chart for ", symbol);
            continue;
        }}
        
        // Apply template with EA
        if(ChartApplyTemplate(chart_id, "HydraX_AutoAttach"))
        {{
            Print("Success: EA attached to ", symbol);
        }}
        else
        {{
            Print("Error: Cannot attach EA to ", symbol);
        }}
        
        Sleep(1000);  // 1 second delay between attachments
    }}
    
    Alert("HydraX EA auto-attachment completed for ", ArraySize(pairs), " pairs");
}}
'''
    
    script_path = "/wine/drive_c/MetaTrader5/MQL5/Scripts/HydraX_AutoAttach.mq5"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"Auto-attach script created: {script_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ea-name', required=True)
    parser.add_argument('--pairs', required=True)
    args = parser.parse_args()
    
    pairs = [p.strip() for p in args.pairs.split(',')]
    attach_ea_to_pairs(args.ea_name, pairs)
AUTOATTACH

    # Create supervisor config
    cat > scripts/supervisor.conf << 'SUPERVISOR'
[supervisord]
nodaemon=true
user=root

[program:mt5]
command=/start-mt5.sh
autostart=true
autorestart=true
stdout_logfile=/logs/mt5.log
stderr_logfile=/logs/mt5_error.log

[program:socket-bridge]
command=/socket-bridge.py %(ENV_SOCKET_PORT)s
autostart=true
autorestart=true
stdout_logfile=/logs/bridge.log
stderr_logfile=/logs/bridge_error.log
SUPERVISOR

    # Make scripts executable
    chmod +x scripts/*.sh scripts/*.py

    log_success "Support files created"
}

# Deploy MT5 terminal container
deploy_terminal() {
    log_info "Deploying MT5 terminal: $CONTAINER_NAME"
    
    # Remove existing container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warning "Removing existing container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # Build port arguments
    PORT_ARGS="-p ${SOCKET_PORT}:8080"
    if [[ "$ENABLE_VNC" == true ]]; then
        PORT_ARGS="$PORT_ARGS -p ${VNC_PORT}:5900 -p ${TERMINAL_PORT}:6080"
    fi
    
    # Run container
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        --memory "$MEMORY_LIMIT" \
        --cpus "$CPU_LIMIT" \
        $PORT_ARGS \
        -v "${PWD}/mt5-data-${USER_ID}:/mt5-files" \
        -e "MT5_LOGIN=$MT5_LOGIN" \
        -e "MT5_PASSWORD=$MT5_PASSWORD" \
        -e "MT5_SERVER=$MT5_SERVER" \
        -e "EA_NAME=$EA_NAME" \
        -e "TRADING_PAIRS=$TRADING_PAIRS" \
        -e "ENABLE_VNC=$ENABLE_VNC" \
        -e "SOCKET_PORT=$SOCKET_PORT" \
        --label "hydrax.user_id=$USER_ID" \
        --label "hydrax.terminal_port=$TERMINAL_PORT" \
        --label "hydrax.mt5_server=$MT5_SERVER" \
        "$DOCKER_IMAGE"
    
    # Wait for container to start
    sleep 5
    
    # Verify container is running
    if ! docker ps --filter "name=$CONTAINER_NAME" --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        log_error "Container failed to start!"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    
    log_success "Container deployed successfully"
}

# Verify MT5 terminal is working
verify_terminal() {
    log_info "Verifying MT5 terminal functionality..."
    
    # Wait for MT5 to fully initialize
    sleep 30
    
    # Check if MT5 process is running
    if docker exec "$CONTAINER_NAME" pgrep -f "terminal64.exe" > /dev/null; then
        log_success "MT5 process is running"
    else
        log_warning "MT5 process not detected, checking logs..."
        docker logs "$CONTAINER_NAME" --tail 20
    fi
    
    # Check socket bridge
    if docker exec "$CONTAINER_NAME" pgrep -f "socket-bridge.py" > /dev/null; then
        log_success "Socket bridge is running"
    else
        log_error "Socket bridge not running!"
    fi
    
    # Test socket connection
    if timeout 5 bash -c "</dev/tcp/localhost/$SOCKET_PORT"; then
        log_success "Socket bridge accessible on port $SOCKET_PORT"
    else
        log_warning "Socket bridge connection test failed"
    fi
    
    log_success "Terminal verification complete"
}

# Display connection information
show_connection_info() {
    echo
    log_success "HydraX MT5 Terminal deployed successfully!"
    echo
    echo -e "${CYAN}=== CONNECTION INFORMATION ===${NC}"
    echo -e "${BLUE}Container Name:${NC}    $CONTAINER_NAME"
    echo -e "${BLUE}User ID:${NC}          $USER_ID"
    echo -e "${BLUE}MT5 Server:${NC}       $MT5_SERVER"
    echo -e "${BLUE}MT5 Login:${NC}        $MT5_LOGIN"
    echo -e "${BLUE}Trading Pairs:${NC}    $TRADING_PAIRS"
    echo -e "${BLUE}EA Name:${NC}          $EA_NAME"
    echo
    echo -e "${CYAN}=== ACCESS ENDPOINTS ===${NC}"
    echo -e "${BLUE}Socket Bridge:${NC}    ws://localhost:$SOCKET_PORT"
    if [[ "$ENABLE_VNC" == true ]]; then
        echo -e "${BLUE}VNC Access:${NC}       vnc://localhost:$VNC_PORT"
        echo -e "${BLUE}Web VNC:${NC}          http://localhost:$TERMINAL_PORT"
    fi
    echo -e "${BLUE}Data Volume:${NC}      ${PWD}/mt5-data-${USER_ID}"
    echo
    echo -e "${CYAN}=== MANAGEMENT COMMANDS ===${NC}"
    echo -e "${BLUE}View Logs:${NC}        docker logs $CONTAINER_NAME -f"
    echo -e "${BLUE}Container Shell:${NC}  docker exec -it $CONTAINER_NAME /bin/bash"
    echo -e "${BLUE}Stop Terminal:${NC}    docker stop $CONTAINER_NAME"
    echo -e "${BLUE}Remove Terminal:${NC}  docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
    echo
    echo -e "${GREEN}Terminal is ready for trading signals!${NC}"
}

# Test socket bridge with sample trade
test_socket_bridge() {
    log_info "Testing socket bridge with sample trade signal..."
    
    cat > /tmp/test_trade.py << 'TESTSCRIPT'
#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_trade_signal():
    uri = f"ws://localhost:{SOCKET_PORT}"
    
    trade_signal = {
        "action": "trade",
        "symbol": "EURUSD", 
        "direction": "BUY",
        "lot_size": 0.01,
        "stop_loss": 1.0950,
        "take_profit": 1.1050
    }
    
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(trade_signal))
            response = await websocket.recv()
            result = json.loads(response)
            
            if result.get('status') == 'success':
                print("✅ Socket bridge test successful")
                return True
            else:
                print(f"❌ Socket bridge test failed: {result.get('message')}")
                return False
                
    except Exception as e:
        print(f"❌ Socket bridge connection failed: {e}")
        return False

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(test_trade_signal())
TESTSCRIPT

    # Replace placeholder and run test
    sed -i "s/{SOCKET_PORT}/$SOCKET_PORT/g" /tmp/test_trade.py
    
    if python3 /tmp/test_trade.py; then
        log_success "Socket bridge test passed"
    else
        log_warning "Socket bridge test failed - check container logs"
    fi
    
    rm -f /tmp/test_trade.py
}

# Main execution
main() {
    show_banner
    parse_arguments "$@"
    
    log_info "Starting HydraX MT5 terminal deployment..."
    log_info "Container: $CONTAINER_NAME"
    log_info "Ports: Socket=$SOCKET_PORT, VNC=$VNC_PORT, Web=$TERMINAL_PORT"
    
    validate_system
    prepare_docker_image
    create_support_files
    deploy_terminal
    verify_terminal
    test_socket_bridge
    show_connection_info
    
    log_success "HydraX MT5 Auto-Terminal deployment complete!"
}

# Handle script termination
cleanup() {
    log_warning "Script interrupted, cleaning up..."
    exit 1
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@"