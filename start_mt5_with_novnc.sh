#!/bin/bash

# Start Xvfb (virtual display)
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &
export DISPLAY=:99

# Start x11vnc (VNC server)
x11vnc -display :99 -listen 0.0.0.0 -rfbport 5900 -forever -shared -nopw &

# Wait for VNC to be ready
sleep 2

# Start noVNC websocket proxy
websockify --web=/usr/share/novnc/ --wrap-mode=ignore 8080 localhost:5900 &

# Initialize fire.txt
echo '{}' > /wine/drive_c/fire.txt

# Start Wine/MT5 setup (but don't exit if it fails)
echo "🔧 Setting up Wine environment..."
wineboot --init || true

# Keep container running
echo "✅ VNC and noVNC are ready!"
echo "🌐 Access VNC at: http://134.199.204.67:8083/vnc.html"
echo "📁 MT5 directory: /wine/drive_c/MetaTrader5/"

# Keep the container alive
tail -f /dev/null