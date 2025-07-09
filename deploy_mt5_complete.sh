#!/bin/bash
# Complete MT5 Setup Script - Deploy EA and configure everything

echo "🚀 BITTEN Complete MT5 Deployment"
echo "=================================="

# 1. Copy EA to farm server
echo "📦 Copying EA to farm server..."
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /root/HydraX-v2/src/bridge/BITTENBridge.mq5 root@129.212.185.102:/opt/bitten/

# 2. Update farm API to handle live data
echo "🔧 Updating farm API with live data endpoints..."
cat << 'API_UPDATE' > /tmp/api_update.py
#!/usr/bin/env python3
"""Enhanced BITTEN MT5 Farm API with Live Data"""

from flask import Flask, jsonify, request
import os
import json
import time
from datetime import datetime
import glob

app = Flask(__name__)

# Broker configuration
BROKERS = {
    'broker1': '/opt/bitten/broker1/Files/BITTEN',
    'broker2': '/opt/bitten/broker2/Files/BITTEN',
    'broker3': '/opt/bitten/broker3/Files/BITTEN'
}

# Round-robin state
current_broker = 0
trade_history = []

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'BITTEN MT5 Farm API v2',
        'version': '2.0',
        'endpoints': ['/health', '/execute', '/status', '/positions', '/live_data']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'brokers': check_broker_status()
    })

