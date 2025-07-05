"""
MT5 Bridge Adapter for BITTEN System - SECURE VERSION
Converts between Python HTTP API and MT5 EA file-based communication
Compatible with BITTENBridge_HYBRID_v1.2_PRODUCTION_SECURE.mq5

OVERWATCH: "Trust no one, validate everything. Even your own code."
"""

import os
import json
import time
import threading
import logging
import fcntl
import csv
import io
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict
from queue import Queue
from decimal import Decimal
import platform

from .security_utils import (
    validate_symbol, validate_direction, validate_volume,
    validate_safe_path, secure_file_write, secure_file_read,
    safe_json_loads, safe_json_dumps, sanitize_log_output,
    sanitize_trade_comment, RateLimiter, SecurityError,
    ValidationError, calculate_file_hmac, verify_file_hmac
)

logger = logging.getLogger(__name__)

# DRILL: "Lock and load, secure parameters incoming!"
@dataclass
class TradeInstruction:
    """Trade instruction format for MT5 EA - HARDENED"""
    trade_id: str
    symbol: str
    direction: str  # BUY or SELL
    lot: Decimal
    price: Decimal = Decimal('0')  # 0 for market orders
    take_profit: Decimal = Decimal('0')
    stop_loss: Decimal = Decimal('0')
    comment: str = ""
    hmac_signature: str = ""  # NEXUS: "Every packet needs authentication"
    
    def to_csv(self) -> str:
        """Convert to CSV format with injection protection"""
        # DOC: "Clean data is healthy data, soldier"
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow([
            self.trade_id,
            self.symbol,
            self.direction.upper(),
            str(self.lot),
            str(self.price),
            str(self.take_profit),
            str(self.stop_loss),
            sanitize_trade_comment(self.comment),
            self.hmac_signature
        ])
        return output.getvalue().strip()

@dataclass
class TradeResult:
    """Trade execution result from MT5 EA - FORTIFIED"""
    trade_id: str
    status: str
    ticket: int = 0
    message: str = ""
    timestamp: str = ""
    balance: Decimal = Decimal('0')
    equity: Decimal = Decimal('0')
    margin: Decimal = Decimal('0')
    free_margin: Decimal = Decimal('0')
    hmac_valid: bool = False
    
    @classmethod
    def from_json(cls, json_str: str, verify_hmac: bool = True) -> 'TradeResult':
        """Parse JSON result with validation"""
        try:
            data = safe_json_loads(json_str)
            account = data.get('account', {})
            
            # OVERWATCH: "Numbers don't lie, but they can be manipulated"
            return cls(
                trade_id=str(data.get('id', '')),
                status=str(data.get('status', 'unknown')),
                ticket=int(data.get('ticket', 0)),
                message=str(data.get('message', ''))[:500],  # Limit message length
                timestamp=str(data.get('timestamp', '')),
                balance=Decimal(str(account.get('balance', 0))),
                equity=Decimal(str(account.get('equity', 0))),
                margin=Decimal(str(account.get('margin', 0))),
                free_margin=Decimal(str(account.get('free_margin', 0))),
                hmac_valid=data.get('hmac_valid', False) if verify_hmac else True
            )
        except Exception as e:
            logger.error(sanitize_log_output(f"Failed to parse trade result: {e}"))
            raise ValidationError(f"Invalid trade result format")

@dataclass
class BridgeStatus:
    """Bridge status from MT5 EA - REINFORCED"""
    type: str
    message: str
    timestamp: str
    connected: bool
    positions: int
    orders: int
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BridgeStatus':
        """Parse JSON status with bounds checking"""
        try:
            data = safe_json_loads(json_str)
            
            # DRILL: "Status reports must be by the book!"
            return cls(
                type=str(data.get('type', ''))[:50],
                message=str(data.get('message', ''))[:500],
                timestamp=str(data.get('timestamp', ''))[:50],
                connected=bool(data.get('connected', False)),
                positions=max(0, min(int(data.get('positions', 0)), 1000)),  # Reasonable bounds
                orders=max(0, min(int(data.get('orders', 0)), 1000))
            )
        except Exception as e:
            logger.error(f"Failed to parse bridge status: {e}")
            raise ValidationError(f"Invalid bridge status format")

