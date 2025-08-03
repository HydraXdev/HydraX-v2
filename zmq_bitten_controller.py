#!/usr/bin/env python3
"""
BITTEN ZMQ Controller - Complete 3-Way Communication
Implements the full architecture: Commands, Telemetry, and Feedback
"""

import zmq
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
from collections import defaultdict
import threading
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BITTENController')

@dataclass
class UserTelemetry:
    """Real-time user account data"""
    uuid: str
    balance: float
    equity: float
    margin: float
    free_margin: float = 0
    profit: float = 0
    positions: int = 0
    last_update: datetime = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.utcnow()

@dataclass
class TradeResult:
    """Trade execution result"""
    signal_id: str
    status: str
    ticket: int = 0
    price: float = 0
    message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class BITTENZMQController:
    """
    Complete 3-way ZMQ controller for BITTEN
    Manages Commands, Telemetry, and Feedback channels
    """
    
    def __init__(self, command_port=5555, feedback_port=5556):
        self.command_port = command_port
        self.feedback_port = feedback_port
        
        # ZMQ setup
        self.context = zmq.Context()
        self.command_socket = None  # PUSH - sends commands to EA
        self.feedback_socket = None  # PULL - receives telemetry + results
        
        # State tracking
        self.running = False
        self.user_telemetry = {}  # uuid -> UserTelemetry
        self.pending_trades = {}  # signal_id -> trade data
        self.trade_results = []   # List of TradeResult
        
        # Callbacks
        self.telemetry_callbacks = []  # Functions called on telemetry update
        self.trade_callbacks = {}      # signal_id -> callback function
        
        # Threading
        self.feedback_thread = None
        
        # ZMQ Architecture Banner
        print("🧠 BITTEN ZMQ MODE ENABLED — File fallback disabled.")
        print(f"📡 EA connects to 134.199.204.67:{command_port}/{feedback_port}")
        print("⚡ All signals flow through ZMQ sockets - no files, no HTTP")
        
        logger.info("BITTEN ZMQ Controller initialized")
        logger.info(f"Command port: {command_port} (Core → EA)")
        logger.info(f"Feedback port: {feedback_port} (EA → Core)")
        
    def start(self):
        """Start the controller"""
        try:
            # Create command socket (PUSH)
            self.command_socket = self.context.socket(zmq.PUSH)
            self.command_socket.bind(f"tcp://*:{self.command_port}")
            logger.info(f"✅ Command socket bound on port {self.command_port}")
            
            # Create feedback socket (PULL) - receives both telemetry and results
            self.feedback_socket = self.context.socket(zmq.PULL)
            self.feedback_socket.bind(f"tcp://*:{self.feedback_port}")
            self.feedback_socket.setsockopt(zmq.RCVTIMEO, 1000)
            logger.info(f"✅ Feedback socket bound on port {self.feedback_port}")
            
            # Start feedback listener thread
            self.running = True
            self.feedback_thread = threading.Thread(target=self._feedback_listener)
            self.feedback_thread.start()
            
            logger.info("🚀 BITTEN Controller started - all 3 channels active")
            
        except Exception as e:
            logger.error(f"Failed to start controller: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Stop the controller"""
        self.running = False
        
        if self.feedback_thread:
            self.feedback_thread.join()
            
        if self.command_socket:
            self.command_socket.close()
        if self.feedback_socket:
            self.feedback_socket.close()
            
        self.context.term()
        logger.info("Controller stopped")
        
    # ========== CHANNEL 1: COMMANDS (Core → EA) ==========
    
    def send_signal(self, signal_data: Dict, callback: Optional[Callable] = None) -> bool:
        """
        Send trade signal via command channel
        
        Args:
            signal_data: Trade signal with symbol, action, lot, sl, tp
            callback: Optional function called when result received
        """
        if not self.command_socket:
            logger.error("Command socket not initialized")
            return False
            
        try:
            # Generate signal ID if not provided
            if 'signal_id' not in signal_data:
                signal_data['signal_id'] = f"SIG_{int(time.time() * 1000)}"
            
            # Format message
            message = {
                "type": "signal",
                "signal_id": signal_data['signal_id'],
                "symbol": signal_data['symbol'],
                "action": signal_data['action'].lower(),
                "lot": float(signal_data.get('lot', 0.01)),
                "sl": float(signal_data.get('sl', 0)),
                "tp": float(signal_data.get('tp', 0)),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store as pending
            self.pending_trades[message['signal_id']] = message
            
            # Register callback if provided
            if callback:
                self.trade_callbacks[message['signal_id']] = callback
            
            # Send via command channel
            self.command_socket.send_string(json.dumps(message))
            
            logger.info(f"🔥 Sent command: {message['signal_id']} - {message['symbol']} {message['action']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send signal: {e}")
            return False
            
    def close_positions(self, symbol: Optional[str] = None) -> bool:
        """Close positions via command channel"""
        signal = {
            'symbol': symbol or '',
            'action': 'close' if symbol else 'close_all',
            'signal_id': f"CLOSE_{int(time.time() * 1000)}"
        }
        return self.send_signal(signal)
        
    def send_command(self, command: str, params: Dict = None) -> bool:
        """Send control command (status, ping, etc)"""
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
            
    # ========== CHANNEL 2 & 3: TELEMETRY + FEEDBACK (EA → Core) ==========
    
    def _feedback_listener(self):
        """Background thread receiving telemetry and trade results"""
        logger.info("📡 Feedback listener started (telemetry + results)")
        
        while self.running:
            try:
                # Receive message from feedback channel
                message = self.feedback_socket.recv_string(zmq.NOBLOCK)
                
                # Parse JSON
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Route to appropriate handler
                if msg_type == 'telemetry' or msg_type == 'heartbeat':
                    self._handle_telemetry(data)
                elif msg_type == 'trade_result':
                    self._handle_trade_result(data)
                elif msg_type == 'error':
                    self._handle_error(data)
                elif msg_type == 'status':
                    self._handle_status(data)
                elif msg_type == 'pong':
                    logger.info("🏓 Received pong")
                else:
                    logger.info(f"📥 Unknown message type: {msg_type}")
                    
            except zmq.Again:
                # No message available
                pass
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
            except Exception as e:
                logger.error(f"Feedback listener error: {e}")
                
        logger.info("Feedback listener stopped")
        
    def _handle_telemetry(self, data: Dict):
        """Handle telemetry data (Channel 2)"""
        # For heartbeat messages, extract telemetry
        if data.get('type') == 'heartbeat':
            uuid = data.get('uuid', 'default')
            telemetry = UserTelemetry(
                uuid=uuid,
                balance=data.get('balance', 0),
                equity=data.get('equity', 0),
                margin=data.get('margin', 0),
                free_margin=data.get('balance', 0) - data.get('margin', 0),
                profit=data.get('equity', 0) - data.get('balance', 0),
                positions=data.get('positions', 0)
            )
        else:
            # Direct telemetry message
            uuid = data.get('uuid', 'default')
            telemetry = UserTelemetry(
                uuid=uuid,
                balance=data.get('balance', 0),
                equity=data.get('equity', 0),
                margin=data.get('margin', 0),
                free_margin=data.get('free_margin', 0),
                profit=data.get('profit', 0),
                positions=data.get('positions', 0)
            )
        
        # Update state
        self.user_telemetry[uuid] = telemetry
        
        # Log key changes
        logger.info(f"📊 Telemetry: {uuid} - Balance: ${telemetry.balance:.2f}, "
                   f"Equity: ${telemetry.equity:.2f}, P&L: ${telemetry.profit:.2f}")
        
        # Call telemetry callbacks
        for callback in self.telemetry_callbacks:
            try:
                callback(telemetry)
            except Exception as e:
                logger.error(f"Telemetry callback error: {e}")
                
    def _handle_trade_result(self, data: Dict):
        """Handle trade execution result (Channel 3)"""
        result = TradeResult(
            signal_id=data.get('signal_id', ''),
            status=data.get('status', 'unknown'),
            ticket=data.get('ticket', 0),
            price=data.get('price', 0),
            message=data.get('message', '')
        )
        
        # Store result
        self.trade_results.append(result)
        
        # Remove from pending
        if result.signal_id in self.pending_trades:
            del self.pending_trades[result.signal_id]
            
        # Log result
        if result.status == 'success':
            logger.info(f"✅ Trade executed: {result.signal_id} - Ticket {result.ticket} @ {result.price}")
        else:
            logger.error(f"❌ Trade failed: {result.signal_id} - {result.message}")
            
        # Call trade callback if registered
        if result.signal_id in self.trade_callbacks:
            callback = self.trade_callbacks.pop(result.signal_id)
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")
                
    def _handle_error(self, data: Dict):
        """Handle error messages"""
        signal_id = data.get('signal_id', '')
        error = data.get('error', 'Unknown error')
        
        logger.error(f"❌ EA Error: {error} (Signal: {signal_id})")
        
        # Create error result
        result = TradeResult(
            signal_id=signal_id,
            status='error',
            message=error
        )
        
        # Handle as failed trade
        self._handle_trade_result(asdict(result))
        
    def _handle_status(self, data: Dict):
        """Handle status messages"""
        status = data.get('status', '')
        message = data.get('message', '')
        
        if status == 'startup':
            logger.info(f"🚀 EA connected: {message}")
        elif status == 'shutdown':
            logger.info(f"👋 EA disconnecting: {message}")
        else:
            logger.info(f"📊 Status: {status} - {message}")
            
    # ========== PUBLIC API ==========
    
    def register_telemetry_callback(self, callback: Callable):
        """Register a callback for telemetry updates"""
        self.telemetry_callbacks.append(callback)
        
    def get_user_telemetry(self, uuid: str) -> Optional[UserTelemetry]:
        """Get latest telemetry for a user"""
        return self.user_telemetry.get(uuid)
        
    def get_all_telemetry(self) -> Dict[str, UserTelemetry]:
        """Get telemetry for all users"""
        return self.user_telemetry.copy()
        
    def get_trade_results(self, limit: int = 10) -> List[TradeResult]:
        """Get recent trade results"""
        return self.trade_results[-limit:]
        
    def get_pending_trades(self) -> Dict:
        """Get trades awaiting confirmation"""
        return self.pending_trades.copy()

# ========== INTEGRATION HELPERS ==========

def execute_bitten_trade(signal_data: Dict, callback: Optional[Callable] = None) -> bool:
    """
    Execute a trade through BITTEN ZMQ system
    Drop-in replacement for file-based execution
    """
    controller = get_bitten_controller()
    return controller.send_signal(signal_data, callback)

def get_bitten_controller() -> BITTENZMQController:
    """Get or create singleton controller instance"""
    global _controller_instance
    if '_controller_instance' not in globals():
        _controller_instance = BITTENZMQController()
        _controller_instance.start()
    return _controller_instance

# ========== TEST INTERFACE ==========

def main():
    """Interactive test interface"""
    controller = BITTENZMQController()
    
    # Register telemetry callback
    def on_telemetry(telemetry: UserTelemetry):
        if telemetry.profit != 0:
            icon = "📈" if telemetry.profit > 0 else "📉"
            print(f"\n{icon} P&L Update: ${telemetry.profit:.2f}")
            
    controller.register_telemetry_callback(on_telemetry)
    
    try:
        controller.start()
        
        print("\n" + "="*60)
        print("BITTEN ZMQ Controller - 3-Way Communication Test")
        print("="*60)
        print("Channels:")
        print("  1. Command (5555): Core → EA trade signals")
        print("  2. Telemetry (5556): EA → Core account data")
        print("  3. Feedback (5556): EA → Core trade results")
        print("="*60)
        print("\nCommands:")
        print("  1 - Send BUY signal (XAUUSD)")
        print("  2 - Send SELL signal (EURUSD)")
        print("  3 - Close all positions")
        print("  4 - Show telemetry")
        print("  5 - Show recent trades")
        print("  p - Ping EA")
        print("  q - Quit")
        print("="*60)
        
        while True:
            try:
                cmd = input("\nCommand> ").strip().lower()
                
                if cmd == 'q':
                    break
                    
                elif cmd == '1':
                    # BUY XAUUSD
                    def on_result(result: TradeResult):
                        print(f"\n🎯 Trade callback: {result.status} - {result.message}")
                        
                    signal = {
                        'symbol': 'XAUUSD',
                        'action': 'buy',
                        'lot': 0.1,
                        'sl': 200,
                        'tp': 400
                    }
                    controller.send_signal(signal, on_result)
                    
                elif cmd == '2':
                    # SELL EURUSD
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
                    controller.close_positions()
                    
                elif cmd == '4':
                    # Show telemetry
                    print("\n📊 Current Telemetry:")
                    for uuid, telem in controller.get_all_telemetry().items():
                        print(f"  {uuid}: Balance=${telem.balance:.2f}, "
                              f"Equity=${telem.equity:.2f}, Positions={telem.positions}")
                        
                elif cmd == '5':
                    # Show trades
                    print("\n📜 Recent Trades:")
                    for result in controller.get_trade_results():
                        status = "✅" if result.status == "success" else "❌"
                        print(f"  {status} {result.signal_id}: {result.message}")
                        
                elif cmd == 'p':
                    # Ping
                    controller.send_command('ping')
                    
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
                
    finally:
        controller.stop()
        print("\n✅ Controller stopped")

if __name__ == "__main__":
    main()