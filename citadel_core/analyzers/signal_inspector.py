"""
Signal Inspector Module - Classify and analyze signal characteristics

Purpose: Identify signal type (breakout, reversal, continuation) and key price context
to provide foundational understanding for shield scoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SignalInspector:
    """
    Analyzes raw trading signals to identify patterns and characteristics
    that indicate institutional behavior vs retail traps.
    """
    
    def __init__(self):
        self.signal_types = {
            'BREAKOUT': 'Price breaking key level',
            'REVERSAL': 'Price rejecting and reversing from level',
            'CONTINUATION': 'Trend continuation after pullback',
            'RETEST': 'Retesting previously broken level',
            'TRAP': 'Potential retail trap formation'
        }
        
    def analyze(self, signal: Dict[str, Any], market_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Classify signal type and identify key characteristics.
        
        Args:
            signal: Raw signal dict with pair, direction, entry, sl, tp
            market_data: Optional market context (recent candles, levels)
            
        Returns:
            Dict with signal classification and characteristics
        """
        try:
            # Extract signal components
            pair = signal.get('pair', 'UNKNOWN')
            direction = signal.get('direction', 'UNKNOWN')
            entry_price = float(signal.get('entry_price', 0))
            stop_loss = float(signal.get('sl', 0))
            take_profit = float(signal.get('tp', 0))
            
            # Calculate risk metrics
            risk_pips = abs(entry_price - stop_loss)
            reward_pips = abs(take_profit - entry_price)
            risk_reward = reward_pips / risk_pips if risk_pips > 0 else 0
            
            # Classify signal type based on pattern
            signal_type = self._classify_signal_pattern(
                entry_price, direction, market_data
            )
            
            # Detect entry structure
            entry_structure = self._analyze_entry_structure(
                entry_price, direction, market_data
            )
            
            # Check for volatility zones
            volatility_zone = self._check_volatility_zone(pair, market_data)
            
            # Identify potential traps
            trap_risk = self._assess_trap_risk(
                signal_type, entry_structure, market_data
            )
            
            result = {
                'signal_type': signal_type,
                'is_breakout': signal_type == 'BREAKOUT',
                'is_reversal': signal_type == 'REVERSAL',
                'is_continuation': signal_type == 'CONTINUATION',
                'is_retest': signal_type == 'RETEST',
                'entry_structure': entry_structure,
                'volatility_zone': volatility_zone,
                'trap_risk': trap_risk,
                'risk_reward_ratio': round(risk_reward, 2),
                'risk_pips': round(risk_pips, 1),
                'signal_strength': self._calculate_signal_strength(signal_type, trap_risk)
            }
            
            logger.info(f"Signal inspection complete for {pair}: {signal_type}")
            return result
            
        except Exception as e:
            logger.error(f"Signal inspection error: {str(e)}")
            return self._get_default_analysis()
    
    def _classify_signal_pattern(self, entry: float, direction: str, 
                                market_data: Optional[Dict]) -> str:
        """Classify the signal pattern type."""
        if not market_data:
            return 'UNKNOWN'
            
        recent_high = market_data.get('recent_high', 0)
        recent_low = market_data.get('recent_low', 0)
        current_price = market_data.get('current_price', entry)
        
        # Breakout detection
        if direction == 'BUY' and current_price > recent_high:
            return 'BREAKOUT'
        elif direction == 'SELL' and current_price < recent_low:
            return 'BREAKOUT'
            
        # Reversal detection
        price_at_extreme = (
            (direction == 'SELL' and abs(current_price - recent_high) < recent_high * 0.001) or
            (direction == 'BUY' and abs(current_price - recent_low) < recent_low * 0.001)
        )
        if price_at_extreme:
            return 'REVERSAL'
            
        # Retest detection
        if market_data.get('previous_breakout_level'):
            if abs(current_price - market_data['previous_breakout_level']) < entry * 0.001:
                return 'RETEST'
                
        # Default to continuation
        return 'CONTINUATION'
    
    def _analyze_entry_structure(self, entry: float, direction: str,
                               market_data: Optional[Dict]) -> str:
        """Analyze the structure around entry point."""
        if not market_data:
            return "Price action entry"
            
        timeframes = market_data.get('timeframes', {})
        
        # Check for multi-timeframe confluence
        if 'M15' in timeframes and 'H1' in timeframes:
            m15_structure = timeframes['M15'].get('structure', '')
            h1_structure = timeframes['H1'].get('structure', '')
            
            if 'resistance' in m15_structure.lower() and direction == 'SELL':
                return f"Retest of M15 resistance with H1 confluence"
            elif 'support' in m15_structure.lower() and direction == 'BUY':
                return f"Retest of M15 support with H1 confluence"
                
        # Check for specific patterns
        if market_data.get('pattern'):
            pattern = market_data['pattern']
            if pattern in ['double_top', 'double_bottom', 'head_shoulders']:
                return f"{pattern.replace('_', ' ').title()} pattern completion"
                
        return "Standard price action entry"
    
    def _check_volatility_zone(self, pair: str, market_data: Optional[Dict]) -> bool:
        """Check if signal is in a high volatility zone."""
        if not market_data:
            return False
            
        # Check ATR-based volatility
        current_atr = market_data.get('atr', 0)
        avg_atr = market_data.get('avg_atr', 1)
        
        if current_atr > avg_atr * 1.5:
            return True
            
        # Check for volatile pairs
        volatile_pairs = ['GBPJPY', 'GBPNZD', 'XAUUSD', 'BTCUSD']
        if any(vp in pair.upper() for vp in volatile_pairs):
            # Extra volatility check for known volatile pairs
            if current_atr > avg_atr * 1.2:
                return True
                
        # Check for news volatility
        if market_data.get('upcoming_news_impact') in ['high', 'critical']:
            return True
            
        return False
    
    def _assess_trap_risk(self, signal_type: str, entry_structure: str,
                         market_data: Optional[Dict]) -> str:
        """Assess the risk of this being a retail trap."""
        trap_score = 0
        
        # Breakouts have higher trap risk
        if signal_type == 'BREAKOUT':
            trap_score += 2
            
        # Check for liquidity clusters
        if market_data and market_data.get('nearby_liquidity_cluster'):
            trap_score += 3
            
        # Check for false breakout patterns
        if market_data and market_data.get('previous_false_breakout'):
            trap_score += 2
            
        # Reversal at round numbers often trap retail
        if 'round number' in entry_structure.lower():
            trap_score += 1
            
        # Time-based trap risk
        if market_data:
            hour = market_data.get('signal_hour', 0)
            # Higher trap risk during quiet hours
            if hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Late US to early Asia
                trap_score += 1
                
        # Classify trap risk
        if trap_score >= 5:
            return 'HIGH'
        elif trap_score >= 3:
            return 'MEDIUM'
        elif trap_score >= 1:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _calculate_signal_strength(self, signal_type: str, trap_risk: str) -> str:
        """Calculate overall signal strength rating."""
        strength_score = 5  # Base score
        
        # Adjust for signal type
        if signal_type in ['REVERSAL', 'RETEST']:
            strength_score += 1
        elif signal_type == 'BREAKOUT' and trap_risk != 'HIGH':
            strength_score += 0.5
            
        # Adjust for trap risk
        trap_penalties = {'HIGH': -2, 'MEDIUM': -1, 'LOW': -0.5, 'MINIMAL': 0}
        strength_score += trap_penalties.get(trap_risk, 0)
        
        # Classify strength
        if strength_score >= 6:
            return 'STRONG'
        elif strength_score >= 4:
            return 'MODERATE'
        elif strength_score >= 2:
            return 'WEAK'
        else:
            return 'VERY_WEAK'
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when inspection fails."""
        return {
            'signal_type': 'UNKNOWN',
            'is_breakout': False,
            'is_reversal': False,
            'is_continuation': False,
            'is_retest': False,
            'entry_structure': 'Unable to analyze',
            'volatility_zone': False,
            'trap_risk': 'UNKNOWN',
            'risk_reward_ratio': 0,
            'risk_pips': 0,
            'signal_strength': 'UNKNOWN'
        }


# Example usage
if __name__ == "__main__":
    inspector = SignalInspector()
    
    # Test signal
    test_signal = {
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0910,
        'timestamp': datetime.now().isoformat()
    }
    
    # Test market data
    test_market = {
        'recent_high': 1.0860,
        'recent_low': 1.0800,
        'current_price': 1.0845,
        'atr': 0.0045,
        'avg_atr': 0.0035,
        'timeframes': {
            'M15': {'structure': 'Testing support zone'},
            'H1': {'structure': 'Bullish trend intact'}
        }
    }
    
    result = inspector.analyze(test_signal, test_market)
    print("Signal Inspection Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")