class MT5BridgeAdapterSecure:
    """
    SECURE Adapter to bridge between Python BITTEN system and MT5 EA
    Handles file-based communication with military-grade security
    
    NEXUS: "Every connection is a potential breach. Secure it."
    """
    
    def __init__(self, mt5_files_path: Optional[str] = None, 
                 hmac_key: Optional[bytes] = None,
                 max_trades_per_minute: int = 10):
        """
        Initialize the secure bridge adapter
        
        Args:
            mt5_files_path: Path to MT5 terminal Files folder
            hmac_key: Secret key for HMAC signatures
            max_trades_per_minute: Rate limit for trades
        """
        # DOC: "Set up the perimeter, check your six"
        self.mt5_files_path = self._setup_mt5_path(mt5_files_path)
        self.hmac_key = hmac_key or os.urandom(32)
        
        # File names matching EA expectations
        self.instruction_file = "bitten_instructions_secure.txt"
        self.result_file = "bitten_results_secure.txt"
        self.status_file = "bitten_status_secure.txt"
        
        # Validate paths upfront
        self.instruction_path = validate_safe_path(self.mt5_files_path, self.instruction_file)
        self.result_path = validate_safe_path(self.mt5_files_path, self.result_file)
        self.status_path = validate_safe_path(self.mt5_files_path, self.status_file)
        
        # State management with thread safety
        self.running = False
        self.monitor_thread = None
        self.result_queue = Queue()
        self.last_status = None
        self.pending_trades = {}  # trade_id -> timestamp
        self._lock = threading.RLock()
        
        # Security features
        self.rate_limiter = RateLimiter(max_requests=max_trades_per_minute, window_seconds=60)
        
        # Timeouts
        self.trade_timeout = 30  # seconds to wait for trade result
        self.status_check_interval = 0.5  # seconds between status checks
        
        logger.info(sanitize_log_output(f"MT5 Secure Bridge initialized with path: {self.mt5_files_path}"))
    
    def _setup_mt5_path(self, custom_path: Optional[str]) -> str:
        """Setup and validate MT5 files path with security checks"""
        if custom_path:
            path = Path(custom_path)
            if not path.exists() or not path.is_dir():
                raise ValueError(f"Invalid MT5 files path: {custom_path}")
            
            # DRILL: "Check for enemy infiltration attempts"
            abs_path = path.resolve()
            if '..' in str(abs_path) or str(abs_path).count('/') > 10:
                raise SecurityError("Suspicious path detected")
            
            return str(abs_path)
        
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
        
        # Default fallback with secure permissions
        default_path = "./mt5_files_secure"
        os.makedirs(default_path, mode=0o700, exist_ok=True)
        logger.warning(f"Using secure local directory for MT5 files: {default_path}")
        return default_path
    
    def start(self):
        """Start the bridge adapter monitor thread"""
        with self._lock:
            if self.running:
                logger.warning("Bridge adapter already running")
                return
            
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, 
                daemon=True,
                name="MT5BridgeMonitor"
            )
            self.monitor_thread.start()
            logger.info("MT5 Secure Bridge Adapter activated - NEXUS online")
    
    def stop(self):
        """Stop the bridge adapter"""
        with self._lock:
            self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("MT5 Secure Bridge Adapter deactivated - NEXUS offline")
    
    def _monitor_loop(self):
        """Main monitoring loop with exception isolation"""
        # DOC: "Keep watch, stay vigilant"
        while self.running:
            try:
                # Check for trade results with file locking
                if os.path.exists(self.result_path):
                    self._process_result_file()
                
                # Check for status updates
                if os.path.exists(self.status_path):
                    self._process_status_file()
                
                # Clean up old pending trades
                self._cleanup_pending_trades()
                
            except Exception as e:
                logger.error(sanitize_log_output(f"Monitor loop error: {e}"))
            
            time.sleep(self.status_check_interval)
    
    def _process_result_file(self):
        """Process trade result file with integrity checks"""
        try:
            # NEXUS: "Verify before you trust"
            content = secure_file_read(self.result_path)
            
            if content:
                # Verify file integrity if HMAC is present
                lines = content.strip().split('\n')
                if len(lines) > 1 and lines[-1].startswith("HMAC:"):
                    expected_hmac = lines[-1].replace("HMAC:", "").strip()
                    actual_content = '\n'.join(lines[:-1])
                    
                    if not verify_file_hmac(self.result_path, expected_hmac, self.hmac_key):
                        logger.error("HMAC verification failed for result file")
                        os.remove(self.result_path)
                        return
                    
                    content = actual_content
                
                result = TradeResult.from_json(content)
                
                # Put result in queue for waiting threads
                with self._lock:
                    self.result_queue.put(result)
                    
                    # Remove from pending
                    if result.trade_id in self.pending_trades:
                        del self.pending_trades[result.trade_id]
                
                logger.info(sanitize_log_output(
                    f"Trade result received: {result.trade_id} - {result.status}"
                ))
                
                # Delete the file after processing
                os.remove(self.result_path)
                
        except Exception as e:
            logger.error(sanitize_log_output(f"Error processing result file: {e}"))
            # Remove potentially corrupted file
            try:
                os.remove(self.result_path)
            except:
                pass
    
    def _process_status_file(self):
        """Process status file with validation"""
        try:
            content = secure_file_read(self.status_path)
            
            if content:
                status = BridgeStatus.from_json(content)
                
                with self._lock:
                    self.last_status = status
                
                # OVERWATCH: "Log everything, trust nothing"
                if status.type in ['error', 'trade_executed']:
                    logger.info(sanitize_log_output(
                        f"EA Status: {status.type} - {status.message}"
                    ))
                
        except Exception as e:
            logger.error(sanitize_log_output(f"Error processing status file: {e}"))
    
    def _cleanup_pending_trades(self):
        """Remove timed-out pending trades with thread safety"""
        current_time = time.time()
        expired = []
        
        with self._lock:
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
                     user_id: str,
                     symbol: str,
                     direction: str,
                     volume: float,
                     stop_loss: float = 0,
                     take_profit: float = 0,
                     comment: str = "") -> Dict[str, Any]:
        """
        Execute a trade through the MT5 EA with full validation
        
        DRILL: "Check your weapon, check your target, fire when ready"
        
        Args:
            user_id: User identifier for rate limiting
            symbol: Trading symbol (e.g., "XAUUSD")
            direction: "buy" or "sell"
            volume: Lot size
            stop_loss: Stop loss price (0 for none)
            take_profit: Take profit price (0 for none)
            comment: Trade comment
            
        Returns:
            Dictionary with trade result
        """
        # Rate limiting check
        if not self.rate_limiter.check_rate_limit(user_id):
            return {
                'success': False,
                'message': 'Rate limit exceeded. Too many trades.',
                'error_code': 'RATE_LIMIT'
            }
        
        try:
            # DRILL: "Validate all inputs, no exceptions!"
            symbol = validate_symbol(symbol)
            direction = validate_direction(direction)
            volume_decimal = validate_volume(volume)
            
            # Validate prices if provided
            from .security_utils import validate_price
            sl_decimal = validate_price(stop_loss) if stop_loss > 0 else Decimal('0')
            tp_decimal = validate_price(take_profit) if take_profit > 0 else Decimal('0')
            
            # Generate unique trade ID with timestamp
            trade_id = f"T{int(time.time() * 1000)}_{user_id[:8]}"
            
            # Create instruction with signature
            instruction = TradeInstruction(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction.upper(),
                lot=volume_decimal,
                price=Decimal('0'),  # Market order
                take_profit=tp_decimal,
                stop_loss=sl_decimal,
                comment=sanitize_trade_comment(comment)
            )
            
            # Calculate HMAC for instruction
            instruction_data = instruction.to_csv()
            instruction.hmac_signature = calculate_file_hmac(
                self.instruction_path, 
                self.hmac_key
            )
            
            # Write instruction file with atomic operation
            secure_file_write(self.instruction_path, instruction_data)
            
            logger.info(sanitize_log_output(f"Trade instruction written: {trade_id}"))
            
            # Track pending trade
            with self._lock:
                self.pending_trades[trade_id] = time.time()
            
            # Wait for result with timeout
            start_time = time.time()
            while time.time() - start_time < self.trade_timeout:
                try:
                    # Check queue for our result
                    result = self.result_queue.get(timeout=0.1)
                    if result.trade_id == trade_id:
                        # OVERWATCH: "Mission complete, counting the profits"
                        return {
                            'success': result.status == 'success',
                            'trade_id': trade_id,
                            'ticket': result.ticket,
                            'message': result.message,
                            'timestamp': result.timestamp,
                            'account': {
                                'balance': float(result.balance),
                                'equity': float(result.equity),
                                'margin': float(result.margin),
                                'free_margin': float(result.free_margin)
                            },
                            'hmac_valid': result.hmac_valid
                        }
                    else:
                        # Not our result, put it back
                        self.result_queue.put(result)
                except:
                    continue
            
            # Timeout - DOC: "Sometimes the market doesn't respond"
            return {
                'success': False,
                'trade_id': trade_id,
                'message': 'Trade execution timeout - EA not responding',
                'error_code': 'TIMEOUT'
            }
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                'success': False,
                'message': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
        except Exception as e:
            logger.error(sanitize_log_output(f"Error executing trade: {e}"))
            return {
                'success': False,
                'message': 'Bridge error occurred',
                'error_code': 'BRIDGE_ERROR'
            }
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current EA status with thread safety"""
        with self._lock:
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
        with self._lock:
            return self.last_status.connected if self.last_status else False


# Singleton instance with thread safety
_adapter_instance = None
_adapter_lock = threading.Lock()

def get_secure_bridge_adapter(mt5_files_path: Optional[str] = None,
                            hmac_key: Optional[bytes] = None) -> MT5BridgeAdapterSecure:
    """Get or create the secure bridge adapter instance"""
    global _adapter_instance
    
    with _adapter_lock:
        if _adapter_instance is None:
            _adapter_instance = MT5BridgeAdapterSecure(mt5_files_path, hmac_key)
            _adapter_instance.start()
    
    return _adapter_instance


# Example usage with military precision
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # DRILL: "This is a drill, not the real deal!"
    logger.info("=== MT5 SECURE BRIDGE TEST SEQUENCE INITIATED ===")
    
    # Create adapter
    adapter = get_secure_bridge_adapter()
    
    # Example trade with full validation
    result = adapter.execute_trade(
        user_id="test_user_001",
        symbol="XAUUSD",
        direction="buy",
        volume=0.01,
        stop_loss=1950.00,
        take_profit=1970.00,
        comment="BITTEN test trade - secure mode"
    )
    
    print(f"Trade result: {result}")
    
    # Check status
    status = adapter.get_status()
    print(f"EA Status: {status}")
    
    # OVERWATCH: "Test complete. Remember, in production there are no second chances."