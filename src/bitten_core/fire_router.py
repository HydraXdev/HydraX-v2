# fire_router.py
# BITTEN Trade Execution Interface - High Probability Trade Filtering

import json
import time
import requests
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime, timedelta

# Import existing HydraX modules for integration
import sys
sys.path.append('/root/HydraX-v2/src')

class TradeDirection(Enum):
    BUY = "buy"
    SELL = "sell"

class TradeResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REJECTED = "rejected"

@dataclass
class TradeRequest:
    """Trade request structure"""
    user_id: int
    symbol: str
    direction: TradeDirection
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = "BITTEN Auto"
    tcs_score: int = 0
    risk_level: str = "medium"

@dataclass
class TradeExecutionResult:
    """Trade execution result"""
    success: bool
    trade_id: Optional[str] = None
    message: str = ""
    execution_price: Optional[float] = None
    timestamp: Optional[str] = None
    error_code: Optional[str] = None
    tcs_score: int = 0

class TradingPairs:
    """Supported trading pairs with specifications"""
    PAIRS = {
        'GBPUSD': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.0,
            'session_hours': ['08:00-17:00', '13:00-22:00'],
            'volatility_filter': True
        },
        'USDCAD': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 2.5,
            'session_hours': ['13:00-22:00'],
            'volatility_filter': True
        },
        'GBPJPY': {
            'pip_value': 0.01,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 4.0,
            'session_hours': ['00:00-09:00', '08:00-17:00'],
            'volatility_filter': True
        },
        'EURUSD': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 2.0,
            'session_hours': ['08:00-17:00', '13:00-22:00'],
            'volatility_filter': True
        },
        'USDJPY': {
            'pip_value': 0.01,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 2.5,
            'session_hours': ['00:00-09:00', '13:00-22:00'],
            'volatility_filter': True
        }
    }

