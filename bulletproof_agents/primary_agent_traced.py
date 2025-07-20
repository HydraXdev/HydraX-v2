import flask
import json
import subprocess
import os
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Create trace log file
TRACE_LOG = r"C:\apex_bridge_requests.log"

def trace_log(message):
    """Write trace log with timestamp"""
    try:
        with open(TRACE_LOG, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    except Exception as e:
        print(f"Trace log error: {e}")

class PrimaryAgent:
    def __init__(self):
        self.status = "running"
        self.last_heartbeat = datetime.now()
        self.commands_processed = 0
        self.start_health_monitor()
        trace_log("Primary Agent Started on port 5555")
    
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
        
        # TRACE LOGGING
        trace_log(f"=== INCOMING REQUEST ===")
        trace_log(f"Agent: primary_5555")
        trace_log(f"Client IP: {request.remote_addr}")
        trace_log(f"Request JSON: {json.dumps(data)}")
        trace_log(f"Command: {command}")
        trace_log(f"Type: {command_type}")
        
        agent.commands_processed += 1
        
        # Check if this is a BITTEN file check
        if "BITTEN" in command and ("dir" in command or "type" in command):
            trace_log(f"BITTEN FILE CHECK DETECTED")
            # Extract the file path being checked
            if "\\" in command:
                parts = command.split('"')
                for part in parts:
                    if "BITTEN" in part:
                        trace_log(f"File path requested: {part}")
                        # Check if file actually exists
                        if os.path.exists(part):
                            trace_log(f"FILE EXISTS: {part}")
                        else:
                            trace_log(f"FILE NOT FOUND: {part}")
        
        if command_type == 'powershell':
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True, text=True, timeout=60
            )
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        
        response_data = {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'timestamp': datetime.now().isoformat(),
            'agent_id': 'primary_5555'
        }
        
        # Log the response
        trace_log(f"Response returncode: {result.returncode}")
        trace_log(f"Response stdout length: {len(result.stdout)}")
        trace_log(f"Response stderr: {result.stderr}")
        trace_log(f"=== END REQUEST ===\n")
        
        return jsonify(response_data)
        
    except Exception as e:
        trace_log(f"ERROR: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'agent_id': 'primary_5555'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': agent.status,
        'last_heartbeat': agent.last_heartbeat.isoformat(),
        'commands_processed': agent.commands_processed,
        'agent_id': 'primary_5555'
    })

@app.route('/restart_backup', methods=['POST'])
def restart_backup():
    """Restart backup agents if needed"""
    try:
        # Kill existing backup processes
        subprocess.run("taskkill /F /IM backup_agent.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /F /IM websocket_agent.exe", shell=True, capture_output=True)
        
        # Restart them
        subprocess.Popen(["python", "backup_agent.py"], cwd=os.path.dirname(__file__))
        subprocess.Popen(["python", "websocket_agent.py"], cwd=os.path.dirname(__file__))
        
        return jsonify({'success': True, 'message': 'Backup agents restarted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    trace_log("Starting Primary Agent Flask server...")
    app.run(host='0.0.0.0', port=5555, debug=False)