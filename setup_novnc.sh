#!/bin/bash
# Setup noVNC web access for MT5 container

echo "🌐 Setting up noVNC web access..."

# Run noVNC container that connects to our VNC server
docker run -d \
  --name novnc_proxy \
  --network host \
  -e REMOTE_HOST=localhost \
  -e REMOTE_PORT=10090 \
  -p 6080:6080 \
  geek1011/easy-novnc:latest \
  --addr :6080 \
  --host localhost \
  --port 10090 \
  --novnc-params "resize=remote"

# Alternative: Run noVNC directly if you prefer
# git clone https://github.com/novnc/noVNC.git /opt/noVNC
# /opt/noVNC/utils/launch.sh --vnc localhost:10090 --listen 6080

echo "✅ noVNC should now be accessible at:"
echo "   http://YOUR_SERVER_IP:6080/vnc.html"
echo "   or"
echo "   http://134.199.204.67:6080/vnc.html"

# Check if it's running
sleep 2
docker ps | grep novnc_proxy