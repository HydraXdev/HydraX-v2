"""
🎯 BITTEN Volatility Manager
Detects market volatility and enforces higher standards during rough conditions
No position size reduction - full send or don't send
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class VolatilityLevel(Enum):
    """Market volatility conditions"""
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    
    def get_tcs_requirement(self, base_tcs: int) -> int:
        """Get adjusted TCS requirement for volatility level"""
        adjustments = {
            VolatilityLevel.NORMAL: 0,
            VolatilityLevel.ELEVATED: 3,    # 72% -> 75%
            VolatilityLevel.HIGH: 8,        # 72% -> 80%
            VolatilityLevel.EXTREME: 13     # 72% -> 85%
        }
        return base_tcs + adjustments[self]
    
    def get_stop_multiplier(self) -> float:
        """Get stop loss width multiplier"""
        multipliers = {
            VolatilityLevel.NORMAL: 1.0,
            VolatilityLevel.ELEVATED: 1.2,
            VolatilityLevel.HIGH: 1.5,
            VolatilityLevel.EXTREME: 2.0
        }
        return multipliers[self]
    
    def requires_confirmation(self) -> bool:
        """Check if user confirmation required"""
        return self in [VolatilityLevel.HIGH, VolatilityLevel.EXTREME]

@dataclass
class VolatilityData:
    """Current volatility metrics"""
    atr_current: float
    atr_average: float
    atr_percentile: float
    spread_current: float
    spread_normal: float
    recent_gaps: List[float]
    vix_level: Optional[float] = None
    news_events: List[str] = None
    
    @property
    def atr_ratio(self) -> float:
        """Current ATR as ratio of average"""
        return self.atr_current / self.atr_average if self.atr_average > 0 else 1.0
    
    @property
    def spread_ratio(self) -> float:
        """Current spread as ratio of normal"""
        return self.spread_current / self.spread_normal if self.spread_normal > 0 else 1.0

class VolatilityManager:
    """
    Manages volatility detection and trading adjustments
    Philosophy: No wimpy position reductions - adapt or don't trade
    """
    
    def __init__(self):
        # ATR thresholds (as percentage above normal)
        self.atr_thresholds = {
            VolatilityLevel.ELEVATED: 1.25,  # 25% above normal
            VolatilityLevel.HIGH: 1.50,      # 50% above normal
            VolatilityLevel.EXTREME: 2.00    # 100% above normal
        }
        
        # Spread thresholds (as ratio of normal)
        self.spread_thresholds = {
            VolatilityLevel.ELEVATED: 2.0,   # 2x normal spread
            VolatilityLevel.HIGH: 3.0,       # 3x normal spread
            VolatilityLevel.EXTREME: 5.0     # 5x normal spread
        }
        
        # VIX thresholds (if available)
        self.vix_thresholds = {
            VolatilityLevel.ELEVATED: 20,
            VolatilityLevel.HIGH: 25,
            VolatilityLevel.EXTREME: 30
        }
        
        # News events that trigger automatic HIGH volatility
        self.high_impact_events = [
            'NFP', 'FOMC', 'ECB', 'BOE', 'CPI', 'GDP',
            'Employment', 'Interest Rate', 'Inflation'
        ]
        
    def calculate_volatility_level(self, data: VolatilityData) -> VolatilityLevel:
        """
        Determine current volatility level
        Multiple factors considered, highest level wins
        """
        level = VolatilityLevel.NORMAL
        
        # Check ATR ratio
        for vol_level, threshold in self.atr_thresholds.items():
            if data.atr_ratio >= threshold:
                level = vol_level
            else:
                break
        
        # Check spread ratio (can upgrade level)
        for vol_level, threshold in self.spread_thresholds.items():
            if data.spread_ratio >= threshold and vol_level.value > level.value:
                level = vol_level
        
        # Check VIX if available
        if data.vix_level:
            for vol_level, threshold in self.vix_thresholds.items():
                if data.vix_level >= threshold and vol_level.value > level.value:
                    level = vol_level
        
        # Check for high-impact news
        if data.news_events:
            for event in data.news_events:
                if any(keyword in event.upper() for keyword in self.high_impact_events):
                    if level.value < VolatilityLevel.HIGH.value:
                        level = VolatilityLevel.HIGH
                        logger.info(f"High impact news detected: {event}")
        
        # Check for recent gaps (weekend or news gaps)
        if data.recent_gaps:
            max_gap = max(abs(gap) for gap in data.recent_gaps)
            if max_gap > 50:  # 50+ pip gap
                if level.value < VolatilityLevel.HIGH.value:
                    level = VolatilityLevel.HIGH
                    logger.info(f"Large gap detected: {max_gap} pips")
        
        return level
    
    def get_mission_brief(self, level: VolatilityLevel, data: VolatilityData,
                         symbol: str, base_tcs: int) -> str:
        """Generate volatility warning for mission brief"""
        if level == VolatilityLevel.NORMAL:
            return ""  # No warning needed
        
        brief = f"""
⚠️ VOLATILITY ALERT - {level.value} ⚠️

Market Conditions: {self._get_condition_description(level)}
Symbol: {symbol}
ATR: {data.atr_ratio:.1%} of normal
Spread: {data.spread_current:.1f} pips ({data.spread_ratio:.1f}x normal)
"""
        
        if data.vix_level:
            brief += f"VIX: {data.vix_level:.1f}\n"
        
        if data.news_events:
            brief += f"Active Events: {', '.join(data.news_events[:3])}\n"
        
        brief += f"""
