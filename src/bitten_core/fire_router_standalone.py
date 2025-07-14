# BITTEN Fire Router - Standalone Socket Bridge Implementation
# Real MT5 bridge execution with basic validation and robust error handling

import socket
import json
import time
import logging
import threading
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

class TradeDirection(Enum):
    """Trade direction enumeration"""
    BUY = "buy"
    SELL = "sell"

class ExecutionMode(Enum):
    """Execution mode - simulation or live"""
    SIMULATION = "simulation"
    LIVE = "live"

@dataclass
class TradeRequest:
    """Standardized trade request structure"""
    symbol: str
    direction: TradeDirection
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = ""
    tcs_score: float = 0
    user_id: str = ""
    mission_id: str = ""
    
    def to_bridge_payload(self) -> Dict[str, Any]:
        """Convert to bridge socket payload format"""
        return {
            "symbol": self.symbol,
            "type": self.direction.value,
            "lot": self.volume,
            "tp": self.take_profit or 0,
            "sl": self.stop_loss or 0,
            "comment": f"{self.comment} TCS:{self.tcs_score}%",
            "mission_id": self.mission_id,
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat()
        }

@dataclass
class TradeExecutionResult:
    """Trade execution result"""
    success: bool
    message: str = ""
    trade_id: Optional[str] = None
    execution_price: Optional[float] = None
    timestamp: str = ""
    tcs_score: float = 0
    ticket: Optional[int] = None
    account_info: Optional[Dict] = None
    error_code: Optional[str] = None
    execution_time_ms: Optional[int] = None

