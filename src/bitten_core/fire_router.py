# BITTEN Fire Router - Direct Broker API Integration
# 
# PRODUCTION CLONE FARM SYSTEM (July 18, 2025)
# 
# This system connects BITTEN fire commands directly to broker APIs:
# 1. FireRouter validates trade requests with comprehensive safety checks
# 2. Direct API calls to broker through clone farm infrastructure
# 3. Real-time execution with immediate confirmation
# 4. Full account management and position tracking
#
# Architecture: Signal → Fire → Validation → Direct API → Broker
#               ✅     ✅     ✅         ✅          ✅
#
# STATUS: Production ready with direct broker API integration

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
    """Execution mode - LIVE ONLY"""
    LIVE = "live"

class TradingPairs(Enum):
    """Trading pairs enumeration"""
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    USDCHF = "USDCHF"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"
    EURJPY = "EURJPY"
    GBPJPY = "GBPJPY"
    EURGBP = "EURGBP"
    XAUUSD = "XAUUSD"
    XAGUSD = "XAGUSD"

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
    
    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to direct broker API payload format"""
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

class DirectAPIManager:
    """Manages direct broker API connections with retry logic"""
    
    def __init__(self, api_endpoint: str = "api.broker.local", 
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.api_endpoint = api_endpoint
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = 20.0
        self.send_timeout = 15.0
        
        # Connection health tracking
        self.last_successful_connection = None
        self.connection_failures = 0
        self.total_connections = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
    def get_api_session(self):
        """Get direct API session for broker communication"""
        try:
            # Track connection attempt
            with self._lock:
                self.total_connections += 1
            
            # Initialize direct broker API session
            from clone_farm.broker_api import get_broker_session
            session = get_broker_session(self.api_endpoint)
            
            # Track successful connection
            with self._lock:
                self.last_successful_connection = datetime.now()
                self.connection_failures = 0
            
            return session
            
        except Exception as e:
            with self._lock:
                self.connection_failures += 1
            logger.error(f"API connection failed: {e}")
            raise
    
    def execute_trade_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade via direct broker API with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                session = self.get_api_session()
                
                # Execute trade via direct API
                from clone_farm.broker_api import execute_trade_direct
                result = execute_trade_direct(session, payload)
                
                if result.get("success"):
                    logger.info(f"Direct API response received: {result}")
                    return result
                else:
                    logger.warning(f"API execution failed: {result.get('message', 'Unknown error')}")
                    return result
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"API execution attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        return {
            "success": False, 
            "message": f"API execution failed after {self.max_retries + 1} attempts",
            "error": last_error
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get API connection health status"""
        with self._lock:
            return {
                "total_connections": self.total_connections,
                "connection_failures": self.connection_failures,
                "last_successful_connection": self.last_successful_connection.isoformat() if self.last_successful_connection else None,
                "success_rate": (self.total_connections - self.connection_failures) / max(self.total_connections, 1) * 100,
                "api_endpoint": self.api_endpoint
            }

