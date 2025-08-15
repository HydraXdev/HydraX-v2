#!/bin/bash

# 🚀 ULTIMATE C.O.R.E. CRYPTO ENGINE - DEPLOYMENT SCRIPT
# Professional deployment with comprehensive system setup and monitoring

echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"
echo "                                                                                    "
echo "    ██╗   ██╗██╗  ████████╗██╗███╗   ███╗ █████╗ ████████╗███████╗               "
echo "    ██║   ██║██║  ╚══██╔══╝██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝               "
echo "    ██║   ██║██║     ██║   ██║██╔████╔██║███████║   ██║   █████╗                 "
echo "    ██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝                 "
echo "    ╚██████╔╝███████╗██║   ██║██║ ╚═╝ ██║██║  ██║   ██║   ███████╗               "
echo "     ╚═════╝ ╚══════╝╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝               "
echo "                                                                                    "
echo "     ██████╗ ██████╗ ██████╗ ███████╗     ██████╗██████╗ ██╗   ██╗██████╗████████╗ ██████╗ "
echo "    ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══████╔═══██╗██╔═══██╗"
echo "    ██║     ██║   ██║██████╔╝█████╗      ██║     ██████╔╝ ╚████╔╝ ██████╔╝█████╗██║   ██║"
echo "    ██║     ██║   ██║██╔══██╗██╔══╝      ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝ ██╔══╝██║   ██║"
echo "    ╚██████╗╚██████╔╝██║  ██║███████╗    ╚██████╗██║  ██║   ██║   ██║     ███████╝╚██████╔╝"
echo "     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝ "
echo "                                                                                    "
echo "                            COMPREHENSIVE OUTSTANDING RELIABLE ENGINE"
echo "                                   DEPLOYMENT SCRIPT v1.0"
echo "                                                                                    "
echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"

# Configuration
SCRIPT_DIR="/root/HydraX-v2"
LOGS_DIR="$SCRIPT_DIR/logs"
MODELS_DIR="$SCRIPT_DIR/models"
PID_FILE="$SCRIPT_DIR/core_crypto_engine.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check if running as root
check_permissions() {
    log_info "🔐 Checking permissions..."
    if [[ $EUID -eq 0 ]]; then
        log_success "✅ Running as root - Full permissions available"
    else
        log_warn "⚠️ Not running as root - Some operations may fail"
    fi
}

# Create necessary directories
setup_directories() {
    log_info "📁 Setting up directories..."
    
    mkdir -p "$LOGS_DIR" 2>/dev/null && log_success "✅ Logs directory: $LOGS_DIR"
    mkdir -p "$MODELS_DIR" 2>/dev/null && log_success "✅ Models directory: $MODELS_DIR"
    
    # Set proper permissions
    chmod 755 "$LOGS_DIR" "$MODELS_DIR" 2>/dev/null
    
    log_success "📁 Directory structure ready"
}

# Check Python dependencies
check_dependencies() {
    log_info "🔍 Checking Python dependencies..."
    
    # Required packages
    REQUIRED_PACKAGES=("zmq" "numpy" "pandas" "sklearn" "scipy" "psutil" "requests")
    
    MISSING_PACKAGES=()
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            log_success "✅ $package - Available"
        else
            log_error "❌ $package - Missing"
            MISSING_PACKAGES+=("$package")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        log_error "❌ Missing dependencies: ${MISSING_PACKAGES[*]}"
        log_info "📦 Installing missing packages..."
        
        # Install missing packages
        for package in "${MISSING_PACKAGES[@]}"; do
            case $package in
                "zmq")
                    pip3 install pyzmq
                    ;;
                "sklearn")
                    pip3 install scikit-learn
                    ;;
                *)
                    pip3 install "$package"
                    ;;
            esac
        done
        
        log_success "📦 Dependencies installation completed"
    else
        log_success "✅ All dependencies satisfied"
    fi
}

