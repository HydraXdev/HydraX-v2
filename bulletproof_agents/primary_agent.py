
import flask
import json
import subprocess
import os
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class PrimaryAgent:
    def __init__(self):
        self.status = "running"
        self.last_heartbeat = datetime.now()
        self.commands_processed = 0
        self.start_health_monitor()
    
    def start_health_monitor(self):
        """Start health monitoring in background"""
        def health_check():
            while True:
                try:
                    self.last_heartbeat = datetime.now()
                    # Check system health
                    subprocess.run("tasklist | findstr python", shell=True, capture_output=True)
                    time.sleep(30)
                except Exception as e:
                    print(f"Health check error: {e}")
                    
        threading.Thread(target=health_check, daemon=True).start()

agent = PrimaryAgent()

@app.route('/execute', methods=['POST'])
def execute_command():
    try:
        data = request.json
        command = data.get('command')
        command_type = data.get('type', 'powershell')
        
        agent.commands_processed += 1
        
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
            'agent_id': 'primary_5555'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'agent_id': 'primary_5555'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': agent.status,
        'last_heartbeat': agent.last_heartbeat.isoformat(),
        'commands_processed': agent.commands_processed,
        'agent_id': 'primary_5555',
        'port': 5555
    })

@app.route('/restart_backup', methods=['POST'])
def restart_backup():
    """Restart backup agent if needed"""
    try:
        subprocess.Popen(['python', 'C:\\BITTEN_Agent\\backup_agent.py'], 
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        return jsonify({'success': True, 'message': 'Backup agent restarted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=False)
