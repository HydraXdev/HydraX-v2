"""
🎯 Volatility Integration with BITTEN Core
Hooks volatility checks into fire modes and trading flow
"""

import asyncio
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import logging

from src.bitten_core.volatility_manager import (
    VolatilityManager, VolatilityLevel, VolatilityData,
    get_volatility_manager
)
from src.bitten_core.fire_modes import FireMode
from src.database.models import User, Trade

logger = logging.getLogger(__name__)


class VolatilityIntegration:
    """
    Integrates volatility management into BITTEN's trading flow
    No position reduction - only higher standards
    """
    
    def __init__(self):
        self.volatility_manager = get_volatility_manager()
        self._volatility_cache: Dict[str, Tuple[VolatilityLevel, datetime]] = {}
        self.cache_duration = 300  # 5 minutes
        self._pending_confirmations: Dict[int, Dict] = {}  # user_id -> trade details
        
    def get_cached_volatility(self, symbol: str) -> Optional[VolatilityLevel]:
        """Get cached volatility level if still valid"""
        if symbol in self._volatility_cache:
            level, timestamp = self._volatility_cache[symbol]
            if (datetime.utcnow() - timestamp).seconds < self.cache_duration:
                return level
        return None
    
    async def check_volatility_requirements(self, 
                                          symbol: str,
                                          tcs: float,
                                          tier: str,
                                          fire_mode: FireMode) -> Dict[str, Any]:
        """
        Check if trade meets volatility-adjusted requirements
        
        Returns:
            Dict with keys:
            - allowed: bool
            - level: VolatilityLevel
            - adjusted_tcs: int
            - requires_confirmation: bool
            - message: str
            - stop_multiplier: float
        """
        # Get volatility level (from cache or calculate)
        level = self.get_cached_volatility(symbol)
        if level is None:
            # In production, would fetch real market data
            # For now, simulate with mock data
            data = await self._fetch_volatility_data(symbol)
            level = self.volatility_manager.calculate_volatility_level(data)
            self._volatility_cache[symbol] = (level, datetime.utcnow())
        
        # Check if trade should be blocked
        should_block, reason = self.volatility_manager.should_block_trade(
            level, tcs, tier
        )
        
        # Get base TCS for tier
        base_tcs = {
            'NIBBLER': 72,
            'FANG': 85,
            'COMMANDER': 91,
            'APEX': 91
        }.get(tier, 72)
        
        adjusted_tcs = level.get_tcs_requirement(base_tcs)
        
        result = {
            'allowed': not should_block,
            'level': level,
            'adjusted_tcs': adjusted_tcs,
            'requires_confirmation': level.requires_confirmation(),
            'message': reason or f"Volatility {level.value}: TCS requirement {adjusted_tcs}%",
            'stop_multiplier': level.get_stop_multiplier()
        }
        
        # Add mission brief if not normal
        if level != VolatilityLevel.NORMAL:
            data = await self._fetch_volatility_data(symbol)
            result['mission_brief'] = self.volatility_manager.get_mission_brief(
                level, data, symbol, base_tcs
            )
        
        return result
    
    async def _fetch_volatility_data(self, symbol: str) -> VolatilityData:
        """
        Fetch volatility data for symbol
        In production, this would connect to market data provider
        """
        # Mock implementation - would use real data source
        import random
        
        # Simulate different market conditions
        market_condition = random.choice(['normal', 'elevated', 'high', 'extreme'])
        
        if market_condition == 'normal':
            return VolatilityData(
                atr_current=0.0010,
                atr_average=0.0010,
                atr_percentile=50.0,
                spread_current=1.0,
                spread_normal=1.0,
                recent_gaps=[],
                vix_level=15.0
            )
        elif market_condition == 'elevated':
            return VolatilityData(
                atr_current=0.0013,
                atr_average=0.0010,
                atr_percentile=65.0,
                spread_current=2.0,
                spread_normal=1.0,
                recent_gaps=[20.0],
                vix_level=22.0
            )
        elif market_condition == 'high':
            return VolatilityData(
                atr_current=0.0016,
                atr_average=0.0010,
                atr_percentile=80.0,
                spread_current=3.5,
                spread_normal=1.0,
                recent_gaps=[45.0, 30.0],
                vix_level=28.0,
                news_events=['FOMC Meeting', 'NFP Release']
            )
        else:  # extreme
            return VolatilityData(
                atr_current=0.0022,
                atr_average=0.0010,
                atr_percentile=95.0,
                spread_current=6.0,
                spread_normal=1.0,
                recent_gaps=[80.0, 65.0, 50.0],
                vix_level=35.0,
                news_events=['Emergency Fed Meeting', 'Banking Crisis']
            )
    
    def store_pending_confirmation(self, user_id: int, trade_details: Dict):
        """Store trade details pending volatility confirmation"""
        self._pending_confirmations[user_id] = {
            'details': trade_details,
            'timestamp': datetime.utcnow()
        }
    
    def get_pending_confirmation(self, user_id: int) -> Optional[Dict]:
        """Get pending trade awaiting confirmation"""
        if user_id in self._pending_confirmations:
            data = self._pending_confirmations[user_id]
            # Check if not expired (5 minute timeout)
            if (datetime.utcnow() - data['timestamp']).seconds < 300:
                return data['details']
            else:
                # Expired, remove it
                del self._pending_confirmations[user_id]
        return None
    
    def clear_pending_confirmation(self, user_id: int):
        """Clear pending confirmation after use"""
        if user_id in self._pending_confirmations:
            del self._pending_confirmations[user_id]
    
    async def process_volatility_confirmation(self, user_id: int, 
                                            response: str) -> Dict[str, Any]:
        """
        Process user's response to volatility confirmation
        
        Returns:
            Dict with keys:
            - confirmed: bool
            - message: str
            - trade_details: Dict (if confirmed)
        """
        pending = self.get_pending_confirmation(user_id)
        if not pending:
            return {
                'confirmed': False,
                'message': "No pending trade awaiting confirmation."
            }
        
        if response.upper() == 'CONFIRM':
            # User confirmed, proceed with trade
            self.clear_pending_confirmation(user_id)
            return {
                'confirmed': True,
                'message': "Trade confirmed. Executing with adjusted parameters.",
                'trade_details': pending
            }
        elif response.upper() == 'ABORT':
            # User aborted
            self.clear_pending_confirmation(user_id)
            return {
                'confirmed': False,
                'message': "Trade aborted. Standing down."
            }
        else:
            return {
                'confirmed': False,
                'message': 'Invalid response. Type "CONFIRM" or "ABORT".'
            }
    
    def adjust_stop_loss(self, base_stop_pips: float, 
                        symbol: str) -> Tuple[float, float]:
        """
        Adjust stop loss based on volatility
        Returns (adjusted_stop_pips, multiplier_used)
        """
        level = self.get_cached_volatility(symbol)
        if level is None:
            return base_stop_pips, 1.0
        
        multiplier = level.get_stop_multiplier()
        adjusted_stop = self.volatility_manager.calculate_adjusted_stop(
            base_stop_pips, level
        )
        
        return adjusted_stop, multiplier
    
    def get_volatility_status(self) -> Dict[str, Any]:
        """Get current volatility status for all cached symbols"""
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbols': {}
        }
        
        for symbol, (level, timestamp) in self._volatility_cache.items():
            age_seconds = (datetime.utcnow() - timestamp).seconds
            if age_seconds < self.cache_duration:
                status['symbols'][symbol] = {
                    'level': level.value,
                    'stop_multiplier': level.get_stop_multiplier(),
                    'age_seconds': age_seconds
                }
        
        return status
    
    async def volatility_briefing(self, symbols: List[str]) -> str:
        """Generate volatility briefing for multiple symbols"""
        briefing = "📊 MARKET VOLATILITY BRIEFING\n"
        briefing += "=" * 30 + "\n\n"
        
        any_elevated = False
        
        for symbol in symbols:
            data = await self._fetch_volatility_data(symbol)
            level = self.volatility_manager.calculate_volatility_level(data)
            
            if level != VolatilityLevel.NORMAL:
                any_elevated = True
                briefing += f"{symbol}: {level.value}\n"
                briefing += f"  • ATR: {data.atr_ratio:.1%} of normal\n"
                briefing += f"  • Spread: {data.spread_ratio:.1f}x normal\n"
                if data.news_events:
                    briefing += f"  • Events: {', '.join(data.news_events[:2])}\n"
                briefing += "\n"
        
        if not any_elevated:
            briefing += "All monitored symbols showing NORMAL volatility.\n"
            briefing += "Standard operating procedures apply.\n"
        else:
            briefing += "⚡ Elevated volatility detected!\n"
            briefing += "Higher TCS requirements and wider stops in effect.\n"
        
        return briefing


# Global instance
_volatility_integration: Optional[VolatilityIntegration] = None


def get_volatility_integration() -> VolatilityIntegration:
    """Get or create volatility integration instance"""
    global _volatility_integration
    if _volatility_integration is None:
        _volatility_integration = VolatilityIntegration()
    return _volatility_integration


# Convenience functions
async def check_trade_volatility(symbol: str, tcs: float, tier: str, 
                               fire_mode: FireMode) -> Dict[str, Any]:
    """Quick check for trade volatility requirements"""
    integration = get_volatility_integration()
    return await integration.check_volatility_requirements(
        symbol, tcs, tier, fire_mode
    )


async def get_market_briefing(symbols: List[str]) -> str:
    """Get market volatility briefing"""
    integration = get_volatility_integration()
    return await integration.volatility_briefing(symbols)