class FireRouter:
    """Advanced trade execution interface with high-probability filtering"""
    
    def __init__(self, bridge_url: str = None):
        self.bridge_url = bridge_url or os.getenv('BRIDGE_URL', 'http://127.0.0.1:9000')
        self.active_trades: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.execution_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_volume': 0.0,
            'last_execution': None
        }
        
        # Trading session and risk management
        self.max_daily_trades = 50
        self.max_concurrent_trades = 10
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Import fire modes for tier-based rules
        from .fire_modes import FireModeValidator, TIER_CONFIGS, TierLevel, FireMode
        self.fire_validator = FireModeValidator()
        
        # User tier mapping (would come from database in production)
        self.user_tiers = {}  # user_id -> TierLevel
        
    def execute_trade(self, trade_request: TradeRequest) -> TradeExecutionResult:
        """Execute trade with comprehensive validation and filtering"""
        try:
            # Reset daily counters if new day
            self._reset_daily_counters()
            
            # Comprehensive trade validation
            validation_result = self._validate_trade(trade_request)
            if not validation_result['valid']:
                return TradeExecutionResult(
                    success=False,
                    message=f"❌ {validation_result['reason']}",
                    error_code="VALIDATION_FAILED"
                )
            
            # High probability filtering
            if trade_request.tcs_score > 0:
                filter_result = self._apply_probability_filter(trade_request)
                if not filter_result['passed']:
                    return TradeExecutionResult(
                        success=False,
                        message=f"🔍 Trade filtered: {filter_result['reason']} (TCS: {trade_request.tcs_score})",
                        error_code="PROBABILITY_FILTER"
                    )
            
            # Risk management checks
            risk_check = self._check_risk_limits(trade_request)
            if not risk_check['approved']:
                return TradeExecutionResult(
                    success=False,
                    message=f"⚠️ Risk limit: {risk_check['reason']}",
                    error_code="RISK_LIMIT"
                )
            
            # Generate optimized SL/TP
            sl_tp = self._generate_smart_sl_tp(trade_request)
            trade_request.stop_loss = sl_tp['stop_loss']
            trade_request.take_profit = sl_tp['take_profit']
            
            # Execute trade via bridge
            execution_result = self._send_to_bridge(trade_request)
            
            if execution_result.success:
                # Log successful trade
                self._log_successful_trade(trade_request, execution_result)
                self.daily_trade_count += 1
                
                # Create success message with details
                success_msg = self._format_success_message(trade_request, execution_result)
                execution_result.message = success_msg
            
            return execution_result
            
        except Exception as e:
            self._log_error(f"Trade execution error: {e}")
            return TradeExecutionResult(
                success=False,
                message=f"❌ Execution error: {str(e)}",
                error_code="EXECUTION_ERROR"
            )
    
    def _validate_trade(self, request: TradeRequest) -> Dict:
        """Comprehensive trade validation"""
        
        # Check if symbol is supported
        if request.symbol not in TradingPairs.PAIRS:
            return {
                'valid': False,
                'reason': f"Unsupported symbol: {request.symbol}. Supported: {', '.join(TradingPairs.PAIRS.keys())}"
            }
        
        pair_spec = TradingPairs.PAIRS[request.symbol]
        
        # Volume validation
        if request.volume < pair_spec['min_volume']:
            return {
                'valid': False,
                'reason': f"Volume too small. Min: {pair_spec['min_volume']}"
            }
        
        if request.volume > pair_spec['max_volume']:
            return {
                'valid': False,
                'reason': f"Volume too large. Max: {pair_spec['max_volume']}"
            }
        
        # Trading session validation
        if not self._is_trading_session_active(request.symbol):
            return {
                'valid': False,
                'reason': f"Outside trading hours for {request.symbol}"
            }
        
        # Daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return {
                'valid': False,
                'reason': f"Daily trade limit reached: {self.max_daily_trades}"
            }
        
        # Concurrent trades limit
        if len(self.active_trades) >= self.max_concurrent_trades:
            return {
                'valid': False,
                'reason': f"Maximum concurrent trades: {self.max_concurrent_trades}"
            }
        
        return {'valid': True, 'reason': 'Validation passed'}
    
    def _apply_probability_filter(self, request: TradeRequest) -> Dict:
        """Apply high-probability trade filtering"""
        
        # TCS score filter
        if request.tcs_score < self.min_tcs_score:
            return {
                'passed': False,
                'reason': f"TCS score too low: {request.tcs_score} < {self.min_tcs_score}"
            }
        
        # High confidence boost
        if request.tcs_score >= self.high_confidence_threshold:
            return {
                'passed': True,
                'reason': f"High confidence trade: TCS {request.tcs_score}",
                'boost': True
            }
        
        # Additional filters can be added here:
        # - Market volatility check
        # - News event filtering
        # - Correlation analysis
        # - Sentiment analysis
        
        return {
            'passed': True,
            'reason': f"Probability filter passed: TCS {request.tcs_score}"
        }
    
    def _check_risk_limits(self, request: TradeRequest) -> Dict:
        """Risk management validation"""
        
        # Calculate position risk
        current_exposure = sum(trade.get('volume', 0) for trade in self.active_trades.values())
        total_exposure = current_exposure + request.volume
        
        # Maximum exposure limit (can be made configurable)
        max_exposure = 5.0  # 5 lots total
        if total_exposure > max_exposure:
            return {
                'approved': False,
                'reason': f"Total exposure limit: {total_exposure:.2f} > {max_exposure}"
            }
        
        # Symbol-specific exposure
        symbol_exposure = sum(
            trade.get('volume', 0) 
            for trade in self.active_trades.values() 
            if trade.get('symbol') == request.symbol
        )
        max_symbol_exposure = 2.0  # 2 lots per symbol
        
        if symbol_exposure + request.volume > max_symbol_exposure:
            return {
                'approved': False,
                'reason': f"{request.symbol} exposure limit: {symbol_exposure + request.volume:.2f} > {max_symbol_exposure}"
            }
        
        return {'approved': True, 'reason': 'Risk limits approved'}
    
    def _generate_smart_sl_tp(self, request: TradeRequest) -> Dict:
        """Generate intelligent stop loss and take profit levels"""
        
        pair_spec = TradingPairs.PAIRS[request.symbol]
        pip_value = pair_spec['pip_value']
        
        # Base SL/TP distances in pips (can be enhanced with volatility analysis)
        base_sl_pips = 20
        base_tp_pips = 40
        
        # Adjust based on TCS score (higher confidence = tighter stops)
        if request.tcs_score >= 90:
            sl_pips = base_sl_pips * 0.8  # Tighter stop for high confidence
            tp_pips = base_tp_pips * 1.5  # Larger target
        elif request.tcs_score >= 80:
            sl_pips = base_sl_pips
            tp_pips = base_tp_pips * 1.2
        else:
            sl_pips = base_sl_pips * 1.2  # Wider stop for lower confidence
            tp_pips = base_tp_pips
        
        # Calculate actual levels (this would need current price in real implementation)
        # For now, using relative pip distances
        sl_distance = sl_pips * pip_value
        tp_distance = tp_pips * pip_value
        
        return {
            'stop_loss': sl_distance,
            'take_profit': tp_distance,
            'sl_pips': sl_pips,
            'tp_pips': tp_pips,
            'risk_reward_ratio': tp_pips / sl_pips
        }
    
    def _send_to_bridge(self, request: TradeRequest) -> TradeExecutionResult:
        """Send trade to MT5 bridge"""
        try:
            # Prepare bridge payload
            payload = {
                'action': 'trade',
                'symbol': request.symbol,
                'direction': request.direction.value,
                'volume': request.volume,
                'stop_loss': request.stop_loss,
                'take_profit': request.take_profit,
                'comment': f"{request.comment} TCS:{request.tcs_score}",
                'timestamp': datetime.now().isoformat(),
                'user_id': request.user_id
            }
            
            # Send to bridge (placeholder for now - will connect to actual MT5 bridge later)
            # response = requests.post(f"{self.bridge_url}/execute", json=payload, timeout=10)
            
            # Simulated response for development
            simulated_success = request.tcs_score >= 75  # Higher TCS = higher success rate
            
            if simulated_success:
                trade_id = f"T{int(time.time())}{request.user_id}"
                return TradeExecutionResult(
                    success=True,
                    trade_id=trade_id,
                    execution_price=1.2500,  # Placeholder price
                    timestamp=datetime.now().isoformat(),
                    tcs_score=request.tcs_score
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message="❌ Bridge execution failed",
                    error_code="BRIDGE_ERROR"
                )
                
        except requests.exceptions.RequestException as e:
            return TradeExecutionResult(
                success=False,
                message=f"❌ Bridge connection error: {str(e)}",
                error_code="BRIDGE_CONNECTION"
            )
    
    def _format_success_message(self, request: TradeRequest, result: TradeExecutionResult) -> str:
        """Format successful trade message for Telegram"""
        
        sl_tp_info = self._generate_smart_sl_tp(request)
        
        confidence_emoji = "🎯" if request.tcs_score >= 85 else "✅"
        
        message = f"""{confidence_emoji} **Trade Executed Successfully**

📈 **{request.symbol}** {request.direction.value.upper()}
💰 **Volume:** {request.volume} lots
🎯 **TCS Score:** {request.tcs_score}/100
💵 **Price:** {result.execution_price}
🛡️ **Stop Loss:** {sl_tp_info['sl_pips']:.0f} pips
🎯 **Take Profit:** {sl_tp_info['tp_pips']:.0f} pips
⚖️ **R:R Ratio:** 1:{sl_tp_info['risk_reward_ratio']:.1f}

🔖 **Trade ID:** {result.trade_id}
⏰ **Time:** {datetime.now().strftime("%H:%M:%S")}"""

        return message
    
    def close_trade(self, trade_id: str, user_id: int) -> TradeExecutionResult:
        """Close specific trade"""
        try:
            if trade_id not in self.active_trades:
                return TradeExecutionResult(
                    success=False,
                    message=f"❌ Trade not found: {trade_id}",
                    error_code="TRADE_NOT_FOUND"
                )
            
            trade = self.active_trades[trade_id]
            
            # Send close request to bridge
            payload = {
                'action': 'close',
                'trade_id': trade_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Simulate close (will connect to actual bridge later)
            # response = requests.post(f"{self.bridge_url}/close", json=payload, timeout=10)
            
            # Remove from active trades
            del self.active_trades[trade_id]
            
            return TradeExecutionResult(
                success=True,
                trade_id=trade_id,
                message=f"✅ Trade {trade_id} closed successfully",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return TradeExecutionResult(
                success=False,
                message=f"❌ Error closing trade: {str(e)}",
                error_code="CLOSE_ERROR"
            )
    
    def get_positions(self, user_id: int) -> Dict:
        """Get current positions for user"""
        user_trades = {
            tid: trade for tid, trade in self.active_trades.items() 
            if trade.get('user_id') == user_id
        }
        
        if not user_trades:
            return {
                'success': True,
                'message': "📊 **No Active Positions**\n\nUse `/fire SYMBOL buy/sell SIZE` to open a position.",
                'positions': []
            }
        
        position_msg = f"📊 **Active Positions ({len(user_trades)})**\n\n"
        
        for trade_id, trade in user_trades.items():
            position_msg += f"🔹 **{trade['symbol']}** {trade['direction'].upper()}\n"
            position_msg += f"   Volume: {trade['volume']} lots\n"
            position_msg += f"   ID: `{trade_id}`\n"
            position_msg += f"   TCS: {trade.get('tcs_score', 'N/A')}\n\n"
        
        position_msg += "💡 Use `/close TRADE_ID` to close a position"
        
        return {
            'success': True,
            'message': position_msg,
            'positions': list(user_trades.keys())
        }
    
    def _is_trading_session_active(self, symbol: str) -> bool:
        """Check if current time is within trading session"""
        # Simplified session check - can be enhanced with timezone handling
        current_hour = datetime.now().hour
        
        # Most forex pairs are active during major sessions
        # London: 8-17, NY: 13-22, Tokyo: 0-9
        active_hours = [
            (0, 9),   # Tokyo
            (8, 17),  # London  
            (13, 22)  # New York
        ]
        
        for start, end in active_hours:
            if start <= current_hour <= end:
                return True
        
        return False
    
    def _reset_daily_counters(self):
        """Reset daily trading counters"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_trade_count = 0
            self.last_reset_date = current_date
    
    def _log_successful_trade(self, request: TradeRequest, result: TradeExecutionResult):
        """Log successful trade for statistics"""
        self.active_trades[result.trade_id] = {
            'user_id': request.user_id,
            'symbol': request.symbol,
            'direction': request.direction,
            'volume': request.volume,
            'execution_price': result.execution_price,
            'timestamp': result.timestamp,
            'tcs_score': request.tcs_score
        }
        
        self.execution_stats['total_trades'] += 1
        self.execution_stats['successful_trades'] += 1
        self.execution_stats['total_volume'] += request.volume
        self.execution_stats['last_execution'] = result.timestamp
    
    def _log_error(self, error_msg: str):
        """Log error for monitoring"""
        print(f"[FIRE_ROUTER ERROR] {datetime.now().isoformat()}: {error_msg}")
        self.execution_stats['failed_trades'] += 1
    
    def get_execution_stats(self) -> Dict:
        """Get trading execution statistics"""
        success_rate = 0
        if self.execution_stats['total_trades'] > 0:
            success_rate = (self.execution_stats['successful_trades'] / self.execution_stats['total_trades']) * 100
        
        return {
            'total_trades': self.execution_stats['total_trades'],
            'successful_trades': self.execution_stats['successful_trades'],
            'failed_trades': self.execution_stats['failed_trades'],
            'success_rate': f"{success_rate:.1f}%",
            'total_volume': f"{self.execution_stats['total_volume']:.2f} lots",
            'active_positions': len(self.active_trades),
            'daily_trades': self.daily_trade_count,
            'last_execution': self.execution_stats['last_execution']
        }
