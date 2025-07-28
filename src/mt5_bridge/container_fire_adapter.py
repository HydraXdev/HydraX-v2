#!/usr/bin/env python3
"""
Container Fire Adapter - Handles fire.txt communication with MT5 containers
Replaces file-based communication with proper container execution
"""

import json
import time
import docker
import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import threading
from queue import Queue, Empty

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Trade signal format for fire.txt"""
    signal_id: str
    symbol: str
    type: str  # buy/sell/close
    lot: float
    sl: float = 0
    tp: float = 0
    comment: str = ""
    action: str = "trade"  # trade or close
    
    def to_fire_json(self) -> str:
        """Convert to fire.txt JSON format"""
        return json.dumps({
            "signal_id": self.signal_id,
            "action": self.action,
            "symbol": self.symbol,
            "type": self.type,
            "lot": self.lot,
            "sl": self.sl,
            "tp": self.tp,
            "comment": self.comment
        })

@dataclass 
class TradeResult:
    """Trade execution result from MT5"""
    signal_id: str
    status: str  # success/error/closed
    ticket: int = 0
    message: str = ""
    timestamp: str = ""
    account: Dict[str, float] = None
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TradeResult':
        """Parse JSON result from trade_result.txt"""
        try:
            data = json.loads(json_str)
            return cls(
                signal_id=data.get('signal_id', ''),
                status=data.get('status', 'unknown'),
                ticket=data.get('ticket', 0),
                message=data.get('message', ''),
                timestamp=data.get('timestamp', ''),
                account=data.get('account', {})
            )
        except:
            return cls(signal_id='', status='error', message='Failed to parse result')

class ContainerFireAdapter:
    """
    Adapter for fire.txt based communication with MT5 containers
    Handles Docker container execution and file monitoring
    """
    
    def __init__(self):
        """Initialize the container fire adapter"""
        self.docker_client = docker.from_env()
        self.container_prefix = "mt5_user_"
        self.fire_path = "/wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt"
        self.result_path = "/wine/drive_c/MetaTrader5/Files/BITTEN/trade_result.txt"
        
        # Result monitoring
        self.result_queue = Queue()
        self.pending_signals = {}  # signal_id -> timestamp
        self.monitor_threads = {}  # container_name -> thread
        
        # Configuration
        self.result_timeout = 30  # seconds to wait for result
        self.check_interval = 0.5  # seconds between result checks
        
        logger.info("Container Fire Adapter initialized")
    
    def execute_trade(self,
                     user_id: str,
                     symbol: str, 
                     direction: str,
                     volume: float,
                     stop_loss: float = 0,
                     take_profit: float = 0,
                     comment: str = "") -> Dict[str, Any]:
        """
        Execute a trade by writing to container's fire.txt
        
        Args:
            user_id: User's telegram ID (used for container name)
            symbol: Trading symbol (e.g., "EURUSD")
            direction: "buy" or "sell"
            volume: Lot size
            stop_loss: Stop loss price (0 for none)
            take_profit: Take profit price (0 for none)
            comment: Trade comment
            
        Returns:
            Dictionary with trade result
        """
        # Generate unique signal ID
        signal_id = f"S{int(time.time() * 1000)}"
        
        # Get container name
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            # Get container
            container = self.docker_client.containers.get(container_name)
            
            # Check if container is running
            if container.status != 'running':
                return {
                    'success': False,
                    'signal_id': signal_id,
                    'message': 'Container not running',
                    'error_code': 'CONTAINER_STOPPED'
                }
            
            # Create trade signal
            signal = TradeSignal(
                signal_id=signal_id,
                symbol=symbol,
                type=direction.lower(),
                lot=volume,
                sl=stop_loss,
                tp=take_profit,
                comment=comment
            )
            
            # Write signal to fire.txt
            fire_json = signal.to_fire_json()
            
            # Execute command to write fire.txt
            exec_result = container.exec_run(
                ['bash', '-c', f'echo \'{fire_json}\' > {self.fire_path}'],
                demux=True
            )
            
            if exec_result.exit_code != 0:
                error_msg = exec_result.output[1].decode() if exec_result.output[1] else "Unknown error"
                return {
                    'success': False,
                    'signal_id': signal_id,
                    'message': f'Failed to write signal: {error_msg}',
                    'error_code': 'WRITE_ERROR'
                }
            
            logger.info(f"Signal {signal_id} written to container {container_name}")
            
            # Start monitoring for result
            if container_name not in self.monitor_threads or not self.monitor_threads[container_name].is_alive():
                self._start_result_monitor(container_name)
            
            # Track pending signal
            self.pending_signals[signal_id] = time.time()
            
            # Wait for result
            return self._wait_for_result(signal_id, container_name)
            
        except docker.errors.NotFound:
            return {
                'success': False,
                'signal_id': signal_id,
                'message': f'Container {container_name} not found',
                'error_code': 'CONTAINER_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'signal_id': signal_id,
                'message': str(e),
                'error_code': 'EXECUTION_ERROR'
            }
    
    def close_positions(self, user_id: str, symbol: str) -> Dict[str, Any]:
        """
        Close all positions for a symbol
        
        Args:
            user_id: User's telegram ID
            symbol: Symbol to close positions for
            
        Returns:
            Dictionary with close result
        """
        signal_id = f"C{int(time.time() * 1000)}"
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Create close signal
            signal = TradeSignal(
                signal_id=signal_id,
                symbol=symbol,
                type="close",
                lot=0,
                action="close"
            )
            
            # Write to fire.txt
            fire_json = signal.to_fire_json()
            exec_result = container.exec_run(
                ['bash', '-c', f'echo \'{fire_json}\' > {self.fire_path}'],
                demux=True
            )
            
            if exec_result.exit_code != 0:
                return {
                    'success': False,
                    'signal_id': signal_id,
                    'message': 'Failed to write close signal',
                    'error_code': 'WRITE_ERROR'
                }
            
            # Wait for result
            return self._wait_for_result(signal_id, container_name)
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return {
                'success': False,
                'signal_id': signal_id,
                'message': str(e),
                'error_code': 'CLOSE_ERROR'
            }
    
    def _start_result_monitor(self, container_name: str):
        """Start monitoring thread for container results"""
        thread = threading.Thread(
            target=self._monitor_container_results,
            args=(container_name,),
            daemon=True
        )
        thread.start()
        self.monitor_threads[container_name] = thread
        logger.info(f"Started result monitor for {container_name}")
    
    def _monitor_container_results(self, container_name: str):
        """Monitor container for trade results"""
        try:
            container = self.docker_client.containers.get(container_name)
            last_result = ""
            
            while container.status == 'running':
                try:
                    # Read trade_result.txt
                    exec_result = container.exec_run(
                        ['bash', '-c', f'cat {self.result_path} 2>/dev/null || echo ""'],
                        demux=True
                    )
                    
                    if exec_result.exit_code == 0 and exec_result.output[0]:
                        content = exec_result.output[0].decode().strip()
                        
                        # Check if we have new result
                        if content and content != last_result:
                            # Parse and queue result
                            try:
                                result = TradeResult.from_json(content)
                                if result.signal_id in self.pending_signals:
                                    self.result_queue.put((result.signal_id, result))
                                    logger.info(f"Got result for signal {result.signal_id}: {result.status}")
                                    
                                    # Clear the result file
                                    container.exec_run(
                                        ['bash', '-c', f'> {self.result_path}']
                                    )
                                    
                                last_result = content
                            except Exception as e:
                                logger.error(f"Failed to parse result: {e}")
                    
                except Exception as e:
                    logger.error(f"Error monitoring {container_name}: {e}")
                
                time.sleep(self.check_interval)
                
                # Refresh container status
                try:
                    container.reload()
                except:
                    break
                    
        except Exception as e:
            logger.error(f"Monitor thread error for {container_name}: {e}")
    
    def _wait_for_result(self, signal_id: str, container_name: str) -> Dict[str, Any]:
        """Wait for trade result with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < self.result_timeout:
            try:
                # Check queue for our result
                queued_signal_id, result = self.result_queue.get(timeout=0.1)
                
                if queued_signal_id == signal_id:
                    # Remove from pending
                    self.pending_signals.pop(signal_id, None)
                    
                    return {
                        'success': result.status == 'success',
                        'signal_id': signal_id,
                        'ticket': result.ticket,
                        'message': result.message,
                        'timestamp': result.timestamp,
                        'account': result.account or {},
                        'container': container_name
                    }
                else:
                    # Not our result, put it back
                    self.result_queue.put((queued_signal_id, result))
                    
            except Empty:
                continue
        
        # Timeout
        self.pending_signals.pop(signal_id, None)
        return {
            'success': False,
            'signal_id': signal_id,
            'message': 'Trade execution timeout - no response from EA',
            'error_code': 'TIMEOUT',
            'container': container_name
        }
    
    def get_container_status(self, user_id: str) -> Dict[str, Any]:
        """Get status of user's MT5 container"""
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Check if EA is active by testing fire.txt access
            exec_result = container.exec_run(
                ['bash', '-c', f'test -w {self.fire_path} && echo "OK" || echo "ERROR"'],
                demux=True
            )
            
            ea_active = exec_result.exit_code == 0 and exec_result.output[0].decode().strip() == "OK"
            
            return {
                'exists': True,
                'running': container.status == 'running',
                'ea_active': ea_active,
                'container_id': container.short_id,
                'created': container.attrs['Created'],
                'status': container.status
            }
            
        except docker.errors.NotFound:
            return {
                'exists': False,
                'running': False,
                'ea_active': False,
                'container_id': None,
                'status': 'not_found'
            }
        except Exception as e:
            logger.error(f"Error checking container status: {e}")
            return {
                'exists': False,
                'running': False,
                'ea_active': False,
                'error': str(e),
                'status': 'error'
            }
    
    def validate_symbols(self, user_id: str) -> Dict[str, bool]:
        """Validate which symbols are available in user's MT5"""
        container_name = f"{self.container_prefix}{user_id}"
        valid_symbols = {}
        
        # 15 standard symbols (no XAUUSD)
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                  "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                  "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"]
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            for symbol in symbols:
                # Test if symbol exists by trying to get tick data
                test_signal = {
                    "action": "validate",
                    "symbol": symbol
                }
                
                # This is a placeholder - actual validation would require EA support
                valid_symbols[symbol] = True
                
        except:
            # If container not found, return all as invalid
            for symbol in symbols:
                valid_symbols[symbol] = False
                
        return valid_symbols
    
    def cleanup_old_signals(self):
        """Clean up old pending signals"""
        current_time = time.time()
        expired = []
        
        for signal_id, timestamp in self.pending_signals.items():
            if current_time - timestamp > self.result_timeout:
                expired.append(signal_id)
        
        for signal_id in expired:
            self.pending_signals.pop(signal_id, None)
            logger.info(f"Cleaned up expired signal: {signal_id}")


