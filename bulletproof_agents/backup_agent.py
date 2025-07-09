
import flask
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class BackupAgent:
    def __init__(self):
        self.status = "backup_ready"
        self.last_heartbeat = datetime.now()
        self.monitor_primary()
    
    def monitor_primary(self):
        """Monitor primary agent and take over if needed"""
        def monitor():
            while True:
                try:
                    import requests
                    resp = requests.get("http://localhost:5555/health", timeout=5)
                    if resp.status_code == 200:
                        self.status = "backup_standby"
                    else:
                        self.status = "primary_failed_taking_over"
                except:
                    self.status = "primary_failed_taking_over"
                    
                time.sleep(10)
                
        threading.Thread(target=monitor, daemon=True).start()

agent = BackupAgent()

@app.route('/execute', methods=['POST'])
def execute_command():
    try:
        data = request.json
        command = data.get('command')
        command_type = data.get('type', 'powershell')
        
        if command_type == 'powershell':
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True, text=True, timeout=60
            )
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        
        return jsonify({
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'timestamp': datetime.now().isoformat(),
            'agent_id': 'backup_5556'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'agent_id': 'backup_5556'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': agent.status,
        'last_heartbeat': datetime.now().isoformat(),
        'agent_id': 'backup_5556',
        'port': 5556
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556, debug=False)