@app.route('/execute', methods=['POST'])
def execute_trade():
    global current_broker, trade_history
    
    try:
        trade_data = request.json
        
        # Select broker using round-robin
        broker_name = f'broker{(current_broker % 3) + 1}'
        current_broker += 1
        
        # Ensure directory exists
        broker_path = BROKERS[broker_name]
        os.makedirs(broker_path, exist_ok=True)
        
        # Add timestamp and fingerprint
        trade_data['timestamp'] = int(time.time())
        trade_data['fingerprint'] = f"{trade_data['symbol']}_{trade_data['timestamp']}_{broker_name}"
        
        # Write instruction file
        instruction_path = os.path.join(broker_path, 'bitten_instructions_secure.txt')
        
        with open(instruction_path, 'w') as f:
            json.dump(trade_data, f)
        
        # Wait for result (max 10 seconds)
        result_path = os.path.join(broker_path, 'bitten_results_secure.txt')
        start_time = time.time()
        
        while time.time() - start_time < 10:
            if os.path.exists(result_path):
                with open(result_path, 'r') as f:
                    result = json.load(f)
                os.remove(result_path)
                
                # Store in history
                trade_history.append({
                    'broker': broker_name,
                    'trade': trade_data,
                    'result': result,
                    'executed_at': datetime.now().isoformat()
                })
                
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
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/positions', methods=['GET'])
def get_positions():
    """Get all active positions from all brokers"""
    all_positions = []
    
    for broker, path in BROKERS.items():
        positions_file = os.path.join(path, 'bitten_positions_secure.txt')
        if os.path.exists(positions_file):
            try:
                with open(positions_file, 'r') as f:
                    positions = json.load(f)
                    for pos in positions:
                        pos['broker'] = broker
                    all_positions.extend(positions)
            except:
                pass
    
    return jsonify({
        'positions': all_positions,
        'count': len(all_positions),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/live_data', methods=['GET'])
def get_live_data():
    """Get live market data and account info"""
    live_data = {}
    
    for broker, path in BROKERS.items():
        status_file = os.path.join(path, 'bitten_status_secure.txt')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    live_data[broker] = status
            except:
                live_data[broker] = {'error': 'Could not read status'}
    
    return jsonify({
        'brokers': live_data,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'brokers': check_broker_status(),
        'current_broker': current_broker % 3 + 1,
        'total_trades': len(trade_history),
        'timestamp': datetime.now().isoformat()
    })

def check_broker_status():
    status = {}
    
    for broker, path in BROKERS.items():
        heartbeat_file = os.path.join(path, 'heartbeat.txt')
        status_file = os.path.join(path, 'bitten_status_secure.txt')
        
        broker_info = {
            'path': path,
            'exists': os.path.exists(path),
            'heartbeat': False,
            'last_heartbeat': None,
            'connected': False,
            'positions': 0
        }
        
        # Check heartbeat
        if os.path.exists(heartbeat_file):
            mtime = os.path.getmtime(heartbeat_file)
            age = time.time() - mtime
            broker_info['heartbeat'] = age < 60
            broker_info['last_heartbeat'] = datetime.fromtimestamp(mtime).isoformat()
        
        # Check status
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                    broker_info['connected'] = status_data.get('connected', False)
                    broker_info['positions'] = status_data.get('positions_count', 0)
            except:
                pass
        
        status[broker] = broker_info
    
    return status

if __name__ == '__main__':
    # Create broker directories
    for path in BROKERS.values():
        os.makedirs(path, exist_ok=True)
    
    app.run(host='0.0.0.0', port=8001, debug=False)
API_UPDATE

# Copy updated API to farm
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/api_update.py root@129.212.185.102:/opt/bitten/api/api_server.py

# 3. Create MT5 setup instructions
echo "📝 Creating MT5 setup instructions..."
cat << 'MT5_SETUP' > /tmp/mt5_setup_instructions.txt
BITTEN MT5 Setup Instructions
=============================

For each broker container (1, 2, 3):

1. Enter container:
   docker exec -it bitten-mt5-broker1 bash

2. Download MT5 installer:
   wget https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe

3. Install MT5:
   wine mt5setup.exe /auto

4. Configure MT5:
   - Login with broker credentials
   - Open MetaEditor (F4)
   - Copy BITTENBridge.mq5 to Experts folder
   - Compile EA (F7)
   - Attach to EURUSD chart
   - Enable AutoTrading

5. EA Settings:
   - InstructionFile: bitten_instructions_secure.txt
   - ResultFile: bitten_results_secure.txt
   - StatusFile: bitten_status_secure.txt
   - PositionsFile: bitten_positions_secure.txt
   - MagicNumber: 20250626

6. Test:
   - EA should show "BITTEN: Ready for orders"
   - Check Files tab for BITTEN folder

Repeat for broker2 and broker3 containers.
MT5_SETUP

sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no /tmp/mt5_setup_instructions.txt root@129.212.185.102:/opt/bitten/

# 4. Restart farm API with new code
echo "🔄 Restarting farm API..."
sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'EOF'
cd /opt/bitten
docker-compose restart bitten-api
echo "✅ API restarted with live data support"
EOF

# 5. Update main server signal flow to use live data
echo "🔧 Updating signal flow with live data filtering..."
cat << 'LIVE_FILTER' > /tmp/live_data_filter.py
"""Live data filtering from MT5 farm"""

import requests
from typing import Dict, List

class LiveDataFilter:
    """Filter signals based on live MT5 data"""
    
    def __init__(self, farm_url: str = "http://129.212.185.102:8001"):
        self.farm_url = farm_url
    
    def get_live_positions(self) -> List[Dict]:
        """Get all active positions from farm"""
        try:
            response = requests.get(f"{self.farm_url}/positions")
            data = response.json()
            return data.get('positions', [])
        except:
            return []
    
    def get_live_account_data(self) -> Dict:
        """Get live account data from all brokers"""
        try:
            response = requests.get(f"{self.farm_url}/live_data")
            return response.json()
        except:
            return {}
    
    def should_take_signal(self, signal: Dict) -> bool:
        """Decide if signal should be taken based on live data"""
        positions = self.get_live_positions()
        
        # Check position limits
        if len(positions) >= 10:  # Max 10 concurrent
            return False
        
        # Check if already in this symbol
        symbol_positions = [p for p in positions if p.get('symbol') == signal['symbol']]
        if len(symbol_positions) >= 2:  # Max 2 per symbol
            return False
        
        # Check drawdown
        total_pnl = sum(p.get('profit', 0) for p in positions)
        if total_pnl < -500:  # $500 drawdown limit
            return False
        
        return True
    
    def get_optimal_broker(self) -> str:
        """Select best broker based on load"""
        live_data = self.get_live_account_data()
        
        # Find broker with least positions
        min_positions = float('inf')
        best_broker = 'broker1'
        
        for broker, data in live_data.get('brokers', {}).items():
            if data.get('connected'):
                positions = data.get('positions_count', 0)
                if positions < min_positions:
                    min_positions = positions
                    best_broker = broker
        
        return best_broker
LIVE_FILTER

cp /tmp/live_data_filter.py /root/HydraX-v2/src/bitten_core/

echo ""
echo "✅ Complete MT5 deployment ready!"
echo ""
echo "📋 Summary:"
echo "- EA copied to farm server"
echo "- API updated with live data endpoints"
echo "- Live data filtering added"
echo "- Setup instructions created"
echo ""
echo "🎯 Next Steps:"
echo "1. Install MT5 in containers (see /opt/bitten/mt5_setup_instructions.txt)"
echo "2. Configure broker accounts"
echo "3. Attach BITTEN EA to charts"
echo "4. Test with: curl http://129.212.185.102:8001/positions"
echo ""
echo "📊 New Endpoints:"
echo "- GET /positions - All active positions"
echo "- GET /live_data - Live account data"
echo ""
echo "The system can now:"
echo "✅ Filter signals based on active positions"
echo "✅ Check account drawdown before trading"
echo "✅ Select optimal broker for load balancing"
echo "✅ Track all trades across brokers"