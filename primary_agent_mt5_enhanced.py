#!/usr/bin/env python3
"""
Enhanced Primary Agent with MT5 Bridge Socket Listener
Handles HTTP requests + Socket commands for MT5 trade execution
"""

import flask
import json
import subprocess
import os
import threading
import time
import socket
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, Any, Optional

# MT5 Integration
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("[BRIDGE] WARNING: MetaTrader5 not available - install with: pip install MetaTrader5")

app = Flask(__name__)

class EnhancedPrimaryAgent:
    def __init__(self):
        self.status = "running"
        self.last_heartbeat = datetime.now()
        self.commands_processed = 0
        self.trades_processed = 0
        self.socket_port = 9000  # Socket listener port
        self.socket_running = False
        
        # MT5 Configuration - Dynamic server and credential injection
        self.mt5_config = {
            'login': int(os.getenv('MT5_LOGIN', '843859')),
            'password': os.getenv('MT5_PASSWORD', os.getenv("BOT_TOKEN")),
            'server': os.getenv('MT5_SERVER', 'MetaQuotes-Demo'),  # Dynamic server from environment
            'path': os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5\terminal64.exe')
        }
        
        # Log the broker/server configuration
        print(f"[BRIDGE] 🏢 Broker/Server Configuration:")
        print(f"[BRIDGE] 📊 Server: {self.mt5_config['server']}")
        print(f"[BRIDGE] 👤 Login: {self.mt5_config['login']}")
        print(f"[BRIDGE] 🔧 Path: {self.mt5_config['path']}")
        print(f"[BRIDGE] 🌐 Environment MT5_SERVER: {os.getenv('MT5_SERVER', 'Not set - using default')}")
        
        self.start_health_monitor()
        self.start_socket_listener()
        self.ensure_mt5_connection()
    
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
                    print(f"[BRIDGE] Health check error: {e}")
                    
        threading.Thread(target=health_check, daemon=True).start()
    
    def ensure_mt5_connection(self):
        """Ensure MT5 is connected and initialized"""
        if not MT5_AVAILABLE:
            print("[BRIDGE] WARNING: MT5 not available - running in simulation mode")
            return False
        
        try:
            # Check if already initialized
            if not mt5.initialize():
                print("[BRIDGE] MT5 not initialized, attempting connection...")
                # Try to initialize with credentials
                if not mt5.initialize(
                    login=self.mt5_config['login'],
                    password=self.mt5_config['password'],
                    server=self.mt5_config['server'],
                    path=self.mt5_config['path']
                ):
                    print(f"[BRIDGE] MT5 initialization failed: {mt5.last_error()}")
                    return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info:
                print(f"[BRIDGE] MT5 Connected - Account: {account_info.login} | Balance: {account_info.balance}")
                return True
            else:
                print("[BRIDGE] MT5 connection failed - no account info")
                return False
                
        except Exception as e:
            print(f"[BRIDGE] MT5 connection error: {e}")
            return False
    
    def get_mt5_status(self) -> Dict[str, Any]:
        """Get current MT5 status for ping response"""
        if not MT5_AVAILABLE:
            return {
                "status": "simulation",
                "account": "N/A",
                "broker": "Simulation Mode",
                "balance": 10000.0,
                "symbols": ["XAUUSD", "GBPJPY", "USDJPY", "EURUSD"],
                "ping": "OK"
            }
        
        try:
            # Ensure connection
            if not self.ensure_mt5_connection():
                return {
                    "status": "offline",
                    "account": "N/A",
                    "broker": "Connection Failed",
                    "balance": 0.0,
                    "symbols": [],
                    "ping": "FAILED"
                }
            
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                return {
                    "status": "offline",
                    "account": "N/A",
                    "broker": "No Account Info",
                    "balance": 0.0,
                    "symbols": [],
                    "ping": "FAILED"
                }
            
            # Get available symbols
            symbols = mt5.symbols_get()
            symbol_names = [s.name for s in symbols[:20]] if symbols else ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
            
            return {
                "status": "online",
                "account": account_info.login,
                "broker": account_info.server,
                "balance": account_info.balance,
                "symbols": symbol_names,
                "ping": "OK"
            }
            
        except Exception as e:
            print(f"[BRIDGE] Status check error: {e}")
            return {
                "status": "error",
                "account": "N/A",
                "broker": f"Error: {str(e)}",
                "balance": 0.0,
                "symbols": [],
                "ping": "ERROR"
            }
    
    def execute_mt5_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MT5 trade and return result"""
        if not MT5_AVAILABLE:
            # Simulation mode
            print(f"[BRIDGE] Command received: FIRE {trade_data.get('symbol', 'UNKNOWN')} {trade_data.get('lot', 0.0)} lots")
            return {
                "retcode": 10009,  # TRADE_RETCODE_DONE
                "order": int(time.time()),
                "ticket": int(time.time()) + 1000,
                "symbol": trade_data.get('symbol', 'EURUSD'),
                "volume": trade_data.get('lot', 0.01),
                "price": 1.0500,
                "sl": trade_data.get('sl', 0.0),
                "tp": trade_data.get('tp', 0.0),
                "comment": f"Simulated trade - {trade_data.get('comment', '')}",
                "request_id": 0
            }
        
        try:
            # Ensure MT5 connection
            if not self.ensure_mt5_connection():
                return {
                    "retcode": 10004,  # TRADE_RETCODE_CONNECTION
                    "comment": "MT5 connection failed"
                }
            
            symbol = trade_data.get('symbol', 'EURUSD')
            lot = trade_data.get('lot', 0.01)
            order_type = mt5.ORDER_TYPE_BUY if trade_data.get('type', 'buy').lower() == 'buy' else mt5.ORDER_TYPE_SELL
            
            # Get current price
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return {
                    "retcode": 10013,  # TRADE_RETCODE_INVALID_SYMBOL
                    "comment": f"Symbol {symbol} not found"
                }
            
            # Get current price
            price = symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid
            
            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": trade_data.get('sl', 0.0),
                "tp": trade_data.get('tp', 0.0),
                "comment": trade_data.get('comment', 'BITTEN_FIRE'),
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            print(f"[BRIDGE] Command received: FIRE {symbol} {lot} lots")
            
            # Execute trade
            result = mt5.order_send(request)
            
            if result:
                self.trades_processed += 1
                print(f"[BRIDGE] Order sent. Retcode: {result.retcode} | Ticket: {result.order}")
                
                # Return full MT5 result as dict
                return {
                    "retcode": result.retcode,
                    "order": result.order,
                    "ticket": result.order,
                    "symbol": symbol,
                    "volume": lot,
                    "price": result.price if hasattr(result, 'price') else price,
                    "sl": trade_data.get('sl', 0.0),
                    "tp": trade_data.get('tp', 0.0),
                    "comment": trade_data.get('comment', 'BITTEN_FIRE'),
                    "request_id": result.request_id if hasattr(result, 'request_id') else 0
                }
            else:
                error = mt5.last_error()
                print(f"[BRIDGE] Order failed. Error: {error}")
                return {
                    "retcode": error[0] if error else 10008,
                    "comment": f"Order failed: {error[1] if error else 'Unknown error'}"
                }
                
        except Exception as e:
            print(f"[BRIDGE] Trade execution error: {e}")
            return {
                "retcode": 10008,  # TRADE_RETCODE_ERROR
                "comment": f"Execution error: {str(e)}"
            }
    
    def start_socket_listener(self):
        """Start socket listener for ping/fire commands"""
        def socket_server():
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('0.0.0.0', self.socket_port))
                server_socket.listen(5)
                
                self.socket_running = True
                print(f"[BRIDGE] Socket listener started on port {self.socket_port}")
                
                while self.socket_running:
                    try:
                        client_socket, addr = server_socket.accept()
                        threading.Thread(
                            target=self.handle_socket_client, 
                            args=(client_socket, addr),
                            daemon=True
                        ).start()
                    except Exception as e:
                        if self.socket_running:
                            print(f"[BRIDGE] Socket accept error: {e}")
                            
            except Exception as e:
                print(f"[BRIDGE] Socket server error: {e}")
            finally:
                if 'server_socket' in locals():
                    server_socket.close()
        
        threading.Thread(target=socket_server, daemon=True).start()
    
    def handle_socket_client(self, client_socket, addr):
        """Handle individual socket client connections"""
        try:
            client_socket.settimeout(10.0)
            
            # Receive command
            data = client_socket.recv(4096)
            if not data:
                return
            
            try:
                command_data = json.loads(data.decode('utf-8'))
                command = command_data.get('command', '').lower()
                
                if command == 'ping':
                    print("[BRIDGE] Command received: PING")
                    
                    # Get MT5 status
                    status = self.get_mt5_status()
                    
                    # Log status
                    print(f"[BRIDGE] Account: {status['account']} | Broker: {status['broker']} | Balance: {status['balance']}")
                    
                    # Send response
                    response = json.dumps(status)
                    client_socket.send(response.encode('utf-8'))
                    
                elif command == 'fire':
                    # Execute trade
                    trade_result = self.execute_mt5_trade(command_data)
                    
                    # Send response
                    response = json.dumps(trade_result)
                    client_socket.send(response.encode('utf-8'))
                    
                else:
                    # Unknown command
                    error_response = {
                        "retcode": 10001,
                        "comment": f"Unknown command: {command}"
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
            except json.JSONDecodeError as e:
                print(f"[BRIDGE] Invalid JSON from {addr}: {e}")
                error_response = {"retcode": 10002, "comment": "Invalid JSON"}
                client_socket.send(json.dumps(error_response).encode('utf-8'))
                
        except Exception as e:
            print(f"[BRIDGE] Socket client error: {e}")
        finally:
            client_socket.close()

# Create agent instance
agent = EnhancedPrimaryAgent()

# Flask HTTP routes (keep existing functionality)
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
        'trades_processed': agent.trades_processed,
        'socket_running': agent.socket_running,
        'socket_port': agent.socket_port,
        'mt5_available': MT5_AVAILABLE,
        'agent_id': 'primary_5555',
        'port': 5555
    })

@app.route('/mt5_status', methods=['GET'])
def mt5_status():
    """Get detailed MT5 status via HTTP"""
    status = agent.get_mt5_status()
    return jsonify(status)

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
    print("[BRIDGE] Enhanced Primary Agent with MT5 Bridge starting...")
    print(f"[BRIDGE] HTTP server: 0.0.0.0:5555")
    print(f"[BRIDGE] Socket listener: 0.0.0.0:{agent.socket_port}")
    print(f"[BRIDGE] MT5 Available: {MT5_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=5555, debug=False)