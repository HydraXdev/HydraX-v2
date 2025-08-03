#!/usr/bin/env python3
"""
ZMQ Trade Controller - Linux side
Sends commands to MT5 EA and receives results
Matches the EA v7 architecture (PUSH commands, PULL results)
"""

import zmq
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ZMQTradeController')

class ZMQTradeController:
    """
    Controller that EA v7 connects to
    - Binds PUSH socket on 5555 (EA pulls commands)
    - Binds PULL socket on 5556 (EA pushes results)
    """
    
    def __init__(self, command_port=5555, result_port=5556):
        self.command_port = command_port
        self.result_port = result_port
        
        # ZMQ setup
        self.context = zmq.Context()
        self.command_socket = None  # PUSH - sends to EA
        self.result_socket = None   # PULL - receives from EA
        
        # State tracking
        self.running = False
        self.connected_eas = {}
        self.pending_trades = {}
        self.result_thread = None
        
        logger.info(f"ZMQ Trade Controller initialized")
        logger.info(f"Command port: {command_port} (EA pulls from here)")
        logger.info(f"Result port: {result_port} (EA pushes to here)")
        
    def start(self):
        """Start the controller"""
        try:
            # Create command socket (PUSH)
            self.command_socket = self.context.socket(zmq.PUSH)
            self.command_socket.bind(f"tcp://*:{self.command_port}")
            logger.info(f"✅ Command socket bound on port {self.command_port}")
            
            # Create result socket (PULL)
            self.result_socket = self.context.socket(zmq.PULL)
            self.result_socket.bind(f"tcp://*:{self.result_port}")
            self.result_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            logger.info(f"✅ Result socket bound on port {self.result_port}")
            
            # Start result listener thread
            self.running = True
            self.result_thread = threading.Thread(target=self._result_listener)
            self.result_thread.start()
            
            logger.info("🚀 ZMQ Trade Controller started and waiting for EA connections")
            
        except Exception as e:
            logger.error(f"Failed to start controller: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Stop the controller"""
        self.running = False
        
        if self.result_thread:
            self.result_thread.join()
            
        if self.command_socket:
            self.command_socket.close()
        if self.result_socket:
            self.result_socket.close()
            
        self.context.term()
        logger.info("Controller stopped")
        
    def send_signal(self, signal_data: Dict) -> bool:
        """
        Send a trade signal to EA
        
        Args:
            signal_data: Dict with symbol, action, lot, sl, tp, signal_id
        """
        if not self.command_socket:
            logger.error("Command socket not initialized")
            return False
            
        try:
            # Format message for EA
            message = {
                "type": "signal",
                "signal_id": signal_data.get('signal_id', f"SIG_{int(time.time())}"),
                "symbol": signal_data['symbol'],
                "action": signal_data['action'].lower(),  # buy/sell/close
                "lot": signal_data.get('lot', 0.01),
                "sl": signal_data.get('sl', 0),
                "tp": signal_data.get('tp', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store as pending
            self.pending_trades[message['signal_id']] = message
            
            # Send to EA
            json_str = json.dumps(message)
            self.command_socket.send_string(json_str)
            
            logger.info(f"📤 Sent signal: {message['signal_id']} - {message['symbol']} {message['action']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send signal: {e}")
            return False
            
    def send_command(self, command: str, params: Dict = None) -> bool:
        """Send a command to EA (status, shutdown, reset, etc)"""
        if not self.command_socket:
            return False
            
        try:
            message = {
                "type": "command",
                "command": command,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if params:
                message.update(params)
                
            self.command_socket.send_string(json.dumps(message))
            logger.info(f"📤 Sent command: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
            
    def send_config(self, param: str, value: str) -> bool:
        """Send configuration update to EA"""
        if not self.command_socket:
            return False
            
        try:
            message = {
                "type": "config",
                "param": param,
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.command_socket.send_string(json.dumps(message))
            logger.info(f"📤 Sent config: {param} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send config: {e}")
            return False
            
    def ping_ea(self) -> bool:
        """Send ping to check if EA is alive"""
        try:
            message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.command_socket.send_string(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"Failed to send ping: {e}")
            return False
            
    def _result_listener(self):
        """Background thread to receive results from EA"""
        logger.info("📡 Result listener started")
        
        while self.running:
            try:
                # Try to receive message
                message = self.result_socket.recv_string(zmq.NOBLOCK)
                
                # Parse JSON
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Handle different message types
                if msg_type == 'heartbeat':
                    self._handle_heartbeat(data)
                elif msg_type == 'trade_result':
                    self._handle_trade_result(data)
                elif msg_type == 'status':
                    self._handle_status(data)
                elif msg_type == 'error':
                    self._handle_error(data)
                elif msg_type == 'pong':
                    logger.info("🏓 Received pong")
                else:
                    logger.info(f"📥 Received: {message}")
                    
            except zmq.Again:
                # No message available, continue
                pass
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
            except Exception as e:
                logger.error(f"Result listener error: {e}")
                
        logger.info("Result listener stopped")
        
    def _handle_heartbeat(self, data: Dict):
        """Handle heartbeat from EA"""
        balance = data.get('balance', 0)
        equity = data.get('equity', 0)
        positions = data.get('positions', 0)
        
        logger.info(f"💓 Heartbeat: Balance=${balance:.2f}, Equity=${equity:.2f}, Positions={positions}")
        
    def _handle_trade_result(self, data: Dict):
        """Handle trade execution result"""
        signal_id = data.get('signal_id', '')
        status = data.get('status', '')
        ticket = data.get('ticket', 0)
        price = data.get('price', 0)
        message = data.get('message', '')
        
        if status == 'success':
            logger.info(f"✅ Trade executed: {signal_id} - Ticket {ticket} @ {price}")
        else:
            logger.error(f"❌ Trade failed: {signal_id} - {message}")
            
        # Remove from pending
        if signal_id in self.pending_trades:
            del self.pending_trades[signal_id]
            
    def _handle_status(self, data: Dict):
        """Handle status message from EA"""
        status = data.get('status', '')
        message = data.get('message', '')
        
        if status == 'startup':
            logger.info(f"🚀 EA connected: {message}")
        elif status == 'shutdown':
            logger.info(f"👋 EA disconnecting: {message}")
        elif status == 'reconnected':
            logger.info(f"🔄 EA reconnected: {message}")
        else:
            logger.info(f"📊 Status: {status} - {message}")
            
    def _handle_error(self, data: Dict):
        """Handle error message from EA"""
        error = data.get('error', '')
        signal_id = data.get('signal_id', '')
        
        logger.error(f"❌ EA Error: {error} (Signal: {signal_id})")

def main():
    """Test the controller"""
    import sys
    
    controller = ZMQTradeController()
    
    try:
        controller.start()
        
        print("\n" + "="*60)
        print("ZMQ Trade Controller Running")
        print("="*60)
        print(f"Command port: 5555 (EA connects here)")
        print(f"Result port: 5556 (EA sends results here)")
        print("="*60)
        print("\nCommands:")
        print("  1 - Send test BUY signal")
        print("  2 - Send test SELL signal")
        print("  3 - Close all positions")
        print("  4 - Request status")
        print("  5 - Ping EA")
        print("  q - Quit")
        print("="*60)
        
        while True:
            try:
                cmd = input("\nEnter command: ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == '1':
                    # Test BUY
                    signal = {
                        'symbol': 'XAUUSD',
                        'action': 'buy',
                        'lot': 0.1,
                        'sl': 200,  # 200 points
                        'tp': 400   # 400 points
                    }
                    controller.send_signal(signal)
                    
                elif cmd == '2':
                    # Test SELL
                    signal = {
                        'symbol': 'EURUSD',
                        'action': 'sell',
                        'lot': 0.01,
                        'sl': 50,
                        'tp': 100
                    }
                    controller.send_signal(signal)
                    
                elif cmd == '3':
                    # Close all
                    signal = {
                        'symbol': '',
                        'action': 'close_all'
                    }
                    controller.send_signal(signal)
                    
                elif cmd == '4':
                    # Status
                    controller.send_command('status')
                    
                elif cmd == '5':
                    # Ping
                    controller.ping_ea()
                    
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
                
    finally:
        controller.stop()
        print("\nController stopped")

if __name__ == "__main__":
    main()