class BridgeConnectionManager:
    """Manages MT5 bridge socket connections with retry logic"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9000, 
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = 10.0
        self.send_timeout = 5.0
        
        # Connection health tracking
        self.last_successful_connection = None
        self.connection_failures = 0
        self.total_connections = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
    @contextmanager
    def get_connection(self):
        """Context manager for bridge socket connections"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            
            # Track connection attempt
            with self._lock:
                self.total_connections += 1
            
            sock.connect((self.host, self.port))
            
            # Track successful connection
            with self._lock:
                self.last_successful_connection = datetime.now()
                self.connection_failures = 0
            
            yield sock
            
        except Exception as e:
            with self._lock:
                self.connection_failures += 1
            logger.error(f"Bridge connection failed: {e}")
            raise
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def send_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send payload to bridge with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                with self.get_connection() as sock:
                    # Send payload
                    message = json.dumps(payload).encode('utf-8')
                    sock.settimeout(self.send_timeout)
                    sock.send(message)
                    
                    # Wait for response (optional)
                    try:
                        sock.settimeout(2.0)  # Short timeout for response
                        response = sock.recv(1024)
                        if response:
                            return json.loads(response.decode('utf-8'))
                    except socket.timeout:
                        # No response expected for some bridge types
                        pass
                    except Exception as e:
                        logger.warning(f"Response read failed: {e}")
                    
                    return {"success": True, "message": "sent_to_bridge"}
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Bridge send attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        return {
            "success": False, 
            "message": f"Bridge connection failed after {self.max_retries + 1} attempts",
            "error": last_error
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get connection health status"""
        with self._lock:
            return {
                "total_connections": self.total_connections,
                "connection_failures": self.connection_failures,
                "last_successful_connection": self.last_successful_connection.isoformat() if self.last_successful_connection else None,
                "success_rate": (self.total_connections - self.connection_failures) / max(self.total_connections, 1) * 100,
                "bridge_endpoint": f"{self.host}:{self.port}"
            }

class SimpleValidator:
    """Simple validation for basic trade safety"""
    
    def validate_trade(self, request: TradeRequest) -> Tuple[bool, str]:
        """Basic trade validation"""
        
        # Check required fields
        if not request.symbol or len(request.symbol) < 6:
            return False, "Invalid symbol format"
        
        if request.volume <= 0 or request.volume > 10:
            return False, "Invalid volume (must be > 0 and <= 10)"
        
        # Check stop loss and take profit logic
        if request.stop_loss and request.take_profit:
            if request.direction == TradeDirection.BUY:
                if request.stop_loss >= request.take_profit:
                    return False, "Stop loss must be below take profit for BUY orders"
            else:  # SELL
                if request.stop_loss <= request.take_profit:
                    return False, "Stop loss must be above take profit for SELL orders"
        
        # Check TCS score
        if request.tcs_score < 50:
            return False, f"TCS score too low: {request.tcs_score}% (minimum 50%)"
        
        return True, "Validation passed"

class FireRouter:
    """Enhanced Fire Router with socket bridge integration"""
    
    def __init__(self, bridge_host: str = "127.0.0.1", bridge_port: int = 9000,
                 execution_mode: ExecutionMode = ExecutionMode.LIVE):
        
        # Bridge connection manager
        self.bridge_manager = BridgeConnectionManager(bridge_host, bridge_port)
        
        # Basic validator
        self.validator = SimpleValidator()
        
        # Execution mode
        self.execution_mode = execution_mode
        
        # Performance tracking
        self.stats = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "validation_failures": 0,
            "bridge_failures": 0,
            "average_execution_time": 0.0
        }
        
        # Thread safety
        self._stats_lock = threading.Lock()
        
        # Trade history
        self.trade_history = []
        self.max_history = 1000
        
        logger.info(f"Fire Router initialized - Mode: {execution_mode.value}, Bridge: {bridge_host}:{bridge_port}")
    
    def execute_trade(self, mission: Dict[str, Any]) -> str:
        """Legacy interface for backward compatibility"""
        # Convert legacy mission format to TradeRequest
        request = self._convert_legacy_mission(mission)
        
        # Execute with basic validation
        result = self.execute_trade_request(request)
        
        # Return legacy format
        return "sent_to_bridge" if result.success else "failed"
    
    def execute_trade_request(self, request: TradeRequest) -> TradeExecutionResult:
        """Execute trade request with validation and bridge communication"""
        
        execution_start = time.time()
        
        try:
            # Update statistics
            with self._stats_lock:
                self.stats["total_trades"] += 1
            
            # 1. VALIDATION PHASE
            is_valid, validation_message = self.validator.validate_trade(request)
            
            if not is_valid:
                with self._stats_lock:
                    self.stats["validation_failures"] += 1
                
                result = TradeExecutionResult(
                    success=False,
                    message=f"❌ Validation failed: {validation_message}",
                    error_code="VALIDATION_FAILED",
                    execution_time_ms=int((time.time() - execution_start) * 1000)
                )
                
                self._log_trade_result(request, result)
                return result
            
            # 2. EXECUTION PHASE
            if self.execution_mode == ExecutionMode.SIMULATION:
                execution_result = self._simulate_execution(request)
            else:
                execution_result = self._execute_live(request)
            
            # 3. FINALIZE RESULT
            execution_time_ms = int((time.time() - execution_start) * 1000)
            
            if execution_result["success"]:
                with self._stats_lock:
                    self.stats["successful_trades"] += 1
                    # Update average execution time
                    total_time = self.stats["average_execution_time"] * (self.stats["successful_trades"] - 1)
                    self.stats["average_execution_time"] = (total_time + execution_time_ms) / self.stats["successful_trades"]
                
                result = TradeExecutionResult(
                    success=True,
                    message=f"✅ Trade executed successfully",
                    trade_id=execution_result.get("trade_id", request.mission_id),
                    execution_price=execution_result.get("price"),
                    timestamp=datetime.now().isoformat(),
                    tcs_score=request.tcs_score,
                    ticket=execution_result.get("ticket"),
                    account_info=execution_result.get("account_info"),
                    execution_time_ms=execution_time_ms
                )
            else:
                with self._stats_lock:
                    self.stats["failed_trades"] += 1
                    if "bridge" in execution_result.get("error", "").lower():
                        self.stats["bridge_failures"] += 1
                
                result = TradeExecutionResult(
                    success=False,
                    message=f"❌ Execution failed: {execution_result.get('message', 'Unknown error')}",
                    error_code=execution_result.get("error_code", "EXECUTION_FAILED"),
                    execution_time_ms=execution_time_ms
                )
            
            self._log_trade_result(request, result)
            return result
            
        except Exception as e:
            with self._stats_lock:
                self.stats["failed_trades"] += 1
            
            logger.error(f"Trade execution exception: {e}")
            
            result = TradeExecutionResult(
                success=False,
                message=f"❌ System error: {str(e)}",
                error_code="SYSTEM_ERROR",
                execution_time_ms=int((time.time() - execution_start) * 1000)
            )
            
            self._log_trade_result(request, result)
            return result
    
    def _execute_live(self, request: TradeRequest) -> Dict[str, Any]:
        """Execute trade through live MT5 bridge"""
        
        try:
            # Prepare bridge payload
            payload = request.to_bridge_payload()
            
            # Send to bridge with retry logic
            result = self.bridge_manager.send_with_retry(payload)
            
            if result["success"]:
                logger.info(f"Trade sent to bridge successfully: {request.symbol} {request.direction.value} {request.volume}")
                return {
                    "success": True,
                    "message": "Trade sent to MT5 bridge",
                    "trade_id": request.mission_id,
                    "bridge_response": result
                }
            else:
                logger.error(f"Bridge communication failed: {result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": result.get("message", "Bridge communication failed"),
                    "error_code": "BRIDGE_ERROR",
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Live execution error: {e}")
            return {
                "success": False,
                "message": f"Live execution failed: {str(e)}",
                "error_code": "LIVE_EXECUTION_ERROR",
                "error": str(e)
            }
    
    def _simulate_execution(self, request: TradeRequest) -> Dict[str, Any]:
        """Simulate trade execution for development/testing"""
        
        # Simulate network delay
        time.sleep(0.1 + (hash(request.symbol) % 100) / 1000)
        
        # Simulate occasional failures (5% rate)
        if hash(request.mission_id) % 100 < 5:
            return {
                "success": False,
                "message": "Simulated network timeout",
                "error_code": "SIMULATION_TIMEOUT"
            }
        
        # Simulate successful execution
        simulated_price = 1.0 + (hash(request.symbol) % 10000) / 10000
        
        return {
            "success": True,
            "message": "Simulated execution successful",
            "trade_id": request.mission_id,
            "price": simulated_price,
            "ticket": hash(request.mission_id) % 1000000,
            "account_info": {
                "balance": 10000,
                "equity": 10000,
                "margin": 100
            }
        }
    
    def _convert_legacy_mission(self, mission: Dict[str, Any]) -> TradeRequest:
        """Convert legacy mission format to TradeRequest"""
        
        direction = TradeDirection.BUY if mission.get("type", "buy").lower() == "buy" else TradeDirection.SELL
        
        return TradeRequest(
            symbol=mission.get("symbol", "EURUSD"),
            direction=direction,
            volume=mission.get("lot_size", mission.get("lot", 0.01)),
            stop_loss=mission.get("sl"),
            take_profit=mission.get("tp"),
            comment=mission.get("comment", ""),
            mission_id=mission.get("mission_id", f"mission_{int(time.time())}"),
            user_id=mission.get("user_id", "unknown"),
            tcs_score=mission.get("tcs", 75)  # Default TCS
        )
    
    def _log_trade_result(self, request: TradeRequest, result: TradeExecutionResult):
        """Log trade result to history"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": request.user_id,
            "mission_id": request.mission_id,
            "symbol": request.symbol,
            "direction": request.direction.value,
            "volume": request.volume,
            "tcs_score": request.tcs_score,
            "success": result.success,
            "message": result.message,
            "execution_time_ms": result.execution_time_ms,
            "error_code": result.error_code
        }
        
        self.trade_history.append(log_entry)
        
        # Maintain history size limit
        if len(self.trade_history) > self.max_history:
            self.trade_history = self.trade_history[-self.max_history:]
        
        # Log to file if needed
        if result.success:
            logger.info(f"Trade executed: {request.symbol} {request.direction.value} {request.volume} - {result.message}")
        else:
            logger.warning(f"Trade failed: {request.symbol} {request.direction.value} {request.volume} - {result.message}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        with self._stats_lock:
            stats = self.stats.copy()
        
        bridge_health = self.bridge_manager.get_health_status()
        
        return {
            "execution_mode": self.execution_mode.value,
            "bridge_health": bridge_health,
            "trade_statistics": stats,
            "recent_trades": self.trade_history[-10:],  # Last 10 trades
            "system_uptime": datetime.now().isoformat()
        }
    
    def set_execution_mode(self, mode: ExecutionMode):
        """Change execution mode (simulation/live)"""
        self.execution_mode = mode
        logger.info(f"Execution mode changed to: {mode.value}")
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        return self.trade_history[-limit:]

# Legacy function for backward compatibility
def execute_trade(mission: Dict[str, Any]) -> str:
    """Legacy execute_trade function for backward compatibility"""
    
    # Use environment variable to determine mode
    mode = ExecutionMode.SIMULATION if os.getenv("BITTEN_SIMULATION_MODE", "false").lower() == "true" else ExecutionMode.LIVE
    
    # Create router instance
    router = FireRouter(execution_mode=mode)
    
    # Execute trade
    return router.execute_trade(mission)

# Global router instance for module-level access
_global_router = None

def get_fire_router(execution_mode: ExecutionMode = ExecutionMode.LIVE) -> FireRouter:
    """Get or create global fire router instance"""
    global _global_router
    
    if _global_router is None:
        _global_router = FireRouter(execution_mode=execution_mode)
    
    return _global_router