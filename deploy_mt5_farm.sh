#!/bin/bash
# BITTEN MT5 Farm Deployment Script

echo "🚀 Deploying BITTEN MT5 Farm"
echo "============================"

# Create directory structure
echo "📁 Creating directories..."
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'EOF'
mkdir -p /opt/bitten/{broker1,broker2,broker3}/Files/BITTEN
mkdir -p /opt/bitten/api
mkdir -p /opt/bitten/config
mkdir -p /backups/daily
mkdir -p /var/log/bitten
echo "✅ Directories created"
EOF

echo ""
echo "🐳 Creating Docker Compose configuration..."

# Create docker-compose.yml
cat << 'DOCKER_EOF' > /tmp/docker-compose.yml
version: '3.8'

services:
  mt5-broker1:
    container_name: bitten-mt5-broker1
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker1:/wine/drive_c/mt5
      - /opt/bitten/broker1/Files/BITTEN:/wine/drive_c/mt5/Files/BITTEN
    environment:
      - DISPLAY=:0
      - WINEARCH=win64
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "test", "-f", "/wine/drive_c/mt5/Files/BITTEN/heartbeat.txt"]
      interval: 30s
      timeout: 10s
      retries: 3

  mt5-broker2:
    container_name: bitten-mt5-broker2
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker2:/wine/drive_c/mt5
      - /opt/bitten/broker2/Files/BITTEN:/wine/drive_c/mt5/Files/BITTEN
    environment:
      - DISPLAY=:0
      - WINEARCH=win64
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "test", "-f", "/wine/drive_c/mt5/Files/BITTEN/heartbeat.txt"]
      interval: 30s
      timeout: 10s
      retries: 3

  mt5-broker3:
    container_name: bitten-mt5-broker3
    image: scottyhardy/docker-wine:latest
    volumes:
      - /opt/bitten/broker3:/wine/drive_c/mt5
      - /opt/bitten/broker3/Files/BITTEN:/wine/drive_c/mt5/Files/BITTEN
    environment:
      - DISPLAY=:0
      - WINEARCH=win64
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "test", "-f", "/wine/drive_c/mt5/Files/BITTEN/heartbeat.txt"]
      interval: 30s
      timeout: 10s
      retries: 3

  bitten-api:
    container_name: bitten-api
    build: ./api
    ports:
      - "8001:8001"
    volumes:
      - /opt/bitten:/opt/bitten:ro
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    depends_on:
      - mt5-broker1
      - mt5-broker2
      - mt5-broker3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  default:
    name: bitten-network
DOCKER_EOF

# Copy docker-compose.yml to server
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/docker-compose.yml root@129.212.185.102:/opt/bitten/

echo "🐍 Creating API server..."

# Create API server
cat << 'API_EOF' > /tmp/api_server.py
#!/usr/bin/env python3
"""BITTEN MT5 Farm API Server"""

from flask import Flask, jsonify, request
import os
import json
import time
import subprocess
from datetime import datetime

app = Flask(__name__)

# Broker configuration
BROKERS = {
    'broker1': '/opt/bitten/broker1/Files/BITTEN',
    'broker2': '/opt/bitten/broker2/Files/BITTEN',
    'broker3': '/opt/bitten/broker3/Files/BITTEN'
}

# Round-robin state
current_broker = 0

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
    
    trade_data = request.json
    
    # Select broker using round-robin
    broker_name = f'broker{(current_broker % 3) + 1}'
    current_broker += 1
    
    # Write instruction file
    instruction_path = os.path.join(BROKERS[broker_name], 'bitten_instructions.json')
    
    with open(instruction_path, 'w') as f:
        json.dump(trade_data, f)
    
    # Wait for result (max 10 seconds)
    result_path = os.path.join(BROKERS[broker_name], 'bitten_results.json')
    start_time = time.time()
    
    while time.time() - start_time < 10:
        if os.path.exists(result_path):
            with open(result_path, 'r') as f:
                result = json.load(f)
            os.remove(result_path)  # Clean up
            
            return jsonify({
                'success': True,
                'broker': broker_name,
                'result': result
            })
        time.sleep(0.1)
    
    return jsonify({
        'success': False,
        'error': 'Trade execution timeout',
        'broker': broker_name
    }), 500

@app.route('/status', methods=['GET'])
def status():
    """Get status of all brokers"""
    return jsonify({
        'brokers': check_broker_status(),
        'current_broker': current_broker,
        'timestamp': datetime.now().isoformat()
    })

def check_broker_status():
    """Check status of each broker"""
    status = {}
    
    for broker, path in BROKERS.items():
        heartbeat_file = os.path.join(path, 'heartbeat.txt')
        if os.path.exists(heartbeat_file):
            mtime = os.path.getmtime(heartbeat_file)
            age = time.time() - mtime
            status[broker] = {
                'online': age < 60,  # Online if heartbeat within 60s
                'last_heartbeat': datetime.fromtimestamp(mtime).isoformat()
            }
        else:
            status[broker] = {
                'online': False,
                'last_heartbeat': None
            }
    
    return status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
API_EOF

# Create Dockerfile for API
cat << 'DOCKERFILE_EOF' > /tmp/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install flask gunicorn

COPY api_server.py .

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "2", "api_server:app"]
DOCKERFILE_EOF

# Copy API files to server
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 "mkdir -p /opt/bitten/api"
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/api_server.py root@129.212.185.102:/opt/bitten/api/
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/Dockerfile root@129.212.185.102:/opt/bitten/api/

echo ""
echo "🚀 Starting Docker containers..."

# Start containers
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'EOF'
cd /opt/bitten
docker-compose up -d
echo "⏳ Waiting for containers to start..."
sleep 10
docker ps
echo ""
echo "✅ MT5 Farm deployed!"
EOF

echo ""
echo "🔧 Setting up nginx reverse proxy..."

# Configure nginx
cat << 'NGINX_EOF' > /tmp/bitten-api.conf
server {
    listen 80;
    server_name _;
    
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/bitten-api.conf root@129.212.185.102:/etc/nginx/sites-available/
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'EOF'
ln -sf /etc/nginx/sites-available/bitten-api.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
echo "✅ Nginx configured"
EOF

echo ""
echo "✅ BITTEN MT5 Farm deployment complete!"
echo ""
echo "📊 Access points:"
echo "- API: http://129.212.185.102:8001"
echo "- Health check: http://129.212.185.102:8001/health"
echo ""
echo "Next step: Update main server to use farm API"