# Check system resources
check_system_resources() {
    log_info "💻 Checking system resources..."
    
    # Check available memory
    AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$AVAILABLE_MEM" -gt 100 ]; then
        log_success "✅ Available memory: ${AVAILABLE_MEM}MB"
    else
        log_warn "⚠️ Low memory: ${AVAILABLE_MEM}MB available"
    fi
    
    # Check disk space
    AVAILABLE_DISK=$(df -h "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    log_success "✅ Available disk space: $AVAILABLE_DISK"
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    log_success "✅ CPU cores: $CPU_CORES"
}

# Check network ports
check_network_ports() {
    log_info "🌐 Checking network ports..."
    
    REQUIRED_PORTS=(5558 5559 5560)
    
    for port in "${REQUIRED_PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warn "⚠️ Port $port - In use (may be normal)"
        else
            log_success "✅ Port $port - Available"
        fi
    done
}

# Check existing processes
check_existing_processes() {
    log_info "🔍 Checking for existing processes..."
    
    # Check if C.O.R.E. engine is already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log_warn "⚠️ C.O.R.E. engine already running (PID: $OLD_PID)"
            echo -n "Do you want to stop it and restart? (y/N): "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                kill "$OLD_PID" 2>/dev/null
                sleep 3
                log_info "🛑 Stopped existing process"
            else
                log_error "❌ Cannot start - Process already running"
                exit 1
            fi
        else
            log_info "🧹 Cleaning up stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check related processes
    RELATED_PROCESSES=("elite_guard" "bitten_production" "webapp_server")
    
    for process in "${RELATED_PROCESSES[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            log_success "✅ $process - Running (good for integration)"
        else
            log_info "ℹ️ $process - Not running (C.O.R.E. can run independently)"
        fi
    done
}

# Test engine initialization
test_engine() {
    log_info "🧪 Testing engine initialization..."
    
    # Test Python imports and basic functionality
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')

try:
    from ultimate_core_crypto_engine import UltimateCORECryptoEngine
    engine = UltimateCORECryptoEngine()
    print('✅ Engine initialization - SUCCESS')
    
    # Test key attributes
    assert hasattr(engine, 'crypto_symbols'), 'Missing crypto_symbols'
    assert hasattr(engine, 'risk_per_trade'), 'Missing risk_per_trade'
    assert hasattr(engine, 'max_daily_signals'), 'Missing max_daily_signals'
    print('✅ Engine attributes - SUCCESS')
    
    # Test key methods
    methods = ['start_zmq_connections', '_detect_smc_patterns', '_enhance_with_ml']
    for method in methods:
        assert hasattr(engine, method), f'Missing method: {method}'
    print('✅ Engine methods - SUCCESS')
    
    print('🚀 ENGINE TEST PASSED - READY FOR DEPLOYMENT')
    
except Exception as e:
    print(f'❌ ENGINE TEST FAILED: {e}')
    sys.exit(1)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "✅ Engine test passed - Ready for deployment"
    else
        log_error "❌ Engine test failed - Check configuration"
        exit 1
    fi
}

# Deploy the engine
deploy_engine() {
    log_info "🚀 Deploying Ultimate C.O.R.E. Crypto Engine..."
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR/ultimate_core_crypto_engine.py"
    chmod +x "$SCRIPT_DIR/start_ultimate_core_crypto.py"
    chmod +x "$SCRIPT_DIR/core_crypto_integration.py"
    
    log_success "✅ Scripts made executable"
    
    # Start the engine using the launcher
    log_info "🎯 Starting Ultimate C.O.R.E. Crypto Engine..."
    
    # Start in background with proper logging
    nohup python3 "$SCRIPT_DIR/start_ultimate_core_crypto.py" \
        > "$LOGS_DIR/core_crypto_startup.log" 2>&1 &
    
    ENGINE_PID=$!
    echo $ENGINE_PID > "$PID_FILE"
    
    log_success "🚀 Engine started with PID: $ENGINE_PID"
    
    # Wait a moment for startup
    sleep 5
    
    # Check if process is still running
    if ps -p "$ENGINE_PID" > /dev/null 2>&1; then
        log_success "✅ Engine is running successfully"
        
        # Display startup log
        echo ""
        log_info "📋 Startup log (last 20 lines):"
        echo "----------------------------------------"
        tail -n 20 "$LOGS_DIR/core_crypto_startup.log" 2>/dev/null || echo "Log file not yet available"
        echo "----------------------------------------"
        
    else
        log_error "❌ Engine failed to start - Check logs"
        cat "$LOGS_DIR/core_crypto_startup.log" 2>/dev/null
        exit 1
    fi
}

# Show deployment summary
show_summary() {
    echo ""
    echo "🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯"
    echo "                                                                                    "
    echo "                    ✅ ULTIMATE C.O.R.E. CRYPTO ENGINE DEPLOYED"
    echo "                                                                                    "
    echo "🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯"
    
    log_success "🚀 ENGINE STATUS: LIVE AND OPERATIONAL"
    log_success "📊 TARGET WIN RATE: 70-85%"
    log_success "💰 RISK MANAGEMENT: 1% per trade"
    log_success "📈 RISK:REWARD RATIO: 1:2"
    log_success "🎯 MAX DAILY SIGNALS: 10"
    log_success "📡 ZMQ PUBLISHER: Port 5558"
    log_success "🔍 SYMBOLS: BTCUSD, ETHUSD, XRPUSD"
    
    echo ""
    log_info "📁 KEY FILES:"
    log_info "   • Engine: $SCRIPT_DIR/ultimate_core_crypto_engine.py"
    log_info "   • Launcher: $SCRIPT_DIR/start_ultimate_core_crypto.py"
    log_info "   • Integration: $SCRIPT_DIR/core_crypto_integration.py"
    log_info "   • Logs: $LOGS_DIR/"
    log_info "   • PID File: $PID_FILE"
    
    echo ""
    log_info "🔧 MANAGEMENT COMMANDS:"
    log_info "   • View Logs: tail -f $LOGS_DIR/ultimate_core_crypto_engine.log"
    log_info "   • Check Status: ps -ef | grep ultimate_core_crypto"
    log_info "   • Stop Engine: kill \$(cat $PID_FILE)"
    log_info "   • Restart: $0"
    
    echo ""
    log_info "📊 MONITORING:"
    log_info "   • Signal Log: tail -f $LOGS_DIR/crypto_signals.jsonl"
    log_info "   • Truth Log: tail -f /root/HydraX-v2/truth_log.jsonl"
    log_info "   • Performance: Check WebApp at http://localhost:8888"
    
    echo ""
    log_success "🎯 ULTIMATE C.O.R.E. CRYPTO ENGINE IS NOW LIVE!"
    log_success "🔥 The most sophisticated crypto signal engine is generating signals!"
    
    echo ""
    echo "🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯"
}

# Handle script interruption
cleanup() {
    echo ""
    log_warn "🛑 Deployment interrupted"
    if [ -n "$ENGINE_PID" ] && ps -p "$ENGINE_PID" > /dev/null 2>&1; then
        kill "$ENGINE_PID" 2>/dev/null
        log_info "🧹 Cleaned up engine process"
    fi
    exit 1
}

# Set trap for cleanup
trap cleanup INT TERM

# Main execution
main() {
    log_info "🚀 Starting Ultimate C.O.R.E. Crypto Engine deployment..."
    
    # Change to script directory
    cd "$SCRIPT_DIR" || exit 1
    
    # Run all checks and setup
    check_permissions
    setup_directories
    check_dependencies
    check_system_resources
    check_network_ports
    check_existing_processes
    test_engine
    deploy_engine
    show_summary
    
    log_success "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
}

# Run main function
main "$@"