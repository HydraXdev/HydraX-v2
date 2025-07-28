"""
MT5 Bridge Adapter for BITTEN System
Converts between Python HTTP API and MT5 EA file-based communication
Compatible with BITTENBridge.mq5
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from queue import Queue
import platform

logger = logging.getLogger(__name__)

@dataclass
class TradeInstruction:
    """Trade instruction format for MT5 EA"""
    trade_id: str
    symbol: str
    direction: str  # BUY or SELL
    lot: float
    price: float = 0  # 0 for market orders
    take_profit: float = 0
    stop_loss: float = 0
    
    def to_csv(self) -> str:
        """Convert to CSV format expected by EA"""
        return f"{self.trade_id},{self.symbol},{self.direction.upper()},{self.lot},{self.price},{self.take_profit},{self.stop_loss}"

@dataclass
class TradeResult:
    """Trade execution result from MT5 EA"""
    trade_id: str
    status: str
    ticket: int = 0
    message: str = ""
    timestamp: str = ""
    balance: float = 0
    equity: float = 0
    margin: float = 0
    free_margin: float = 0
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TradeResult':
        """Parse JSON result from EA"""
        data = json.loads(json_str)
        account = data.get('account', {})
        return cls(
            trade_id=data.get('id', ''),
            status=data.get('status', 'unknown'),
            ticket=data.get('ticket', 0),
            message=data.get('message', ''),
            timestamp=data.get('timestamp', ''),
            balance=account.get('balance', 0),
            equity=account.get('equity', 0),
            margin=account.get('margin', 0),
            free_margin=account.get('free_margin', 0)
        )

@dataclass
class BridgeStatus:
    """Bridge status from MT5 EA"""
    type: str
    message: str
    timestamp: str
    connected: bool
    positions: int
    orders: int
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BridgeStatus':
        """Parse JSON status from EA"""
        data = json.loads(json_str)
        return cls(
            type=data.get('type', ''),
            message=data.get('message', ''),
            timestamp=data.get('timestamp', ''),
            connected=data.get('connected', False),
            positions=data.get('positions', 0),
            orders=data.get('orders', 0)
        )

class MT5BridgeAdapter:
    """
    Adapter to bridge between Python BITTEN system and MT5 EA
    Handles file-based communication with BITTENBridge.mq5
    """
    
    def __init__(self, mt5_files_path: Optional[str] = None):
        """
        Initialize the bridge adapter
        
        Args:
            mt5_files_path: Path to MT5 terminal Files folder
                           If None, will attempt to auto-detect
        """
        self.mt5_files_path = self._setup_mt5_path(mt5_files_path)
        
        # File names matching EA expectations
        self.instruction_file = "bitten_instructions.txt"
        self.result_file = "bitten_results.txt"
        self.status_file = "bitten_status.txt"
        
        # Full paths
        self.instruction_path = os.path.join(self.mt5_files_path, self.instruction_file)
        self.result_path = os.path.join(self.mt5_files_path, self.result_file)
        self.status_path = os.path.join(self.mt5_files_path, self.status_file)
        
        # State management
        self.running = False
        self.monitor_thread = None
        self.result_queue = Queue()
        self.last_status = None
        self.pending_trades = {}  # trade_id -> timestamp
        
        # Timeouts
        self.trade_timeout = 30  # seconds to wait for trade result
        self.status_check_interval = 0.5  # seconds between status checks
        
        logger.info(f"MT5 Bridge Adapter initialized with path: {self.mt5_files_path}")
    
    def _setup_mt5_path(self, custom_path: Optional[str]) -> str:
        """Setup and validate MT5 files path"""
        if custom_path:
            path = Path(custom_path)
            if path.exists() and path.is_dir():
                return str(path)
            else:
                raise ValueError(f"Invalid MT5 files path: {custom_path}")
        
        # Try to auto-detect MT5 path based on platform
        if platform.system() == "Windows":
            # Common Windows paths
            possible_paths = [
                r"C:\Users\%USERNAME%\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
                r"C:\Program Files\MetaTrader 5\MQL5\Files",
                r"C:\MT5\MQL5\Files"
            ]
            
            for path in possible_paths:
                expanded = os.path.expandvars(path)
                if os.path.exists(expanded):
                    return expanded
        
        # Default fallback
        default_path = "./mt5_files"
        os.makedirs(default_path, exist_ok=True)
        logger.warning(f"Using local directory for MT5 files: {default_path}")
        return default_path
    
    def start(self):
        """Start the bridge adapter monitor thread"""
        if self.running:
            logger.warning("Bridge adapter already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("MT5 Bridge Adapter started")
    
    def stop(self):
        """Stop the bridge adapter"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("MT5 Bridge Adapter stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop for EA responses"""
        while self.running:
            try:
                # Check for trade results
                if os.path.exists(self.result_path):
                    self._process_result_file()
                
                # Check for status updates
                if os.path.exists(self.status_path):
                    self._process_status_file()
                
                # Clean up old pending trades
                self._cleanup_pending_trades()
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            time.sleep(self.status_check_interval)
    
    def _process_result_file(self):
        """Process trade result file from EA"""
        try:
            with open(self.result_path, 'r') as f:
                content = f.read().strip()
            
            if content:
                result = TradeResult.from_json(content)
                
                # Put result in queue for waiting threads
                self.result_queue.put(result)
                
                # Remove from pending
                if result.trade_id in self.pending_trades:
                    del self.pending_trades[result.trade_id]
                
                logger.info(f"Trade result received: {result.trade_id} - {result.status}")
                
                # Delete the file after processing
                os.remove(self.result_path)
                
        except Exception as e:
            logger.error(f"Error processing result file: {e}")
    
    def _process_status_file(self):
        """Process status file from EA"""
        try:
            with open(self.status_path, 'r') as f:
                content = f.read().strip()
            
            if content:
                status = BridgeStatus.from_json(content)
                self.last_status = status
                
                # Log important status changes
                if status.type in ['error', 'trade_executed']:
                    logger.info(f"EA Status: {status.type} - {status.message}")
                
        except Exception as e:
            logger.error(f"Error processing status file: {e}")
    
    def _cleanup_pending_trades(self):
        """Remove timed-out pending trades"""
        current_time = time.time()
        expired = []
        
        for trade_id, timestamp in self.pending_trades.items():
            if current_time - timestamp > self.trade_timeout:
                expired.append(trade_id)
        
        for trade_id in expired:
            logger.warning(f"Trade timeout: {trade_id}")
            del self.pending_trades[trade_id]
            
            # Add timeout result to queue
            timeout_result = TradeResult(
                trade_id=trade_id,
                status="timeout",
                message="No response from EA within timeout period"
            )
            self.result_queue.put(timeout_result)
    
    def execute_trade(self, 
                     symbol: str,
                     direction: str,
                     volume: float,
                     stop_loss: float = 0,
                     take_profit: float = 0,
                     comment: str = "") -> Dict[str, Any]:
        """
        Execute a trade through the MT5 EA
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD")
            direction: "buy" or "sell"
            volume: Lot size
            stop_loss: Stop loss price (0 for none)
            take_profit: Take profit price (0 for none)
            comment: Trade comment
            
        Returns:
            Dictionary with trade result
        """
        # Generate unique trade ID
        trade_id = f"T{int(time.time() * 1000)}"
        
        # Create instruction
        instruction = TradeInstruction(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction.upper(),
            lot=volume,
            price=0,  # Market order
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        
        # Write instruction file
        try:
            with open(self.instruction_path, 'w') as f:
                f.write(instruction.to_csv())
            
            logger.info(f"Trade instruction written: {trade_id}")
            
            # Track pending trade
            self.pending_trades[trade_id] = time.time()
            
            # Wait for result
            start_time = time.time()
            while time.time() - start_time < self.trade_timeout:
                try:
                    # Check queue for our result
                    result = self.result_queue.get(timeout=0.1)
                    if result.trade_id == trade_id:
                        return {
                            'success': result.status == 'success',
                            'trade_id': trade_id,
                            'ticket': result.ticket,
                            'message': result.message,
                            'timestamp': result.timestamp,
                            'account': {
                                'balance': result.balance,
                                'equity': result.equity,
                                'margin': result.margin,
                                'free_margin': result.free_margin
                            }
                        }
                    else:
                        # Not our result, put it back
                        self.result_queue.put(result)
                except:
                    continue
            
            # Timeout
            return {
                'success': False,
                'trade_id': trade_id,
                'message': 'Trade execution timeout',
                'error_code': 'TIMEOUT'
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'trade_id': trade_id,
                'message': str(e),
                'error_code': 'BRIDGE_ERROR'
            }
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current EA status"""
        if self.last_status:
            return {
                'connected': self.last_status.connected,
                'positions': self.last_status.positions,
                'orders': self.last_status.orders,
                'message': self.last_status.message,
                'timestamp': self.last_status.timestamp
            }
        return None
    
    def is_connected(self) -> bool:
        """Check if EA is connected"""
        return self.last_status.connected if self.last_status else False
    
    def get_trade_result(self, trade_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Get trade result for a specific trade ID with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if result is in queue
                while not self.result_queue.empty():
                    result = self.result_queue.get()
                    if result.trade_id == trade_id:
                        return {
                            'trade_id': result.trade_id,
                            'status': result.status,
                            'ticket': result.ticket,
                            'message': result.message,
                            'timestamp': result.timestamp,
                            'balance': result.balance,
                            'equity': result.equity,
                            'margin': result.margin,
                            'free_margin': result.free_margin
                        }
                
                # Brief sleep to avoid busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error checking trade result for {trade_id}: {e}")
                break
        
        return None  # Timeout or error

# Singleton instance
_adapter_instance = None

def get_bridge_adapter(mt5_files_path: Optional[str] = None) -> MT5BridgeAdapter:
    """Get or create the bridge adapter instance"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = MT5BridgeAdapter(mt5_files_path)
        _adapter_instance.start()
    return _adapter_instance

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create adapter
    adapter = get_bridge_adapter()
    
    # Example trade
    result = adapter.execute_trade(
        symbol="XAUUSD",
        direction="buy",
        volume=0.01,
        stop_loss=1950.00,
        take_profit=1970.00
    )
    
    print(f"Trade result: {result}")
    
    # Check status
    status = adapter.get_status()
    print(f"EA Status: {status}")