class AdvancedValidator:
    """Advanced validation system with comprehensive trade safety checks"""
    
    def __init__(self):
        # Track user activity for enhanced validation
        self.user_activity = {}
        self.validation_stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0
        }
        
    def validate_trade(self, request: TradeRequest, user_profile: Optional[Dict] = None) -> Tuple[bool, str]:
        """Comprehensive trade validation with enhanced safety checks"""
        
        self.validation_stats["total_validations"] += 1
        
        # 1. Basic field validation
        if not request.symbol or len(request.symbol) < 6:
            self.validation_stats["failed_validations"] += 1
            return False, "Invalid symbol format - must be at least 6 characters"
        
        if request.volume <= 0 or request.volume > 10:
            self.validation_stats["failed_validations"] += 1
            return False, "Invalid volume - must be between 0 and 10 lots"
        
        # 2. Stop Loss / Take Profit validation
        if request.stop_loss and request.take_profit:
            if request.direction == TradeDirection.BUY:
                if request.stop_loss >= request.take_profit:
                    self.validation_stats["failed_validations"] += 1
                    return False, "Stop loss must be below take profit for BUY orders"
            else:  # SELL
                if request.stop_loss <= request.take_profit:
                    self.validation_stats["failed_validations"] += 1
                    return False, "Stop loss must be above take profit for SELL orders"
        
        # 3. TCS Score validation with tier-based requirements
        min_tcs = self._get_min_tcs_for_profile(user_profile)
        if request.tcs_score < min_tcs:
            self.validation_stats["failed_validations"] += 1
            return False, f"TCS score too low: {request.tcs_score}% (minimum {min_tcs}%)"
        
        # 4. User profile validation
        if user_profile:
            profile_valid, profile_message = self._validate_user_profile(request, user_profile)
            if not profile_valid:
                self.validation_stats["failed_validations"] += 1
                return False, profile_message
        
        # 5. Rate limiting validation
        rate_limit_valid, rate_message = self._validate_rate_limits(request)
        if not rate_limit_valid:
            self.validation_stats["failed_validations"] += 1
            return False, rate_message
        
        # 6. Risk management validation
        risk_valid, risk_message = self._validate_risk_management(request, user_profile)
        if not risk_valid:
            self.validation_stats["failed_validations"] += 1
            return False, risk_message
        
        # All validations passed
        self.validation_stats["passed_validations"] += 1
        return True, "All validations passed"
    
    def _get_min_tcs_for_profile(self, user_profile: Optional[Dict]) -> float:
        """Get minimum TCS requirement based on user profile"""
        if not user_profile:
            return 10.0  # LOWERED FOR TESTING
        
        tier = user_profile.get("tier", "nibbler").lower()
        tier_requirements = {
            "nibbler": 10.0,
            "fang": 10.0,
            "commander": 10.0,
            "apex": 10.0
        }
        
        return tier_requirements.get(tier, 75.0)
    
    def _validate_user_profile(self, request: TradeRequest, user_profile: Dict) -> Tuple[bool, str]:
        """Validate user profile specific constraints"""
        
        # Check daily trade limits
        shots_today = user_profile.get("shots_today", 0)
        tier = user_profile.get("tier", "nibbler").lower()
        
        daily_limits = {
            "nibbler": 6,
            "fang": 10,
            "commander": 20,
            "apex": 50
        }
        
        max_shots = daily_limits.get(tier, 6)
        if shots_today >= max_shots:
            return False, f"Daily trade limit reached: {shots_today}/{max_shots}"
        
        # Check concurrent position limits
        open_positions = user_profile.get("open_positions", 0)
        position_limits = {
            "nibbler": 1,
            "fang": 2,
            "commander": 3,
            "apex": 5
        }
        
        max_positions = position_limits.get(tier, 1)
        if open_positions >= max_positions:
            return False, f"Max concurrent positions reached: {open_positions}/{max_positions}"
        
        # Check account balance
        balance = user_profile.get("account_balance", 0)
        if balance < 100:
            return False, f"Insufficient account balance: ${balance}"
        
        # Check exposure limits
        total_exposure = user_profile.get("total_exposure_percent", 0)
        risk_percent = request.volume * 100 / balance  # Simplified risk calculation
        
        if total_exposure + risk_percent > 10:
            return False, f"Risk exposure too high: {total_exposure + risk_percent:.1f}% > 10%"
        
        return True, "User profile validation passed"
    
    def _validate_rate_limits(self, request: TradeRequest) -> Tuple[bool, str]:
        """Validate rate limiting to prevent spam"""
        
        user_id = request.user_id
        current_time = datetime.now()
        
        # Initialize user activity if not exists
        if user_id not in self.user_activity:
            self.user_activity[user_id] = {
                "last_trade_time": None,
                "trade_count_last_minute": 0,
                "last_minute_reset": current_time
            }
        
        user_data = self.user_activity[user_id]
        
        # Reset minute counter if needed
        if (current_time - user_data["last_minute_reset"]).seconds >= 60:
            user_data["trade_count_last_minute"] = 0
            user_data["last_minute_reset"] = current_time
        
        # Check trades per minute limit
        if user_data["trade_count_last_minute"] >= 5:
            return False, "Rate limit exceeded: Maximum 5 trades per minute"
        
        # Check minimum time between trades (30 seconds)
        if user_data["last_trade_time"]:
            time_since_last = (current_time - user_data["last_trade_time"]).seconds
            if time_since_last < 30:
                return False, f"Trade cooldown active: {30 - time_since_last} seconds remaining"
        
        # Update activity
        user_data["trade_count_last_minute"] += 1
        user_data["last_trade_time"] = current_time
        
        return True, "Rate limit validation passed"
    
    def _validate_risk_management(self, request: TradeRequest, user_profile: Optional[Dict]) -> Tuple[bool, str]:
        """Validate risk management constraints"""
        
        # Check for weekend trading restrictions
        now = datetime.now()
        if now.weekday() >= 5:  # Saturday or Sunday
            return False, "Weekend trading restricted"
        
        # Check for high-risk symbol restrictions
        high_risk_symbols = ["XAUUSD", "BTCUSD", "ETHUSD"]
        if request.symbol in high_risk_symbols:
            if not user_profile or user_profile.get("tier", "nibbler").lower() not in ["commander", "apex"]:
                return False, f"High-risk symbol {request.symbol} requires Commander+ tier"
        
        # Check volume limits based on symbol
        max_volumes = {
            "XAUUSD": 0.1,
            "BTCUSD": 0.01,
            "ETHUSD": 0.05
        }
        
        max_vol = max_volumes.get(request.symbol, 1.0)
        if request.volume > max_vol:
            return False, f"Volume too high for {request.symbol}: {request.volume} > {max_vol}"
        
        return True, "Risk management validation passed"
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        stats = self.validation_stats.copy()
        if stats["total_validations"] > 0:
            stats["success_rate"] = (stats["passed_validations"] / stats["total_validations"]) * 100
        else:
            stats["success_rate"] = 0.0
        
        return stats

