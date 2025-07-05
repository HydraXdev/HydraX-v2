"""
Enhanced Fire Router with Risk Management and Trade Management
Integrates all advanced features for complete trading lifecycle
"""

import os
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime

from .fire_router import FireRouter, TradeRequest, TradeExecutionResult
from .risk_management import (
    RiskCalculator, RiskProfile, AccountInfo, 
    RiskMode, TradeManagementFeature, FEATURE_DESCRIPTIONS
)
from .trade_manager import TradeManager, ActiveTrade
from .mt5_bridge_integration import MT5BridgeIntegration

logger = logging.getLogger(__name__)

class EnhancedFireRouter(FireRouter):
    """
    Enhanced fire router with full risk and trade management
    """
    
    def __init__(self, bridge_url: str = None):
        super().__init__(bridge_url)
        
        # Initialize components
        self.risk_calculator = RiskCalculator()
        self.trade_manager = TradeManager()
        
        # User profiles cache (would be from database)
        self.user_profiles: Dict[int, RiskProfile] = {}
        
        # Start trade monitoring
        self.monitor_task = None
        if asyncio.get_event_loop().is_running():
            self.monitor_task = asyncio.create_task(self.trade_manager.start_monitoring())
    
    def execute_trade(self, request: TradeRequest) -> TradeExecutionResult:
        """
        Enhanced trade execution with risk management
        """
        try:
            # Get user profile
            profile = self._get_user_profile(request.user_id)
            
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
                    direction=request.direction.value,
                    entry_price=result.execution_price or 0,
                    current_sl=request.stop_loss,
                    current_tp=request.take_profit,
                    original_sl=request.stop_loss,
                    volume=request.volume,
                    open_time=datetime.now(),
                    management_plans=plans,
                    user_id=request.user_id
                )
                
                # Add to manager
                self.trade_manager.add_trade(active_trade)
                
                # Add feature notifications to result
                feature_names = [FEATURE_DESCRIPTIONS[p.feature]['name'] for p in plans]
                if feature_names:
                    result.message += f"\n🎯 Active features: {', '.join(feature_names)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced execution error: {e}")
            return TradeExecutionResult(
                success=False,
                message=f"❌ System error: {str(e)}",
                error_code="SYSTEM_ERROR"
            )
    
    def _get_user_profile(self, user_id: int) -> RiskProfile:
        """Get or create user risk profile"""
        if user_id not in self.user_profiles:
            # In production, load from database
            # For now, create default with some XP
            self.user_profiles[user_id] = RiskProfile(
                user_id=user_id,
                current_xp=1000,  # Default 1000 XP
                tier_level=self.user_tiers.get(user_id, "NIBBLER").value
            )
        
        return self.user_profiles[user_id]
    
    def _get_account_info(self) -> AccountInfo:
        """Get current account info from MT5"""
        # In production, get from MT5 bridge
        # For now, return dummy data
        return AccountInfo(
            balance=10000.0,
            equity=10500.0,
            margin=500.0,
            free_margin=10000.0,
            currency="USD",
            leverage=100
        )
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
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
        profile = self._get_user_profile(user_id)
        old_xp = profile.current_xp
        profile.current_xp += xp_gained
        
        # Check for new unlocks
        old_features = set(profile.get_unlocked_features())
        new_features = set(profile.get_unlocked_features())
        
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
    
    def get_trade_status(self, trade_id: str) -> Optional[Dict]:
        """Get enhanced trade status with management info"""
        status = self.trade_manager.get_trade_status(trade_id)
        
        if status:
            # Add risk info
            trade = self.trade_manager.active_trades.get(trade_id)
            if trade:
                profile = self._get_user_profile(trade.user_id)
                status['risk_profile'] = {
                    'max_risk_percent': profile.max_risk_percent,
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
async def execute_leroy_jenkins_mode(router: EnhancedFireRouter, user_id: int, symbol: str):
    """
    LEEEEEROYYY JENKINS!
    Ultra-aggressive mode for experienced traders
    """
    profile = router._get_user_profile(user_id)
    
    if profile.current_xp < 20000:
        return "❌ LEROY JENKINS mode requires 20,000 XP!"
    
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
    
    result = router.execute_trade(request)
    
    if result.success:
        return f"🔥 LEEEEEROYYY JENKINS! 🔥\n{symbol} YOLO ACTIVATED!\nRisk it for the biscuit!"
    else:
        return f"❌ Even Leroy couldn't make it work: {result.message}"