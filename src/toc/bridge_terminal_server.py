"""
Bridge Terminal Server - MT5 Terminal Management on Windows VPS

This server runs on the Windows VPS with MT5 terminals and:
- Receives terminal launch commands from TOC
- Manages MT5 terminal instances
- Receives trade signals and writes to fire.json
- Monitors trade results and reports back to TOC
"""

import os
import json
import time
import logging
import subprocess
import threading
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import shutil
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app for receiving commands
app = Flask(__name__)

# Configuration
CONFIG = {
    'PORT': int(os.getenv('BRIDGE_PORT', '5001')),
    'HOST': '0.0.0.0',
    'MT5_BASE_PATH': os.getenv('MT5_BASE_PATH', 'C:\\MT5Terminals'),
    'TOC_CALLBACK_URL': os.getenv('TOC_CALLBACK_URL', 'http://localhost:5000'),
    'CHECK_INTERVAL': 5  # seconds
}

# Active terminals tracking
active_terminals = {}
terminal_lock = threading.Lock()

class TradeResultWatcher(FileSystemEventHandler):
    """Watches for trade result files from MT5 EA"""
    
    def __init__(self, terminal_id: str, user_id: str, folder_path: str):
        self.terminal_id = terminal_id
        self.user_id = user_id
        self.folder_path = folder_path
        self.processed_files = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('_result.json'):
            self.process_trade_result(event.src_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('_result.json'):
            self.process_trade_result(event.src_path)
    
    def process_trade_result(self, file_path: str):
        """Process trade result and send to TOC"""
        try:
            # Avoid processing same file multiple times
            if file_path in self.processed_files:
                return
            
            self.processed_files.add(file_path)
            
            # Read result file
            with open(file_path, 'r') as f:
                result_data = json.load(f)
            
            # Send to TOC
            self._send_result_to_toc(result_data)
            
            # Archive the file
            archive_path = Path(file_path).parent / 'archive'
            archive_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = archive_path / f"{timestamp}_{Path(file_path).name}"
            shutil.move(file_path, archive_file)
            
        except Exception as e:
            logger.error(f"Error processing trade result: {e}")
    
    def _send_result_to_toc(self, result_data: Dict):
        """Send trade result back to TOC"""
        try:
            import requests
            
            url = f"{CONFIG['TOC_CALLBACK_URL']}/trade-result"
            payload = {
                'user_id': self.user_id,
                'terminal_id': self.terminal_id,
                'trade_result': result_data
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Trade result sent to TOC for user {self.user_id}")
            else:
                logger.error(f"Failed to send trade result: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending result to TOC: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Bridge Terminal Server',
        'active_terminals': len(active_terminals),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/launch-terminal', methods=['POST'])
def launch_terminal():
    """
    Launch MT5 terminal with credentials
    
    Expected JSON:
    {
        "folder_path": "/mt5/terminals/demo_01",
        "credentials": {
            "login": "12345",
            "password": "password",
            "server": "broker-server.com:443"
        }
    }
    """
    try:
        data = request.json
        folder_path = data.get('folder_path')
        credentials = data.get('credentials', {})
        
        if not folder_path:
            return jsonify({'error': 'folder_path required'}), 400
        
        # Generate terminal ID
        terminal_id = f"terminal_{int(time.time())}"
        
        # Create terminal folder if needed
        terminal_path = Path(CONFIG['MT5_BASE_PATH']) / folder_path.strip('/')
        terminal_path.mkdir(parents=True, exist_ok=True)
        
        # Write login configuration
        if credentials:
            login_ini_path = terminal_path / 'config' / 'login.ini'
            login_ini_path.parent.mkdir(exist_ok=True)
            
            with open(login_ini_path, 'w') as f:
                f.write(f"[Login]\n")
                f.write(f"Login={credentials.get('login', '')}\n")
                f.write(f"Password={credentials.get('password', '')}\n")
                f.write(f"Server={credentials.get('server', '')}\n")
                f.write(f"AutoLogin=1\n")
        
        # Launch terminal
        success = _launch_mt5_terminal(terminal_id, terminal_path)
        
        if success:
            # Track terminal
            with terminal_lock:
                active_terminals[terminal_id] = {
                    'path': str(terminal_path),
                    'pid': success,  # Process ID
                    'launched_at': datetime.now().isoformat(),
                    'credentials': {k: v for k, v in credentials.items() if k != 'password'}
                }
            
            return jsonify({
                'success': True,
                'terminal_id': terminal_id,
                'message': 'Terminal launched successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to launch terminal'
            }), 500
            
    except Exception as e:
        logger.error(f"Terminal launch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fire', methods=['POST'])
def receive_fire_signal():
    """
    Receive fire signal from TOC
    
    Expected JSON:
    {
        "terminal_id": "terminal_123",
        "signal": {
            "symbol": "EURUSD",
            "direction": "buy",
            "volume": 0.01,
            "stop_loss": 1.0850,
            "take_profit": 1.0950,
            "comment": "BITTEN Signal",
            "magic_number": 12345
        }
    }
    """
    try:
        data = request.json
        terminal_id = data.get('terminal_id')
        signal = data.get('signal', {})
        
        if not terminal_id or not signal:
            return jsonify({'error': 'terminal_id and signal required'}), 400
        
        # Get terminal info
        with terminal_lock:
            terminal_info = active_terminals.get(terminal_id)
        
        if not terminal_info:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Write fire.json to terminal's MQL5/Files directory
        terminal_path = Path(terminal_info['path'])
        fire_file_path = terminal_path / 'MQL5' / 'Files' / 'fire.json'
        fire_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare fire data
        fire_data = {
            'timestamp': datetime.now().isoformat(),
            'signal_id': f"sig_{int(time.time() * 1000)}",
            'action': 'open_position',
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'volume': signal.get('volume', 0.01),
            'stop_loss': signal.get('stop_loss', 0),
            'take_profit': signal.get('take_profit', 0),
            'comment': signal.get('comment', 'BITTEN'),
            'magic_number': signal.get('magic_number', 12345),
            'slippage': 3,
            'max_retries': 3
        }
        
        # Write fire signal
        with open(fire_file_path, 'w') as f:
            json.dump(fire_data, f, indent=2)
        
        logger.info(f"Fire signal written to {fire_file_path}")
        
        return jsonify({
            'success': True,
            'signal_id': fire_data['signal_id'],
            'terminal_id': terminal_id,
            'message': 'Signal sent to terminal'
        })
        
    except Exception as e:
        logger.error(f"Fire signal error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/terminals', methods=['GET'])
def list_terminals():
    """List all active terminals"""
    with terminal_lock:
        terminals = []
        for tid, info in active_terminals.items():
            # Check if process is still running
            try:
                process = psutil.Process(info['pid'])
                status = 'running' if process.is_running() else 'stopped'
            except:
                status = 'unknown'
            
            terminals.append({
                'terminal_id': tid,
                'path': info['path'],
                'status': status,
                'launched_at': info['launched_at']
            })
    
    return jsonify({'terminals': terminals})

@app.route('/terminal/<terminal_id>/stop', methods=['POST'])
def stop_terminal(terminal_id):
    """Stop a specific terminal"""
    try:
        with terminal_lock:
            terminal_info = active_terminals.get(terminal_id)
        
        if not terminal_info:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Terminate process
        try:
            process = psutil.Process(terminal_info['pid'])
            process.terminate()
            process.wait(timeout=10)
        except:
            pass
        
        # Remove from tracking
        with terminal_lock:
            del active_terminals[terminal_id]
        
        return jsonify({
            'success': True,
            'message': f'Terminal {terminal_id} stopped'
        })
        
    except Exception as e:
        logger.error(f"Terminal stop error: {e}")
        return jsonify({'error': str(e)}), 500

def _launch_mt5_terminal(terminal_id: str, terminal_path: Path) -> Optional[int]:
    """Launch MT5 terminal and return process ID"""
    try:
        # Find terminal.exe
        terminal_exe = terminal_path / 'terminal.exe'
        if not terminal_exe.exists():
            # Try common MT5 installation paths
            common_paths = [
                'C:\\Program Files\\MetaTrader 5\\terminal.exe',
                'C:\\Program Files (x86)\\MetaTrader 5\\terminal.exe',
                terminal_path.parent / 'terminal.exe'
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    terminal_exe = Path(path)
                    break
            else:
                logger.error("MT5 terminal.exe not found")
                return None
        
        # Launch with portable mode
        cmd = [
            str(terminal_exe),
            '/portable',
            f'/config:{terminal_path}'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(terminal_path)
        )
        
        # Give it time to start
        time.sleep(5)
        
        if process.poll() is None:
            logger.info(f"MT5 terminal launched with PID {process.pid}")
            return process.pid
        else:
            logger.error("MT5 terminal failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Failed to launch MT5: {e}")
        return None

def start_result_watchers():
    """Start watching for trade results in all active terminals"""
    observer = Observer()
    
    def watch_terminal(terminal_id: str, terminal_info: Dict):
        try:
            results_path = Path(terminal_info['path']) / 'MQL5' / 'Files' / 'results'
            results_path.mkdir(parents=True, exist_ok=True)
            
            # Extract user_id from path or use terminal_id
            user_id = terminal_info.get('user_id', terminal_id)
            
            handler = TradeResultWatcher(terminal_id, user_id, str(results_path))
            observer.schedule(handler, str(results_path), recursive=False)
            
            logger.info(f"Watching for results in {results_path}")
            
        except Exception as e:
            logger.error(f"Failed to setup watcher for {terminal_id}: {e}")
    
    # Watch existing terminals
    with terminal_lock:
        for tid, info in active_terminals.items():
            watch_terminal(tid, info)
    
    observer.start()
    
    # Keep watching for new terminals
    while True:
        time.sleep(30)
        # Could add logic to watch new terminals here

def cleanup_stale_terminals():
    """Clean up terminals that are no longer running"""
    while True:
        try:
            time.sleep(60)  # Check every minute
            
            with terminal_lock:
                stale = []
                for tid, info in active_terminals.items():
                    try:
                        process = psutil.Process(info['pid'])
                        if not process.is_running():
                            stale.append(tid)
                    except:
                        stale.append(tid)
                
                for tid in stale:
                    logger.info(f"Removing stale terminal {tid}")
                    del active_terminals[tid]
                    
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

if __name__ == '__main__':
    # Start background threads
    watcher_thread = threading.Thread(target=start_result_watchers, daemon=True)
    watcher_thread.start()
    
    cleanup_thread = threading.Thread(target=cleanup_stale_terminals, daemon=True)
    cleanup_thread.start()
    
    # Start Flask server
    logger.info(f"Starting Bridge Terminal Server on port {CONFIG['PORT']}")
    app.run(
        host=CONFIG['HOST'],
        port=CONFIG['PORT'],
        debug=False
    )