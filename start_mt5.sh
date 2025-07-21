#!/bin/bash
#=================================================================
# HydraX MT5 Headless Launch Script
# 
# This script handles the complete startup sequence for a headless
# MT5 terminal inside a Docker container, including:
# - Virtual display setup (Xvfb)
# - VNC server for remote access
# - MT5 installation and configuration
# - Python socket bridge initialization
# - Process monitoring and auto-restart
#
# The script is designed to run as the main process (PID 1) in
# a Docker container and will handle graceful shutdown when
# receiving SIGTERM or SIGINT signals.
#=================================================================

set -euo pipefail  # Exit on error, undefined variables, pipe failures

echo "🧠 Starting HydraX MT5 Terminal..."

# =================================================================
# ENVIRONMENT CONFIGURATION
# =================================================================
# These environment variables are typically set by the Docker
# container or passed through from the spinup_terminal.sh script

BRIDGE_PORT=${BRIDGE_PORT:-9013}        # Port for Python socket bridge
MT5_LOGIN=${MT5_LOGIN:-""}              # MT5 account login number
MT5_PASSWORD=${MT5_PASSWORD:-""}        # MT5 account password
MT5_SERVER=${MT5_SERVER:-""}            # MT5 server name
USER_LABEL=${USER_LABEL:-"DEFAULT"}     # User identification label
DISPLAY_NUM=${DISPLAY_NUM:-99}          # X11 display number

echo "🔐 User: $MT5_LOGIN @ $MT5_SERVER"
echo "🔌 Bridge Port: $BRIDGE_PORT"
echo "🏷️  Label: $USER_LABEL"

# =================================================================
# DISPLAY AND VNC SETUP
# =================================================================

# Initialize Wine environment - Wine needs time to set up its registry
# and configuration on first run in a container
echo "⏳ Initializing Wine environment..."
sleep 5

# Start Xvfb (X Virtual Framebuffer) for headless operation
# This creates a virtual display that MT5 can render to even without
# a physical monitor attached to the system
echo "🖥️  Starting virtual display..."
Xvfb :${DISPLAY_NUM} -screen 0 1920x1080x24 &
XVFB_PID=$!
export DISPLAY=:${DISPLAY_NUM}
sleep 2

# Start VNC server to allow remote access to the virtual display
# This enables users to connect via VNC client to see MT5 GUI
# if needed for debugging or manual intervention
echo "📺 Starting VNC server..."
x11vnc -display :${DISPLAY_NUM} -nopw -listen 0.0.0.0 -xkb -ncache 10 -forever -rfbport 5900 &
VNC_PID=$!

# =================================================================
# MT5 INSTALLATION AND SETUP
# =================================================================

# Define paths for MT5 installation
MT5_INSTALLER="/wine/drive_c/mt5setup.exe"
MT5_EXECUTABLE="/wine/drive_c/MetaTrader5/terminal64.exe"
MT5_CONFIG_DIR="/wine/drive_c/MetaTrader5/config"

# Download MT5 installer if not already present
# This allows the container to work even if the installer wasn't
# pre-baked into the Docker image
if [[ ! -f "$MT5_INSTALLER" ]]; then
    echo "📥 Downloading MT5 installer..."
    wget -q -O "$MT5_INSTALLER" "https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe" || {
        echo "❌ Failed to download MT5 installer"
        echo "🔍 Check internet connectivity and try again"
        exit 1
    }
    echo "✅ MT5 installer downloaded successfully"
fi

# Install MT5 if not already installed
# The /auto flag performs silent installation
if [[ ! -f "$MT5_EXECUTABLE" ]]; then
    echo "🔧 Installing MetaTrader 5..."
    cd /wine/drive_c
    
    # Run silent installation
    export WINEDEBUG=-all  # Suppress Wine debug output
    wine mt5setup.exe /auto
    
    # Wait for installation to complete
    # MT5 installer can take 30-60 seconds depending on system performance
    echo "⏳ Waiting for installation to complete..."
    sleep 30
    
    # Verify installation succeeded
    if [[ ! -f "$MT5_EXECUTABLE" ]]; then
        echo "❌ MT5 installation failed - terminal64.exe not found"
        echo "🔍 Check Wine compatibility and system resources"
        exit 1
    fi
    
    echo "✅ MT5 installation completed successfully"
else
    echo "✅ MT5 already installed"
fi

# =================================================================
# MT5 CONFIGURATION AND DIRECTORY SETUP
# =================================================================

# Create necessary configuration directories
echo "📁 Setting up MT5 directory structure..."
mkdir -p "$MT5_CONFIG_DIR"
mkdir -p /wine/drive_c/MetaTrader5/MQL5/Files
mkdir -p /wine/drive_c/MetaTrader5/MQL5/Experts
mkdir -p /wine/drive_c/MetaTrader5/Profiles/Templates
mkdir -p /wine/drive_c/MetaTrader5/Profiles/Charts

# Inject login credentials if provided
# This allows automatic login without manual intervention
if [[ -n "$MT5_LOGIN" && -n "$MT5_PASSWORD" && -n "$MT5_SERVER" ]]; then
    echo "🔑 Injecting login credentials for $MT5_LOGIN @ $MT5_SERVER..."
    if [[ -f "/inject_login.sh" ]]; then
        /inject_login.sh "$MT5_LOGIN" "$MT5_PASSWORD" "$MT5_SERVER"
    else
        echo "⚠️  Warning: inject_login.sh not found, manual login required"
    fi
else
    echo "ℹ️  No credentials provided - MT5 will start in demo/manual login mode"
fi

