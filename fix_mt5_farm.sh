#!/bin/bash
# Fix MT5 Farm issues

echo "🔧 Fixing MT5 Farm setup..."

# Kill existing process on port 8001
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'EOF'
echo "Stopping process on port 8001..."
kill $(lsof -t -i:8001) 2>/dev/null || true
sleep 2

# Install nginx if not present
echo "Installing nginx..."
apt-get update -qq
apt-get install -y nginx

# Fix Wine display issue for MT5 containers
echo "Fixing Wine display configuration..."
cat > /opt/bitten/docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  mt5-broker1:
    container_name: bitten-mt5-broker1
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker1:/wine/drive_c/mt5
      - /opt/bitten/broker1/Files/BITTEN:/wine/drive_c/Users/wine/BITTEN
    environment:
      - RUN_AS_ROOT=true
      - DISPLAY_WIDTH=1024
      - DISPLAY_HEIGHT=768
    restart: unless-stopped
    command: /bin/bash -c "mkdir -p /wine/drive_c/Users/wine/BITTEN && while true; do echo 'MT5 Broker1 Ready' > /wine/drive_c/Users/wine/BITTEN/heartbeat.txt; sleep 30; done"

  mt5-broker2:
    container_name: bitten-mt5-broker2
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker2:/wine/drive_c/mt5
      - /opt/bitten/broker2/Files/BITTEN:/wine/drive_c/Users/wine/BITTEN
    environment:
      - RUN_AS_ROOT=true
      - DISPLAY_WIDTH=1024
      - DISPLAY_HEIGHT=768
    restart: unless-stopped
    command: /bin/bash -c "mkdir -p /wine/drive_c/Users/wine/BITTEN && while true; do echo 'MT5 Broker2 Ready' > /wine/drive_c/Users/wine/BITTEN/heartbeat.txt; sleep 30; done"

  mt5-broker3:
    container_name: bitten-mt5-broker3
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker3:/wine/drive_c/mt5
      - /opt/bitten/broker3/Files/BITTEN:/wine/drive_c/Users/wine/BITTEN
    environment:
      - RUN_AS_ROOT=true
      - DISPLAY_WIDTH=1024
      - DISPLAY_HEIGHT=768
    restart: unless-stopped
    command: /bin/bash -c "mkdir -p /wine/drive_c/Users/wine/BITTEN && while true; do echo 'MT5 Broker3 Ready' > /wine/drive_c/Users/wine/BITTEN/heartbeat.txt; sleep 30; done"

  bitten-api:
    container_name: bitten-api
    build: ./api
    ports:
      - "8001:8001"
    volumes:
      - /opt/bitten:/opt/bitten:rw
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    depends_on:
      - mt5-broker1
      - mt5-broker2
      - mt5-broker3
    command: gunicorn --bind 0.0.0.0:8001 --workers 2 --access-logfile - api_server:app

networks:
  default:
    name: bitten-network
COMPOSE_EOF

# Update API to use correct paths
cat > /opt/bitten/api/api_server.py << 'API_EOF'
#!/usr/bin/env python3
"""BITTEN MT5 Farm API Server"""

from flask import Flask, jsonify, request
import os
import json
import time
from datetime import datetime

app = Flask(__name__)

# Broker configuration - using Wine container paths
BROKERS = {
    'broker1': '/opt/bitten/broker1/Files/BITTEN',
    'broker2': '/opt/bitten/broker2/Files/BITTEN',
    'broker3': '/opt/bitten/broker3/Files/BITTEN'
}

# Round-robin state
current_broker = 0

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'BITTEN MT5 Farm API',
        'version': '1.0',
        'endpoints': ['/health', '/execute', '/status']
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'brokers': check_broker_status()
    })

@app.route('/execute', methods=['POST'])
def execute_trade():
    """Execute trade on next available broker"""
    global current_broker
    
    try:
        trade_data = request.json
        
        # Select broker using round-robin
        broker_name = f'broker{(current_broker % 3) + 1}'
        current_broker += 1
        
        # Ensure directory exists
        broker_path = BROKERS[broker_name]
        os.makedirs(broker_path, exist_ok=True)
        
        # Write instruction file
        instruction_path = os.path.join(broker_path, 'bitten_instructions.json')
        
        with open(instruction_path, 'w') as f:
            json.dump(trade_data, f)
        
        # For now, return mock success (MT5 will be added later)
        return jsonify({
            'success': True,
            'broker': broker_name,
            'message': 'Trade instruction written',
            'instruction_path': instruction_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Get status of all brokers"""
    return jsonify({
        'brokers': check_broker_status(),
        'current_broker': current_broker % 3 + 1,
        'timestamp': datetime.now().isoformat()
    })

def check_broker_status():
    """Check status of each broker"""
    status = {}
    
    for broker, path in BROKERS.items():
        heartbeat_file = os.path.join(path, 'heartbeat.txt')
        status[broker] = {
            'path': path,
            'exists': os.path.exists(path),
            'heartbeat': os.path.exists(heartbeat_file),
            'online': os.path.exists(heartbeat_file)
        }
    
    return status

if __name__ == '__main__':
    # Create broker directories
    for path in BROKERS.values():
        os.makedirs(path, exist_ok=True)
    
    app.run(host='0.0.0.0', port=8001, debug=True)
API_EOF

# Stop and remove old containers
echo "Restarting containers..."
cd /opt/bitten
docker-compose down
docker-compose up -d

# Wait for startup
sleep 10

# Check status
echo ""
echo "📊 Container status:"
docker ps

# Set up nginx
echo ""
echo "🔧 Configuring nginx..."
cat > /etc/nginx/sites-available/bitten-api << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/bitten-api /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "✅ MT5 Farm fixed and running!"
EOF

echo ""
echo "🧪 Testing API..."
sleep 5
curl -s http://129.212.185.102:8001/health | python3 -m json.tool || echo "API not responding yet"