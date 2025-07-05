"""
Enhanced Fire Router with Risk Management and Trade Management - SECURE VERSION
Integrates all advanced features for complete trading lifecycle
Enhanced with security features from security_utils.py
"""

import os
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
import secrets

from .fire_router import FireRouter, TradeRequest, TradeExecutionResult
from .risk_management_secure import (
    RiskCalculator, RiskProfile, AccountInfo, 
    RiskMode, TradeManagementFeature, FEATURE_DESCRIPTIONS
)
from .trade_manager_secure import TradeManager, ActiveTrade
from .mt5_bridge_integration import MT5BridgeIntegration
from .security_utils import (
    validate_symbol, validate_direction, validate_volume, validate_price,
    sanitize_log_output, generate_secure_token, RateLimiter,
    ValidationError, SecurityError
)

logger = logging.getLogger(__name__)

# Configuration from environment variables
MAX_DAILY_TRADES = int(os.environ.get('BITTEN_MAX_DAILY_TRADES', '50'))
MAX_CONCURRENT_TRADES = int(os.environ.get('BITTEN_MAX_CONCURRENT_TRADES', '10'))
BRIDGE_URL = os.environ.get('BITTEN_BRIDGE_URL', 'http://localhost:5050')

class EnhancedFireRouter(FireRouter):
    """
    Enhanced fire router with full risk and trade management - SECURE VERSION
    """
    
    def __init__(self, bridge_url: str = None, api_key: str = None):
        # Use environment variable if not provided
        bridge_url = bridge_url or BRIDGE_URL
        super().__init__(bridge_url)
        
        # Authentication
        self.api_key = api_key or os.environ.get('BITTEN_API_KEY')
        if not self.api_key:
            self.api_key = generate_secure_token()
            logger.warning(f"No API key provided, generated new key: {self.api_key[:8]}...")
        
        # Initialize components
        self.risk_calculator = RiskCalculator()
        self.trade_manager = TradeManager()
        
        # User profiles cache (would be from database)
        self.user_profiles: Dict[int, RiskProfile] = {}
        
        # Rate limiter
        self.rate_limiter = RateLimiter(max_requests=MAX_DAILY_TRADES, window_seconds=86400)  # Daily limit
        
        # Track active trades per user
        self.user_active_trades: Dict[int, List[str]] = {}
        
        # Start trade monitoring
        self.monitor_task = None
        if asyncio.get_event_loop().is_running():
            self.monitor_task = asyncio.create_task(self.trade_manager.start_monitoring())
    
    def _authenticate_request(self, api_key: str) -> bool:
        """Authenticate API request"""
        return secrets.compare_digest(api_key, self.api_key)
    
    def execute_trade(self, request: TradeRequest, api_key: Optional[str] = None) -> TradeExecutionResult:
        """
        Enhanced trade execution with risk management and security
        """
        try:
            # Authenticate if API key provided
            if api_key and not self._authenticate_request(api_key):
                return TradeExecutionResult(
                    success=False,
                    message="Authentication failed",
                    error_code="AUTH_FAILED"
                )
            
            # Validate request inputs
            try:
                request.symbol = validate_symbol(request.symbol)
                request.direction = validate_direction(request.direction)
                if request.volume > 0:
                    request.volume = float(validate_volume(request.volume))
                if request.stop_loss:
                    request.stop_loss = float(validate_price(request.stop_loss))
                if request.take_profit:
                    request.take_profit = float(validate_price(request.take_profit))
            except ValidationError as e:
                return TradeExecutionResult(
                    success=False,
                    message=str(e),
                    error_code="VALIDATION_ERROR"
                )
            
            # Rate limiting
            if not self.rate_limiter.check_rate_limit(str(request.user_id)):
                return TradeExecutionResult(
                    success=False,
                    message=f"Daily trade limit reached ({MAX_DAILY_TRADES} trades)",
                    error_code="RATE_LIMIT"
                )
            
            # Get user profile
            profile = self._get_user_profile(request.user_id)
            
            # Check concurrent trades limit
            user_trades = self.user_active_trades.get(request.user_id, [])
            if len(user_trades) >= MAX_CONCURRENT_TRADES:
                return TradeExecutionResult(
                    success=False,
                    message=f"Maximum concurrent trades reached ({MAX_CONCURRENT_TRADES})",
                    error_code="CONCURRENT_LIMIT"
                )
            
            # Get account info from MT5
            account = self._get_account_info()
            
            # Calculate position size based on risk
            if request.stop_loss:
                risk_calc = self.risk_calculator.calculate_position_size(
                    account=account,
                    profile=profile,
                    symbol=request.symbol,
                    entry_price=self._get_current_price(request.symbol),
                    stop_loss_price=request.stop_loss,
                    risk_mode=RiskMode.PERCENTAGE
                )
                
                # Override volume with calculated size
                original_volume = request.volume
                request.volume = risk_calc['lot_size']
                
                logger.info(f"Risk calculation for {request.symbol}: "
                          f"Original: {original_volume}, Calculated: {request.volume}, "
                          f"Risk: {risk_calc['risk_percent']:.2f}%")
            
            # Check daily drawdown limit
            if self._check_daily_drawdown(profile):
                return TradeExecutionResult(
                    success=False,
                    message="❌ Daily drawdown limit reached (-7%). Trading suspended.",
                    error_code="DAILY_LIMIT"
                )
            
            # Execute trade through parent class
            result = super().execute_trade(request)
            
            # If successful, add to trade manager
            if result.success and result.trade_id:
                # Track active trade
                if request.user_id not in self.user_active_trades:
                    self.user_active_trades[request.user_id] = []
                self.user_active_trades[request.user_id].append(result.trade_id)
                
                # Create management plans based on XP
                plans = self.risk_calculator.create_trade_management_plan(
                    profile=profile,
                    entry_price=result.execution_price or self._get_current_price(request.symbol),
                    stop_loss_price=request.stop_loss,
                    take_profit_price=request.take_profit,
                    symbol=request.symbol
                )
                
                # Create active trade
                active_trade = ActiveTrade(
                    trade_id=result.trade_id,
                    ticket=result.ticket or 0,
                    symbol=request.symbol,
                    direction=request.direction.upper(),
                    entry_price=Decimal(str(result.execution_price or 0)),
                    current_sl=Decimal(str(request.stop_loss)),
                    current_tp=Decimal(str(request.take_profit)),
                    original_sl=Decimal(str(request.stop_loss)),
                    volume=Decimal(str(request.volume)),
                    open_time=datetime.now(),
                    management_plans=plans,
                    user_id=request.user_id
                )
                
                # Add to manager
                self.trade_manager.add_trade(active_trade)
                
                # Add feature notifications to result
                feature_names = [FEATURE_DESCRIPTIONS[p.feature]['name'] for p in plans if p.feature in FEATURE_DESCRIPTIONS]
                if feature_names:
                    result.message += f"\n🎯 Active features: {', '.join(feature_names)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced execution error: {sanitize_log_output(str(e))}")
            return TradeExecutionResult(
                success=False,
                message="System error",
                error_code="SYSTEM_ERROR"
            )
    
    def _get_user_profile(self, user_id: int) -> RiskProfile:
        """Get or create user risk profile"""
        if user_id not in self.user_profiles:
            # In production, load from database
            # For now, create default with some XP
            tier = self.user_tiers.get(user_id, "NIBBLER")
            if hasattr(tier, 'value'):
                tier = tier.value
            
            self.user_profiles[user_id] = RiskProfile(
                user_id=user_id,
                current_xp=1000,  # Default 1000 XP
                tier_level=tier
            )
        
        return self.user_profiles[user_id]
    
    def _get_account_info(self) -> AccountInfo:
        """Get current account info from MT5"""
        # In production, get from MT5 bridge
        # For now, return dummy data with validation
        return AccountInfo(
            balance=Decimal('10000.0'),
            equity=Decimal('10500.0'),
            margin=Decimal('500.0'),
            free_margin=Decimal('10000.0'),
            currency="USD",
            leverage=100
        )
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        # Validate symbol
        symbol = validate_symbol(symbol)
        
        # In production, get from price feed
        # For now, return dummy prices
        prices = {
            'XAUUSD': 1950.00,
            'EURUSD': 1.0800,
            'GBPUSD': 1.2500,
            'USDJPY': 145.00,
            'USDCAD': 1.3500,
            'GBPJPY': 180.00
        }
        return prices.get(symbol, 1.0000)
    
    def _check_daily_drawdown(self, profile: RiskProfile) -> bool:
        """Check if daily drawdown limit is reached"""
        # In production, calculate from trade history
        # For now, always allow
        return False
    
    def get_unlocked_features(self, user_id: int) -> List[Dict]:
        """Get user's unlocked trade management features"""
        profile = self._get_user_profile(user_id)
        unlocked = profile.get_unlocked_features()
        
        features = []
        for feature in unlocked:
            if feature in FEATURE_DESCRIPTIONS:
                desc = FEATURE_DESCRIPTIONS[feature]
                features.append({
                    'feature': feature.value,
                    'name': desc['name'],
                    'description': desc['description'],
                    'icon': desc['icon'],
                    'xp_required': desc['xp_required']
                })
        
        # Add next unlock
        all_features = list(TradeManagementFeature)
        for feature in all_features:
            if feature not in unlocked and feature in FEATURE_DESCRIPTIONS:
                desc = FEATURE_DESCRIPTIONS[feature]
                if desc['xp_required'] > profile.current_xp:
                    features.append({
                        'feature': feature.value,
                        'name': desc['name'],
                        'description': desc['description'],
                        'icon': desc['icon'],
                        'xp_required': desc['xp_required'],
                        'locked': True,
                        'xp_needed': desc['xp_required'] - profile.current_xp
                    })
                    break
        
        return features
    
    def update_user_xp(self, user_id: int, xp_gained: int):
        """Update user XP and check for unlocks"""
        if xp_gained < 0 or xp_gained > 10000:
            raise ValidationError(f"Invalid XP gain: {xp_gained}")
        
        profile = self._get_user_profile(user_id)
        old_xp = profile.current_xp
        profile.current_xp += xp_gained
        
        # Cap XP at reasonable maximum
        if profile.current_xp > 1000000:
            profile.current_xp = 1000000
        
        # Check for new unlocks
        old_features = set(profile.get_unlocked_features())
        profile.current_xp = old_xp  # Reset to check
        new_features = set(profile.get_unlocked_features())
        profile.current_xp = old_xp + xp_gained  # Apply gain
        
        newly_unlocked = new_features - old_features
        
        notifications = []
        for feature in newly_unlocked:
            if feature in FEATURE_DESCRIPTIONS:
                desc = FEATURE_DESCRIPTIONS[feature]
                notifications.append({
                    'type': 'feature_unlock',
                    'message': f"🎊 UNLOCKED: {desc['name']} {desc['icon']}",
                    'description': desc['description'],
                    'feature': feature.value
                })
        
        return notifications
    
    def get_trade_status(self, trade_id: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """Get enhanced trade status with management info"""
        # Validate user owns the trade
        if user_id:
            user_trades = self.user_active_trades.get(user_id, [])
            if trade_id not in user_trades:
                logger.warning(f"User {user_id} attempted to access trade {trade_id} they don't own")
                return None
        
        status = self.trade_manager.get_trade_status(trade_id)
        
        if status:
            # Add risk info
            trade = None
            for active_trade in self.trade_manager.active_trades.values():
                if active_trade.trade_id == trade_id:
                    trade = active_trade
                    break
            
            if trade:
                profile = self._get_user_profile(trade.user_id)
                status['risk_profile'] = {
                    'max_risk_percent': float(profile.max_risk_percent),
                    'tier_level': profile.tier_level,
                    'current_xp': profile.current_xp
                }
                
                # Add feature status
                status['management_features'] = []
                for plan in trade.management_plans:
                    if plan.feature in FEATURE_DESCRIPTIONS:
                        desc = FEATURE_DESCRIPTIONS[plan.feature]
                        status['management_features'].append({
                            'name': desc['name'],
                            'icon': desc['icon'],
                            'active': True
                        })
        
        return status
    
    def close_trade(self, trade_id: str, user_id: int) -> Dict:
        """Close an active trade"""
        # Validate user owns the trade
        user_trades = self.user_active_trades.get(user_id, [])
        if trade_id not in user_trades:
            return {
                'success': False,
                'message': 'Trade not found or access denied',
                'error_code': 'NOT_FOUND'
            }
        
        # Remove from active trades
        self.user_active_trades[user_id].remove(trade_id)
        self.trade_manager.remove_trade(trade_id)
        
        # In production, would send close command to MT5
        return {
            'success': True,
            'message': f'Trade {trade_id} closed',
            'trade_id': trade_id
        }


# Example Telegram integration
def format_trade_result_with_features(result: TradeExecutionResult, features: List[Dict]) -> str:
    """Format trade result for Telegram with feature icons"""
    if not result.success:
        return result.message
    
    message = f"✅ Trade Executed!\n"
    message += f"ID: {result.trade_id}\n"
    
    if features:
        message += "\n🎯 Active Management:\n"
        for feature in features:
            if not feature.get('locked', False):
                message += f"{feature['icon']} {feature['name']}\n"
    
    return message


# Leroy Jenkins Special Mode
async def execute_leroy_jenkins_mode(router: EnhancedFireRouter, user_id: int, symbol: str, api_key: Optional[str] = None):
    """
    LEEEEEROYYY JENKINS!
    Ultra-aggressive mode for experienced traders
    """
    profile = router._get_user_profile(user_id)
    
    if profile.current_xp < 20000:
        return "❌ LEROY JENKINS mode requires 20,000 XP!"
    
    # Validate symbol
    try:
        symbol = validate_symbol(symbol)
    except ValidationError:
        return f"❌ Invalid symbol: {symbol}"
    
    # Get current price
    price = router._get_current_price(symbol)
    
    # Super tight SL, massive TP
    sl = price * 0.995 if symbol != 'XAUUSD' else price - 5  # 0.5% or 5 pips
    tp = price * 1.05 if symbol != 'XAUUSD' else price + 50  # 5% or 50 pips
    
    # Max risk allowed
    request = TradeRequest(
        user_id=user_id,
        symbol=symbol,
        direction="BUY",  # Always bullish in Leroy mode
        volume=0,  # Will be calculated
        stop_loss=sl,
        take_profit=tp,
        comment="LEEEEEROYYY JENKINS!",
        tcs_score=100,  # Override TCS
        fire_mode="LEROY_JENKINS"
    )
    
    result = router.execute_trade(request, api_key)
    
    if result.success:
        return f"🔥 LEEEEEROYYY JENKINS! 🔥\n{symbol} YOLO ACTIVATED!\nRisk it for the biscuit!"
    else:
        return f"❌ Even Leroy couldn't make it work: {result.message}"


# Singleton instance
_router_instance = None

def get_enhanced_router(bridge_url: Optional[str] = None, api_key: Optional[str] = None) -> EnhancedFireRouter:
    """Get or create the enhanced router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedFireRouter(bridge_url, api_key)
    return _router_instance