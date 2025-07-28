"""
Fire Router TOC - Terminal-Aware Signal Routing System

This module handles routing trade signals from Flask to the correct MT5 terminal
based on user-to-terminal assignments. It supports both AWS HTTP endpoints and
local file-based communication with retry logic and failover capabilities.
"""

import json
import time
import requests
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import threading
from contextlib import contextmanager
from enum import Enum

# Import terminal assignment system
from terminal_assignment import TerminalAssignment, TerminalType, TerminalStatus

# Configure logging
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Types of trading signals"""
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    MODIFY_POSITION = "modify_position"
    CLOSE_ALL = "close_all"

class DeliveryMethod(Enum):
    """Signal delivery methods"""
    HTTP_POST = "http_post"
    FILE_WRITE = "file_write"
    HYBRID = "hybrid"  # Try HTTP first, fallback to file

@dataclass
class TradeSignal:
    """Trade signal data structure"""
    user_id: str
    signal_type: SignalType
    symbol: str
    direction: str  # buy/sell
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = ""
    magic_number: Optional[int] = None
    ticket: Optional[int] = None  # For close/modify operations
    metadata: Optional[Dict] = None

@dataclass
class SignalResponse:
    """Response from signal routing"""
    success: bool
    message: str
    terminal_id: Optional[int] = None
    terminal_name: Optional[str] = None
    delivery_method: Optional[str] = None
    response_data: Optional[Dict] = None
    error_code: Optional[str] = None
    retry_count: int = 0

class FireRouterTOC:
    """Terminal-aware signal router with retry and failover"""
    
    def __init__(self, 
                 terminal_db_path: str = "terminal_assignments.db",
                 config_path: Optional[str] = None):
        """
        Initialize the Fire Router TOC
        
        Args:
            terminal_db_path: Path to terminal assignments database
            config_path: Optional path to configuration file
        """
        self.terminal_manager = TerminalAssignment(terminal_db_path)
        self.config = self._load_config(config_path)
        
        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.timeout = self.config.get('timeout', 10)
        
        # Delivery preferences
        self.default_delivery = DeliveryMethod.HYBRID
        self.file_base_path = Path(self.config.get('file_base_path', '/mt5/signals'))
        
        # Performance tracking
        self.stats = {
            'total_signals': 0,
            'successful_signals': 0,
            'failed_signals': 0,
            'retries': 0,
            'http_failures': 0,
            'file_failures': 0
        }
        
        # Thread safety
        self._stats_lock = threading.Lock()
        
        # Signal history
        self.signal_history = []
        self.max_history = 1000
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'max_retries': 3,
            'retry_delay': 1.0,
            'timeout': 10,
            'file_base_path': '/mt5/signals',
            'http_headers': {
                'Content-Type': 'application/json',
                'X-Signal-Source': 'HydraX-TOC'
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def route_signal(self, signal: TradeSignal, 
                    terminal_type: TerminalType = TerminalType.PRESS_PASS,
                    preferred_terminal_id: Optional[int] = None,
                    delivery_method: Optional[DeliveryMethod] = None) -> SignalResponse:
        """
        Route a trade signal to the appropriate terminal
        
        Args:
            signal: Trade signal to route
            terminal_type: Type of terminal required
            preferred_terminal_id: Optional specific terminal preference
            delivery_method: Override default delivery method
            
        Returns:
            SignalResponse with routing results
        """
        try:
            # Update statistics
            with self._stats_lock:
                self.stats['total_signals'] += 1
            
            # Get or assign terminal for user
            assignment = self._get_or_assign_terminal(
                signal.user_id, terminal_type, preferred_terminal_id
            )
            
            if not assignment:
                return SignalResponse(
                    success=False,
                    message=f"No available {terminal_type.value} terminal for user {signal.user_id}",
                    error_code="NO_TERMINAL_AVAILABLE"
                )
            
            # Determine delivery method
            method = delivery_method or self.default_delivery
            
            # Route signal with retry logic
            response = self._route_with_retry(signal, assignment, method)
            
            # Log to history
            self._log_signal(signal, assignment, response)
            
            # Update statistics
            with self._stats_lock:
                if response.success:
                    self.stats['successful_signals'] += 1
                else:
                    self.stats['failed_signals'] += 1
            
            return response
            
        except Exception as e:
            logger.error(f"Signal routing error: {e}")
            return SignalResponse(
                success=False,
                message=f"Routing error: {str(e)}",
                error_code="ROUTING_ERROR"
            )
    
    def _get_or_assign_terminal(self, user_id: str, 
                               terminal_type: TerminalType,
                               preferred_terminal_id: Optional[int] = None) -> Optional[Dict]:
        """Get existing assignment or create new one"""
        # Check existing assignments
        assignments = self.terminal_manager.get_user_assignments(user_id, active_only=True)
        
        for assignment in assignments:
            if assignment['terminal_type'] == terminal_type.value:
                return assignment
        
        # No existing assignment, create new one
        assignment = self.terminal_manager.assign_terminal(
            user_id=user_id,
            terminal_type=terminal_type,
            preferred_terminal_id=preferred_terminal_id,
            metadata={
                'source': 'fire_router_toc',
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return assignment
    
    def _route_with_retry(self, signal: TradeSignal, 
                         assignment: Dict,
                         method: DeliveryMethod) -> SignalResponse:
        """Route signal with retry logic"""
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                if method == DeliveryMethod.HTTP_POST:
                    return self._send_http(signal, assignment, retry_count)
                elif method == DeliveryMethod.FILE_WRITE:
                    return self._write_file(signal, assignment, retry_count)
                elif method == DeliveryMethod.HYBRID:
                    # Try HTTP first
                    response = self._send_http(signal, assignment, retry_count)
                    if response.success:
                        return response
                    
                    # Fallback to file
                    logger.warning(f"HTTP failed, falling back to file write: {response.message}")
                    return self._write_file(signal, assignment, retry_count)
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Delivery attempt {retry_count + 1} failed: {e}")
                
                retry_count += 1
                if retry_count <= self.max_retries:
                    time.sleep(self.retry_delay * retry_count)  # Exponential backoff
                
                with self._stats_lock:
                    self.stats['retries'] += 1
        
        return SignalResponse(
            success=False,
            message=f"All delivery attempts failed. Last error: {last_error}",
            terminal_id=assignment['terminal_id'],
            terminal_name=assignment['terminal_name'],
            error_code="MAX_RETRIES_EXCEEDED",
            retry_count=retry_count
        )
    
    def _send_http(self, signal: TradeSignal, assignment: Dict, retry_count: int) -> SignalResponse:
        """Send signal via HTTP POST to bridge"""
        try:
            # Build URL
            base_url = f"http://{assignment['ip_address']}:{assignment['port']}"
            endpoint = "/fire" if signal.signal_type == SignalType.OPEN_POSITION else "/execute"
            url = f"{base_url}{endpoint}"
            
            # Prepare payload
            payload = {
                'user_id': signal.user_id,
                'terminal_id': assignment['terminal_id'],
                'terminal_name': assignment['terminal_name'],
                'signal': asdict(signal),
                'timestamp': datetime.now().isoformat(),
                'retry_count': retry_count
            }
            
            # Send request
            response = requests.post(
                url,
                json=payload,
                headers=self.config.get('http_headers', {}),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return SignalResponse(
                    success=True,
                    message="Signal delivered successfully via HTTP",
                    terminal_id=assignment['terminal_id'],
                    terminal_name=assignment['terminal_name'],
                    delivery_method="HTTP_POST",
                    response_data=response.json(),
                    retry_count=retry_count
                )
            else:
                with self._stats_lock:
                    self.stats['http_failures'] += 1
                    
                return SignalResponse(
                    success=False,
                    message=f"HTTP delivery failed: {response.status_code}",
                    terminal_id=assignment['terminal_id'],
                    terminal_name=assignment['terminal_name'],
                    error_code=f"HTTP_{response.status_code}",
                    retry_count=retry_count
                )
                
        except requests.exceptions.RequestException as e:
            with self._stats_lock:
                self.stats['http_failures'] += 1
                
            return SignalResponse(
                success=False,
                message=f"HTTP request failed: {str(e)}",
                terminal_id=assignment['terminal_id'],
                terminal_name=assignment['terminal_name'],
                error_code="HTTP_REQUEST_ERROR",
                retry_count=retry_count
            )
    
    def _write_file(self, signal: TradeSignal, assignment: Dict, retry_count: int) -> SignalResponse:
        """Write signal to file for bridge pickup"""
        try:
            # Create directory structure
            signal_dir = self.file_base_path / assignment['folder_path'] / 'signals'
            signal_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f"fire_{signal.user_id}_{timestamp}.json"
            filepath = signal_dir / filename
            
            # Prepare signal data
            signal_data = {
                'user_id': signal.user_id,
                'terminal_id': assignment['terminal_id'],
                'terminal_name': assignment['terminal_name'],
                'signal': asdict(signal),
                'timestamp': datetime.now().isoformat(),
                'retry_count': retry_count,
                'file_version': '1.0'
            }
            
            # Write atomically
            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(signal_data, f, indent=2)
            
            # Atomic rename
            temp_path.rename(filepath)
            
            # Also write to common fire.json for compatibility
            fire_json_path = signal_dir / 'fire.json'
            with open(fire_json_path, 'w') as f:
                json.dump(signal_data, f, indent=2)
            
            return SignalResponse(
                success=True,
                message=f"Signal written to file: {filename}",
                terminal_id=assignment['terminal_id'],
                terminal_name=assignment['terminal_name'],
                delivery_method="FILE_WRITE",
                response_data={'filepath': str(filepath)},
                retry_count=retry_count
            )
            
        except Exception as e:
            with self._stats_lock:
                self.stats['file_failures'] += 1
                
            return SignalResponse(
                success=False,
                message=f"File write failed: {str(e)}",
                terminal_id=assignment['terminal_id'],
                terminal_name=assignment['terminal_name'],
                error_code="FILE_WRITE_ERROR",
                retry_count=retry_count
            )
    
    def _log_signal(self, signal: TradeSignal, assignment: Dict, response: SignalResponse):
        """Log signal to history"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': signal.user_id,
            'signal_type': signal.signal_type.value,
            'symbol': signal.symbol,
            'terminal_id': assignment['terminal_id'],
            'terminal_name': assignment['terminal_name'],
            'success': response.success,
            'delivery_method': response.delivery_method,
            'retry_count': response.retry_count,
            'error_code': response.error_code
        }
        
        self.signal_history.append(log_entry)
        
        # Maintain history size limit
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
    
    def get_user_routing_info(self, user_id: str) -> Dict[str, Any]:
        """Get current routing information for a user"""
        assignments = self.terminal_manager.get_user_assignments(user_id, active_only=True)
        
        routing_info = {
            'user_id': user_id,
            'active_assignments': len(assignments),
            'terminals': []
        }
        
        for assignment in assignments:
            terminal_info = {
                'terminal_id': assignment['terminal_id'],
                'terminal_name': assignment['terminal_name'],
                'terminal_type': assignment['terminal_type'],
                'bridge_endpoint': f"http://{assignment['ip_address']}:{assignment['port']}",
                'folder_path': assignment['folder_path'],
                'assigned_at': assignment['assigned_at']
            }
            routing_info['terminals'].append(terminal_info)
        
        # Add recent signal history for this user
        user_history = [
            entry for entry in self.signal_history 
            if entry['user_id'] == user_id
        ][-10:]  # Last 10 signals
        
        routing_info['recent_signals'] = user_history
        
        return routing_info
    
    def get_terminal_health(self, terminal_id: int) -> Dict[str, Any]:
        """Check health status of a specific terminal"""
        terminal_info = self.terminal_manager.get_terminal_info(terminal_id)
        
        if not terminal_info:
            return {
                'terminal_id': terminal_id,
                'status': 'NOT_FOUND',
                'healthy': False
            }
        
        health = {
            'terminal_id': terminal_id,
            'terminal_name': terminal_info['terminal_name'],
            'status': terminal_info['status'],
            'active_users': terminal_info['active_users'],
            'max_users': terminal_info['max_users'],
            'utilization': f"{(terminal_info['active_users'] / terminal_info['max_users'] * 100):.1f}%"
        }
        
        # Try to ping the HTTP endpoint
        if terminal_info['status'] == TerminalStatus.AVAILABLE.value:
            try:
                url = f"http://{terminal_info['ip_address']}:{terminal_info['port']}/health"
                response = requests.get(url, timeout=5)
                health['bridge_responsive'] = response.status_code == 200
                health['bridge_latency'] = response.elapsed.total_seconds() * 1000  # ms
            except:
                health['bridge_responsive'] = False
                health['bridge_latency'] = None
        
        health['healthy'] = (
            health['status'] == TerminalStatus.AVAILABLE.value and
            health.get('bridge_responsive', False)
        )
        
        return health
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get overall routing statistics"""
        with self._stats_lock:
            stats = self.stats.copy()
        
        # Calculate success rate
        if stats['total_signals'] > 0:
            stats['success_rate'] = f"{(stats['successful_signals'] / stats['total_signals'] * 100):.1f}%"
        else:
            stats['success_rate'] = "N/A"
        
        # Get terminal statistics
        terminal_stats = self.terminal_manager.get_statistics()
        stats['terminal_stats'] = terminal_stats
        
        # Add delivery method breakdown
        delivery_breakdown = {
            'http_success': stats['successful_signals'] - stats['file_failures'],
            'file_success': stats['successful_signals'] - stats['http_failures'],
            'http_failure_rate': f"{(stats['http_failures'] / max(stats['total_signals'], 1) * 100):.1f}%",
            'file_failure_rate': f"{(stats['file_failures'] / max(stats['total_signals'], 1) * 100):.1f}%"
        }
        stats['delivery_breakdown'] = delivery_breakdown
        
        return stats
    
    def failover_terminal(self, terminal_id: int, reason: str = "Manual failover") -> Dict[str, Any]:
        """
        Perform failover for a terminal by reassigning all users
        
        Args:
            terminal_id: Terminal to failover
            reason: Reason for failover
            
        Returns:
            Failover results
        """
        try:
            # Mark terminal as in error state
            self.terminal_manager.update_terminal_status(terminal_id, TerminalStatus.ERROR)
            
            # Get all active assignments for this terminal
            assignments = self.terminal_manager.get_terminal_assignments(terminal_id, active_only=True)
            
            results = {
                'terminal_id': terminal_id,
                'affected_users': len(assignments),
                'reassignments': [],
                'failures': []
            }
            
            for assignment in assignments:
                user_id = assignment['user_id']
                terminal_type = TerminalType(assignment['terminal_type'])
                
                # Release current assignment
                self.terminal_manager.release_terminal(user_id, terminal_id)
                
                # Try to reassign to another terminal
                new_assignment = self.terminal_manager.assign_terminal(
                    user_id=user_id,
                    terminal_type=terminal_type,
                    metadata={
                        'failover_from': terminal_id,
                        'failover_reason': reason,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                if new_assignment:
                    results['reassignments'].append({
                        'user_id': user_id,
                        'new_terminal_id': new_assignment['terminal_id'],
                        'new_terminal_name': new_assignment['terminal_name']
                    })
                else:
                    results['failures'].append({
                        'user_id': user_id,
                        'reason': 'No available terminals'
                    })
            
            results['success'] = len(results['failures']) == 0
            results['message'] = f"Failover completed. {len(results['reassignments'])} users reassigned, {len(results['failures'])} failures"
            
            return results
            
        except Exception as e:
            logger.error(f"Failover error: {e}")
            return {
                'success': False,
                'message': f"Failover failed: {str(e)}",
                'terminal_id': terminal_id
            }

# Flask endpoint handler
def create_fire_endpoint(router: FireRouterTOC):
    """
    Create Flask endpoint handler for /fire route
    
    Args:
        router: FireRouterTOC instance
        
    Returns:
        Flask route handler function
    """
    def fire_endpoint():
        """Handle POST /fire requests"""
        from flask import request, jsonify
        
        try:
            # Parse request data
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['user_id', 'symbol', 'direction', 'volume']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'Missing required field: {field}'
                    }), 400
            
            # Create trade signal
            signal = TradeSignal(
                user_id=str(data['user_id']),
                signal_type=SignalType.OPEN_POSITION,
                symbol=data['symbol'],
                direction=data['direction'],
                volume=float(data['volume']),
                stop_loss=data.get('stop_loss'),
                take_profit=data.get('take_profit'),
                comment=data.get('comment', 'HydraX Signal'),
                magic_number=data.get('magic_number'),
                metadata=data.get('metadata', {})
            )
            
            # Determine terminal type from request or default
            terminal_type = TerminalType(data.get('terminal_type', 'press_pass'))
            
            # Route the signal
            response = router.route_signal(
                signal=signal,
                terminal_type=terminal_type,
                preferred_terminal_id=data.get('preferred_terminal_id')
            )
            
            # Return response
            return jsonify({
                'success': response.success,
                'message': response.message,
                'terminal_id': response.terminal_id,
                'terminal_name': response.terminal_name,
                'delivery_method': response.delivery_method,
                'response_data': response.response_data
            }), 200 if response.success else 500
            
        except Exception as e:
            logger.error(f"Fire endpoint error: {e}")
            return jsonify({
                'success': False,
                'message': f'Server error: {str(e)}'
            }), 500
    
    return fire_endpoint

# Example usage
if __name__ == "__main__":
    # Initialize router
    router = FireRouterTOC()
    
    # Example: Route a trade signal
    signal = TradeSignal(
        user_id="user123",
        signal_type=SignalType.OPEN_POSITION,
        symbol="GBPUSD",
        direction="buy",
        volume=0.1,
        stop_loss=1.2450,
        take_profit=1.2550,
        comment="Test signal"
    )
    
    # Route the signal
    response = router.route_signal(signal, TerminalType.PRESS_PASS)
    print(f"Routing result: {response.success} - {response.message}")
    
    # Check user routing info
    routing_info = router.get_user_routing_info("user123")
    print(f"User routing info: {json.dumps(routing_info, indent=2)}")
    
    # Get statistics
    stats = router.get_routing_statistics()
    print(f"Routing statistics: {json.dumps(stats, indent=2)}")