# Backward compatibility wrapper
class MT5BridgeAdapter(ContainerFireAdapter):
    """Compatibility wrapper for existing code"""
    
    def execute_trade(self, 
                     symbol: str,
                     direction: str, 
                     volume: float,
                     stop_loss: float = 0,
                     take_profit: float = 0,
                     comment: str = "",
                     user_id: str = None) -> Dict[str, Any]:
        """
        Execute trade with backward compatibility
        Note: user_id is required for container-based execution
        """
        if not user_id:
            return {
                'success': False,
                'message': 'user_id required for container execution',
                'error_code': 'MISSING_USER_ID'
            }
        
        return super().execute_trade(
            user_id=user_id,
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=comment
        )


# Test the adapter
if __name__ == "__main__":
    print("🧪 Testing Container Fire Adapter...")
    
    adapter = ContainerFireAdapter()
    
    # Test with a sample user ID
    test_user_id = "123456789"
    
    # Check container status
    print(f"\n📊 Checking container status for user {test_user_id}...")
    status = adapter.get_container_status(test_user_id)
    print(f"Container status: {json.dumps(status, indent=2)}")
    
    if status['exists'] and status['running']:
        # Test trade execution
        print(f"\n🔥 Testing trade execution...")
        result = adapter.execute_trade(
            user_id=test_user_id,
            symbol="EURUSD",
            direction="buy",
            volume=0.01,
            stop_loss=0,
            take_profit=0,
            comment="Test trade from Container Fire Adapter"
        )
        print(f"Trade result: {json.dumps(result, indent=2)}")
        
        # Test symbol validation
        print(f"\n✅ Testing symbol validation...")
        symbols = adapter.validate_symbols(test_user_id)
        print(f"Valid symbols: {json.dumps(symbols, indent=2)}")
    else:
        print("⚠️ Container not available for testing")
        print("Please ensure mt5_user_123456789 container is running")