ADJUSTMENTS:
• Required TCS: {level.get_tcs_requirement(base_tcs)}% (up from {base_tcs}%)
• Stop Width: {level.get_stop_multiplier():.1f}x normal
• Confirmation: {'REQUIRED' if level.requires_confirmation() else 'Not required'}

⚡ Market is rough. Higher standards apply.
"""
        
        return brief.strip()
    
    def _get_condition_description(self, level: VolatilityLevel) -> str:
        """Get description of market conditions"""
        descriptions = {
            VolatilityLevel.NORMAL: "Calm seas, normal operations",
            VolatilityLevel.ELEVATED: "Choppy waters, stay alert",
            VolatilityLevel.HIGH: "Storm conditions, extreme caution",
            VolatilityLevel.EXTREME: "Hurricane - only the brave survive"
        }
        return descriptions[level]
    
    def get_confirmation_message(self, level: VolatilityLevel, 
                               symbol: str, direction: str) -> str:
        """Generate confirmation message for high volatility trades"""
        if not level.requires_confirmation():
            return None
        
        return f"""
🚨 {level.value} VOLATILITY CONFIRMATION 🚨

You're about to enter {direction} on {symbol} in {level.value.lower()} volatility.

ACKNOWLEDGED RISKS:
✓ Wider stops will be used (same $ risk)
✓ Price may whipsaw violently
✓ Spreads are elevated
✓ Gaps are possible

This is not a normal market. Are you ready for combat?

Type "CONFIRM" to proceed with full position.
Type "ABORT" to stand down.
"""
    
    def calculate_adjusted_stop(self, base_stop_pips: float, 
                              level: VolatilityLevel) -> float:
        """Calculate adjusted stop loss width"""
        return base_stop_pips * level.get_stop_multiplier()
    
    def should_block_trade(self, level: VolatilityLevel, 
                         current_tcs: float, tier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if trade should be blocked due to volatility
        Returns (should_block, reason)
        """
        # Get base TCS for tier
        base_tcs_requirements = {
            'NIBBLER': 72,
            'FANG': 85,
            'COMMANDER': 91,
            '': 91
        }
        base_tcs = base_tcs_requirements.get(tier, 72)
        
        # Get adjusted requirement
        required_tcs = level.get_tcs_requirement(base_tcs)
        
        if current_tcs < required_tcs:
            return True, (
                f"TCS {current_tcs}% below {level.value} volatility "
                f"requirement of {required_tcs}%"
            )
        
        return False, None
    
    def get_post_trade_message(self, level: VolatilityLevel, 
                             trade_opened: bool) -> Optional[str]:
        """Message after trade execution in volatile conditions"""
        if level == VolatilityLevel.NORMAL or not trade_opened:
            return None
        
        messages = {
            VolatilityLevel.ELEVATED: "📊 Trade opened in elevated volatility. Stay sharp.",
            VolatilityLevel.HIGH: "⚡ Trade opened in HIGH volatility. Buckle up, soldier.",
            VolatilityLevel.EXTREME: "🌪️ Trade opened in EXTREME conditions. May the odds be with you."
        }
        
        return messages.get(level)
    
    def calculate_metrics_from_history(self, price_history: List[Dict],
                                     symbol: str) -> VolatilityData:
        """
        Calculate volatility metrics from price history
        This is a simplified version - real implementation would use proper data
        """
        if not price_history or len(price_history) < 20:
            # Default to normal if insufficient data
            return VolatilityData(
                atr_current=0.0010,
                atr_average=0.0010,
                atr_percentile=50.0,
                spread_current=1.0,
                spread_normal=1.0,
                recent_gaps=[]
            )
        
        # Calculate ATR (simplified)
        ranges = []
        for i in range(1, len(price_history)):
            high = price_history[i].get('high', price_history[i]['close'])
            low = price_history[i].get('low', price_history[i]['close'])
            prev_close = price_history[i-1]['close']
            
            true_range = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            ranges.append(true_range)
        
        # Current ATR (last 14 periods)
        atr_current = sum(ranges[-14:]) / 14 if len(ranges) >= 14 else sum(ranges) / len(ranges)
        
        # Average ATR (all history)
        atr_average = sum(ranges) / len(ranges)
        
        # Percentile (simplified)
        atr_percentile = (atr_current / atr_average) * 50 + 50
        atr_percentile = min(100, max(0, atr_percentile))
        
        # Detect gaps
        gaps = []
        for i in range(1, min(5, len(price_history))):
            gap = abs(price_history[i]['open'] - price_history[i-1]['close'])
            if 'JPY' in symbol:
                gap *= 100  # Convert to pips for JPY
            else:
                gap *= 10000  # Convert to pips
            gaps.append(gap)
        
        return VolatilityData(
            atr_current=atr_current,
            atr_average=atr_average,
            atr_percentile=atr_percentile,
            spread_current=1.0,  # Would get from broker
            spread_normal=1.0,   # Would get from broker
            recent_gaps=gaps
        )

# Global instance
_volatility_manager: Optional[VolatilityManager] = None

def get_volatility_manager() -> VolatilityManager:
    """Get or create volatility manager instance"""
    global _volatility_manager
    if _volatility_manager is None:
        _volatility_manager = VolatilityManager()
    return _volatility_manager