# fire_router.py
# BITTEN Trade Execution Interface - High Probability Trade Filtering

import json
import time
import requests
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime, timedelta
import random
import hashlib

# Import existing HydraX modules for integration
import sys
sys.path.append('/root/HydraX-v2/src')

# Import fire mode types
from .fire_modes import FireModeValidator, TIER_CONFIGS, TierLevel, FireMode

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
    fire_mode: FireMode = FireMode.SINGLE_SHOT

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
        # Core pairs - standard tier requirements
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
        },
        # Extra pairs - require 85% minimum TCS
        'AUDUSD': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.0,
            'session_hours': ['00:00-09:00'],
            'volatility_filter': True
        },
        'NZDUSD': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.5,
            'session_hours': ['00:00-09:00'],
            'volatility_filter': True
        },
        'AUDJPY': {
            'pip_value': 0.01,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 4.0,
            'session_hours': ['00:00-09:00'],
            'volatility_filter': True
        },
        'EURJPY': {
            'pip_value': 0.01,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.5,
            'session_hours': ['08:00-17:00'],
            'volatility_filter': True
        },
        'EURGBP': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.0,
            'session_hours': ['08:00-17:00'],
            'volatility_filter': True
        },
        'GBPCHF': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 4.0,
            'session_hours': ['08:00-17:00'],
            'volatility_filter': True
        },
        'USDCHF': {
            'pip_value': 0.0001,
            'min_volume': 0.01,
            'max_volume': 100.0,
            'spread_limit': 3.0,
            'session_hours': ['08:00-17:00', '13:00-22:00'],
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
        
        # TCS thresholds from THE LAW
        self.min_tcs_score = 70  # Base minimum (Nibbler)
        self.high_confidence_threshold = 85  # High confidence trades
        
        # Import fire modes for tier-based rules
        from .fire_modes import FireModeValidator, TIER_CONFIGS, TierLevel, FireMode
        self.fire_validator = FireModeValidator()
        
        # User tier mapping (would come from database in production)
        self.user_tiers = {}  # user_id -> TierLevel
        self.last_shot_time = {}  # user_id -> datetime
        
        # Bit mode decision tracking
        self.pending_bit_decisions = {}  # decision_id -> trade_request
        
        # Low TCS warning tracking
        self.pending_low_tcs_trades = {}  # warning_id -> {trade_request, warning_dialog, timestamp}
        
        # Bot personalities for UI responses
        self.bot_responses = {
            'drillbot': {
                'pre_trade': "SCANNING TARGET. MAINTAIN DISCIPLINE.",
                'win': "ACCEPTABLE. FORGET IT. NEXT TARGET.",
                'loss': "SLOPPY. BUT YOU FOLLOWED PROTOCOL. IMPROVE.",
                'panic': "WEAKNESS DETECTED. CONTROL YOUR EMOTIONS."
            },
            'medicbot': {
                'pre_trade': "Vitals stable. You're ready for this.",
                'win': "Dopamine spike controlled. Well managed.",
                'loss': "You're bleeding, but you're not broken. Breathe. Analyze. Heal.",
                'panic': "Cortisol spike detected. Let's process this properly."
            },
            'bit': {
                'calm': "*calm purring*",
                'alert': "*ears perked, watching intensely*",
                'warning': "*low growl, blocking UI elements*",
                'comfort': "*comforting nuzzle*"
            }
        }
        
        # Initialize tactical education system
        self.education_system = TacticalEducationSystem()
        self.user_performance = {}  # user_id -> performance metrics
        self.active_missions = {}  # user_id -> active mission data
        self.recovery_games = {}  # user_id -> mini-game state
        
    def execute_trade(self, trade_request: TradeRequest) -> TradeExecutionResult:
        """Execute trade with comprehensive validation and filtering"""
        try:
            # Reset daily counters if new day
            self._reset_daily_counters()
            
            # Build user profile for validation
            user_profile = self._build_user_profile(trade_request.user_id)
            
            # Check for tactical recovery period (cooldown as game mechanic)
            recovery_check = self._check_tactical_recovery(trade_request.user_id)
            if recovery_check['in_recovery']:
                return self._handle_recovery_period(trade_request.user_id, recovery_check)
            
            # Generate mission briefing instead of warnings
            mission_briefing = self.education_system.generate_mission_briefing(
                trade_request, user_profile, self._get_user_performance(trade_request.user_id)
            )
            
            # If educational intervention needed, make it feel like squad support
            if mission_briefing.get('requires_support'):
                return self._provide_squad_support(trade_request, mission_briefing)
            
            # Integrate Uncertainty & Control Interplay System
            from .uncertainty_control_system import UncertaintyControlSystem, ControlMode, BitModeDecision
            uncertainty_system = UncertaintyControlSystem()
            
            # Check if user is in Bit Mode (requires YES/NO confirmation)
            if uncertainty_system.current_mode == ControlMode.BIT_MODE:
                # Create binary decision point
                context = f"trade_entry"
                trade_data = {
                    'symbol': trade_request.symbol,
                    'direction': trade_request.direction.value,
                    'volume': trade_request.volume,
                    'tcs_score': trade_request.tcs_score
                }
                
                decision = uncertainty_system.activate_bit_mode(context, None)
                
                # Store decision and trade request for later processing
                self.pending_bit_decisions[decision.decision_id] = trade_request
                
                # Return decision request instead of executing immediately
                return TradeExecutionResult(
                    success=False,
                    message=f"🤖 **BIT MODE ACTIVE**\n\n{decision.question}\n\n**Trade Details:**\n📊 {trade_request.symbol} {trade_request.direction.value.upper()}\n💰 Volume: {trade_request.volume}\n🎯 TCS: {trade_request.tcs_score}\n\n*Respond with `/yes {decision.decision_id}` or `/no {decision.decision_id}`*",
                    error_code="BIT_MODE_CONFIRMATION_REQUIRED",
                    trade_id=decision.decision_id  # Store decision ID for later processing
                )
            
            # Apply uncertainty injection for other modes
            decision_point = {
                'symbol': trade_request.symbol,
                'tcs_score': trade_request.tcs_score,
                'fire_mode': trade_request.fire_mode.value,
                'confidence_score': trade_request.tcs_score / 100
            }
            modified_decision = uncertainty_system.inject_uncertainty(decision_point)
            
            # Apply uncertainty modifications
            if modified_decision.get('artificial_delay'):
                import time
                time.sleep(min(modified_decision['artificial_delay'], 30))
                
            # Apply dynamic difficulty adjustments based on performance
            difficulty_adjustment = self.education_system.calculate_difficulty_adjustment(
                trade_request.user_id,
                self._get_user_performance(trade_request.user_id)
            )
            
            # Modify TCS requirement based on performance (stealth education)
            adjusted_tcs = trade_request.tcs_score
            if difficulty_adjustment['modifier'] != 1.0:
                adjusted_tcs = int(trade_request.tcs_score * difficulty_adjustment['modifier'])
                # Don't tell the user - this is stealth education
            
            # Run comprehensive fire mode validation
            from .fire_mode_validator import validate_fire_request, apply_trade_mutations
            
            trade_payload = {
                'tcs': adjusted_tcs,  # Use adjusted TCS for validation
                'fire_mode': trade_request.fire_mode.value,
                'symbol': trade_request.symbol,
                'risk_percent': 2.0,  # Default 2% risk
                'volume': trade_request.volume,
                'signal_type': 'arcade'  # Would come from signal analyzer
            }
            
            # Apply Stealth Mode mutations if active
            if uncertainty_system.current_mode == ControlMode.STEALTH_MODE:
                base_algorithm = {
                    'entry_delay': trade_payload.get('entry_delay', 0),
                    'size_multiplier': 1.0,
                    'tp_multiplier': 1.0
                }
                modified_algorithm = uncertainty_system.activate_stealth_mode(base_algorithm)
                
                if modified_algorithm.get('stealth_applied'):
                    # Apply stealth variations
                    if 'entry_delay' in modified_algorithm:
                        trade_payload['entry_delay'] = modified_algorithm['entry_delay']
                    if modified_algorithm.get('size_multiplier', 1.0) != 1.0:
                        trade_request.volume *= modified_algorithm['size_multiplier']
            
            fire_validation = validate_fire_request(trade_payload, str(trade_request.user_id), user_profile)
            
            if not fire_validation['valid']:
                # Check if this is a low TCS warning case
                if fire_validation.get('reason') == 'LOW_TCS_WARNING_REQUIRED':
                    # Get the warning dialog from mutations
                    warning_dialog = fire_validation.get('mutations', {}).get('warning_dialog')
                    if warning_dialog:
                        # Import the warning formatter
                        from .bit_warnings import format_warning_for_telegram
                        
                        # Format the warning message
                        warning_message = format_warning_for_telegram(warning_dialog)
                        
                        # Store the trade request for later processing after confirmation
                        warning_id = f"tcs_warning_{trade_request.user_id}_{int(time.time())}"
                        self.pending_low_tcs_trades[warning_id] = {
                            'trade_request': trade_request,
                            'warning_dialog': warning_dialog,
                            'timestamp': datetime.now()
                        }
                        
                        # Return warning dialog
                        return TradeExecutionResult(
                            success=False,
                            message=warning_message,
                            error_code="LOW_TCS_WARNING",
                            trade_id=warning_id  # Use this to track the warning
                        )
                
                # Regular validation failure
                bot_msgs = fire_validation.get('bot_responses', {})
                formatted_msg = f"❌ {fire_validation['reason']}\n\n"
                if bot_msgs.get('drillbot'):
                    formatted_msg += f"🤖 **{bot_msgs['drillbot']}**\n"
                if bot_msgs.get('medicbot'):
                    formatted_msg += f"💊 {bot_msgs['medicbot']}\n"
                if bot_msgs.get('bit'):
                    formatted_msg += f"🐾 {bot_msgs['bit']}"
                
                return TradeExecutionResult(
                    success=False,
                    message=formatted_msg,
                    error_code="FIRE_MODE_VALIDATION"
                )
            
            # Apply any mutations from validation
            if fire_validation.get('mutations'):
                modified_payload = apply_trade_mutations(trade_payload, fire_validation['mutations'])
                trade_request.volume = modified_payload.get('volume', trade_request.volume)
            
            # Apply execution delay if needed
            if fire_validation.get('delay'):
                import time
                time.sleep(min(fire_validation['delay'], 5))  # Cap at 5 seconds
            
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
            
            # Risk management checks with HARD LOCK validation
            risk_check = self._check_risk_limits(trade_request)
            if not risk_check['approved']:
                # HARD LOCK: Block the trade, no auto-adjustment
                return TradeExecutionResult(
                    success=False,
                    message=risk_check['reason'],
                    error_code="RISK_LIMIT_HARD_LOCK"
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
                
                # Update performance metrics for stealth education
                self._update_performance_metrics(trade_request.user_id, True, trade_request)
                
                # Generate tactical debrief (educational content disguised as game feedback)
                debrief = self.education_system.generate_tactical_debrief(
                    trade_request, execution_result, self._get_user_performance(trade_request.user_id)
                )
                
                # Check for achievement unlocks (gamified learning milestones)
                achievements = self._check_achievements(trade_request.user_id)
                
                # Generate Gemini comparison if in Gemini mode
                if uncertainty_system.current_mode == ControlMode.GEMINI_MODE:
                    trading_scenario = {
                        'description': f"{trade_request.symbol} {trade_request.direction.value.upper()} trade",
                        'tcs_score': trade_request.tcs_score,
                        'volume': trade_request.volume
                    }
                    gemini_challenge = uncertainty_system.generate_gemini_challenge(trading_scenario)
                    execution_result.message += f"\n\n🤖 **GEMINI CHALLENGE**\nGemini Action: {gemini_challenge.gemini_action}\nGemini Confidence: {gemini_challenge.gemini_confidence:.0%}\n💭 {gemini_challenge.psychological_impact}"
                
                # Create success message with tactical feedback
                success_msg = self._format_success_message(trade_request, execution_result)
                
                # Add debrief and achievements
                if debrief:
                    success_msg += f"\n\n{debrief}"
                if achievements:
                    success_msg += f"\n\n🏆 **ACHIEVEMENTS UNLOCKED:**\n{achievements}"
                
                execution_result.message = success_msg
            else:
                # Update performance for failed trades
                self._update_performance_metrics(trade_request.user_id, False, trade_request)
            
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
        
        # Daily trade limit (with bonuses)
        # Get user tier for bonus checking
        user_tier = self.user_tiers.get(request.user_id, TierLevel.NIBBLER)
        bonuses = self._check_active_bonuses(request.user_id, user_tier.value)
        
        max_daily_with_bonus = self.max_daily_trades + bonuses['daily_shots']
        
        if self.daily_trade_count >= max_daily_with_bonus:
            return {
                'valid': False,
                'reason': f"Daily trade limit reached: {max_daily_with_bonus} (includes {bonuses['daily_shots']} bonus shots)"
            }
        
        # Concurrent trades limit (with position bonuses)
        max_positions_with_bonus = self.max_concurrent_trades + bonuses['positions']
        
        if len(self.active_trades) >= max_positions_with_bonus:
            return {
                'valid': False,
                'reason': f"Maximum concurrent trades: {max_positions_with_bonus} (includes {bonuses['positions']} bonus positions)"
            }
        
        return {'valid': True, 'reason': 'Validation passed'}
    
    def _apply_probability_filter(self, request: TradeRequest) -> Dict:
        """Apply high-probability trade filtering with tier-based rules"""
        
        # Get user tier
        user_tier = self.user_tiers.get(request.user_id, TierLevel.NIBBLER)
        tier_config = TIER_CONFIGS[user_tier]
        
        # Tier-specific TCS requirement (with arcade/sniper split for FANG)
        if user_tier == TierLevel.FANG and hasattr(request, 'signal_type'):
            # Load FANG config for arcade/sniper split
            import yaml
            config_path = '/root/HydraX-v2/config/tier_settings.yml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            fang_config = config['tiers']['FANG']['fire_settings']
            
            # Use different TCS based on signal type
            if request.signal_type == 'sniper':
                min_tcs = fang_config.get('min_tcs_sniper', 85)
                signal_label = "sniper"
            else:  # arcade
                min_tcs = fang_config.get('min_tcs_arcade', 75)
                signal_label = "arcade"
                
            if request.tcs_score < min_tcs:
                return {
                    'passed': False,
                    'reason': f"TCS below FANG {signal_label} minimum: {request.tcs_score} < {min_tcs}"
                }
        else:
            # Standard TCS check for other tiers
            min_tcs = tier_config.min_tcs
            if request.tcs_score < min_tcs:
                return {
                    'passed': False,
                    'reason': f"TCS below {tier_config.name} minimum: {request.tcs_score} < {min_tcs}"
                }
        
        # High confidence boost
        if request.tcs_score >= self.high_confidence_threshold:
            return {
                'passed': True,
                'reason': f"High confidence trade: TCS {request.tcs_score}",
                'boost': True
            }
        
        # Check fire mode permissions
        fire_mode = getattr(request, 'fire_mode', FireMode.SINGLE_SHOT)
        can_fire, reason = self.fire_validator.can_fire(
            request.user_id, user_tier, fire_mode, request.tcs_score
        )
        
        if not can_fire:
            return {
                'passed': False,
                'reason': reason
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
        """Risk management validation with HARD LOCK protection"""
        
        try:
            # Load bitmode configuration
            import yaml
            config_path = '/root/HydraX-v2/config/tier_settings.yml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            bitmode = config.get('bitmode', {})
            
            # Get account info (would come from MT5 in production)
            account = self._get_account_info(request.user_id)
            
            # Calculate stop loss distance in pips
            sl_tp_data = self._generate_smart_sl_tp(request)
            stop_loss_pips = sl_tp_data['sl_pips']
            
            # HARD LOCK: Calculate actual risk percentage
            pip_value_per_lot = 10  # Standard for forex
            risk_amount = request.volume * stop_loss_pips * pip_value_per_lot
            risk_percent = (risk_amount / account.balance) * 100
            
            # Check 1: Single trade risk limit from bitmode
            max_risk = bitmode.get('risk_boost', 2.5) if account.balance >= bitmode.get('boost_min_balance', 500) else bitmode.get('risk_default', 2.0)
            
            if risk_percent > max_risk:
                return {
                    'approved': False,
                    'reason': f"🔒 HARD LOCK: Trade risks {risk_percent:.1f}% of account, exceeds {max_risk}% limit"
                }
            
            # Check 2: Daily drawdown cap from bitmode
            # Get daily P&L (would come from database in production)
            daily_loss = self._get_daily_pnl(request.user_id)
            daily_loss_percent = abs(daily_loss / account.balance * 100) if daily_loss < 0 else 0
            
            drawdown_cap = bitmode.get('drawdown_cap', 6.0)
            if daily_loss_percent + risk_percent > drawdown_cap:
                remaining = drawdown_cap - daily_loss_percent
                if remaining <= 0:
                    return {
                        'approved': False,
                        'reason': f"🛑 HARD LOCK: Daily {drawdown_cap}% loss limit reached. No more trades today."
                    }
                else:
                    return {
                        'approved': False,
                        'reason': f"🔒 HARD LOCK: Trade would exceed {drawdown_cap}% daily limit. Only {remaining:.1f}% risk remaining today."
                    }
            
            # Additional exposure checks (existing logic)
            current_exposure = sum(trade.get('volume', 0) for trade in self.active_trades.values())
            total_exposure = current_exposure + request.volume
            
            # Maximum exposure limit
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
            
            # All checks passed
            return {
                'approved': True, 
                'reason': 'Risk limits approved',
                'risk_percent': risk_percent,
                'daily_loss_percent': daily_loss_percent
            }
            
        except Exception as e:
            self._log_error(f"Risk validation error: {e}")
            # On error, reject trade for safety
            return {
                'approved': False,
                'reason': f"Risk validation error: {str(e)}. Trade blocked for safety."
            }
    
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
        """Send trade to MT5 bridge with enhanced tier-based execution"""
        try:
            # Get user tier for special features
            user_tier = self.user_tiers.get(request.user_id, TierLevel.NIBBLER)
            tier_config = TIER_CONFIGS[user_tier]
            
            # Apply Stealth Mode for APEX tier
            if user_tier == TierLevel.APEX and request.fire_mode == FireMode.STEALTH:
                from .fire_modes import StealthMode
                stealth = StealthMode()
                trade_params = {
                    'volume': request.volume,
                    'entry_delay': 0
                }
                trade_params = stealth.apply_stealth(trade_params)
                request.volume = trade_params['volume']
                # Add delay if stealth mode requires it
                if trade_params.get('entry_delay', 0) > 0:
                    time.sleep(min(trade_params['entry_delay'], 5))  # Cap at 5 seconds
            
            # Prepare bridge payload
            payload = {
                'action': 'trade',
                'symbol': request.symbol,
                'direction': request.direction.value,
                'volume': request.volume,
                'stop_loss': request.stop_loss,
                'take_profit': request.take_profit,
                'comment': f"{request.comment} TCS:{request.tcs_score} {request.fire_mode.value} [{getattr(request, 'signal_type', 'arcade').upper()}]",
                'timestamp': datetime.now().isoformat(),
                'user_id': request.user_id,
                'tier': user_tier.value,
                'fire_mode': request.fire_mode.value
            }
            
            # Actual bridge connection (when MT5 bridge is ready)
            if os.getenv('USE_LIVE_BRIDGE', 'false').lower() == 'true':
                response = requests.post(
                    f"{self.bridge_url}/execute", 
                    json=payload, 
                    timeout=10,
                    headers={'Authorization': f'Bearer {os.getenv("BRIDGE_API_KEY", "")}'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return TradeExecutionResult(
                        success=True,
                        trade_id=result.get('trade_id'),
                        execution_price=result.get('price'),
                        timestamp=result.get('timestamp'),
                        tcs_score=request.tcs_score
                    )
                else:
                    return TradeExecutionResult(
                        success=False,
                        message=f"❌ Bridge error: {response.status_code}",
                        error_code=f"BRIDGE_{response.status_code}"
                    )
            
            # Development mode - simulated response
            else:
                # Simulate execution with tier-based success rates
                base_success_rate = 0.6
                tcs_bonus = (request.tcs_score - 70) * 0.01  # 1% per TCS point above 70
                tier_bonus = {
                    TierLevel.NIBBLER: 0,
                    TierLevel.FANG: 0.05,
                    TierLevel.COMMANDER: 0.1,
                    TierLevel.APEX: 0.15
                }.get(user_tier, 0)
                
                success_rate = min(base_success_rate + tcs_bonus + tier_bonus, 0.95)
                simulated_success = request.tcs_score >= 75 or (time.time() % 100) / 100 < success_rate
                
                if simulated_success:
                    trade_id = f"T{int(time.time())}{request.user_id}"
                    # Record shot for fire mode tracking
                    self.fire_validator.record_shot(request.user_id, request.fire_mode)
                    
                    return TradeExecutionResult(
                        success=True,
                        trade_id=trade_id,
                        execution_price=1.2500,  # Would come from price feed
                        timestamp=datetime.now().isoformat(),
                        tcs_score=request.tcs_score
                    )
                else:
                    return TradeExecutionResult(
                        success=False,
                        message="❌ Trade rejected by market conditions",
                        error_code="MARKET_REJECT"
                    )
                    
        except requests.exceptions.RequestException as e:
            return TradeExecutionResult(
                success=False,
                message=f"❌ Bridge connection error: {str(e)}",
                error_code="BRIDGE_CONNECTION"
            )
    
    def _format_success_message(self, request: TradeRequest, result: TradeExecutionResult) -> str:
        """Format successful trade message with bot personalities for Telegram"""
        
        sl_tp_info = self._generate_smart_sl_tp(request)
        
        # Fire mode indicators
        fire_mode_icon = {
            FireMode.SINGLE_SHOT: "🔫",
            FireMode.CHAINGUN: "🔥",
            FireMode.AUTO_FIRE: "🤖",
            FireMode.STEALTH: "👻",
            FireMode.MIDNIGHT_HAMMER: "🔨"
        }.get(request.fire_mode, "🔫")
        
        confidence_emoji = "🎯" if request.tcs_score >= 85 else "✅"
        
        # Get user tier
        user_tier = self.user_tiers.get(request.user_id, TierLevel.NIBBLER)
        tier_badge = {
            TierLevel.NIBBLER: "🟢",
            TierLevel.FANG: "🔵",
            TierLevel.COMMANDER: "🟣",
            TierLevel.APEX: "🔴"
        }.get(user_tier, "🟢")
        
        message = f"""{confidence_emoji} **Trade Executed Successfully**

{fire_mode_icon} **Fire Mode:** {request.fire_mode.value.replace('_', ' ').title()}
📈 **{request.symbol}** {request.direction.value.upper()}
💰 **Volume:** {request.volume} lots
🎯 **TCS Score:** {request.tcs_score}/100
💵 **Price:** {result.execution_price}
🛡️ **Stop Loss:** {sl_tp_info['sl_pips']:.0f} pips
🎯 **Take Profit:** {sl_tp_info['tp_pips']:.0f} pips
⚖️ **R:R Ratio:** 1:{sl_tp_info['risk_reward_ratio']:.1f}

{tier_badge} **Tier:** {user_tier.value.upper()}
🔖 **Trade ID:** {result.trade_id}
⏰ **Time:** {datetime.now().strftime("%H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━

💬 **{self.bot_responses['drillbot']['pre_trade']}**

🐾 {self.bot_responses['bit']['alert']}"""

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
            
            # Calculate XP for FANG tier trades
            xp_message = ""
            user_tier = self.user_tiers.get(user_id, TierLevel.NIBBLER)
            
            if user_tier == TierLevel.FANG:
                from .sniper_xp_handler import calculate_fang_trade_xp
                
                # Simulate trade result (would come from MT5 in production)
                exit_price = 1.2550  # Simulated
                pnl = 50.0  # Simulated profit
                exit_reason = 'manual_close'  # or 'tp_hit', 'sl_hit'
                
                xp_result = calculate_fang_trade_xp(
                    trade_id=trade_id,
                    signal_type=trade.get('signal_type', 'arcade'),
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    pnl=pnl
                )
                
                if 'final_xp' in xp_result:
                    xp_message = f"\n\n{xp_result['message']}\n🎖️ XP Earned: +{xp_result['final_xp']}"
            
            # Remove from active trades
            del self.active_trades[trade_id]
            
            return TradeExecutionResult(
                success=True,
                trade_id=trade_id,
                message=f"✅ Trade {trade_id} closed successfully{xp_message}",
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
        # Store trade data including signal type
        trade_data = {
            'user_id': request.user_id,
            'symbol': request.symbol,
            'direction': request.direction,
            'volume': request.volume,
            'execution_price': result.execution_price,
            'timestamp': result.timestamp,
            'tcs_score': request.tcs_score,
            'signal_type': getattr(request, 'signal_type', 'arcade')  # Track signal type
        }
        
        self.active_trades[result.trade_id] = trade_data
        
        # For FANG tier sniper trades, register with XP handler
        user_tier = self.user_tiers.get(request.user_id, TierLevel.NIBBLER)
        if user_tier == TierLevel.FANG and trade_data['signal_type'] == 'sniper':
            # Register sniper trade for XP tracking
            from .sniper_xp_handler import calculate_fang_trade_xp
            
            # Generate SL/TP from smart levels (would come from actual trade in production)
            sl_tp = self._generate_smart_sl_tp(request)
            
            entry_data = {
                'user_id': request.user_id,
                'symbol': request.symbol,
                'entry_price': result.execution_price or 1.0,
                'tp_price': (result.execution_price or 1.0) + sl_tp['take_profit'],
                'sl_price': (result.execution_price or 1.0) - sl_tp['stop_loss']
            }
            
            calculate_fang_trade_xp(
                trade_id=result.trade_id,
                signal_type='sniper',
                exit_price=0,
                exit_reason='',
                pnl=0,
                entry_data=entry_data
            )
        
        self.execution_stats['total_trades'] += 1
        self.execution_stats['successful_trades'] += 1
        self.execution_stats['total_volume'] += request.volume
        self.execution_stats['last_execution'] = result.timestamp
    
    def _log_error(self, error_msg: str):
        """Log error for monitoring"""
        print(f"[FIRE_ROUTER ERROR] {datetime.now().isoformat()}: {error_msg}")
        self.execution_stats['failed_trades'] += 1
    
    def _log_info(self, info_msg: str):
        """Log info for monitoring"""
        print(f"[FIRE_ROUTER INFO] {datetime.now().isoformat()}: {info_msg}")
    
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
    
    def _build_user_profile(self, user_id: int) -> Dict:
        """Build user profile for fire mode validation"""
        # In production, this would fetch from database
        # For now, build from available data
        
        user_tier = self.user_tiers.get(user_id, TierLevel.NIBBLER)
        
        # Count user's active trades
        user_trades = [t for t in self.active_trades.values() if t.get('user_id') == user_id]
        
        # Calculate daily stats
        daily_trades = sum(1 for t in self.trade_history 
                          if t.get('user_id') == user_id 
                          and t.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d')))
        
        # Build profile
        profile = {
            'user_id': user_id,
            'tier': user_tier.value,
            'shots_today': daily_trades,
            'open_positions': len(user_trades),
            'account_balance': 10000,  # Placeholder - would come from MT5
            'daily_loss_percent': 0,  # Would calculate from trade history
            'total_exposure_percent': sum(t.get('volume', 0) * 2 for t in user_trades),  # 2% per lot
            'last_loss_time': None,  # Would track from trade history
            'last_shot_time': self.last_shot_time.get(user_id),
            'xp_penalty_active': False,  # Would come from XP system
            'recent_win_rate': 0.65,  # Placeholder
            'active_chaingun_sequence': None,  # Would track chaingun state
            'active_hammer_event': None  # Would check for network events
        }
        
        return profile
    
    def process_bit_mode_confirmation(self, decision_id: str, choice: bool, user_id: int) -> TradeExecutionResult:
        """Process user's YES/NO confirmation for bit mode"""
        try:
            # Check if decision exists
            if decision_id not in self.pending_bit_decisions:
                return TradeExecutionResult(
                    success=False,
                    message="❌ Decision not found or expired",
                    error_code="DECISION_NOT_FOUND"
                )
            
            # Get the original trade request
            trade_request = self.pending_bit_decisions[decision_id]
            
            # Verify user owns this decision
            if trade_request.user_id != user_id:
                return TradeExecutionResult(
                    success=False,
                    message="❌ Unauthorized decision access",
                    error_code="UNAUTHORIZED"
                )
            
            # Initialize uncertainty system
            from .uncertainty_control_system import UncertaintyControlSystem
            uncertainty_system = UncertaintyControlSystem()
            
            # Process the bit decision
            decision_result = uncertainty_system.process_bit_decision(decision_id, choice, user_id)
            
            if not decision_result['success']:
                return TradeExecutionResult(
                    success=False,
                    message=f"❌ {decision_result.get('error', 'Decision processing failed')}",
                    error_code="DECISION_FAILED"
                )
            
            # Clean up pending decision
            del self.pending_bit_decisions[decision_id]
            
            if choice:  # YES - execute the trade
                # Continue with normal trade execution
                result = self.execute_trade(trade_request)
                
                # Add bit response
                bit_response = decision_result.get('bit_response', '')
                if bit_response:
                    result.message += f"\n\n🤖 **BIT:** {bit_response}"
                
                return result
            else:  # NO - cancel the trade
                bit_response = decision_result.get('bit_response', '')
                return TradeExecutionResult(
                    success=False,
                    message=f"🛑 **Trade Cancelled**\n\nYou chose not to execute the {trade_request.symbol} {trade_request.direction.value.upper()} trade.\n\n🤖 **BIT:** {bit_response}",
                    error_code="USER_CANCELLED"
                )
                
        except Exception as e:
            return TradeExecutionResult(
                success=False,
                message=f"❌ Error processing confirmation: {str(e)}",
                error_code="CONFIRMATION_ERROR"
            )
    
    def set_uncertainty_mode(self, user_id: int, mode: str) -> Dict[str, Any]:
        """Set user's uncertainty control mode"""
        try:
            from .uncertainty_control_system import UncertaintyControlSystem, ControlMode
            uncertainty_system = UncertaintyControlSystem()
            
            # Map string to enum
            mode_mapping = {
                'full_control': ControlMode.FULL_CONTROL,
                'bit_mode': ControlMode.BIT_MODE,
                'stealth_mode': ControlMode.STEALTH_MODE,
                'gemini_mode': ControlMode.GEMINI_MODE,
                'chaos_mode': ControlMode.CHAOS_MODE
            }
            
            if mode not in mode_mapping:
                return {
                    'success': False,
                    'message': f"❌ Invalid mode: {mode}. Available: {', '.join(mode_mapping.keys())}"
                }
            
            control_mode = mode_mapping[mode]
            result = uncertainty_system.set_control_mode(control_mode, user_id)
            
            return {
                'success': True,
                'message': f"🎮 **Control Mode Changed**\n\n{result['response']}\n\n**New Mode:** {mode.replace('_', ' ').title()}",
                'mode': mode,
                'psychological_profile': result.get('psychological_profile', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Error setting mode: {str(e)}"
            }
    
    def get_uncertainty_status(self, user_id: int) -> Dict[str, Any]:
        """Get current uncertainty system status"""
        try:
            from .uncertainty_control_system import UncertaintyControlSystem
            uncertainty_system = UncertaintyControlSystem()
            
            status = uncertainty_system.get_system_status()
            
            # Format status message
            mode_descriptions = {
                'full_control': '🎯 **Full Control** - You have complete command authority',
                'bit_mode': '🤖 **Bit Mode** - Binary YES/NO confirmation system',
                'stealth_mode': '👻 **Stealth Mode** - Hidden algorithm variations',
                'gemini_mode': '⚡ **Gemini Mode** - AI competitor tension',
                'chaos_mode': '🌪️ **Chaos Mode** - Maximum uncertainty injection'
            }
            
            current_mode = status['current_mode']
            description = mode_descriptions.get(current_mode, 'Unknown mode')
            
            message = f"🎮 **Uncertainty & Control Status**\n\n{description}\n\n"
            message += f"**Uncertainty Level:** {status['uncertainty_level'].title()}\n"
            message += f"**Pending Decisions:** {status['pending_decisions']}\n"
            message += f"**Gemini Comparisons:** {status['gemini_comparisons']}\n\n"
            
            profile = status.get('psychological_profile', {})
            if profile:
                message += f"**Psychological Profile:**\n"
                message += f"• Control Preference: {profile.get('control_preference', 0.5):.1%}\n"
                message += f"• Decision Anxiety: {profile.get('decision_anxiety', 0.5):.1%}\n"
                message += f"• Gemini Win Rate: {profile.get('gemini_win_rate', 0.0):.1%}\n"
            
            return {
                'success': True,
                'message': message,
                'status': status
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Error getting status: {str(e)}"
            }
    
    def _check_tactical_recovery(self, user_id: int) -> Dict[str, Any]:
        """Check if user is in tactical recovery period (cooldown as game mechanic)"""
        last_shot = self.last_shot_time.get(user_id)
        if not last_shot:
            return {'in_recovery': False}
        
        # Get user performance to determine recovery period
        performance = self._get_user_performance(user_id)
        
        # Dynamic recovery based on recent performance
        base_recovery = 60  # seconds
        if performance.get('recent_losses', 0) >= 3:
            recovery_time = base_recovery * 2  # Double recovery after streak
        elif performance.get('win_rate', 0.5) < 0.3:
            recovery_time = base_recovery * 1.5
        else:
            recovery_time = base_recovery
        
        time_since_last = (datetime.now() - last_shot).total_seconds()
        if time_since_last < recovery_time:
            return {
                'in_recovery': True,
                'time_remaining': int(recovery_time - time_since_last),
                'recovery_type': 'tactical_cooldown',
                'mini_game_available': True
            }
        
        return {'in_recovery': False}
    
    def _handle_recovery_period(self, user_id: int, recovery_info: Dict) -> TradeExecutionResult:
        """Handle recovery period with mini-games and tactical feedback"""
        time_remaining = recovery_info['time_remaining']
        
        # Check if user has active mini-game
        if user_id in self.recovery_games:
            game = self.recovery_games[user_id]
            return TradeExecutionResult(
                success=False,
                message=f"🎮 **TACTICAL RECOVERY MODE**\n\n"
                       f"⏱️ Recovery Time: {time_remaining}s\n\n"
                       f"**Active Mini-Game:** {game['name']}\n"
                       f"Progress: {game['progress']}/100\n\n"
                       f"Complete the mission to reduce recovery time!\n"
                       f"Use `/recovery complete` to submit your answer.",
                error_code="TACTICAL_RECOVERY"
            )
        
        # Generate new mini-game
        mini_game = self._generate_recovery_mini_game(user_id)
        self.recovery_games[user_id] = mini_game
        
        return TradeExecutionResult(
            success=False,
            message=f"🎯 **TACTICAL RECOVERY INITIATED**\n\n"
                   f"Your squad needs {time_remaining}s to regroup.\n\n"
                   f"**OPTIONAL MISSION:** {mini_game['name']}\n"
                   f"{mini_game['description']}\n\n"
                   f"💡 Complete this mission to reduce recovery by 50%!\n\n"
                   f"_{mini_game['hint']}_",
            error_code="TACTICAL_RECOVERY"
        )
    
    def _generate_recovery_mini_game(self, user_id: int) -> Dict:
        """Generate educational mini-game disguised as tactical mission"""
        games = [
            {
                'name': 'Market Recon',
                'description': 'Identify the highest volatility pair from: GBPJPY, EURUSD, USDCAD',
                'answer': 'GBPJPY',
                'hint': 'Check pip values - JPY pairs move differently',
                'educational_value': 'volatility_awareness'
            },
            {
                'name': 'Risk Assessment',
                'description': 'Calculate: 2% risk on $10,000 account = ? dollars',
                'answer': '200',
                'hint': 'Basic percentage calculation',
                'educational_value': 'risk_management'
            },
            {
                'name': 'Session Intel',
                'description': 'Which trading session overlaps London and New York?',
                'answer': '13:00-17:00',
                'hint': 'Think about time zones',
                'educational_value': 'market_sessions'
            }
        ]
        
        game = random.choice(games)
        game['progress'] = 0
        game['user_id'] = user_id
        game['start_time'] = datetime.now()
        
        return game
    
    def _provide_squad_support(self, trade_request: TradeRequest, mission_briefing: Dict) -> TradeExecutionResult:
        """Provide educational intervention as squad support"""
        support_type = mission_briefing.get('support_type', 'general')
        
        messages = {
            'risk_management': (
                "🛡️ **SQUAD SUPPORT ACTIVATED**\n\n"
                "📡 Intel suggests high risk on this operation.\n"
                f"Current exposure would exceed tactical limits.\n\n"
                "**Recommended Actions:**\n"
                "• Reduce position size by 50%\n"
                "• Wait for higher TCS confirmation\n"
                "• Close existing positions first\n\n"
                "_Your squad has your back, soldier._"
            ),
            'low_confidence': (
                "🎯 **TACTICAL ADVISORY**\n\n"
                f"TCS Score: {trade_request.tcs_score} - Below optimal range\n\n"
                "**Squad Analysis:**\n"
                "• Low probability of mission success\n"
                "• Consider waiting for better setup\n"
                "• Review THE PATTERN for guidance\n\n"
                "💡 *Higher TCS = Higher success rate*"
            ),
            'cooldown_needed': (
                "⚡ **RAPID FIRE DETECTED**\n\n"
                "Your firing rate exceeds tactical parameters.\n"
                "Accuracy decreases with fatigue.\n\n"
                "**Squad Recommendation:**\n"
                "• Take tactical pause (2-5 min)\n"
                "• Review recent trades\n"
                "• Reset mental state\n\n"
                "_Patience is a tactical advantage._"
            )
        }
        
        message = messages.get(support_type, mission_briefing.get('message', 'Squad support active'))
        
        return TradeExecutionResult(
            success=False,
            message=message,
            error_code="SQUAD_SUPPORT"
        )
    
    def _get_user_performance(self, user_id: int) -> Dict:
        """Get user performance metrics for adaptive difficulty"""
        if user_id not in self.user_performance:
            self.user_performance[user_id] = {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.5,
                'recent_trades': [],
                'recent_losses': 0,
                'avg_tcs': 75,
                'education_level': 1,  # 1-5 scale
                'achievements': []
            }
        return self.user_performance[user_id]
    
    def _update_performance_metrics(self, user_id: int, success: bool, trade_request: TradeRequest):
        """Update user performance for adaptive difficulty"""
        perf = self._get_user_performance(user_id)
        
        perf['total_trades'] += 1
        if success:
            perf['wins'] += 1
            perf['recent_losses'] = 0
        else:
            perf['losses'] += 1
            perf['recent_losses'] += 1
        
        perf['win_rate'] = perf['wins'] / max(perf['total_trades'], 1)
        
        # Track recent trades
        perf['recent_trades'].append({
            'time': datetime.now(),
            'success': success,
            'tcs': trade_request.tcs_score,
            'symbol': trade_request.symbol
        })
        
        # Keep only last 10 trades
        if len(perf['recent_trades']) > 10:
            perf['recent_trades'] = perf['recent_trades'][-10:]
        
        # Update average TCS
        recent_tcs = [t['tcs'] for t in perf['recent_trades']]
        perf['avg_tcs'] = sum(recent_tcs) / len(recent_tcs) if recent_tcs else 75
        
        # Adjust education level based on performance
        if perf['win_rate'] > 0.7 and perf['avg_tcs'] > 85:
            perf['education_level'] = min(5, perf['education_level'] + 1)
        elif perf['win_rate'] < 0.3:
            perf['education_level'] = max(1, perf['education_level'] - 1)
    
    def _check_achievements(self, user_id: int) -> str:
        """Check for unlocked achievements (gamified education milestones)"""
        perf = self._get_user_performance(user_id)
        new_achievements = []
        
        achievement_checks = [
            ('first_blood', 'First Successful Trade', lambda p: p['wins'] == 1),
            ('sharpshooter', 'Sharpshooter: 5 wins in a row', lambda p: self._check_win_streak(p, 5)),
            ('high_roller', 'High Roller: Average TCS > 85', lambda p: p['avg_tcs'] > 85),
            ('discipline', 'Discipline: No losses for 24h', lambda p: self._check_no_recent_losses(p)),
            ('master_trader', 'Master Trader: 70% win rate', lambda p: p['win_rate'] >= 0.7 and p['total_trades'] >= 20)
        ]
        
        for achievement_id, name, check_func in achievement_checks:
            if achievement_id not in perf['achievements'] and check_func(perf):
                perf['achievements'].append(achievement_id)
                new_achievements.append(f"🎖️ {name}")
        
        return "\n".join(new_achievements) if new_achievements else ""
    
    def _check_win_streak(self, performance: Dict, streak_length: int) -> bool:
        """Check if user has win streak"""
        if len(performance['recent_trades']) < streak_length:
            return False
        
        last_n = performance['recent_trades'][-streak_length:]
        return all(t['success'] for t in last_n)
    
    def _check_no_recent_losses(self, performance: Dict) -> bool:
        """Check if no losses in last 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [t for t in performance['recent_trades'] if t['time'] > cutoff]
        return len(recent) > 0 and all(t['success'] for t in recent)
    
    def complete_recovery_game(self, user_id: int, answer: str) -> Dict[str, Any]:
        """Complete recovery mini-game and check answer"""
        if user_id not in self.recovery_games:
            return {
                'success': False,
                'message': "❌ No active recovery mission found"
            }
        
        game = self.recovery_games[user_id]
        correct = answer.lower().strip() == game['answer'].lower().strip()
        
        if correct:
            # Reduce recovery time by 50%
            if user_id in self.last_shot_time:
                reduction = timedelta(seconds=30)  # 50% of 60s base
                self.last_shot_time[user_id] = self.last_shot_time[user_id] - reduction
            
            # Award XP or other rewards
            del self.recovery_games[user_id]
            
            return {
                'success': True,
                'message': f"✅ **MISSION COMPLETE!**\n\n"
                          f"Excellent work, soldier! Recovery time reduced.\n"
                          f"Educational value: {game['educational_value'].replace('_', ' ').title()}\n\n"
                          f"You may now proceed with your next trade."
            }
        else:
            # Give hint and let them try again
            game['progress'] += 25
            
            if game['progress'] >= 100:
                # Failed too many times, give answer
                del self.recovery_games[user_id]
                return {
                    'success': False,
                    'message': f"⚠️ **Mission Failed**\n\n"
                              f"The correct answer was: {game['answer']}\n"
                              f"Study this concept: {game['educational_value'].replace('_', ' ').title()}\n\n"
                              f"Recovery continues normally."
                }
            
            return {
                'success': False,
                'message': f"❌ Incorrect. Progress: {game['progress']}/100\n\n"
                          f"💡 Hint: {game['hint']}\n\n"
                          f"Try again with `/recovery complete YOUR_ANSWER`"
            }
    
    def process_low_tcs_warning_response(self, user_id: int, warning_id: str, action: str) -> Dict[str, Any]:
        """Process user's response to low TCS warning"""
        # Check if warning exists
        if warning_id not in self.pending_low_tcs_trades:
            return {
                'success': False,
                'message': "❌ Warning not found or expired. Please submit a new trade."
            }
        
        # Get the pending trade data
        pending_data = self.pending_low_tcs_trades[warning_id]
        trade_request = pending_data['trade_request']
        warning_dialog = pending_data['warning_dialog']
        
        # Check if warning has expired (5 minute timeout)
        if (datetime.now() - pending_data['timestamp']).total_seconds() > 300:
            del self.pending_low_tcs_trades[warning_id]
            return {
                'success': False,
                'message': "⏰ Warning expired. Please submit a new trade."
            }
        
        # Import bit warnings processor
        from .bit_warnings import process_warning_response
        
        # Process the response
        response = process_warning_response(
            str(user_id), 
            trade_request.tcs_score, 
            action
        )
        
        # Clean up the pending trade
        del self.pending_low_tcs_trades[warning_id]
        
        # Check if trade should proceed
        if response['proceed']:
            # Apply any cooldown if needed
            if response.get('enforce_cooldown'):
                self.last_shot_time[user_id] = datetime.now()
            
            # Re-execute the trade without the warning check
            # Temporarily increase TCS to bypass the warning (already confirmed)
            original_tcs = trade_request.tcs_score
            trade_request.tcs_score = 76  # Set to minimum to bypass warning
            
            # Execute the trade
            result = self.execute_trade(trade_request)
            
            # Restore original TCS in the result message
            if result.message:
                result.message = result.message.replace("TCS: 76", f"TCS: {original_tcs}")
            
            # Add Bit's reaction to the result
            if result.success:
                result.message += f"\n\n{response['bit_reaction']}"
            
            # Add wisdom score update
            wisdom_score = response['wisdom_score']
            result.message += f"\n\n📊 **Wisdom Score**: {wisdom_score['score']}% ({wisdom_score['rating']})"
            
            return {
                'success': result.success,
                'message': result.message,
                'execution_result': result
            }
        else:
            # Trade cancelled
            message = f"✅ **Trade Cancelled**\n\n{response['bit_reaction']}\n\n"
            
            # Add wisdom score
            wisdom_score = response['wisdom_score']
            message += f"📊 **Wisdom Score**: {wisdom_score['score']}% ({wisdom_score['rating']})\n"
            message += f"Warnings Heeded: {wisdom_score['warnings_heeded']}/{wisdom_score['total_warnings']}\n\n"
            message += "💡 _Patience is the path to consistent profitability._"
            
            return {
                'success': True,
                'message': message,
                'trade_cancelled': True
            }
    
    def get_user_wisdom_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's wisdom statistics"""
        from .bit_warnings import BitWarningSystem
        
        warning_system = BitWarningSystem()
        wisdom_data = warning_system.get_user_wisdom_score(str(user_id))
        
        # Format statistics message
        message = f"🧘 **Your Wisdom Statistics**\n\n"
        message += f"📊 **Wisdom Score**: {wisdom_data['score']}%\n"
        message += f"🏆 **Rating**: {wisdom_data['rating']}\n"
        message += f"⚠️ **Total Warnings**: {wisdom_data['total_warnings']}\n"
        message += f"✅ **Warnings Heeded**: {wisdom_data['warnings_heeded']}\n\n"
        
        # Add motivational message based on score
        if wisdom_data['score'] >= 80:
            message += "✨ _Bit is proud of your discipline. The Force is strong with you._"
        elif wisdom_data['score'] >= 60:
            message += "💪 _Good progress, young padawan. Continue on this path._"
        elif wisdom_data['score'] >= 40:
            message += "⚡ _Room for improvement. Listen to Bit's wisdom more often._"
        else:
            message += "🚨 _Dangerous path you walk. Heed Bit's warnings, you must!_"
        
        return {
            'success': True,
            'message': message,
            'wisdom_data': wisdom_data
        }


class TacticalEducationSystem:
    """Educational system disguised as tactical game mechanics"""
    
    def __init__(self):
        self.education_modules = {
            'risk_management': {
                'lessons': [
                    "Position sizing is ammunition management",
                    "Stop losses are tactical retreats",
                    "Portfolio heat is squad stamina"
                ],
                'mini_games': [
                    "Calculate optimal position size",
                    "Identify overexposure scenarios",
                    "Risk/reward ratio puzzles"
                ]
            },
            'market_dynamics': {
                'lessons': [
                    "Volatility is the battlefield terrain",
                    "Sessions are combat zones",
                    "Correlations are squad formations"
                ],
                'mini_games': [
                    "Identify active sessions",
                    "Spot correlated pairs",
                    "Volatility pattern recognition"
                ]
            },
            'psychology': {
                'lessons': [
                    "Fear is the mind-killer",
                    "Greed clouds judgment",
                    "Discipline wins wars"
                ],
                'mini_games': [
                    "Emotional state check-ins",
                    "Bias identification",
                    "Decision journaling"
                ]
            }
        }
    
    def generate_mission_briefing(self, trade_request: TradeRequest, user_profile: Dict, performance: Dict) -> Dict:
        """Generate pre-trade briefing with embedded education"""
        briefing = {
            'requires_support': False,
            'support_type': None,
            'intel': []
        }
        
        # Check various educational triggers
        if performance.get('recent_losses', 0) >= 3:
            briefing['requires_support'] = True
            briefing['support_type'] = 'cooldown_needed'
            return briefing
        
        if trade_request.tcs_score < 75 and performance.get('education_level', 1) < 3:
            briefing['requires_support'] = True
            briefing['support_type'] = 'low_confidence'
            return briefing
        
        if user_profile.get('total_exposure_percent', 0) > 5:
            briefing['requires_support'] = True
            briefing['support_type'] = 'risk_management'
            return briefing
        
        # Generate tactical intel (educational tips)
        briefing['intel'] = self._generate_tactical_intel(trade_request, performance)
        return briefing
    
    def _generate_tactical_intel(self, trade_request: TradeRequest, performance: Dict) -> List[str]:
        """Generate tactical tips based on context"""
        intel = []
        
        # Session-based intel
        current_hour = datetime.now().hour
        if 8 <= current_hour <= 9:
            intel.append("🌍 London session opening - expect volatility")
        elif 13 <= current_hour <= 14:
            intel.append("🗽 NY session opening - major moves possible")
        
        # Pair-specific intel
        if 'JPY' in trade_request.symbol:
            intel.append("🇯🇵 JPY pairs: Remember pip value difference")
        
        # Performance-based intel
        if performance.get('avg_tcs', 75) < 80:
            intel.append("📊 Consider waiting for TCS > 80 setups")
        
        return intel
    
    def generate_tactical_debrief(self, trade_request: TradeRequest, result: TradeExecutionResult, performance: Dict) -> str:
        """Generate post-trade debrief with stealth education"""
        if not result.success:
            return ""
        
        debrief_parts = []
        
        # Analyze the trade setup
        if trade_request.tcs_score >= 85:
            debrief_parts.append("📍 **Tactical Analysis:** High-confidence entry executed perfectly")
        elif trade_request.tcs_score >= 75:
            debrief_parts.append("📍 **Tactical Analysis:** Standard engagement, textbook execution")
        else:
            debrief_parts.append("📍 **Tactical Analysis:** Aggressive entry - monitor closely")
        
        # Add performance insight
        if performance['win_rate'] > 0.6:
            debrief_parts.append("🎯 Current win rate maintaining tactical advantage")
        
        # Random educational tip
        tips = [
            "💡 **Squad Tip:** Exit winners at 2R to maintain positive expectancy",
            "💡 **Squad Tip:** Multiple positions in correlated pairs increase risk",
            "💡 **Squad Tip:** Best setups often come after patience",
            "💡 **Squad Tip:** Your stop loss is your friend, not your enemy"
        ]
        
        if random.random() < 0.3:  # 30% chance to show tip
            debrief_parts.append(random.choice(tips))
        
        return "\n".join(debrief_parts) if debrief_parts else ""
    
    def calculate_difficulty_adjustment(self, user_id: int, performance: Dict) -> Dict:
        """Dynamically adjust difficulty based on performance"""
        base_modifier = 1.0
        
        # Make it easier if struggling
        if performance.get('recent_losses', 0) >= 2:
            base_modifier = 0.9  # Reduce TCS requirements by 10%
        elif performance.get('win_rate', 0.5) < 0.4:
            base_modifier = 0.95
        
        # Make it harder if doing too well (push to learn)
        elif performance.get('win_rate', 0.5) > 0.8:
            base_modifier = 1.1  # Increase requirements by 10%
        
        return {
            'modifier': base_modifier,
            'reason': 'performance_based',
            'applied_silently': True
        }
    
    def _get_user_xp(self, user_id: int) -> int:
        """Get user's current XP - would come from database"""
        # In production, this would fetch from database
        # For now, return a default value
        return 1000  # Default XP for testing
    
    def _get_account_info(self, user_id: int) -> 'AccountInfo':
        """Get account information - would come from MT5"""
        from .risk_management import AccountInfo
        
        # In production, this would fetch from MT5
        # For now, return test data
        return AccountInfo(
            balance=10000.0,  # $10,000 test balance
            equity=10000.0,
            margin=0.0,
            free_margin=10000.0,
            currency="USD",
            leverage=100,
            starting_balance=10000.0
        )
    
    def _get_daily_pnl(self, user_id: int) -> float:
        """Get user's daily P&L - would come from database"""
        # In production, this would calculate from today's closed trades
        # For now, return 0 (no loss)
        return 0.0