# Set proper file permissions for MT5 file access
# The 777 permissions ensure MT5 and Python bridge can both
# read/write to these directories regardless of user context
chmod -R 777 /wine/drive_c/MetaTrader5/MQL5/Files
chmod -R 777 /wine/drive_c/MetaTrader5/Profiles

# =================================================================
# HYDRAX BRIDGE INITIALIZATION
# =================================================================

# Initialize the fire.txt control file
# This file serves as the communication bridge between the Python
# socket server and MT5 Expert Advisors
FIRE_FILE="/wine/drive_c/MetaTrader5/MQL5/Files/fire.txt"
echo "{}" > "$FIRE_FILE"
echo "🔥 Fire control file initialized at $FIRE_FILE"

# Start the Python socket bridge in background
# This bridge listens for trading signals and writes them to fire.txt
# for pickup by the BITTENBridge EA running in MT5
echo "🌉 Starting HydraX socket bridge on port $BRIDGE_PORT..."
if [[ -f "/bridge.py" ]]; then
    python3 /bridge.py "$BRIDGE_PORT" "$FIRE_FILE" &
    BRIDGE_PID=$!
    echo "✅ Bridge started with PID $BRIDGE_PID"
else
    echo "❌ Bridge script not found at /bridge.py"
    exit 1
fi

# Wait for bridge to initialize and start listening
sleep 3

# =================================================================
# MT5 TERMINAL LAUNCH
# =================================================================

# Launch MT5 terminal with configuration
echo "🚀 Launching MetaTrader 5..."
cd /wine/drive_c/MetaTrader5

# Launch MT5 with specific flags:
# /portable - Run in portable mode (uses local config)
# /config: - Use specific configuration file if available
export WINEDEBUG=-all  # Suppress Wine debug output for cleaner logs
if [[ -f "$MT5_CONFIG_DIR/login.ini" ]]; then
    wine terminal64.exe /portable "/config:$MT5_CONFIG_DIR/login.ini" &
else
    wine terminal64.exe /portable &
fi
MT5_PID=$!

# =================================================================
# STARTUP COMPLETION AND STATUS REPORTING
# =================================================================

echo ""
echo "✅ HydraX MT5 Terminal startup complete!"
echo "=================================="
echo "📊 MT5 Terminal PID: $MT5_PID"
echo "🌉 Socket Bridge PID: $BRIDGE_PID"
echo "📺 VNC Server PID: $VNC_PID"
echo "🖥️  Virtual Display PID: $XVFB_PID"
echo "🔌 Bridge Port: $BRIDGE_PORT"
echo "📺 VNC Port: 5900"
echo "🏷️  User Label: $USER_LABEL"
echo "=================================="

# =================================================================
# SIGNAL HANDLERS AND CLEANUP
# =================================================================

# Define cleanup function to gracefully shutdown all processes
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal - cleaning up processes..."
    
    # Kill MT5 terminal
    if [[ -n "${MT5_PID:-}" ]] && kill -0 "$MT5_PID" 2>/dev/null; then
        echo "🔄 Stopping MT5 terminal (PID: $MT5_PID)..."
        kill "$MT5_PID" 2>/dev/null || true
        sleep 2
    fi
    
    # Kill bridge process
    if [[ -n "${BRIDGE_PID:-}" ]] && kill -0 "$BRIDGE_PID" 2>/dev/null; then
        echo "🔄 Stopping socket bridge (PID: $BRIDGE_PID)..."
        kill "$BRIDGE_PID" 2>/dev/null || true
    fi
    
    # Kill VNC server
    if [[ -n "${VNC_PID:-}" ]] && kill -0 "$VNC_PID" 2>/dev/null; then
        echo "🔄 Stopping VNC server (PID: $VNC_PID)..."
        kill "$VNC_PID" 2>/dev/null || true
    fi
    
    # Kill virtual display
    if [[ -n "${XVFB_PID:-}" ]] && kill -0 "$XVFB_PID" 2>/dev/null; then
        echo "🔄 Stopping virtual display (PID: $XVFB_PID)..."
        kill "$XVFB_PID" 2>/dev/null || true
    fi
    
    echo "✅ HydraX Terminal shutdown complete"
    exit 0
}

# Register signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# =================================================================
# PROCESS MONITORING AND AUTO-RESTART
# =================================================================

echo "🔄 Starting process monitoring loop..."
echo "ℹ️  Monitoring will restart failed processes automatically"

# Main monitoring loop - keeps container alive and processes healthy
while true; do
    
    # Check MT5 terminal health
    if ! kill -0 "$MT5_PID" 2>/dev/null; then
        echo "⚠️  MT5 terminal stopped unexpectedly - restarting..."
        cd /wine/drive_c/MetaTrader5
        if [[ -f "$MT5_CONFIG_DIR/login.ini" ]]; then
            wine terminal64.exe /portable "/config:$MT5_CONFIG_DIR/login.ini" &
        else
            wine terminal64.exe /portable &
        fi
        MT5_PID=$!
        echo "✅ MT5 restarted with PID: $MT5_PID"
    fi
    
    # Check bridge health
    if ! kill -0 "$BRIDGE_PID" 2>/dev/null; then
        echo "⚠️  Socket bridge stopped unexpectedly - restarting..."
        python3 /bridge.py "$BRIDGE_PORT" "$FIRE_FILE" &
        BRIDGE_PID=$!
        echo "✅ Bridge restarted with PID: $BRIDGE_PID"
    fi
    
    # Sleep before next health check
    # 30 seconds provides good balance between responsiveness and resource usage
    sleep 30
done