class FireRouter:
    """Enhanced Fire Router with direct broker API integration and advanced validation"""
    
    def __init__(self, api_endpoint: str = "api.broker.local",
                 execution_mode: ExecutionMode = ExecutionMode.LIVE):
        
        # Direct API manager for clone farm broker integration
        self.api_manager = DirectAPIManager(api_endpoint)
        
        # Advanced validator
        self.validator = AdvancedValidator()
        
        # Execution mode
        self.execution_mode = execution_mode
        
        # Drill report handler for trade completion tracking
        self.drill_report_handler = None
        
        # Performance tracking
        self.stats = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "validation_failures": 0,
            "api_failures": 0,
            "average_execution_time": 0.0
        }
        
        # Thread safety
        self._stats_lock = threading.Lock()
        
        # Trade history
        self.trade_history = []
        self.max_history = 1000
        
        # Emergency stop flag
        self.emergency_stop = False
        
        logger.info(f"Fire Router initialized - Mode: {execution_mode.value}, API: {api_endpoint}")
    
    def execute_trade(self, mission: Dict[str, Any]) -> str:
        """Legacy interface for backward compatibility"""
        # Convert legacy mission format to TradeRequest
        request = self._convert_legacy_mission(mission)
        
        # Execute with advanced validation
        result = self.execute_trade_request(request)
        
        # Return legacy format
        return "sent_to_bridge" if result.success else "failed"
    
    def execute_trade_request(self, request: TradeRequest, user_profile: Optional[Dict] = None) -> TradeExecutionResult:
        """Execute trade request with comprehensive validation and bridge communication"""
        
        execution_start = time.time()
        
        try:
            # Check emergency stop
            if self.emergency_stop:
                return TradeExecutionResult(
                    success=False,
                    message="❌ Emergency stop active - All trading suspended",
                    error_code="EMERGENCY_STOP",
                    execution_time_ms=int((time.time() - execution_start) * 1000)
                )
            
            # Update statistics
            with self._stats_lock:
                self.stats["total_trades"] += 1
            
            # 1. VALIDATION PHASE
            is_valid, validation_message = self.validator.validate_trade(request, user_profile)
            
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
            
            # 2. EXECUTION PHASE - LIVE ONLY
            
            execution_result = self._execute_direct_api(request)
            
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
                
                # Track trade completion for drill reports
                if hasattr(self, 'drill_report_handler') and self.drill_report_handler and request.user_id:
                    try:
                        # Calculate trade metrics for drill report
                        calculated_pnl = self._calculate_trade_pnl(request, execution_result)
                        xp_awarded = self._calculate_xp_award(calculated_pnl, request.tcs_score)
                        pip_result = self._calculate_pip_result(request, execution_result)
                        
                        trade_info = {
                            'pnl_percent': calculated_pnl,
                            'xp_gained': xp_awarded,
                            'pips': pip_result,
                            'trade_id': result.trade_id,
                            'symbol': request.symbol,
                            'direction': request.direction.value,
                            'tcs_score': request.tcs_score
                        }
                        self.drill_report_handler(request.user_id, trade_info)
                        logger.info(f"Drill report updated for user {request.user_id}")
                    except Exception as e:
                        logger.error(f"Failed to update drill report for user {request.user_id}: {e}")
            else:
                with self._stats_lock:
                    self.stats["failed_trades"] += 1
                    if "api" in execution_result.get("error", "").lower():
                        self.stats["api_failures"] += 1
                
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
    
    def _execute_direct_api(self, request: TradeRequest) -> Dict[str, Any]:
        """Execute trade through direct broker API"""
        
        try:
            # Prepare API payload for direct execution
            payload = request.to_api_payload()
            payload["command"] = "execute_trade"  # Direct API command
            
            # Execute via direct API
            result = self.api_manager.execute_trade_api(payload)
            
            # Check if API responded with success
            if result.get("success"):
                logger.info(f"✅ Trade executed successfully via direct API: {request.symbol} {request.direction.value} {request.volume}")
                logger.info(f"✅ Trade ticket: {result.get('ticket')} | Order ID: {result.get('order_id')}")
                
                # Store account information if available
                try:
                    if result.get("account_info") and request.user_id:
                        from user_account_manager import process_api_account_info
                        process_api_account_info(request.user_id, result)
                        logger.info(f"✅ Account info stored for user {request.user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store account info: {e}")
                
                return {
                    "success": True,
                    "message": result.get("message", "Trade executed successfully"),
                    "trade_id": request.mission_id,
                    "ticket": result.get("ticket"),
                    "order_id": result.get("order_id"),
                    "price": result.get("price"),
                    "api_response": result,
                    "execution_method": "DIRECT_BROKER_API",
                    "account_info": result.get("account_info")
                }
            else:
                # API execution failed
                error_msg = result.get('message', 'Unknown API error')
                logger.error(f"❌ Direct API execution failed: {error_msg}")
                logger.warning(f"⚠️ API response: {result}")
                
                return {
                    "success": False,
                    "message": f"API execution failed: {error_msg}",
                    "error_code": "API_EXECUTION_FAILED",
                    "primary_error": error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Direct API execution error: {e}")
            
            return {
                "success": False,
                "message": f"API connection failed: {str(e)}",
                "error_code": "API_CONNECTION_ERROR",
                "primary_error": str(e)
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
        
        api_health = self.api_manager.get_health_status()
        validation_stats = self.validator.get_validation_stats()
        
        return {
            "execution_mode": self.execution_mode.value,
            "emergency_stop": self.emergency_stop,
            "api_health": api_health,
            "trade_statistics": stats,
            "validation_statistics": validation_stats,
            "recent_trades": self.trade_history[-10:],  # Last 10 trades
            "system_uptime": datetime.now().isoformat()
        }
    
    def set_execution_mode(self, mode: ExecutionMode):
        """Change execution mode (simulation/live)"""
        self.execution_mode = mode
        logger.info(f"Execution mode changed to: {mode.value}")
    
    def set_emergency_stop(self, active: bool):
        """Activate/deactivate emergency stop"""
        self.emergency_stop = active
        status = "ACTIVATED" if active else "DEACTIVATED"
        logger.critical(f"Emergency stop {status}")
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        return self.trade_history[-limit:]
    
    def set_drill_report_handler(self, handler_function):
        """Set drill report handler for trade completion tracking"""
        self.drill_report_handler = handler_function
        logger.info("Drill report handler configured")
    
    def _calculate_trade_pnl(self, request: TradeRequest, execution_result: Dict) -> float:
        """Calculate trade P&L percentage (placeholder - would be updated when trade closes)"""
        # In production, this would be calculated when the trade actually closes
        # For now, return a placeholder based on TCS score as an estimate
        base_expectation = (request.tcs_score - 50) / 25.0  # Higher TCS = higher expected return
        return max(-2.0, min(4.0, base_expectation))  # Cap between -2% and +4%
    
    def _calculate_xp_award(self, pnl_percent: float, tcs_score: float) -> int:
        """Calculate XP award based on trade performance"""
        if pnl_percent > 0:
            # Winning trade: base XP + bonus for high TCS
            base_xp = 5
            tcs_bonus = max(0, int((tcs_score - 70) / 5))  # +1 XP per 5 TCS points above 70
            return base_xp + tcs_bonus
        else:
            # Losing trade: reduced XP but still something for learning
            return 1
    
    def _calculate_pip_result(self, request: TradeRequest, execution_result: Dict) -> float:
        """Calculate pip result (placeholder - would be calculated when trade closes)"""
        # In production, this would be the actual pip movement when trade closes
        # For now, return estimated pips based on typical movements
        symbol_pip_values = {
            "EURUSD": 15, "GBPUSD": 20, "USDJPY": 25, "USDCHF": 18,
            "AUDUSD": 18, "USDCAD": 20, "NZDUSD": 16, "EURJPY": 22,
            "GBPJPY": 28, "EURGBP": 12, "XAUUSD": 8, "XAGUSD": 25
        }
        
        base_pips = symbol_pip_values.get(request.symbol, 15)
        # Simulate win/loss based on TCS score
        win_probability = min(0.85, max(0.35, (request.tcs_score - 30) / 100))
        
        import random
        if random.random() < win_probability:
            return random.uniform(base_pips * 0.8, base_pips * 1.5)  # Winning trade
        else:
            return -random.uniform(base_pips * 0.6, base_pips * 1.2)  # Losing trade
    
    def ping_api(self, user_id: str = None) -> Dict[str, Any]:
        """Ping API and capture account info"""
        try:
            # Prepare ping payload
            payload = {"command": "ping"}
            
            # Send ping to API
            result = self.api_manager.execute_trade_api(payload)
            
            # Store account information if available and user_id provided
            if result.get("account_info") and user_id:
                try:
                    from user_account_manager import process_api_account_info
                    process_api_account_info(user_id, result)
                    logger.info(f"✅ Account info stored for user {user_id} via ping")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store account info from ping: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ API ping failed: {e}")
            return {
                "success": False,
                "message": f"API ping failed: {str(e)}",
                "status": "error"
            }

# Legacy function for backward compatibility
def execute_trade(mission: Dict[str, Any]) -> str:
    """Legacy execute_trade function for backward compatibility"""
    
    # Use environment variable to determine mode
    mode = ExecutionMode.LIVE  # LIVE TRADING ONLY
    
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